extends Control
## 主菜单脚本

@onready var start_button: Button = $VBoxContainer/StartButton
@onready var settings_button: Button = $VBoxContainer/SettingsButton
@onready var quit_button: Button = $VBoxContainer/QuitButton

var settings_panel: Control = null


func _ready() -> void:
	_connect_buttons()
	_check_vibe_connection()


func _connect_buttons() -> void:
	"""连接按钮信号"""
	if start_button:
		start_button.pressed.connect(_on_start_pressed)
	if settings_button:
		settings_button.pressed.connect(_on_settings_pressed)
	if quit_button:
		quit_button.pressed.connect(_on_quit_pressed)


func _check_vibe_connection() -> void:
	"""检查 VibeHub 连接状态"""
	if VibeClient and VibeClient.is_connected:
		print("[MainMenu] VibeHub 已连接")
	else:
		print("[MainMenu] VibeHub 未连接，将使用本地存档")


func _on_start_pressed() -> void:
	"""开始游戏"""
	# 更新登录状态
	if GameManager:
		GameManager.update_login_status()
		GameManager.save_player_data()

	get_tree().change_scene_to_file("res://scenes/main/game_world.tscn")


func _on_settings_pressed() -> void:
	"""打开设置"""
	if settings_panel == null or not is_instance_valid(settings_panel):
		var panel_scene := load("res://scenes/ui/settings.tscn")
		if panel_scene:
			settings_panel = panel_scene.instantiate()
			add_child(settings_panel)
		else:
			push_warning("[MainMenu] 无法加载设置面板")
			return

	settings_panel.show()


func _on_quit_pressed() -> void:
	"""退出游戏"""
	# 保存数据
	if GameManager:
		GameManager.save_player_data()

	get_tree().quit()
