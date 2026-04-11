"""
评分与概率计算
负责偏好打分、录取概率、风险等级、综合评分等
"""
import math
from .config import MAJOR_KEYWORDS


def calc_pref_score(item: dict, pref_majors: list, pref_provinces: list) -> float:
    """计算偏好匹配得分（0~1）"""
    score = 0.5  # 基础分
    major = item.get("major_name", "")
    province = item.get("province", "")

    # 专业匹配
    if pref_majors:
        matched = False
        for pm in pref_majors:
            if pm and pm in MAJOR_KEYWORDS:
                keywords = MAJOR_KEYWORDS[pm]
                for kw in keywords:
                    if kw in major:
                        score += 0.3
                        matched = True
                        break
            if matched:
                break

    # 省份匹配
    if pref_provinces:
        if province in pref_provinces:
            score += 0.2
    else:
        score += 0.1

    return min(score, 1.0)


def calc_prob_by_rank(rank_diff: float) -> float:
    """简化版：只用位次差计算录取概率

    rank_diff: 考生位次 - 专业2025年最低录取位次
        > 0: 考生位次更差（冲刺），正得越多越不安全，概率越低
        < 0: 考生位次更好（保底），负得越多越安全，概率越高
    """
    if rank_diff <= 0:
        return 0.97  # 保底，概率很高
    z = rank_diff / 15000
    return max(0.03, min(0.97, 1 / (1 + math.exp(z))))


def risk_level(prob: float) -> str:
    """风险等级判定"""
    if prob < 0.50:
        return "高"
    elif prob < 0.80:
        return "中"
    return "低"


def tier_from_prob(prob: float) -> str:
    """根据概率确定梯度标签"""
    if prob < 0.50:
        return "冲"
    elif prob < 0.80:
        return "稳"
    return "保"
