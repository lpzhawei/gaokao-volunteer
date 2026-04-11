"""
生成精美的 PDF 用户手册
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from datetime import datetime
import os

# 注册中文字体
def register_chinese_fonts():
    """注册系统中文字体"""
    # 尝试注册微软雅黑
    font_paths = [
        r"C:\Windows\Fonts\msyh.ttc",  # 微软雅黑
        r"C:\Windows\Fonts\msyhbd.ttc",  # 微软雅黑粗体
        r"C:\Windows\Fonts\simsun.ttc",  # 宋体
        r"C:\Windows\Fonts\simhei.ttf",  # 黑体
    ]
    
    registered = []
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_name = os.path.basename(font_path).replace('.ttc', '').replace('.ttf', '')
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                registered.append(font_name)
            except Exception as e:
                print(f"注册字体失败 {font_path}: {e}")
    
    return registered

# 全局字体名称
CHINESE_FONT = 'msyh'  # 微软雅黑
CHINESE_FONT_BOLD = 'msyhbd'  # 微软雅黑粗体

# 颜色定义
PRIMARY_COLOR = HexColor("#1B5E9B")      # 主色调：深蓝
SECONDARY_COLOR = HexColor("#2E86AB")    # 次色调：中蓝
ACCENT_COLOR = HexColor("#E74C3C")       # 强调色：红色
LIGHT_BG = HexColor("#F8F9FA")           # 浅背景
DARK_TEXT = HexColor("#2C3E50")          # 深色文字

def create_styles():
    """创建自定义样式"""
    styles = getSampleStyleSheet()
    
    # 封面标题
    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=28,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=20,
        leading=34
    ))
    
    # 封面副标题
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName=CHINESE_FONT,
        fontSize=14,
        textColor=SECONDARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=10
    ))
    
    # 章节标题
    styles.add(ParagraphStyle(
        name='ChapterTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=20,
        textColor=PRIMARY_COLOR,
        spaceBefore=20,
        spaceAfter=15,
        leading=26
    ))
    
    # 小节标题
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=14,
        textColor=SECONDARY_COLOR,
        spaceBefore=15,
        spaceAfter=8,
        leading=18
    ))
    
    # 正文
    styles.add(ParagraphStyle(
        name='Body',
        fontName=CHINESE_FONT,
        fontSize=11,
        textColor=DARK_TEXT,
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6,
        leading=16,
        firstLineIndent=22  # 首行缩进
    ))
    
    # 列表项
    styles.add(ParagraphStyle(
        name='ListItem',
        fontName=CHINESE_FONT,
        fontSize=11,
        textColor=DARK_TEXT,
        spaceBefore=3,
        spaceAfter=3,
        leading=15,
        leftIndent=15
    ))
    
    # 提示框
    styles.add(ParagraphStyle(
        name='TipText',
        fontName=CHINESE_FONT,
        fontSize=10,
        textColor=DARK_TEXT,
        spaceBefore=8,
        spaceAfter=8,
        leading=14,
        leftIndent=10,
        rightIndent=10
    ))
    
    # 脚注
    styles.add(ParagraphStyle(
        name='Footer',
        fontName=CHINESE_FONT,
        fontSize=9,
        textColor=HexColor("#7F8C8D"),
        alignment=TA_CENTER
    ))
    
    return styles


def add_header_footer(canvas, doc):
    """添加页眉页脚"""
    canvas.saveState()
    
    # 页眉
    canvas.setStrokeColor(PRIMARY_COLOR)
    canvas.setLineWidth(2)
    canvas.line(2*cm, A4[1] - 1.5*cm, A4[0] - 2*cm, A4[1] - 1.5*cm)
    
    canvas.setFont(CHINESE_FONT, 9)
    canvas.setFillColor(PRIMARY_COLOR)
    canvas.drawString(2*cm, A4[1] - 1.2*cm, "河北省高考志愿填报系统")
    canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.2*cm, "用户手册")
    
    # 页脚
    canvas.setStrokeColor(PRIMARY_COLOR)
    canvas.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)
    
    canvas.setFillColor(HexColor("#7F8C8D"))
    canvas.drawString(2*cm, 1*cm, f"版本 1.0.0 · {datetime.now().strftime('%Y年%m月')}")
    canvas.drawRightString(A4[0] - 2*cm, 1*cm, f"第 {doc.page} 页")
    
    canvas.restoreState()


def create_tip_box(text, styles):
    """创建提示框"""
    tip_data = [[Paragraph(f"<b>💡 提示：</b>{text}", styles['TipText'])]]
    tip_table = Table(tip_data, colWidths=[15*cm])
    tip_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#E8F4FD")),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return tip_table


def create_warning_box(text, styles):
    """创建警告框"""
    warn_data = [[Paragraph(f"<b>⚠️ 注意：</b>{text}", styles['TipText'])]]
    warn_table = Table(warn_data, colWidths=[15*cm])
    warn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#FDEDEC")),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return warn_table


def build_manual():
    """构建手册内容"""
    styles = create_styles()
    story = []
    
    # ═══════════════════════════════════════════════════════
    # 封面
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 5*cm))
    story.append(Paragraph("河北省高考志愿填报系统", styles['CoverTitle']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("用户手册", styles['CoverTitle']))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("版本 2.1.0 | 张雪峰视角增强版", styles['CoverSubtitle']))
    story.append(Paragraph(datetime.now().strftime("%Y年%m月"), styles['CoverSubtitle']))
    story.append(Spacer(1, 4*cm))
    
    # 封面说明
    cover_desc = """
    本系统基于河北省2026年高考"3+1+2"新高考模式设计，
    专为河北省高考考生提供科学、精准的志愿填报参考建议。
    """
    story.append(Paragraph(cover_desc.strip(), styles['CoverSubtitle']))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════
    # 目录
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("目录", styles['ChapterTitle']))
    story.append(Spacer(1, 0.5*cm))
    
    toc_items = [
        "一、系统简介",
        "二、安装与启动",
        "三、操作流程",
        "    3.1 录入考生信息",
        "    3.2 设置筛选条件",
        "    3.3 生成志愿方案",
        "    3.4 查看分析结果",
        "    3.5 导出报告文件",
        "    3.6 张雪峰视角解读",
        "    3.7 六边形分析图",
        "四、推荐算法说明",
        "五、注意事项",
        "六、常见问题",
        "七、张雪峰避坑指南",
    ]
    
    for item in toc_items:
        story.append(Paragraph(item, styles['ListItem']))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════
    # 一、系统简介
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("一、系统简介", styles['ChapterTitle']))
    
    story.append(Paragraph(
        "河北省高考志愿填报系统是一款专为河北省2026届高考考生设计的智能志愿填报辅助工具。"
        "系统基于河北省近三年（2023-2025年）真实录取数据，结合\"3+1+2\"新高考模式特点，"
        "为考生提供科学、精准的志愿填报参考建议。",
        styles['Body']
    ))
    
    story.append(Paragraph("核心功能", styles['SectionTitle']))
    
    features = [
        "<b>智能推荐</b>：基于位次差算法，自动生成冲稳保梯度志愿方案",
        "<b>数据全面</b>：收录2023-2025年本科批完整录取数据，含城市、专业赛道等 enrichment 信息",
        "<b>张雪峰视角</b>：专业赛道分类（热门/天坑）、城市分级（北上广/二线）、办学性质醒目提示",
        "<b>精准过滤</b>：支持选科要求、体检限制（可报/慎报双重提示）、省份偏好等多维度筛选",
        "<b>六边形分析图</b>：就业率、薪资、考研、考公、城市机会、专业热度六维可视化对比",
        "<b>一键导出</b>：支持导出Excel志愿表和PDF分析报告（含张雪峰视角标注）",
    ]
    for f in features:
        story.append(Paragraph(f"• {f}", styles['ListItem']))
    
    story.append(Paragraph("适用对象", styles['SectionTitle']))
    story.append(Paragraph(
        "本系统适用于河北省2026届参加普通高考的物理类和历史类考生。"
        "艺术类、体育类、对口升学等特殊类型招生不在本系统服务范围内。",
        styles['Body']
    ))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════
    # 二、安装与启动
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("二、安装与启动", styles['ChapterTitle']))
    
    story.append(Paragraph("系统要求", styles['SectionTitle']))
    story.append(Paragraph(
        "操作系统：Windows 10/11（64位）<br/>"
        "硬盘空间：约200MB可用空间<br/>"
        "显示器分辨率：1280×720及以上",
        styles['Body']
    ))
    
    story.append(Paragraph("安装步骤", styles['SectionTitle']))
    
    install_steps = [
        "双击运行安装程序 HebeiGaokaoVolunteer_Setup_v1.0.0.exe",
        "按照安装向导提示完成安装（建议使用默认路径）",
        "安装完成后，桌面会自动创建快捷方式",
        "双击桌面快捷方式即可启动程序",
    ]
    for i, step in enumerate(install_steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles['ListItem']))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(create_tip_box(
        "首次启动可能需要几秒钟加载数据库，请耐心等待。",
        styles
    ))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════
    # 三、操作流程
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("三、操作流程", styles['ChapterTitle']))
    
    story.append(Paragraph(
        "系统操作流程分为五个步骤：录入考生信息 → 设置筛选条件 → 生成志愿方案 → 查看分析结果 → 导出报告文件。",
        styles['Body']
    ))
    
    # 3.1 录入考生信息
    story.append(Paragraph("3.1 录入考生信息", styles['SectionTitle']))
    
    story.append(Paragraph(
        "在左侧\"考生信息\"面板中，完整填写以下信息：",
        styles['Body']
    ))
    
    info_items = [
        "<b>基本信息</b>：姓名、性别",
        "<b>高考成绩</b>：预估分数、政策加分（如有）",
        "<b>选科情况</b>：首选科目（物理/历史）、再选科目（两门）",
        "<b>体检信息</b>：色觉状态、裸眼视力、身高、体重",
    ]
    for item in info_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(create_warning_box(
        "体检信息会影响部分专业的录取资格，请如实填写。色盲/色弱考生将被自动过滤受限专业。",
        styles
    ))
    
    # 3.2 设置筛选条件
    story.append(Paragraph("3.2 设置筛选条件", styles['SectionTitle']))
    
    story.append(Paragraph(
        "在左侧\"筛选条件\"面板中，根据个人偏好设置：",
        styles['Body']
    ))
    
    filter_items = [
        "<b>目标批次</b>：本科批（默认）、本科提前批",
        "<b>偏好专业</b>：勾选感兴趣的专业方向（可多选）",
        "<b>偏好省份</b>：勾选目标就读省份（可多选）",
        "<b>院校类型</b>：是否接受民办院校、中外合作办学",
    ]
    for item in filter_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(create_tip_box(
        "筛选条件越宽松，推荐的志愿数量越多；条件越严格，推荐结果越精准。",
        styles
    ))
    
    # 3.3 生成志愿方案
    story.append(Paragraph("3.3 生成志愿方案", styles['SectionTitle']))
    
    story.append(Paragraph(
        "点击左下角\"生成志愿\"按钮，系统将自动进行智能推荐。"
        "推荐过程约需5-10秒，进度条会实时显示处理进度。",
        styles['Body']
    ))
    
    story.append(Paragraph(
        "生成完成后，右侧结果面板会显示推荐的96个平行志愿方案，"
        "包含院校名称、专业名称、近三年录取分数、位次差、录取概率等详细信息。",
        styles['Body']
    ))
    
    # 3.4 查看分析结果
    story.append(Paragraph("3.4 查看分析结果", styles['SectionTitle']))
    
    story.append(Paragraph(
        "结果面板上方显示考生基本信息卡片，包括：",
        styles['Body']
    ))
    
    result_items = [
        "预估分数、考生位次（基于2025年一分一段表）",
        "选科情况、体检信息",
    ]
    for item in result_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))
    
    story.append(Paragraph(
        "志愿列表按梯度（冲/稳/保）排序，每条志愿包含：",
        styles['Body']
    ))
    
    detail_items = [
        "<b>梯度标识</b>：冲（红色）、稳（绿色）、保（蓝色）",
        "<b>城市标签</b>：🔴一线城市 🟠新一线 🟡二线 🟢三线 🔵四五线，一目了然城市机会",
        "<b>办学性质</b>：🏛️公办 ⚠️独立学院（母体不保证） 🚫民办（学费高） 💰中外合作（学费昂贵）",
        "<b>专业赛道</b>：🔥热门赛道（计算机/医学/公安） 🟡普通赛道 ⚠️天坑赛道（生化环材/普通师范） 🚫避坑赛道（哲学/农学）",
        "<b>学费提示</b>：中外合作/高学费专业自动标注 💰 警告",
        "<b>张雪峰风险描述</b>：🟢稳妥 🟠可冲 🔴高冲 ⚫盲冲，家长能看懂的表述",
        "<b>近三年数据</b>：最低分、平均分、最低位次",
        "<b>录取概率</b>：基于位次差计算的概率值",
        "<b>选科要求</b>：专业对再选科目的要求（紫色标注）",
        "<b>体检限制</b>：专业的身体条件要求（红色标注）",
    ]
    for item in detail_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))
    
    # 3.5 导出报告文件
    story.append(Paragraph("3.5 导出报告文件", styles['ChapterTitle']))
    
    story.append(Paragraph(
        "点击结果面板底部的导出按钮，可选择导出格式：",
        styles['Body']
    ))
    
    export_items = [
        "<b>导出Excel</b>：生成志愿表Excel文件，包含完整志愿列表和考生信息，可用于进一步筛选和打印",
        "<b>导出PDF</b>：生成志愿分析报告PDF文件，包含统计图表和详细分析，适合正式存档",
    ]
    for item in export_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(create_tip_box(
        "导出文件默认保存在 %LOCALAPPDATA%\\河北高考志愿填报系统\\output\\ 目录下。",
        styles
    ))
    
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # 3.6 张雪峰视角解读
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("3.6 张雪峰视角解读", styles['ChapterTitle']))

    story.append(Paragraph(
        "系统在推荐结果中融入了张雪峰式的志愿填报思路，帮助家长快速识别高价值志愿和潜在风险：",
        styles['Body']
    ))

    story.append(Paragraph("专业赛道分类", styles['SectionTitle']))
    track_items = [
        "<b>🔥 热门赛道</b>：计算机/电子信息/口腔医学/公安类 — 就业前景好，建议优先考虑",
        "<b>🟡 普通赛道</b>：大部分工科/商科/管理 — 就业稳定，可根据兴趣选择",
        "<b>⚠️ 天坑赛道</b>：生化环材/普通师范/理学基础 — 就业难度大，若非真爱请谨慎",
        "<b>🚫 避坑赛道</b>：哲学/历史/农学（无特定背景）— 普通家庭强烈不建议",
    ]
    for item in track_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))

    story.append(Paragraph("城市分级原则", styles['SectionTitle']))
    city_items = [
        "<b>🔴 一线城市（北京/上海/广州/深圳）</b>：就业机会多、薪资高，建议优先考虑",
        "<b>🟠 新一线城市（成都/杭州/武汉/南京等）</b>：发展迅速，机会较多",
        "<b>🟡 二线省会城市</b>：综合性价比高，省内高校多在本省有优势",
        "<b>🟢 三线及以下</b>：适合保底，省内院校在本省就业有一定优势",
    ]
    for item in city_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))

    story.append(Paragraph("办学性质提示", styles['SectionTitle']))
    nature_items = [
        "<b>🏛️ 公办院校</b>：学费低（5000-8000元/年），优先考虑",
        "<b>⚠️ 独立学院</b>：母体高校不保证，推荐度低，谨慎选择",
        "<b>🚫 民办院校</b>：学费高（1-3万/年），就业认可度低，普通家庭不建议",
        "<b>💰 中外合作办学</b>：学费昂贵（5-20万/年），家庭条件一般勿选",
    ]
    for item in nature_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))

    story.append(Paragraph("风险描述翻译（张雪峰式）", styles['SectionTitle']))
    risk_items = [
        "<b>🟢 稳妥</b>（概率≥90%）：基本能上，去了不会后悔",
        "<b>🟠 可冲</b>（概率50-90%）：有希望，但要做好保底准备",
        "<b>🔴 高冲</b>（概率25-50%）：风险较大，家里条件允许才冲",
        "<b>⚫ 盲冲</b>（概率<25%）：不建议，纯属浪费志愿",
    ]
    for item in risk_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))

    story.append(Paragraph("体检限制：可报/慎报双重提示", styles['SectionTitle']))
    story.append(Paragraph(
        "系统会根据考生输入的色觉、视力、身高体重信息，智能判断哪些专业可以报考、"
        "哪些专业存在风险，并在志愿表中以⚠️/❌标识。",
        styles['Body']
    ))

    story.append(create_tip_box(
        "张雪峰提醒：体检受限≠完全不能报！系统会告诉你哪些专业可以放心填报。",
        styles
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # 3.7 六边形分析图
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("3.7 六边形分析图", styles['ChapterTitle']))

    story.append(Paragraph(
        "点击结果面板中的「六边形分析图」按钮，可生成张雪峰式的六维分析图，"
        "直观对比多个院校/专业的综合表现。",
        styles['Body']
    ))

    hex_items = [
        "<b>就业率</b>：该专业/院校的毕业生就业情况",
        "<b>薪资水平</b>：参考城市薪资水平估算",
        "<b>考研比例</b>：该专业读研深造的比例（生化环材、理学等基础学科考研比例高）",
        "<b>考公比例</b>：该专业考公的友好程度（法学、汉语言、财经类考公机会多）",
        "<b>城市机会</b>：院校所在城市的就业和发展机会",
        "<b>专业热度</b>：该专业近年报考热度（计算机/医学持续热门）",
    ]
    for item in hex_items:
        story.append(Paragraph(f"• {item}", styles['ListItem']))

    story.append(Paragraph(
        "六边形分析图有两种模式：<b>Top5志愿对比</b>（推荐）和<b>单个志愿详情</b>。"
        "系统支持选择任意志愿进行详细分析。",
        styles['Body']
    ))

    story.append(create_tip_box(
        "六边形分析图的数据基于专业赛道统计估算，非官方数据，仅供趋势参考。",
        styles
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # 四、推荐算法说明
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("四、推荐算法说明", styles['ChapterTitle']))
    
    story.append(Paragraph("排序规则", styles['SectionTitle']))
    
    story.append(Paragraph(
        "系统采用\"位次差驱动\"的排序算法，核心指标为：",
        styles['Body']
    ))
    
    story.append(Paragraph(
        "<b>位次差 = 考生位次 - 专业近三年平均最低位次</b>",
        styles['ListItem']
    ))
    
    story.append(Paragraph(
        "位次差为正，表示考生位次低于专业录取位次，属于冲刺区间；"
        "位次差为负，表示考生位次高于专业录取位次，属于保底区间。"
        "系统按位次差从大到小排序，找到位次差≈0的锚点作为分界线。",
        styles['Body']
    ))
    
    story.append(Paragraph("梯度分配", styles['SectionTitle']))
    
    # 梯度表格（使用 Paragraph 支持中文）
    gradient_data = [
        [Paragraph("<b>梯度</b>", styles['Body']), Paragraph("<b>位置</b>", styles['Body']), 
         Paragraph("<b>数量</b>", styles['Body']), Paragraph("<b>说明</b>", styles['Body'])],
        [Paragraph("冲刺", styles['Body']), Paragraph("第1~30条", styles['Body']), 
         Paragraph("30个", styles['Body']), Paragraph("位次差为正，录取概率较低但有希望", styles['Body'])],
        [Paragraph("稳妥", styles['Body']), Paragraph("第31~75条（默认）", styles['Body']), 
         Paragraph("45个（默认）", styles['Body']), Paragraph("位次差接近0，录取概率较高", styles['Body'])],
        [Paragraph("保底", styles['Body']), Paragraph("第76~96条（默认）", styles['Body']), 
         Paragraph("21个（默认）", styles['Body']), Paragraph("位次差为负，录取概率很高", styles['Body'])],
    ]
    
    gradient_table = Table(gradient_data, colWidths=[2.5*cm, 3*cm, 2*cm, 7*cm])
    gradient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7")),
        ('BACKGROUND', (0, 1), (-1, 1), HexColor("#FADBD8")),  # 冲刺-浅红
        ('BACKGROUND', (0, 2), (-1, 2), HexColor("#D5F5E3")),  # 稳妥-浅绿
        ('BACKGROUND', (0, 3), (-1, 3), HexColor("#D6EAF8")),  # 保底-浅蓝
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(gradient_table)
    
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        "<b>冲稳保比例随考生策略自动调整：</b>富裕家庭→冲42个（多冲好城市）；"
        "普通家庭→冲29个（均衡策略）；困难家庭→冲20个（多保底+就业导向）。"
        "比例调整不影响\u201C第30位锚点\u201D——锚点始终固定在考生位次附近。",
        styles['Body']
    ))
    
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("过滤规则", styles['SectionTitle']))
    
    story.append(Paragraph(
        "系统自动应用以下过滤规则，确保推荐的志愿符合考生实际情况：",
        styles['Body']
    ))
    
    filter_rules = [
        "<b>位次范围</b>：仅推荐考生位次±50000范围内的专业",
        "<b>选科要求</b>：过滤不符合考生再选科目的专业",
        "<b>体检限制</b>：色盲/色弱考生自动过滤受限专业",
        "<b>院校类型</b>：根据考生偏好过滤民办/中外合作院校",
        "<b>省份偏好</b>：优先推荐指定省份的院校",
    ]
    for rule in filter_rules:
        story.append(Paragraph(f"• {rule}", styles['ListItem']))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════
    # 五、注意事项
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("五、注意事项", styles['ChapterTitle']))
    
    story.append(Paragraph("数据说明", styles['SectionTitle']))
    
    data_notes = [
        "本系统使用的历史数据为2023-2025年河北省本科批平行志愿投档情况，仅供参考",
        "每年的招生计划、录取分数线会有变化，请以河北省教育考试院公布的信息为准",
        "推荐结果仅为辅助参考，最终志愿填报请结合个人实际情况综合判断",
    ]
    for note in data_notes:
        story.append(Paragraph(f"• {note}", styles['ListItem']))
    
    story.append(Paragraph("填报建议", styles['SectionTitle']))
    
    tips = [
        "建议在正式填报前多次模拟，熟悉系统操作和推荐结果",
        "96个志愿可不必填满，但建议充分利用志愿容量",
        "冲刺志愿录取概率较低，稳妥和保底志愿是录取的关键",
        "注意查看专业的选科要求和体检限制，避免无效填报",
        "建议将导出的志愿表与家人、老师讨论后再做最终决定",
    ]
    for tip in tips:
        story.append(Paragraph(f"• {tip}", styles['ListItem']))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(create_warning_box(
        "河北省新高考模式无专业调剂，投档后如因身体条件或单科成绩不符被退档，只能参加征集志愿。请务必核实体检限制！",
        styles
    ))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════
    # 六、常见问题
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("六、常见问题", styles['ChapterTitle']))
    
    faqs = [
        {
            "q": "Q：预估分数如何确定？",
            "a": "A：可参考平时模拟考试成绩，或使用河北省2025年一分一段表查询对应位次后反推分数。建议保守估计，略低于模拟考试平均水平。"
        },
        {
            "q": "Q：为什么推荐的专业数量不足96个？",
            "a": "A：可能原因：① 位次范围过窄，符合条件的专业有限；② 筛选条件过严，建议放宽省份或院校类型限制；③ 选科组合可选专业较少（如不选化学的物理类考生）。"
        },
        {
            "q": "Q：位次差为负为什么还显示高风险？",
            "a": "A：风险等级综合考虑位次差和历年录取波动。部分专业录取位次波动较大，即使位次差为负也存在一定风险。"
        },
        {
            "q": "Q：色弱考生哪些专业不能报考？",
            "a": "A：色弱受限专业包括：化学类、化工与制药类、药学类、生物科学类、医学类、公安技术类、地质学类等。具体以《普通高等学校招生体检工作指导意见》为准。"
        },
        {
            "q": "Q：导出的文件在哪里找？",
            "a": "A：导出文件默认保存在 %LOCALAPPDATA%\\河北高考志愿填报系统\\output\\ 目录。可在文件资源管理器地址栏直接粘贴此路径打开。"
        },
    ]
    
    for faq in faqs:
        story.append(Paragraph(faq["q"], styles['SectionTitle']))
        story.append(Paragraph(faq["a"], styles['Body']))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # 七、张雪峰避坑指南（常见错误清单）
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("七、张雪峰避坑指南", styles['ChapterTitle']))

    story.append(Paragraph(
        "以下内容综合了张雪峰老师的核心观点，供家长和考生参考，"
        "希望帮助普通家庭的孩子少走弯路、选对赛道。",
        styles['Body']
    ))

    story.append(Paragraph("❌ 常见错误1：只看学校名气，不看专业出路", styles['SectionTitle']))
    story.append(Paragraph(
        "同样的分数，能上普通985的天坑专业，也能上强势211的热门专业。"
        "张雪峰观点：对于普通家庭的孩子，专业出路比学校名气更重要。"
        "计算机、电子信息、口腔医学等专业的就业和薪资，远好于生化环材等天坑专业。",
        styles['Body']
    ))

    story.append(Paragraph("❌ 常见错误2：盲目冲北上广，不考虑性价比", styles['SectionTitle']))
    story.append(Paragraph(
        "北京、上海的分数极高，但如果只能上普通专业，不如选择新一线城市（成都、杭州、武汉）的强势专业。"
        "张雪峰观点：城市 > 学校 > 专业。一线城市是好，但二线省会的性价比更高。",
        styles['Body']
    ))

    story.append(Paragraph("❌ 常见错误3：选独立学院/民办院校当保底", styles['SectionTitle']))
    story.append(Paragraph(
        "XX大学XX学院（独立学院）和母体大学完全不是一回事！"
        "毕业证上写的是独立学院的名称，用人单位HR心里有数。"
        "张雪峰观点：独立学院和民办院校的就业认可度远低于公办院校，普通家庭强烈不建议。",
        styles['Body']
    ))

    story.append(Paragraph('❌ 常见错误4：选中外合作办学"凑分数"', styles['SectionTitle']))
    story.append(Paragraph(
        "中外合作办学收费5-20万/年，对普通家庭是沉重负担。"
        "且部分中外合作专业的教学质量和就业质量并不理想。"
        "张雪峰观点：家里没矿，不要碰中外合作办学！",
        styles['Body']
    ))

    story.append(Paragraph("❌ 常见错误5：忽视体检限制导致退档", styles['SectionTitle']))
    story.append(Paragraph(
        "河北省新高考无专业调剂，退档即滑档。"
        "每年都有考生因色弱/色盲被医学类专业退档，因身高不足被公安类退档。"
        "张雪峰观点：填报前务必核实体检限制，本系统会提供可报/慎报双重提示。",
        styles['Body']
    ))

    story.append(Paragraph("✅ 正确思路：城市+赛道+就业三维评估", styles['SectionTitle']))
    correct_tips = [
        "<b>城市</b>：优先考虑新一线及以上城市，次选二线省会，避免四五线城市",
        "<b>赛道</b>：优先🔥热门赛道（计算机/医学/公安），慎选⚠️天坑赛道",
        "<b>就业</b>：普通家庭选能直接找工作的专业（计算机/口腔医学/电气）",
        "<b>考研</b>：基础学科（数学/物理）适合走学术路线，但需要考研才能有出路",
        "<b>考公</b>：法学/汉语言/财经类专业考公机会多",
    ]
    for tip in correct_tips:
        story.append(Paragraph(f"• {tip}", styles['ListItem']))

    # ═══════════════════════════════════════════════════════════════
    # 八、案例演示（高分/中分/低分）
    # ═══════════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("八、案例演示：三种分数段如何操作", styles['ChapterTitle']))

    story.append(Paragraph(
        "以下通过三个真实模拟案例，展示如何使用本系统生成最优志愿方案。",
        styles['Body']
    ))

    # 案例1：高分
    story.append(Paragraph("📗 案例一：物理类·高分考生（省排名5,000名）", styles['SectionTitle']))
    case1_steps = [
        "<b>考生信息</b>：男，预估580分，首选物理，位次约5,000，色觉正常",
        "<b>策略设置</b>：家庭普通，选择\u201C困难家庭\u201D策略（多保底+就业导向）",
        "<b>系统操作</b>：在【考生信息】页输入580分+2026位次5,000，策略选择\u201C困难家庭+直接就业\u201D，点击生成",
        "<b>系统推荐</b>：冲志愿含北京航空航天大学计算机类、杭州电子科技大学电子信息类；保志愿含河北工业大学计算机类、天津工业大学软件工程",
        "<b>张雪峰解读</b>：省排名5,000可以冲\u201C两电一邮\u201D类院校的计算机方向，但保底必须有河北/天津等本地强校计算机（直接就业）。推荐指数⭐⭐⭐⭐⭐的专业：杭州电子科技大学计算机（城市新一线+专业热门+公办，学费低）",
        "<b>导出结果</b>：系统生成96个志愿表，导出Excel备用，投档前核对当年招生计划",
    ]
    for step in case1_steps:
        story.append(Paragraph(f"  {step}", styles['ListItem']))

    # 案例2：中分
    story.append(Paragraph("📙 案例二：物理类·中分考生（省排名75,000名）", styles['SectionTitle']))
    case2_steps = [
        "<b>考生信息</b>：女，预估510分，首选物理，位次约75,000，色觉正常，愿意去外地",
        "<b>策略设置</b>：家庭普通，选择\u201C普通家庭\u201D策略，地域选择\u201C愿意去外地\u201D",
        "<b>系统操作</b>：输入510分+位次75,000，策略选\u201C普通家庭+直接就业+愿意去外地\u201D，点击生成",
        "<b>系统推荐</b>：冲志愿含山东科技大学计算机类、江苏大学电气类；稳含河北大学软件工程、唐山学院计算机；保含河北地质大学测绘类",
        "<b>张雪峰解读</b>：75,000名是河北省物理类的中间分数段。优先\u201C去外地\u201D可以选济南/青岛/徐州的工科院校（城市较好+专业实用）。推荐关注\u201C计算机\u201D和\u201C电气\u201D两个就业导向专业。⚠️独立学院（XX大学XX学院）不在推荐前列，避免踩坑",
        "<b>导出结果</b>：六边形分析图对比杭州电子科技大学vs山东科技大学，显示就业导向维度",
    ]
    for step in case2_steps:
        story.append(Paragraph(f"  {step}", styles['ListItem']))

    # 案例3：低分
    story.append(Paragraph("📕 案例三：历史类·低分考生（省排名120,000名）", styles['SectionTitle']))
    case3_steps = [
        "<b>考生信息</b>：男，预估470分，首选历史，位次约120,000，色弱，优先省内",
        "<b>策略设置</b>：家庭困难，选择\u201C困难家庭\u201D策略（就业导向+省内），色觉异常已录入系统",
        "<b>系统操作</b>：输入470分+位次120,000，策略选\u201C困难家庭+直接就业+优先省内\u201D，身体条件选\u201C色弱\u201D，点击生成",
        "<b>系统推荐</b>：保底含河北经贸大学会计学、河北金融学院财务管理；冲含河北师范大学法学（师范方向）；系统自动过滤对色弱受限的化学/医学类专业",
        "<b>张雪峰解读</b>：历史类120,000名竞争激烈，色弱限制了部分专业（化学/生物/医学均受限）。建议选\u201C会计\u201D或\u201C财务管理\u201D——能直接就业，不需要色觉受限的专业。推荐指数⭐⭐⭐以上的专业：河北经贸大学会计（公办+省内+就业好）",
        "<b>特别提示</b>：系统对色觉异常考生会自动在体检限制列标注\u201C⚠️色弱受限\u201D或\u201C✅对色弱友好\u201D，家长务必核对",
    ]
    for step in case3_steps:
        story.append(Paragraph(f"  {step}", styles['ListItem']))

    story.append(create_tip_box(
        "💡 使用建议：案例仅供演示参考。真实填报时请以当年考试院公布的投档数据和招生计划为准。\n"
        "系统推荐96个志愿，请务必结合考生个人兴趣、家庭条件、目标城市综合决策。",
        styles
    ))

    story.append(create_tip_box(
        "最终提醒：所有建议仅供参考，孩子的人生由孩子自己决定。"
        "系统只是工具，选学校、选专业、选城市，最终都是家庭共同商量决定的事。",
        styles
    ))

    story.append(Spacer(1, 1*cm))
    
    # 结语
    story.append(Paragraph(
        "祝各位考生金榜题名，前程似锦！",
        styles['CoverSubtitle']
    ))
    
    return story


def main():
    """生成PDF手册"""
    # 注册中文字体
    global CHINESE_FONT, CHINESE_FONT_BOLD
    registered = register_chinese_fonts()
    if 'msyh' in registered:
        CHINESE_FONT = 'msyh'
        CHINESE_FONT_BOLD = 'msyhbd'
    elif 'simhei' in registered:
        CHINESE_FONT = 'simhei'
        CHINESE_FONT_BOLD = 'simhei'
    elif 'simsun' in registered:
        CHINESE_FONT = 'simsun'
        CHINESE_FONT_BOLD = 'simsun'
    else:
        print("警告：未找到中文字体，PDF可能无法正常显示中文")
    
    output_path = Path(__file__).parent / "用户手册.pdf"
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 添加页眉页脚模板
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        id='normal'
    )
    template = PageTemplate(
        id='main',
        frames=frame,
        onPage=add_header_footer
    )
    doc.addPageTemplates([template])
    
    # 构建内容
    story = build_manual()
    
    # 生成PDF
    doc.build(story)
    print(f"用户手册已生成：{output_path}")
    return output_path


if __name__ == "__main__":
    main()
