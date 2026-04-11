"""
数据模型
StudentProfile 和 VolunteerItem 的定义
"""
from dataclasses import dataclass, field


@dataclass
class StudentProfile:
    """考生信息"""
    estimated_score: int
    subject_first: str          # 物理/历史
    subject_elective1: str = ""
    subject_elective2: str = ""
    color_vision: str = "正常"  # 正常/色弱/色盲
    naked_eye_vision: str = "5.0"  # 裸眼视力（如 "5.0", "4.8", "4.5"）
    gender: str = "男"          # 男/女
    height_cm: int = 170
    weight_kg: int = 60         # 体重（kg）
    extra_score: int = 0
    pref_majors: list = field(default_factory=list)
    pref_provinces: list = field(default_factory=list)
    accept_private: bool = True
    accept_joint: bool = True
    max_tuition: int = 0        # 0=不限
    # 位次控制（双滑块独立控制冲/保方向）
    rank_2026: int = 0          # 用户手动输入的2026位次
    rank_offset_neg: int = 0    # 冲方向滑块值（位次向更好的方向浮动多少名）
    rank_offset_pos: int = 0    # 保方向滑块值（位次向更差的方向浮动多少名）
    # ── 张雪峰策略选项 ─────────────────────────
    student_strategy: str = "average"   # wealthy / average / struggle
    work_preference: str = "work"        # work / graduate / civil
    out_of_province: str = "yes"         # yes / no


@dataclass
class VolunteerItem:
    """志愿条目"""
    seq: int
    college_code: str
    college_name: str
    major_name: str
    subject_type: str
    batch: str
    tier: str
    min_score_3yr: float
    avg_score_3yr: float
    rank_diff: float            # 位次差：考生位次 - 专业最低录取位次
    admit_prob: float
    risk_level: str             # 高/中/低
    province: str = ""
    college_nature: str = "公办"
    plan_count: int = 0
    min_rank: int = 0            # 最低录取位次（2025年最新位次）
    min_rank_2025: int = 0       # 2025年录取最低位次
    student_rank: int = 0       # 考生位次
    body_restrict: str = ""     # 体检限制
    elective_req: str = "不限"  # 选科要求
    province_relaxed: bool = False  # 是否因省份候选不足而放宽了省份限制
    major_relaxed: bool = False     # 是否因专业偏好候选不足而放宽了专业限制
    # 等效分相关字段
    equivalent_score: int = 0    # 考生等效分（2026分数对应的2025等效分）
    score_diff: float = 0.0      # 分差：考生等效分 - 专业近3年平均分
    # ── 张雪峰视角新增字段 ─────────────────────
    city: str = ""               # 院校所在城市
    city_level: str = ""         # 城市级别（一线/新一线/二线...）
    city_level_emoji: str = "⚪"  # 城市级别emoji
    city_level_label: str = ""   # 城市级别简称
    major_track: str = ""         # 专业赛道（如"工：新工科和数学"）
    track_emoji: str = "🟡"      # 赛道emoji
    track_level: str = "普通"    # 赛道级别（热门/普通/天坑/避坑）
    track_desc: str = ""         # 赛道描述
    tuition: str = ""             # 学费（如"5000"/"待定"/"140000"）
    tuition_warn: str = ""        # 学费警告
    color_restrict_detail: str = ""  # 色觉限制详情
    nature_emoji: str = "🏛️"     # 办学性质emoji
    nature_label: str = ""        # 办学性质简称
    nature_tip: str = ""          # 办学性质提示
    risk_desc: str = ""           # 张雪峰式风险描述
    recommend_index: str = ""     # 综合推荐指数（如 "⭐⭐⭐⭐⭐"）

