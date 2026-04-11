"""
志愿结果面板
展示96个志愿列表、统计图表、支持导出
"""
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QMessageBox, QSplitter, QTabWidget,
    QTextEdit, QFrame, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush

from .theme import Colors, Font, Radius, Spacing, ComponentStyles
from .widgets import StatCard, TipBox

logger = logging.getLogger(__name__)

RISK_COLORS = {
    "高": QColor(Colors.RISK_HIGH),
    "中": QColor(Colors.RISK_MEDIUM),
    "低": QColor(Colors.RISK_LOW),
}


class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._volunteers = []
        self._student    = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── 顶部工具栏 ────────────────────────────────────
        toolbar = QWidget()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(8)

        # 筛选
        lbl_filter = QLabel("风险筛选：")
        lbl_filter.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; font-size: {Font.SIZE_BASE};")
        tb_layout.addWidget(lbl_filter)

        self.cmb_risk = QComboBox()
        self.cmb_risk.addItems(["全部", "高", "中", "低"])
        self.cmb_risk.currentTextChanged.connect(self._apply_filter)
        self.cmb_risk.setFixedWidth(80)
        tb_layout.addWidget(self.cmb_risk)

        lbl_search = QLabel("搜索：")
        lbl_search.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; font-size: {Font.SIZE_BASE};")
        tb_layout.addWidget(lbl_search)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("院校名/专业名关键字...")
        self.inp_search.setFixedWidth(200)
        self.inp_search.textChanged.connect(self._apply_filter)
        tb_layout.addWidget(self.inp_search)

        tb_layout.addStretch()

        self.btn_export_excel = QPushButton("\U0001F4CA  导出Excel")
        self.btn_export_excel.setFixedHeight(34)
        self.btn_export_excel.setStyleSheet(ComponentStyles.BTN_EXPORT)
        self.btn_export_excel.clicked.connect(self._export_excel)
        tb_layout.addWidget(self.btn_export_excel)

        self.btn_export_pdf = QPushButton("\U0001F4C4  导出PDF报告")
        self.btn_export_pdf.setFixedHeight(34)
        self.btn_export_pdf.setStyleSheet(ComponentStyles.BTN_EXPORT)
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        tb_layout.addWidget(self.btn_export_pdf)

        self.btn_hexagram = QPushButton("\U0001F4CA  六边形分析图")
        self.btn_hexagram.setFixedHeight(34)
        self.btn_hexagram.setStyleSheet(ComponentStyles.BTN_EXPORT)
        self.btn_hexagram.clicked.connect(self._show_hexagram)
        tb_layout.addWidget(self.btn_hexagram)

        layout.addWidget(toolbar)

        # ── 主体：表格 + 摘要 ─────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 志愿表格（扩展：+城市/+赛道/+性质/+学费/+风险描述 → 23列）
        self.table = QTableWidget(0, 24)
        self.table.setHorizontalHeaderLabels([
            "序号", "梯度", "院校名称", "专业名称", "批次", "省份", "城市", "城市级别",
            "办学性质", "专业赛道", "学费", "推荐指数",
            "近3年最低分", "近3年均分", "等效分", "分差", "位次差", "录取概率", "风险", "张雪峰提示",
            "最低位次", "2025年位次", "考生位次", "选科要求", "体检限制"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(15, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setFont(QFont(Font.FAMILY, 10))
        splitter.addWidget(self.table)

        # 右侧摘要面板
        right = QWidget()
        right.setFixedWidth(290)
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(4, 0, 4, 0)

        # ── 张雪峰提示横幅（天坑/避坑预警）──
        self.lbl_zxf_banner = QLabel()
        self.lbl_zxf_banner.setWordWrap(True)
        self.lbl_zxf_banner.setFont(QFont(Font.FAMILY, 9))
        self.lbl_zxf_banner.setStyleSheet(
            "background:#FFF3CD; color:#856404; border-radius:6px; "
            "padding:8px 10px; line-height:1.5; border:1px solid #FFEAA7;"
        )
        self.lbl_zxf_banner.setVisible(False)
        right_layout.addWidget(self.lbl_zxf_banner)

        # 统计卡片
        grp_stat = QGroupBox("汇总统计")
        self.stat_layout = QVBoxLayout(grp_stat)
        self.stat_layout.setSpacing(6)
        self.card_total = StatCard("总志愿数", "0", Colors.PRIMARY_500)
        self.card_high  = StatCard("高风险", "0", Colors.RISK_HIGH)
        self.card_mid   = StatCard("中风险", "0", Colors.RISK_MEDIUM)
        self.card_low   = StatCard("低风险", "0", Colors.RISK_LOW)
        for card in [self.card_total, self.card_high, self.card_mid, self.card_low]:
            self.stat_layout.addWidget(card)
        right_layout.addWidget(grp_stat)

        # ── 城市分布统计 ──────────────────────────────
        grp_city = QGroupBox("🏙️ 城市分布")
        city_layout = QVBoxLayout(grp_city)
        city_layout.setSpacing(4)
        self.lbl_city_stats = QLabel("（尚未生成）")
        self.lbl_city_stats.setWordWrap(True)
        self.lbl_city_stats.setFont(QFont(Font.FAMILY, 9))
        self.lbl_city_stats.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; line-height: 1.5; background: transparent;")
        city_layout.addWidget(self.lbl_city_stats)
        right_layout.addWidget(grp_city)

        # ── 张雪峰视角解读 ─────────────────────────────
        grp_zxf = QGroupBox("📌 张雪峰视角解读")
        zxf_layout = QVBoxLayout(grp_zxf)
        zxf_layout.setSpacing(4)
        self.lbl_zxf_tips = QLabel("（尚未生成）")
        self.lbl_zxf_tips.setWordWrap(True)
        self.lbl_zxf_tips.setFont(QFont(Font.FAMILY, 9))
        self.lbl_zxf_tips.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; line-height: 1.6; "
            "background: transparent;"
        )
        zxf_layout.addWidget(self.lbl_zxf_tips)
        right_layout.addWidget(grp_zxf)

        # 考生信息卡片
        self.grp_student = QGroupBox("考生信息")
        stu_layout = QVBoxLayout(self.grp_student)
        self.lbl_stu_info = QLabel("（尚未生成志愿）")
        self.lbl_stu_info.setWordWrap(True)
        self.lbl_stu_info.setFont(QFont(Font.FAMILY, 10))
        self.lbl_stu_info.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; line-height: 1.6;")
        stu_layout.addWidget(self.lbl_stu_info)
        right_layout.addWidget(self.grp_student)

        # 注意事项
        tip = TipBox(
            "\u26A0 注意事项：\n\n"
            "\u2460 本推荐仅供参考\n"
            "\u2461 请核对选科要求\n"
            "\u2462 注意招生计划数\n"
            "\u2463 以官方数据为准\n"
            "\u2464 最终方案自行决策",
            tip_type="warning"
        )
        right_layout.addWidget(tip)
        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([900, 280])
        layout.addWidget(splitter, 1)

        # 底部图例
        legend = QWidget()
        leg_hl = QHBoxLayout(legend)
        leg_hl.setContentsMargins(0, 0, 0, 0)
        leg_hl.setSpacing(4)

        lbl_sep = QLabel("  风险：")
        lbl_sep.setStyleSheet(f"color: {Colors.TEXT_HINT}; font-size: {Font.SIZE_SM}; background: transparent;")
        leg_hl.addWidget(lbl_sep)

        for risk, color in [("高风险", Colors.RISK_HIGH), ("中风险", Colors.RISK_MEDIUM), ("低风险", Colors.RISK_LOW)]:
            lbl = QLabel(f"  {risk}  ")
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; background: transparent;")
            leg_hl.addWidget(lbl)

        lbl_sep2 = QLabel("  |")
        lbl_sep2.setStyleSheet(f"color: {Colors.GRAY_300}; background: transparent;")
        leg_hl.addWidget(lbl_sep2)

        lbl_prov_relax = QLabel(" 省份（放宽）")
        lbl_prov_relax.setStyleSheet(f"color: {Colors.RISK_MEDIUM}; font-weight: bold; font-size: 11px; background: transparent;")
        lbl_prov_relax.setToolTip("省份候选不足，已自动补充其他省份")
        leg_hl.addWidget(lbl_prov_relax)

        lbl_sep3 = QLabel(" |")
        lbl_sep3.setStyleSheet(f"color: {Colors.GRAY_300}; background: transparent;")
        leg_hl.addWidget(lbl_sep3)

        lbl_major_relax = QLabel(" 专业（放宽）")
        lbl_major_relax.setStyleSheet(f"color: {Colors.RISK_MEDIUM}; font-weight: bold; font-size: 11px; background: transparent;")
        lbl_major_relax.setToolTip("专业候选不足，已自动补充其他专业")
        leg_hl.addWidget(lbl_major_relax)

        leg_hl.addStretch()
        layout.addWidget(legend)

    def load_volunteers(self, volunteers: list, student: dict):
        """加载志愿数据"""
        self._volunteers = volunteers
        self._student    = student
        self._apply_filter()
        self._update_stats()
        self._update_student_card(student)

    def _apply_filter(self):
        risk_f   = self.cmb_risk.currentText()
        search_f = self.inp_search.text().strip().lower()

        filtered = []
        for v in self._volunteers:
            if risk_f != "全部" and v.risk_level != risk_f:
                continue
            if search_f and search_f not in v.college_name.lower() and search_f not in v.major_name.lower():
                continue
            filtered.append(v)

        self.table.setRowCount(len(filtered))
        # 筛选后仍显示全量城市统计和张雪峰提示（基于全部96个志愿）
        self._update_zxf_banner()
        self._update_city_stats()
        for r, v in enumerate(filtered):
            # 省份列
            province_display = v.province
            if getattr(v, 'province_relaxed', False):
                province_display = f"{v.province}（放宽）"

            # 专业名称列
            major_display = v.major_name
            if getattr(v, 'major_relaxed', False):
                major_display = f"{v.major_name}（放宽）"

            # 办学性质（显眼化）
            nature_display = f"{v.nature_emoji} {v.nature_label}"
            # 专业赛道
            track_display = f"{v.track_emoji} {v.track_desc}" if v.track_emoji else "-"
            # 学费
            tuition_display = v.tuition if v.tuition else "-"
            # 城市级别
            city_level_display = f"{v.city_level_emoji} {v.city_level_label}" if v.city_level_emoji else "-"

            vals = [
                str(v.seq), v.tier, v.college_name, major_display,
                v.batch, province_display,
                v.city or "-",
                city_level_display,
                nature_display,
                track_display,
                tuition_display,
                v.recommend_index or "-",
                f"{v.min_score_3yr:.1f}", f"{v.avg_score_3yr:.1f}",
                f"{v.equivalent_score}" if v.equivalent_score > 0 else "-",
                f"{v.score_diff:+.1f}" if v.equivalent_score > 0 else "-",
                f"{int(v.rank_diff):+,}", f"{v.admit_prob:.0%}",
                v.risk_level, v.risk_desc,
                f"{v.min_rank:,}" if v.min_rank else "-",
                f"{v.min_rank_2025:,}" if v.min_rank_2025 else "-",
                f"{v.student_rank:,}",
                v.elective_req if v.elective_req and v.elective_req != "不限" else "不限",
                v.body_restrict if v.body_restrict else "-"
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # 推荐指数 → 加大字号醒目
                if c == 11 and val != "-":
                    item.setFont(QFont(Font.FAMILY, 13, QFont.Weight.Bold))
                # 专业名放宽
                if c == 3 and getattr(v, 'major_relaxed', False):
                    item.setForeground(QBrush(QColor(Colors.RISK_MEDIUM)))
                    item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                    item.setToolTip("您设置的专业偏好候选不足，\n已自动补充其他专业以填满96个志愿")
                # 省份放宽
                if c == 5 and getattr(v, 'province_relaxed', False):
                    item.setForeground(QBrush(QColor(Colors.RISK_MEDIUM)))
                    item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                    item.setToolTip("您设置的偏好省份候选不足，\n已自动补充其他省份院校以填满96个志愿")
                # 城市级别 → 颜色编码
                if c == 7:
                    if v.city_level_label in ("一线城市", "一线省会"):
                        item.setForeground(QBrush(QColor("#E53935")))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                    elif v.city_level_label in ("新一线", "新一线省会"):
                        item.setForeground(QBrush(QColor("#FB8C00")))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                # 办学性质 → 特殊颜色
                if c == 8:
                    if v.nature_label == "独立学院":
                        item.setForeground(QBrush(QColor("#E65100")))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                        item.setToolTip(v.nature_tip)
                    elif v.nature_label == "民办":
                        item.setForeground(QBrush(QColor(Colors.DANGER_DARK)))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                        item.setToolTip(v.nature_tip)
                    elif v.nature_label == "中外合作":
                        item.setForeground(QBrush(QColor("#6A1B9A")))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                        item.setToolTip(f"{v.nature_tip}\n{tuition_display}")
                # 专业赛道 → 颜色编码
                if c == 9:
                    if v.track_level == "热门":
                        item.setForeground(QBrush(QColor("#2E7D32")))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                        item.setToolTip("🔥 张雪峰推荐：热门赛道，就业前景好")
                    elif v.track_level == "天坑":
                        item.setForeground(QBrush(QColor(Colors.DANGER_DARK)))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                        item.setToolTip("⚠️ 张雪峰提醒：天坑专业需谨慎，就业难度大，考研才能活")
                    elif v.track_level == "避坑":
                        item.setForeground(QBrush(QColor("#880E4F")))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                        item.setToolTip("🚫 张雪峰提醒：强烈不建议普通家庭孩子报考！")
                # 学费警告
                if c == 10 and v.tuition_warn:
                    item.setForeground(QBrush(QColor("#6A1B9A")))
                    item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                    item.setToolTip(v.tuition_warn)
                # 风险列（c=17）
                if c == 17:
                    item.setForeground(QBrush(RISK_COLORS.get(v.risk_level, QColor("black"))))
                    item.setFont(QFont(Font.FAMILY, 10, QFont.Weight.Bold))
                # 张雪峰提示（c=18）
                if c == 18:
                    if "盲冲" in val or "高冲" in val:
                        item.setForeground(QBrush(QColor(Colors.DANGER_DARK)))
                        item.setFont(QFont(Font.FAMILY, 9, QFont.Weight.Bold))
                    elif "可冲" in val or "较稳" in val:
                        item.setForeground(QBrush(QColor(Colors.RISK_MEDIUM)))
                    elif "稳妥" in val:
                        item.setForeground(QBrush(QColor(Colors.SUCCESS)))
                    item.setFont(QFont(Font.FAMILY, 9))
                # 选科要求（c=22）
                if c == 22 and v.elective_req and v.elective_req != "不限":
                    item.setForeground(QBrush(QColor("#8E24AA")))
                    item.setFont(QFont(Font.FAMILY, 9))
                    item.setToolTip(f"该专业要求再选科目：{v.elective_req}")
                # 体检限制（c=23）
                if c == 23 and v.body_restrict:
                    item.setForeground(QBrush(QColor(Colors.DANGER_DARK)))
                    item.setFont(QFont(Font.FAMILY, 9))
                    item.setToolTip(v.body_restrict)
                self.table.setItem(r, c, item)

    def _update_stats(self):
        total = len(self._volunteers)
        high  = sum(1 for v in self._volunteers if v.risk_level == "高")
        mid   = sum(1 for v in self._volunteers if v.risk_level == "中")
        low   = sum(1 for v in self._volunteers if v.risk_level == "低")
        self.card_total.set_value(str(total))
        self.card_high.set_value(str(high))
        self.card_mid.set_value(str(mid))
        self.card_low.set_value(str(low))
        self._update_zxf_banner()
        self._update_city_stats()

    def _update_zxf_banner(self):
        """张雪峰视角：天坑/避坑专业预警横幅"""
        tiankeng = [v for v in self._volunteers if v.track_level in ("天坑", "避坑")]
        if not tiankeng:
            self.lbl_zxf_banner.setVisible(False)
            return

        # 按赛道分组
        by_track = {}
        for v in tiankeng:
            key = v.track_desc
            by_track.setdefault(key, []).append(v)

        lines = ["\U0001F6A8 张雪峰提醒：以下专业需谨慎对待"]
        for track, vols in by_track.items():
            majors = ", ".join(set(v.major_name[:8] for v in vols[:3]))
            if len(vols) > 3:
                majors += f"…等{len(vols)}个"
            level_icon = "\U0001DEDB" if vols[0].track_level == "避坑" else "\u26A0\uFE0F"
            lines.append(f"  {level_icon} {track}：{majors}")
        lines.append("  \u2192 建议：普通家庭优先选择\u201C🔥热门赛道\u201D专业")

        self.lbl_zxf_banner.setText("<br>".join(lines))
        self.lbl_zxf_banner.setVisible(True)

    def _update_city_stats(self):
        """城市分布统计 + 张雪峰式解读"""
        if not self._volunteers:
            self.lbl_city_stats.setText("（尚未生成）")
            self.lbl_zxf_tips.setText("（尚未生成）")
            return

        # 城市分布
        tier1 = sum(1 for v in self._volunteers if v.city_level_label in ("一线城市", "一线省会"))
        new1  = sum(1 for v in self._volunteers if v.city_level_label in ("新一线", "新一线省会"))
        tier2 = sum(1 for v in self._volunteers if v.city_level_label in ("二线城市", "二线省会"))
        other = sum(1 for v in self._volunteers if v.city_level_label not in (
            "一线城市", "一线省会", "新一线", "新一线省会", "二线城市", "二线省会"))
        total = len(self._volunteers)

        city_lines = [
            f"\uD83D\uDD34 一线城市: {tier1}个({tier1*100//total if total else 0}%)",
            f"\uD83D\uDDE1\uFE0F 新一线城市: {new1}个({new1*100//total if total else 0}%)",
            f"\uD83D\uDFE1 二线城市: {tier2}个({tier2*100//total if total else 0}%)",
            f"\u26AA 其他城市: {other}个",
        ]

        # ── 张雪峰视角综合解读 ───────────────────────
        strategy = self._student.get("student_strategy", "average")
        work_pref = self._student.get("work_preference", "work")

        zxf_lines = []
        # 城市维度
        if tier1 + new1 >= total * 0.5:
            zxf_lines.append("\U0001F3AF 城市推荐指数：\u2B50\u2B50\u2B50\u2B50 优秀！")
            zxf_lines.append("  \u2714 一线/新一线占比超过50%，城市资源优质")
        elif tier1 + new1 >= total * 0.25:
            zxf_lines.append("\U0001F3AF 城市推荐指数：\u2B50\u2B50 良好")
            zxf_lines.append("  \u26A0 建议：有条件优先冲一线/新一线城市")
        else:
            zxf_lines.append("\U0001F3AF 城市推荐指数：\u2B50 一般")
            zxf_lines.append("  \u26A0 张雪峰提醒：城市>学校>专业，能去大城市不去小城市！")

        # 天坑专业
        tiankeng = sum(1 for v in self._volunteers if v.track_level in ("天坑", "避坑"))
        if tiankeng > 0:
            zxf_lines.append(f"  \u26A0\uFE0F 含{tiankeng}个天坑/避坑专业，填报时注意规避")

        # 独立学院/民办
        private = sum(1 for v in self._volunteers if v.nature_label in ("独立学院", "民办"))
        if private > 0:
            zxf_lines.append(f"  \u26A0 含{private}个独立/民办院校，学费高、就业认可度低")

        # 策略提示
        if strategy == "wealthy":
            zxf_lines.append("  \uD83D\uDCB0 家庭条件较好：可适当多冲好城市好专业")
        elif strategy == "struggle":
            zxf_lines.append("  \u26D1 普通家庭：优先就业导向，保底要充足")

        self.lbl_city_stats.setText("<br>".join(city_lines))
        self.lbl_zxf_tips.setText("<br>".join(zxf_lines))

    def _update_student_card(self, s: dict):
        student_rank = s.get('student_rank', 0)
        rank_str = f"{student_rank:,}名" if student_rank else "未知"

        # 策略标签
        strat_map = {"wealthy": "富裕家庭", "average": "普通家庭", "struggle": "困难家庭"}
        work_map  = {"graduate": "考研深造", "civil": "考公方向", "work": "直接就业"}
        city_map  = {"yes": "愿意去外地", "no": "优先省内"}

        strat = strat_map.get(s.get('student_strategy', ''), "")
        work  = work_map.get(s.get('work_preference', ''), "")
        city  = city_map.get(s.get('out_of_province', ''), "")

        strat_line = f"家庭定位：{strat}\n" if strat else ""
        work_line  = f"目标方向：{work}\n" if work else ""
        city_line  = f"地域偏好：{city}\n" if city else ""

        info = (
            f"姓名：{s.get('name','考生')}\n"
            f"预估分：{s.get('estimated_score',0)}分"
            f"（+{s.get('extra_score',0)}加分）\n"
            f"首选科目：{s.get('subject_first','物理')}\n"
            f"再选：{s.get('subject_elective1','')}、{s.get('subject_elective2','')}\n"
            f"性别：{s.get('gender','男')}\n"
            f"色觉：{s.get('color_vision','正常')}\n"
            f"裸眼视力：{s.get('naked_eye_vision','5.0')}\n"
            f"身高：{s.get('height_cm',170)}cm  体重：{s.get('weight_kg',60)}kg\n"
            f"考生位次：{rank_str}\n"
            f"{strat_line}{work_line}{city_line}"
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.lbl_stu_info.setText(info)

    def _show_hexagram(self):
        """显示六边形分析图"""
        if not self._volunteers:
            QMessageBox.warning(self, "提示", "尚未生成志愿，请先生成推荐结果")
            return

        try:
            from ..gui.hexagram_chart import create_comparison_chart, draw_hexagram
            import tempfile, os
            from PyQt6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QLabel
            from PyQt6.QtGui import QPixmap
            from PyQt6.QtCore import Qt

            # 选择模式：单个 or 对比
            choice, ok = QInputDialog.getItem(
                self, "六边形分析图",
                "请选择分析模式：",
                ["Top5志愿对比（推荐）", "单个志愿详情"],
                0, False
            )
            if not ok:
                return

            with tempfile.TemporaryDirectory() as tmpdir:
                if "对比" in choice:
                    # 生成对比图
                    top_volunteers = self._volunteers[:5]
                    out_path = os.path.join(tmpdir, "hexagram_compare.png")
                    create_comparison_chart(top_volunteers, top_n=5, out_path=out_path)

                    dialog = QDialog(self)
                    dialog.setWindowTitle("六边形分析图 - Top5志愿对比")
                    dialog.resize(800, 800)
                    layout = QVBoxLayout(dialog)
                    pixmap = QPixmap(out_path)
                    lbl = QLabel()
                    lbl.setPixmap(pixmap.scaled(760, 760, Qt.AspectRatioMode.KeepAspectRatio))
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(lbl)
                else:
                    # 单个志愿详情
                    items = [f"{v.seq}. {v.college_name} / {v.major_name}" for v in self._volunteers]
                    item, ok = QInputDialog.getItem(
                        self, "选择志愿", "请选择要分析的志愿：", items, 0, False
                    )
                    if not ok:
                        return
                    seq = int(item.split(".")[0])
                    vol = next((v for v in self._volunteers if v.seq == seq), None)
                    if vol is None:
                        return
                    title = f"{vol.college_name} / {vol.major_name}"
                    out_path = os.path.join(tmpdir, "hexagram_single.png")
                    draw_hexagram(title, vol.major_track, vol.city_level, out_path)

                    dialog = QDialog(self)
                    dialog.setWindowTitle(f"六边形分析图 - {title}")
                    dialog.resize(720, 800)
                    layout = QVBoxLayout(dialog)
                    pixmap = QPixmap(out_path)
                    lbl = QLabel()
                    lbl.setPixmap(pixmap.scaled(680, 750, Qt.AspectRatioMode.KeepAspectRatio))
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(lbl)

                btn_close = QPushButton("关闭")
                btn_close.clicked.connect(dialog.accept)
                layout.addWidget(btn_close)
                dialog.exec()

        except ImportError as e:
            QMessageBox.warning(self, "提示", f"六边形分析图依赖 matplotlib\n请确认已安装：pip install matplotlib\n{str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成六边形图失败：\n{str(e)}")

    def _export_excel(self):
        if not self._volunteers:
            QMessageBox.warning(self, "提示", "尚未生成志愿，请先在【考生信息与推荐】页生成")
            return

        from datetime import datetime
        default_name = f"志愿表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", default_name,
            "Excel文件 (*.xlsx);;所有文件 (*)"
        )
        if not path:
            return

        try:
            from ..core.exporter import export_excel
            result_path = export_excel(self._volunteers, self._student, path)
            QMessageBox.information(self, "导出成功", f"Excel文件已保存至：\n{result_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _export_pdf(self):
        if not self._volunteers:
            QMessageBox.warning(self, "提示", "尚未生成志愿，请先在【考生信息与推荐】页生成")
            return

        from datetime import datetime
        default_name = f"志愿表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", default_name,
            "PDF文件 (*.pdf);;所有文件 (*)"
        )
        if not path:
            return

        try:
            from ..core.exporter import export_pdf
            result_path = export_pdf(self._volunteers, self._student, path)
            QMessageBox.information(self, "导出成功", f"PDF报告已保存至：\n{result_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
