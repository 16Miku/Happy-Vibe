## settings.gd
## 设置面板 UI - 管理游戏设置
extends Control

# 节点引用
@onready var close_button: Button = $MarginContainer/VBoxContainer/Header/CloseButton
@onready var master_slider: HSlider = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AudioSection/MasterVolume/MasterSlider
@onready var master_value: Label = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AudioSection/MasterVolume/MasterValue
@onready var music_slider: HSlider = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AudioSection/MusicVolume/MusicSlider
@onready var music_value: Label = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AudioSection/MusicVolume/MusicValue
@onready var sfx_slider: HSlider = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AudioSection/SFXVolume/SFXSlider
@onready var sfx_value: Label = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AudioSection/SFXVolume/SFXValue
@onready var fullscreen_check: CheckBox = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/DisplaySection/Fullscreen/FullscreenCheck
@onready var vsync_check: CheckBox = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/DisplaySection/VSync/VSyncCheck
@onready var notifications_check: CheckBox = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/GameSection/Notifications/NotificationsCheck
@onready var autosave_check: CheckBox = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/GameSection/AutoSave/AutoSaveCheck
@onready var username_edit: LineEdit = $MarginContainer/VBoxContainer/ScrollContainer/SettingsContent/AccountSection/Username/UsernameEdit
@onready var save_button: Button = $MarginContainer/VBoxContainer/ButtonContainer/SaveButton
@onready var reset_button: Button = $MarginContainer/VBoxContainer/ButtonContainer/ResetButton

# 设置数据
var settings: Dictionary = {}
var original_settings: Dictionary = {}


func _ready() -> void:
	_setup_ui()
	_load_settings()
	_apply_settings_to_ui()


func _setup_ui() -> void:
	close_button.pressed.connect(_on_close_pressed)
	save_button.pressed.connect(_on_save_pressed)
	reset_button.pressed.connect(_on_reset_pressed)

	# 音量滑块
	master_slider.value_changed.connect(_on_master_volume_changed)
	music_slider.value_changed.connect(_on_music_volume_changed)
	sfx_slider.value_changed.connect(_on_sfx_volume_changed)

	# 显示设置
	fullscreen_check.toggled.connect(_on_fullscreen_toggled)
	vsync_check.toggled.connect(_on_vsync_toggled)


## 加载设置
func _load_settings() -> void:
	if GameManager and GameManager.player_data.has("settings"):
		settings = GameManager.player_data["settings"].duplicate()
	else:
		settings = _get_default_settings()

	original_settings = settings.duplicate()

	# 加载用户名
	if GameManager:
		username_edit.text = GameManager.get_username()


## 获取默认设置
func _get_default_settings() -> Dictionary:
	return {
		"master_volume": 1.0,
		"music_volume": 1.0,
		"sfx_volume": 1.0,
		"fullscreen": false,
		"vsync": true,
		"notifications_enabled": true,
		"autosave_enabled": true
	}


## 应用设置到 UI
func _apply_settings_to_ui() -> void:
	master_slider.value = settings.get("master_volume", 1.0)
	music_slider.value = settings.get("music_volume", 1.0)
	sfx_slider.value = settings.get("sfx_volume", 1.0)
	fullscreen_check.button_pressed = settings.get("fullscreen", false)
	vsync_check.button_pressed = settings.get("vsync", true)
	notifications_check.button_pressed = settings.get("notifications_enabled", true)
	autosave_check.button_pressed = settings.get("autosave_enabled", true)

	_update_volume_labels()


## 更新音量标签
func _update_volume_labels() -> void:
	master_value.text = "%d%%" % int(master_slider.value * 100)
	music_value.text = "%d%%" % int(music_slider.value * 100)
	sfx_value.text = "%d%%" % int(sfx_slider.value * 100)


## 保存设置
func _save_settings() -> void:
	settings["master_volume"] = master_slider.value
	settings["music_volume"] = music_slider.value
	settings["sfx_volume"] = sfx_slider.value
	settings["fullscreen"] = fullscreen_check.button_pressed
	settings["vsync"] = vsync_check.button_pressed
	settings["notifications_enabled"] = notifications_check.button_pressed
	settings["autosave_enabled"] = autosave_check.button_pressed

	if GameManager:
		GameManager.player_data["settings"] = settings.duplicate()

		# 保存用户名
		var new_username: String = username_edit.text.strip_edges()
		if not new_username.is_empty():
			GameManager.set_username(new_username)

		GameManager.save_player_data()

	# 应用设置
	_apply_audio_settings()
	_apply_display_settings()

	original_settings = settings.duplicate()

	if EventBus:
		EventBus.notify_success("设置已保存")


## 应用音频设置
func _apply_audio_settings() -> void:
	# 设置音频总线音量
	var master_db: float = linear_to_db(settings.get("master_volume", 1.0))
	var music_db: float = linear_to_db(settings.get("music_volume", 1.0))
	var sfx_db: float = linear_to_db(settings.get("sfx_volume", 1.0))

	# 假设有 Master, Music, SFX 三个音频总线
	var master_bus_idx: int = AudioServer.get_bus_index("Master")
	if master_bus_idx >= 0:
		AudioServer.set_bus_volume_db(master_bus_idx, master_db)

	var music_bus_idx: int = AudioServer.get_bus_index("Music")
	if music_bus_idx >= 0:
		AudioServer.set_bus_volume_db(music_bus_idx, music_db)

	var sfx_bus_idx: int = AudioServer.get_bus_index("SFX")
	if sfx_bus_idx >= 0:
		AudioServer.set_bus_volume_db(sfx_bus_idx, sfx_db)


## 应用显示设置
func _apply_display_settings() -> void:
	# 全屏模式
	if settings.get("fullscreen", false):
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)

	# 垂直同步
	if settings.get("vsync", true):
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
	else:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)


# ==================== 事件处理 ====================

func _on_close_pressed() -> void:
	# 检查是否有未保存的更改
	if _has_unsaved_changes():
		if EventBus:
			EventBus.request_confirm(
				"未保存的更改",
				"您有未保存的设置更改，是否保存？",
				_save_and_close
			)
		else:
			hide()
	else:
		hide()

	if EventBus:
		EventBus.close_panel.emit("settings")


func _save_and_close() -> void:
	_save_settings()
	hide()


func _on_save_pressed() -> void:
	_save_settings()


func _on_reset_pressed() -> void:
	settings = _get_default_settings()
	_apply_settings_to_ui()
	if EventBus:
		EventBus.notify("设置已重置为默认值")


func _on_master_volume_changed(value: float) -> void:
	master_value.text = "%d%%" % int(value * 100)
	# 实时预览
	var master_bus_idx: int = AudioServer.get_bus_index("Master")
	if master_bus_idx >= 0:
		AudioServer.set_bus_volume_db(master_bus_idx, linear_to_db(value))


func _on_music_volume_changed(value: float) -> void:
	music_value.text = "%d%%" % int(value * 100)
	var music_bus_idx: int = AudioServer.get_bus_index("Music")
	if music_bus_idx >= 0:
		AudioServer.set_bus_volume_db(music_bus_idx, linear_to_db(value))


func _on_sfx_volume_changed(value: float) -> void:
	sfx_value.text = "%d%%" % int(value * 100)
	var sfx_bus_idx: int = AudioServer.get_bus_index("SFX")
	if sfx_bus_idx >= 0:
		AudioServer.set_bus_volume_db(sfx_bus_idx, linear_to_db(value))


func _on_fullscreen_toggled(pressed: bool) -> void:
	# 实时预览
	if pressed:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)


func _on_vsync_toggled(pressed: bool) -> void:
	if pressed:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
	else:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)


## 检查是否有未保存的更改
func _has_unsaved_changes() -> bool:
	if master_slider.value != original_settings.get("master_volume", 1.0):
		return true
	if music_slider.value != original_settings.get("music_volume", 1.0):
		return true
	if sfx_slider.value != original_settings.get("sfx_volume", 1.0):
		return true
	if fullscreen_check.button_pressed != original_settings.get("fullscreen", false):
		return true
	if vsync_check.button_pressed != original_settings.get("vsync", true):
		return true
	if notifications_check.button_pressed != original_settings.get("notifications_enabled", true):
		return true
	if autosave_check.button_pressed != original_settings.get("autosave_enabled", true):
		return true
	return false


## 显示面板
func show_panel() -> void:
	_load_settings()
	_apply_settings_to_ui()
	show()


## 隐藏面板
func hide_panel() -> void:
	hide()
