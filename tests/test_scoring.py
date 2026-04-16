"""
测试 scoring.py —— 偏好打分、录取概率、风险等级
"""
import pytest
from src.core.scoring import (
    calc_pref_score,
    calc_prob_by_rank,
    risk_level,
    tier_from_prob,
)


class TestCalcProbByRank:
    """录取概率计算测试（正确逻辑：rank_diff>0 冲刺→低概率，<0 保底→高概率）"""

    def test_negative_rank_diff_high_prob(self):
        """考生位次更好（rank_diff < 0），高概率"""
        prob = calc_prob_by_rank(-10000)
        assert 0.98 < prob < 0.99  # 物理类保底，概率很高

    def test_zero_rank_diff_physics_calibrated(self):
        """物理类压线不是 97%，应接近历史回测值"""
        prob = calc_prob_by_rank(0)
        assert 0.80 < prob < 0.83

    def test_zero_rank_diff_history_calibrated(self):
        """历史类压线显著低于物理类"""
        prob = calc_prob_by_rank(0, "历史")
        assert 0.49 < prob < 0.51

    def test_small_positive_diff(self):
        """物理类小幅冲刺时仍有一定机会"""
        prob = calc_prob_by_rank(3000)
        assert 0.5 < prob < 0.6

    def test_history_small_positive_diff_drops_fast(self):
        """历史类对小幅冲刺更敏感"""
        prob = calc_prob_by_rank(2000, "历史")
        assert 0.08 < prob < 0.09

    def test_large_positive_diff(self):
        """位次差大（冲刺很远），概率很低"""
        prob = calc_prob_by_rank(30000)
        assert 0.01 < prob < 0.02

    def test_very_large_diff(self):
        """极大位次差（冲刺极远），概率贴近下限"""
        prob = calc_prob_by_rank(100000)
        assert prob < 0.02

    def test_probability_range(self):
        """概率始终在 [0, 1] 范围内"""
        for rd in [-50000, -1000, 0, 1000, 30000, 60000, 100000]:
            prob = calc_prob_by_rank(rd)
            assert 0.0 <= prob <= 1.0, f"rank_diff={rd}, prob={prob}"

    def test_chong_lower_prob_than_bao(self):
        """冲刺的概率应该低于保底（核心逻辑验证）"""
        prob_chong = calc_prob_by_rank(20000)  # 冲刺
        prob_bao = calc_prob_by_rank(-20000)   # 保底
        assert prob_chong < prob_bao, "冲刺(rank_diff>0)概率应低于保底(rank_diff<0)"


class TestRiskLevel:
    """风险等级测试"""

    def test_high_risk(self):
        assert risk_level(0.3) == "高"
        assert risk_level(0.49) == "高"

    def test_medium_risk(self):
        assert risk_level(0.5) == "中"
        assert risk_level(0.79) == "中"

    def test_low_risk(self):
        assert risk_level(0.8) == "低"
        assert risk_level(0.97) == "低"


class TestTierFromProb:
    """梯度标签测试"""

    def test_chong_tier(self):
        assert tier_from_prob(0.3) == "冲"
        assert tier_from_prob(0.49) == "冲"

    def test_wen_tier(self):
        assert tier_from_prob(0.5) == "稳"
        assert tier_from_prob(0.79) == "稳"

    def test_bao_tier(self):
        assert tier_from_prob(0.8) == "保"
        assert tier_from_prob(0.97) == "保"


class TestCalcPrefScore:
    """偏好匹配得分测试"""

    def test_base_score(self):
        """无偏好时基础分"""
        score = calc_pref_score(
            {"major_name": "计算机科学与技术", "province": "北京"},
            [], []
        )
        assert score == 0.5 + 0.1  # 基础分 + 不限地域加成

    def test_major_match(self):
        """专业偏好匹配加分"""
        score = calc_pref_score(
            {"major_name": "计算机科学与技术", "province": "北京"},
            ["计算机/信息技术"], []
        )
        assert score == 0.5 + 0.3 + 0.1  # 基础 + 专业 + 不限地域

    def test_province_match(self):
        """省份偏好匹配加分"""
        score = calc_pref_score(
            {"major_name": "某专业", "province": "北京"},
            [], ["北京"]
        )
        assert score == 0.5 + 0.2  # 基础 + 省份

    def test_both_match(self):
        """专业和省份都匹配"""
        score = calc_pref_score(
            {"major_name": "软件工程", "province": "北京"},
            ["计算机/信息技术"], ["北京"]
        )
        assert score == 0.5 + 0.3 + 0.2  # 基础 + 专业 + 省份

    def test_major_no_match(self):
        """专业偏好不匹配"""
        score = calc_pref_score(
            {"major_name": "学前教育", "province": "北京"},
            ["计算机/信息技术"], ["北京"]
        )
        assert score == 0.5 + 0.2  # 基础 + 省份（专业未加分）

    def test_score_capped_at_1(self):
        """得分不超过1.0"""
        score = calc_pref_score(
            {"major_name": "计算机科学与技术", "province": "北京"},
            ["计算机/信息技术"], ["北京"]
        )
        assert score <= 1.0

    def test_multiple_pref_categories(self):
        """多个偏好类别"""
        score = calc_pref_score(
            {"major_name": "法学", "province": "北京"},
            ["计算机/信息技术", "法学/政治"], ["北京"]
        )
        assert score == 0.5 + 0.3 + 0.2  # 基础 + 法学匹配 + 省份
