extends Node
## Vibe 客户端
## 与 VibeHub 本地服务通信

signal connection_status_changed(connected: bool)
signal energy_received(amount: int, breakdown: Dictionary)
signal flow_state_changed(is_flow: bool)

const DEFAULT_HOST := "127.0.0.1"
const DEFAULT_PORT := 8765

var http_request: HTTPRequest
var is_connected: bool = false
var poll_timer: Timer


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
	var url := "http://%s:%d/api/health" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url)


func _poll_activity() -> void:
	"""轮询活动数据"""
	if not is_connected:
		_check_connection()
		return

	# TODO: 实现活动数据轮询


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
	else:
		_set_connected(false)


func _set_connected(connected: bool) -> void:
	"""设置连接状态"""
	if is_connected != connected:
		is_connected = connected
		connection_status_changed.emit(connected)


func _handle_response(data: Dictionary) -> void:
	"""处理响应数据"""
	# 处理健康检查响应
	if data.has("status") and data["status"] == "ok":
		return

	# 处理能量数据
	if data.has("energy"):
		var energy: int = data["energy"]
		var breakdown: Dictionary = data.get("breakdown", {})
		energy_received.emit(energy, breakdown)
		GameManager.add_energy(energy)

	# 处理心流状态
	if data.has("flow_state"):
		var is_flow: bool = data["flow_state"]
		flow_state_changed.emit(is_flow)
		if is_flow:
			EventBus.flow_state_entered.emit()


func start_activity(source: String) -> void:
	"""开始活动追踪"""
	if not is_connected:
		return

	var url := "http://%s:%d/api/activity/start" % [DEFAULT_HOST, DEFAULT_PORT]
	var body := JSON.stringify({"source": source})
	var headers := ["Content-Type: application/json"]
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func end_activity() -> void:
	"""结束活动追踪"""
	if not is_connected:
		return

	var url := "http://%s:%d/api/activity/end" % [DEFAULT_HOST, DEFAULT_PORT]
	http_request.request(url, [], HTTPClient.METHOD_POST)
