"""
Excel数据导入模块
负责解析河北省高考投档数据Excel文件并写入数据库

已适配河北省教育考试院真实Excel格式：
- 表头在第2行（行索引2），前两行是标题和排序说明
- 列名含换行符（如"院校\n代号"、"投档\n最低\n分"）
- 院校名称后缀带[公办]/[民办]/[中外合作] 等
- 2025年文件含"一分一段"sheet，自动识别并跳过投档sheet处理
"""
import pandas as pd
import numpy as np
import logging
import re
from pathlib import Path
from .database import get_connection
from ..utils.province_mapping import get_province

logger = logging.getLogger(__name__)

# 跳过的Sheet名称关键词（不含投档数据）
SKIP_SHEET_KEYWORDS = ["一分一段", "说明", "备注", "封面", "目录"]

# 办学性质识别（兼容多种括号格式）
NATURE_PATTERN = re.compile(r'[\[【(（]([公办民办独立学院中外合作办学职业学院]+)[\]】)）]')

# 性质标准化映射（将各种写法统一）
NATURE_MAP = {
    '公办': '公办',
    '民办': '民办',
    '独立学院': '独立学院',
    '中外合作': '中外合作',
    '中外合作办学': '中外合作',
    '合作办学': '中外合作',
    '职业学院': '公办',
}


def _normalize_col(col: str) -> str:
    """规范化列名：去除换行符、多余空格"""
    return re.sub(r'\s+', '', str(col)).strip()


class ExcelImporter:
    """河北省高考投档数据导入器（已适配2023~2025年真实格式）"""

    # 列名映射（支持含换行符的真实列名，匹配时用规范化后的值）
    COL_MAP = {
        "college_code": ["院校代号", "院校代码", "学校代码", "代码", "代号"],
        "college_name": ["院校名称", "学校名称", "院校"],
        "major_code":   ["专业代号", "专业代码"],
        "major_name":   ["专业名称", "专业(类)名称", "专业(类)", "专业"],
        "plan_count":   ["计划数", "招生计划", "计划招生人数", "计划人数"],
        "actual_count": ["录取人数", "实际录取", "录取数", "实际人数"],
        # 真实文件只有"投档最低分"，没有最高/平均分
        "min_score":    ["投档最低分", "最低分", "录取最低分"],
        "max_score":    ["最高分", "录取最高分"],
        "avg_score":    ["平均分", "录取平均分"],
        # 2025年文件列名为"2025年位次"，需模糊匹配
        "min_rank":     ["2025年位次", "2024年位次", "2023年位次", "最低位次", "投档最低位次", "位次"],
        "province":     ["省份", "生源地"],
        "batch":        ["批次", "录取批次"],
        "remark":       ["备注"],
    }

    def __init__(self, filepath: str, year: int, subject_type: str = "物理",
                 batch: str = "本科批", progress_cb=None):
        self.filepath = Path(filepath)
        self.year = year
        self.subject_type = subject_type
        self.batch = batch
        self.progress_cb = progress_cb

    def _find_col(self, df: pd.DataFrame, key: str):
        """在DataFrame列中查找匹配的字段名（支持含换行列名）"""
        candidates = self.COL_MAP.get(key, [])
        norm_candidates = [_normalize_col(c) for c in candidates]
        norm_cols = {col: _normalize_col(col) for col in df.columns}

        # 第一轮：精确匹配
        for col, col_norm in norm_cols.items():
            if col_norm in norm_candidates:
                return col

        # 第二轮：候选词完整包含在列名中（列名包含候选词）
        for col, col_norm in norm_cols.items():
            for cand_norm in norm_candidates:
                # 要求候选词长度>=3，避免"院校"误匹配"院校代号"
                if cand_norm and len(cand_norm) >= 3 and cand_norm in col_norm:
                    return col

        # 第三轮：列名包含在候选词中（列名是候选词的子串，要求列名>=3字）
        for col, col_norm in norm_cols.items():
            for cand_norm in norm_candidates:
                if col_norm and len(col_norm) >= 3 and col_norm in cand_norm:
                    return col

        return None

    def _emit(self, current, total, msg):
        if self.progress_cb:
            self.progress_cb(current, total, msg)

    @staticmethod
    def _clean_college_name(raw: str):
        """
        提取院校名称中的办学性质标记：
        - 识别 [公办] [民办] [独立学院] [中外合作] 等方括号后缀
        - 返回 (clean_name, nature)
        - clean_name：去除方括号性质标记后的院校名（保留城市括注如 (合肥市)）
        - nature：标准化的办学性质字符串
        """
        raw = str(raw).strip()
        # 用宽松正则匹配方括号内的性质标记
        nature_re = re.compile(r'\[([^\]]+)\]')
        nature = '公办'
        clean = raw
        for m in nature_re.finditer(raw):
            tag = m.group(1).strip()
            # 判断是否是性质标记（含以下关键词）
            if any(k in tag for k in ['公办', '民办', '独立学院', '中外合作', '合作办学', '职业学院']):
                nature = NATURE_MAP.get(tag, tag)
                clean = raw[:m.start()].strip() + raw[m.end():].strip()
                break
        return clean.strip(), nature

    def import_file(self) -> dict:
        """导入Excel文件，返回 {success, skipped, errors, score_rank_imported}"""
        if not self.filepath.exists():
            raise FileNotFoundError(f"文件不存在: {self.filepath}")

        self._emit(0, 100, f"正在读取文件：{self.filepath.name}")
        score_rank_result = None
        try:
            xl = pd.ExcelFile(self.filepath)
            sheets = xl.sheet_names
            logger.info("Excel文件共 %d 个Sheet: %s", len(sheets), sheets)

            all_rows = []
            for sheet in sheets:
                sheet_str = str(sheet)
                # 如果是一分一段sheet，单独处理
                if "一分一段" in sheet_str:
                    logger.info("检测到一分一段sheet: %s，单独导入", sheet_str)
                    self._emit(5, 100, f"检测到一分一段表（{sheet_str}），正在导入...")
                    score_rank_result = self._import_score_rank_sheet(xl, sheet_str)
                    continue
                # 跳过非数据sheet
                if any(kw in sheet_str for kw in SKIP_SHEET_KEYWORDS):
                    logger.info("跳过非数据Sheet: %s", sheet_str)
                    continue

                df = xl.parse(sheet, header=None)
                df = self._preprocess_df(df, sheet_str)
                if df is not None and not df.empty:
                    all_rows.append(df)
                    logger.info("Sheet[%s] 解析到 %d 行", sheet_str, len(df))

            if not all_rows:
                raise ValueError("未能从Excel中解析出有效投档数据，请检查文件格式")

            df_all = pd.concat(all_rows, ignore_index=True)
            # 去重（同院校+专业可能跨sheet重复）
            df_all = df_all.drop_duplicates(
                subset=["college_name", "major_name"], keep="first"
            ) if "college_name" in df_all.columns and "major_name" in df_all.columns else df_all

        except Exception as e:
            logger.error("读取Excel失败: %s", e)
            raise

        self._emit(30, 100, f"解析完成，共 {len(df_all)} 行有效数据，开始写入数据库...")
        result = self._write_to_db(df_all)
        if score_rank_result:
            result["score_rank_imported"] = score_rank_result.get("inserted", 0)
        self._emit(100, 100, f"导入完成：成功 {result['success']} 条，跳过 {result['skipped']} 条")
        return result

    def _preprocess_df(self, df: pd.DataFrame, sheet_name: str = ""):
        """自动识别表头行并整理DataFrame（适配真实格式）"""
        # 真实文件表头在第2行（索引2），前两行是标题和排序子项说明
        # 策略：扫描前10行，找含"院校"/"专业"/"代号"关键词的行
        header_row = None
        for i in range(min(10, len(df))):
            row_str = " ".join(str(v) for v in df.iloc[i].values)
            if any(kw in row_str for kw in ["院校", "专业", "代号", "代码"]):
                # 确保不是纯说明行（说明行通常是"一、二、三"或"语数成绩"等）
                if not all(kw in row_str for kw in ["语数", "外语"]):
                    header_row = i
                    break

        if header_row is None:
            logger.warning("Sheet[%s] 未找到表头行，跳过", sheet_name)
            return None

        # 设置列名，合并换行符
        raw_cols = df.iloc[header_row].tolist()
        df.columns = [_normalize_col(c) for c in raw_cols]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        df = df.dropna(how="all")

        # 跳过紧随表头的说明行（可能有多行：排序编号行 + 排序字段名行）
        # 特征：不含院校代号格式的数值（4位数字），但含"一二三四五"或"语数"等
        rows_to_skip = 0
        for i in range(min(5, len(df))):
            row_vals = [str(v) for v in df.iloc[i].values if str(v) not in ("nan", "None", "")]
            row_str = " ".join(row_vals)
            # 说明行特征1：全是汉字序号（一二三四五六...）
            # 说明行特征2：含"语数""外语""首选科目"等字样
            # 数据行特征：第一列是4位数字院校代码
            first_val = row_vals[0] if row_vals else ""
            is_data_row = bool(re.match(r'^\d{4}$', first_val)) or bool(re.match(r'^\d{4,5}$', first_val))
            is_skip_row = (
                any(kw in row_str for kw in ["语数", "外语", "首选科目", "再选科目"]) or
                (not is_data_row and all(re.match(r'^[一二三四五六七八九十\d]+$', v) for v in row_vals[:5] if v))
            )
            if is_skip_row:
                rows_to_skip = i + 1
            elif is_data_row:
                break  # 遇到真实数据行，停止

        if rows_to_skip > 0:
            df = df.iloc[rows_to_skip:].reset_index(drop=True)

        # 重新用规范化列名做映射
        col_mapping = {}
        for key in self.COL_MAP:
            col = self._find_col(df, key)
            if col and col not in col_mapping:
                col_mapping[col] = key

        if "college_name" not in col_mapping.values() or "major_name" not in col_mapping.values():
            logger.warning("Sheet[%s] 未找到院校名称或专业名称列，跳过（可用列：%s）",
                           sheet_name, list(df.columns)[:10])
            return None

        df = df.rename(columns=col_mapping)
        return df

    def _clean_score(self, val):
        if pd.isna(val) or str(val).strip() in ("", "-", "—", "无", "N/A", "nan", "None"):
            return None
        try:
            return float(str(val).replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    def _clean_int(self, val):
        v = self._clean_score(val)
        return int(v) if v is not None else None

    def _write_to_db(self, df: pd.DataFrame) -> dict:
        """批量写入 admission_data 表，同时维护 colleges 表"""
        conn = get_connection()
        success = 0
        skipped = 0
        errors = []
        total = len(df)

        try:
            cur = conn.cursor()
            # 先删除同年同科目同批次旧数据（幂等）
            cur.execute(
                "DELETE FROM admission_data WHERE year=? AND subject_type=? AND batch=?",
                (self.year, self.subject_type, self.batch)
            )

            batch_data = []
            colleges_seen = {}  # code -> (clean_name, nature)

            for i, row in df.iterrows():
                if i % 500 == 0 and total > 0:
                    self._emit(30 + int(60 * i / total), 100, f"正在处理 {i}/{total} 条...")

                raw_college_name = str(row.get("college_name", "")).strip()
                major_name = str(row.get("major_name", "")).strip()

                if not raw_college_name or not major_name:
                    skipped += 1
                    continue
                if raw_college_name in ("nan", "None") or major_name in ("nan", "None"):
                    skipped += 1
                    continue
                # 过滤非数据行（数字编号行等）
                if re.match(r'^[一二三四五六七八九十\d]+$', raw_college_name):
                    skipped += 1
                    continue

                clean_name, nature = self._clean_college_name(raw_college_name)
                college_code = str(row.get("college_code", "")).strip()
                if not college_code or college_code in ("nan", "None"):
                    college_code = "UNKNOWN"

                # 使用省份映射工具获取院校省份
                province = get_province(college_name=clean_name, college_code=college_code)

                # 记录院校信息用于写colleges表
                if college_code != "UNKNOWN" and college_code not in colleges_seen:
                    colleges_seen[college_code] = (clean_name, nature, province)

                record = (
                    self.year,
                    college_code,
                    clean_name,
                    nature,          # college_nature
                    major_name,
                    self.subject_type,
                    str(row.get("batch", self.batch)).strip() or self.batch,
                    self._clean_int(row.get("plan_count")),
                    self._clean_int(row.get("actual_count")),
                    self._clean_score(row.get("min_score")),
                    self._clean_score(row.get("max_score")),
                    self._clean_score(row.get("avg_score")),
                    self._clean_int(row.get("min_rank")),
                    province,
                )
                batch_data.append(record)
                success += 1

            cur.executemany("""
                INSERT INTO admission_data
                (year, college_code, college_name, college_nature, major_name, subject_type, batch,
                 plan_count, actual_count, min_score, max_score, avg_score, min_rank, province)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, batch_data)

            # 同步写入 colleges 表（INSERT OR IGNORE，不覆盖已有记录）
            for code, (name, nature, province) in colleges_seen.items():
                cur.execute("""
                    INSERT OR IGNORE INTO colleges (code, name, nature, province, level)
                    VALUES (?, ?, ?, ?, '本科')
                """, (code, name, nature, province))

            conn.commit()
            logger.info("写入完成：%d 条投档记录，%d 所院校", success, len(colleges_seen))

        except Exception as e:
            conn.rollback()
            logger.error("写入数据库失败: %s", e)
            errors.append(str(e))
            raise
        finally:
            conn.close()

        return {"success": success, "skipped": skipped, "errors": errors}

    def _import_score_rank_sheet(self, xl: pd.ExcelFile, sheet_name: str) -> dict:
        """从Excel的一分一段sheet导入位次数据"""
        try:
            df = xl.parse(sheet_name, header=None)
            # 找表头（真实格式：
            #   行0：大标题 "2025年河北省普通高校招生物理科目组合、历史科目组合"
            #   行1：nan, "考生成绩统计表", ...
            #   行2：分数档次, 物理(含优惠分), nan, 历史(含优惠分), nan
            #   行3：nan, 人数, 累计人数, 人数, 累计人数   ← 子表头
            #   行4 起：真实数据
            # 寻找含"分数档次"或"考生成绩统计表"的行，真实数据在该行之后3行
            header_row = None
            for i in range(min(10, len(df))):
                row_str = " ".join(str(v) for v in df.iloc[i].values)
                if "分数档次" in row_str or "考生成绩统计表" in row_str:
                    header_row = i
                    break
            if header_row is None:
                return {"inserted": 0, "error": "未找到一分一段表头"}

            # 数据从 header_row + 3 开始（跳过：科目标签行+子表头行）
            # 注意：如果"考生成绩统计表"在行1，真实数据在行4（1+3=4）✓
            #       如果"分数档次"在行2，真实数据在行4（2+2=4）
            # 需要智能判断：找到"考生成绩统计表"时+3，找到"分数档次"时+2
            row_str_found = " ".join(str(v) for v in df.iloc[header_row].values)
            if "考生成绩统计表" in row_str_found:
                data_start = header_row + 3
            else:
                data_start = header_row + 2
            df_data = df.iloc[data_start:].reset_index(drop=True)

            # 根据科目类型选择正确的列
            if self.subject_type == "物理":
                score_col_idx = 0      # 第0列：分数档次
                this_col_idx = 1       # 第1列：物理人数
                cum_col_idx = 2        # 第2列：物理累计人数
            else:  # 历史
                score_col_idx = 0      # 第0列：分数档次
                this_col_idx = 3       # 第3列：历史人数
                cum_col_idx = 4        # 第4列：历史累计人数

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM score_rank WHERE year=? AND subject_type=?",
                        (self.year, self.subject_type))
            inserted = 0
            for _, row in df_data.iterrows():
                try:
                    score = row[score_col_idx]
                    if pd.isna(score):
                        continue
                    score = int(float(score))

                    this_val = row.get(this_col_idx)
                    cum_val = row.get(cum_col_idx)

                    # 处理空值
                    if this_val is None or pd.isna(this_val) or str(this_val).strip() == "":
                        rank_this = 0
                    else:
                        try:
                            rank_this = int(float(this_val))
                        except:
                            rank_this = 0

                    if cum_val is None or pd.isna(cum_val) or str(cum_val).strip() == "":
                        rank_cum = 0
                    else:
                        try:
                            rank_cum = int(float(cum_val))
                        except:
                            rank_cum = 0

                    cur.execute("""
                        INSERT OR REPLACE INTO score_rank
                        (year, subject_type, score, rank_this, rank_cumulative)
                        VALUES (?,?,?,?,?)
                    """, (self.year, self.subject_type, score, rank_this, rank_cum))
                    inserted += 1
                except (ValueError, TypeError):
                    continue
            conn.commit()
            conn.close()
            logger.info("一分一段导入完成：%d 条（%s %s）", inserted, self.year, self.subject_type)
            return {"inserted": inserted}
        except Exception as e:
            logger.error("一分一段导入失败: %s", e)
            return {"inserted": 0, "error": str(e)}


def import_score_rank(filepath: str, year: int, subject_type: str = "物理") -> dict:
    """
    从独立一分一段Excel文件导入（单独文件时使用）
    Excel格式预期：分数 | 本段人数 | 累计人数
    """
    df = pd.read_excel(filepath, header=None)

    # 自动找表头
    header_row = 0
    for i in range(min(10, len(df))):
        row_str = " ".join(str(v) for v in df.iloc[i].values)
        if any(kw in row_str for kw in ["分数", "成绩", "位次", "人数"]):
            header_row = i
            break

    df.columns = [_normalize_col(c) for c in df.iloc[header_row].tolist()]
    df = df.iloc[header_row + 1:].reset_index(drop=True).dropna(how="all")

    col_score = col_this = col_cum = None
    for c in df.columns:
        cn = _normalize_col(c)
        if any(k in cn for k in ["分数", "成绩"]):
            col_score = c
        elif any(k in cn for k in ["本段", "本分段", "该分段"]):
            col_this = c
        elif any(k in cn for k in ["累计", "位次", "累积"]):
            col_cum = c

    if not col_score:
        raise ValueError("一分一段表中未找到分数列")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM score_rank WHERE year=? AND subject_type=?", (year, subject_type))
    inserted = 0
    for _, row in df.iterrows():
        try:
            score = int(float(row[col_score]))
            rank_this = int(float(row[col_this])) if col_this else 0
            rank_cum = int(float(row[col_cum])) if col_cum else 0
            cur.execute(
                "INSERT OR REPLACE INTO score_rank (year, subject_type, score, rank_this, rank_cumulative) VALUES (?,?,?,?,?)",
                (year, subject_type, score, rank_this, rank_cum)
            )
            inserted += 1
        except (ValueError, TypeError):
            continue
    conn.commit()
    conn.close()
    return {"inserted": inserted}
