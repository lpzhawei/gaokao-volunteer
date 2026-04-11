"""
生成河北省高考志愿填报系统程序图标
使用 Pillow 绘制精美矢量风格图标
"""
import math
from PIL import Image, ImageDraw, ImageFont
import os

# 颜色配置（深蓝 + 金色）
BG_DARK     = (15, 40, 90)       # 深蓝背景
BG_LIGHT    = (26, 68, 148)      # 中蓝
GOLD        = (212, 175, 55)     # 金色
GOLD_LIGHT  = (255, 220, 100)    # 亮金
WHITE       = (255, 255, 255)    # 白色
WHITE_T     = (255, 255, 255, 80)  # 半透明白
RED_ACCENT  = (220, 50, 50)      # 红色点缀（河北色）

def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=1):
    """绘制圆角矩形"""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill,
                           outline=outline, width=outline_width)

def create_icon(size):
    """创建指定尺寸的图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    
    s = size
    pad = int(s * 0.04)
    
    # === 背景：深蓝圆角矩形 ===
    radius = int(s * 0.18)
    # 渐变背景（用多层叠加模拟）
    for i in range(s):
        t = i / s
        r = int(BG_DARK[0] * (1-t) + BG_LIGHT[0] * t)
        g = int(BG_DARK[1] * (1-t) + BG_LIGHT[1] * t)
        b = int(BG_DARK[2] * (1-t) + BG_LIGHT[2] * t)
        draw.line([(0, i), (s, i)], fill=(r, g, b, 0))
    
    # 底色圆角矩形
    draw_rounded_rect(draw, [pad, pad, s-pad, s-pad], radius,
                      fill=BG_DARK, outline=None)
    
    # 内层渐变（亮蓝光晕效果）
    center_x, center_y = s // 2, int(s * 0.42)
    for r_step in range(int(s * 0.5), 0, -1):
        alpha = max(0, int(60 * (1 - r_step / (s * 0.5))))
        draw.ellipse([center_x - r_step, center_y - r_step,
                      center_x + r_step, center_y + r_step],
                     fill=(*BG_LIGHT, alpha))
    
    # === 学士帽 ===
    cap_cx = s // 2
    cap_cy = int(s * 0.34)
    
    # 帽顶板（菱形）
    board_half_w = int(s * 0.30)
    board_half_h = int(s * 0.10)
    board_points = [
        (cap_cx, cap_cy - board_half_h),          # 上
        (cap_cx + board_half_w, cap_cy),           # 右
        (cap_cx, cap_cy + board_half_h),           # 下
        (cap_cx - board_half_w, cap_cy),           # 左
    ]
    # 帽顶板阴影
    shadow_pts = [(x+3, y+3) for x, y in board_points]
    draw.polygon(shadow_pts, fill=(0, 0, 0, 80))
    # 帽顶板主体（金色渐变效果用两层）
    draw.polygon(board_points, fill=GOLD)
    # 高光
    highlight_pts = [
        (cap_cx, cap_cy - board_half_h + 4),
        (cap_cx + board_half_w - 8, cap_cy - 2),
        (cap_cx + board_half_w - 20, cap_cy + 2),
        (cap_cx, cap_cy - board_half_h + 12),
    ]
    draw.polygon(highlight_pts, fill=GOLD_LIGHT)
    
    # 帽顶装饰（中心点）
    dot_r = int(s * 0.025)
    draw.ellipse([cap_cx - dot_r, cap_cy - dot_r,
                  cap_cx + dot_r, cap_cy + dot_r], fill=WHITE)
    
    # 帽帽体（梯形）
    body_top_w = int(s * 0.16)
    body_bot_w = int(s * 0.22)
    body_top_y = cap_cy + int(s * 0.04)
    body_bot_y = cap_cy + int(s * 0.18)
    body_pts = [
        (cap_cx - body_top_w, body_top_y),
        (cap_cx + body_top_w, body_top_y),
        (cap_cx + body_bot_w, body_bot_y),
        (cap_cx - body_bot_w, body_bot_y),
    ]
    # 帽体阴影
    shadow_body = [(x+2, y+2) for x, y in body_pts]
    draw.polygon(shadow_body, fill=(0, 0, 0, 60))
    draw.polygon(body_pts, fill=GOLD)
    # 帽体高光线
    draw.line([(cap_cx - body_top_w + 6, body_top_y + 4),
               (cap_cx + body_top_w - 6, body_top_y + 4)],
              fill=GOLD_LIGHT, width=max(2, s//128))
    
    # 流苏绳（左侧）
    tassel_x = cap_cx - board_half_w + int(s * 0.02)
    tassel_top_y = cap_cy
    tassel_bot_y = cap_cy + int(s * 0.22)
    lw = max(2, s // 128)
    # 绳子弧线
    draw.line([(tassel_x, tassel_top_y),
               (tassel_x - int(s * 0.06), tassel_top_y + int(s * 0.08)),
               (tassel_x - int(s * 0.04), tassel_bot_y)],
              fill=GOLD, width=lw)
    # 流苏末端圆球
    ball_r = int(s * 0.025)
    bx = tassel_x - int(s * 0.04)
    by = tassel_bot_y
    draw.ellipse([bx - ball_r, by - ball_r,
                  bx + ball_r, by + ball_r], fill=GOLD)
    # 流苏穗
    for i in range(5):
        fx = bx + int((i - 2) * s * 0.012)
        fy_end = by + int(s * 0.06) + int(abs(i - 2) * s * 0.012)
        draw.line([(bx, by), (fx, fy_end)], fill=GOLD, width=max(1, s//256))
    
    # === 底部文字区域 ===
    text_y = int(s * 0.60)
    
    # 分割线（金色）
    line_y = int(s * 0.58)
    line_lw = max(1, s // 256)
    line_margin = int(s * 0.12)
    draw.line([(line_margin, line_y), (s - line_margin, line_y)],
              fill=(*GOLD, 180), width=line_lw)
    
    # 主文字"高考志愿"
    font_size_main = int(s * 0.16)
    font_size_sub  = int(s * 0.075)
    
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
    ]
    font_main = None
    font_sub  = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_main = ImageFont.truetype(fp, font_size_main)
                font_sub  = ImageFont.truetype(fp, font_size_sub)
                break
            except Exception:
                continue
    
    if font_main is None:
        font_main = ImageFont.load_default()
        font_sub  = ImageFont.load_default()
    
    # 主文字
    main_text = "高考志愿"
    bbox = draw.textbbox((0, 0), main_text, font=font_main)
    tw = bbox[2] - bbox[0]
    tx = (s - tw) // 2
    # 文字阴影
    draw.text((tx + 2, text_y + 2), main_text, font=font_main, fill=(0, 0, 0, 120))
    # 金色文字
    draw.text((tx, text_y), main_text, font=font_main, fill=GOLD)
    
    # 副文字
    sub_text = "智能填报系统"
    bbox_s = draw.textbbox((0, 0), sub_text, font=font_sub)
    sw = bbox_s[2] - bbox_s[0]
    sx = (s - sw) // 2
    sy = text_y + font_size_main + int(s * 0.02)
    draw.text((sx, sy), sub_text, font=font_sub, fill=(*WHITE, 200))
    
    # 底部小字"河北省"
    font_tiny_size = int(s * 0.055)
    try:
        font_tiny = ImageFont.truetype(font_paths[0], font_tiny_size)
    except:
        font_tiny = ImageFont.load_default()
    tiny_text = "河  北  省"
    bbox_t = draw.textbbox((0, 0), tiny_text, font=font_tiny)
    ttw = bbox_t[2] - bbox_t[0]
    ttx = (s - ttw) // 2
    tty = sy + font_size_sub + int(s * 0.02)
    draw.text((ttx, tty), tiny_text, font=font_tiny, fill=(*GOLD_LIGHT, 160))
    
    # === 边框装饰 ===
    border_pad = int(s * 0.05)
    border_r = int(s * 0.16)
    draw_rounded_rect(draw, [border_pad, border_pad, s - border_pad, s - border_pad],
                      border_r, fill=None,
                      outline=(*GOLD, 120), outline_width=max(2, s // 128))
    # 内边框（细）
    inner_pad = int(s * 0.065)
    inner_r = max(4, border_r - 4)
    if s - 2 * inner_pad > 2 * inner_r:
        draw_rounded_rect(draw, [inner_pad, inner_pad, s - inner_pad, s - inner_pad],
                          inner_r, fill=None,
                          outline=(*GOLD, 40), outline_width=max(1, s // 256))
    
    # === 四角装饰点 ===
    corner_pad = int(s * 0.10)
    corner_r = int(s * 0.018)
    corners = [
        (corner_pad, corner_pad),
        (s - corner_pad, corner_pad),
        (corner_pad, s - corner_pad),
        (s - corner_pad, s - corner_pad),
    ]
    for cx, cy in corners:
        draw.ellipse([cx - corner_r, cy - corner_r,
                      cx + corner_r, cy + corner_r], fill=(*GOLD, 160))
    
    # 应用圆角遮罩
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([pad, pad, s-pad, s-pad], radius=radius, fill=255)
    img.putalpha(mask)
    
    return img


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(out_dir, "resources")
    os.makedirs(resources_dir, exist_ok=True)
    
    # 生成各尺寸 PNG
    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    icon_images = {}
    
    print("正在生成图标...")
    for sz in sizes:
        icon = create_icon(sz)
        png_path = os.path.join(resources_dir, f"icon_{sz}.png")
        icon.save(png_path, "PNG")
        icon_images[sz] = icon
        print(f"  OK {sz}x{sz} -> {png_path}")
    
    # 保存主图标 PNG（256x256）
    main_png = os.path.join(resources_dir, "icon.png")
    icon_images[256].save(main_png, "PNG")
    print(f"  OK main icon -> {main_png}")
    
    # 生成 ICO（多尺寸嵌入）- 正确方式
    ico_path = os.path.join(resources_dir, "icon.ico")
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    # 使用第一张图作为基础，保存所有尺寸
    base_img = icon_images[ico_sizes[0]].convert("RGBA")
    append_imgs = [icon_images[sz].convert("RGBA") for sz in ico_sizes[1:]]
    base_img.save(
        ico_path,
        format="ICO",
        append_images=append_imgs
    )
    print(f"  OK ICO -> {ico_path}")
    
    print("\nIcon generation complete!")
    return ico_path, main_png


if __name__ == "__main__":
    main()
