## quest_data.gd
## 任务数据定义 - 包含所有任务的静态数据
## 作为全局类使用 (class_name)
class_name QuestData
extends RefCounted

# 引用任务类型枚举
const QuestType = preload("res://scripts/quest/quest_manager.gd").QuestType

# ==================== 日常任务定义 ====================

static var DAILY_QUESTS: Array = [
	{
		"id": "daily_harvest_3",
		"name": "勤劳农夫",
		"description": "收获 3 次作物",
		"type": QuestType.DAILY,
		"condition": "harvest_crop",
		"target": 3,
		"rewards": {"gold": 100, "exp": 50}
	},
	{
		"id": "daily_harvest_5",
		"name": "丰收季节",
		"description": "收获 5 次作物",
		"type": QuestType.DAILY,
		"condition": "harvest_crop",
		"target": 5,
		"rewards": {"gold": 200, "exp": 100}
	},
	{
		"id": "daily_energy_100",
		"name": "能量收集者",
		"description": "获得 100 点能量",
		"type": QuestType.DAILY,
		"condition": "earn_energy",
		"target": 100,
		"rewards": {"gold": 150, "exp": 75}
	},
	{
		"id": "daily_energy_300",
		"name": "能量大师",
		"description": "获得 300 点能量",
		"type": QuestType.DAILY,
		"condition": "earn_energy",
		"target": 300,
		"rewards": {"gold": 300, "exp": 150, "diamonds": 5}
	},
	{
		"id": "daily_coding_30",
		"name": "代码时光",
		"description": "编码 30 分钟",
		"type": QuestType.DAILY,
		"condition": "coding_time",
		"target": 30,
		"rewards": {"gold": 200, "exp": 100}
	},
	{
		"id": "daily_coding_60",
		"name": "专注编程",
		"description": "编码 60 分钟",
		"type": QuestType.DAILY,
		"condition": "coding_time",
		"target": 60,
		"rewards": {"gold": 400, "exp": 200, "diamonds": 10}
	},
	{
		"id": "daily_flow_1",
		"name": "心流初体验",
		"description": "进入 1 次心流状态",
		"type": QuestType.DAILY,
		"condition": "achieve_flow",
		"target": 1,
		"rewards": {"gold": 500, "exp": 250, "diamonds": 15}
	},
	{
		"id": "daily_plant_3",
		"name": "播种希望",
		"description": "种植 3 株作物",
		"type": QuestType.DAILY,
		"condition": "plant_crop",
		"target": 3,
		"rewards": {"gold": 80, "exp": 40}
	},
	{
		"id": "daily_water_5",
		"name": "浇水达人",
		"description": "浇水 5 次",
		"type": QuestType.DAILY,
		"condition": "water_crop",
		"target": 5,
		"rewards": {"gold": 100, "exp": 50}
	},
	{
		"id": "daily_login",
		"name": "每日签到",
		"description": "完成每日签到",
		"type": QuestType.DAILY,
		"condition": "daily_login",
		"target": 1,
		"rewards": {"gold": 50, "exp": 25}
	}
]

# ==================== 周常任务定义 ====================

static var WEEKLY_QUESTS: Array = [
	{
		"id": "weekly_harvest_20",
		"name": "周末大丰收",
		"description": "本周收获 20 次作物",
		"type": QuestType.WEEKLY,
		"condition": "harvest_crop",
		"target": 20,
		"rewards": {"gold": 1000, "exp": 500, "diamonds": 20}
	},
	{
		"id": "weekly_energy_1000",
		"name": "能量周挑战",
		"description": "本周获得 1000 点能量",
		"type": QuestType.WEEKLY,
		"condition": "earn_energy",
		"target": 1000,
		"rewards": {"gold": 1500, "exp": 750, "diamonds": 30}
	},
	{
		"id": "weekly_coding_300",
		"name": "编程马拉松",
		"description": "本周编码 300 分钟",
		"type": QuestType.WEEKLY,
		"condition": "coding_time",
		"target": 300,
		"rewards": {"gold": 2000, "exp": 1000, "diamonds": 50}
	},
	{
		"id": "weekly_flow_5",
		"name": "心流大师",
		"description": "本周进入 5 次心流状态",
		"type": QuestType.WEEKLY,
		"condition": "achieve_flow",
		"target": 5,
		"rewards": {"gold": 2500, "exp": 1250, "diamonds": 80}
	},
	{
		"id": "weekly_build_1",
		"name": "建设家园",
		"description": "本周建造 1 座建筑",
		"type": QuestType.WEEKLY,
		"condition": "build_building",
		"target": 1,
		"rewards": {"gold": 800, "exp": 400, "diamonds": 15}
	},
	{
		"id": "weekly_login_7",
		"name": "全勤奖励",
		"description": "本周登录 7 天",
		"type": QuestType.WEEKLY,
		"condition": "daily_login",
		"target": 7,
		"rewards": {"gold": 1000, "exp": 500, "diamonds": 30}
	}
]

# ==================== 成就任务定义 ====================

static var ACHIEVEMENT_QUESTS: Array = [
	# 能量成就
	{
		"id": "ach_energy_1000",
		"name": "能量新手",
		"description": "累计获得 1,000 点能量",
		"type": QuestType.ACHIEVEMENT,
		"condition": "earn_energy",
		"target": 1000,
		"rewards": {"diamonds": 10, "title": "能量新手"}
	},
	{
		"id": "ach_energy_10000",
		"name": "能量达人",
		"description": "累计获得 10,000 点能量",
		"type": QuestType.ACHIEVEMENT,
		"condition": "earn_energy",
		"target": 10000,
		"rewards": {"diamonds": 50, "title": "能量达人"}
	},
	{
		"id": "ach_energy_100000",
		"name": "能量大师",
		"description": "累计获得 100,000 点能量",
		"type": QuestType.ACHIEVEMENT,
		"condition": "earn_energy",
		"target": 100000,
		"rewards": {"diamonds": 200, "title": "能量大师"}
	},
	# 心流成就
	{
		"id": "ach_flow_10",
		"name": "心流入门",
		"description": "累计进入 10 次心流状态",
		"type": QuestType.ACHIEVEMENT,
		"condition": "achieve_flow",
		"target": 10,
		"rewards": {"diamonds": 30, "title": "心流入门"}
	},
	{
		"id": "ach_flow_50",
		"name": "心流专家",
		"description": "累计进入 50 次心流状态",
		"type": QuestType.ACHIEVEMENT,
		"condition": "achieve_flow",
		"target": 50,
		"rewards": {"diamonds": 100, "title": "心流专家"}
	},
	{
		"id": "ach_flow_200",
		"name": "心流宗师",
		"description": "累计进入 200 次心流状态",
		"type": QuestType.ACHIEVEMENT,
		"condition": "achieve_flow",
		"target": 200,
		"rewards": {"diamonds": 500, "title": "心流宗师"}
	},
	# 编码时长成就
	{
		"id": "ach_coding_600",
		"name": "代码学徒",
		"description": "累计编码 10 小时",
		"type": QuestType.ACHIEVEMENT,
		"condition": "coding_time",
		"target": 600,
		"rewards": {"diamonds": 20, "title": "代码学徒"}
	},
	{
		"id": "ach_coding_3000",
		"name": "代码工匠",
		"description": "累计编码 50 小时",
		"type": QuestType.ACHIEVEMENT,
		"condition": "coding_time",
		"target": 3000,
		"rewards": {"diamonds": 80, "title": "代码工匠"}
	},
	{
		"id": "ach_coding_12000",
		"name": "代码大师",
		"description": "累计编码 200 小时",
		"type": QuestType.ACHIEVEMENT,
		"condition": "coding_time",
		"target": 12000,
		"rewards": {"diamonds": 300, "title": "代码大师"}
	},
	# 农场成就
	{
		"id": "ach_harvest_100",
		"name": "农场新手",
		"description": "累计收获 100 次作物",
		"type": QuestType.ACHIEVEMENT,
		"condition": "harvest_crop",
		"target": 100,
		"rewards": {"diamonds": 25, "title": "农场新手"}
	},
	{
		"id": "ach_harvest_500",
		"name": "农场能手",
		"description": "累计收获 500 次作物",
		"type": QuestType.ACHIEVEMENT,
		"condition": "harvest_crop",
		"target": 500,
		"rewards": {"diamonds": 100, "title": "农场能手"}
	},
	{
		"id": "ach_harvest_2000",
		"name": "农场大亨",
		"description": "累计收获 2000 次作物",
		"type": QuestType.ACHIEVEMENT,
		"condition": "harvest_crop",
		"target": 2000,
		"rewards": {"diamonds": 400, "title": "农场大亨"}
	},
	# 建筑成就
	{
		"id": "ach_build_5",
		"name": "建筑新手",
		"description": "建造 5 座建筑",
		"type": QuestType.ACHIEVEMENT,
		"condition": "build_building",
		"target": 5,
		"rewards": {"diamonds": 30, "title": "建筑新手"}
	},
	{
		"id": "ach_build_20",
		"name": "建筑师",
		"description": "建造 20 座建筑",
		"type": QuestType.ACHIEVEMENT,
		"condition": "build_building",
		"target": 20,
		"rewards": {"diamonds": 120, "title": "建筑师"}
	},
	# 连续登录成就
	{
		"id": "ach_login_7",
		"name": "坚持一周",
		"description": "连续登录 7 天",
		"type": QuestType.ACHIEVEMENT,
		"condition": "consecutive_login",
		"target": 7,
		"rewards": {"diamonds": 20, "title": "坚持一周"}
	},
	{
		"id": "ach_login_30",
		"name": "月度坚持",
		"description": "连续登录 30 天",
		"type": QuestType.ACHIEVEMENT,
		"condition": "consecutive_login",
		"target": 30,
		"rewards": {"diamonds": 100, "title": "月度坚持"}
	},
	{
		"id": "ach_login_100",
		"name": "百日坚守",
		"description": "连续登录 100 天",
		"type": QuestType.ACHIEVEMENT,
		"condition": "consecutive_login",
		"target": 100,
		"rewards": {"diamonds": 500, "title": "百日坚守"}
	}
]

# ==================== 活动任务定义 ====================

static var EVENT_QUESTS: Array = [
	{
		"id": "event_spring_harvest",
		"name": "春日丰收",
		"description": "在春季活动期间收获 50 次作物",
		"type": QuestType.EVENT,
		"condition": "harvest_crop",
		"target": 50,
		"rewards": {"gold": 5000, "diamonds": 100, "items": [{"id": "spring_seed_pack", "quantity": 1}]},
		"event_id": "spring_festival",
		"start_time": 0,
		"end_time": 0
	},
	{
		"id": "event_coding_marathon",
		"name": "编程马拉松",
		"description": "活动期间编码 500 分钟",
		"type": QuestType.EVENT,
		"condition": "coding_time",
		"target": 500,
		"rewards": {"gold": 8000, "diamonds": 150, "items": [{"id": "marathon_badge", "quantity": 1}]},
		"event_id": "coding_marathon",
		"start_time": 0,
		"end_time": 0
	}
]

# ==================== 主线任务定义 ====================

static var STORY_QUESTS: Array = [
	{
		"id": "story_tutorial_1",
		"name": "初来乍到",
		"description": "完成新手教程",
		"type": QuestType.STORY,
		"condition": "complete_tutorial",
		"target": 1,
		"rewards": {"gold": 500, "exp": 100, "items": [{"id": "starter_seeds", "quantity": 5}]},
		"prerequisite": null
	},
	{
		"id": "story_first_harvest",
		"name": "第一次收获",
		"description": "收获你的第一株作物",
		"type": QuestType.STORY,
		"condition": "harvest_crop",
		"target": 1,
		"rewards": {"gold": 200, "exp": 50},
		"prerequisite": "story_tutorial_1"
	},
	{
		"id": "story_first_building",
		"name": "建设家园",
		"description": "建造你的第一座建筑",
		"type": QuestType.STORY,
		"condition": "build_building",
		"target": 1,
		"rewards": {"gold": 500, "exp": 150, "diamonds": 10},
		"prerequisite": "story_first_harvest"
	},
	{
		"id": "story_first_flow",
		"name": "心流初体验",
		"description": "第一次进入心流状态",
		"type": QuestType.STORY,
		"condition": "achieve_flow",
		"target": 1,
		"rewards": {"gold": 1000, "exp": 300, "diamonds": 30},
		"prerequisite": "story_first_building"
	},
	{
		"id": "story_energy_master",
		"name": "能量觉醒",
		"description": "累计获得 5000 点能量",
		"type": QuestType.STORY,
		"condition": "earn_energy",
		"target": 5000,
		"rewards": {"gold": 2000, "exp": 500, "diamonds": 50},
		"prerequisite": "story_first_flow"
	}
]


# ==================== 静态方法 ====================

## 获取所有任务
static func get_all_quests() -> Dictionary:
	var result: Dictionary = {}

	for quest in DAILY_QUESTS:
		result[quest.id] = quest

	for quest in WEEKLY_QUESTS:
		result[quest.id] = quest

	for quest in ACHIEVEMENT_QUESTS:
		result[quest.id] = quest

	for quest in EVENT_QUESTS:
		result[quest.id] = quest

	for quest in STORY_QUESTS:
		result[quest.id] = quest

	return result


## 根据类型获取任务列表
static func get_quests_by_type(quest_type: int) -> Array:
	match quest_type:
		QuestType.DAILY:
			return DAILY_QUESTS.duplicate()
		QuestType.WEEKLY:
			return WEEKLY_QUESTS.duplicate()
		QuestType.ACHIEVEMENT:
			return ACHIEVEMENT_QUESTS.duplicate()
		QuestType.EVENT:
			return EVENT_QUESTS.duplicate()
		QuestType.STORY:
			return STORY_QUESTS.duplicate()
		_:
			return []


## 根据 ID 获取任务
static func get_quest_by_id(quest_id: String) -> Dictionary:
	var all_quests := get_all_quests()
	return all_quests.get(quest_id, {})


## 获取任务奖励描述文本
static func get_reward_text(rewards: Dictionary) -> String:
	var parts: Array = []

	if rewards.has("gold") and rewards["gold"] > 0:
		parts.append("%d 金币" % rewards["gold"])

	if rewards.has("exp") and rewards["exp"] > 0:
		parts.append("%d 经验" % rewards["exp"])

	if rewards.has("diamonds") and rewards["diamonds"] > 0:
		parts.append("%d 钻石" % rewards["diamonds"])

	if rewards.has("energy") and rewards["energy"] > 0:
		parts.append("%d 能量" % rewards["energy"])

	if rewards.has("title"):
		parts.append("称号: %s" % rewards["title"])

	if rewards.has("items"):
		for item in rewards["items"]:
			parts.append("%s x%d" % [item.get("id", "物品"), item.get("quantity", 1)])

	return ", ".join(parts)


## 获取任务类型名称
static func get_type_name(quest_type: int) -> String:
	match quest_type:
		QuestType.DAILY:
			return "日常"
		QuestType.WEEKLY:
			return "周常"
		QuestType.ACHIEVEMENT:
			return "成就"
		QuestType.EVENT:
			return "活动"
		QuestType.STORY:
			return "主线"
		_:
			return "未知"


## 获取任务类型颜色
static func get_type_color(quest_type: int) -> Color:
	match quest_type:
		QuestType.DAILY:
			return Color(0.3, 0.7, 0.3)  # 绿色
		QuestType.WEEKLY:
			return Color(0.3, 0.5, 0.9)  # 蓝色
		QuestType.ACHIEVEMENT:
			return Color(0.9, 0.7, 0.2)  # 金色
		QuestType.EVENT:
			return Color(0.9, 0.3, 0.5)  # 粉红色
		QuestType.STORY:
			return Color(0.7, 0.4, 0.9)  # 紫色
		_:
			return Color.WHITE
