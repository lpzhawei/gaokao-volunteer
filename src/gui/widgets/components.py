"""
自定义 UI 组件库

提供可复用的视觉组件，统一应用设计语言。
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPalette, QColor

from ..theme import Colors, Font, Radius, Spacing, ComponentStyles


class CardWidget(QFrame):
    """通用卡片容器 - 白色圆角背景"""

    def __init__(self, parent=None, padding=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.GRAY_200};
                border-radius: {Radius.LG};
                {f'padding: {padding};' if padding else ''}
            }}
        """)


class StatCard(QWidget):
    """统计卡片 - 显示指标名称和数值"""

    def __init__(self, name: str, value: str, color: str = Colors.PRIMARY_500,
                 parent=None):
        super().__init__(parent)
        self.setStyleSheet(ComponentStyles.STAT_CARD)
        self.setMinimumHeight(36)  # 确保卡片有足够高度显示

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(0)

        # 指标名
        self.lbl_name = QLabel(name)
        self.lbl_name.setFont(QFont(Font.FAMILY, 11))
        self.lbl_name.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")

        # 指标值 - 使用深色确保可见
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(QFont(Font.FAMILY, 16, QFont.Weight.Bold))
        self.lbl_value.setStyleSheet(f"color: {color}; background: transparent; font-size: 14pt;")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_value.setMinimumWidth(50)

        layout.addWidget(self.lbl_name)
        layout.addStretch()
        layout.addWidget(self.lbl_value)

    def set_value(self, value: str):
        self.lbl_value.setText(value)


class TipBox(QWidget):
    """提示框组件 - 支持 warning/info/success 三种类型"""

    def __init__(self, text: str, tip_type: str = "warning", parent=None):
        super().__init__(parent)

        style_map = {
            "warning": ComponentStyles.TIP_WARNING,
            "info": ComponentStyles.TIP_INFO,
            "success": ComponentStyles.TIP_SUCCESS,
        }
        style = style_map.get(tip_type, ComponentStyles.TIP_WARNING)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(style)
        layout.addWidget(self.label)

    def setText(self, text: str):
        self.label.setText(text)


class HeaderBar(QFrame):
    """顶部标题栏 - 使用QFrame并设置背景色"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("header_bar")
        self.setFixedHeight(64)
        
        # 使用autoFillBackground + QPalette设置背景色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1976D2"))
        self.setPalette(palette)
        self.setBackgroundRole(QPalette.ColorRole.Window)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_title = QLabel("🎓  河北省高考志愿填报系统")
        self.lbl_title.setObjectName("header_title")
        self.lbl_title.setFont(QFont(Font.FAMILY, 18, QFont.Weight.Bold))
        self.lbl_title.setForegroundRole(QPalette.ColorRole.WindowText)
        self.lbl_title.setBackgroundRole(QPalette.ColorRole.Window)
        self.lbl_title.setAutoFillBackground(True)

        self.lbl_sub = QLabel("2026版  |  基于河北省教育考试院官方规则")
        self.lbl_sub.setObjectName("header_subtitle")
        self.lbl_sub.setFont(QFont(Font.FAMILY, 10))
        self.lbl_sub.setForegroundRole(QPalette.ColorRole.WindowText)
        self.lbl_sub.setBackgroundRole(QPalette.ColorRole.Window)
        self.lbl_sub.setAutoFillBackground(True)

        layout.addWidget(self.lbl_title)
        layout.addStretch()
        layout.addWidget(self.lbl_sub)


class ActionPanel(QWidget):
    """操作面板 - 浅灰背景圆角容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ComponentStyles.ACTION_PANEL)
