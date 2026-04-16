"""
测试 filters.py —— 体检、选科、办学性质、位次过滤
所有测试使用内存数据库和 mock profile，不依赖真实数据
"""
import pytest
from src.core.models import StudentProfile
from src.core.filters import (
    passes_body_check,
    passes_filter,
    passes_rank_filter,
    major_matches,
    is_joint_program,
    parse_tuition_value,
    is_police_major,
)


# ═══════════════════════════════════════════════════════
# Fixture: 干净 profile（无偏好限制）
# ═══════════════════════════════════════════════════════

@pytest.fixture
def clean_profile():
    """创建一个无省份/专业偏好的测试 profile"""
    return StudentProfile(
        estimated_score=580,
        subject_first="物理",
        subject_elective1="化学",
        subject_elective2="生物",
        color_vision="正常",
        naked_eye_vision="5.0",
        gender="男",
        height_cm=175,
        weight_kg=65,
        accept_private=True,
        accept_joint=True,
        pref_majors=[],
        pref_provinces=[],
        rank_2026=74000,
    )


# ═══════════════════════════════════════════════════════
# 1. 色觉检查
# ═══════════════════════════════════════════════════════

class TestColorVision:
    """色觉异常过滤测试"""

    def test_normal_vision_passes_all(self, clean_profile):
        """正常色觉通过所有专业"""
        item = {"major_name": "化学", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True

    def test_color_weak_restricted_major(self, clean_profile):
        """色弱不能录取化学类专业"""
        clean_profile.color_vision = "色弱"
        item = {"major_name": "化学工程与工艺", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_color_weak_unrestricted_major(self, clean_profile):
        """色弱可以录取计算机类"""
        clean_profile.color_vision = "色弱"
        item = {"major_name": "计算机科学与技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True

    def test_color_blind_restricted_major(self, clean_profile):
        """色盲不能录取绘画类"""
        clean_profile.color_vision = "色盲"
        item = {"major_name": "绘画", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_color_blind_includes_color_weak(self, clean_profile):
        """色盲包含色弱限制"""
        clean_profile.color_vision = "色盲"
        item = {"major_name": "药学", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_color_blind_restricted_by_db_field(self, clean_profile):
        """数据库 body_restrict 字段优先"""
        clean_profile.color_vision = "色盲"
        item = {"major_name": "某特殊专业", "body_restrict": "色盲不录"}
        assert passes_body_check(item, clean_profile) is False

    def test_color_weak_restricted_by_db_field(self, clean_profile):
        """色弱受 body_restrict 限制"""
        clean_profile.color_vision = "色弱"
        item = {"major_name": "某特殊专业", "body_restrict": "色弱不录"}
        assert passes_body_check(item, clean_profile) is False

    def test_color_blind_catches_color_weak_db(self, clean_profile):
        """body_restrict 有"色弱"时，色盲也被拦截"""
        clean_profile.color_vision = "色盲"
        item = {"major_name": "某专业", "body_restrict": "色弱不录"}
        assert passes_body_check(item, clean_profile) is False


# ═══════════════════════════════════════════════════════
# 2. 视力检查
# ═══════════════════════════════════════════════════════

class TestVision:
    """裸眼视力过滤测试"""

    def test_normal_vision_passes(self, clean_profile):
        """5.0 以上视力通过"""
        item = {"major_name": "飞行技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True

    def test_below_5_0_blocks_flight(self, clean_profile):
        """视力低于5.0不能录取飞行技术"""
        clean_profile.naked_eye_vision = "4.9"
        item = {"major_name": "飞行技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_below_5_0_blocks_navigation(self, clean_profile):
        clean_profile.naked_eye_vision = "4.7"
        item = {"major_name": "航海技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_below_4_8_blocks_engine(self, clean_profile):
        clean_profile.naked_eye_vision = "4.7"
        item = {"major_name": "轮机工程", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_4_8_passes_5_0_restricted(self, clean_profile):
        clean_profile.naked_eye_vision = "4.8"
        item = {"major_name": "飞行技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_invalid_vision_defaults_to_normal(self, clean_profile):
        clean_profile.naked_eye_vision = "invalid"
        item = {"major_name": "飞行技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True


# ═══════════════════════════════════════════════════════
# 3. 身高体重检查
# ═══════════════════════════════════════════════════════

class TestHeightWeight:
    """身高体重过滤测试"""

    def test_police_male_height_ok(self, clean_profile):
        clean_profile.gender = "男"
        clean_profile.height_cm = 170
        item = {"major_name": "刑事科学技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True

    def test_police_male_height_fail(self, clean_profile):
        clean_profile.gender = "男"
        clean_profile.height_cm = 169
        item = {"major_name": "刑事科学技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_police_female_height_ok(self, clean_profile):
        clean_profile.gender = "女"
        clean_profile.height_cm = 160
        item = {"major_name": "侦查学", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True

    def test_police_female_height_fail(self, clean_profile):
        clean_profile.gender = "女"
        clean_profile.height_cm = 159
        item = {"major_name": "侦查学", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_police_male_weight_fail(self, clean_profile):
        clean_profile.gender = "男"
        clean_profile.weight_kg = 49
        item = {"major_name": "网络安全与执法", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_non_police_no_height_limit(self, clean_profile):
        clean_profile.height_cm = 150
        item = {"major_name": "计算机科学与技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is True

    def test_navigation_height(self, clean_profile):
        clean_profile.height_cm = 164
        item = {"major_name": "航海技术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False

    def test_female_broadcast_height(self, clean_profile):
        clean_profile.gender = "女"
        clean_profile.height_cm = 159
        item = {"major_name": "播音与主持艺术", "body_restrict": ""}
        assert passes_body_check(item, clean_profile) is False


# ═══════════════════════════════════════════════════════
# 4. 公安类专业识别
# ═══════════════════════════════════════════════════════

class TestPoliceMajor:
    def test_identifies_police(self):
        assert is_police_major("刑事科学技术") is True
        assert is_police_major("侦查学") is True
        assert is_police_major("网络安全与执法") is True

    def test_non_police(self):
        assert is_police_major("计算机科学与技术") is False
        assert is_police_major("土木工程") is False


# ═══════════════════════════════════════════════════════
# 5. 办学性质过滤（使用 clean_profile）
# ═══════════════════════════════════════════════════════

class TestCollegeNature:
    def test_accept_private_passes(self, clean_profile):
        item = {"college_nature": "民办"}
        assert passes_filter(item, clean_profile) is True

    def test_reject_private(self, clean_profile):
        clean_profile.accept_private = False
        item = {"college_nature": "民办"}
        assert passes_filter(item, clean_profile) is False

    def test_reject_independent(self, clean_profile):
        clean_profile.accept_private = False
        item = {"college_nature": "独立学院"}
        assert passes_filter(item, clean_profile) is False

    def test_accept_public(self, clean_profile):
        clean_profile.accept_private = False
        item = {"college_nature": "公办"}
        assert passes_filter(item, clean_profile) is True

    def test_reject_joint(self, clean_profile):
        clean_profile.accept_joint = False
        item = {"college_nature": "中外合作"}
        assert passes_filter(item, clean_profile) is False

    def test_reject_joint_when_marker_is_only_in_major_name(self, clean_profile):
        clean_profile.accept_joint = False
        item = {
            "college_nature": "公办",
            "major_name": "计算机科学与技术(中外合作办学)",
        }
        assert passes_filter(item, clean_profile) is False

    def test_accept_joint(self, clean_profile):
        item = {"college_nature": "中外合作"}
        assert passes_filter(item, clean_profile) is True


class TestJointProgramDetection:
    def test_detects_joint_from_college_nature(self):
        item = {"college_nature": "中外合作"}
        assert is_joint_program(item) is True

    def test_detects_joint_from_major_name(self):
        item = {"college_nature": "公办", "major_name": "金融学(中外合作办学)"}
        assert is_joint_program(item) is True

    def test_detects_joint_from_college_name(self):
        item = {"college_name": "某某大学[内地与港澳台地区合作办学]"}
        assert is_joint_program(item) is True


# ═══════════════════════════════════════════════════════
# 6. 选科要求过滤（使用 clean_profile）
# ═══════════════════════════════════════════════════════

class TestTuitionFilter:
    def test_parse_numeric_tuition(self):
        assert parse_tuition_value("20000") == 20000

    def test_parse_textual_tuition(self):
        assert parse_tuition_value("22000元/年") == 22000

    def test_parse_unknown_tuition_as_zero(self):
        assert parse_tuition_value("待定") == 0

    def test_reject_high_tuition_when_limit_set(self, clean_profile):
        clean_profile.max_tuition = 20000
        item = {"college_nature": "公办", "elective_req": "不限", "tuition": "22000"}
        assert passes_filter(item, clean_profile) is False

    def test_accept_low_tuition_when_limit_set(self, clean_profile):
        clean_profile.max_tuition = 20000
        item = {"college_nature": "公办", "elective_req": "不限", "tuition": "8000"}
        assert passes_filter(item, clean_profile) is True

    def test_unknown_tuition_not_filtered(self, clean_profile):
        clean_profile.max_tuition = 20000
        item = {"college_nature": "公办", "elective_req": "不限", "tuition": "待定"}
        assert passes_filter(item, clean_profile) is True


class TestElectiveRequirement:
    def test_no_requirement(self, clean_profile):
        item = {"elective_req": "不限"}
        assert passes_filter(item, clean_profile) is True

    def test_single_required_passes(self, clean_profile):
        item = {"elective_req": "化学"}
        assert passes_filter(item, clean_profile) is True

    def test_single_required_fails(self, clean_profile):
        clean_profile.subject_elective1 = "地理"
        clean_profile.subject_elective2 = "生物"
        item = {"elective_req": "化学"}
        assert passes_filter(item, clean_profile) is False

    def test_and_requirement_passes(self, clean_profile):
        item = {"elective_req": "化学和生物"}
        assert passes_filter(item, clean_profile) is True

    def test_and_requirement_fails(self, clean_profile):
        clean_profile.subject_elective2 = "地理"
        item = {"elective_req": "化学和生物"}
        assert passes_filter(item, clean_profile) is False

    def test_or_requirement_passes(self, clean_profile):
        item = {"elective_req": "化学或生物"}
        assert passes_filter(item, clean_profile) is True

    def test_or_requirement_fails(self, clean_profile):
        clean_profile.subject_elective1 = "地理"
        clean_profile.subject_elective2 = "政治"
        item = {"elective_req": "化学或生物"}
        assert passes_filter(item, clean_profile) is False


# ═══════════════════════════════════════════════════════
# 7. 省份和专业偏好过滤
# ═══════════════════════════════════════════════════════

class TestPrefFilter:
    def test_province_match(self, clean_profile):
        clean_profile.pref_provinces = ["北京", "河北"]
        item = {"province": "北京", "college_nature": "公办", "elective_req": "不限"}
        assert passes_filter(item, clean_profile, strict_province=True) is True

    def test_province_no_match(self, clean_profile):
        clean_profile.pref_provinces = ["北京"]
        item = {"province": "河北", "college_nature": "公办", "elective_req": "不限"}
        assert passes_filter(item, clean_profile, strict_province=True) is False

    def test_province_relaxed(self, clean_profile):
        clean_profile.pref_provinces = ["北京"]
        item = {"province": "河北", "college_nature": "公办", "elective_req": "不限"}
        assert passes_filter(item, clean_profile, strict_province=False) is True

    def test_major_match(self, clean_profile):
        clean_profile.pref_majors = ["计算机/信息技术"]
        item = {"major_name": "计算机科学与技术", "college_nature": "公办", "elective_req": "不限"}
        assert passes_filter(item, clean_profile, strict_major=True) is True

    def test_major_no_match(self, clean_profile):
        clean_profile.pref_majors = ["计算机/信息技术"]
        item = {"major_name": "学前教育", "college_nature": "公办", "elective_req": "不限"}
        assert passes_filter(item, clean_profile, strict_major=True) is False

    def test_major_relaxed(self, clean_profile):
        clean_profile.pref_majors = ["计算机/信息技术"]
        item = {"major_name": "学前教育", "college_nature": "公办", "elective_req": "不限"}
        assert passes_filter(item, clean_profile, strict_major=False) is True


# ═══════════════════════════════════════════════════════
# 8. 专业偏好匹配
# ═══════════════════════════════════════════════════════

class TestMajorMatches:
    def test_computer_keyword(self):
        assert major_matches("计算机科学与技术", ["计算机/信息技术"]) is True

    def test_software_keyword(self):
        assert major_matches("软件工程", ["计算机/信息技术"]) is True

    def test_ai_keyword(self):
        assert major_matches("人工智能", ["计算机/信息技术"]) is True

    def test_no_pref_always_matches(self):
        assert major_matches("任何专业", []) is True

    def test_no_match(self):
        assert major_matches("学前教育", ["计算机/信息技术"]) is False

    def test_multiple_prefs(self):
        assert major_matches("法学", ["计算机/信息技术", "法学/政治"]) is True


# ═══════════════════════════════════════════════════════
# 9. 位次筛选
# ═══════════════════════════════════════════════════════

class TestRankFilter:
    def test_within_range(self):
        item = {"min_rank": 50000}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 0) is True

    def test_below_range(self):
        item = {"min_rank": 5000}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 0) is False

    def test_above_range(self):
        item = {"min_rank": 70000}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 0) is False

    def test_exact_min(self):
        item = {"min_rank": 10000}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 0) is True

    def test_exact_max(self):
        item = {"min_rank": 60000}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 0) is True

    def test_no_rank_with_score(self):
        item = {"min_rank": None, "min_score": 600}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 50000) is True

    def test_no_rank_no_score(self):
        item = {"min_rank": None, "min_score": 0}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 0) is False

    def test_fallback_rank_too_high(self):
        item = {"min_rank": None, "min_score": 600}
        assert passes_rank_filter(item, 10000, 60000, lambda s, y: 999999) is False
