## test_vibe_communication.gd
## 测试 VibeClient 与 VibeHub 的通信
extends Control

@onready var connection_status_label: Label = $VBoxContainer/ConnectionStatus
@onready var start_activity_btn: Button = $VBoxContainer/ButtonContainer/StartActivityBtn
@onready var update_activity_btn: Button = $VBoxContainer/ButtonContainer/UpdateActivityBtn
@onready var end_activity_btn: Button = $VBoxContainer/ButtonContainer/EndActivityBtn
@onready var log_label: Label = $VBoxContainer/LogContainer/LogLabel

var vibe_client: Node
var is_connected: bool = false
var current_session_id: String = ""

func _ready() -> void:
	_setup_vibe_client()
	_connect_signals()
	_add_log("等待 VibeHub 连接...")


func _setup_vibe_client() -> void:
	# 查找 VibeClient 单例
	vibe_client = get_node.get_node_or_null("/root/VibeClient")

	if not vibe_client:
		_add_log("错误: 未找到 VibeClient！")
		_set_buttons_enabled(false)
		return

	_add_log("VibeClient 已加载")


func _connect_signals() -> void:
	if not vibe_client:
		return

	# 连接 VibeClient 信号
	if vibe_client.has_signal("connection_status_changed"):
		vibe_client.connection_status_changed.connect(_on_connection_status_changed)
		_add_log("已连接 connection_status_changed 信号")

	if vibe_client.has_signal("player_data_received"):
		vibe_client.player_data_received.connect(_on_player_data_received)
		_add_log("已连接 player_data_received 信号")

	if vibe_client.has_signal("energy_received"):
		vibe_client.energy_received.connect(_on_energy_received)
		_add_log("已连接 energy_received 信号")

	if vibe_client.has_signal("flow_state_changed"):
		vibe_client.flow_state_changed.connect(_on_flow_state_changed)
		_add_log("已连接 flow_state_changed 信号")

	# 连接按钮信号
	start_activity_btn.pressed.connect(_on_start_activity)
	update_activity_btn.pressed.connect(_on_update_activity)
	end_activity_btn.pressed.connect(_on_end_activity)

	_set_buttons_enabled(false)


func _on_connection_status_changed(connected: bool) -> void:
	is_connected = connected

	if connected:
		connection_status_label.text = "连接状态: 已连接"
		connection_status_label.modulate = Color(0.2, 0.8, 0.2, 1.0)  # 绿色
		_add_log("✓ 已连接到 VibeHub")
		_set_buttons_enabled(true)

		# 自动获取玩家数据
		if vibe_client.has_method("get_player"):
			vibe_client.call("get_player")
			_add_log("→ 请求玩家数据...")
	else:
		connection_status_label.text = "连接状态: 未连接"
		connection_status_label.modulate = Color(0.8, 0.2, 0.2, 1.0)  # 红色
		_add_log("✗ 与 VibeHub 断开连接")
		_set_buttons_enabled(false)


func _on_player_data_received(player_data: Dictionary) -> void:
	_add_log("← 收到玩家数据:")
	_add_log("  用户名: " + str(player_data.get("username", "Unknown")))
	_add_log("  等级: " + str(player_data.get("level", 1)))
	_add_log("  能量: " + str(player_data.get("energy", 0)))
	_add_log("  金币: " + str(player_data.get("gold", 0)))


func _on_energy_received(energy: int, breakdown: Dictionary) -> void:
	_add_log("← 收到能量: " + str(energy))
	if breakdown.size() > 0:
		_add_log("  细分:")
		for key in breakdown.keys():
			_add_log("    " + str(key) + ": " + str(breakdown[key]))


func _on_flow_state_changed(is_flow: bool) -> void:
	if is_flow:
		_add_log("← 心流状态: 进入心流！")
		connection_status_label.text = "连接状态: 已连接 (心流中)"
	else:
		_add_log("← 心流状态: 退出心流")
		connection_status_label.text = "连接状态: 已连接"


func _on_start_activity() -> void:
	if not is_connected:
		_add_log("错误: 未连接到 VibeHub")
		return

	_add_log("→ 开始活动追踪")
	if vibe_client.has_method("start_activity"):
		vibe_client.call("start_activity", "test_source")
		_add_log("  已发送活动开始请求")
	else:
		_add_log("错误: start_activity 方法不存在")


func _on_update_activity() -> void:
	if not is_connected:
		_add_log("错误: 未连接到 VibeHub")
		return

	_add_log("→ 更新活动进度")
	if vibe_client.has_method("update_activity"):
		vibe_client.call("update_activity", 5.0, 100)  # 5分钟，100 tokens
		_add_log("  已发送更新请求")
	else:
		_add_log("错误: update_activity 方法不存在")


func _on_end_activity() -> void:
	if not is_connected:
		_add_log("错误: 未连接到 VibeHub")
		return

	_add_log("→ 结束活动追踪")
	if vibe_client.has_method("end_activity"):
		vibe_client.call("end_activity")
		_add_log("  已发送结束请求")
	else:
		_add_log("错误: end_activity 方法不存在")


func _set_buttons_enabled(enabled: bool) -> void:
	start_activity_btn.disabled = not enabled
	update_activity_btn.disabled = not enabled
	end_activity_btn.disabled = not enabled


func _add_log(message: String) -> void:
	var timestamp := _get_timestamp()
	var new_line := "[%s] %s" % [timestamp, message]

	if log_label.text == "等待连接...":
		log_label.text = new_line
	else:
		log_label.text += "\n" + new_line

	# 滚动到底部
	await get_tree().process_frame
	var scroll_container := $VBoxContainer/LogContainer
	if scroll_container:
		scroll_container.scroll_vertical = scroll_container.get_v_scroll_bar().max_value


func _get_timestamp() -> String:
	var datetime_dict := Time.get_datetime_dict_from_system()
	return "%02d:%02d:%02d" % [
		datetime_dict.hour,
		datetime_dict.minute,
		datetime_dict.second
	]


func _exit_tree() -> void:
	if vibe_client:
		if vibe_client.has_signal("connection_status_changed"):
			vibe_client.connection_status_changed.disconnect(_on_connection_status_changed)
		if vibe_client.has_signal("player_data_received"):
			vibe_client.player_data_received.disconnect(_on_player_data_received)
		if vibe_client.has_signal("energy_received"):
			vibe_client.energy_received.disconnect(_on_energy_received)
		if vibe_client.has_signal("flow_state_changed"):
			vibe_client.flow_state_changed.disconnect(_on_flow_state_changed)
