"""
过滤规则
负责体检检查、选科过滤、办学性质过滤、位次筛选等
"""
from .config import (
    COLOR_WEAK_RESTRICTED_MAJORS,
    COLOR_BLIND_ADDITIONAL_MAJORS,
    COLOR_VISION_DEFICIENCY_ADDITIONAL_MAJORS,
    VISION_BELOW_5_0_MAJORS,
    VISION_BELOW_4_8_MAJORS,
    HEIGHT_RESTRICTED_MAJORS,
    POLICE_COLLEGE_BODY_REQUIREMENTS,
    POLICE_COLLEGE_KEYWORDS,
    COLOR_WEAK_CAN_APPLY,
    COLOR_BLIND_CAN_APPLY,
)


def is_police_major(major: str) -> bool:
    """判断专业是否属于公安类院校专业"""
    for kw in POLICE_COLLEGE_KEYWORDS:
        if kw in major:
            return True
    return False


def get_body_restrict_detail(item: dict, profile) -> dict:
    """
    返回考生对该专业的体检提示信息（可报/慎报）
    返回 dict: {
        "pass": bool,          # 是否符合体检要求
        "level": str,           # "ok"/"warn"/"reject"
        "color_msg": str,       # 色觉相关提示
        "vision_msg": str,     # 视力相关提示
        "height_msg": str,     # 身高相关提示
        "summary": str,        # 总体描述（张雪峰式）
    }
    """
    major = item.get("major_name", "") or ""
    color_msg = ""
    vision_msg = ""
    height_msg = ""
    warnings = []
    is_reject = False

    cv = profile.color_vision
    body_restrict = item.get("body_restrict", "") or ""
    color_detail = item.get("color_restrict_detail", "") or ""

    # ── 1. 色觉检查 ──────────────────────────
    if cv != "正常":
        if cv == "色盲":
            # 色盲考生应继承色弱限制（业务常识：色盲比色弱更严格）
            if "色盲" in body_restrict or "色盲" in color_detail:
                color_msg = "❌ 色盲不予录取"
                is_reject = True
            elif "色弱" in body_restrict or "色弱" in color_detail:
                # 色盲继承色弱限制
                color_msg = "❌ 色盲不录（含色弱限制）"
                is_reject = True
            else:
                # 尝试关键词判断：色盲应被所有色弱/色盲限制专业拦截
                blocked = any(rm in major for rm in COLOR_WEAK_RESTRICTED_MAJORS + COLOR_BLIND_ADDITIONAL_MAJORS + COLOR_VISION_DEFICIENCY_ADDITIONAL_MAJORS)
                if blocked:
                    color_msg = "❌ 该专业对色盲受限"
                    is_reject = True
                else:
                    color_msg = "✅ 未见色盲限制"
        elif cv == "色弱":
            if "色弱" in body_restrict or "色盲" in body_restrict:
                color_msg = "⚠️ 色弱/色盲受限"
                warnings.append("该专业对色弱考生受限，色盲更严格")
                is_reject = True
            elif "色盲" in color_detail:
                color_msg = "⚠️ 色弱考生请注意"
                warnings.append("专业备注含色盲限制，可能对色弱也受限")
                is_reject = True
            else:
                blocked = any(rm in major for rm in COLOR_WEAK_RESTRICTED_MAJORS)
                if blocked:
                    color_msg = "⚠️ 色弱受限专业"
                    warnings.append("部分医学/化工/生物专业对色弱受限")
                    is_reject = True
                else:
                    # 检查可报清单
                    can_apply = any(kw in major for kw in COLOR_WEAK_CAN_APPLY)
                    if can_apply:
                        color_msg = "✅ 该专业对色弱友好"
                    else:
                        color_msg = "⚠️ 色弱请确认"

    # ── 2. 裸眼视力检查 ───────────────────────
    try:
        vision_val = float(profile.naked_eye_vision)
    except (ValueError, TypeError):
        vision_val = 5.0

    if vision_val < 5.0:
        for vm in VISION_BELOW_5_0_MAJORS:
            if vm in major:
                vision_msg = f"⚠️ 裸眼视力{vision_val}，飞行/航海/刑侦要求<5.0"
                warnings.append(f"{vm}专业要求裸眼视力≥5.0")
                is_reject = True
                break

    if vision_val < 4.8:
        for vm in VISION_BELOW_4_8_MAJORS:
            if vm in major:
                vision_msg = f"⚠️ 裸眼视力{vision_val}，轮机/运动训练要求<4.8"
                warnings.append(f"{vm}专业要求裸眼视力≥4.8")
                is_reject = True
                break

    # ── 3. 身高体重检查 ───────────────────────
    height = profile.height_cm
    gender = profile.gender

    if is_police_major(major):
        req = POLICE_COLLEGE_BODY_REQUIREMENTS
        if gender == "男" and height < req["min_height_male"]:
            height_msg = f"❌ 身高{height}cm，公安类男≥170cm"
            is_reject = True
        elif gender == "女" and height < req["min_height_female"]:
            height_msg = f"❌ 身高{height}cm，公安类女≥160cm"
            is_reject = True
        else:
            height_msg = f"✅ 身高满足公安类要求"

    if "航海技术" in major and height < 165:
        height_msg = f"⚠️ 航海技术要求身高≥165cm"
        is_reject = True
    if "飞行技术" in major:
        limit = 170 if gender == "男" else 165
        if height < limit:
            height_msg = f"❌ 飞行技术要求身高≥{limit}cm"
            is_reject = True

    if gender == "女":
        for hrm in HEIGHT_RESTRICTED_MAJORS.get("min_160", []):
            if hrm in major and height < 160:
                height_msg = f"⚠️ {hrm}专业女身高建议≥160cm"
                warnings.append(f"{hrm}对女生身高有一定要求")
                is_reject = True

    # ── 4. 体重检查 ───────────────────────────
    weight_msg = ""
    weight = profile.weight_kg
    if is_police_major(major):
        req = POLICE_COLLEGE_BODY_REQUIREMENTS
        if gender == "男" and weight < req["min_weight_male"]:
            weight_msg = f"❌ 体重{weight}kg，公安类男≥50kg"
            is_reject = True
        elif gender == "女" and weight < req["min_weight_female"]:
            weight_msg = f"❌ 体重{weight}kg，公安类女≥45kg"
            is_reject = True

    # ── 汇总 ─────────────────────────────────
    if is_reject:
        level = "reject"
        summary = f"❌ 该专业不适合您（{'; '.join(warnings[:2]) if warnings else '体检受限'}）"
    elif warnings:
        level = "warn"
        summary = f"⚠️ 可报，但存在风险（{warnings[0]}）"
    else:
        level = "ok"
        summary = "✅ 体检无限制，可放心填报"

    return {
        "pass": not is_reject,
        "level": level,
        "color_msg": color_msg,
        "vision_msg": vision_msg,
        "height_msg": height_msg,
        "weight_msg": weight_msg,
        "warnings": warnings,
        "summary": summary,
    }


def passes_body_check(item: dict, profile) -> bool:
    """
    检查考生身体条件是否符合专业要求
    依据《普通高等学校招生体检工作指导意见》（2003年）
    优先使用数据库中的 body_restrict 字段，兜底使用专业名称关键词匹配
    """
    result = get_body_restrict_detail(item, profile)
    return result["pass"]


def major_matches(major_name: str, pref_majors: list) -> bool:
    """检查专业名称是否匹配用户偏好（使用关键词映射）"""
    if not pref_majors:
        return True
    from .config import MAJOR_KEYWORDS
    for pref_cat in pref_majors:
        if pref_cat and pref_cat in MAJOR_KEYWORDS:
            for kw in MAJOR_KEYWORDS[pref_cat]:
                if kw in major_name:
                    return True
    return False


def is_joint_program(item: dict) -> bool:
    """识别中外合作/合作办学项目。

    真实数据里有一部分记录会把项目性质写在 major_name，而 college_nature 仍然是“公办”。
    这里统一做多字段兜底，避免“不接受中外合作”时漏过滤。
    """
    markers = ("中外合作", "合作办学", "内地与港澳台地区合作办学")
    fields = (
        item.get("college_nature", "") or "",
        item.get("major_name", "") or "",
        item.get("college_name", "") or "",
    )
    return any(marker in field for field in fields for marker in markers)


def parse_tuition_value(tuition) -> int:
    """把数据库里的学费字段尽量解析成整数，无法识别时返回 0。"""
    if tuition is None:
        return 0

    if isinstance(tuition, (int, float)):
        return int(tuition)

    text = str(tuition).strip()
    if not text:
        return 0

    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def passes_filter(item: dict, profile, strict_province: bool = True,
                  strict_major: bool = True) -> bool:
    """综合筛选（办学性质、选科要求、省份偏好、专业偏好等）

    strict_province: True=省份硬过滤，False=不检查省份
    strict_major:   True=专业偏好硬过滤，False=不检查专业偏好
    """
    nature = item.get("college_nature", "公办")
    if not profile.accept_private and ("民办" in nature or "独立学院" in nature):
        return False
    if not profile.accept_joint and is_joint_program(item):
        return False
    if getattr(profile, "max_tuition", 0) > 0:
        tuition_val = parse_tuition_value(item.get("tuition", ""))
        if tuition_val >= profile.max_tuition:
            return False

    if strict_province and profile.pref_provinces:
        province = item.get("province", "")
        if province not in profile.pref_provinces:
            return False

    if strict_major and profile.pref_majors:
        major = item.get("major_name", "")
        if not major_matches(major, profile.pref_majors):
            return False

    # 再选科目要求过滤（兼容多种分隔符）
    elective_req = item.get("elective_req", "不限") or "不限"
    if elective_req != "不限":
        student_electives = {
            s for s in [profile.subject_elective1, profile.subject_elective2]
            if s and s not in ("不选", "")
        }
        # 兼容多种分隔符：中文逗号（，）、英文逗号（,）、斜杠（/）、顿号（、）、加号（+）、且（且）、或（|）
        if any(sep in elective_req for sep in ("或", "/", "，", ",", "、", "+", "|")):
            # 找到第一个分隔符
            for sep in ("或", "/", "，", ",", "、", "+", "|"):
                if sep in elective_req:
                    or_sep = sep
                    break
            required_any = {s.strip() for s in elective_req.split(or_sep) if s.strip()}
            if required_any and not required_any.intersection(student_electives):
                return False
        elif "和" in elective_req or "且" in elective_req:
            and_sep = "和" if "和" in elective_req else "且"
            required_all = {s.strip() for s in elective_req.split(and_sep) if s.strip()}
            if required_all and not required_all.issubset(student_electives):
                return False
        else:
            # 单字段精确匹配（如"物理"）
            required = {elective_req.strip()}
            if required and not required.issubset(student_electives):
                return False

    return True


def passes_rank_filter(item: dict, rank_min: int, rank_max: int,
                       get_rank_fn) -> bool:
    """位次筛选：直接用2025年数据中的min_rank字段

    get_rank_fn: (score, year) -> rank 的回调函数
    """
    raw_rank = item.get("min_rank") or 0
    if raw_rank > 0:
        rank_2025 = raw_rank
    else:
        score = item.get("min_score") or 0
        if score > 0:
            rank_2025 = get_rank_fn(score, 2025)
        else:
            return False

    if rank_2025 <= 0 or rank_2025 >= 999999:
        return False
    return rank_min <= rank_2025 <= rank_max
