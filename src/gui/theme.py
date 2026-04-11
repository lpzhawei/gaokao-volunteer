"""
统一设计系统 - 河北省高考志愿填报系统

集中管理所有设计令牌：色彩、字体、间距、阴影、圆角。
所有 QSS 样式从这里导出，确保全局一致性。
"""


# ═══════════════════════════════════════════════════════════
#  色彩令牌
# ═══════════════════════════════════════════════════════════

class Colors:
    # ── 主色调：专业商务蓝 ──
    PRIMARY_50   = "#E3F2FD"
    PRIMARY_100  = "#BBDEFB"
    PRIMARY_200  = "#90CAF9"
    PRIMARY_300  = "#64B5F6"
    PRIMARY_400  = "#42A5F5"
    PRIMARY_500  = "#2196F3"   # 主色 - 经典蓝
    PRIMARY_600  = "#1E88E5"
    PRIMARY_700  = "#1976D2"
    PRIMARY_800  = "#1565C0"
    PRIMARY_900  = "#0D47A1"

    # ── 辅助色：金橙 ──
    SECONDARY_50  = "#FFF8E1"
    SECONDARY_100 = "#FFECB3"
    SECONDARY_200 = "#FFE082"
    SECONDARY_500 = "#FFC107"

    # ── 中性色 ──
    GRAY_50   = "#FAFAFA"
    GRAY_100  = "#F5F5F5"
    GRAY_200  = "#EEEEEE"
    GRAY_300  = "#E0E0E0"
    GRAY_400  = "#BDBDBD"
    GRAY_500  = "#9E9E9E"
    GRAY_600  = "#757575"
    GRAY_700  = "#616161"
    GRAY_800  = "#424242"
    GRAY_900  = "#212121"

    # ── 语义色 ──
    SUCCESS_LIGHT = "#E8F5E9"
    SUCCESS       = "#4CAF50"
    SUCCESS_DARK  = "#388E3C"

    WARNING_LIGHT = "#FFF3E0"
    WARNING       = "#FF9800"
    WARNING_DARK  = "#F57C00"

    DANGER_LIGHT  = "#FFEBEE"
    DANGER        = "#F44336"
    DANGER_DARK   = "#D32F2F"

    INFO_LIGHT    = "#E3F2FD"
    INFO          = "#2196F3"
    INFO_DARK     = "#1976D2"

    # ── 风险色 ──
    RISK_HIGH     = "#F44336"
    RISK_MEDIUM   = "#FF9800"
    RISK_LOW      = "#4CAF50"

    # ── 冲保色 ──
    CHONG_LIGHT   = "#FFEBEE"
    CHONG         = "#EF5350"
    BAO_LIGHT     = "#E8F5E9"
    BAO           = "#66BB6A"

    # ── 背景 ──
    BG_MAIN       = "#F5F7FA"
    BG_CARD       = "#FFFFFF"
    BG_SIDEBAR    = "#FAFBFC"
    BG_HEADER     = "#1976D2"

    # ── 文字 ──
    TEXT_PRIMARY   = "#212121"
    TEXT_SECONDARY = "#616161"
    TEXT_HINT      = "#9E9E9E"
    TEXT_WHITE     = "#FFFFFF"
    TEXT_ON_PRIMARY = "#FFFFFF"


# ═══════════════════════════════════════════════════════════
#  字体令牌
# ═══════════════════════════════════════════════════════════

class Font:
    FAMILY = "微软雅黑"

    SIZE_XS    = "10px"    # 10
    SIZE_SM    = "11px"    # 11
    SIZE_BASE  = "12px"    # 12
    SIZE_MD    = "13px"    # 13
    SIZE_LG    = "14px"    # 14
    SIZE_XL    = "16px"    # 16
    SIZE_2XL   = "18px"    # 18
    SIZE_3XL   = "22px"    # 22
    SIZE_4XL   = "28px"    # 28

    WEIGHT_NORMAL = "normal"
    WEIGHT_MEDIUM = "500"
    WEIGHT_BOLD   = "bold"


# ═══════════════════════════════════════════════════════════
#  间距令牌
# ═══════════════════════════════════════════════════════════

class Spacing:
    XS   = 4
    SM   = 6
    MD   = 8
    BASE = 12
    LG   = 16
    XL   = 20
    XXL  = 24
    XXXL = 32


# ═══════════════════════════════════════════════════════════
#  圆角令牌
# ═══════════════════════════════════════════════════════════

class Radius:
    SM    = 4
    MD    = 6
    LG    = 8
    XL    = 10
    XXL   = 12
    PILL  = 20
    CIRCLE = 9999


# ═══════════════════════════════════════════════════════════
#  阴影令牌（QSS 支持有限，主要用于边框模拟）
# ═══════════════════════════════════════════════════════════

class Shadow:
    # 通过边框颜色模拟浅阴影
    CARD = f"1px solid {Colors.GRAY_200}"
    CARD_HOVER = f"1px solid {Colors.PRIMARY_200}"
    ELEVATED = f"1px solid {Colors.GRAY_300}"


# ═══════════════════════════════════════════════════════════
#  全局样式表
# ═══════════════════════════════════════════════════════════

GLOBAL_STYLESHEET = f"""
/* ═══════════════════════════════════════════════════════
   全局基础样式
   ═══════════════════════════════════════════════════════ */

QMainWindow {{
    background-color: {Colors.BG_MAIN};
}}

/* 不用 QWidget 全局规则，改为精确选择器避免覆盖 HeaderBar */
QLabel, QGroupBox, QFormLayout > QWidget {{
    font-family: "{Font.FAMILY}";
    font-size: {Font.SIZE_BASE};
    color: {Colors.TEXT_PRIMARY};
}}

/* ── 标题栏（渐变蓝色背景 + 白色文字） ── */
#header_bar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {Colors.PRIMARY_700}, stop:0.5 {Colors.PRIMARY_500}, stop:1 {Colors.PRIMARY_600});
    border-radius: {Radius.XL}px;
}}
#header_title {{
    color: #FFFFFF;
    background: transparent;
    font-size: {Font.SIZE_2XL};
    font-weight: {Font.WEIGHT_BOLD};
}}
#header_subtitle {{
    color: {Colors.PRIMARY_100};
    background: transparent;
    font-size: {Font.SIZE_SM};
}}

/* ── Tab 页面 ── */
QTabWidget::pane {{
    border: none;
    background: {Colors.BG_MAIN};
    border-radius: {Radius.LG}px;
}}

QTabBar::tab {{
    background: transparent;
    color: {Colors.TEXT_SECONDARY};
    padding: 10px 24px;
    margin-right: 2px;
    border-top-left-radius: {Radius.LG}px;
    border-top-right-radius: {Radius.LG}px;
    font-size: {Font.SIZE_MD};
    font-weight: {Font.WEIGHT_MEDIUM};
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {Colors.PRIMARY_500};
    border-bottom: 2px solid {Colors.PRIMARY_500};
    font-weight: {Font.WEIGHT_BOLD};
}}

QTabBar::tab:hover:!selected {{
    color: {Colors.PRIMARY_500};
    background: {Colors.PRIMARY_50};
}}

/* ── 按钮 ── */
QPushButton {{
    background-color: {Colors.PRIMARY_500};
    color: {Colors.TEXT_ON_PRIMARY};
    border: none;
    padding: 8px 20px;
    border-radius: {Radius.MD}px;
    font-size: {Font.SIZE_MD};
    font-weight: {Font.WEIGHT_MEDIUM};
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {Colors.PRIMARY_400};
}}

QPushButton:pressed {{
    background-color: {Colors.PRIMARY_600};
}}

QPushButton:disabled {{
    background-color: {Colors.GRAY_300};
    color: {Colors.GRAY_500};
}}

QPushButton#btn_secondary {{
    background-color: {Colors.BG_CARD};
    color: {Colors.PRIMARY_500};
    border: 1px solid {Colors.PRIMARY_300};
}}

QPushButton#btn_secondary:hover {{
    background-color: {Colors.PRIMARY_50};
    border-color: {Colors.PRIMARY_400};
}}

QPushButton#btn_secondary:pressed {{
    background-color: {Colors.PRIMARY_100};
}}

/* ── GroupBox ── */
QGroupBox {{
    border: 1px solid {Colors.GRAY_200};
    border-radius: {Radius.LG}px;
    margin-top: 16px;
    padding: {Spacing.LG}px {Spacing.LG}px {Spacing.MD}px {Spacing.LG}px;
    font-weight: {Font.WEIGHT_BOLD};
    font-size: {Font.SIZE_MD};
    color: {Colors.TEXT_PRIMARY};
    background: {Colors.BG_CARD};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {Colors.PRIMARY_500};
}}

/* ── 输入框 ── */
QLineEdit, QDoubleSpinBox, QComboBox {{
    border: 1px solid {Colors.GRAY_300};
    border-radius: {Radius.MD}px;
    padding: 6px 10px;
    font-size: {Font.SIZE_MD};
    background: {Colors.BG_CARD};
    color: {Colors.TEXT_PRIMARY};
    min-height: 20px;
}}

/* SpinBox */
QSpinBox {{
    border: 1px solid {Colors.GRAY_300};
    border-radius: {Radius.MD}px;
    padding: 2px 28px 2px 4px;
    font-size: {Font.SIZE_MD};
    background: {Colors.BG_CARD};
    color: {Colors.TEXT_PRIMARY};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {Colors.PRIMARY_400};
    outline: none;
}}

QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
    background-color: {Colors.GRAY_100};
    color: {Colors.GRAY_500};
}}

QComboBox {{
    border: 1px solid {Colors.GRAY_300};
    border-radius: {Radius.MD}px;
    padding: 4px 8px;
    font-size: {Font.SIZE_MD};
    background: {Colors.BG_CARD};
    color: {Colors.TEXT_PRIMARY};
}}

/* ── 复选框 ── */
QCheckBox {{
    font-size: {Font.SIZE_MD};
    spacing: 8px;
    color: {Colors.TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: {Radius.SM}px;
    border: 1px solid {Colors.GRAY_400};
    background: {Colors.BG_CARD};
}}

QCheckBox::indicator:checked {{
    background-color: {Colors.PRIMARY_500};
    border-color: {Colors.PRIMARY_500};
}}

QCheckBox::indicator:hover {{
    border-color: {Colors.PRIMARY_400};
}}

/* ── 表格 ── */
QTableWidget {{
    border: 1px solid {Colors.GRAY_200};
    border-radius: {Radius.MD}px;
    gridline-color: {Colors.GRAY_100};
    font-size: {Font.SIZE_BASE};
    background: {Colors.BG_CARD};
    selection-background-color: {Colors.PRIMARY_50};
    selection-color: {Colors.TEXT_PRIMARY};
    alternate-background-color: {Colors.GRAY_50};
}}

QTableWidget::item {{
    padding: 4px 6px;
    border-bottom: 1px solid {Colors.GRAY_100};
}}

QTableWidget::item:selected {{
    background-color: {Colors.PRIMARY_50};
    color: {Colors.PRIMARY_700};
}}

QHeaderView::section {{
    background-color: {Colors.GRAY_100};
    color: {Colors.TEXT_SECONDARY};
    padding: 8px 6px;
    font-weight: {Font.WEIGHT_BOLD};
    font-size: {Font.SIZE_SM};
    border: none;
    border-bottom: 2px solid {Colors.GRAY_200};
}}

QHeaderView::section:first {{
    border-top-left-radius: {Radius.MD}px;
}}

QHeaderView::section:last {{
    border-top-right-radius: {Radius.MD}px;
}}

/* ── 滚动条 ── */
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
    margin: 4px 2px 4px 2px;
}}

QScrollBar::handle:vertical {{
    background: {Colors.GRAY_400};
    border-radius: 3px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Colors.GRAY_500};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    height: 6px;
    background: transparent;
    margin: 2px 4px 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background: {Colors.GRAY_400};
    border-radius: 3px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {Colors.GRAY_500};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

/* ── 进度条 ── */
QProgressBar {{
    border: none;
    border-radius: {Radius.PILL}px;
    text-align: center;
    font-size: {Font.SIZE_SM};
    font-weight: {Font.WEIGHT_MEDIUM};
    color: {Colors.TEXT_ON_PRIMARY};
    background: {Colors.GRAY_200};
    min-height: 8px;
    max-height: 8px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {Colors.PRIMARY_400}, stop:1 {Colors.PRIMARY_600});
    border-radius: {Radius.PILL}px;
}}

/* ── 状态栏 ── */
QStatusBar {{
    background: {Colors.BG_CARD};
    color: {Colors.TEXT_SECONDARY};
    font-size: {Font.SIZE_SM};
    border-top: 1px solid {Colors.GRAY_200};
    padding: 2px 12px;
}}

/* ── 分割器 ── */
QSplitter::handle {{
    background: {Colors.GRAY_200};
    width: 1px;
}}

QSplitter::handle:hover {{
    background: {Colors.PRIMARY_300};
}}

/* ── 列表 ── */
QListWidget {{
    border: 1px solid {Colors.GRAY_300};
    border-radius: {Radius.MD}px;
    padding: 2px;
    background: {Colors.BG_CARD};
    outline: none;
}}

QListWidget::item {{
    padding: 5px 8px;
    border-radius: {Radius.SM}px;
    margin: 1px 0px;
}}

QListWidget::item:selected {{
    background-color: {Colors.PRIMARY_50};
    color: {Colors.PRIMARY_700};
}}

QListWidget::item:hover:!selected {{
    background-color: {Colors.GRAY_50};
}}

/* ── 消息框 ── */
QMessageBox {{
    background-color: {Colors.BG_CARD};
}}

QMessageBox QLabel {{
    font-size: {Font.SIZE_MD};
    color: {Colors.TEXT_PRIMARY};
}}
"""


# ═══════════════════════════════════════════════════════════
#  组件级样式片段（供面板引用）
# ═══════════════════════════════════════════════════════════

class ComponentStyles:

    # 标题栏
    HEADER = f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {Colors.PRIMARY_700}, stop:0.5 {Colors.PRIMARY_500}, stop:1 {Colors.PRIMARY_600});
        border-radius: {Radius.XL}px;
    """

    HEADER_TITLE = f"""
        color: {Colors.TEXT_WHITE};
        background: transparent;
        font-size: {Font.SIZE_2XL};
        font-weight: {Font.WEIGHT_BOLD};
        letter-spacing: 1px;
    """

    HEADER_SUBTITLE = f"""
        color: {Colors.PRIMARY_100};
        background: transparent;
        font-size: {Font.SIZE_SM};
    """

    # 生成按钮（主操作 - 青绿色）
    BTN_PRIMARY = f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.PRIMARY_400}, stop:1 {Colors.PRIMARY_600});
            color: white;
            border: none;
            border-radius: {Radius.LG}px;
            padding: 10px 24px;
            font-size: {Font.SIZE_LG};
            font-weight: {Font.WEIGHT_BOLD};
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.PRIMARY_300}, stop:1 {Colors.PRIMARY_500});
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.PRIMARY_600}, stop:1 {Colors.PRIMARY_700});
        }}
        QPushButton:disabled {{
            background: {Colors.GRAY_300};
            color: {Colors.GRAY_500};
        }}
    """

    # 次要按钮（蓝色）
    BTN_ACTION = f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.PRIMARY_400}, stop:1 {Colors.PRIMARY_500});
            color: white;
            border: none;
            border-radius: {Radius.MD}px;
            padding: 8px 20px;
            font-size: {Font.SIZE_MD};
            font-weight: {Font.WEIGHT_MEDIUM};
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.PRIMARY_300}, stop:1 {Colors.PRIMARY_400});
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.PRIMARY_500}, stop:1 {Colors.PRIMARY_600});
        }}
    """

    # 冲方向滑块
    SLIDER_CHONG = f"""
        QSlider::groove:horizontal {{
            border: none;
            height: 6px;
            background: {Colors.CHONG_LIGHT};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {Colors.CHONG};
            border: 2px solid white;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::sub-page:horizontal {{
            background: {Colors.CHONG};
            border-radius: 3px;
        }}
    """

    # 保方向滑块
    SLIDER_BAO = f"""
        QSlider::groove:horizontal {{
            border: none;
            height: 6px;
            background: {Colors.BAO_LIGHT};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {Colors.BAO};
            border: 2px solid white;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::sub-page:horizontal {{
            background: {Colors.BAO};
            border-radius: 3px;
        }}
    """

    # 终端日志（浅色主题）
    TERMINAL = f"""
        background: {Colors.GRAY_50};
        color: {Colors.GRAY_700};
        border: 1px solid {Colors.GRAY_200};
        border-radius: {Radius.MD}px;
        padding: 8px;
        font-family: "Consolas", "Cascadia Code", monospace;
        font-size: {Font.SIZE_SM};
    """

    # 提示框
    TIP_WARNING = f"""
        background: {Colors.WARNING_LIGHT};
        border: 1px solid {Colors.WARNING};
        border-radius: {Radius.MD}px;
        padding: 12px;
        font-size: {Font.SIZE_BASE};
        color: #5D4037;
    """

    TIP_INFO = f"""
        background: {Colors.INFO_LIGHT};
        border: 1px solid {Colors.INFO};
        border-radius: {Radius.MD}px;
        padding: 12px;
        font-size: {Font.SIZE_BASE};
        color: {Colors.INFO_DARK};
    """

    TIP_SUCCESS = f"""
        background: {Colors.SUCCESS_LIGHT};
        border: 1px solid {Colors.SUCCESS};
        border-radius: {Radius.MD}px;
        padding: 12px;
        font-size: {Font.SIZE_BASE};
        color: {Colors.SUCCESS_DARK};
    """

    # 统计卡片
    STAT_CARD = f"""
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.GRAY_200};
        border-radius: {Radius.MD}px;
        padding: 8px;
    """

    # 侧边操作区
    ACTION_PANEL = f"""
        background: {Colors.BG_SIDEBAR};
        border-radius: {Radius.XL}px;
        border: 1px solid {Colors.GRAY_200};
    """

    # 自动计算按钮
    BTN_AUTO = f"""
        QPushButton {{
            background: {Colors.INFO_LIGHT};
            color: {Colors.INFO_DARK};
            border: 1px solid {Colors.INFO};
            border-radius: {Radius.MD}px;
            padding: 6px 12px;
            font-size: {Font.SIZE_SM};
        }}
        QPushButton:hover {{
            background: {Colors.PRIMARY_100};
        }}
    """

    # 导出按钮（带图标色彩）
    BTN_EXPORT = f"""
        QPushButton {{
            background: {Colors.BG_CARD};
            color: {Colors.PRIMARY_500};
            border: 1px solid {Colors.PRIMARY_300};
            border-radius: {Radius.MD}px;
            padding: 6px 14px;
            font-size: {Font.SIZE_BASE};
            font-weight: {Font.WEIGHT_MEDIUM};
        }}
        QPushButton:hover {{
            background: {Colors.PRIMARY_50};
            border-color: {Colors.PRIMARY_500};
        }}
        QPushButton:pressed {{
            background: {Colors.PRIMARY_100};
        }}
    """

    # 文件选择区（未选择）
    FILE_UNSELECTED = f"""
        color: {Colors.TEXT_HINT};
        font-size: {Font.SIZE_BASE};
        border: 1px dashed {Colors.GRAY_400};
        padding: 8px;
        border-radius: {Radius.MD}px;
    """

    # 文件选择区（已选择）
    FILE_SELECTED = f"""
        color: {Colors.PRIMARY_500};
        font-size: {Font.SIZE_BASE};
        border: 1px solid {Colors.PRIMARY_300};
        padding: 8px;
        border-radius: {Radius.MD}px;
        background: {Colors.PRIMARY_50};
    """

    # 表格行背景色（交替）
    TABLE_ROW_ALT = f"{Colors.GRAY_50}"
