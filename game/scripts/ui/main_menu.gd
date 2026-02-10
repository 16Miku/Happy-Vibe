extends Control
## 主菜单脚本

@onready var start_button: Button = $VBoxContainer/StartButton
@onready var settings_button: Button = $VBoxContainer/SettingsButton
@onready var quit_button: Button = $VBoxContainer/QuitButton


func _ready() -> void:
	_connect_buttons()


func _connect_buttons() -> void:
	"""连接按钮信号"""
	if start_button:
		start_button.pressed.connect(_on_start_pressed)
	if settings_button:
		settings_button.pressed.connect(_on_settings_pressed)
	if quit_button:
		quit_button.pressed.connect(_on_quit_pressed)


func _on_start_pressed() -> void:
	"""开始游戏"""
	get_tree().change_scene_to_file("res://scenes/main/game_world.tscn")


func _on_settings_pressed() -> void:
	"""打开设置"""
	# TODO: 实现设置界面
	pass


func _on_quit_pressed() -> void:
	"""退出游戏"""
	get_tree().quit()
