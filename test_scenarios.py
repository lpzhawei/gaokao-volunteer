"""
高考志愿推荐系统 - 场景测试程序

测试用例：
1. 物理类：570分，65000位
2. 历史类：480分，220000位

覆盖场景：
- 冲稳保比例验证
- 张雪峰视角策略差异
- 体检限制过滤
- 办学性质过滤
"""
import sys
import os

# 将项目根目录加入 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.models import StudentProfile
from src.core.engine import RecommendEngine
from src.core.config import get_nature_label, get_city_level_label


# 测试配置
TEST_PROFILES = [
    {
        "name": "物理类 - 中分段",
        "score": 570,
        "rank": 65000,
        "subject": "物理",
        "electives": ["化学", "生物"],
    },
    {
        "name": "历史类 - 低分段",
        "score": 480,
        "rank": 220000,
        "subject": "历史",
        "electives": ["政治", "地理"],
    },
]


def create_profile(test_case: dict, strategy: str = "average") -> StudentProfile:
    """创建考生档案"""
    return StudentProfile(
        estimated_score=test_case["score"],
        subject_first=test_case["subject"],
        subject_elective1=test_case["electives"][0],
        subject_elective2=test_case["electives"][1],
        color_vision="正常",
        naked_eye_vision="5.0",
        gender="男",
        height_cm=175,
        weight_kg=65,
        extra_score=0,
        pref_majors=[],
        pref_provinces=["河北"],
        accept_private=True,
        accept_joint=True,
        rank_2026=test_case["rank"],
        rank_offset_neg=0,
        rank_offset_pos=0,
        student_strategy=strategy,
        work_preference="work",
        out_of_province="yes",
    )


def print_header(text: str, width: int = 80):
    """打印分隔标题"""
    print("\n" + "=" * width)
    print(" " + text)
    print("=" * width)


def print_summary(results: list, profile: StudentProfile):
    """打印推荐结果汇总"""
    if not results:
        print("  [WARN] 未找到符合条件的志愿")
        return

    # 统计各梯度数量
    chong = [r for r in results if r.tier == "冲"]
    wen = [r for r in results if r.tier == "稳"]
    bao = [r for r in results if r.tier == "保"]

    print(f"\n  [STAT] 推荐结果统计（共 {len(results)} 个志愿）")
    print(f"  |-- 冲刺院校：{len(chong)} 个")
    print(f"  |-- 稳妥院校：{len(wen)} 个")
    print(f"  +-- 保底院校：{len(bao)} 个")

    # 按办学性质统计
    natures = {}
    for r in results:
        natures[r.college_nature] = natures.get(r.college_nature, 0) + 1
    print(f"\n  [BUILD] 办学性质分布：")
    for n, c in sorted(natures.items()):
        print(f"      {n}：{c} 个")

    # 按城市级别统计
    city_levels = {}
    for r in results:
        if r.city_level_label:
            city_levels[r.city_level_label] = city_levels.get(r.city_level_label, 0) + 1
    if city_levels:
        print(f"\n  [CITY] 城市级别分布：")
        for lvl, c in sorted(city_levels.items(), key=lambda x: ["一线", "新一线", "二线", "三线"].index(x[0]) if x[0] in ["一线", "新一线", "二线", "三线"] else 99):
            print(f"      {lvl}：{c} 个")

    # 录取概率分布
    probs = {"高": 0, "中": 0, "低": 0}
    for r in results:
        probs[r.risk_level] = probs.get(r.risk_level, 0) + 1
    print(f"\n  [PROB] 录取概率分布：")
    print(f"      高风险：{probs.get('低', 0)} 个（冲刺）")
    print(f"      中风险：{probs.get('中', 0)} 个（稳妥）")
    print(f"      低风险：{probs.get('高', 0)} 个（保底）")


def print_volunteer_list(results: list, profile: StudentProfile, top_n: int = 30):
    """打印志愿列表前N条"""
    if not results:
        return

    print(f"\n  [LIST] 志愿列表（前 {min(top_n, len(results))} 条）：")
    print(f"  {'序号':^4} {'院校名称':^20} {'专业名称':^16} {'梯度':^4} {'位次差':^8} {'概率':^6} {'推荐':^6}")
    print(f"  {'-'*70}")

    for i, item in enumerate(results[:top_n], 1):
        college = (item.college_name[:18] + "..") if len(item.college_name) > 20 else item.college_name
        major = (item.major_name[:14] + "..") if len(item.major_name) > 16 else item.major_name
        rank_diff_str = f"+{int(item.rank_diff):,}" if item.rank_diff > 0 else f"{int(item.rank_diff):,}"
        prob_str = f"{item.admit_prob:.0%}"
        recommend = item.recommend_index.replace("⭐", "+") if item.recommend_index else "-"

        print(f"  {i:^4} {college:<20} {major:<16} {item.tier:^4} {rank_diff_str:>8} {prob_str:^6} {recommend:^6}")

    if len(results) > top_n:
        print(f"  ... 还有 {len(results) - top_n} 条志愿")


def run_single_test(test_case: dict, strategy: str = "average"):
    """运行单个测试"""
    name = test_case["name"]
    strategy_names = {"average": "普通家庭", "wealthy": "富裕家庭", "struggle": "困难家庭"}

    print_header(f"测试用例：{name} | {test_case['score']}分 | 位次:{test_case['rank']:,} | 策略:{strategy_names[strategy]}")

    profile = create_profile(test_case, strategy)

    print(f"\n  [PROFILE] 考生信息：")
    print(f"     首选科目：{profile.subject_first}")
    print(f"     再选科目：{profile.subject_elective1} + {profile.subject_elective2}")
    print(f"     2026预估分：{profile.estimated_score} + {profile.extra_score} = {profile.estimated_score + profile.extra_score} 分")
    print(f"     2026位次：{profile.rank_2026:,}")
    print(f"     策略方向：{strategy_names[strategy]}")
    print(f"     未来目标：{profile.work_preference}")
    print(f"     地域偏好：{'省外' if profile.out_of_province == 'yes' else '省内'}")

    # 等效分
    engine = RecommendEngine(profile)
    eq_score = engine.get_student_equivalent_score(2025)
    print(f"\n  [EQUIV] 等效分转换（2026 -> 2025）：")
    print(f"     2026年 {profile.estimated_score} 分 / 位次 {profile.rank_2026:,}")
    print(f"     折算2025年 = {eq_score} 分" if eq_score > 0 else "     折算2025年 = 待查询")

    # 生成推荐
    print(f"\n  [GENERATING] 正在生成推荐方案...")
    results = engine.generate()

    if not results:
        print(f"\n  [WARN] 未能生成推荐结果")
        print(f"     可能原因：位次超出数据范围或筛选条件过严")
        return

    print_summary(results, profile)
    print_volunteer_list(results, profile, top_n=20)


def run_equivalent_score_test():
    """测试等效分转换"""
    print_header("等效分转换测试")

    test_cases = [
        (570, 65000, "物理"),
        (480, 220000, "历史"),
    ]

    for score, rank, subject in test_cases:
        profile = StudentProfile(
            estimated_score=score,
            subject_first=subject,
            rank_2026=rank,
        )
        engine = RecommendEngine(profile)

        print(f"\n  [{subject}] {score}分 / 位次 {rank:,}")

        for year in [2023, 2024, 2025]:
            eq_score = engine.get_student_equivalent_score(year)
            eq_str = f"{eq_score} 分" if eq_score > 0 else "超出范围"
            print(f"     {year}年等效分：{eq_str}")


def run_rank_conversion_test():
    """测试位次-分数互转"""
    print_header("位次-分数互转测试")

    test_cases = [
        (570, "物理"),
        (480, "历史"),
    ]

    for score, subject in test_cases:
        profile = StudentProfile(
            estimated_score=score,
            subject_first=subject,
            rank_2026=0,
        )
        engine = RecommendEngine(profile)

        print(f"\n  [{subject}] {score} 分 -> ", end="")
        rank = engine.get_rank(score, 2025)
        print(f"位次 {rank:,}")
        back_score = engine.get_score_by_rank(rank, 2025)
        print(f"  反查：{rank:,} -> {back_score} 分")


def run_filter_test():
    """测试筛选功能"""
    print_header("体检/选科筛选测试")

    from src.core.filters import passes_body_check

    test_cases = [
        (
            {"major_name": "计算机科学与技术", "body_restrict": "色盲不录;色弱不录", "color_restrict_detail": ""},
            StudentProfile(estimated_score=580, subject_first="物理", color_vision="正常", naked_eye_vision="5.0"),
            True, "正常视力通过色盲限制"
        ),
        (
            {"major_name": "化学工程", "body_restrict": "色弱不录", "color_restrict_detail": ""},
            StudentProfile(estimated_score=580, subject_first="物理", color_vision="色弱", naked_eye_vision="5.0"),
            False, "色弱不通过色弱限制"
        ),
        (
            {"major_name": "应用化学", "body_restrict": "色弱不录", "color_restrict_detail": ""},
            StudentProfile(estimated_score=580, subject_first="物理", color_vision="色盲", naked_eye_vision="5.0"),
            False, "色盲继承色弱限制"
        ),
        (
            {"major_name": "飞行技术", "body_restrict": "裸眼视力<5.0不录取", "color_restrict_detail": ""},
            StudentProfile(estimated_score=580, subject_first="物理", naked_eye_vision="4.5"),
            False, "视力4.5不通过飞行限制"
        ),
        (
            {"major_name": "航海技术", "body_restrict": "裸眼视力<4.8不录取", "color_restrict_detail": ""},
            StudentProfile(estimated_score=580, subject_first="物理", naked_eye_vision="4.6"),
            False, "视力4.6不通过航海限制"
        ),
    ]

    print(f"\n  {'场景':^20} {'体检限制':^25} {'预期':^6} {'实际':^6} {'结果':^6}")
    print(f"  {'-'*80}")

    for item, profile, expected, desc in test_cases:
        actual = passes_body_check(item, profile)
        result = "[OK]" if actual == expected else "[FAIL]"
        restrict_short = (item["body_restrict"][:23] + "..") if len(item["body_restrict"]) > 25 else item["body_restrict"]
        print(f"  {desc[:20]:^20} {restrict_short:^25} {str(expected):^6} {str(actual):^6} {result:^6}")


def main():
    """主函数"""
    print("\n")
    print("+" + "=" * 78 + "+")
    print("|" + "  高考志愿推荐系统 - 场景测试程序  ".center(78) + "|")
    print("|" + "  测试时间：2026-04-10".center(78) + "|")
    print("+" + "=" * 78 + "+")

    # 1. 等效分转换测试
    run_equivalent_score_test()

    # 2. 位次-分数互转测试
    run_rank_conversion_test()

    # 3. 筛选功能测试
    run_filter_test()

    # 4. 推荐引擎测试
    for test_case in TEST_PROFILES:
        for strategy in ["average", "wealthy", "struggle"]:
            run_single_test(test_case, strategy)

    # 5. 总结
    print_header("测试完成")
    print("\n  [DONE] 所有测试用例执行完毕")
    print("\n  说明：")
    print("     - 冲：录取概率 < 50%，有一定风险但值得尝试")
    print("     - 稳：录取概率 50% ~ 80%，比较稳妥")
    print("     - 保：录取概率 > 80%，基本能录取")
    print("     - 推荐指数：*越多越推荐（张雪峰视角）")
    print()


if __name__ == "__main__":
    main()
