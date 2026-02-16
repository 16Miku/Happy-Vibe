"""生成 Monitor 托盘图标资源"""

from PIL import Image, ImageDraw
from pathlib import Path
import math

# 图标配置
SIZES = [16, 32, 64, 256]
STATES = {
    "normal": {"bg": "#4B5563", "fg": "#E5E7EB", "accent": "#9CA3AF", "glow": None},
    "active": {"bg": "#059669", "fg": "#FFFFFF", "accent": "#6EE7B7", "glow": "#34D399"},
    "flow": {"bg": "#7C3AED", "fg": "#FCD34D", "accent": "#C4B5FD", "glow": "#A78BFA"},
    "error": {"bg": "#DC2626", "fg": "#FFFFFF", "accent": "#FCA5A5", "glow": "#F87171"},
}

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """将十六进制颜色转换为 RGB 元组"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """将十六进制颜色转换为 RGBA 元组"""
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)

def draw_vibe_icon(draw: ImageDraw.Draw, size: int, colors: dict):
    """绘制 Vibe 风格图标 - 能量脉冲波形"""
    bg = hex_to_rgb(colors["bg"])
    fg = hex_to_rgb(colors["fg"])
    accent = hex_to_rgb(colors["accent"])

    center = size // 2
    radius = size // 2 - max(1, size // 16)

    # 绘制圆形背景
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=bg
    )

    # 绘制内圈装饰
    inner_radius = int(radius * 0.85)
    ring_width = max(1, size // 20)
    draw.ellipse(
        [center - inner_radius, center - inner_radius,
         center + inner_radius, center + inner_radius],
        outline=accent, width=ring_width
    )

    # 绘制能量波形 (三条脉冲线)
    wave_height = int(radius * 0.4)
    wave_width = int(radius * 0.5)
    stroke = max(1, size // 10)

    # 中间高波
    mid_y = center
    draw.line(
        [(center - wave_width, mid_y),
         (center - wave_width // 2, mid_y - wave_height),
         (center, mid_y),
         (center + wave_width // 2, mid_y + wave_height),
         (center + wave_width, mid_y)],
        fill=fg, width=stroke, joint="curve"
    )

    # 顶部能量点
    dot_radius = max(1, size // 10)
    dot_y = center - int(radius * 0.55)
    draw.ellipse(
        [center - dot_radius, dot_y - dot_radius,
         center + dot_radius, dot_y + dot_radius],
        fill=fg
    )

def generate_icons():
    """生成所有状态和尺寸的图标"""
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    for state_name, colors in STATES.items():
        for size in SIZES:
            # 创建透明背景图像
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # 绘制图标
            draw_vibe_icon(draw, size, colors)

            # 保存文件
            filename = f"icon_{state_name}_{size}.png"
            filepath = assets_dir / filename
            img.save(filepath, "PNG")
            print(f"[OK] Generated: {filename}")

    # 生成默认图标 (normal 32x32 的副本)
    default_src = assets_dir / "icon_normal_32.png"
    default_dst = assets_dir / "icon.png"
    if default_src.exists():
        Image.open(default_src).save(default_dst)
        print(f"[OK] Generated: icon.png (default)")

    print(f"\n共生成 {len(STATES) * len(SIZES) + 1} 个图标文件")

if __name__ == "__main__":
    generate_icons()
