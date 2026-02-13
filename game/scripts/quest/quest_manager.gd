## quest_manager.gd
## 任务管理器 - 管理日常任务、成就任务、活动任务
## 作为 AutoLoad 单例运行
extends Node

# 任务类型枚举
enum QuestType {
	DAILY,      # 日常任务 - 每日重置
	WEEKLY,     # 周常任务 - 每周重置
	ACHIEVEMENT,# 成就任务 - 永久
	EVENT,      # 活动任务 - 限时
	STORY       # 主线任务 - 一次性
}

# 任务状态枚举
enum QuestStatus {
	LOCKED,     # 未解锁
	AVAILABLE,  # 可接取
	IN_PROGRESS,# 进行中
	COMPLETED,  # 已完成（待领取）
	CLAIMED     # 已领取
}

# 信号定义
signal quest_accepted(quest_id: String)
signal quest_progress_updated(quest_id: String, current: int, target: int)
signal quest_completed(quest_id: String)
signal quest_reward_claimed(quest_id: String, rewards: Dictionary)
signal daily_quests_refreshed()
signal weekly_quests_refreshed()

# 任务数据
var all_quests: Dictionary =         # 所有任务定义
var player_quests: Dictionary = {}     # 玩家任务进度
var daily_refresh_time: int = 0        # 日常任务刷新时间
var weekly_refresh_time: int = 0       # 周常任务刷新时间

# 常量
const DAILY_QUEST_COUNT: int = 5       # 每日任务数量
const WEEKLY_QUEST_COUNT: int = 3      # 每周任务数量


func _ready() -> void:
	_load_quest_definitions()
	_load_player_quests()
	_check_quest_refresh()
	_connect_signals()


## 加载任务定义
func _load_quest_definitions() -> void:
	all_quests = QuestData.get_all_quests()


## 加载玩家任务进度
func _load_player_quests() -> void:
	if SaveManager:
		var save_data: Dictionary = SaveManager.load_game()
		if save_data.has("quests"):
			player_quests = save_data["quests"]
			daily_refresh_time = save_data.get("daily_refresh_time", 0)
			weekly_refresh_time = save_data.get("weekly_refresh_time", 0)
		else:
			_initialize_player_quests()
	else:
		_initialize_player_quests()


## 初始化玩家任务数据
func _initialize_player_quests() -> void:
	player_quests = {
		"active": {},      # 当前活跃任务 {quest_id: {progress, status, accepted_time}}
		"completed": [],   # 已完成任务ID列表
		"daily_ids": [],   # 今日日常任务ID
		"weekly_ids": []   # 本周周常任务ID
	}
	_refresh_daily_quests()
	_refresh_weekly_quests()


## 检查任务刷新
func _check_quest_refresh() -> void:
	var current_time: int = int(Time.get_unix_time_from_system())

	# 检查日常任务刷新（每天凌晨4点）
	if _should_refresh_daily(current_time):
		_refresh_daily_quests()

	# 检查周常任务刷新（每周一凌晨4点）
	if _should_refresh_weekly(current_time):
		_refresh_weekly_quests()


## 判断是否需要刷新日常任务
func _should_refresh_daily(current_time: int) -> bool:
	if daily_refresh_time == 0:
		return true

	var last_refresh := Time.get_datetime_dict_from_unix_time(daily_refresh_time)
	var now := Time.get_datetime_dict_from_unix_time(current_time)

	# 如果日期不同，需要刷新
	if last_refresh.day != now.day or last_refresh.month != now.month or last_refresh.year != now.year:
		return true

	return false


## 判断是否需要刷新周常任务
func _should_refresh_weekly(current_time: int) -> bool:
	if weekly_refresh_time == 0:
		return true

	var days_since_refresh: int = (current_time - weekly_refresh_time) / 86400
	if days_since_refresh >= 7:
		return true

	return false


## 刷新日常任务
func _refresh_daily_quests() -> void:
	# 清除旧的日常任务进度
	for quest_id in player_quests.get("daily_ids", []):
		if player_quests["active"].has(quest_id):
			player_quests["active"].erase(quest_id)

	# 随机选择新的日常任务
	var daily_pool: Array = QuestData.get_quests_by_type(QuestType.DAILY)
	daily_pool.shuffle()

	var new_daily_ids: Array = []
	for i in range(mini(DAILY_QUEST_COUNT, daily_pool.size())):
		new_daily_ids.append(daily_pool[i].id)
		# 初始化任务进度
		player_quests["active"][daily_pool[i].id] = {
			"progress": 0,
			"status": QuestStatus.AVAILABLE,
			"accepted_time": 0
		}

	player_quests["daily_ids"] = new_daily_ids
	daily_refresh_time = int(Time.get_unix_time_from_system())

	daily_quests_refreshed.emit()
	_save_player_quests()
	print("[QuestManager] 日常任务已刷新: ", new_daily_ids.size(), " 个")


## 刷新周常任务
func _refresh_weekly_quests() -> void:
	# 清除旧的周常任务进度
	for quest_id in player_quests.get("weekly_ids", []):
		if player_quests["active"].has(quest_id):
			player_quests["active"].erase(quest_id)

	# 随机选择新的周常任务
	var weekly_pool: Array = QuestData.get_quests_by_type(QuestType.WEEKLY)
	weekly_pool.shuffle()

	var new_weekly_ids: Array = []
	for i in range(mini(WEEKLY_QUEST_COUNT, weekly_pool.size())):
		new_weekly_ids.append(weekly_pool[i].id)
		player_quests["active"][weekly_pool[i].id] = {
			"progress": 0,
			"status": QuestStatus.AVAILABLE,
			"accepted_time": 0
		}

	player_quests["weekly_ids"] = new_weekly_ids
	weekly_refresh_time = int(Time.get_unix_time_from_system())

	weekly_quests_refreshed.emit()
	_save_player_quests()
	print("[QuestManager] 周常任务已刷新: ", new_weekly_ids.size(), " 个")


## 连接事件信号
func _connect_signals() -> void:
	# 连接各种游戏事件来更新任务进度
	if EventBus:
		EventBus.crop_harvested.connect(_on_crop_harvested)
		EventBus.vibe_energy_received.connect(_on_energy_received)
		EventBus.flow_state_achieved.connect(_on_flow_achieved)
		EventBus.coding_session_ended.connect(_on_coding_session_ended)
		EventBus.item_added.connect(_on_item_added)
		EventBus.building_completed.connect(_on_building_completed)
		EventBus.achievement_unlocked.connect(_on_achievement_unlocked)


## 保存玩家任务数据
func _save_player_quests() -> void:
	if SaveManager and GameManager:
		var player_data: Dictionary = GameManager.player_data.duplicate(true)
		player_data["quests"] = player_quests
		player_data["daily_refresh_time"] = daily_refresh_time
		player_data["weekly_refresh_time"] = weekly_refresh_time
		SaveManager.save_game(player_data)


# ==================== 公共 API ====================

## 获取所有可用任务
func get_available_quests() -> Array:
	var result: Array = []
	for quest_id in player_quests["active"].keys():
		var quest_progress: Dictionary = player_quests["active"][quest_id]
		if quest_progress["status"] == QuestStatus.AVAILABLE or quest_progress["status"] == QuestStatus.IN_PROGRESS:
			if all_quests.has(quest_id):
				var quest_info: Dictionary = all_quests[quest_id].duplicate()
				quest_info["progress"] = quest_progress["progress"]
				quest_info["status"] = quest_progress["status"]
				result.append(quest_info)
	return result


## 获取日常任务列表
func get_daily_quests() -> Array:
	var result: Array = []
	for quest_id in player_quests.get("daily_ids", []):
		if all_quests.has(quest_id):
			var quest_info: Dictionary = all_quests[quest_id].duplicate()
			if player_quests["active"].has(quest_id):
				quest_info["progress"] = player_quests["active"][quest_id]["progress"]
				quest_info["status"] = player_quests["active"][quest_id]["status"]
			result.append(quest_info)
	return result


## 获取周常任务列表
func get_weekly_quests() -> Array:
	var result: Array = []
	for quest_id in player_quests.get("weekly_ids", []):
		if all_quests.has(quest_id):
			var quest_info: Dictionary = all_quests[quest_id].duplicate()
			if player_quests["active"].has(quest_id):
				quest_info["progress"] = player_quests["active"][quest_id]["progress"]
				quest_info["status"] = player_quests["active"][quest_id]["status"]
			result.append(quest_info)
	return result


## 获取成就任务列表
func get_achievement_quests() -> Array:
	var result: Array = []
	var achievement_quests: Array = QuestData.get_quests_by_type(QuestType.ACHIEVEMENT)
	for quest in achievement_quests:
		var quest_info: Dictionary = quest.duplicate()
		if player_quests["active"].has(quest.id):
			quest_info["progress"] = player_quests["active"][quest.id]["progress"]
			quest_info["status"] = player_quests["active"][quest.id]["status"]
		elif quest.id in player_quests.get("completed", []):
			quest_info["progress"] = quest.target
			quest_info["status"] = QuestStatus.CLAIMED
		else:
			quest_info["progress"] = 0
			quest_info["status"] = QuestStatus.AVAILABLE
		result.append(quest_info)
	return result


## 获取任务详情
func get_quest(quest_id: String) -> Dictionary:
	if not all_quests.has(quest_id):
		return {}

	var quest_info: Dictionary = all_quests[quest_id].duplicate()
	if player_quests["active"].has(quest_id):
		quest_info["progress"] = player_quests["active"][quest_id]["progress"]
		quest_info["status"] = player_quests["active"][quest_id]["status"]
	elif quest_id in player_quests.get("completed", []):
		quest_info["progress"] = quest_info.get("target", 1)
		quest_info["status"] = QuestStatus.CLAIMED
	else:
		quest_info["progress"] = 0
		quest_info["status"] = QuestStatus.LOCKED

	return quest_info


## 接取任务
func accept_quest(quest_id: String) -> bool:
	if not all_quests.has(quest_id):
		push_warning("[QuestManager] 任务不存在: ", quest_id)
		return false

	if not player_quests["active"].has(quest_id):
		player_quests["active"][quest_id] = {
			"progress": 0,
			"status": QuestStatus.AVAILABLE,
			"accepted_time": 0
		}

	var quest_progress: Dictionary = player_quests["active"][quest_id]
	if quest_progress["status"] != QuestStatus.AVAILABLE:
		push_warning("[QuestManager] 任务状态不允许接取: ", quest_id)
		return false

	quest_progress["status"] = QuestStatus.IN_PROGRESS
	quest_progress["accepted_time"] = int(Time.get_unix_time_from_system())

	quest_accepted.emit(quest_id)
	_save_player_quests()

	if EventBus:
		EventBus.notify_success("已接取任务: " + all_quests[quest_id].get("name", quest_id))

	return true


## 更新任务进度
func update_quest_progress(quest_id: String, amount: int = 1) -> void:
	if not player_quests["active"].has(quest_id):
		return

	var quest_progress: Dictionary = player_quests["active"][quest_id]
	if quest_progress["status"] != QuestStatus.IN_PROGRESS and quest_progress["status"] != QuestStatus.AVAILABLE:
		return

	# 如果是 AVAILABLE 状态，自动变为 IN_PROGRESS
	if quest_progress["status"] == QuestStatus.AVAILABLE:
		quest_progress["status"] = QuestStatus.IN_PROGRESS
		quest_progress["accepted_time"] = int(Time.get_unix_time_from_system())

	var quest_def: Dictionary = all_quests.get(quest_id, {})
	var target: int = quest_def.get("target", 1)

	quest_progress["progress"] = mini(quest_progress["progress"] + amount, target)

	quest_progress_updated.emit(quest_id, quest_progress["progress"], target)

	# 检查是否完成
	if quest_progress["progress"] >= target:
		quest_progress["status"] = QuestStatus.COMPLETED
		quest_completed.emit(quest_id)
		if EventBus:
			EventBus.notify_success("任务完成: " + quest_def.get("name", quest_id))

	_save_player_quests()


## 领取任务奖励
func claim_quest_reward(quest_id: String) -> Dictionary:
	if not player_quests["active"].has(quest_id):
		push_warning("[QuestManager] 任务不存在: ", quest_id)
		return {}

	var quest_progress: Dictionary = player_quests["active"][quest_id]
	if quest_progress["status"] != QuestStatus.COMPLETED:
		push_warning("[QuestManager] 任务未完成: ", quest_id)
		return {}

	var quest_def: Dictionary = all_quests.get(quest_id, {})
	var rewards: Dictionary = quest_def.get("rewards", {})

	# 发放奖励
	_grant_rewards(rewards)

	# 更新状态
	quest_progress["status"] = QuestStatus.CLAIMED

	# 对于非日常/周常任务，添加到已完成列表
	var quest_type: int = quest_def.get("type", QuestType.DAILY)
	if quest_type != QuestType.DAILY and quest_type != QuestType.WEEKLY:
		if not player_quests["completed"].has(quest_id):
			player_quests["completed"].append(quest_id)
		player_quests["active"].erase(quest_id)

	quest_reward_claimed.emit(quest_id, rewards)
	_save_player_quests()

	if EventBus:
		EventBus.show_rewards(rewards)

	return rewards


## 发放奖励
func _grant_rewards(rewards: Dictionary) -> void:
	if not GameManager:
		return

	if rewards.has("energy"):
		GameManager.add_energy(rewards["energy"])

	if rewards.has("exp"):
		GameManager.add_exp(rewards["exp"])

	if rewards.has("gold"):
		GameManager.add_gold(rewards["gold"])

	if rewards.has("diamonds"):
		GameManager.add_diamonds(rewards["diamonds"])

	if rewards.has("items"):
		for item in rewards["items"]:
			if EventBus:
				EventBus.item_added.emit(item.get("id", ""), item.get("quantity", 1))


## 获取日常任务刷新剩余时间（秒）
func get_daily_refresh_remaining() -> int:
	var current_time: int = int(Time.get_unix_time_from_system())
	var now := Time.get_datetime_dict_from_unix_time(current_time)

	# 计算到明天凌晨4点的秒数
	var seconds_until_4am: int = (4 - now.hour) * 3600 - now.minute * 60 - now.second
	if seconds_until_4am <= 0:
		seconds_until_4am += 86400  # 加一天

	return seconds_until_4am


## 获取周常任务刷新剩余时间（秒）
func get_weekly_refresh_remaining() -> int:
	var current_time: int = int(Time.get_unix_time_from_system())
	var now := Time.get_datetime_dict_from_unix_time(current_time)

	# 计算到下周一凌晨4点的秒数
	var days_until_monday: int = (8 - now.weekday) % 7
	if days_until_monday == 0:
		days_until_monday = 7

	var seconds_until_4am: int = (4 - now.hour) * 3600 - now.minute * 60 - now.second
	if seconds_until_4am <= 0:
		seconds_until_4am += 86400
		days_until_monday -= 1

	return days_until_monday * 86400 + seconds_until_4am


# ==================== 事件处理 ====================

## 作物收获事件
func _on_crop_harvested(_plot_id: String, crop_data: Dictionary) -> void:
	_update_quests_by_condition("harvest_crop", 1)

	var crop_type: String = crop_data.get("type", "")
	if not crop_type.is_empty():
		_update_quests_by_condition("harvest_" + crop_type, 1)


## 能量获得事件
func _on_energy_received(energy: int, _exp: int, _is_flow: bool) -> void:
	_update_quests_by_condition("earn_energy", energy)


## 心流状态达成事件
func _on_flow_achieved() -> void:
	_update_quests_by_condition("achieve_flow", 1)


## 编码会话结束事件
func _on_coding_session_ended(duration_minutes: int, _energy_earned: int) -> void:
	_update_quests_by_condition("coding_time", duration_minutes)


## 物品获得事件
func _on_item_added(item_id: String, quantity: int) -> void:
	_update_quests_by_condition("collect_item", quantity)
	_update_quests_by_condition("collect_" + item_id, quantity)


## 建筑完成事件
func _on_building_completed(_building_id: int, building_type: String) -> void:
	_update_quests_by_condition("build_building", 1)
	_update_quests_by_condition("build_" + building_type, 1)


## 成就解锁事件
func _on_achievement_unlocked(_achievement_id: String) -> void:
	_update_quests_by_condition("unlock_achievement", 1)


## 根据条件更新任务进度
func _update_quests_by_condition(condition: String, amount: int) -> void:
	for quest_id in player_quests["active"].keys():
		var quest_progress: Dictionary = player_quests["active"][quest_id]
		if quest_progress["status"] == QuestStatus.IN_PROGRESS or quest_progress["status"] == QuestStatus.AVAILABLE:
			var quest_def: Dictionary = all_quests.get(quest_id, {})
			if quest_def.get("condition", "") == condition:
				update_quest_progress(quest_id, amount)
