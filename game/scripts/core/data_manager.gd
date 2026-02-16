## data_manager.gd
## 数据管理器 - 缓存和管理玩家数据，负责与 API 同步
## 作为 AutoLoad 单例运行
extends Node

# ==================== 数据模型 ====================

## 玩家数据
var player_data: PlayerData = null

## 成就数据
var achievements_data: Dictionary = {}  # achievement_id -> AchievementDefinition
var achievement_progress: Dictionary = {}  # achievement_id -> AchievementProgress

## 公会数据
var my_guild: GuildData = null
var guild_list: Array[GuildData] = []

## 排行榜数据
var leaderboards: Dictionary = {}  # lb_type -> LeaderboardData
var my_ranks: Dictionary = {}  # lb_type -> rank

## PVP 数据
var pvp_info: PVPPlayerInfo = null
var pvp_leaderboard: Array[PVPEntry] = []
var pvp_history: Array[PVPMatchRecord] = []

## 赛季数据
var current_season: SeasonData = null

## 商城数据
var shop_items: Dictionary = {}  # shop_type -> Array[ShopItem]

# ==================== 信号定义 ====================

## 数据同步开始
signal data_sync_started(type: String)

## 数据同步完成
signal data_sync_completed(type: String, success: bool)

## 玩家数据更新
signal player_data_updated()

## 成就数据更新
signal achievements_updated()

## 公会数据更新
signal guild_data_updated()

## 排行榜数据更新
signal leaderboard_updated(lb_type: String)

## PVP 数据更新
signal pvp_data_updated()

# ==================== 同步状态 ====================

var _is_syncing: bool = false
var _last_sync_time: float = 0.0
var _auto_sync_enabled: bool = true
var _auto_sync_interval: float = 60.0  # 自动同步间隔（秒）
var _sync_timer: Timer = null

# ==================== 生命周期 ====================

func _ready() -> void:
	_setup_sync_timer()
	_initialize_data()
	print("[DataManager] 数据管理器已初始化")


func _setup_sync_timer() -> void:
	"""设置自动同步定时器"""
	_sync_timer = Timer.new()
	_sync_timer.wait_time = _auto_sync_interval
	_sync_timer.autostart = true
	_sync_timer.timeout.connect(_on_auto_sync)
	add_child(_sync_timer)


func _on_auto_sync() -> void:
	"""自动同步触发"""
	if _auto_sync_enabled and not _is_syncing:
		sync_all()


func _initialize_data() -> void:
	"""初始化默认数据"""
	player_data = PlayerData.new()


# ==================== 玩家数据 ====================

## 获取玩家数据
func get_player() -> PlayerData:
	return player_data


## 更新玩家数据
func update_player(data: Dictionary) -> void:
	if player_data:
		player_data.from_dict(data)
	player_data_updated.emit()


## 从 API 同步玩家数据
func sync_player(callback: Callable = Callable()) -> void:
	if not ApiManager:
		if callback.is_valid():
			callback.call(false, {})
		return

	data_sync_started.emit("player")

	ApiManager.get_player(func(success: bool, data: Dictionary):
		if success and data:
			update_player(data)
			_last_sync_time = Time.get_unix_time_from_system()

		data_sync_completed.emit("player", success)

		if callback.is_valid():
			callback.call(success, data)
	)


# ==================== 成就数据 ====================

## 获取所有成就定义
func get_achievements() -> Dictionary:
	return achievements_data


## 获取成就进度
func get_achievement_progress() -> Dictionary:
	return achievement_progress


## 从 API 同步成就数据
func sync_achievements(callback: Callable = Callable()) -> void:
	if not ApiManager:
		if callback.is_valid():
			callback.call(false, {})
		return

	data_sync_started.emit("achievements")

	# 并行请求成就定义和进度
	var pending := 2
	var all_success := true

	ApiManager.get_achievements(func(success: bool, data: Dictionary):
		if success:
			if data.has("achievements"):
				for achievement_dict in data["achievements"]:
					var achievement := AchievementDefinition.new()
					achievement.from_dict(achievement_dict)
					achievements_data[achievement.id] = achievement
		else:
			all_success = false

		pending -= 1
		if pending == 0:
			achievements_updated.emit()
			data_sync_completed.emit("achievements", all_success)
			if callback.is_valid():
				callback.call(all_success, {})
	)

	ApiManager.get_achievement_progress(func(success: bool, data: Dictionary):
		if success:
			if data.has("progress"):
				for progress_dict in data["progress"]:
					var progress := AchievementProgress.new()
					progress.from_dict(progress_dict)
					achievement_progress[progress.achievement_id] = progress
		else:
			all_success = false

		pending -= 1
		if pending == 0:
			achievements_updated.emit()
			data_sync_completed.emit("achievements", all_success)
			if callback.is_valid():
				callback.call(all_success, {})
	)


## 领取成就奖励
func claim_achievement(achievement_id: String, callback: Callable = Callable()) -> void:
	if not ApiManager:
		return

	ApiManager.claim_achievement_reward(achievement_id, func(success: bool, data: Dictionary):
		if success:
			if achievement_progress.has(achievement_id):
				achievement_progress[achievement_id].claimed = true
			# 更新玩家数据（奖励）
			if data.has("rewards"):
				_apply_rewards(data["rewards"])
			achievements_updated.emit()

		if callback.is_valid():
			callback.call(success, data)
	)


# ==================== 公会数据 ====================

## 获取我的公会
func get_my_guild() -> GuildData:
	return my_guild


## 获取公会列表
func get_guild_list() -> Array[GuildData]:
	return guild_list


## 从 API 同步公会数据
func sync_guilds(callback: Callable = Callable()) -> void:
	if not ApiManager:
		if callback.is_valid():
			callback.call(false, {})
		return

	data_sync_started.emit("guilds")

	ApiManager.get_my_guild(func(success: bool, data: Dictionary):
		if success and not data.is_empty():
			var guild := GuildData.new()
			guild.from_dict(data)
			my_guild = guild

		guild_data_updated.emit()
		data_sync_completed.emit("guilds", success)

		if callback.is_valid():
			callback.call(success, data)
	)


## 获取公会列表
func fetch_guild_list(page: int = 1, callback: Callable = Callable()) -> void:
	if not ApiManager:
		return

	ApiManager.get_guilds(page, 20, func(success: bool, data: Dictionary):
		if success:
			guild_list.clear()
			if data.has("guilds"):
				for guild_dict in data["guilds"]:
					var guild := GuildData.new()
					guild.from_dict(guild_dict)
					guild_list.append(guild)

		if callback.is_valid():
			callback.call(success, data)
	)


## 加入公会
func join_guild(guild_id: String, callback: Callable = Callable()) -> void:
	if not ApiManager:
		return

	ApiManager.join_guild(guild_id, func(success: bool, data: Dictionary):
		if success:
			sync_guilds()  # 重新同步公会数据

		if callback.is_valid():
			callback.call(success, data)
	)


## 离开公会
func leave_guild(callback: Callable = Callable()) -> void:
	if not ApiManager:
		return

	ApiManager.leave_guild(func(success: bool, data: Dictionary):
		if success:
			my_guild = null
			guild_data_updated.emit()

		if callback.is_valid():
			callback.call(success, data)
	)


# ==================== 排行榜数据 ====================

## 获取排行榜数据
func get_leaderboard(lb_type: String) -> LeaderboardData:
	return leaderboards.get(lb_type)


## 获取我的排名
func get_my_rank(lb_type: String) -> int:
	return my_ranks.get(lb_type, -1)


## 从 API 同步排行榜
func sync_leaderboard(lb_type: String, page: int = 1, callback: Callable = Callable()) -> void:
	if not ApiManager:
		if callback.is_valid():
			callback.call(false, {})
		return

	data_sync_started.emit("leaderboard_" + lb_type)

	ApiManager.get_leaderboard(lb_type, page, 50, func(success: bool, data: Dictionary):
		if success:
			var leaderboard := LeaderboardData.new()
			leaderboard.from_dict(data)
			leaderboards[lb_type] = leaderboard

			# 获取我的排名
			ApiManager.get_player_rank(lb_type, func(rank_success: bool, rank_data: Dictionary):
				if rank_success and rank_data.has("rank"):
					my_ranks[lb_type] = rank_data["rank"]

				leaderboard_updated.emit(lb_type)
				data_sync_completed.emit("leaderboard_" + lb_type, success)

				if callback.is_valid():
					callback.call(success, data)
			)
		else:
			data_sync_completed.emit("leaderboard_" + lb_type, false)
			if callback.is_valid():
				callback.call(false, data)
	)


# ==================== PVP 数据 ====================

## 获取 PVP 信息
func get_pvp_info() -> PVPPlayerInfo:
	return pvp_info


## 获取 PVP 排行榜
func get_pvp_leaderboard() -> Array[PVPEntry]:
	return pvp_leaderboard


## 从 API 同步 PVP 数据
func sync_pvp(callback: Callable = Callable()) -> void:
	if not ApiManager:
		if callback.is_valid():
			callback.call(false, {})
		return

	data_sync_started.emit("pvp")

	var pending := 2
	var all_success := true

	# 获取 PVP 信息
	ApiManager.get_pvp_info(func(success: bool, data: Dictionary):
		if success:
			pvp_info = PVPPlayerInfo.new()
			pvp_info.from_dict(data)
		else:
			all_success = false

		pending -= 1
		if pending == 0:
			pvp_data_updated.emit()
			data_sync_completed.emit("pvp", all_success)
			if callback.is_valid():
				callback.call(all_success, {})
	)

	# 获取 PVP 排行榜
	ApiManager.get_pvp_leaderboard(1, 50, func(success: bool, data: Dictionary):
		if success:
			pvp_leaderboard.clear()
			if data.has("entries"):
				for entry_dict in data["entries"]:
					var entry := PVPEntry.new()
					entry.from_dict(entry_dict)
					pvp_leaderboard.append(entry)
		else:
			all_success = false

		pending -= 1
		if pending == 0:
			pvp_data_updated.emit()
			data_sync_completed.emit("pvp", all_success)
			if callback.is_valid():
				callback.call(all_success, {})
	)


## 发起 PVP 匹配
func start_pvp_matchmaking(callback: Callable = Callable()) -> void:
	if not ApiManager:
		return

	ApiManager.start_pvp_matchmaking(func(success: bool, data: Dictionary):
		if callback.is_valid():
			callback.call(success, data)
	)


# ==================== 赛季数据 ====================

## 获取当前赛季
func get_current_season() -> SeasonData:
	return current_season


## 从 API 同步赛季数据
func sync_season(callback: Callable = Callable()) -> void:
	if not ApiManager:
		if callback.is_valid():
			callback.call(false, {})
		return

	ApiManager.get_current_season(func(success: bool, data: Dictionary):
		if success:
			current_season = SeasonData.new()
			current_season.from_dict(data)

		if callback.is_valid():
			callback.call(success, data)
	)


# ==================== 全量同步 ====================

## 同步所有数据
func sync_all(callback: Callable = Callable()) -> void:
	if _is_syncing:
		if callback.is_valid():
			callback.call(false, {"message": "正在同步中"})
		return

	_is_syncing = true
	var pending := 0
	var all_success := true

	var sync_complete := func():
		_is_syncing = false
		if callback.is_valid():
			callback.call(all_success, {})

	# 同步玩家数据
	pending += 1
	sync_player(func(success: bool, data: Dictionary):
		if not success:
			all_success = false
		pending -= 1
		if pending == 0:
			sync_complete.call()
	)

	# 同步成就数据
	pending += 1
	sync_achievements(func(success: bool, data: Dictionary):
		if not success:
			all_success = false
		pending -= 1
		if pending == 0:
			sync_complete.call()
	)

	# 同步公会数据
	pending += 1
	sync_guilds(func(success: bool, data: Dictionary):
		if not success:
			all_success = false
		pending -= 1
		if pending == 0:
			sync_complete.call()
	)

	# 同步赛季数据
	pending += 1
	sync_season(func(success: bool, data: Dictionary):
		if not success:
			all_success = false
		pending -= 1
		if pending == 0:
			sync_complete.call()
	)


# ==================== 工具方法 ====================

## 应用奖励到玩家数据
func _apply_rewards(rewards: Dictionary) -> void:
	if rewards.has("gold"):
		GameManager.add_gold(rewards["gold"])
	if rewards.has("exp"):
		GameManager.add_exp(rewards["exp"])
	if rewards.has("energy"):
		GameManager.add_energy(rewards["energy"])
	if rewards.has("diamonds"):
		GameManager.add_diamonds(rewards["diamonds"])


## 设置自动同步状态
func set_auto_sync(enabled: bool) -> void:
	_auto_sync_enabled = enabled
	if _sync_timer:
		_sync_timer.autostart = enabled
		if enabled:
			_sync_timer.start()
		else:
			_sync_timer.stop()


## 获取同步状态
func is_syncing() -> bool:
	return _is_syncing


## 获取距离上次同步的时间
func get_time_since_last_sync() -> float:
	return Time.get_unix_time_from_system() - _last_sync_time


# ==================== 数据类 ====================

## 玩家数据类
class PlayerData:
	var id: String
	var username: String
	var level: int
	var exp: int
	var max_exp: int
	var gold: int
	var diamonds: int
	var energy: int
	var max_energy: int
	var vip_level: int
	var vip_exp: int
	var guild_id: String = ""
	var avatar_id: String = "default_coder"
	var title_id: String = ""
	var consecutive_days: int = 0
	var total_playtime: int = 0

	func from_dict(data: Dictionary) -> void:
		id = data.get("id", "")
		username = data.get("username", "Player")
		level = data.get("level", 1)
		exp = data.get("exp", 0)
		max_exp = data.get("max_exp", 100)
		gold = data.get("gold", 0)
		diamonds = data.get("diamonds", 0)
		energy = data.get("energy", 100)
		max_energy = data.get("max_energy", 1000)
		vip_level = data.get("vip_level", 0)
		vip_exp = data.get("vip_exp", 0)
		guild_id = data.get("guild_id", "")
		avatar_id = data.get("avatar_id", "default_coder")
		title_id = data.get("title_id", "")
		consecutive_days = data.get("consecutive_days", 0)
		total_playtime = data.get("total_playtime", 0)

	func to_dict() -> Dictionary:
		return {
			"id": id,
			"username": username,
			"level": level,
			"exp": exp,
			"max_exp": max_exp,
			"gold": gold,
			"diamonds": diamonds,
			"energy": energy,
			"max_energy": max_energy,
			"vip_level": vip_level,
			"vip_exp": vip_exp,
			"guild_id": guild_id,
			"avatar_id": avatar_id,
			"title_id": title_id,
			"consecutive_days": consecutive_days,
			"total_playtime": total_playtime
		}


## 成就定义类
class AchievementDefinition:
	var id: String
	var name: String
	var description: String
	var category: String
	var tier: String
	var target_value: int
	var rewards: Dictionary
	var hidden: bool = false
	var icon: String = ""

	func from_dict(data: Dictionary) -> void:
		id = data.get("id", "")
		name = data.get("name", "")
		description = data.get("description", "")
		category = data.get("category", "general")
		tier = data.get("tier", "bronze")
		target_value = data.get("target_value", 1)
		rewards = data.get("rewards", {})
		hidden = data.get("hidden", false)
		icon = data.get("icon", "")


## 成就进度类
class AchievementProgress:
	var achievement_id: String
	var current_value: int
	var completed: bool = false
	var claimed: bool = false
	var completed_at: int = 0

	func from_dict(data: Dictionary) -> void:
		achievement_id = data.get("achievement_id", "")
		current_value = data.get("current_value", 0)
		completed = data.get("completed", false)
		claimed = data.get("claimed", false)
		completed_at = data.get("completed_at", 0)


## 公会数据类
class GuildData:
	var id: String
	var name: String
	var description: String
	var level: int
	var exp: int
	var leader_id: String
	var leader_name: String
	var member_count: int
	var max_members: int
	var rank: int = 0

	func from_dict(data: Dictionary) -> void:
		id = data.get("id", "")
		name = data.get("name", "")
		description = data.get("description", "")
		level = data.get("level", 1)
		exp = data.get("exp", 0)
		leader_id = data.get("leader_id", "")
		leader_name = data.get("leader_name", "")
		member_count = data.get("member_count", 0)
		max_members = data.get("max_members", 50)
		rank = data.get("rank", 0)


## 排行榜数据类
class LeaderboardData:
	var lb_type: String
	var title: String
	var season_id: String = ""
	var entries: Array[Dictionary] = []
	var my_rank: int = -1

	func from_dict(data: Dictionary) -> void:
		lb_type = data.get("lb_type", "")
		title = data.get("title", "")
		season_id = data.get("season_id", "")
		if data.has("entries"):
			entries = data["entries"]
		my_rank = data.get("my_rank", -1)


## PVP 玩家信息类
class PVPPlayerInfo:
	var rating: int = 1200
	var max_rating: int = 1200
	var wins: int = 0
	var losses: int = 0
	var draws: int = 0
	var current_streak: int = 0
	var max_streak: int = 0
	var rank: int = -1
	var tier: String = "bronze"

	func from_dict(data: Dictionary) -> void:
		rating = data.get("rating", 1200)
		max_rating = data.get("max_rating", 1200)
		wins = data.get("wins", 0)
		losses = data.get("losses", 0)
		draws = data.get("draws", 0)
		current_streak = data.get("current_streak", 0)
		max_streak = data.get("max_streak", 0)
		rank = data.get("rank", -1)
		tier = data.get("tier", "bronze")


## PVP 排行榜条目类
class PVPEntry:
	var rank: int
	var player_id: String
	var username: String
	var rating: int
	var tier: String
	var wins: int
	var losses: int

	func from_dict(data: Dictionary) -> void:
		rank = data.get("rank", 0)
		player_id = data.get("player_id", "")
		username = data.get("username", "")
		rating = data.get("rating", 1200)
		tier = data.get("tier", "bronze")
		wins = data.get("wins", 0)
		losses = data.get("losses", 0)


## PVP 战斗记录类
class PVPMatchRecord:
	var match_id: String
	var opponent_id: String
	var opponent_name: String
	var result: String  # win/loss/draw
	var rating_change: int
	var timestamp: int

	func from_dict(data: Dictionary) -> void:
		match_id = data.get("match_id", "")
		opponent_id = data.get("opponent_id", "")
		opponent_name = data.get("opponent_name", "")
		result = data.get("result", "draw")
		rating_change = data.get("rating_change", 0)
		timestamp = data.get("timestamp", 0)


## 赛季数据类
class SeasonData:
	var id: String
	var name: String
	var number: int
	var start_time: int
	var end_time: int
	var current: bool = false
	var effects: Dictionary = {}

	func from_dict(data: Dictionary) -> void:
		id = data.get("id", "")
		name = data.get("name", "")
		number = data.get("number", 1)
		start_time = data.get("start_time", 0)
		end_time = data.get("end_time", 0)
		current = data.get("current", false)
		effects = data.get("effects", {})
