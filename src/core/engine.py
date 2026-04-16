"""
智能推荐引擎（协调器）
核心算法：分数位次匹配 + 多维度权重 + 冲稳保梯度生成

拆分后的架构：
- config.py    → 常量和规则配置
- models.py    → StudentProfile, VolunteerItem
- ranking.py   → 位次查询、等效分
- filters.py   → 体检过滤、选科过滤、位次筛选
- scoring.py   → 偏好打分、录取概率、风险等级
- engine.py    → 本文件，仅负责编排 generate() 主流程
"""
import logging
from .models import StudentProfile, VolunteerItem
from .ranking import RankingService
from .filters import (
    passes_body_check, passes_filter, passes_rank_filter,
    major_matches,
)
from .scoring import calc_pref_score, calc_prob_by_rank, risk_level as _risk_level
from .scoring import tier_from_prob
from .config import MAJOR_KEYWORDS, get_track_label, get_city_level_label, get_nature_label, get_risk_description
from ..data.database import get_connection

logger = logging.getLogger(__name__)


class RecommendEngine:
    """
    志愿推荐引擎（2026-04-04 简化版）
    只用2025年数据，不聚合，直接按专业位次围绕考生位次排序
    """

    def __init__(self, profile: StudentProfile, progress_cb=None):
        self.profile = profile
        self.progress_cb = progress_cb
        self.actual_score = profile.estimated_score + profile.extra_score
        self._ranking = RankingService(profile.subject_first)

    def _emit(self, pct, msg):
        if self.progress_cb:
            self.progress_cb(pct, 100, msg)

    # ── 兼容旧接口：位次查询代理 ──────────────────────
    def get_rank(self, score: int, year: int) -> int:
        return self._ranking.get_rank(score, year)

    def get_score_by_rank(self, rank: int, year: int) -> int:
        return self._ranking.get_score_by_rank(rank, year)

    def get_equivalent_score(self, score: int, from_year: int, to_year: int) -> int:
        return self._ranking.get_equivalent_score(score, from_year, to_year)

    def get_equivalent_score_by_rank(self, rank_2026: int, to_year: int) -> int:
        return self._ranking.get_equivalent_score_by_rank(rank_2026, to_year)

    def get_student_equivalent_score(self, year: int = 2025) -> int:
        return self._ranking.get_student_equivalent_score(self.profile.rank_2026, year)

    # ── 数据加载：只加载2025年 ────────────────────────
    def _load_2025(self) -> list[dict]:
        """只加载2025年投档数据，去重（按院校名+专业名）
        兼容旧 schema：自动检测列是否存在，缺失时用基础列
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # 检查 schema 是否有新列
            cur.execute("PRAGMA table_info(admission_data)")
            columns = {row[1] for row in cur.fetchall()}
            optional_columns = {
                "city": "''",
                "city_level": "''",
                "major_track": "''",
                "tuition": "0",
                "color_restrict_detail": "''",
            }
            optional_selects = []
            for col, default in optional_columns.items():
                if col in columns:
                    optional_selects.append(f"COALESCE(a.{col}, {default}) AS {col}")
                else:
                    optional_selects.append(f"{default} AS {col}")

            cur.execute(f"""
                SELECT 
                    a.college_code, a.college_name, a.major_name, a.subject_type,
                    a.batch, a.province,
                    a.min_score, a.max_score, a.avg_score, a.min_rank, a.plan_count, a.actual_count,
                    a.body_restrict,
                    a.elective_req,
                    a.college_nature,
                    {", ".join(optional_selects)}
                FROM admission_data a
                WHERE a.subject_type=? AND a.year=2025
            """, [self.profile.subject_first])

            rows = [dict(r) for r in cur.fetchall()]

            # 去重：按院校名+专业名，只保留第一条
            seen = {}
            unique = []
            for r in rows:
                key = r['college_name'] + '|' + r['major_name']
                if key not in seen:
                    seen[key] = True
                    unique.append(r)
            return unique
        finally:
            conn.close()

    # ── 位次范围 ─────────────────────────────────────
    def _get_rank_range(self) -> tuple:
        """确定位次范围"""
        student_rank = self._ranking.get_student_rank(self.profile.rank_2026)
        neg = self.profile.rank_offset_neg
        pos = self.profile.rank_offset_pos

        if neg != 0 or pos != 0:
            rank_min = max(1, student_rank - neg) if neg > 0 else 1
            rank_max = student_rank + pos if pos > 0 else 999999
            return rank_min, rank_max

        # 自动计算
        if student_rank <= 5000:
            expand = 0.8
            base_up, base_down = 4000, 12000
        elif student_rank <= 20000:
            expand = 1.0
            base_up, base_down = 15000, 30000
        elif student_rank <= 80000:
            expand = 1.3
            base_up, base_down = 35000, 45000
        else:
            expand = 1.3
            base_up, base_down = 40000, 60000

        rank_min = max(1, student_rank - int(base_up * expand))
        rank_max = student_rank + int(base_down * expand)
        return rank_min, rank_max

    # ── 主生成函数 ───────────────────────────────────
    def generate(self, batch: str = "本科批", total: int = 96) -> list[VolunteerItem]:
        """生成志愿列表"""
        # ── 0. 检查位次是否输入（必填）
        student_rank = self._ranking.get_student_rank(self.profile.rank_2026)
        if student_rank == 0:
            logger.warning("考生位次未输入，无法生成志愿！")
            return []

        # ── 1. 加载2025年数据 ─────────────────────────
        self._emit(5, "加载2025年投档数据...")
        items = self._load_2025()
        if not items:
            logger.warning("数据库中无2025年投档数据，请先导入！")
            return []

        self._emit(20, "筛选数据...")

        # ── 2. 筛选目标批次 ───────────────────────────
        if batch != "全部":
            items = [it for it in items if it.get("batch") == batch]

        # ── 3. 合规筛选（选科/身体条件）────────────────
        items = [it for it in items if passes_body_check(it, self.profile)]

        # ── 4. 位次范围确定 ───────────────────────────
        rank_min, rank_max = self._get_rank_range()
        user_manual_range = (self.profile.rank_offset_neg != 0 or self.profile.rank_offset_pos != 0)

        # ── 5. 位次筛选 + 自动扩大 ────────────────────
        rank_fn = self._ranking.get_rank_cached
        items_by_rank = [it for it in items if passes_rank_filter(it, rank_min, rank_max, rank_fn)]
        self._emit(40, f"位次筛选：{rank_min}~{rank_max}，命中{len(items_by_rank)}条")

        rank_range_relaxed = False
        if not user_manual_range and len(items_by_rank) < total:
            rank_min_orig, rank_max_orig = rank_min, rank_max
            expand_factor = 1.5
            max_expand = 10
            for _ in range(max_expand):
                range_half = max(rank_max - rank_min, rank_min - rank_min_orig) // 2
                extra = int(range_half * (expand_factor - 1.0))
                rank_min = max(1, rank_min - extra)
                rank_max = rank_max + extra
                items_by_rank = [it for it in items if passes_rank_filter(it, rank_min, rank_max, rank_fn)]
                if len(items_by_rank) >= total:
                    rank_range_relaxed = True
                    break
                expand_factor += 0.5
            else:
                rank_range_relaxed = len(items_by_rank) < total
            if rank_range_relaxed or len(items_by_rank) < total:
                self._emit(42, f"位次范围已从{rank_min_orig}~{rank_max_orig}扩大到{rank_min}~{rank_max}，候选{len(items_by_rank)}条")

        self._emit(45, f"最终位次范围：{rank_min}~{rank_max}，位次内候选{len(items_by_rank)}条")

        # ── 6. 省份过滤 ───────────────────────────────
        items_strict_prov = [it for it in items_by_rank if passes_filter(it, self.profile, strict_province=True)]
        items_no_prov = [it for it in items_by_rank if passes_filter(it, self.profile, strict_province=False)]

        province_relaxed = False
        if self.profile.pref_provinces and len(items_strict_prov) < total:
            province_relaxed = True
            self._emit(47, f"偏好省份候选仅{len(items_strict_prov)}条（需{total}条），已自动放宽省份限制...")
            items = items_no_prov
        else:
            items = items_strict_prov

        for it in items:
            it["_province_relaxed"] = province_relaxed and it.get("province", "") not in self.profile.pref_provinces if self.profile.pref_provinces else False

        # ── 7. 专业偏好过滤 ───────────────────────────
        items_all_prov = list(items)
        items_strict_major = [it for it in items if passes_filter(it, self.profile, strict_province=False, strict_major=True)]

        major_relaxed = False
        if self.profile.pref_majors:
            if len(items_strict_major) < total:
                major_relaxed = True
                items = items_all_prov
                for it in items:
                    it["_major_relaxed"] = not major_matches(it.get("major_name", ""), self.profile.pref_majors)
                self._emit(48, f"偏好专业候选仅{len(items_strict_major)}条（需{total}条），已自动放宽专业限制...")
            else:
                items = items_strict_major
                for it in items:
                    it["_major_relaxed"] = False
                self._emit(48, f"偏好专业候选{len(items_strict_major)}条，使用偏好专业...")
        else:
            items = items_all_prov
            for it in items:
                it["_major_relaxed"] = False

        # ── 8. 计算位次差、概率等 ─────────────────────
        student_rank = self._ranking.get_student_rank(self.profile.rank_2026)
        student_equiv_score = self._ranking.get_student_equivalent_score(self.profile.rank_2026, 2025)

        for it in items:
            raw_rank = it.get("min_rank") or 0
            if raw_rank > 0:
                min_rank_2025 = raw_rank
            else:
                min_rank_2025 = self._ranking.get_rank_cached(it.get("min_score", 0), 2025)
                if min_rank_2025 >= 999999:
                    min_rank_2025 = 0

            it["min_rank_2025"] = min_rank_2025
            it["rank_diff"] = student_rank - min_rank_2025 if min_rank_2025 > 0 else 0
            it["score_diff"] = student_equiv_score - (it.get("min_score") or 0)
            it["prob"] = calc_prob_by_rank(it["rank_diff"], self.profile.subject_first)
            it["composite"] = calc_pref_score(it, self.profile.pref_majors, self.profile.pref_provinces)

        # ── 9. 张雪峰策略加权 ─────────────────────────────
        # 根据考生策略，在 composite 分数上追加张雪峰视角加权
        def zxf_bonus(it: dict) -> float:
            """根据考生策略返回额外加分/减分"""
            bonus = 0.0
            strat = getattr(self.profile, 'student_strategy', 'average')
            work  = getattr(self.profile, 'work_preference', 'work')
            out_prov = getattr(self.profile, 'out_of_province', 'yes')

            city_lvl = it.get("city_level", "")
            track    = it.get("major_track", "")
            nature   = it.get("college_nature", "")
            prov     = it.get("province", "")

            # ── 城市加权 ──────────────────────────────────
            is_tier1 = city_lvl in ("一线城市", "一线城市/省会城市", "一线省会")
            is_new1  = city_lvl in ("新一线城市", "新一线城市/省会城市", "新一线省会")
            is_tier2 = city_lvl in ("二线城市", "二线城市/省会城市", "二线省会")
            is_provincial = (prov == "河北")

            if out_prov == "yes":
                # 愿意去外地 → 大城市优先
                if is_tier1:
                    bonus += 30
                elif is_new1:
                    bonus += 20
                elif is_tier2:
                    bonus += 8
                elif is_provincial:
                    bonus -= 5
            else:
                # 优先省内 → 河北加分
                if is_provincial:
                    bonus += 15
                elif is_tier1:
                    bonus += 5  # 仍给一线城市一点加分

            # ── 家庭条件策略 ───────────────────────────────
            if strat == "wealthy":
                # 富裕家庭：可接受中外合作/民办，不歧视高学费
                if "中外合作" in nature:
                    bonus += 5  # 额外加分
                if "民办" in nature or "独立学院" in nature:
                    bonus += 3
            elif strat == "struggle":
                # 困难家庭：强烈不推荐中外合作/民办/天坑
                if "中外合作" in nature:
                    bonus -= 40
                elif "民办" in nature or "独立学院" in nature:
                    bonus -= 20
                # 天坑专业降权
                tiankeng_tracks = ("工：生化环材食药", "理：理学其他", "理：地矿油",
                                   "农：农学植物", "农：农学动物", "文：文科其他")
                if track in tiankeng_tracks:
                    bonus -= 25
                # 避坑赛道直接降权
                if track.startswith("农：") or track == "艺：艺术":
                    bonus -= 35

            # ── 未来目标策略 ───────────────────────────────
            if work == "civil":
                # 考公方向：法学/汉语言/行政管理加分
                civil_keywords = ("法学", "汉语言", "行政管理", "思政", "政治学", "社会学")
                if any(kw in it.get("major_name", "") for kw in civil_keywords):
                    bonus += 25
            elif work == "graduate":
                # 考研深造：基础学科加分
                grad_keywords = ("数学", "物理", "化学", "生物", "英语")
                if any(kw in it.get("major_name", "") for kw in grad_keywords):
                    bonus += 20
            elif work == "work":
                # 直接就业：计算机/口腔/电气加分
                work_keywords = ("计算机", "软件", "电子", "电气", "自动化",
                                 "口腔", "护理", "机械", "土木")
                if any(kw in it.get("major_name", "") for kw in work_keywords):
                    bonus += 15

            return bonus

        for it in items:
            it["zxf_bonus"] = zxf_bonus(it)

        # ── 10. 锚点排序：第30位是锚点 ─────────────────
        # 根据家庭条件调整冲/保比例
        strat = getattr(self.profile, 'student_strategy', 'average')
        if strat == "wealthy":
            # 富裕家庭：多冲
            chong_count = min(40, int(total * 0.42))
        elif strat == "struggle":
            # 困难家庭：多保
            chong_count = min(20, int(total * 0.21))
        else:
            chong_count = 29  # 普通家庭默认
        bao_count = total - chong_count

        chong_pool = [it for it in items if it.get('min_rank_2025', 0) < student_rank]
        bao_pool = [it for it in items if it.get('min_rank_2025', 0) >= student_rank]

        # 冲池排序：两步
        # 第一步：按专业位次降序，取最接近考生位次的chong_count个
        # 排序综合分：composite + zxf_bonus，优先好城市好赛道
        chong_pool.sort(key=lambda x: (
            -x.get('min_rank_2025', 0),
            x.get('college_name', ''),
            -(x.get('composite', 0) + x.get('zxf_bonus', 0)),
        ))
        chong_items = chong_pool[:chong_count]

        # 第二步：这N个按专业位次升序排列（第1个最接近考生位次）
        chong_items.sort(key=lambda x: (
            x.get('min_rank_2025', 0),
            x.get('college_name', ''),
            -(x.get('composite', 0) + x.get('zxf_bonus', 0)),
        ))

        # 保池排序：按专业位次升序 + zxf_bonus
        for i, it in enumerate(bao_pool):
            it['_idx'] = i
        bao_pool.sort(key=lambda x: (
            x.get('min_rank_2025', 0),
            x.get('college_name', ''),
            -(x.get('composite', 0) + x.get('zxf_bonus', 0)),
            x.get('_idx', 0)
        ))
        bao_items = bao_pool[:bao_count]

        result = chong_items + bao_items

        # 张雪峰策略提示
        strat = getattr(self.profile, 'student_strategy', 'average')
        strat_msg = {"wealthy": "富裕家庭→多冲策略", "average": "普通家庭→均衡策略", "struggle": "困难家庭→多保策略"}.get(strat, "")
        self._emit(90, f"生成志愿序号...（{strat_msg}）")

        # ── 10. 构建 VolunteerItem ────────────────────
        volunteers = []
        for seq, it in enumerate(result, start=1):
            prob = it.get("prob", 0.5)
            tier = tier_from_prob(prob)

            vol = VolunteerItem(
                seq=seq,
                college_code=it.get("college_code", ""),
                college_name=it.get("college_name", ""),
                major_name=it.get("major_name", ""),
                subject_type=it.get("subject_type", ""),
                batch=it.get("batch", ""),
                tier=tier,
                min_score_3yr=round(it.get("min_score") or 0, 1),
                avg_score_3yr=round(it.get("avg_score") or it.get("min_score") or 0, 1),
                rank_diff=round(it.get("rank_diff", 0), 0),
                admit_prob=round(prob, 3),
                risk_level=_risk_level(prob),
                province=it.get("province", ""),
                college_nature=it.get("college_nature", "公办"),
                plan_count=it.get("plan_count") or 0,
                min_rank=it.get("min_rank_2025") or 0,
                min_rank_2025=it.get("min_rank_2025") or 0,
                student_rank=student_rank,
                body_restrict=it.get("body_restrict", ""),
                elective_req=it.get("elective_req", "不限"),
                province_relaxed=it.get("_province_relaxed", False),
                major_relaxed=it.get("_major_relaxed", False),
                equivalent_score=student_equiv_score,
                score_diff=round(it.get("score_diff", 0), 1),
                # ── 张雪峰视角新字段 ──────────────────
                city=it.get("city") or "",
                city_level=it.get("city_level") or "",
                major_track=it.get("major_track") or "",
                tuition=it.get("tuition") or "",
                color_restrict_detail=it.get("color_restrict_detail") or "",
            )

            # 补充派生标签（运行时计算，不存库）
            city_emoji, city_lbl = get_city_level_label(vol.city_level)
            vol.city_level_emoji = city_emoji
            vol.city_level_label = city_lbl

            track_e, track_lvl, track_d = get_track_label(vol.major_track)
            vol.track_emoji = track_e
            vol.track_level = track_lvl
            vol.track_desc = track_d

            nat_e, nat_lbl, nat_tip = get_nature_label(vol.college_nature)
            vol.nature_emoji = nat_e
            vol.nature_label = nat_lbl
            vol.nature_tip = nat_tip

            vol.risk_desc = get_risk_description(prob)

            # 学费警告
            if vol.tuition and vol.tuition not in ("待定", "免费", ""):
                try:
                    t = int(vol.tuition)
                    if t >= 50000:
                        vol.tuition_warn = "💰 高学费（≥5万/年）"
                    elif t >= 20000:
                        vol.tuition_warn = "💰 中外合作（≥2万/年）"
                except (ValueError, TypeError):
                    pass

            # ── 综合推荐指数（五星，张雪峰式） ───────────────
            score = 0
            # 城市维度（最重要）
            if vol.city_level_label in ("一线城市", "一线省会"):
                score += 2
            elif vol.city_level_label in ("新一线", "新一线省会"):
                score += 1.5
            elif vol.city_level_label in ("二线城市", "二线省会"):
                score += 0.5
            # 专业赛道
            if vol.track_level == "热门":
                score += 2
            elif vol.track_level == "普通":
                score += 1
            # 办学性质
            if vol.nature_label == "公办":
                score += 1
            elif vol.nature_label == "中外合作":
                score -= 1
            elif vol.nature_label in ("独立学院", "民办"):
                score -= 1.5
            # 录取概率加权（稳妥的更有价值）
            if prob >= 0.9:
                score += 1
            elif prob >= 0.75:
                score += 0.5

            stars = max(1, min(5, int(score + 2.5)))
            vol.recommend_index = "⭐" * stars

            volunteers.append(vol)

        return volunteers
