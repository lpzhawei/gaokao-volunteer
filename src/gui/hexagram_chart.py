"""
六边形分析图（雷达图）
张雪峰视角：帮家长从6个维度快速评估院校/专业
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
from pathlib import Path
import platform

# ── 中文字体设置 ───────────────────────────────────────────────
def _get_cn_font(size=10):
    if platform.system() == "Windows":
        font_paths = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
        ]
    else:
        font_paths = ["/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]
    for fp in font_paths:
        if Path(fp).exists():
            return FontProperties(fname=fp, size=size)
    return plt.rcParams['font.sans-serif']


# ── 专业赛道 → 就业/考研/考公比例估算 ─────────────────────────
TRACK_EMPLOYMENT = {
    "工：新工科和数学":    {"就业": 0.88, "考研": 0.45, "考公": 0.08, "热度": 0.90},
    "医：临床口腔":         {"就业": 0.92, "考研": 0.60, "考公": 0.05, "热度": 0.95},
    "警：公安类":           {"就业": 0.95, "考研": 0.10, "考公": 0.75, "热度": 0.80},
    "工：力学能动交通海洋核安全": {"就业": 0.82, "考研": 0.35, "考公": 0.10, "热度": 0.70},
    "工：工科其他":         {"就业": 0.80, "考研": 0.38, "考公": 0.10, "热度": 0.65},
    "文：法学财会汉语言思政新传": {"就业": 0.72, "考研": 0.35, "考公": 0.55, "热度": 0.70},
    "文：大经济学类":      {"就业": 0.75, "考研": 0.40, "考公": 0.45, "热度": 0.72},
    "管：管理其他":         {"就业": 0.70, "考研": 0.30, "考公": 0.35, "热度": 0.55},
    "管：物流工工":        {"就业": 0.78, "考研": 0.25, "考公": 0.15, "热度": 0.60},
    "医：医学其他":         {"就业": 0.85, "考研": 0.55, "考公": 0.08, "热度": 0.75},
    "医：中医中西医":       {"就业": 0.82, "考研": 0.55, "考公": 0.10, "热度": 0.72},
    "理：理学其他":         {"就业": 0.55, "考研": 0.75, "考公": 0.20, "热度": 0.50},
    "理：地矿油":           {"就业": 0.70, "考研": 0.40, "考公": 0.12, "热度": 0.45},
    "工：生化环材食药":     {"就业": 0.45, "考研": 0.80, "考公": 0.12, "热度": 0.40},
    "农：农学植物":         {"就业": 0.40, "考研": 0.70, "考公": 0.15, "热度": 0.30},
    "农：农学动物":         {"就业": 0.45, "考研": 0.65, "考公": 0.15, "热度": 0.32},
    "文：文科其他":         {"就业": 0.50, "考研": 0.60, "考公": 0.40, "热度": 0.45},
    "艺：艺术":             {"就业": 0.55, "考研": 0.30, "考公": 0.12, "热度": 0.60},
    "试验班":               {"就业": 0.80, "考研": 0.70, "考公": 0.15, "热度": 0.78},
    "港校":                 {"就业": 0.78, "考研": 0.55, "考公": 0.20, "热度": 0.70},
    "军事":                 {"就业": 0.98, "考研": 0.05, "考公": 0.02, "热度": 0.60},
}

CITY_LEVEL_SCORES = {
    "一线城市":          {"城市机会": 0.95, "薪资水平": 0.90},
    "新一线城市":        {"城市机会": 0.82, "薪资水平": 0.78},
    "二线城市":          {"城市机会": 0.70, "薪资水平": 0.65},
    "三线城市":          {"城市机会": 0.55, "薪资水平": 0.52},
    "四线城市":          {"城市机会": 0.42, "薪资水平": 0.40},
    "五线城市":          {"城市机会": 0.32, "薪资水平": 0.32},
    "一线城市/省会城市":  {"城市机会": 0.95, "薪资水平": 0.90},
    "新一线城市/省会城市":{"城市机会": 0.82, "薪资水平": 0.78},
    "二线城市/省会城市":  {"城市机会": 0.70, "薪资水平": 0.65},
    "三线城市/省会城市":  {"城市机会": 0.55, "薪资水平": 0.52},
    "四线城市/省会城市":  {"城市机会": 0.42, "薪资水平": 0.40},
}


def get_track_data(major_track: str, city_level: str) -> dict:
    """根据专业赛道和城市级别估算六维数据"""
    track_data = TRACK_EMPLOYMENT.get(major_track, {"就业": 0.65, "考研": 0.35, "考公": 0.20, "热度": 0.60})

    city_data = {"城市机会": 0.60, "薪资水平": 0.60}
    for key, val in CITY_LEVEL_SCORES.items():
        if key and city_level and city_level.startswith(key.split("/")[0]):
            city_data = val
            break

    return {
        "就业率": track_data.get("就业", 0.65),
        "薪资水平": city_data.get("薪资水平", 0.60),
        "考研比例": track_data.get("考研", 0.35),
        "考公比例": track_data.get("考公", 0.20),
        "城市机会": city_data.get("城市机会", 0.60),
        "专业热度": track_data.get("热度", 0.60),
    }


def draw_hexagram(item_name: str, major_track: str, city_level: str,
                  out_path: str = None) -> str:
    """
    绘制六边形分析图（雷达图）

    参数:
        item_name: 院校专业名称（标题用）
        major_track: 专业赛道
        city_level: 城市级别
        out_path: 输出文件路径（不含后缀）
    """
    cn_font = _get_cn_font(10)

    data = get_track_data(major_track, city_level)
    labels = list(data.keys())
    values = list(data.values())

    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    values_plot = values + [values[0]]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#FAFBFC')
    ax.set_facecolor('#FAFBFC')

    # ── 背景网格 ───────────────────────────────────────────
    for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
        ax.plot(angles, [level] * (N + 1), color='#DDD', linewidth=0.5, linestyle='--')

    # ── 区域填充 ───────────────────────────────────────────
    ax.fill(angles, values_plot, color='#3498DB', alpha=0.20)
    ax.plot(angles, values_plot, color='#2980B9', linewidth=2.5, marker='o', markersize=7,
            markerfacecolor='white', markeredgecolor='#2980B9', markeredgewidth=2)

    # ── 标签 ───────────────────────────────────────────────
    label_colors = ['#27AE60', '#8E44AD', '#E67E22', '#C0392B', '#2980B9', '#F39C12']
    for i, (angle, label, val) in enumerate(zip(angles[:-1], labels, values[:-1])):
        offset = 0.12
        ha = 'center'
        if abs(angle - 0) < 0.01:
            ha = 'left'
        elif abs(angle - np.pi) < 0.01:
            ha = 'right'
        ax.text(angle, 1.0 + offset, label, fontproperties=cn_font, fontsize=9,
                ha=ha, va='center', color=label_colors[i % len(label_colors)], fontweight='bold')
        ax.text(angle, val + 0.04, f"{val:.0%}", fontproperties=cn_font, fontsize=8.5,
                ha='center', va='center', color='#333', fontweight='bold')

    # ── 标题 ───────────────────────────────────────────────
    track_emoji = {"热门": "[热]", "天坑": "[坑]", "避坑": "[慎]", "普通": "[中]"}.get(
        _get_track_level(major_track), "[中]")
    city_emoji = {"一线": "[一线]", "新一线": "[新一线]", "二线": "[二线]", "三线": "[三线]", "其他": "[其他]"}.get(
        city_level, "[其他]")

    title = f"{track_emoji} {item_name}\n{track_emoji} {major_track or '普通赛道'}  {city_emoji} {city_level or '未知城市'}"
    ax.set_title(title, fontproperties=cn_font, fontsize=12, fontweight='bold',
                 color='#2C3E50', pad=20)

    # ── 图例说明 ──────────────────────────────────────────
    zxf_tips = (
        "[提示] 张雪峰视角：\n"
        f"  就业率={data['就业率']:.0%} | 考研={data['考研比例']:.0%} | 考公={data['考公比例']:.0%}\n"
        f"  城市机会={data['城市机会']:.0%} | 薪资={data['薪资水平']:.0%} | 专业热度={data['专业热度']:.0%}\n"
        "  [注意] 数据基于专业赛道估算，仅供参考"
    )
    fig.text(0.5, 0.01, zxf_tips, fontproperties=cn_font, fontsize=7.5,
             ha='center', va='bottom', color='#888',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#F8F9FA', edgecolor='#DDD', alpha=0.8))

    ax.set_ylim(0, 1.15)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels([])

    plt.tight_layout(rect=[0, 0.06, 1, 1])

    if out_path:
        out_png = out_path if out_path.endswith('.png') else f"{out_path}.png"
        plt.savefig(out_png, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close()
        return out_png
    else:
        plt.show()
        return ""


def _get_track_level(major_track: str) -> str:
    from ..core.config import get_track_label
    _, lvl, _ = get_track_label(major_track)
    return lvl


def _get_city_emoji(city_level: str) -> str:
    """城市 emoji 已弃用，返回空字符串"""
    return ""


def create_comparison_chart(volunteers: list, top_n: int = 5,
                            out_path: str = None) -> str:
    """
    生成top_n个志愿的对比雷达图（多图层叠加）
    用于在同一图上对比多个院校专业的六维表现
    """
    cn_font = _get_cn_font(9)

    labels = ["就业率", "薪资水平", "考研比例", "考公比例", "城市机会", "专业热度"]
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#FAFBFC')
    ax.set_facecolor('#FAFBFC')

    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#9B59B6', '#F39C12', '#1ABC9C', '#E91E63', '#00BCD4']
    shown = 0
    for i, vol in enumerate(volunteers):
        if shown >= top_n:
            break
        data = get_track_data(getattr(vol, 'major_track', ''), getattr(vol, 'city_level', ''))
        values = list(data.values()) + [values[0]] if (values := list(data.values())) else None
        if values is None:
            continue
        label_str = f"{vol.college_name[:8]}/{vol.major_name[:6]}"
        ax.fill(angles, values, color=colors[shown % len(colors)], alpha=0.08)
        ax.plot(angles, values, color=colors[shown % len(colors)], linewidth=1.8,
                marker='o', markersize=4, label=label_str)
        shown += 1

    for level in [0.25, 0.5, 0.75, 1.0]:
        ax.plot(angles, [level] * (N + 1), color='#DDD', linewidth=0.5, linestyle='--')

    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontproperties=cn_font, fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels([])

    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.12), prop=cn_font, fontsize=8)
    ax.set_title("📊 院校专业六维对比（张雪峰视角）", fontproperties=cn_font,
                 fontsize=13, fontweight='bold', color='#2C3E50', pad=18)

    plt.tight_layout()
    if out_path:
        out_png = out_path if out_path.endswith('.png') else f"{out_path}.png"
        plt.savefig(out_png, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close()
        return out_png
    else:
        plt.show()
        return ""
