"""
数据管理面板
支持导入Excel投档数据、查看数据库状态
"""
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QFileDialog, QComboBox, QSpinBox, QProgressBar,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFormLayout, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor

from ..data.database import get_connection, init_db
from ..data.importer import ExcelImporter
from .theme import Colors, Font, Radius, Spacing, ComponentStyles
from .widgets import TipBox

logger = logging.getLogger(__name__)


class ImportWorkerSignals(QObject):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)


class ImportWorker(QThread):
    def __init__(self, filepath, year, subject_type, batch):
        super().__init__()
        self.filepath    = filepath
        self.year        = year
        self.subject_type = subject_type
        self.batch       = batch
        self.signals     = ImportWorkerSignals()

    def run(self):
        try:
            importer = ExcelImporter(
                self.filepath, self.year, self.subject_type, self.batch,
                progress_cb=lambda c, t, m: self.signals.progress.emit(c, t, m)
            )
            result = importer.import_file()
            self.signals.finished.emit(result)
        except Exception as e:
            logger.exception("导入失败")
            self.signals.error.emit(str(e))


class DataPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._refresh_stats()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── 左侧：导入操作区 ────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        # 导入配置
        grp_import = QGroupBox("导入投档数据（Excel）")
        fl = QFormLayout(grp_import)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 文件选择
        file_row = QWidget()
        file_hl  = QHBoxLayout(file_row)
        file_hl.setContentsMargins(0, 0, 0, 0)
        self.lbl_file = QLabel("未选择文件")
        self.lbl_file.setWordWrap(True)
        self.lbl_file.setStyleSheet(ComponentStyles.FILE_UNSELECTED)
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.setFixedWidth(70)
        self.btn_browse.setStyleSheet(ComponentStyles.BTN_EXPORT)
        self.btn_browse.clicked.connect(self._browse_file)
        file_hl.addWidget(self.lbl_file, 1)
        file_hl.addWidget(self.btn_browse)
        fl.addRow("数据文件：", file_row)

        self.spn_year = QSpinBox()
        self.spn_year.setRange(2020, 2030)
        self.spn_year.setValue(2025)
        fl.addRow("数据年份：", self.spn_year)

        self.cmb_subject = QComboBox()
        self.cmb_subject.addItems(["物理", "历史"])
        fl.addRow("科目类型：", self.cmb_subject)

        self.cmb_batch = QComboBox()
        self.cmb_batch.addItems(["本科批", "本科提前批", "专科批", "专科提前批"])
        fl.addRow("录取批次：", self.cmb_batch)

        self.btn_import = QPushButton("\U0001F4E5  开始导入")
        self.btn_import.setFixedHeight(42)
        self.btn_import.setEnabled(False)
        self.btn_import.setStyleSheet(ComponentStyles.BTN_ACTION)
        self.btn_import.clicked.connect(self._on_import)
        fl.addRow("", self.btn_import)

        left_layout.addWidget(grp_import)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(8)
        left_layout.addWidget(self.progress_bar)

        # 操作日志
        grp_log = QGroupBox("导入日志")
        log_layout = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas", 10))
        self.txt_log.setStyleSheet(ComponentStyles.TERMINAL)
        log_layout.addWidget(self.txt_log)
        left_layout.addWidget(grp_log, 1)

        # 使用说明
        tip = TipBox(
            "\U0001F4CC 导入说明：\n"
            "\u2022 支持河北省教育考试院发布的Excel格式\n"
            "\u2022 系统自动识别表头，兼容多种列名\n"
            "\u2022 同年份数据支持重复导入（自动覆盖）\n"
            "\u2022 建议导入2022~2025年全部数据",
            tip_type="info"
        )
        left_layout.addWidget(tip)

        splitter.addWidget(left)

        # ── 右侧：数据库状态 ─────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(10)

        # 数据统计
        grp_stats = QGroupBox("数据库状态")
        stats_layout = QVBoxLayout(grp_stats)

        self.btn_refresh = QPushButton("\U0001F504  刷新统计")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.clicked.connect(self._refresh_stats)
        stats_layout.addWidget(self.btn_refresh)

        self.tbl_stats = QTableWidget(0, 4)
        self.tbl_stats.setHorizontalHeaderLabels(["年份", "科目类型", "批次", "记录数"])
        self.tbl_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_stats.setAlternatingRowColors(True)
        self.tbl_stats.verticalHeader().setVisible(False)
        self.tbl_stats.verticalHeader().setDefaultSectionSize(30)
        stats_layout.addWidget(self.tbl_stats)

        right_layout.addWidget(grp_stats)

        # 数据预览
        grp_preview = QGroupBox("数据预览（最新20条）")
        prev_layout = QVBoxLayout(grp_preview)

        filter_row = QWidget()
        filter_hl  = QHBoxLayout(filter_row)
        filter_hl.setContentsMargins(0, 0, 0, 0)

        lbl_filter = QLabel("筛选年份：")
        lbl_filter.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        filter_hl.addWidget(lbl_filter)

        self.cmb_preview_year = QComboBox()
        self.cmb_preview_year.addItem("全部年份")
        self.cmb_preview_year.setFixedWidth(100)
        filter_hl.addWidget(self.cmb_preview_year)

        btn_preview = QPushButton("查看")
        btn_preview.setFixedWidth(60)
        btn_preview.setStyleSheet(ComponentStyles.BTN_EXPORT)
        btn_preview.clicked.connect(self._load_preview)
        filter_hl.addWidget(btn_preview)
        filter_hl.addStretch()
        prev_layout.addWidget(filter_row)

        self.tbl_preview = QTableWidget(0, 7)
        self.tbl_preview.setHorizontalHeaderLabels(
            ["年份", "院校名称", "专业名称", "科目", "批次", "最低分", "位次"]
        )
        self.tbl_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_preview.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_preview.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl_preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_preview.setAlternatingRowColors(True)
        self.tbl_preview.verticalHeader().setVisible(False)
        self.tbl_preview.verticalHeader().setDefaultSectionSize(28)
        prev_layout.addWidget(self.tbl_preview)

        right_layout.addWidget(grp_preview, 1)

        splitter.addWidget(right)
        splitter.setSizes([420, 680])
        layout.addWidget(splitter)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择投档数据Excel文件", "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        if path:
            self._filepath = path
            name = Path(path).name
            self.lbl_file.setText(name)
            self.lbl_file.setStyleSheet(ComponentStyles.FILE_SELECTED)
            self.btn_import.setEnabled(True)
            self._log(f"已选择文件：{path}")

    def _on_import(self):
        if not hasattr(self, "_filepath"):
            QMessageBox.warning(self, "提示", "请先选择Excel文件")
            return

        self.btn_import.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._log(f"开始导入：年份={self.spn_year.value()}，"
                  f"科目={self.cmb_subject.currentText()}，"
                  f"批次={self.cmb_batch.currentText()}")

        self._worker = ImportWorker(
            self._filepath,
            self.spn_year.value(),
            self.cmb_subject.currentText(),
            self.cmb_batch.currentText()
        )
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_import_done)
        self._worker.signals.error.connect(self._on_import_error)
        self._worker.start()

    def _on_progress(self, cur, total, msg):
        self.progress_bar.setValue(int(cur / total * 100))
        self._log(msg)

    def _on_import_done(self, result):
        self.progress_bar.setValue(100)
        self.btn_import.setEnabled(True)
        msg = f"\u2705 导入完成！成功：{result['success']} 条，跳过：{result['skipped']} 条"
        if result.get("errors"):
            msg += f"\n\u26A0 错误：{result['errors'][0]}"
        self._log(msg)
        self._refresh_stats()
        self._load_preview()
        QMessageBox.information(self, "导入完成", msg)

    def _on_import_error(self, err):
        self.progress_bar.setVisible(False)
        self.btn_import.setEnabled(True)
        self._log(f"\u274C 导入失败：{err}")
        QMessageBox.critical(self, "导入失败", f"导入过程中发生错误：\n{err}")

    def _refresh_stats(self):
        try:
            rows = self._query_stats()
            self.tbl_stats.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, key in enumerate(["year", "subject_type", "batch", "cnt"]):
                    item = QTableWidgetItem(str(row.get(key, "")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_stats.setItem(r, c, item)

            years = sorted(set(str(row["year"]) for row in rows), reverse=True)
            self.cmb_preview_year.clear()
            self.cmb_preview_year.addItem("全部年份")
            for y in years:
                self.cmb_preview_year.addItem(y)
        except Exception as e:
            self._log(f"刷新统计失败：{e}")

    def _query_stats(self):
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT year, subject_type, batch, COUNT(*) as cnt
            FROM admission_data
            GROUP BY year, subject_type, batch
            ORDER BY year DESC, subject_type, batch
        """)
        result = [dict(r) for r in cur.fetchall()]
        conn.close()
        return result

    def _load_preview(self):
        year_filter = self.cmb_preview_year.currentText()
        try:
            conn = get_connection()
            cur  = conn.cursor()
            if year_filter == "全部年份":
                cur.execute("""
                    SELECT year, college_name, major_name, subject_type,
                           batch, min_score, min_rank
                    FROM admission_data ORDER BY rowid DESC LIMIT 20
                """)
            else:
                cur.execute("""
                    SELECT year, college_name, major_name, subject_type,
                           batch, min_score, min_rank
                    FROM admission_data WHERE year=? ORDER BY rowid DESC LIMIT 20
                """, (int(year_filter),))
            rows = cur.fetchall()
            conn.close()

            self.tbl_preview.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_preview.setItem(r, c, item)
        except Exception as e:
            self._log(f"加载预览失败：{e}")

    def _log(self, msg):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{ts}] {msg}")
        self.txt_log.verticalScrollBar().setValue(
            self.txt_log.verticalScrollBar().maximum()
        )
