## season_data.gd
## 赛季数据定义 - 包含季节效果、赛季通行证奖励等静态数据
## 作为全局类使用 (class_name)
class_name SeasonData
extends RefCounted

# 引用枚举
const Season = preload("res://scripts/season/season_manager.gd").Season
const SeasonPassTier = preload("res://scripts/season/season_manager.gd").SeasonPassTier

# ==================== 季节效果定义 ====================

static var SEASON_EFFECTS: Dictionary = {
	Season.SPRING: {
		"name": "春季",
		"description": "万物复苏，作物生长加速",
		"crop_growth_bonus": 1.2,    # 作物生长速度 +20%
		"energy_bonus": 1.0,
		"gold_bonus": 1.0,
		"special_effect": "花朵绽放，农场更美丽"
	},
	Season.SUMMER: {
		"name": "夏季",
		"description": "阳光充足，能量获取增加",
		"crop_growth_bonus": 1.0,
		"energy_bonus": 1.25,        # 能量获取 +25%
		"gold_bonus": 1.0,
		"special_effect": "心流状态更容易达成"
	},
	Season.AUTUMN: {
		"name": "秋季",
		"description": "丰收季节，金币收益提升",
		"crop_growth_bonus": 1.0,
		"energy_bonus": 1.0,
		"gold_bonus": 1.3,           # 金币收益 +30%
		"special_effect": "收获作物获得额外奖励"
	},
	Season.WINTER: {
		"name": "冬季",
		"description": "休养生息，经验获取增加",
		"crop_growth_bonus": 0.8,    # 作物生长速度 -20%
		"energy_bonus": 1.0,
		"gold_bonus": 1.0,
		"exp_bonus": 1.2,            # 经验获取 +20%
		"special_effect": "编码时间转化为更多经验"
	}
}

# ==================== 季节作物定义 ====================

static var SEASONAL_CROPS: Dictionary = {
	Season.SPRING: [
		"cherry_blossom",    # 樱花
		"tulip",             # 郁金香
		"spring_onion",      # 春葱
		"strawberry"         # 草莓
	],
	Season.SUMMER: [
		"sunflower",         # 向日葵
		"watermelon",        # 西瓜
		"corn",              # 玉米
		"tomato"             # 番茄
	],
	Season.AUTUMN: [
		"pumpkin",           # 南瓜
		"maple_leaf",        # 枫叶
		"apple",             # 苹果
		"grape"              # 葡萄
	],
	Season.WINTER: [
		"pine_tree",         # 松树
		"holly",             # 冬青
		"snowdrop",          # 雪花莲
		"winter_melon"       # 冬瓜
	]
}

# ==================== 赛季通行证奖励定义 ====================

static var SEASON_PASS_REWARDS: Array = [
	# 等级 1-10
	{"level": 1, "free": {"gold": 500}, "premium": {"diamonds": 50}},
	{"level": 2, "free": {"exp": 200}, "premium": {"gold": 1000}},
	{"level": 3, "free": {"gold": 800}, "premium": {"items": [{"id": "spring_seed_pack", "quantity": 1}]}},
	{"level": 4, "free": {"exp": 300}, "premium": {"diamonds": 80}},
	{"level": 5, "free": {"gold": 1000, "diamonds": 20}, "premium": {"decoration": "season_banner_1"}},
	{"level": 6, "free": {"exp": 400}, "premium": {"gold": 1500}},
	{"level": 7, "free": {"gold": 1200}, "premium": {"items": [{"id": "quality_fertilizer", "quantity": 5}]}},
	{"level": 8, "free": {"exp": 500}, "premium": {"diamonds": 100}},
	{"level": 9, "free": {"gold": 1500}, "premium": {"gold": 2000}},
	{"level": 10, "free": {"gold": 2000, "diamonds": 50}, "premium": {"decoration": "season_statue_1", "diamonds": 150}},

	# 等级 11-20
	{"level": 11, "free": {"exp": 600}, "premium": {"gold": 2500}},
	{"level": 12, "free": {"gold": 1800}, "premium": {"items": [{"id": "rare_seed_pack", "quantity": 1}]}},
	{"level": 13, "free": {"exp": 700}, "premium": {"diamonds": 120}},
	{"level": 14, "free": {"gold": 2000}, "premium": {"gold": 3000}},
	{"level": 15, "free": {"gold": 2500, "diamonds": 80}, "premium": {"decoration": "season_lamp_1", "diamonds": 200}},
	{"level": 16, "free": {"exp": 800}, "premium": {"gold": 3500}},
	{"level": 17, "free": {"gold": 2200}, "premium": {"items": [{"id": "super_fertilizer", "quantity": 3}]}},
	{"level": 18, "free": {"exp": 900}, "premium": {"diamonds": 150}},
	{"level": 19, "free": {"gold": 2500}, "premium": {"gold": 4000}},
	{"level": 20, "free": {"gold": 3000, "diamonds": 100}, "premium": {"decoration": "season_fountain", "diamonds": 250}},

	# 等级 21-30
	{"level": 21, "free": {"exp": 1000}, "premium": {"gold": 4500}},
	{"level": 22, "free": {"gold": 2800}, "premium": {"items": [{"id": "legendary_seed", "quantity": 1}]}},
	{"level": 23, "free": {"exp": 1100}, "premium": {"diamonds": 180}},
	{"level": 24, "free": {"gold": 3000}, "premium": {"gold": 5000}},
	{"level": 25, "free": {"gold": 3500, "diamonds": 120}, "premium": {"decoration": "season_tree", "diamonds": 300}},
	{"level": 26, "free": {"exp": 1200}, "premium": {"gold": 5500}},
	{"level": 27, "free": {"gold": 3200}, "premium": {"items": [{"id": "golden_tool", "quantity": 1}]}},
	{"level": 28, "free": {"exp": 1300}, "premium": {"diamonds": 200}},
	{"level": 29, "free": {"gold": 3500}, "premium": {"gold": 6000}},
	{"level": 30, "free": {"gold": 4000, "diamonds": 150}, "premium": {"decoration": "season_monument", "diamonds": 350}},

	# 等级 31-40
	{"level": 31, "free": {"exp": 1400}, "premium": {"gold": 6500}},
	{"level": 32, "free": {"gold": 3800}, "premium": {"items": [{"id": "epic_seed_pack", "quantity": 1}]}},
	{"level": 33, "free": {"exp": 1500}, "premium": {"diamonds": 220}},
	{"level": 34, "free": {"gold": 4000}, "premium": {"gold": 7000}},
	{"level": 35, "free": {"gold": 4500, "diamonds": 180}, "premium": {"decoration": "season_arch", "diamonds": 400}},
	{"level": 36, "free": {"exp": 1600}, "premium": {"gold": 7500}},
	{"level": 37, "free": {"gold": 4200}, "premium": {"items": [{"id": "diamond_tool", "quantity": 1}]}},
	{"level": 38, "free": {"exp": 1700}, "premium": {"diamonds": 250}},
	{"level": 39, "free": {"gold": 4500}, "premium": {"gold": 8000}},
	{"level": 40, "free": {"gold": 5000, "diamonds": 200}, "premium": {"decoration": "season_palace", "diamonds": 450}},

	# 等级 41-50
	{"level": 41, "free": {"exp": 1800}, "premium": {"gold": 8500}},
	{"level": 42, "free": {"gold": 4800}, "premium": {"items": [{"id": "mythic_seed", "quantity": 1}]}},
	{"level": 43, "free": {"exp": 1900}, "premium": {"diamonds": 280}},
	{"level": 44, "free": {"gold": 5000}, "premium": {"gold": 9000}},
	{"level": 45, "free": {"gold": 5500, "diamonds": 220}, "premium": {"decoration": "season_crystal", "diamonds": 500}},
	{"level": 46, "free": {"exp": 2000}, "premium": {"gold": 9500}},
	{"level": 47, "free": {"gold": 5200}, "premium": {"items": [{"id": "legendary_tool", "quantity": 1}]}},
	{"level": 48, "free": {"exp": 2100}, "premium": {"diamonds": 300}},
	{"level": 49, "free": {"gold": 5500}, "premium": {"gold": 10000}},
	{"level": 50, "free": {"gold": 10000, "diamonds": 500}, "premium": {"decoration": "season_throne", "diamonds": 1000, "title": "赛季王者"}}
]


# ==================== 静态方法 ====================

## 获取季节效果
static func get_season_effects(season: int) -> Dictionary:
	return SEASON_EFFECTS.get(season, {})


## 获取季节名称
static func get_season_name(season: int) -> String:
	var effects: Dictionary = SEASON_EFFECTS.get(season, {})
	return effects.get("name", "未知")


## 获取季节描述
static func get_season_description(season: int) -> String:
	var effects: Dictionary = SEASON_EFFECTS.get(season, {})
	return effects.get("description", "")


## 获取季节特殊效果描述
static func get_season_special_effect(season: int) -> String:
	var effects: Dictionary = SEASON_EFFECTS.get(season, {})
	return effects.get("special_effect", "")


## 获取季节作物列表
static func get_seasonal_crops(season: int) -> Array:
	return SEASONAL_CROPS.get(season, [])


## 获取赛季通行证奖励
static func get_season_pass_reward(level: int, tier: int) -> Dictionary:
	for reward_data in SEASON_PASS_REWARDS:
		if reward_data.get("level", 0) == level:
			if tier == SeasonPassTier.FREE:
				return reward_data.get("free", {})
			else:
				return reward_data.get("premium", {})
	return {}


## 获取所有赛季通行证奖励
static func get_all_season_pass_rewards() -> Array:
	return SEASON_PASS_REWARDS.duplicate()


## 获取奖励描述文本
static func get_reward_text(rewards: Dictionary) -> String:
	var parts: Array = []

	if rewards.has("gold") and rewards["gold"] > 0:
		parts.append("%d 金币" % rewards["gold"])

	if rewards.has("diamonds") and rewards["diamonds"] > 0:
		parts.append("%d 钻石" % rewards["diamonds"])

	if rewards.has("exp") and rewards["exp"] > 0:
		parts.append("%d 经验" % rewards["exp"])

	if rewards.has("energy") and rewards["energy"] > 0:
		parts.append("%d 能量" % rewards["energy"])

	if rewards.has("decoration"):
		parts.append("装饰: %s" % rewards["decoration"])

	if rewards.has("title"):
		parts.append("称号: %s" % rewards["title"])

	if rewards.has("items"):
		for item in rewards["items"]:
			parts.append("%s x%d" % [item.get("id", "物品"), item.get("quantity", 1)])

	return ", ".join(parts)


## 获取季节颜色
static func get_season_color(season: int) -> Color:
	match season:
		Season.SPRING:
			return Color(0.9, 0.6, 0.7)  # 粉色
		Season.SUMMER:
			return Color(0.3, 0.8, 0.3)  # 绿色
		Season.AUTUMN:
			return Color(0.9, 0.6, 0.2)  # 橙色
		Season.WINTER:
			return Color(0.6, 0.8, 0.95) # 淡蓝色
		_:
			return Color.WHITE


## 获取季节图标路径
static func get_season_icon_path(season: int) -> String:
	match season:
		Season.SPRING:
			return "res://assets/sprites/ui/season_spring.png"
		Season.SUMMER:
			return "res://assets/sprites/ui/season_summer.png"
		Season.AUTUMN:
			return "res://assets/sprites/ui/season_autumn.png"
		Season.WINTER:
			return "res://assets/sprites/ui/season_winter.png"
		_:
			return ""


## 计算赛季通行证总价值（免费）
static func calculate_free_total_value() -> Dictionary:
	var total := {"gold": 0, "diamonds": 0, "exp": 0}

	for reward_data in SEASON_PASS_REWARDS:
		var free_reward: Dictionary = reward_data.get("free", {})
		total["gold"] += free_reward.get("gold", 0)
		total["diamonds"] += free_reward.get("diamonds", 0)
		total["exp"] += free_reward.get("exp", 0)

	return total


## 计算赛季通行证总价值（高级）
static func calculate_premium_total_value() -> Dictionary:
	var total := {"gold": 0, "diamonds": 0, "decorations": 0, "items": 0}

	for reward_data in SEASON_PASS_REWARDS:
		var premium_reward: Dictionary = reward_data.get("premium", {})
		total["gold"] += premium_reward.get("gold", 0)
		total["diamonds"] += premium_reward.get("diamonds", 0)
		if premium_reward.has("decoration"):
			total["decorations"] += 1
		if premium_reward.has("items"):
			total["items"] += premium_reward["items"].size()

	return total
