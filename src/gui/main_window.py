"""
主窗口 - 河北省高考志愿填报系统
"""
import sys
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QStatusBar, QMessageBox, QApplication, QLabel, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

from .input_panel import InputPanel
from .data_panel  import DataPanel
from .result_panel import ResultPanel
from .theme import GLOBAL_STYLESHEET
from .widgets import HeaderBar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("河北省高考志愿填报系统 2026")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        # 设置窗口图标
        self._apply_icon()
        self._setup_ui()
        # 全局样式表要在HeaderBar创建之后再设置
        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._setup_statusbar()

    def _apply_icon(self):
        """设置窗口图标（多尺寸 PNG）"""
        from PyQt6.QtGui import QPixmap
        from pathlib import Path as _Path
        if getattr(sys, 'frozen', False):
            base = _Path(sys.executable).parent / "_internal"
        else:
            base = _Path(__file__).parent.parent.parent  # gaokao_volunteer/
        
        resources = base / "resources"
        icon = QIcon()
        for sz in [16, 24, 32, 48, 64, 128, 256]:
            p = resources / f"icon_{sz}.png"
            if p.exists():
                icon.addPixmap(QPixmap(str(p)))
        if not icon.isNull():
            self.setWindowIcon(icon)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(12)

        # ── 顶部标题栏 ─────────────────────────────────
        header = HeaderBar()
        main_layout.addWidget(header)

        # ── Tab页面 ─────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab1：考生信息 & 推荐
        self.input_panel = InputPanel(self)
        self.tabs.addTab(self.input_panel, "  考生信息与推荐  ")

        # Tab2：数据管理
        self.data_panel = DataPanel(self)
        self.tabs.addTab(self.data_panel, "  数据管理  ")

        # Tab3：志愿结果
        self.result_panel = ResultPanel(self)
        self.tabs.addTab(self.result_panel, "  志愿结果  ")

        main_layout.addWidget(self.tabs)

        # 信号连接
        self.input_panel.volunteers_ready.connect(self._on_volunteers_ready)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("系统就绪  |  请先在【数据管理】中导入投档数据，再填写考生信息生成志愿")

    def _on_volunteers_ready(self, volunteers):
        """推荐完成，切换到结果页"""
        student_info = self.input_panel.get_student_info()
        if volunteers:
            student_info["student_rank"] = volunteers[0].student_rank
        self.result_panel.load_volunteers(volunteers, student_info)
        self.tabs.setCurrentIndex(2)
        self.status.showMessage(f"\u2705  已生成 {len(volunteers)} 个志愿，请在【志愿结果】页查看并导出")

    def show_status(self, msg: str):
        self.status.showMessage(msg)
