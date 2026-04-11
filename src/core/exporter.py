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
    导出志愿分析报告PDF
    Returns: 输出文件路径
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)
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

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontName=cn_font, fontSize=16, leading=22,
                                  alignment=1, spaceAfter=12, textColor=colors.HexColor("#1B5E9B"))
    h2_style    = ParagraphStyle("h2", fontName=cn_font, fontSize=12, leading=18,
                                  spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#2E86C1"))
    body_style  = ParagraphStyle("body", fontName=cn_font, fontSize=9, leading=14,
                                  spaceAfter=4)

    story = []

    # 封面标题
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("河北省高考志愿填报分析报告", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E86C1")))
    story.append(Spacer(1, 0.3*cm))

    # 考生基本信息
    story.append(Paragraph("一、考生基本信息", h2_style))
    info_data = [
        ["姓名", student.get("name", "考生"),
         "预估分数", f"{student.get('estimated_score', 0)}分"],
        ["首选科目", student.get("subject_first", "物理"),
         "政策加分", f"+{student.get('extra_score', 0)}分"],
        ["再选科目", f"{student.get('subject_elective1','')}、{student.get('subject_elective2','')}",
         "性别", student.get("gender", "男")],
        ["色觉状态", student.get("color_vision", "正常"),
         "裸眼视力", f"{student.get('naked_eye_vision', '5.0')}"],
        ["身高", f"{student.get('height_cm', 170)}cm",
         "体重", f"{student.get('weight_kg', 60)}kg"],
        ["考生位次", f"{student.get('student_rank', 0):,}名" if student.get('student_rank', 0) else "未知",
         "生成时间", datetime.now().strftime('%Y-%m-%d %H:%M')],
    ]
    info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), cn_font),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#D6EAF8")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#D6EAF8")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*cm))

    # 志愿分布统计
    story.append(Paragraph("二、志愿统计", h2_style))
    risk_counts  = {"高": 0, "中": 0, "低": 0}
    for v in volunteers:
        risk_counts[v.risk_level] = risk_counts.get(v.risk_level, 0) + 1

    dist_data = [
        ["风险等级", "数量", "说明"],
        ["高风险（概率<40%）", str(risk_counts.get("高", 0)), "录取概率较低，需谨慎考虑"],
        ["中风险（概率40-70%）", str(risk_counts.get("中", 0)), "录取概率中等"],
        ["低风险（概率>70%）", str(risk_counts.get("低", 0)), "录取概率较高"],
        ["合计", str(len(volunteers)), ""],
    ]
    dist_table = Table(dist_data, colWidths=[4*cm, 3*cm, 9*cm])
    dist_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), cn_font),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1B5E9B")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
        ("FONTNAME", (0,-1), (-1,-1), cn_font),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#ECF0F1")),
    ]))
    story.append(dist_table)
    story.append(Spacer(1, 0.3*cm))

    # 志愿明细表（最多显示96行）
    story.append(Paragraph("三、96个志愿明细（张雪峰视角增强版）", h2_style))
    # 张雪峰提示
    zxf_tip = Paragraph(
        "🔥 热门专业 | ⚠️ 天坑/谨慎专业 | 🚫 避坑专业 | 💰 高学费/中外合作 | 办学性质：⚠️ 独立学院 🚫 民办 💰 中外合作 | 推荐指数：⭐越多越推荐",
        ParagraphStyle("zxf_tip", fontName=cn_font, fontSize=7.5, textColor=colors.HexColor("#E67E22"), spaceBefore=2, spaceAfter=4))
    story.append(zxf_tip)

    vol_headers = [
        "序号", "梯度", "院校名称", "专业名称", "城市", "城市级别", "办学性质", "专业赛道", "学费", "推荐指数",
        "近三年最低分", "等效分", "分差", "位次差", "概率", "风险", "张雪峰提示", "2025位次", "选科", "体检"
    ]
    vol_data = [vol_headers]
    for v in volunteers:
        elec_short = (v.elective_req[:6] if v.elective_req and v.elective_req != "不限" else "")
        equiv_score = getattr(v, 'equivalent_score', 0) or "-"
        score_diff = f"{getattr(v, 'score_diff', 0):+.1f}" if hasattr(v, 'score_diff') else "-"
        city = getattr(v, 'city', '') or '-'
        city_lv = f"{getattr(v,'city_level_emoji','')}{getattr(v,'city_level_label','')}" if getattr(v,'city_level_emoji','') else '-'
        nature = f"{getattr(v,'nature_emoji','')}{getattr(v,'nature_label','')}"
        track = f"{getattr(v,'track_emoji','')}{getattr(v,'track_desc','')}" if getattr(v,'track_emoji','') else '-'
        tuition = getattr(v, 'tuition', '') or '-'
        risk_desc = getattr(v, 'risk_desc', '') or ''
        rec_idx = getattr(v, 'recommend_index', '') or '-'
        vol_data.append([
            str(v.seq), v.tier, v.college_name[:10], v.major_name[:12],
            city[:6], city_lv[:8], nature[:8], track[:12], tuition[:8], rec_idx,
            str(v.min_score_3yr), str(equiv_score), score_diff,
            f"{int(v.rank_diff):+,}", f"{v.admit_prob:.0%}", v.risk_level, risk_desc,
            f"{v.min_rank_2025:,}" if v.min_rank_2025 else "-",
            elec_short, v.body_restrict[:10] if v.body_restrict else ""
        ])
    col_ws = [
        0.6*cm, 0.6*cm, 2.0*cm, 2.5*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.6*cm, 1.0*cm, 0.9*cm,
        1.4*cm, 1.0*cm, 0.8*cm, 1.0*cm, 0.8*cm, 0.6*cm, 1.8*cm, 1.3*cm, 0.8*cm, 1.4*cm
    ]
    vol_table = Table(vol_data, colWidths=col_ws, repeatRows=1)
    row_styles = [
        ("FONTNAME", (0,0), (-1,-1), cn_font),
        ("FONTSIZE", (0,0), (-1,-1), 7),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1B5E9B")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
    ]
    vol_table.setStyle(TableStyle(row_styles))
    story.append(vol_table)
    story.append(Spacer(1, 0.3*cm))

    # 免责声明
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Paragraph(
        "【免责声明】本报告由系统基于历史数据自动生成，仅供参考，不构成任何录取承诺。"
        "考生应以河北省教育考试院官方发布信息为准，最终填报责任由考生自行承担。",
        ParagraphStyle("disclaimer", fontName=cn_font, fontSize=7.5, leading=12,
                       textColor=colors.grey, spaceBefore=6)
    ))

    doc.build(story)
    logger.info("PDF报告导出完成：%s", out_path)
    return out_path
