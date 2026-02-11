extends Node
## Vibe 客户端
## 与 VibeHub 本地服务通信

signal connection_status_changed(connected: bool)
signal player_data_received(player: Dictionary)
signal energy_received(amount: int, breakdown: Dictionary)
signal flow_state_changed(is_flow: bool)
signal farm_data_received(farm: Dictionary)
signal achievements_received(achievements: Array)

const DEFAULT_HOST := "127.0.0.1"
const DEFAULT_PORT := 8765

var http_request: HTTPRequest
var is_connected: bool = false
var poll_timer: Timer
var current_session_id: String = ""
var current_request_type: String = ""  # 标识当前请求类型


func _ready() -> void:
	_setup_http_request()
	_setup_poll_timer()
	_check_connection()


func _setup_http_request() -> void:
	"""设置 HTTP 请求节点"""
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)


func _setup_poll_timer() -> void:
	"""设置轮询定时器"""
	poll_timer = Timer.new()
	poll_timer.wait_time = 5.0  # 每 5 秒检查一次
	poll_timer.autostart = true
	poll_timer.timeout.connect(_poll_activity)
	add_child(poll_timer)


func _check_connection() -> void:
	"""检查与 VibeHub 的连接"""
	current_request_type = "health"
	var url := "http://%s:%d/api/health" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url)


func _poll_activity() -> void:
	"""轮询活动数据"""
	if not is_connected:
		_check_connection()
		return

	# 获取当前活动状态（使用默认玩家ID）
	current_request_type = "activity_current"
	var url := "http://%s:%d/api/activity/current?player_id=default" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url)


func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	"""HTTP 请求完成回调"""
	if result != HTTPRequest.RESULT_SUCCESS:
		_set_connected(false)
		return

	if response_code == 200:
		_set_connected(true)
		var json := JSON.new()
		var parse_result := json.parse(body.get_string_from_utf8())
		if parse_result == OK:
			_handle_response(json.data)
	elif response_code == 404 and current_request_type == "activity_current":
		# 没有活动是正常的，不改变连接状态
		pass
	else:
		_set_connected(false)


func _set_connected(connected: bool) -> void:
	"""设置连接状态"""
	if is_connected != connected:
		is_connected = connected
		connection_status_changed.emit(connected)
		if connected:
			print("[VibeClient] 已连接到 VibeHub")
		else:
			print("[VibeClient] 与 VibeHub 断开连接")


func _handle_response(data: Dictionary) -> void:
	"""处理响应数据"""
	# 处理健康检查响应
	if current_request_type == "health" and data.has("status") and data["status"] == "ok":
		return

	# 处理当前活动响应
	if current_request_type == "activity_current":
		if data.has("has_active_session") and data["has_active_session"]:
			if data.has("session_id"):
				current_session_id = data["session_id"]
			# 触发心流状态更新信号（如果有心流数据）
			if data.has("flow_status"):
				var flow_status: Dictionary = data["flow_status"]
				if flow_status.has("is_active"):
					flow_state_changed.emit(flow_status["is_active"])
		return

	# 处理心流状态
	if current_request_type == "activity_flow_status":
		if data.has("is_active"):
			var is_flow: bool = data["is_active"]
			flow_state_changed.emit(is_flow)
			if is_flow:
				EventBus.flow_state_entered.emit()
		return

	# 处理玩家数据
	if current_request_type == "player":
		player_data_received.emit(data)
		return

	# 处理能量数据
	if data.has("energy"):
		var energy: int = data["energy"]
		var breakdown: Dictionary = data.get("breakdown", {})
		energy_received.emit(energy, breakdown)

	# 处理农场数据
	if current_request_type == "farm":
		farm_data_received.emit(data)
		return

	# 处理成就数据
	if current_request_type == "achievements":
		if data.has("achievements"):
			achievements_received.emit(data["achievements"])
		return


## ========== 玩家 API ==========

func get_player() -> void:
	"""获取玩家数据"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "player"
	var url := "http://%s:%d/api/player" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url)


func update_player(data: Dictionary) -> void:
	"""更新玩家数据"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "player_update"
	var url := "http://%s:%d/api/player" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify(data)
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func add_energy(amount: int) -> void:
	"""添加能量"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "player_energy"
	var url := "http://%s:80/api/player/energy" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify({"amount": amount})
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func add_experience(amount: int) -> void:
	"""添加经验值"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "player_exp"
	var url := "http://%s:%d/api/player/exp" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify({"amount": amount})
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


## ========== 活动 API ==========

func start_activity(source: String) -> void:
	"""开始活动追踪"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "activity_start"
	var url := "http://%s:%d/api/activity/start" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify({"source": source})
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func update_activity(duration: float = 0.0, quality: Dictionary = {}) -> void:
	"""更新活动进度"""
	if not is_connected or current_session_id.is_empty():
		push_warning("[VibeClient] 未连接或无活动会话")
		return

	current_request_type = "activity_update"
	var url := "http://%s:%d/api/activity/update" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify({
		"session_id": current_session_id,
		"last_interaction_gap": duration
	})
	if quality.size() > 0:
		# 转换质量指标格式
		var request_quality := {
			"success_rate": quality.get("success_rate", 0.5),
			"iteration_count": quality.get("iteration_count", 1),
			"lines_changed": quality.get("lines_changed", 0),
			"files_affected": quality.get("files_affected", 0),
			"languages": quality.get("languages", []),
			"tool_usage": {
				"read": quality.get("tool_usage_read", 0),
				"write": quality.get("tool_usage_write", 0),
				"bash": quality.get("tool_usage_bash", 0),
				"search": quality.get("tool_usage_search", 0),
			}
		}
		body = JSON.stringify({
			"session_id": current_session_id,
			"last_interaction_gap": duration,
			"quality": request_quality
		})

	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func end_activity() -> void:
	"""结束活动追踪"""
	if not is_connected or current_session_id.is_empty():
		push_warning("[VibeClient] 未连接或无活动会话")
		return

	current_request_type = "activity_end"
	var url := "http://%s:%d/api/activity/end" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url, [], HTTPClient.METHOD_POST)


## ========== 农场 API ==========

func get_farm() -> void:
	"""获取农场数据"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "farm"
	var url := "http://%s:%d/api/farm" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url)


func update_farm(farm_data: Dictionary) -> void:
	"""更新农场数据"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "farm_update"
	var url :=: "http://%s:%d/api/farm" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify(farm_data)
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


## ========== 成就 API ==========

func get_achievements() -> void:
	"""获取成就列表"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "achievements"
	var url := "http://%s:%d/api/achievements" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url)


func unlock_achievement(achievement_id: String) -> void:
	"""解锁成就"""
	if not is_connected:
		push_warning("[VibeClient] 未连接到 VibeHub")
		return

	current_request_type = "achievement_unlock"
	var url := "http://%s:%d/api/achievements/%s/unlock" % [DEFAULT_HOST, DEFAULT_PORT, achievement_id]
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, "")


## ========== 实用函数 ==========

func _build_url(endpoint: String) -> String:
	"""构建完整的 API URL"""
	return "http://%s:%d/api/%s" % [DEFAULT_HOST, DEFAULT_PORT, endpoint]


func _get_current_time() -> String:
	"""获取当前时间字符串"""
	var datetime_dict := Time.get_datetime_dict_from_system()
	return "%02d:%02d:%02d" % [datetime_dict.hour, datetime_dict.minute, datetime_dict.second]
