"""
考生信息录入面板 + 推荐触发
"""
import json
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QTextEdit, QSplitter, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox, QFrame, QSlider, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIntValidator

from ..core.engine import RecommendEngine, StudentProfile
from .theme import Colors, Font, Radius, Spacing, ComponentStyles
from .widgets import ActionPanel, TipBox

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)


class RecommendWorker(QThread):
    def __init__(self, profile: StudentProfile, batch: str):
        super().__init__()
        self.profile = profile
        self.batch   = batch
        self.signals = WorkerSignals()

    def run(self):
        import traceback
        try:
            engine = RecommendEngine(
                self.profile,
                progress_cb=lambda c, t, m: self.signals.progress.emit(c, t, m)
            )
            result = engine.generate(batch=self.batch, total=96)
            self.signals.finished.emit(result)
        except Exception as e:
            tb = traceback.format_exc()
            logger.exception("推荐引擎异常")
            self.signals.error.emit(f"{e}\n\n{tb}")


class InputPanel(QWidget):
    volunteers_ready = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._worker = None

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # ── 左侧：表单 ───────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(484)  # 原440加宽10%
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(4, 4, 4, 4)

        # 基本信息
        grp_basic = QGroupBox("基本信息")
        fl_basic  = QFormLayout(grp_basic)
        fl_basic.setSpacing(8)
        fl_basic.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_name = QLineEdit("考生")
        self.inp_name.setPlaceholderText("请输入姓名（选填）")
        fl_basic.addRow("姓名：", self.inp_name)

        self.inp_score = QSpinBox()
        self.inp_score.setRange(100, 750)
        self.inp_score.setValue(550)
        self.inp_score.setSuffix(" 分")
        self.inp_score.valueChanged.connect(self._update_rank_display)
        fl_basic.addRow("预估总分：", self.inp_score)

        # 考生位次显示
        self.lbl_rank = QLabel("2025参考位次：---")
        self.lbl_rank.setStyleSheet(f"color: {Colors.TEXT_HINT}; font-size: 10pt; background: transparent;")
        fl_basic.addRow("", self.lbl_rank)

        # 2026位次输入框（必填）
        self.inp_rank_2026 = QLineEdit("")
        self.inp_rank_2026.setPlaceholderText("2026年高考位次（必填）")
        self.inp_rank_2026.setValidator(QIntValidator(1, 999999, self))
        fl_basic.addRow("2026位次：", self.inp_rank_2026)

        self.inp_extra = QSpinBox()
        self.inp_extra.setRange(0, 30)
        self.inp_extra.setValue(0)
        self.inp_extra.setSuffix(" 分")
        self.inp_extra.valueChanged.connect(self._update_rank_display)
        fl_basic.addRow("政策加分：", self.inp_extra)

        form_layout.addWidget(grp_basic)

        # ── 位次控制双滑块 ─────────
        grp_rank = QGroupBox("位次浮动控制")
        grp_rank.setToolTip("以考生位次为中心，分别控制冲和保方向的位次浮动范围\n"
                            "冲滑块（红色）：位次向更好的方向浮动\n"
                            "保滑块（绿色）：位次向更差的方向浮动\n"
                            "两个都为0时自动计算范围；任一不为0时严格按范围筛选")
        rank_layout = QVBoxLayout(grp_rank)
        rank_layout.setSpacing(6)

        # 冲方向滑块
        lbl_chong = QLabel("\U0001F534  冲方向（位次更好的学校）")
        lbl_chong.setStyleSheet(f"color: {Colors.CHONG}; font-weight: bold; font-size: 10pt; background: transparent;")
        rank_layout.addWidget(lbl_chong)

        chong_row = QHBoxLayout()
        self.slider_chong = QSlider(Qt.Orientation.Horizontal)
        self.slider_chong.setRange(0, 50000)
        self.slider_chong.setValue(3000)
        self.slider_chong.setSingleStep(500)
        self.slider_chong.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_chong.setTickInterval(10000)
        self.slider_chong.setStyleSheet(ComponentStyles.SLIDER_CHONG)
        chong_row.addWidget(QLabel("0"))
        chong_row.addWidget(self.slider_chong, 1)
        self.lbl_chong_val = QLabel("0")
        self.lbl_chong_val.setFixedWidth(60)
        self.lbl_chong_val.setStyleSheet(f"color: {Colors.CHONG}; font-weight: bold; background: transparent;")
        chong_row.addWidget(self.lbl_chong_val)
        rank_layout.addLayout(chong_row)

        # 保方向滑块
        lbl_bao = QLabel("\U0001F7E2  保方向（位次更差的学校）")
        lbl_bao.setStyleSheet(f"color: {Colors.BAO}; font-weight: bold; font-size: 10pt; background: transparent;")
        rank_layout.addWidget(lbl_bao)

        bao_row = QHBoxLayout()
        self.slider_bao = QSlider(Qt.Orientation.Horizontal)
        self.slider_bao.setRange(0, 50000)
        self.slider_bao.setValue(10000)
        self.slider_bao.setSingleStep(500)
        self.slider_bao.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_bao.setTickInterval(10000)
        self.slider_bao.setStyleSheet(ComponentStyles.SLIDER_BAO)
        bao_row.addWidget(QLabel("0"))
        bao_row.addWidget(self.slider_bao, 1)
        self.lbl_bao_val = QLabel("0")
        self.lbl_bao_val.setFixedWidth(60)
        self.lbl_bao_val.setStyleSheet(f"color: {Colors.BAO}; font-weight: bold; background: transparent;")
        bao_row.addWidget(self.lbl_bao_val)
        rank_layout.addLayout(bao_row)

        # 当前范围显示
        self.lbl_slider_val = QLabel("当前：自动范围（将根据筛选条件设定）")
        self.lbl_slider_val.setStyleSheet(f"color: {Colors.PRIMARY_500}; font-weight: bold; background: transparent;")
        rank_layout.addWidget(self.lbl_slider_val)
        self.slider_chong.valueChanged.connect(self._on_slider_changed)
        self.slider_bao.valueChanged.connect(self._on_slider_changed)

        # 自动计算按钮
        btn_auto = QPushButton("\U0001F504  根据当前条件自动计算范围")
        btn_auto.setToolTip("根据分数、科目等条件自动设置合理的位次浮动范围")
        btn_auto.setStyleSheet(ComponentStyles.BTN_AUTO)
        btn_auto.clicked.connect(self._auto_set_rank_range)
        rank_layout.addWidget(btn_auto)

        # 位次范围说明
        lbl_tip = QLabel("\U0001F4A1 提示：\n"
                         "\u2022 两个滑块都为0 \u2192 自动根据筛选条件计算范围\n"
                         "\u2022 调整任一滑块 \u2192 严格按范围筛选\n"
                         "\u2022 冲=位次更好的学校，保=位次更差的学校")
        lbl_tip.setStyleSheet(f"color: {Colors.TEXT_HINT}; font-size: 9pt; background: transparent;")
        lbl_tip.setWordWrap(True)
        rank_layout.addWidget(lbl_tip)

        form_layout.addWidget(grp_rank)

        # 选科信息
        grp_subject = QGroupBox("选考科目")
        fl_sub = QFormLayout(grp_subject)
        fl_sub.setSpacing(8)
        fl_sub.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cmb_first = QComboBox()
        self.cmb_first.addItems(["物理", "历史"])
        fl_sub.addRow("首选科目：", self.cmb_first)

        self.cmb_elec1 = QComboBox()
        self.cmb_elec1.addItems(["化学", "生物", "地理", "政治", "不选"])
        fl_sub.addRow("再选科目1：", self.cmb_elec1)

        self.cmb_elec2 = QComboBox()
        self.cmb_elec2.addItems(["生物", "化学", "地理", "政治", "不选"])
        fl_sub.addRow("再选科目2：", self.cmb_elec2)

        form_layout.addWidget(grp_subject)

        # 身体条件
        grp_body = QGroupBox("身体条件")
        fl_body = QFormLayout(grp_body)
        fl_body.setSpacing(8)
        fl_body.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cmb_gender = QComboBox()
        self.cmb_gender.addItems(["男", "女"])
        fl_body.addRow("性别：", self.cmb_gender)

        self.cmb_color = QComboBox()
        self.cmb_color.addItems(["正常", "色弱", "色盲"])
        fl_body.addRow("色觉状态：", self.cmb_color)

        self.cmb_vision = QComboBox()
        self.cmb_vision.addItems(["5.0及以上", "4.9", "4.8", "4.7", "4.6", "4.5", "4.3及以下"])
        self.cmb_vision.setCurrentIndex(0)
        self.cmb_vision.setToolTip("裸眼视力：飞行技术、航海技术、公安类专业有视力要求")
        fl_body.addRow("裸眼视力：", self.cmb_vision)

        self.inp_height = QSpinBox()
        self.inp_height.setRange(140, 220)
        self.inp_height.setValue(170)
        self.inp_height.setSuffix(" cm")
        self.inp_height.setToolTip("公安类、航海类、播音主持等专业有身高要求")
        fl_body.addRow("身高：", self.inp_height)

        self.inp_weight = QSpinBox()
        self.inp_weight.setRange(30, 150)
        self.inp_weight.setValue(60)
        self.inp_weight.setSuffix(" kg")
        self.inp_weight.setToolTip("公安类院校有最低体重要求（男\u226550kg，女\u226545kg）")
        fl_body.addRow("体重：", self.inp_weight)

        form_layout.addWidget(grp_body)

        # ── 张雪峰视角：考生策略方向 ─────────────────────────
        grp_strategy = QGroupBox("🎯 志愿策略方向（张雪峰视角）")
        grp_strategy.setToolTip("张雪峰建议：根据家庭条件和目标选择适合自己的策略\n"
                                "这三个问题将影响推荐算法对城市和专业赛道的侧重")
        fl_strat = QFormLayout(grp_strategy)
        fl_strat.setSpacing(8)
        fl_strat.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 家庭条件
        self.cmb_strategy = QComboBox()
        self.cmb_strategy.addItems([
            "普通家庭（默认）",
            "富裕家庭（可接受高学费）",
            "困难家庭（优先就业导向）",
        ])
        self.cmb_strategy.setToolTip(
            "普通家庭：优先就业导向，保底充足\n"
            "富裕家庭：可冲好城市好专业，注意学费\n"
            "困难家庭：强烈建议选择直接能找工作的专业"
        )
        fl_strat.addRow("家庭条件：", self.cmb_strategy)

        # 未来目标
        self.cmb_work = QComboBox()
        self.cmb_work.addItems([
            "直接就业（默认）",
            "考研深造",
            "考公方向",
        ])
        self.cmb_work.setToolTip(
            "直接就业：优先计算机、口腔、电气等好就业专业\n"
            "考研深造：可考虑基础学科（数学、物理）\n"
            "考公方向：优先法学、汉语言、行政管理"
        )
        fl_strat.addRow("未来目标：", self.cmb_work)

        # 地域偏好
        self.cmb_city_pref = QComboBox()
        self.cmb_city_pref.addItems([
            "愿意去外地（默认）",
            "优先在河北省内",
        ])
        self.cmb_city_pref.setToolTip(
            "愿意去外地：优先推荐北京、上海、广州、深圳、杭州等大城市\n"
            "优先省内：优先推荐石家庄、保定、唐山等河北城市"
        )
        fl_strat.addRow("地域偏好：", self.cmb_city_pref)

        # 张雪峰提示
        zxf_hint = TipBox(
            "\U0001F4A1 张雪峰核心理念：城市 > 学校 > 专业\n"
            "能去一线城市就不去二线，能去二线就不去县城。"
            "好城市=更多实习机会+更宽人脉+更好视野。",
            tip_type="info"
        )
        zxf_hint.setFixedHeight(60)
        fl_strat.addRow("", zxf_hint)

        form_layout.addWidget(grp_strategy)

        # 偏好设置
        grp_pref = QGroupBox("偏好设置")
        fl_pref = QVBoxLayout(grp_pref)

        lbl_major = QLabel("专业偏好（可多选）：")
        lbl_major.setFont(QFont(Font.FAMILY, 10))
        fl_pref.addWidget(lbl_major)
        self.lst_major = QListWidget()
        self.lst_major.setFixedHeight(130)
        self.lst_major.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        major_cats = ["不限", "计算机/信息技术", "电子/通信", "机械/制造",
                      "土木/建筑", "医学/药学", "经济/金融", "管理/工商",
                      "师范/教育", "法学/政治", "中文/新闻", "外语",
                      "数学/物理", "化工/化学", "生物/农学", "艺术/设计"]
        for cat in major_cats:
            self.lst_major.addItem(QListWidgetItem(cat))
        self.lst_major.item(0).setSelected(True)
        fl_pref.addWidget(self.lst_major)

        lbl_prov = QLabel("偏好省份（可多选）：")
        lbl_prov.setFont(QFont(Font.FAMILY, 10))
        fl_pref.addWidget(lbl_prov)
        self.lst_prov = QListWidget()
        self.lst_prov.setFixedHeight(120)
        self.lst_prov.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        provinces = [
            "不限",
            "北京", "上海", "天津", "重庆",
            "河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建",
            "江西", "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "四川",
            "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆", "台湾",
            "香港", "澳门"
        ]
        for p in provinces:
            self.lst_prov.addItem(QListWidgetItem(p))
        self.lst_prov.item(0).setSelected(True)
        fl_pref.addWidget(lbl_prov)
        fl_pref.addWidget(self.lst_prov)

        form_layout.addWidget(grp_pref)

        # 其他条件
        grp_other = QGroupBox("其他条件")
        fl_other = QFormLayout(grp_other)
        fl_other.setSpacing(8)
        fl_other.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.chk_private = QCheckBox("接受民办院校")
        self.chk_private.setChecked(True)
        fl_other.addRow("", self.chk_private)

        self.chk_joint = QCheckBox("接受中外合作办学")
        self.chk_joint.setChecked(True)
        fl_other.addRow("", self.chk_joint)

        self.cmb_batch = QComboBox()
        self.cmb_batch.addItems(["本科批", "本科提前批", "专科批", "全部"])
        fl_other.addRow("志愿批次：", self.cmb_batch)

        form_layout.addWidget(grp_other)
        form_layout.addStretch()

        scroll.setWidget(form_container)
        layout.addWidget(scroll)

        # ── 右侧：操作区 + 进度 ──────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 操作按钮区
        action_panel = ActionPanel()
        btn_layout = QVBoxLayout(action_panel)
        btn_layout.setContentsMargins(16, 16, 16, 16)
        btn_layout.setSpacing(12)

        lbl_ops = QLabel("操作")
        lbl_ops.setFont(QFont(Font.FAMILY, 12, QFont.Weight.Bold))
        lbl_ops.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        btn_layout.addWidget(lbl_ops)

        self.btn_generate = QPushButton("\U0001F680  开始生成96个志愿")
        self.btn_generate.setFixedHeight(48)
        self.btn_generate.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_generate.setFont(QFont(Font.FAMILY, 14, QFont.Weight.Bold))
        self.btn_generate.setStyleSheet(ComponentStyles.BTN_PRIMARY)
        self.btn_generate.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.btn_generate)

        self.btn_clear = QPushButton("\U0001F504  重置表单")
        self.btn_clear.setFixedHeight(40)
        self.btn_clear.setMinimumWidth(120)  # 防止被压扁
        self.btn_clear.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_clear.setStyleSheet(ComponentStyles.BTN_ACTION)
        self.btn_clear.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.btn_clear)

        right_layout.addWidget(action_panel)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # 日志输出
        grp_log = QGroupBox("运行日志")
        log_layout = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas", 10))
        self.txt_log.setStyleSheet(ComponentStyles.TERMINAL)
        log_layout.addWidget(self.txt_log)
        right_layout.addWidget(grp_log, 1)

        # 提示信息
        tip = TipBox(
            "\U0001F4A1 使用提示：\n"
            "\u2460 请先在【数据管理】页导入投档Excel数据\n"
            "\u2461 填写考生信息后点击「开始生成」\n"
            "\u2462 系统将自动生成96个冲稳保志愿\n"
            "\u2463 在【志愿结果】页查看并导出方案\n\n"
            "\u26A0 本系统推荐仅供参考，最终填报以官方为准",
            tip_type="warning"
        )
        right_layout.addWidget(tip)

        layout.addWidget(right, 1)

    def _log(self, msg: str):
        self.txt_log.append(f"[{self._ts()}] {msg}")
        self.txt_log.verticalScrollBar().setValue(
            self.txt_log.verticalScrollBar().maximum()
        )

    @staticmethod
    def _ts():
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def get_student_info(self) -> dict:
        selected_majors = [
            self.lst_major.item(i).text()
            for i in range(self.lst_major.count())
            if self.lst_major.item(i).isSelected() and self.lst_major.item(i).text() != "不限"
        ]
        selected_provs = [
            self.lst_prov.item(i).text()
            for i in range(self.lst_prov.count())
            if self.lst_prov.item(i).isSelected() and self.lst_prov.item(i).text() != "不限"
        ]
        rank_text = self.inp_rank_2026.text().strip()
        rank_2026 = int(rank_text) if rank_text.isdigit() and int(rank_text) > 0 else 0

        # 策略选项解析
        strat_map = {"普通家庭": "average", "富裕家庭": "wealthy", "困难家庭": "struggle"}
        work_map  = {"直接就业": "work", "考研深造": "graduate", "考公方向": "civil"}
        city_map  = {"愿意去外地": "yes", "优先在河北省内": "no"}

        strat_text = self.cmb_strategy.currentText().split("（")[0]
        work_text  = self.cmb_work.currentText().split("（")[0]
        city_text  = self.cmb_city_pref.currentText().split("（")[0]

        return {
            "name":            self.inp_name.text().strip() or "考生",
            "estimated_score": self.inp_score.value(),
            "extra_score":     self.inp_extra.value(),
            "rank_2026":       rank_2026,
            "subject_first":   self.cmb_first.currentText(),
            "subject_elective1": self.cmb_elec1.currentText(),
            "subject_elective2": self.cmb_elec2.currentText(),
            "color_vision":    self.cmb_color.currentText(),
            "naked_eye_vision": self._parse_vision(self.cmb_vision.currentText()),
            "gender":          self.cmb_gender.currentText(),
            "height_cm":       self.inp_height.value(),
            "weight_kg":       self.inp_weight.value(),
            "pref_majors":     selected_majors,
            "pref_provinces":  selected_provs,
            "accept_private":  self.chk_private.isChecked(),
            "accept_joint":    self.chk_joint.isChecked(),
            "rank_offset_neg":  self.slider_chong.value(),
            "rank_offset_pos":  self.slider_bao.value(),
            # 张雪峰策略
            "student_strategy": strat_map.get(strat_text, "average"),
            "work_preference":  work_map.get(work_text, "work"),
            "out_of_province":  city_map.get(city_text, "yes"),
        }

    def _update_rank_display(self):
        """实时更新考生位次显示"""
        score = self.inp_score.value() + self.inp_extra.value()
        subject = self.cmb_first.currentText()
        rank = self._query_rank(score, subject, 2025)
        year_label = "2025"
        if rank == 999999:
            rank = self._query_rank(score, subject, 2024)
            year_label = "2024"
        if rank == 999999:
            self.lbl_rank.setText(f"参考位次：--（{score}分对应位次未找到）")
        else:
            self.lbl_rank.setText(f"{year_label}参考位次：{rank:,}（{score}分 \u2248 {year_label}年第{rank:,}名）")
        if not self.inp_rank_2026.text().strip():
            if rank < 999999:
                self.inp_rank_2026.setPlaceholderText(f"留空则使用{year_label}参考位次 {rank:,}")

    def _on_slider_changed(self):
        chong = self.slider_chong.value()
        bao = self.slider_bao.value()

        if chong == 0 and bao == 0:
            self.lbl_slider_val.setText("当前：自动范围（将根据筛选条件设定）")
        else:
            chong_str = f"冲{chong:,}名" if chong > 0 else "不限"
            bao_str = f"保{bao:,}名" if bao > 0 else "不限"
            self.lbl_slider_val.setText(f"当前：{chong_str} / {bao_str}（严格按范围筛选）")
            self._log(f"位次范围已调整：冲{chong:,}名 / 保{bao:,}名")

        self.lbl_chong_val.setText(f"{chong:,}")
        self.lbl_bao_val.setText(f"{bao:,}")

    def _auto_set_rank_range(self):
        score = self.inp_score.value() + self.inp_extra.value()
        subject = self.cmb_first.currentText()
        student_rank = self._query_rank(score, subject, 2025)
        if student_rank == 999999:
            self.lbl_slider_val.setText("\u26A0 无法查询位次，请检查分数和科目")
            return

        # 向上冲5分对应的位次
        rank_chong = self._query_rank(score + 5, subject, 2025)
        # 向下保20分对应的位次
        rank_bao = self._query_rank(score - 20, subject, 2025)

        if rank_chong == 999999 or rank_bao == 999999:
            self.lbl_slider_val.setText("\u26A0 无法查询位次，请检查分数和科目")
            return

        # 冲的位次差 = 考生位次 - 冲方向位次（位次越小越好）
        chong_range = max(student_rank - rank_chong, 0)
        # 保的位次差 = 保方向位次 - 考生位次（位次越大越容易录取）
        bao_range = max(rank_bao - student_rank, 0)

        # 设置合理的最小值
        chong_range = max(chong_range, 3000)
        bao_range = max(bao_range, 5000)

        self.slider_chong.setRange(0, max(chong_range * 2, 20000))
        self.slider_bao.setRange(0, max(bao_range * 2, 20000))
        self.slider_chong.setValue(chong_range)
        self.slider_bao.setValue(bao_range)

        self.lbl_slider_val.setText(
            f"\u2705 自动设定：冲{chong_range:,}名 / 保{bao_range:,}名\n"
            f"   考生位次：{student_rank:,} (分数{score}分)"
        )
        self._log(f"自动计算位次范围：冲{chong_range:,}名 / 保{bao_range:,}名（考生位次{student_rank:,}，冲5分位次{rank_chong:,}，保20分位次{rank_bao:,}）")

    def _query_rank(self, score: int, subject: str, year: int) -> int:
        from ..core.engine import RecommendEngine
        temp_profile = StudentProfile(
            estimated_score=score,
            subject_first=subject
        )
        engine = RecommendEngine(temp_profile)
        return engine.get_rank(score, year)

    @staticmethod
    def _parse_vision(text: str) -> str:
        mapping = {
            "5.0及以上": "5.0",
            "4.9": "4.9",
            "4.8": "4.8",
            "4.7": "4.7",
            "4.6": "4.6",
            "4.5": "4.5",
            "4.3及以下": "4.3",
        }
        return mapping.get(text, "5.0")

    def _build_profile(self) -> StudentProfile:
        info = self.get_student_info()
        return StudentProfile(
            estimated_score    = info["estimated_score"],
            subject_first      = info["subject_first"],
            subject_elective1  = info["subject_elective1"],
            subject_elective2  = info["subject_elective2"],
            color_vision       = info["color_vision"],
            naked_eye_vision   = info["naked_eye_vision"],
            gender             = info["gender"],
            height_cm          = info["height_cm"],
            weight_kg          = info["weight_kg"],
            extra_score        = info["extra_score"],
            pref_majors        = info["pref_majors"],
            pref_provinces     = info["pref_provinces"],
            accept_private     = info["accept_private"],
            accept_joint       = info["accept_joint"],
            rank_2026          = info["rank_2026"],
            rank_offset_neg    = info["rank_offset_neg"],
            rank_offset_pos    = info["rank_offset_pos"],
            # 张雪峰策略字段
            student_strategy   = info["student_strategy"],
            work_preference    = info["work_preference"],
            out_of_province    = info["out_of_province"],
        )

    def _on_generate(self):
        rank_2026 = self.inp_rank_2026.text().strip()
        if not rank_2026:
            QMessageBox.warning(self, "提示",
                "请先输入您的2026年高考位次！\n\n"
                "位次是推荐引擎的核心基准，必须填写才能生成志愿。\n"
                "如果您不知道自己的位次，请咨询班主任或查询省教育考试院公布的一分一段表。")
            self.inp_rank_2026.setFocus()
            return

        profile = self._build_profile()
        batch   = self.cmb_batch.currentText()

        rank = self._query_rank(profile.estimated_score + profile.extra_score, profile.subject_first, 2025)
        rank_display = f"{profile.rank_2026:,}" if profile.rank_2026 > 0 else f"{rank:,}(2025参考)"
        self._log(f"开始生成志愿 | 分数:{profile.estimated_score}+{profile.extra_score} | "
                  f"位次:{rank_display} | 科目:{profile.subject_first} | 批次:{batch}")
        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._worker = RecommendWorker(profile, batch)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current, total, msg):
        self.progress_bar.setValue(int(current / total * 100))
        self._log(msg)

    def _on_finished(self, volunteers):
        self.progress_bar.setValue(100)
        self.btn_generate.setEnabled(True)
        self._log(f"\u2705 生成完成！共 {len(volunteers)} 个志愿")
        if not volunteers:
            QMessageBox.warning(self, "提示",
                "未生成任何志愿！\n\n可能原因：\n"
                "\u2460 数据库中无投档数据，请先导入Excel文件\n"
                "\u2461 筛选条件过严，无符合条件的院校专业\n"
                "\u2462 所选批次暂无数据")
            return
        self.volunteers_ready.emit(volunteers)

    def _on_error(self, msg):
        self.progress_bar.setVisible(False)
        self.btn_generate.setEnabled(True)
        self._log(f"\u274C 错误：{msg}")
        QMessageBox.critical(self, "错误", f"推荐引擎异常：\n{msg}")

    def _on_clear(self):
        self.inp_name.setText("考生")
        self.inp_score.setValue(550)
        self.inp_extra.setValue(0)
        self.inp_rank_2026.setText("")
        self.cmb_first.setCurrentIndex(0)
        self.cmb_elec1.setCurrentIndex(0)
        self.cmb_elec2.setCurrentIndex(0)
        self.cmb_color.setCurrentIndex(0)
        self.cmb_vision.setCurrentIndex(0)
        self.inp_height.setValue(170)
        self.inp_weight.setValue(60)
        self.slider_chong.setRange(0, 50000)
        self.slider_chong.setValue(0)
        self.slider_bao.setRange(0, 50000)
        self.slider_bao.setValue(0)
        self._update_rank_display()
        self.chk_private.setChecked(True)
        self.chk_joint.setChecked(True)
        self.txt_log.clear()
        self._log("表单已重置")
