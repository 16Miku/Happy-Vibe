extends Node2D
## 游戏世界场景脚本
## 管理游戏主场景的初始化和更新

@onready var player: CharacterBody2D = $Player
@onready var camera: Camera2D = $Player/Camera2D
@onready var hud: Control = $CanvasLayer/HUD
@onready var farm: Node2D = $Farm


func _ready() -> void:
	_setup_camera()
	_connect_signals()
	_sync_data_from_backend()
	_check_tutorial()


func _setup_camera() -> void:
	"""设置摄像机"""
	if camera:
		camera.make_current()


func _connect_signals() -> void:
	"""连接信号"""
	if GameManager.is_initialized:
		_update_hud()

	GameManager.energy_changed.connect(_on_energy_changed)
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.level_up.connect(_on_level_up)


func _update_hud() -> void:
	"""更新 HUD 显示"""
	pass  # HUD 脚本会处理具体更新


func _on_energy_changed(_value: int) -> void:
	_update_hud()


func _on_gold_changed(_value: int) -> void:
	_update_hud()


func _on_level_up(new_level: int) -> void:
	EventBus.notify("升级了！当前等级: %d" % new_level, "success")


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		_toggle_pause()


func _toggle_pause() -> void:
	"""切换暂停状态"""
	var tree := get_tree()
	if tree:
		tree.paused = not tree.paused
		if tree.paused:
			EventBus.game_paused.emit()
		else:
			EventBus.game_resumed.emit()


func _sync_data_from_backend() -> void:
	"""从后端同步数据"""
	# 连接 VibeClient 信号
	if VibeClient:
		VibeClient.energy_received.connect(_on_energy_received)
		VibeClient.farm_data_received.connect(_on_farm_data_received)
		VibeClient.connection_status_changed.connect(_on_connection_status_changed)

		# 请求初始数据
		if VibeClient.is_connected:
			VibeClient.get_player()
			VibeClient.get_farm()


func _on_energy_received(amount: int, _breakdown: Dictionary) -> void:
	"""收到能量数据"""
	GameManager.add_energy(amount)


func _on_farm_data_received(data: Dictionary) -> void:
	"""收到农场数据"""
	if farm and farm.has_method("load_from_data"):
		farm.load_from_data(data)


func _on_connection_status_changed(connected: bool) -> void:
	"""连接状态变化"""
	if connected:
		EventBus.notify("已连接到 VibeHub", "success")
		VibeClient.get_player()
		VibeClient.get_farm()
	else:
		EventBus.notify("与 VibeHub 断开连接", "warning")


func _check_tutorial() -> void:
	"""检查是否需要显示新手引导"""
	if TutorialManager and TutorialManager.should_show_tutorial():
		# 延迟一帧启动引导，确保 HUD 已加载
		await get_tree().process_frame
		var hud_node := _find_hud()
		TutorialManager.start_tutorial(hud_node)


func _find_hud() -> Control:
	"""查找 HUD 节点"""
	var canvas_layer := get_node_or_null("CanvasLayer")
	if canvas_layer:
		var hud_control := canvas_layer.get_node_or_null("HUD")
		if hud_control:
			return hud_control
	return null
