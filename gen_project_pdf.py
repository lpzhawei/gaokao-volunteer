#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
河北省高考志愿填报系统 2026 — 项目说明文档 PDF 生成脚本
使用 reportlab 生成带格式的专业PDF文档
全部字符串用单引号，避免嵌套双引号问题
"""

import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── 中文字体检测 ──────────────────────────────────────────
FONT_CANDIDATES = [
    ('C:/Windows/Fonts/msyh.ttc',   'msyh'),
    ('C:/Windows/Fonts/simhei.ttf', 'simhei'),
    ('C:/Windows/Fonts/simsun.ttc', 'simsun'),
    ('C:/Windows/Fonts/simkai.ttf', 'simkai'),
]

FONT_NAME = None
for path, name in FONT_CANDIDATES:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            FONT_NAME = name
            print(f'使用字体：{name} ({path})')
            break
        except Exception as e:
            print(f'字体加载失败 {path}: {e}')

BOLD_CANDIDATES = [
    ('C:/Windows/Fonts/msyhbd.ttc', 'msyhbd'),
    ('C:/Windows/Fonts/simhei.ttf', 'simhei'),
]
FONT_BOLD = FONT_NAME
for path, name in BOLD_CANDIDATES:
    if os.path.exists(path):
        try:
            if name != FONT_NAME:
                pdfmetrics.registerFont(TTFont(name, path))
            FONT_BOLD = name
            break
        except:
            pass

if not FONT_NAME:
    print('警告：未找到中文字体')
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'

# ── 颜色常量 ──────────────────────────────────────────────
C_PRIMARY    = colors.HexColor('#1B5E9B')
C_SECONDARY  = colors.HexColor('#2E86C1')
C_ACCENT     = colors.HexColor('#1A6B3A')
C_LIGHT_BLUE = colors.HexColor('#D6EAF8')
C_LIGHT_GREEN= colors.HexColor('#E8F5E9')
C_GRAY       = colors.HexColor('#5D6D7E')
C_CODE_BG    = colors.HexColor('#F0F4F8')
C_BORDER     = colors.HexColor('#BDC3C7')

# ── 样式定义 ──────────────────────────────────────────────
def make_styles():
    s = {}
    s['cover_title'] = ParagraphStyle('cover_title', fontName=FONT_BOLD, fontSize=26,
        textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=10, leading=36)
    s['cover_sub'] = ParagraphStyle('cover_sub', fontName=FONT_NAME, fontSize=14,
        textColor=C_SECONDARY, alignment=TA_CENTER, spaceAfter=6)
    s['h1'] = ParagraphStyle('h1', fontName=FONT_BOLD, fontSize=18, textColor=C_PRIMARY,
        spaceBefore=20, spaceAfter=8, leading=26)
    s['h2'] = ParagraphStyle('h2', fontName=FONT_BOLD, fontSize=14, textColor=C_SECONDARY,
        spaceBefore=14, spaceAfter=6, leading=22)
    s['h3'] = ParagraphStyle('h3', fontName=FONT_BOLD, fontSize=12, textColor=C_ACCENT,
        spaceBefore=10, spaceAfter=4, leading=18)
    s['body'] = ParagraphStyle('body', fontName=FONT_NAME, fontSize=10.5,
        textColor=colors.black, spaceBefore=4, spaceAfter=4, leading=17,
        alignment=TA_JUSTIFY)
    s['bullet'] = ParagraphStyle('bullet', fontName=FONT_NAME, fontSize=10.5,
        textColor=colors.black, spaceBefore=2, spaceAfter=2, leading=16,
        leftIndent=16, bulletIndent=4)
    s['code'] = ParagraphStyle('code', fontName='Courier', fontSize=8.5,
        textColor=colors.HexColor('#2C3E50'), spaceBefore=2, spaceAfter=2,
        leading=13, leftIndent=8, backColor=C_CODE_BG)
    s['notice'] = ParagraphStyle('notice', fontName=FONT_NAME, fontSize=10,
        textColor=colors.HexColor('#7D3C00'), spaceBefore=4, spaceAfter=4,
        leftIndent=10, leading=16)
    return s

# ── 辅助函数 ──────────────────────────────────────────────
def h1(t, s): return Paragraph(t, s['h1'])
def h2(t, s): return Paragraph(t, s['h2'])
def h3(t, s): return Paragraph(t, s['h3'])
def p(t, s):  return Paragraph(t, s['body'])
def sp(n=8):  return Spacer(1, n)
def hr():     return HRFlowable(width='100%', thickness=0.5, color=C_BORDER,
                                 spaceAfter=6, spaceBefore=6)

def bullets(items, s):
    return [Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']) for item in items]

def code_block(lines_list, s):
    result = [sp(4)]
    for line in lines_list:
        safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        result.append(Paragraph(safe, s['code']))
    result.append(sp(4))
    return result

def notice_p(text, s):
    return Paragraph(f'<b>注意：</b> {text}', s['notice'])

def make_table(headers, rows, col_widths, s, header_bg=None):
    if header_bg is None:
        header_bg = C_PRIMARY
    data = [[Paragraph(f'<b><font color="white">{h}</font></b>', s['body']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(cell), s['body']) for cell in row])
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_LIGHT_BLUE, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return tbl

# ── 页眉页脚 ──────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, h - 28, w, 28, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont(FONT_BOLD, 10)
    canvas.drawString(20, h - 19, '河北省高考志愿填报系统 2026')
    canvas.setFont(FONT_NAME, 8.5)
    canvas.drawRightString(w - 20, h - 19, '全项目说明文档 v1.0.0')
    canvas.setFillColor(C_GRAY)
    canvas.setFont(FONT_NAME, 8)
    canvas.drawCentredString(w / 2, 18, f'第 {doc.page} 页  |  版权所有 2026 河北省高考志愿填报系统开发组')
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20, 28, w - 20, 28)
    canvas.restoreState()

# ── 文档内容构建 ──────────────────────────────────────────
def build_document():
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '河北省高考志愿填报系统_项目说明文档.pdf')
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title='河北省高考志愿填报系统_项目说明文档',
        author='开发部 张哥',
    )
    s = make_styles()
    W = A4[0] - 4*cm

    story = []

    # ══ 封面 ══════════════════════════════════════════════
    story.append(sp(60))
    story.append(Paragraph('河北省高考志愿填报系统 2026', s['cover_title']))
    story.append(sp(8))
    story.append(Paragraph('全项目说明文档', s['cover_sub']))
    story.append(sp(40))

    cover_data = [
        [Paragraph('<b>版本</b>', s['body']),      Paragraph('v1.0.0', s['body'])],
        [Paragraph('<b>编制日期</b>', s['body']),   Paragraph('2026-04-03', s['body'])],
        [Paragraph('<b>项目负责人</b>', s['body']), Paragraph('张哥，开发部', s['body'])],
        [Paragraph('<b>目标上线</b>', s['body']),   Paragraph('2026年6月30日前', s['body'])],
        [Paragraph('<b>技术栈</b>', s['body']),
         Paragraph('Python 3.13 · PyQt6 · SQLite · pandas · reportlab', s['body'])],
    ]
    cover_tbl = Table(cover_data, colWidths=[W*0.25, W*0.75])
    cover_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), C_LIGHT_BLUE),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10.5),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(cover_tbl)
    story.append(PageBreak())

    # ══ 第一章 项目概览 ════════════════════════════════════
    story.append(h1('第一章  项目概览', s))
    story.append(hr())
    story.append(h2('1.1  项目背景', s))
    story.append(p(
        '河北省自2021年起推行"3+1+2"新高考改革，本科批次实行平行志愿96个（无专业调剂，退档即滑档）。'
        '考生面临海量数据（每年约2万条录取记录）、多年横向比对、体检政策合规等挑战。'
        '本系统旨在为考生提供智能化、数据驱动的志愿填报辅助决策工具。', s))
    story.append(sp(6))

    story.append(h2('1.2  核心功能', s))
    story.append(make_table(
        ['模块', '功能说明'],
        [
            ['数据管理', '导入2023~2025年河北省招生Excel数据，自动清洗、去重、入库'],
            ['智能推荐', '基于考生位次，按冲/稳/保三梯度生成96个志愿方案'],
            ['合规过滤', '体检限制（色觉/视力/身高体重）、选科要求自动过滤'],
            ['结果导出', '支持Excel（带颜色格式）、PDF（三段式报告）、DOCX三种格式'],
            ['数据查询', '历史录取数据预览、院校信息查询、一分一段表查询'],
        ],
        [W*0.22, W*0.78], s))
    story.append(sp(8))

    story.append(h2('1.3  技术栈', s))
    story.append(make_table(
        ['层次', '技术选型'],
        [
            ['语言', 'Python 3.13'],
            ['GUI框架', 'PyQt6 6.4+'],
            ['数据库', 'SQLite 3（内嵌，无需安装）'],
            ['数据处理', 'pandas 2.0+、numpy 1.24+'],
            ['Excel导出', 'xlsxwriter 3.1+'],
            ['PDF导出', 'reportlab 4.0+'],
            ['Excel读取', 'openpyxl 3.1+'],
            ['打包工具', 'PyInstaller 6.0+'],
        ],
        [W*0.3, W*0.7], s))
    story.append(sp(8))

    story.append(h2('1.4  数据规模', s))
    story.append(make_table(
        ['年份', '科目', '条数', '院校数'],
        [
            ['2023', '物理', '16,864', '1,127'],
            ['2024', '历史', '6,507', '1,100'],
            ['2024', '物理', '18,176', '1,210'],
            ['2025', '历史', '6,535', '1,063'],
            ['2025', '物理', '19,176', '1,218'],
        ],
        [W*0.2, W*0.2, W*0.3, W*0.3], s))
    story.append(sp(4))
    story.extend(bullets([
        '院校信息表：2,221所（公办1,605 / 民办419 / 独立学院197）',
        '一分一段表：2023~2025年 物理+历史均已导入',
        '选科要求：8,072条有要求（化学7,486 / 政治174 / 化学和生物169）',
        '体检限制：935条有记录',
    ], s))
    story.append(PageBreak())

    # ══ 第二章 目录结构 ════════════════════════════════════
    story.append(h1('第二章  项目目录结构', s))
    story.append(hr())
    story.extend(code_block([
        'gaokao_volunteer/',
        '├── main.py                    # 程序入口',
        '├── requirements.txt           # Python依赖清单',
        '├── gaokao.spec                # PyInstaller打包配置',
        '├── build_exe.bat              # 一键打包脚本',
        '├── resources/',
        '│   ├── icon.ico               # 程序主图标（ICO格式）',
        '│   └── icon_16~512.png        # 多尺寸PNG图标',
        '├── data/db/gaokao.db          # SQLite数据库',
        '├── src/',
        '│   ├── core/',
        '│   │   ├── engine.py          # 推荐引擎（~940行）',
        '│   │   └── exporter.py        # 导出模块',
        '│   ├── data/',
        '│   │   ├── database.py        # 数据库管理',
        '│   │   └── importer.py        # Excel数据导入',
        '│   └── gui/',
        '│       ├── main_window.py     # 主窗口',
        '│       ├── input_panel.py     # 信息输入面板',
        '│       ├── data_panel.py      # 数据管理面板',
        '│       └── result_panel.py    # 推荐结果面板',
        '└── dist/河北高考志愿填报系统/',
        '    └── 河北高考志愿填报系统.exe',
    ], s))
    story.append(PageBreak())

    # ══ 第三章 数据库设计 ══════════════════════════════════
    story.append(h1('第三章  数据库设计', s))
    story.append(hr())
    story.append(p(
        '数据库文件：开发模式下为 gaokao_volunteer/data/db/gaokao.db，'
        '打包后迁移到 %LOCALAPPDATA%/GaokaoVolunteer/gaokao.db。'
        '系统启用 PRAGMA foreign_keys = ON，所有外键约束强制执行。', s))
    story.append(sp(6))

    story.append(h2('3.1  表结构总览', s))
    story.append(make_table(
        ['表名', '说明', '核心字段'],
        [
            ['admission_data', '历年录取数据', 'college_name, major_name, year, rank_lowest'],
            ['score_rank', '一分一段表', 'year, subject, score, rank_min'],
            ['colleges', '院校基础信息', 'college_name, province, type, nature'],
            ['student_profiles', '考生档案', 'name, score, subject, electives, body conditions'],
            ['volunteer_plans', '志愿方案', 'student_id, plan_name, created_at'],
            ['volunteer_items', '方案志愿项', 'plan_id, tier, college_name, probability'],
        ],
        [W*0.25, W*0.3, W*0.45], s))
    story.append(sp(8))

    story.append(h2('3.2  admission_data 表（核心）', s))
    story.extend(code_block([
        'CREATE TABLE admission_data (',
        '    id           INTEGER PRIMARY KEY AUTOINCREMENT,',
        '    year         INTEGER NOT NULL,   -- 录取年份',
        '    subject      TEXT NOT NULL,      -- 物理/历史',
        '    college_name TEXT NOT NULL,      -- 院校名（已清洗）',
        '    major_name   TEXT NOT NULL,      -- 专业名',
        '    rank_lowest  INTEGER,            -- 最低录取位次（核心字段）',
        '    score_lowest INTEGER,            -- 最低录取分数',
        '    plan_count   INTEGER,            -- 计划招生数',
        '    province     TEXT,              -- 院校所在省份',
        '    elective_req TEXT,              -- 选科要求',
        '    body_restrict TEXT,             -- 体检限制说明',
        '    UNIQUE(year, subject, batch, college_name, major_name)',
        ');',
    ], s))
    story.append(notice_p(
        'college_code 字段的值是Excel行序号，各年度不一致，'
        '不能跨年作为院校唯一标识。跨年匹配应使用标准化后的 college_name。', s))

    story.append(h2('3.3  student_profiles 表（考生档案）', s))
    story.append(make_table(
        ['字段', '类型', '说明'],
        [
            ['score', 'INTEGER', '高考总分（满分750）'],
            ['subject', 'TEXT', '物理/历史'],
            ['electives', 'TEXT', '选考科目，逗号分隔（如"化学,生物"）'],
            ['rank_min', 'INTEGER', '对应位次（最好名次）'],
            ['color_vision', 'TEXT', '正常/色弱/色盲'],
            ['naked_eye_vision', 'REAL', '裸眼视力（对数视力表，如5.0）'],
            ['height_cm / weight_kg', 'INTEGER', '身高cm / 体重kg'],
            ['rank_reach_pct', 'INTEGER', '冲刺位次放宽百分比（默认20）'],
        ],
        [W*0.3, W*0.2, W*0.5], s))
    story.append(PageBreak())

    # ══ 第四章 数据导入 ════════════════════════════════════
    story.append(h1('第四章  数据导入模块（importer.py）', s))
    story.append(hr())

    story.append(h2('4.1  支持格式', s))
    story.append(p('已适配河北省教育考试院2023~2025年发布的原始Excel文件，具有以下特殊格式：', s))
    story.append(make_table(
        ['格式特点', '处理方式'],
        [
            ['表头位置', '第2行（行索引1），第0行是大标题，第1行是排序说明行'],
            ['列名含换行符', '系统自动去除所有空白字符后匹配'],
            ['院校名含后缀', '自动去除[公办][民办][独立学院][中外合作]'],
            ['2025年位次列', '单独有"2025年位次"列，早年文件无此列'],
            ['2025年一分一段', '含在投档数据Excel的独立Sheet中，自动识别'],
            ['2023年物理', '数据分5个Sheet存储，系统自动合并后去重'],
        ],
        [W*0.3, W*0.7], s))
    story.append(sp(8))

    story.append(h2('4.2  三轮列名匹配策略', s))
    story.extend(bullets([
        '第一轮：精确匹配（去空白后完全一致）',
        '第二轮：包含匹配（列名包含关键词，如最低位次）',
        '第三轮：宽松匹配（关键词分词匹配）',
    ], s))
    story.append(sp(6))

    story.append(h2('4.3  幂等导入', s))
    story.append(p(
        '每次导入前先按 (year, subject, batch) 删除已有数据，再重新插入，'
        '保证多次导入结果完全一致，不会产生重复数据。', s))
    story.append(PageBreak())

    # ══ 第五章 推荐引擎 ════════════════════════════════════
    story.append(h1('第五章  推荐引擎核心算法（engine.py）', s))
    story.append(hr())
    story.append(p('推荐引擎位于 src/core/engine.py，约940行代码，是系统的核心模块。', s))

    story.append(h2('5.1  多年数据聚合策略', s))
    story.append(p('聚合Key设计：使用"标准化院校名 || 标准化专业名 || 批次"作为跨年匹配的唯一Key。', s))
    story.extend(bullets([
        '标准化规则：去除院校名括号内的城市后缀；去除专业名括号内的方向后缀',
        '年份权重：2025年50%，2024年35%，2023年15%',
        '修复后：72.5%的专业有2~3年数据，11,962个专业具有3年完整数据',
    ], s))
    story.append(sp(6))

    story.append(h2('5.2  过滤规则', s))
    story.append(h3('5.2.1  体检限制过滤', s))
    story.append(make_table(
        ['条件', '过滤专业'],
        [
            ['色盲', '所有色弱+色盲限制专业（美术/绘画/化学/医学/药学等）'],
            ['色弱', '色弱限制专业（化学/化工/药学/生物/医学/公安技术等）'],
            ['裸眼视力 < 5.0', '飞行技术/航海技术/消防工程/刑事科学技术/侦查学'],
            ['裸眼视力 < 4.8', '轮机工程/运动训练/民族传统体育'],
            ['公安类（男）', '身高 < 170cm 或体重 < 50kg'],
            ['公安类（女）', '身高 < 160cm 或体重 < 45kg'],
        ],
        [W*0.3, W*0.7], s))
    story.append(sp(6))

    story.append(h3('5.2.2  选科要求过滤', s))
    story.append(p(
        '仅当专业的必选科目是考生已选科目的子集时，该专业通过过滤。'
        '例如：专业要求化学，考生选了化学+生物则通过；考生选了生物+政治则过滤。', s))
    story.append(sp(6))

    story.append(h2('5.3  录取概率计算', s))
    story.extend(code_block([
        '# rank_diff = student_rank - avg_rank_lowest',
        '# 正值 -> 偏冲刺（考生位次较差），概率较低',
        '# 负值 -> 偏保底（考生位次较好），概率较高',
        '',
        'base_prob = sigmoid(-rank_diff / (rank_std + 2000))',
        'completeness_factor = {1: 0.85, 2: 0.95, 3: 1.0}[years_count]',
        'probability = base_prob * completeness_factor',
    ], s))
    story.append(sp(6))

    story.append(h2('5.4  梯度切分算法（96志愿）', s))
    story.append(p(
        '将候选专业按位次差排序，rank_diff≈0的专业（考生位次与历史最低位次基本持平）'
        '作为锚点放在第30位，然后向两侧分配：', s))
    story.append(make_table(
        ['梯度', '序号范围', '数量', '说明'],
        [
            ['冲（Tier 1）', '第 1~30 位', '30个', '录取难度大，录取概率较低'],
            ['稳（Tier 2）', '第 31~75 位', '45个', '位次匹配，录取稳健'],
            ['保（Tier 3）', '第 76~96 位', '21个', '明显优于历史位次，录取概率高'],
        ],
        [W*0.2, W*0.22, W*0.13, W*0.45], s))
    story.append(sp(6))

    story.append(h2('5.5  综合评分权重', s))
    story.append(make_table(
        ['评分因子', '权重', '说明'],
        [
            ['录取概率', '35%', 'Sigmoid计算的录取概率'],
            ['偏好匹配度', '30%', '省份+专业偏好满足程度'],
            ['位次稳定性', '20%', '历史位次标准差（越小越稳）'],
            ['数据完整度', '15%', '参考年数（1~3年）'],
        ],
        [W*0.25, W*0.15, W*0.6], s))
    story.append(PageBreak())

    # ══ 第六章 GUI设计 ═════════════════════════════════════
    story.append(h1('第六章  GUI 界面设计', s))
    story.append(hr())

    story.append(h2('6.1  主窗口', s))
    story.extend(bullets([
        '窗口尺寸：1200x800 px，最小尺寸 900x600 px',
        '标题栏：渐变背景（#1B5E9B → #2E86C1），金色字体，程序图标',
        '布局：QTabWidget 三标签页（信息输入 / 数据管理 / 推荐结果）',
        '主题色：蓝色系（#1B5E9B 主色，#2E86C1 次色）',
        '图标加载：多尺寸PNG（16~512px）合并为QIcon，兼容高DPI显示',
    ], s))
    story.append(sp(6))

    story.append(h2('6.2  信息输入面板', s))
    story.append(make_table(
        ['控件区域', '包含内容'],
        [
            ['基本信息', '姓名、高考分数、科目（物理/历史）、性别'],
            ['位次信息', '实时显示对应位次，双滑块控制冲刺/保底幅度'],
            ['选科设置', '物理/历史/化学/生物/政治/地理 六科勾选框'],
            ['体检信息', '色觉（正常/色弱/色盲）、裸眼视力、身高、体重'],
            ['专业偏好', '16大方向多选列表'],
            ['省份偏好', '22个省份多选列表（含直辖市）'],
        ],
        [W*0.3, W*0.7], s))
    story.append(sp(6))

    story.append(h2('6.3  推荐结果面板', s))
    story.extend(bullets([
        '结果表格：16列，展示序号/梯度/院校/专业/省份/概率/位次差/参考分等',
        '行颜色：冲=浅红，稳=浅绿，保=浅蓝',
        '橙色高亮：放宽偏好匹配条件后纳入的志愿项（is_relaxed=True）',
        '过滤工具栏：梯度过滤、省份过滤、关键词搜索',
        '统计侧边栏：各梯度数量、平均录取概率',
        '导出按钮：Excel / PDF / DOCX 三种格式导出',
    ], s))
    story.append(PageBreak())

    # ══ 第七章 导出模块 ════════════════════════════════════
    story.append(h1('第七章  导出模块（exporter.py）', s))
    story.append(hr())

    story.append(h2('7.1  Excel导出（xlsxwriter）', s))
    story.extend(bullets([
        '第1~2行：考生基本信息（姓名、分数、科目、位次）',
        '第3行：列标题（加粗蓝色背景）',
        '第4行起：志愿数据，按梯度交替配色',
        '最后两行：图例（颜色含义说明）',
        '工作表：志愿方案（96条）+ 统计分析（各梯度汇总）',
    ], s))
    story.append(sp(6))

    story.append(h2('7.2  PDF导出（reportlab）', s))
    story.extend(bullets([
        '封面：标题、考生信息、生成时间',
        '三节报告：冲刺志愿（30个）/ 稳妥志愿（45个）/ 保底志愿（21个）',
        '末页：免责声明',
        '中文字体自动检测：优先微软雅黑、黑体、宋体',
    ], s))
    story.append(sp(6))

    story.append(h2('7.3  DOCX导出（python-docx）', s))
    story.extend(bullets([
        '标准Word格式，适合打印和存档',
        '包含学生信息表格和志愿明细表格',
        '支持页眉页脚',
    ], s))
    story.append(PageBreak())

    # ══ 第八章 打包部署 ════════════════════════════════════
    story.append(h1('第八章  打包与部署', s))
    story.append(hr())

    story.append(h2('8.1  PyInstaller配置（gaokao.spec）', s))
    story.extend(code_block([
        "a = Analysis(",
        "    ['main.py'],",
        "    datas=[('resources', 'resources')],  # 打包图标资源",
        "    hiddenimports=['openpyxl', 'xlsxwriter', 'reportlab', ...],",
        ")",
        "exe = EXE(",
        "    name='河北高考志愿填报系统',",
        "    icon='resources/icon.ico',",
        "    console=False,   # 无控制台窗口",
        "    upx=True,        # UPX压缩",
        ")",
    ], s))
    story.append(sp(6))

    story.append(h2('8.2  数据库路径适配', s))
    story.append(p(
        '打包后的exe文件会将数据库迁移到 %LOCALAPPDATA%/GaokaoVolunteer/gaokao.db，'
        '确保多用户环境下数据隔离，避免写入受保护的Program Files目录。', s))
    story.append(sp(6))

    story.append(h2('8.3  程序图标', s))
    story.extend(bullets([
        'ICO文件：resources/icon.ico（内含多尺寸）',
        'PNG系列：icon_16/24/32/48/64/128/256/512.png',
        '图标样式：深蓝渐变背景 + 金色学士帽 + "高考志愿"中文',
        '生成脚本：create_icon.py（使用Pillow绘制）',
    ], s))
    story.append(PageBreak())

    # ══ 第九章 录取规则 ════════════════════════════════════
    story.append(h1('第九章  河北省2026年高考录取规则', s))
    story.append(hr())

    story.append(h2('9.1  考试模式', s))
    story.append(make_table(
        ['项目', '说明'],
        [
            ['高考模式', '3+1+2（新高考）'],
            ['总分', '750分'],
            ['首选科目', '物理或历史（100分，原始分计入）'],
            ['再选科目', '从化学/生物/政治/地理中选2科（等级赋分，各100分）'],
            ['语数外', '各150分，合计450分'],
        ],
        [W*0.25, W*0.75], s))
    story.append(sp(8))

    story.append(h2('9.2  本科批平行志愿规则', s))
    story.append(make_table(
        ['规则', '说明'],
        [
            ['志愿数量', '96个平行志愿（专业+院校组合）'],
            ['投档顺序', '按考生位次从高到低，每人只投档一次'],
            ['专业调剂', '无专业调剂，退档即无缘该批次'],
            ['退档后果', '直接滑档到征集志愿或下一批次'],
        ],
        [W*0.25, W*0.75], s))
    story.append(sp(8))

    story.append(h2('9.3  同分排序规则', s))
    story.append(p('同分考生按以下优先级依次比较：', s))
    for i, item in enumerate([
        '语文+数学合计分高者优先',
        '语文或数学单科高者（取最高分科目比较）',
        '外语分高者',
        '首选科目分高者',
        '再选科目中最高分科目高者',
        '再选科目中次高分科目高者',
    ], 1):
        story.append(Paragraph(f'{i}. {item}', s['bullet']))
    story.append(sp(6))

    story.append(h2('9.4  加分政策', s))
    story.append(make_table(
        ['类型', '加分幅度'],
        [
            ['烈士子女', '+20分'],
            ['退役军人（服役期间荣立二等功及以上）', '+20分'],
            ['自主就业退役士兵', '+10分'],
            ['归侨、华侨子女、归侨子女、台湾省籍考生', '+10分'],
        ],
        [W*0.6, W*0.4], s))
    story.append(PageBreak())

    # ══ 第十章 工具脚本 ════════════════════════════════════
    story.append(h1('第十章  工具脚本', s))
    story.append(hr())
    story.append(make_table(
        ['脚本', '用途'],
        [
            ['check_db.py', '数据库内容检查，输出各表统计信息'],
            ['check_score_sheet.py', '验证一分一段数据完整性'],
            ['analyze_province_file.py', '分析院校省份分布，生成报告'],
            ['create_icon.py', '使用Pillow绘制程序图标'],
            ['create_manual_docx.js', '用户手册生成（Node.js + docx库）'],
            ['gen_project_doc.js', '全项目说明文档生成脚本（DOCX版）'],
        ],
        [W*0.38, W*0.62], s))
    story.append(PageBreak())

    # ══ 第十一章 开发环境 ══════════════════════════════════
    story.append(h1('第十一章  开发环境配置', s))
    story.append(hr())

    story.append(h2('11.1  环境要求', s))
    story.extend(bullets([
        '操作系统：Windows 10/11（主要开发环境）',
        'Python：3.13.x',
        'Node.js：24.x（仅用于生成文档）',
        'venv路径：C:/Users/lpzha/WorkBuddy/20260329193053/venv/',
    ], s))
    story.append(sp(6))

    story.append(h2('11.2  安装与运行', s))
    story.extend(code_block([
        '# 1. 创建虚拟环境',
        'python -m venv venv',
        '.\\venv\\Scripts\\activate',
        '',
        '# 2. 安装依赖',
        'pip install -r gaokao_volunteer\\requirements.txt',
        '',
        '# 3. 运行程序',
        'cd gaokao_volunteer',
        '..\\venv\\Scripts\\python.exe main.py',
        '',
        '# 4. 打包exe',
        'build_exe.bat',
    ], s))
    story.append(PageBreak())

    # ══ 第十二章 常见问题 ══════════════════════════════════
    story.append(h1('第十二章  常见问题与维护', s))
    story.append(hr())

    story.append(h2('12.1  常见问题', s))
    faqs = [
        ('程序启动后数据库为空？',
         '首次运行需在"数据管理"面板导入Excel数据文件。'),
        ('推荐结果数量不足96个？',
         '系统已自动进行4轮放宽匹配，若仍不足可调大"冲刺位次放宽%"滑块。'),
        ('部分专业行显示为橙色？',
         '橙色表示该专业是放宽省份或专业偏好限制后纳入的，位次符合但偏好不完全匹配。'),
        ('导出PDF时中文显示为方块？',
         '请确保Windows系统已安装宋体(simsun.ttc)或黑体(simhei.ttf)，系统自动检测。'),
        ('打包后exe在其他电脑无法运行？',
         '目标电脑需安装Visual C++ Redistributable 2019+，或使用NSIS打包完整安装包。'),
    ]
    for q, a in faqs:
        story.append(KeepTogether([
            Paragraph(f'<b>Q：{q}</b>', s['body']),
            Paragraph(f'A：{a}', s['bullet']),
            sp(4),
        ]))

    story.append(h2('12.2  年度数据更新流程', s))
    for i, item in enumerate([
        '下载当年河北省招生Excel文件（通常6月底发布）',
        '通过数据管理面板选择文件，设置年份/科目/批次',
        '点击"开始导入"，等待完成，确认记录数',
        '一分一段表单独导入（若与投档数据分开发布）',
        '旧年度数据（3年前）可根据需要清理，建议保留',
    ], 1):
        story.append(Paragraph(f'{i}. {item}', s['bullet']))
    story.append(PageBreak())

    # ══ 附录 ══════════════════════════════════════════════
    story.append(h1('附录A  依赖清单（requirements.txt）', s))
    story.append(hr())
    story.extend(code_block([
        'pandas>=2.0',
        'openpyxl>=3.1',
        'PyQt6>=6.4',
        'matplotlib>=3.7',
        'reportlab>=4.0',
        'xlsxwriter>=3.1',
        'numpy>=1.24',
        'pyinstaller>=6.0',
        'python-docx>=1.0',
        'Pillow>=10.0',
    ], s))
    story.append(sp(16))

    story.append(h1('附录B  数据库字段映射表', s))
    story.append(hr())
    story.append(make_table(
        ['Excel列名（原始）', '数据库字段', '说明'],
        [
            ['院校名称', 'college_name', '已清洗，去除[公办]等后缀'],
            ['专业名称', 'major_name', '已清洗'],
            ['投档最低位次', 'rank_lowest', '核心排序字段'],
            ['投档最低分', 'score_lowest', '参考分数'],
            ['计划招生数', 'plan_count', '招生计划数'],
            ['选科要求', 'elective_req', '如"化学"、"化学和生物"'],
            ['体检限制', 'body_restrict', '如"色盲不录"'],
            ['院校所在地', 'province', '省份名'],
        ],
        [W*0.3, W*0.28, W*0.42], s))
    story.append(sp(20))
    story.append(p('本文档由系统自动生成。版权所有 2026 河北省高考志愿填报系统开发组', s))

    # ── 生成PDF ─────────────────────────────────────────────
    print('正在生成PDF...')
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    size_kb = os.path.getsize(output_path) / 1024
    print(f'PDF已生成：{output_path}')
    print(f'文件大小：{size_kb:.1f} KB')
    return output_path

if __name__ == '__main__':
    build_document()
