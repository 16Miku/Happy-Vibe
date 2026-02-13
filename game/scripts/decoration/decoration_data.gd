## decoration_data.gd
## 装饰数据定义 - 包含所有装饰物的静态数据
## 作为全局类使用 (class_name)
class_name DecorationData
extends RefCounted

# 引用装饰类型枚举
const DecorationType = preload("res://scripts/decoration/decoration_manager.gd").DecorationType

# ==================== 家具装饰 ====================

static var FURNITURE: Array = [
	{
		"id": "wooden_bench",
		"name": "木质长椅",
		"description": "一张舒适的木质长椅，适合休息",
		"type": DecorationType.FURNITURE,
		"size": Vector2i(2, 1),
		"price": 200,
		"beauty": 5,
		"unlock_level": 1
	},
	{
		"id": "stone_table",
		"name": "石桌",
		"description": "坚固的石桌，可以放置物品",
		"type": DecorationType.FURNITURE,
		"size": Vector2i(2, 2),
		"price": 350,
		"beauty": 8,
		"unlock_level": 3
	},
	{
		"id": "wooden_chair",
		"name": "木椅",
		"description": "简单的木椅",
		"type": DecorationType.FURNITURE,
		"size": Vector2i(1, 1),
		"price": 100,
		"beauty": 3,
		"unlock_level": 1
	},
	{
		"id": "hammock",
		"name": "吊床",
		"description": "悠闲的吊床，编码累了可以休息",
		"type": DecorationType.FURNITURE,
		"size": Vector2i(3, 1),
		"price": 500,
		"beauty": 15,
		"unlock_level": 8
	},
	{
		"id": "picnic_set",
		"name": "野餐套装",
		"description": "包含桌布和餐具的野餐套装",
		"type": DecorationType.FURNITURE,
		"size": Vector2i(2, 2),
		"price": 400,
		"beauty": 12,
		"unlock_level": 5
	}
]

# ==================== 植物装饰 ====================

static var PLANTS: Array = [
	{
		"id": "flower_pot",
		"name": "花盆",
		"description": "精美的陶瓷花盆，种着小花",
		"type": DecorationType.PLANT,
		"size": Vector2i(1, 1),
		"price": 80,
		"beauty": 4,
		"unlock_level": 1
	},
	{
		"id": "rose_bush",
		"name": "玫瑰丛",
		"description": "盛开的玫瑰花丛",
		"type": DecorationType.PLANT,
		"size": Vector2i(1, 1),
		"price": 150,
		"beauty": 8,
		"unlock_level": 4
	},
	{
		"id": "small_tree",
		"name": "小树",
		"description": "一棵可爱的小树",
		"type": DecorationType.PLANT,
		"size": Vector2i(2, 2),
		"price": 300,
		"beauty": 12,
		"unlock_level": 6
	},
	{
		"id": "bamboo_cluster",
		"name": "竹丛",
		"description": "清新的竹子，带来宁静感",
		"type": DecorationType.PLANT,
		"size": Vector2i(1, 2),
		"price": 250,
		"beauty": 10,
		"unlock_level": 5
	},
	{
		"id": "sunflower",
		"name": "向日葵",
		"description": "明亮的向日葵，充满活力",
		"type": DecorationType.PLANT,
		"size": Vector2i(1, 1),
		"price": 120,
		"beauty": 6,
		"unlock_level": 2
	},
	{
		"id": "bonsai",
		"name": "盆景",
		"description": "精心修剪的盆景树",
		"type": DecorationType.PLANT,
		"size": Vector2i(1, 1),
		"price": 400,
		"beauty": 15,
		"unlock_level": 10
	}
]

# ==================== 围栏装饰 ====================

static var FENCES: Array = [
	{
		"id": "wooden_fence",
		"name": "木栅栏",
		"description": "基础的木质栅栏",
		"type": DecorationType.FENCE,
		"size": Vector2i(1, 1),
		"price": 30,
		"beauty": 1,
		"unlock_level": 1
	},
	{
		"id": "stone_fence",
		"name": "石围栏",
		"description": "坚固的石头围栏",
		"type": DecorationType.FENCE,
		"size": Vector2i(1, 1),
		"price": 60,
		"beauty": 2,
		"unlock_level": 3
	},
	{
		"id": "iron_fence",
		"name": "铁艺围栏",
		"description": "精美的铁艺围栏",
		"type": DecorationType.FENCE,
		"size": Vector2i(1, 1),
		"price": 100,
		"beauty": 4,
		"unlock_level": 7
	},
	{
		"id": "hedge",
		"name": "树篱",
		"description": "修剪整齐的绿色树篱",
		"type": DecorationType.FENCE,
		"size": Vector2i(1, 1),
		"price": 80,
		"beauty": 3,
		"unlock_level": 5
	}
]

# ==================== 道路装饰 ====================

static var PATHS: Array = [
	{
		"id": "stone_path",
		"name": "石板路",
		"description": "平整的石板铺成的小路",
		"type": DecorationType.PATH,
		"size": Vector2i(1, 1),
		"price": 20,
		"beauty": 1,
		"unlock_level": 1
	},
	{
		"id": "brick_path",
		"name": "砖石路",
		"description": "红砖铺成的小路",
		"type": DecorationType.PATH,
		"size": Vector2i(1, 1),
		"price": 35,
		"beauty": 2,
		"unlock_level": 3
	},
	{
		"id": "wooden_path",
		"name": "木板路",
		"description": "木板铺成的乡村小路",
		"type": DecorationType.PATH,
		"size": Vector2i(1, 1),
		"price": 25,
		"beauty": 1,
		"unlock_level": 2
	},
	{
		"id": "cobblestone_path",
		"name": "鹅卵石路",
		"description": "圆润的鹅卵石铺成的小路",
		"type": DecorationType.PATH,
		"size": Vector2i(1, 1),
		"price": 40,
		"beauty": 3,
		"unlock_level": 5
	}
]

# ==================== 灯光装饰 ====================

static var LIGHTING: Array = [
	{
		"id": "small_lamp",
		"name": "小灯笼",
		"description": "温馨的小灯笼",
		"type": DecorationType.LIGHTING,
		"size": Vector2i(1, 1),
		"price": 100,
		"beauty": 5,
		"unlock_level": 1
	},
	{
		"id": "street_lamp",
		"name": "路灯",
		"description": "复古风格的路灯",
		"type": DecorationType.LIGHTING,
		"size": Vector2i(1, 1),
		"price": 200,
		"beauty": 8,
		"unlock_level": 4
	},
	{
		"id": "fairy_lights",
		"name": "彩灯串",
		"description": "浪漫的彩色灯串",
		"type": DecorationType.LIGHTING,
		"size": Vector2i(2, 1),
		"price": 150,
		"beauty": 10,
		"unlock_level": 6
	},
	{
		"id": "lantern_post",
		"name": "灯柱",
		"description": "高大的装饰灯柱",
		"type": DecorationType.LIGHTING,
		"size": Vector2i(1, 1),
		"price": 300,
		"beauty": 12,
		"unlock_level": 8
	}
]

# ==================== 雕像装饰 ====================

static var STATUES: Array = [
	{
		"id": "garden_gnome",
		"name": "花园小矮人",
		"description": "可爱的花园小矮人雕像",
		"type": DecorationType.STATUE,
		"size": Vector2i(1, 1),
		"price": 150,
		"beauty": 6,
		"unlock_level": 2
	},
	{
		"id": "stone_fountain",
		"name": "石头喷泉",
		"description": "优雅的石头喷泉",
		"type": DecorationType.STATUE,
		"size": Vector2i(2, 2),
		"price": 800,
		"beauty": 25,
		"unlock_level": 10
	},
	{
		"id": "bird_bath",
		"name": "鸟浴盆",
		"description": "吸引小鸟的浴盆",
		"type": DecorationType.STATUE,
		"size": Vector2i(1, 1),
		"price": 200,
		"beauty": 8,
		"unlock_level": 4
	},
	{
		"id": "code_monument",
		"name": "代码纪念碑",
		"description": "纪念编程成就的特殊雕像",
		"type": DecorationType.STATUE,
		"size": Vector2i(2, 2),
		"price": 1500,
		"beauty": 40,
		"unlock_level": 15
	},
	{
		"id": "flow_crystal",
		"name": "心流水晶",
		"description": "象征心流状态的神秘水晶",
		"type": DecorationType.STATUE,
		"size": Vector2i(1, 1),
		"price": 2000,
		"beauty": 50,
		"unlock_level": 20
	}
]

# ==================== 季节限定装饰 ====================

static var SEASONAL: Array = [
	{
		"id": "spring_cherry",
		"name": "樱花树",
		"description": "春季限定 - 盛开的樱花树",
		"type": DecorationType.SEASONAL,
		"size": Vector2i(2, 2),
		"price": 500,
		"beauty": 20,
		"unlock_level": 1,
		"season": "spring"
	},
	{
		"id": "summer_umbrella",
		"name": "遮阳伞",
		"description": "夏季限定 - 清凉的遮阳伞",
		"type": DecorationType.SEASONAL,
		"size": Vector2i(2, 2),
		"price": 400,
		"beauty": 15,
		"unlock_level": 1,
		"season": "summer"
	},
	{
		"id": "autumn_pumpkin",
		"name": "南瓜装饰",
		"description": "秋季限定 - 丰收的南瓜",
		"type": DecorationType.SEASONAL,
		"size": Vector2i(1, 1),
		"price": 200,
		"beauty": 10,
		"unlock_level": 1,
		"season": "autumn"
	},
	{
		"id": "winter_snowman",
		"name": "雪人",
		"description": "冬季限定 - 可爱的雪人",
		"type": DecorationType.SEASONAL,
		"size": Vector2i(1, 1),
		"price": 300,
		"beauty": 12,
		"unlock_level": 1,
		"season": "winter"
	},
	{
		"id": "christmas_tree",
		"name": "圣诞树",
		"description": "冬季限定 - 装饰华丽的圣诞树",
		"type": DecorationType.SEASONAL,
		"size": Vector2i(2, 2),
		"price": 600,
		"beauty": 30,
		"unlock_level": 1,
		"season": "winter"
	}
]


# ==================== 静态方法 ====================

## 获取所有装饰
static func get_all_decorations() -> Dictionary:
	var result: Dictionary = {}

	for deco in FURNITURE:
		result[deco.id] = deco

	for deco in PLANTS:
		result[deco.id] = deco

	for deco in FENCES:
		result[deco.id] = deco

	for deco in PATHS:
		result[deco.id] = deco

	for deco in LIGHTING:
		result[deco.id] = deco

	for deco in STATUES:
		result[deco.id] = deco

	for deco in SEASONAL:
		result[deco.id] = deco

	return result


## 根据类型获取装饰列表
static func get_decorations_by_type(deco_type: int) -> Array:
	match deco_type:
		DecorationType.FURNITURE:
			return FURNITURE.duplicate()
		DecorationType.PLANT:
			return PLANTS.duplicate()
		DecorationType.FENCE:
			return FENCES.duplicate()
		DecorationType.PATH:
			return PATHS.duplicate()
		DecorationType.LIGHTING:
			return LIGHTING.duplicate()
		DecorationType.STATUE:
			return STATUES.duplicate()
		DecorationType.SEASONAL:
			return SEASONAL.duplicate()
		_:
			return []


## 根据 ID 获取装饰
static func get_decoration(decoration_id: String) -> Dictionary:
	var all_decorations := get_all_decorations()
	return all_decorations.get(decoration_id, {})


## 获取装饰类型名称
static func get_type_name(deco_type: int) -> String:
	match deco_type:
		DecorationType.FURNITURE:
			return "家具"
		DecorationType.PLANT:
			return "植物"
		DecorationType.FENCE:
			return "围栏"
		DecorationType.PATH:
			return "道路"
		DecorationType.LIGHTING:
			return "灯光"
		DecorationType.STATUE:
			return "雕像"
		DecorationType.SEASONAL:
			return "季节限定"
		_:
			return "未知"


## 获取装饰类型颜色
static func get_type_color(deco_type: int) -> Color:
	match deco_type:
		DecorationType.FURNITURE:
			return Color(0.6, 0.4, 0.2)  # 棕色
		DecorationType.PLANT:
			return Color(0.3, 0.7, 0.3)  # 绿色
		DecorationType.FENCE:
			return Color(0.5, 0.5, 0.5)  # 灰色
		DecorationType.PATH:
			return Color(0.7, 0.6, 0.5)  # 米色
		DecorationType.LIGHTING:
			return Color(0.9, 0.8, 0.3)  # 黄色
		DecorationType.STATUE:
			return Color(0.6, 0.6, 0.8)  # 淡紫色
		DecorationType.SEASONAL:
			return Color(0.9, 0.4, 0.6)  # 粉色
		_:
			return Color.WHITE


## 根据等级获取可解锁的装饰
static func get_decorations_by_level(level: int) -> Array:
	var result: Array = []
	var all_decorations := get_all_decorations()

	for deco_id in all_decorations:
		var deco: Dictionary = all_decorations[deco_id]
		if deco.get("unlock_level", 1) <= level:
			result.append(deco)

	return result


## 根据季节获取装饰
static func get_seasonal_decorations(season: String) -> Array:
	var result: Array = []

	for deco in SEASONAL:
		if deco.get("season", "") == season:
			result.append(deco)

	return result


## 计算装饰总价值
static func calculate_total_value(decoration_ids: Array) -> int:
	var total: int = 0

	for deco_id in decoration_ids:
		var deco: Dictionary = get_decoration(deco_id)
		total += deco.get("price", 0)

	return total
