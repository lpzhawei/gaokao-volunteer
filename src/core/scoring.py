"""
评分与概率计算
负责偏好打分、录取概率、风险等级、综合评分等
"""
from .config import MAJOR_KEYWORDS


# 基于 2023->2024、2024->2025 跨年回测做的经验校准点。
# rank_diff = 考生位次 - 上一年最低录取位次：
#   < 0 说明考生位次更好，录取概率应更高
#   > 0 说明考生位次更差，录取概率应更低
#
# 说明：
# - 物理、历史的跨年波动差异非常大，必须分科类校准
# - 这些点来自真实历史样本命中率，使用分段线性插值即可显著优于固定 sigmoid
PROB_CALIBRATION_POINTS = {
    "物理": [
        (-20000, 0.9955),
        (-15000, 0.9931),
        (-10000, 0.9874),
        (-5000, 0.9672),
        (-2000, 0.9221),
        (0, 0.8184),
        (2000, 0.6248),
        (5000, 0.4438),
        (8000, 0.3052),
        (10000, 0.2329),
        (15000, 0.1223),
        (20000, 0.0682),
        (30000, 0.0161),
    ],
    "历史": [
        (-20000, 0.9965),
        (-15000, 0.9945),
        (-10000, 0.9901),
        (-5000, 0.9477),
        (-2000, 0.7793),
        (0, 0.5006),
        (2000, 0.0851),
        (5000, 0.0229),
        (8000, 0.0124),
        (10000, 0.0092),
        (15000, 0.0064),
        (20000, 0.0040),
        (30000, 0.0019),
    ],
}


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


def calc_prob_by_rank(rank_diff: float, subject_type: str = "物理") -> float:
    """按科类校准的位次差录取概率

    rank_diff: 考生位次 - 上一年最低录取位次
        > 0: 考生位次更差（冲刺），正得越多越不安全，概率越低
        < 0: 考生位次更好（保底），负得越多越安全，概率越高

    subject_type:
        物理 / 历史。两者跨年波动差异较大，必须分别校准。
    """
    points = PROB_CALIBRATION_POINTS.get(subject_type) or PROB_CALIBRATION_POINTS["物理"]

    if rank_diff <= points[0][0]:
        return points[0][1]
    if rank_diff >= points[-1][0]:
        return points[-1][1]

    for idx in range(1, len(points)):
        x0, y0 = points[idx - 1]
        x1, y1 = points[idx]
        if rank_diff <= x1:
            ratio = (rank_diff - x0) / (x1 - x0)
            return y0 + (y1 - y0) * ratio

    return points[-1][1]


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
