"""
Happy Vibe 游戏精灵资源生成器
生成像素风格的占位符精灵图
"""

from PIL import Image, ImageDraw
import os

# 基础路径
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES_PATH = os.path.join(BASE_PATH, "game", "assets", "sprites")

# 颜色定义
COLORS = {
    "player_body": (100, 149, 237),  # 蓝色
    "player_skin": (255, 218, 185),  # 肤色
    "player_hair": (139, 69, 19),    # 棕色头发

    # 作物颜色
    "variable_grass": (34, 139, 34),   # 绿色
    "code_cane": (255, 215, 0),        # 金色
    "bug_berry": (220, 20, 60),        # 红色
    "feature_fruit": (138, 43, 226),   # 紫色

    # 品质颜色边框
    "Q1": (169, 169, 169),  # 灰色 - 普通
    "Q2": (50, 205, 50),    # 绿色 - 良好
    "Q3": (30, 144, 255),   # 蓝色 - 优秀
    "Q4": (255, 215, 0),    # 金色 - 完美

    # 建筑颜色
    "warehouse": (139, 90, 43),
    "shop": (255, 165, 0),
    "laboratory": (70, 130, 180),
    "guild_hall": (128, 0, 128),
    "arena": (220, 20, 60),
    "bank": (255, 215, 0),
    "market": (34, 139, 34),
    "workshop": (105, 105, 105),
    "garden": (144, 238, 144),
    "tower": (75, 0, 130),

    # UI 颜色
    "button_normal": (70, 130, 180),
    "button_pressed": (50, 100, 150),
    "panel": (45, 45, 60),
    "energy": (255, 215, 0),
    "coin": (255, 215, 0),
    "diamond": (0, 191, 255),
}


def create_player_sprite(direction: str, frame: int, size: int = 32) -> Image.Image:
    """创建玩家精灵"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 身体位置偏移（模拟行走动画）
    offset_x = 0
    offset_y = 0
    if frame == 2:
        offset_y = -1
    elif frame == 3:
        offset_y = 1

    center_x = size // 2 + offset_x
    center_y = size // 2 + offset_y

    # 绘制身体（椭圆）
    body_top = center_y
    body_bottom = center_y + 12
    draw.ellipse([center_x - 6, body_top, center_x + 6, body_bottom],
                 fill=COLORS["player_body"])

    # 绘制头部
    head_y = center_y - 6
    draw.ellipse([center_x - 5, head_y - 5, center_x + 5, head_y + 5],
                 fill=COLORS["player_skin"])

    # 绘制头发
    draw.arc([center_x - 5, head_y - 6, center_x + 5, head_y + 2],
             0, 180, fill=COLORS["player_hair"], width=2)

    # 根据方向绘制眼睛
    if direction == "down":
        draw.point((center_x - 2, head_y), fill=(0, 0, 0))
        draw.point((center_x + 2, head_y), fill=(0, 0, 0))
    elif direction == "up":
        pass  # 背面不画眼睛
    elif direction == "left":
        draw.point((center_x - 3, head_y), fill=(0, 0, 0))
    elif direction == "right":
        draw.point((center_x + 3, head_y), fill=(0, 0, 0))

    # 绘制腿部（行走动画）
    leg_y = body_bottom
    if frame == 1:
        draw.line([(center_x - 3, leg_y), (center_x - 3, leg_y + 5)], fill=COLORS["player_body"], width=2)
        draw.line([(center_x + 3, leg_y), (center_x + 3, leg_y + 5)], fill=COLORS["player_body"], width=2)
    elif frame == 2:
        draw.line([(center_x - 4, leg_y), (center_x - 2, leg_y + 5)], fill=COLORS["player_body"], width=2)
        draw.line([(center_x + 2, leg_y), (center_x + 4, leg_y + 5)], fill=COLORS["player_body"], width=2)
    else:
        draw.line([(center_x - 2, leg_y), (center_x - 4, leg_y + 5)], fill=COLORS["player_body"], width=2)
        draw.line([(center_x + 4, leg_y), (center_x + 2, leg_y + 5)], fill=COLORS["player_body"], width=2)

    return img


def create_crop_sprite(crop_type: str, quality: str, stage: int, size: int = 32) -> Image.Image:
    """创建作物精灵"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    crop_color = COLORS.get(crop_type, (100, 100, 100))
    quality_color = COLORS.get(quality, (169, 169, 169))

    center_x = size // 2
    ground_y = size - 4

    # 根据生长阶段绘制
    if stage == 1:  # 种子/幼苗
        # 土壤
        draw.rectangle([center_x - 8, ground_y - 2, center_x + 8, ground_y + 2],
                      fill=(139, 90, 43))
        # 小芽
        draw.line([(center_x, ground_y - 2), (center_x, ground_y - 6)],
                 fill=(34, 139, 34), width=2)
        draw.ellipse([center_x - 2, ground_y - 8, center_x + 2, ground_y - 5],
                    fill=(144, 238, 144))

    elif stage == 2:  # 生长中
        # 土壤
        draw.rectangle([center_x - 8, ground_y - 2, center_x + 8, ground_y + 2],
                      fill=(139, 90, 43))
        # 茎
        draw.line([(center_x, ground_y - 2), (center_x, ground_y - 14)],
                 fill=(34, 139, 34), width=2)
        # 叶子
        draw.ellipse([center_x - 6, ground_y - 12, center_x - 1, ground_y - 8],
                    fill=(34, 139, 34))
        draw.ellipse([center_x + 1, ground_y - 14, center_x + 6, ground_y - 10],
                    fill=(34, 139, 34))

    else:  # stage == 3, 成熟
        # 土壤
        draw.rectangle([center_x - 8, ground_y - 2, center_x + 8, ground_y + 2],
                      fill=(139, 90, 43))
        # 茎
        draw.line([(center_x, ground_y - 2), (center_x, ground_y - 18)],
                 fill=(34, 139, 34), width=2)
        # 叶子
        draw.ellipse([center_x - 8, ground_y - 14, center_x - 2, ground_y - 8],
                    fill=(34, 139, 34))
        draw.ellipse([center_x + 2, ground_y - 16, center_x + 8, ground_y - 10],
                    fill=(34, 139, 34))
        # 果实
        draw.ellipse([center_x - 4, ground_y - 22, center_x + 4, ground_y - 16],
                    fill=crop_color)
        # 品质边框
        draw.arc([center_x - 5, ground_y - 23, center_x + 5, ground_y - 15],
                0, 360, fill=quality_color, width=1)

    return img


def create_building_sprite(building_type: str, size: int = 64) -> Image.Image:
    """创建建筑精灵"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    color = COLORS.get(building_type, (128, 128, 128))
    darker = tuple(max(0, c - 40) for c in color)

    # 基础建筑形状
    base_y = size - 8

    # 地基
    draw.rectangle([8, base_y - 4, size - 8, base_y + 4], fill=(100, 100, 100))

    # 主体
    draw.rectangle([12, base_y - 36, size - 12, base_y - 4], fill=color)

    # 屋顶
    draw.polygon([
        (6, base_y - 36),
        (size // 2, base_y - 52),
        (size - 6, base_y - 36)
    ], fill=darker)

    # 门
    draw.rectangle([size // 2 - 6, base_y - 20, size // 2 + 6, base_y - 4],
                  fill=(80, 50, 20))

    # 窗户
    draw.rectangle([18, base_y - 30, 26, base_y - 22], fill=(200, 230, 255))
    draw.rectangle([size - 26, base_y - 30, size - 18, base_y - 22], fill=(200, 230, 255))

    return img


def create_ui_button(state: str, size: tuple = (64, 24)) -> Image.Image:
    """创建 UI 按钮"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if state == "normal":
        color = COLORS["button_normal"]
    else:
        color = COLORS["button_pressed"]

    darker = tuple(max(0, c - 30) for c in color)
    lighter = tuple(min(255, c + 30) for c in color)

    # 按钮主体
    draw.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=4, fill=color)

    # 高光
    draw.line([(2, 2), (size[0] - 3, 2)], fill=lighter, width=1)

    # 阴影
    draw.line([(2, size[1] - 3), (size[0] - 3, size[1] - 3)], fill=darker, width=1)

    return img


def create_ui_panel(size: tuple = (128, 96)) -> Image.Image:
    """创建 UI 面板"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 面板背景
    draw.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=8,
                          fill=(45, 45, 60, 230))

    # 边框
    draw.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=8,
                          outline=(100, 100, 120), width=2)

    return img


def create_icon(icon_type: str, size: int = 24) -> Image.Image:
    """创建图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    if icon_type == "energy":
        # 闪电图标
        points = [
            (center + 2, 2),
            (center - 4, center),
            (center, center),
            (center - 2, size - 2),
            (center + 4, center),
            (center, center),
        ]
        draw.polygon(points, fill=COLORS["energy"])

    elif icon_type == "coin":
        # 金币图标
        draw.ellipse([2, 2, size - 3, size - 3], fill=COLORS["coin"])
        draw.ellipse([4, 4, size - 5, size - 5], fill=(255, 235, 100))
        draw.text((center - 3, center - 6), "$", fill=(200, 150, 0))

    elif icon_type == "diamond":
        # 钻石图标
        points = [
            (center, 2),
            (size - 4, center - 2),
            (center, size - 4),
            (4, center - 2),
        ]
        draw.polygon(points, fill=COLORS["diamond"])
        draw.polygon(points, outline=(255, 255, 255), width=1)

    elif icon_type == "heart":
        # 心形图标
        draw.ellipse([3, 5, center, center + 2], fill=(255, 80, 80))
        draw.ellipse([center, 5, size - 3, center + 2], fill=(255, 80, 80))
        draw.polygon([
            (4, center - 1),
            (center, size - 4),
            (size - 4, center - 1),
        ], fill=(255, 80, 80))

    elif icon_type == "star":
        # 星星图标
        import math
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = size // 2 - 2 if i % 2 == 0 else size // 4
            x = center + r * math.cos(angle)
            y = center - r * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=(255, 215, 0))

    elif icon_type == "settings":
        # 齿轮图标
        draw.ellipse([6, 6, size - 6, size - 6], fill=(150, 150, 150))
        draw.ellipse([9, 9, size - 9, size - 9], fill=(100, 100, 100))
        # 齿轮齿
        for i in range(8):
            import math
            angle = i * math.pi / 4
            x1 = center + 8 * math.cos(angle)
            y1 = center + 8 * math.sin(angle)
            x2 = center + 11 * math.cos(angle)
            y2 = center + 11 * math.sin(angle)
            draw.line([(x1, y1), (x2, y2)], fill=(150, 150, 150), width=3)

    elif icon_type == "menu":
        # 菜单图标（三条横线）
        draw.rectangle([4, 6, size - 4, 8], fill=(200, 200, 200))
        draw.rectangle([4, center - 1, size - 4, center + 1], fill=(200, 200, 200))
        draw.rectangle([4, size - 8, size - 4, size - 6], fill=(200, 200, 200))

    elif icon_type == "close":
        # 关闭图标
        draw.line([(6, 6), (size - 6, size - 6)], fill=(255, 100, 100), width=3)
        draw.line([(size - 6, 6), (6, size - 6)], fill=(255, 100, 100), width=3)

    elif icon_type == "check":
        # 勾选图标
        draw.line([(4, center), (center - 2, size - 6)], fill=(100, 255, 100), width=3)
        draw.line([(center - 2, size - 6), (size - 4, 6)], fill=(100, 255, 100), width=3)

    elif icon_type == "arrow_up":
        draw.polygon([
            (center, 4),
            (size - 6, size - 8),
            (6, size - 8),
        ], fill=(200, 200, 200))

    elif icon_type == "arrow_down":
        draw.polygon([
            (center, size - 4),
            (size - 6, 8),
            (6, 8),
        ], fill=(200, 200, 200))

    elif icon_type == "arrow_left":
        draw.polygon([
            (4, center),
            (size - 8, 6),
            (size - 8, size - 6),
        ], fill=(200, 200, 200))

    elif icon_type == "arrow_right":
        draw.polygon([
            (size - 4, center),
            (8, 6),
            (8, size - 6),
        ], fill=(200, 200, 200))

    return img


def create_item_sprite(item_type: str, size: int = 32) -> Image.Image:
    """创建物品精灵"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    if item_type == "seed":
        # 种子
        draw.ellipse([center - 4, center - 2, center + 4, center + 4],
                    fill=(139, 90, 43))
        draw.ellipse([center - 3, center - 1, center + 3, center + 3],
                    fill=(160, 110, 60))

    elif item_type == "fertilizer":
        # 肥料袋
        draw.rectangle([center - 8, center - 6, center + 8, center + 8],
                      fill=(80, 60, 40))
        draw.rectangle([center - 6, center - 4, center + 6, center + 6],
                      fill=(100, 80, 50))

    elif item_type == "water":
        # 水滴
        draw.polygon([
            (center, center - 8),
            (center + 6, center + 4),
            (center, center + 8),
            (center - 6, center + 4),
        ], fill=(100, 180, 255))

    elif item_type == "tool":
        # 工具（锄头）
        draw.rectangle([center - 2, center - 10, center + 2, center + 8],
                      fill=(139, 90, 43))
        draw.rectangle([center - 6, center - 10, center + 6, center - 6],
                      fill=(150, 150, 150))

    return img


def create_effect_sprite(effect_type: str, size: int = 32) -> Image.Image:
    """创建特效精灵"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    if effect_type == "sparkle":
        # 闪光效果
        for i in range(4):
            import math
            angle = i * math.pi / 2
            x = center + 8 * math.cos(angle)
            y = center + 8 * math.sin(angle)
            draw.line([(center, center), (x, y)], fill=(255, 255, 200, 200), width=2)
        draw.ellipse([center - 3, center - 3, center + 3, center + 3],
                    fill=(255, 255, 255))

    elif effect_type == "levelup":
        # 升级效果
        draw.polygon([
            (center, 2),
            (center + 10, center + 6),
            (center + 4, center + 6),
            (center + 4, size - 2),
            (center - 4, size - 2),
            (center - 4, center + 6),
            (center - 10, center + 6),
        ], fill=(255, 215, 0))

    elif effect_type == "heal":
        # 治疗效果（十字）
        draw.rectangle([center - 2, center - 8, center + 2, center + 8],
                      fill=(100, 255, 100))
        draw.rectangle([center - 8, center - 2, center + 8, center + 2],
                      fill=(100, 255, 100))

    return img


def main():
    """生成所有精灵资源"""
    os.makedirs(SPRITES_PATH, exist_ok=True)

    # 1. 生成玩家精灵
    print("生成玩家精灵...")
    player_path = os.path.join(SPRITES_PATH, "player")
    os.makedirs(player_path, exist_ok=True)

    directions = ["down", "up", "left", "right"]
    for direction in directions:
        for frame in range(1, 4):
            sprite = create_player_sprite(direction, frame)
            filename = f"player_{direction}_{frame}.png"
            sprite.save(os.path.join(player_path, filename))
            print(f"  [OK] {filename}")

    # 2. 生成作物精灵
    print("\n生成作物精灵...")
    crops_path = os.path.join(SPRITES_PATH, "crops")
    os.makedirs(crops_path, exist_ok=True)

    crop_types = ["variable_grass", "code_cane", "bug_berry", "feature_fruit"]
    qualities = ["Q1", "Q2", "Q3", "Q4"]

    for crop in crop_types:
        for quality in qualities:
            for stage in range(1, 4):
                sprite = create_crop_sprite(crop, quality, stage)
                filename = f"{crop}_{quality}_stage{stage}.png"
                sprite.save(os.path.join(crops_path, filename))
                print(f"  [OK] {filename}")

    # 3. 生成建筑精灵
    print("\n生成建筑精灵...")
    buildings_path = os.path.join(SPRITES_PATH, "buildings")
    os.makedirs(buildings_path, exist_ok=True)

    building_types = ["warehouse", "shop", "laboratory", "guild_hall", "arena",
                      "bank", "market", "workshop", "garden", "tower"]

    for building in building_types:
        sprite = create_building_sprite(building)
        filename = f"{building}.png"
        sprite.save(os.path.join(buildings_path, filename))
        print(f"  [OK] {filename}")

    # 4. 生成 UI 元素
    print("\n生成 UI 元素...")
    ui_path = os.path.join(SPRITES_PATH, "ui")
    os.makedirs(ui_path, exist_ok=True)

    # 按钮
    for state in ["normal", "pressed"]:
        sprite = create_ui_button(state)
        filename = f"button_{state}.png"
        sprite.save(os.path.join(ui_path, filename))
        print(f"  [OK] {filename}")

    # 面板
    panel = create_ui_panel()
    panel.save(os.path.join(ui_path, "panel.png"))
    print("  [OK] panel.png")

    # 大面板
    panel_large = create_ui_panel((256, 192))
    panel_large.save(os.path.join(ui_path, "panel_large.png"))
    print("  [OK] panel_large.png")

    # 图标
    icon_types = ["energy", "coin", "diamond", "heart", "star", "settings",
                  "menu", "close", "check", "arrow_up", "arrow_down",
                  "arrow_left", "arrow_right"]

    for icon in icon_types:
        sprite = create_icon(icon)
        filename = f"{icon}_icon.png"
        sprite.save(os.path.join(ui_path, filename))
        print(f"  [OK] {filename}")

    # 5. 生成物品精灵
    print("\n生成物品精灵...")
    items_path = os.path.join(SPRITES_PATH, "items")
    os.makedirs(items_path, exist_ok=True)

    item_types = ["seed", "fertilizer", "water", "tool"]
    for item in item_types:
        sprite = create_item_sprite(item)
        filename = f"{item}.png"
        sprite.save(os.path.join(items_path, filename))
        print(f"  [OK] {filename}")

    # 6. 生成特效精灵
    print("\n生成特效精灵...")
    effects_path = os.path.join(SPRITES_PATH, "effects")
    os.makedirs(effects_path, exist_ok=True)

    effect_types = ["sparkle", "levelup", "heal"]
    for effect in effect_types:
        sprite = create_effect_sprite(effect)
        filename = f"{effect}.png"
        sprite.save(os.path.join(effects_path, filename))
        print(f"  [OK] {filename}")

    # 统计
    print("\n" + "=" * 50)
    print("精灵资源生成完成！")
    print(f"  - 玩家精灵: {len(directions) * 3} 张")
    print(f"  - 作物精灵: {len(crop_types) * len(qualities) * 3} 张")
    print(f"  - 建筑精灵: {len(building_types)} 张")
    print(f"  - UI 元素: {2 + 2 + len(icon_types)} 张")
    print(f"  - 物品精灵: {len(item_types)} 张")
    print(f"  - 特效精灵: {len(effect_types)} 张")

    total = (len(directions) * 3 +
             len(crop_types) * len(qualities) * 3 +
             len(building_types) +
             2 + 2 + len(icon_types) +
             len(item_types) +
             len(effect_types))
    print(f"  总计: {total} 张")


if __name__ == "__main__":
    main()
