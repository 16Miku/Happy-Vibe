## leaderboard_manager.gd
## 排行榜系统管理器
## 处理排行榜相关的 HTTP API 调用
extends Node

# ==================== 信号定义 ====================

## 排行榜类型列表更新
signal leaderboard_types_updated(types: Array)

## 排行榜数据更新
signal leaderboard_updated(lb_type: String, period: String, entries: Array, total: int)

## 玩家排名更新
signal player_rank_updated(lb_type: String, rank_info: Dictionary)

## 玩家周围排名更新
signal around_player_updated(lb_type: String, entries: Array, player_rank: int)

## 排行榜奖励更新
signal rewards_updated(lb_type: String, rewards: Array)

## 操作失败
signal operation_failed(error: String)

# ==================== 常量 ====================

const API_BASE := "http://127.0.0.1:8765/api/leaderboards"

# 排行榜类型
enum LeaderboardType {
	LEVEL,
	CODING_TIME,
	HARVEST,
	WEALTH,
	FLOW_TIME,
	BUILDING,
	GUILD
}

# 排行榜周期
enum LeaderboardPeriod {
	DAILY,
	WEEKLY,
	MONTHLY,
	ALL_TIME
}

const TYPE_NAMES := {
	LeaderboardType.LEVEL: "level",
	LeaderboardType.CODING_TIME: "coding_time",
	LeaderboardType.HARVEST: "harvest",
	LeaderboardType.WEALTH: "wealth",
	LeaderboardType.FLOW_TIME: "flow_time",
	LeaderboardType.BUILDING: "building",
	LeaderboardType.GUILD: "guild",
}

const PERIOD_NAMES := {
	LeaderboardPeriod.DAILY: "daily",
	LeaderboardPeriod.WEEKLY: "weekly",
	LeaderboardPeriod.MONTHLY: "monthly",
	LeaderboardPeriod.ALL_TIME: "all_time",
}

# ==================== 变量 ====================

var _http_request: HTTPRequest
var _current_request_type: String = ""
var _current_lb_type: String = ""
var _current_period: String = ""
var _player_id: String = ""

# 缓存
var _leaderboard_types: Array = []
var _leaderboard_cache: Dictionary = {}  # {(type, period): entries}
var _player_ranks: Dictionary = {}  # {type: rank_info}

# ==================== 生命周期 ====================

func _ready() -> void:
	_http_request = HTTPRequest.new()
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


func set_player_id(player_id: String) -> void:
	"""设置当前玩家 ID"""
	_player_id = player_id


# ==================== 排行榜查询 ====================

func get_leaderboard_types() -> void:
	"""获取所有排行榜类型"""
	_current_request_type = "types"
	var url := "%s/types" % API_BASE
	_http_request.request(url)


func get_leaderboard(lb_type: String, period: String = "weekly", page: int = 1, page_size: int = 50) -> void:
	"""获取排行榜数据

	Args:
		lb_type: 排行榜类型
		period: 周期 (daily, weekly, monthly, all_time)
		page: 页码
		page_size: 每页数量
	"""
	_current_request_type = "leaderboard"
	_current_lb_type = lb_type
	_current_period = period
	var url := "%s/%s?period=%s&page=%d&page_size=%d" % [API_BASE, lb_type, period, page, page_size]
	_http_request.request(url)


func get_player_rank(lb_type: String, period: String = "weekly") -> void:
	"""获取玩家在排行榜中的排名

	Args:
		lb_type: 排行榜类型
		period: 周期
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "player_rank"
	_current_lb_type = lb_type
	_current_period = period
	var url := "%s/%s/player/%s?period=%s" % [API_BASE, lb_type, _player_id, period]
	_http_request.request(url)


func get_leaderboard_around_player(lb_type: String, period: String = "weekly", range_size: int = 5) -> void:
	"""获取玩家周围的排行榜数据

	Args:
		lb_type: 排行榜类型
		period: 周期
		range_size: 上下各显示多少名
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "around_player"
	_current_lb_type = lb_type
	_current_period = period
	var url := "%s/%s/around/%s?period=%s&range_size=%d" % [API_BASE, lb_type, _player_id, period, range_size]
	_http_request.request(url)


func get_leaderboard_rewards(lb_type: String) -> void:
	"""获取排行榜奖励配置

	Args:
		lb_type: 排行榜类型
	"""
	_current_request_type = "rewards"
	_current_lb_type = lb_type
	var url := "%s/%s/rewards" % [API_BASE, lb_type]
	_http_request.request(url)


# ==================== 便捷方法 ====================

func get_level_leaderboard(period: String = "weekly") -> void:
	"""获取等级榜"""
	get_leaderboard("level", period)


func get_coding_time_leaderboard(period: String = "weekly") -> void:
	"""获取编码时长榜"""
	get_leaderboard("coding_time", period)


func get_harvest_leaderboard(period: String = "weekly") -> void:
	"""获取丰收榜"""
	get_leaderboard("harvest", period)


func get_wealth_leaderboard(period: String = "weekly") -> void:
	"""获取财富榜"""
	get_leaderboard("wealth", period)


func get_flow_time_leaderboard(period: String = "weekly") -> void:
	"""获取心流时长榜"""
	get_leaderboard("flow_time", period)


# ==================== 响应处理 ====================

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	"""HTTP 请求完成回调"""
	if result != HTTPRequest.RESULT_SUCCESS:
		operation_failed.emit("Network error")
		return

	var json := JSON.new()
	var parse_result := json.parse(body.get_string_from_utf8())
	if parse_result != OK:
		operation_failed.emit("Invalid response")
		return

	var data: Dictionary = json.data

	if response_code != 200:
		var error_msg: String = data.get("detail", "Unknown error")
		operation_failed.emit(error_msg)
		return

	match _current_request_type:
		"types":
			_leaderboard_types = data.get("types", [])
			leaderboard_types_updated.emit(_leaderboard_types)

		"leaderboard":
			var entries: Array = data.get("entries", [])
			var total: int = data.get("total", 0)
			var cache_key := "%s_%s" % [_current_lb_type, _current_period]
			_leaderboard_cache[cache_key] = entries
			leaderboard_updated.emit(_current_lb_type, _current_period, entries, total)

		"player_rank":
			var rank_info: Dictionary = {
				"rank": data.get("rank", 0),
				"total": data.get("total", 0),
				"value": data.get("value", 0),
				"value_label": data.get("value_label", ""),
				"on_leaderboard": data.get("on_leaderboard", false),
				"percentile": data.get("percentile", 0.0),
			}
			_player_ranks[_current_lb_type] = rank_info
			player_rank_updated.emit(_current_lb_type, rank_info)

		"around_player":
			var entries: Array = data.get("entries", [])
			var player_rank: int = data.get("player_rank", 0)
			around_player_updated.emit(_current_lb_type, entries, player_rank)

		"rewards":
			var rewards: Array = data.get("rewards", [])
			rewards_updated.emit(_current_lb_type, rewards)


# ==================== 工具方法 ====================

func get_cached_leaderboard(lb_type: String, period: String) -> Array:
	"""获取缓存的排行榜数据"""
	var cache_key := "%s_%s" % [lb_type, period]
	return _leaderboard_cache.get(cache_key, [])


func get_cached_player_rank(lb_type: String) -> Dictionary:
	"""获取缓存的玩家排名"""
	return _player_ranks.get(lb_type, {})


func get_leaderboard_type_info(lb_type: String) -> Dictionary:
	"""获取排行榜类型信息"""
	for type_info in _leaderboard_types:
		if type_info.get("type", "") == lb_type:
			return type_info
	return {}


func format_rank(rank: int) -> String:
	"""格式化排名显示"""
	match rank:
		1:
			return "🥇 1"
		2:
			return "🥈 2"
		3:
			return "🥉 3"
		_:
			return str(rank)


func get_rank_color(rank: int) -> Color:
	"""获取排名对应的颜色"""
	match rank:
		1:
			return Color.GOLD
		2:
			return Color.SILVER
		3:
			return Color("#CD7F32")  # Bronze
		_:
			return Color.WHITE
