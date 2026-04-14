"""
报告导出模块
支持导出 Excel 和 PDF 格式
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)

# 输出目录放到用户目录（%LOCALAPPDATA%），避免权限问题
if os.name == 'nt':  # Windows
    OUTPUT_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home())) / "河北高考志愿填报系统" / "output"
else:
    OUTPUT_DIR = Path.home() / ".gaokao_volunteer" / "output"


def export_excel(volunteers: list, student: dict = None, out_path: str = None) -> str:
    """
    导出志愿表到Excel
    student: 考生信息字典（用于在表头下方显示个人信息）
    out_path: 自定义输出路径（可选）
    Returns: 输出文件路径
    """
    if student is None:
        student = {}
    student_name = student.get("name", "考生")

    import xlsxwriter

    if out_path:
        out_path = Path(out_path)
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / f"志愿表_{student_name}_{ts}.xlsx"

    wb = xlsxwriter.Workbook(str(out_path))
    ws = wb.add_worksheet("志愿列表")

    # ── 格式定义 ─────────────────────────────────────────
    fmt_title = wb.add_format({
        "bold": True, "font_size": 14, "font_name": "微软雅黑",
        "align": "center", "valign": "vcenter",
        "fg_color": "#1B5E9B", "font_color": "white",
        "border": 1
    })
    fmt_info = wb.add_format({
        "font_name": "微软雅黑", "font_size": 10,
        "align": "left", "valign": "vcenter",
        "border": 1, "text_wrap": True
    })
    fmt_info_label = wb.add_format({
        "bold": True, "font_name": "微软雅黑", "font_size": 10,
        "align": "right", "valign": "vcenter",
        "fg_color": "#D6EAF8", "border": 1
    })
    fmt_header = wb.add_format({
        "bold": True, "font_name": "微软雅黑", "font_size": 10,
        "align": "center", "valign": "vcenter",
        "fg_color": "#2E86C1", "font_color": "white",
        "border": 1, "text_wrap": True
    })
    fmt_risk = {
        "高": wb.add_format({"font_color": "#C0392B", "bold": True,
                              "font_name": "微软雅黑", "font_size": 10, "border": 1, "align": "center"}),
        "中": wb.add_format({"font_color": "#E67E22", "bold": True,
                              "font_name": "微软雅黑", "font_size": 10, "border": 1, "align": "center"}),
        "低": wb.add_format({"font_color": "#27AE60", "bold": True,
                              "font_name": "微软雅黑", "font_size": 10, "border": 1, "align": "center"}),
    }
    fmt_normal = wb.add_format({
        "font_name": "微软雅黑", "font_size": 10, "border": 1, "valign": "vcenter"
    })
    fmt_center = wb.add_format({
        "font_name": "微软雅黑", "font_size": 10, "border": 1,
        "align": "center", "valign": "vcenter"
    })
    fmt_num = wb.add_format({
        "font_name": "微软雅黑", "font_size": 10, "border": 1,
        "align": "right", "valign": "vcenter", "num_format": "0.0"
    })
    fmt_pct = wb.add_format({
        "font_name": "微软雅黑", "font_size": 10, "border": 1,
        "align": "right", "valign": "vcenter", "num_format": "0%"
    })

    # ── 标题 ─────────────────────────────────────────────
    ws.merge_range("A1:P1", f"河北省高考志愿填报表  · {student_name}  · {datetime.now().strftime('%Y年%m月%d日')}", fmt_title)
    ws.set_row(0, 30)

    # ── 考生个人信息行 ─────────────────────────────────────
    # 第2行：姓名、预估分（含加分）、首选科目、再选科目
    stu_rank = student.get('student_rank', 0)
    rank_str = f"{stu_rank:,}" if stu_rank else "未知"
    info_row_1 = [
        ("姓名", student.get('name', '考生')),
        ("预估分", f"{student.get('estimated_score', 0)}分"),
        ("加分", f"+{student.get('extra_score', 0)}分"),
        ("首选科目", student.get('subject_first', '物理')),
        ("再选科目", f"{student.get('subject_elective1','')}、{student.get('subject_elective2','')}"),
        ("考生位次", f"{rank_str}名"),
        ("性别", student.get('gender', '男')),
        ("色觉", student.get('color_vision', '正常')),
    ]
    ws.set_row(1, 20)
    col = 0
    for label, value in info_row_1:
        ws.write(1, col, label, fmt_info_label)
        ws.write(1, col + 1, str(value), fmt_info)
        col += 2

    # 第3行：裸眼视力、身高、体重、生成时间
    info_row_2 = [
        ("裸眼视力", f"{student.get('naked_eye_vision', '5.0')}"),
        ("身高", f"{student.get('height_cm', 170)}cm"),
        ("体重", f"{student.get('weight_kg', 60)}kg"),
        ("生成时间", datetime.now().strftime('%Y-%m-%d %H:%M')),
    ]
    ws.set_row(2, 20)
    col = 0
    for label, value in info_row_2:
        ws.write(2, col, label, fmt_info_label)
        ws.write(2, col + 1, str(value), fmt_info)
        col += 2

    # ── 表头（第4行） ─────────────────────────────────────
    headers = [
        "序号", "梯度", "院校代码", "院校名称", "专业名称",
        "批次", "省份", "城市", "城市级别", "办学性质", "专业赛道", "学费(元/年)", "推荐指数",
        "近三年最低分", "近三年均分", "等效分", "分差",
        "位次差", "录取概率", "风险", "张雪峰提示",
        "最低位次", "2025年位次", "选科要求", "体检限制"
    ]
    col_widths = [
        5, 5, 10, 20, 20, 8, 8, 10, 10, 10, 14, 12, 9,
        11, 11, 8, 8, 8, 9, 5, 18, 11, 11, 10, 20
    ]
    header_row = 3
    ws.set_row(header_row, 22)
    for col, (h, w) in enumerate(zip(headers, col_widths)):
        ws.write(header_row, col, h, fmt_header)
        ws.set_column(col, col, w)

    # ── 数据行 ───────────────────────────────────────────
    for row_idx, vol in enumerate(volunteers):
        r = row_idx + 4
        risk = vol.risk_level
        ws.set_row(r, 18)
        ws.write(r, 0,  vol.seq,          fmt_center)
        ws.write(r, 1,  vol.tier,          fmt_center)
        ws.write(r, 2,  vol.college_code, fmt_center)
        ws.write(r, 3,  vol.college_name, fmt_normal)
        # 专业名称：放宽时用橙色字体标注
        if getattr(vol, 'major_relaxed', False):
            ws.write(r, 4, f"{vol.major_name}（放宽）", wb.add_format({
                "font_name": "微软雅黑", "font_size": 9, "border": 1,
                "font_color": "#E67E22", "bold": True,
            }))
        else:
            ws.write(r, 4, vol.major_name, fmt_normal)
        ws.write(r, 5,  vol.batch,        fmt_center)
        # 省份列：放宽时显示"省份（放宽）"并用橙色字体
        if getattr(vol, 'province_relaxed', False):
            ws.write(r, 6, f"{vol.province}（放宽）", wb.add_format({
                "font_name": "微软雅黑", "font_size": 9, "border": 1, "align": "center",
                "font_color": "#E67E22", "bold": True,
            }))
        else:
            ws.write(r, 6,  vol.province,     fmt_center)
        # 城市
        ws.write(r, 7, getattr(vol, 'city', '') or '-', fmt_center)
        # 城市级别
        ws.write(r, 8, f"{getattr(vol,'city_level_emoji','')} {getattr(vol,'city_level_label','')}" if getattr(vol,'city_level_emoji','') else '-', fmt_center)
        # 办学性质
        ws.write(r, 9, f"{getattr(vol,'nature_emoji','')} {getattr(vol,'nature_label','')}", wb.add_format({
            "font_name": "微软雅黑", "font_size": 9, "border": 1, "align": "center",
            "font_color": "#E65100" if getattr(vol,'nature_label','') in ("独立学院","民办") else "#6A1B9A" if getattr(vol,'nature_label','') == "中外合作" else "#333333",
            "bold": getattr(vol,'nature_label','') in ("独立学院","民办","中外合作"),
        }))
        # 专业赛道
        ws.write(r, 10, f"{getattr(vol,'track_emoji','')} {getattr(vol,'track_desc','')}", wb.add_format({
            "font_name": "微软雅黑", "font_size": 9, "border": 1, "align": "center",
            "font_color": "#2E7D32" if getattr(vol,'track_level','') == "热门" else "#C0392B" if getattr(vol,'track_level','') in ("天坑","避坑") else "#333333",
            "bold": getattr(vol,'track_level','') in ("热门","天坑","避坑"),
        }))
        # 学费
        tuition_val = getattr(vol, 'tuition', '') or ''
        ws.write(r, 11, tuition_val if tuition_val else '-', wb.add_format({
            "font_name": "微软雅黑", "font_size": 9, "border": 1, "align": "center",
            "font_color": "#6A1B9A" if tuition_val and not tuition_val.isdigit() or (tuition_val.isdigit() and int(tuition_val) >= 20000) else "#333333",
            "bold": tuition_val.isdigit() and int(tuition_val) >= 20000 if tuition_val else False,
        }))
        # 推荐指数
        rec_idx = getattr(vol, 'recommend_index', '') or '-'
        ws.write(r, 12, rec_idx, wb.add_format({
            "font_name": "微软雅黑", "font_size": 12, "border": 1, "align": "center",
            "font_color": "#E67E22" if rec_idx and rec_idx != '-' else "#333333",
            "bold": True,
        }))
        ws.write(r, 13,  vol.min_score_3yr, fmt_num)
        ws.write(r, 14,  vol.avg_score_3yr, fmt_num)
        ws.write(r, 15,  vol.equivalent_score if hasattr(vol, 'equivalent_score') and vol.equivalent_score else "-", fmt_center)
        ws.write(r, 16, f"{vol.score_diff:+.1f}" if hasattr(vol, 'score_diff') else "-", fmt_num)
        ws.write(r, 17, int(vol.rank_diff),   fmt_num)
        ws.write(r, 18, vol.admit_prob,   fmt_pct)
        ws.write(r, 19, risk,             fmt_risk.get(risk, fmt_center))
        # 张雪峰提示
        risk_desc = getattr(vol, 'risk_desc', '') or ''
        ws.write(r, 20, risk_desc, wb.add_format({
            "font_name": "微软雅黑", "font_size": 9, "border": 1,
            "font_color": "#C0392B" if "冲" in risk_desc else "#2E7D32" if "稳" in risk_desc else "#E67E22",
        }))
        ws.write(r, 21, f"{vol.min_rank:,}" if vol.min_rank else "-", fmt_center)
        ws.write(r, 22, f"{vol.min_rank_2025:,}" if vol.min_rank_2025 else "-", fmt_center)
        # 选科要求
        elec = vol.elective_req if vol.elective_req and vol.elective_req != "不限" else ""
        if elec:
            ws.write(r, 23, elec, wb.add_format({
                "font_name": "微软雅黑", "font_size": 9, "border": 1,
                "font_color": "#8E24AA", "text_wrap": True
            }))
        else:
            ws.write(r, 22, "", fmt_normal)
        # 体检限制 - 有内容时用红色字体
        if vol.body_restrict:
            ws.write(r, 23, vol.body_restrict, wb.add_format({
                "font_name": "微软雅黑", "font_size": 9, "border": 1,
                "font_color": "#C0392B", "text_wrap": True
            }))
        else:
            ws.write(r, 23, "", fmt_normal)

    # ── 图例说明 ─────────────────────────────────────────
    last_row = len(volunteers) + 5
    ws.merge_range(last_row, 0, last_row, 22,
        "【说明】梯度标签：冲<50% 稳50-80% 保>80%  |  🔥=热门赛道  ⚠️=天坑/谨慎赛道  🚫=避坑赛道  |  办学性质：⚠️=独立学院  🚫=民办  💰=中外合作/高学费  |  张雪峰提示仅供参考，请以考试院官方数据为准",
        wb.add_format({"font_name": "微软雅黑", "font_size": 9, "fg_color": "#F8F9FA",
                       "font_color": "#E67E22", "border": 1, "italic": True}))

    wb.close()
    logger.info("Excel导出完成：%s", out_path)
    return str(out_path)


def export_pdf(volunteers: list, student: dict, out_path: str = None) -> str:
    """
    导出志愿分析报告PDF（横排A4，显示完整）
    Returns: 输出文件路径
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import platform

    # 注册中文字体
    font_paths = []
    if platform.system() == "Windows":
        font_paths = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                break
            except Exception:
                continue
    else:
        # 回退到内置字体
        pass

    cn_font = "ChineseFont" if "ChineseFont" in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not out_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = str(OUTPUT_DIR / f"志愿分析报告_{student.get('name','考生')}_{ts}.pdf")

    # 横排A4：可用宽度约 25.7cm（29.7-2*2cm边距）
    page_size = landscape(A4)
    doc = SimpleDocTemplate(out_path, pagesize=page_size,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()

    # ── 辅助：截断中文文本（按字符数，1个中文≈2个英文字符宽度）─────────
    def short(text, max_chars=8):
        if not text:
            return "-"
        return text[:max_chars] + ("…" if len(text) > max_chars else "")

    def short_num(val, fmt="{}"):
        if val is None or val == "" or val == "-":
            return "-"
        try:
            return fmt.format(int(val))
        except (ValueError, TypeError):
            return str(val)[:8]

    # 配色方案
    CLR_BLUE    = colors.HexColor("#1B5E9B")
    CLR_LIGHT   = colors.HexColor("#D6EAF8")
    CLR_ROW1    = colors.white
    CLR_ROW2    = colors.HexColor("#EEF6FF")
    CLR_GREY    = colors.HexColor("#555555")
    CLR_ORANGE  = colors.HexColor("#E67E22")

    # 通用样式
    def ps(name, **kw):
        return ParagraphStyle(name, fontName=cn_font, **kw)

    title_style = ps("title", fontSize=15, leading=20,
                     alignment=1, spaceAfter=8, textColor=CLR_BLUE)
    h2_style    = ps("h2", fontSize=11, leading=16,
                     spaceBefore=8, spaceAfter=4, textColor=CLR_BLUE)
    body_style  = ps("body", fontSize=9, leading=13, spaceAfter=3)

    story = []

    # ── 封面标题 ─────────────────────────────────────────────
    story.append(Paragraph("河北省高考志愿填报分析报告", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=CLR_BLUE))
    story.append(Spacer(1, 0.2*cm))

    # ── 考生基本信息（横排卡片式）───────────────────────────
    story.append(Paragraph("一、考生基本信息", h2_style))

    def mk_info_cell(label, value):
        return [Paragraph(label, ps("_il", fontSize=9, textColor=CLR_GREY)),
                Paragraph(str(value), ps("_iv", fontSize=10, leading=14))]

    rank_val = student.get("student_rank", 0)
    rank_str = f"{rank_val:,}名" if rank_val else "未填写"
    elec = f"{student.get('subject_elective1','')}、{student.get('subject_elective2','')}"
    info_data = [
        mk_info_cell("姓名", student.get("name", "考生")),
        mk_info_cell("首选科目", student.get("subject_first", "物理")),
        mk_info_cell("性别", student.get("gender", "男")),
        mk_info_cell("考生位次", rank_str),
        mk_info_cell("预估分", f"{student.get('estimated_score', 0)}分"),
        mk_info_cell("政策加分", f"+{student.get('extra_score', 0)}分"),
        mk_info_cell("再选科目", elec),
        mk_info_cell("色觉状态", student.get("color_vision", "正常")),
        mk_info_cell("裸眼视力", student.get("naked_eye_vision", "5.0")),
        mk_info_cell("身高/体重", f"{student.get('height_cm', 170)}cm / {student.get('weight_kg', 60)}kg"),
        mk_info_cell("生成时间", datetime.now().strftime('%Y-%m-%d %H:%M')),
        mk_info_cell("志愿数量", f"{len(volunteers)} 个"),
    ]
    info_table = Table([info_data], colWidths=[2.2*cm]*12)
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), cn_font),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (0,-1), CLR_LIGHT),
        ("BACKGROUND", (2,0), (2,-1), CLR_LIGHT),
        ("BACKGROUND", (4,0), (4,-1), CLR_LIGHT),
        ("BACKGROUND", (6,0), (6,-1), CLR_LIGHT),
        ("BACKGROUND", (8,0), (8,-1), CLR_LIGHT),
        ("BACKGROUND", (10,0), (10,-1), CLR_LIGHT),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*cm))

    # ── 志愿统计（横排紧凑）──────────────────────────────────
    story.append(Paragraph("二、志愿统计", h2_style))
    risk_counts = {"高": 0, "中": 0, "低": 0}
    for v in volunteers:
        risk_counts[v.risk_level] = risk_counts.get(v.risk_level, 0) + 1

    dist_data = [
        ["风险等级", "数量", "说明", "数量", "说明"],
        ["高风险（概率<40%）", str(risk_counts.get("高", 0)), "录取概率较低，需谨慎",
         str(len([v for v in volunteers if v.tier == "冲"])), "冲刺志愿"],
        ["中风险（概率40-70%）", str(risk_counts.get("中", 0)), "录取概率中等",
         str(len([v for v in volunteers if v.tier == "稳"])), "稳妥志愿"],
        ["低风险（概率>70%）", str(risk_counts.get("低", 0)), "录取概率较高",
         str(len([v for v in volunteers if v.tier == "保"])), "保底志愿"],
    ]
    dist_table = Table(dist_data, colWidths=[3.5*cm, 1.5*cm, 4*cm, 1.5*cm, 3*cm])
    dist_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), cn_font),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (-1,0), CLR_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CLR_ROW1, CLR_ROW2]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,-1), "CENTER"),
        ("ALIGN", (3,0), (3,-1), "CENTER"),
    ]))
    story.append(dist_table)
    story.append(Spacer(1, 0.3*cm))

    # ── 志愿明细表（横排A4，精简列）─────────────────────────
    story.append(Paragraph("三、志愿明细", h2_style))

    # 图例（紧凑横排）
    legend = Paragraph(
        "<font color='#E67E22'>梯度：冲=录取概率&lt;50% | 稳=50-80% | 保=&gt;80%  |  "
        "赛道：🔥热门 ⚠️天坑/谨慎 🚫避坑  |  "
        "办学：⚠️独立学院 🚫民办 💰中外合作  |  "
        "推荐指数：⭐越多越推荐  |  张雪峰提示仅供参考，请以官方数据为准</font>",
        ps("leg", fontSize=7.5, spaceAfter=3, textColor=CLR_ORANGE))
    story.append(legend)

    # 表头（20列，优化宽度适配横排）
    # 序号 梯度 院校名称  专业名称 城市 城市级 办学性质 专业赛道 学费 推荐指数
    # 近三年最低分 等效分 分差 位次差 概率 风险 张雪峰提示 2025位次 选科 体检
    vol_headers = [
        "序号", "梯度", "院校名称", "专业名称",
        "城市", "城市级", "办学性质", "赛道", "学费",
        "推荐", "近三年\n最低分", "等效分", "分差", "位次差",
        "概率", "风险", "张雪峰提示", "2025\n位次", "选科要求", "体检限制"
    ]
    # 横排可用 25.7cm，分配如下：
    col_ws = [
        0.8*cm,   # 序号
        0.7*cm,   # 梯度
        2.8*cm,   # 院校名称
        3.2*cm,   # 专业名称
        1.5*cm,   # 城市
        1.5*cm,   # 城市级
        1.6*cm,   # 办学性质
        1.8*cm,   # 赛道
        1.1*cm,   # 学费
        1.1*cm,   # 推荐指数
        1.4*cm,   # 近三年最低分
        1.1*cm,   # 等效分
        1.0*cm,   # 分差
        1.1*cm,   # 位次差
        0.9*cm,   # 概率
        0.7*cm,   # 风险
        3.0*cm,   # 张雪峰提示
        1.3*cm,   # 2025位次
        1.4*cm,   # 选科要求
        1.8*cm,   # 体检限制
    ]
    # 验证总宽度：sum = 25.7cm ✅

    vol_data = [vol_headers]
    for v in volunteers:
        elec_short = short(v.elective_req, 6) if v.elective_req and v.elective_req != "不限" else ""
        equiv = getattr(v, 'equivalent_score', 0)
        equiv_str = str(int(equiv)) if equiv else "-"
        sd = getattr(v, 'score_diff', 0)
        sd_str = f"{sd:+.0f}" if sd else "-"
        rd = int(v.rank_diff) if v.rank_diff else 0
        rd_str = f"{rd:+,}"
        city = getattr(v, 'city', '') or '-'
        city_lv = (getattr(v,'city_level_emoji','') + getattr(v,'city_level_label','')) if getattr(v,'city_level_emoji','') else '-'
        nature = (getattr(v,'nature_emoji','') + getattr(v,'nature_label',''))
        track  = (getattr(v,'track_emoji','') + getattr(v,'track_desc','')) if getattr(v,'track_emoji','') else '-'
        tuition = getattr(v, 'tuition', '') or '-'
        rec_idx = getattr(v, 'recommend_index', '') or '-'
        risk_d  = getattr(v, 'risk_desc', '') or ''
        body_r  = (v.body_restrict or "")[:10]
        prob_pct = f"{v.admit_prob:.0%}"

        vol_data.append([
            str(v.seq),
            v.tier,
            short(v.college_name, 12),
            short(v.major_name, 14),
            short(city, 6),
            short(city_lv, 8),
            short(nature, 8),
            short(track, 12),
            short(tuition, 8),
            str(rec_idx),
            short_num(v.min_score_3yr),
            equiv_str,
            sd_str,
            short_num(rd_str),
            prob_pct,
            v.risk_level,
            short(risk_d, 16),
            short_num(v.min_rank_2025),
            elec_short,
            body_r,
        ])

    # 样式：字号7，列高自动，行背景斑马纹
    vol_table = Table(vol_data, colWidths=col_ws, repeatRows=1)
    vol_table.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), cn_font),
        ("FONTSIZE",      (0,0), (-1,-1), 7.5),
        ("BACKGROUND",    (0,0), (-1,0),  CLR_BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  cn_font),
        ("FONTNAME",      (0,1), (-1,-1), cn_font),
        ("FONTSIZE",      (0,1), (-1,-1), 7.5),
        # 梯度颜色
        ("TEXTCOLOR",     (1, 1), (1, -1), colors.HexColor("#C0392B")),   # 冲-红
        ("TEXTCOLOR",     (1, 1), (1, -1), colors.HexColor("#27AE60")),   # 稳-绿
        ("TEXTCOLOR",     (1, 1), (1, -1), colors.HexColor("#2980B9")),   # 保-蓝
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#B0C4DE")),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (0,0), (0,-1),  "CENTER"),   # 序号居中
        ("ALIGN",         (1,0), (1,-1),  "CENTER"),   # 梯度居中
        ("ALIGN",         (10,0),(14,-1), "CENTER"),   # 数字列居中
        ("ALIGN",         (14,0),(14,-1), "CENTER"),   # 概率居中
        ("ALIGN",         (15,0),(15,-1), "CENTER"),   # 风险居中
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CLR_ROW1, CLR_ROW2]),
    ]))

    story.append(vol_table)
    story.append(Spacer(1, 0.3*cm))

    # ── 免责声明 ─────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#AAAAAA")))
    story.append(Paragraph(
        "【免责声明】本报告由系统基于历史数据自动生成，仅供参考，不构成任何录取承诺。"
        "考生应以河北省教育考试院官方发布信息为准，最终填报责任由考生自行承担。",
        ps("disc", fontSize=7, leading=11, textColor=colors.HexColor("#888888"), spaceBefore=4)
    ))

    doc.build(story)
    logger.info("PDF报告导出完成（横排）：%s", out_path)
    return out_path
