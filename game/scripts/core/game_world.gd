extends Node2D
## 游戏世界场景脚本
## 管理游戏主场景的初始化和更新

@onready var camera: Camera2D = $Camera2D
@onready var player: CharacterBody2D = $Player
@onready var hud: Control = $CanvasLayer/HUD


func _ready() -> void:
	_setup_camera()
	_connect_signals()


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
