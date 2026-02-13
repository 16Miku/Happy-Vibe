## audio_manager.gd
## 音频管理器 - 管理背景音乐和音效播放
## 作为 AutoLoad 单例运行
extends Node

# 信号
signal music_changed(track_name: String)
signal sfx_played(sfx_name: String)

# 音频播放器
var music_player: AudioStreamPlayer = null
var sfx_players: Array[AudioStreamPlayer] = []

# 音频设置
var master_volume: float = 1.0
var music_volume: float = 1.0
var sfx_volume: float = 1.0
var music_enabled: bool = true
var sfx_enabled: bool = true

# 当前播放
var current_music: String = ""
var music_fade_tween: Tween = null

# 常量
const MAX_SFX_PLAYERS: int = 8
const MUSIC_FADE_DURATION: float = 1.0

# 音乐轨道定义
const MUSIC_TRACKS: Dictionary = {
	"menu": "res://assets/audio/music/menu_theme.ogg",
	"farm": "res://assets/audio/music/farm_theme.ogg",
	"flow": "res://assets/audio/music/flow_theme.ogg",
	"shop": "res://assets/audio/music/shop_theme.ogg",
	"event": "res://assets/audio/music/event_theme.ogg"
}

# 音效定义
const SFX_SOUNDS: Dictionary = {
	"click": "res://assets/audio/sfx/click.wav",
	"success": "res://assets/audio/sfx/success.wav",
	"error": "res://assets/audio/sfx/error.wav",
	"coin": "res://assets/audio/sfx/coin.wav",
	"levelup": "res://assets/audio/sfx/levelup.wav",
	"harvest": "res://assets/audio/sfx/harvest.wav",
	"plant": "res://assets/audio/sfx/plant.wav",
	"water": "res://assets/audio/sfx/water.wav",
	"build": "res://assets/audio/sfx/build.wav",
	"notification": "res://assets/audio/sfx/notification.wav",
	"reward": "res://assets/audio/sfx/reward.wav",
	"flow_enter": "res://assets/audio/sfx/flow_enter.wav",
	"flow_exit": "res://assets/audio/sfx/flow_exit.wav"
}


func _ready() -> void:
	_setup_audio_players()
	_load_settings()
	_connect_signals()


## 设置音频播放器
func _setup_audio_players() -> void:
	# 创建音乐播放器
	music_player = AudioStreamPlayer.new()
	music_player.bus = "Music"
	add_child(music_player)
	music_player.finished.connect(_on_music_finished)

	# 创建音效播放器池
	for i in range(MAX_SFX_PLAYERS):
		var sfx_player := AudioStreamPlayer.new()
		sfx_player.bus = "SFX"
		add_child(sfx_player)
		sfx_players.append(sfx_player)


## 加载音频设置
func _load_settings() -> void:
	if GameManager and GameManager.player_data.has("settings"):
		var settings: Dictionary = GameManager.player_data["settings"]
		master_volume = settings.get("master_volume", 1.0)
		music_volume = settings.get("music_volume", 1.0)
		sfx_volume = settings.get("sfx_volume", 1.0)

	_apply_volume_settings()


## 应用音量设置
func _apply_volume_settings() -> void:
	# 设置音频总线音量
	var master_bus_idx: int = AudioServer.get_bus_index("Master")
	if master_bus_idx >= 0:
		AudioServer.set_bus_volume_db(master_bus_idx, linear_to_db(master_volume))

	var music_bus_idx: int = AudioServer.get_bus_index("Music")
	if music_bus_idx >= 0:
		AudioServer.set_bus_volume_db(music_bus_idx, linear_to_db(music_volume))

	var sfx_bus_idx: int = AudioServer.get_bus_index("SFX")
	if sfx_bus_idx >= 0:
		AudioServer.set_bus_volume_db(sfx_bus_idx, linear_to_db(sfx_volume))


## 连接信号
func _connect_signals() -> void:
	if EventBus:
		EventBus.flow_state_achieved.connect(_on_flow_entered)
		EventBus.flow_state_ended.connect(_on_flow_exited)
		EventBus.crop_harvested.connect(_on_crop_harvested)
		EventBus.gold_updated.connect(_on_gold_updated)
		EventBus.player_leveled_up.connect(_on_level_up)
		EventBus.achievement_unlocked.connect(_on_achievement_unlocked)


# ==================== 音乐控制 ====================

## 播放音乐
func play_music(track_name: String, fade_in: bool = true) -> void:
	if not music_enabled:
		return

	if current_music == track_name and music_player.playing:
		return

	var track_path: String = MUSIC_TRACKS.get(track_name, "")
	if track_path.is_empty():
		push_warning("[AudioManager] 未找到音乐轨道: ", track_name)
		return

	if not ResourceLoader.exists(track_path):
		push_warning("[AudioManager] 音乐文件不存在: ", track_path)
		return

	# 淡出当前音乐
	if music_player.playing and fade_in:
		_fade_out_music(func(): _start_music(track_name, track_path, fade_in))
	else:
		_start_music(track_name, track_path, fade_in)


## 开始播放音乐
func _start_music(track_name: String, track_path: String, fade_in: bool) -> void:
	var stream := load(track_path) as AudioStream
	if stream:
		music_player.stream = stream
		current_music = track_name

		if fade_in:
			music_player.volume_db = -80.0
			music_player.play()
			_fade_in_music()
		else:
			music_player.volume_db = 0.0
			music_player.play()

		music_changed.emit(track_name)


## 淡入音乐
func _fade_in_music() -> void:
	if music_fade_tween:
		music_fade_tween.kill()

	music_fade_tween = create_tween()
	music_fade_tween.tween_property(music_player, "volume_db", 0.0, MUSIC_FADE_DURATION)


## 淡出音乐
func _fade_out_music(callback: Callable = Callable()) -> void:
	if music_fade_tween:
		music_fade_tween.kill()

	music_fade_tween = create_tween()
	music_fade_tween.tween_property(music_player, "volume_db", -80.0, MUSIC_FADE_DURATION)

	if callback.is_valid():
		music_fade_tween.tween_callback(callback)


## 停止音乐
func stop_music(fade_out: bool = true) -> void:
	if fade_out:
		_fade_out_music(func(): music_player.stop())
	else:
		music_player.stop()

	current_music = ""


## 暂停音乐
func pause_music() -> void:
	music_player.stream_paused = true


## 恢复音乐
func resume_music() -> void:
	music_player.stream_paused = false


## 音乐播放完成
func _on_music_finished() -> void:
	# 循环播放
	if not current_music.is_empty():
		music_player.play()


# ==================== 音效控制 ====================

## 播放音效
func play_sfx(sfx_name: String) -> void:
	if not sfx_enabled:
		return

	var sfx_path: String = SFX_SOUNDS.get(sfx_name, "")
	if sfx_path.is_empty():
		push_warning("[AudioManager] 未找到音效: ", sfx_name)
		return

	if not ResourceLoader.exists(sfx_path):
		# 音效文件不存在时静默失败（开发阶段可能没有音效文件）
		return

	var stream := load(sfx_path) as AudioStream
	if stream:
		var player := _get_available_sfx_player()
		if player:
			player.stream = stream
			player.play()
			sfx_played.emit(sfx_name)


## 获取可用的音效播放器
func _get_available_sfx_player() -> AudioStreamPlayer:
	for player in sfx_players:
		if not player.playing:
			return player

	# 如果所有播放器都在使用，返回第一个（会中断当前播放）
	return sfx_players[0]


## 停止所有音效
func stop_all_sfx() -> void:
	for player in sfx_players:
		player.stop()


# ==================== 音量控制 ====================

## 设置主音量
func set_master_volume(volume: float) -> void:
	master_volume = clampf(volume, 0.0, 1.0)
	var bus_idx: int = AudioServer.get_bus_index("Master")
	if bus_idx >= 0:
		AudioServer.set_bus_volume_db(bus_idx, linear_to_db(master_volume))


## 设置音乐音量
func set_music_volume(volume: float) -> void:
	music_volume = clampf(volume, 0.0, 1.0)
	var bus_idx: int = AudioServer.get_bus_index("Music")
	if bus_idx >= 0:
		AudioServer.set_bus_volume_db(bus_idx, linear_to_db(music_volume))


## 设置音效音量
func set_sfx_volume(volume: float) -> void:
	sfx_volume = clampf(volume, 0.0, 1.0)
	var bus_idx: int = AudioServer.get_bus_index("SFX")
	if bus_idx >= 0:
		AudioServer.set_bus_volume_db(bus_idx, linear_to_db(sfx_volume))


## 启用/禁用音乐
func set_music_enabled(enabled: bool) -> void:
	music_enabled = enabled
	if not enabled:
		stop_music(false)


## 启用/禁用音效
func set_sfx_enabled(enabled: bool) -> void:
	sfx_enabled = enabled
	if not enabled:
		stop_all_sfx()


# ==================== 事件处理 ====================

func _on_flow_entered() -> void:
	play_sfx("flow_enter")
	# 可以切换到心流状态音乐
	# play_music("flow")


func _on_flow_exited(_duration: int) -> void:
	play_sfx("flow_exit")


func _on_crop_harvested(_plot_id: String, _crop_data: Dictionary) -> void:
	play_sfx("harvest")


func _on_gold_updated(_amount: int) -> void:
	play_sfx("coin")


func _on_level_up(_new_level: int) -> void:
	play_sfx("levelup")


func _on_achievement_unlocked(_achievement_id: String) -> void:
	play_sfx("reward")


# ==================== 便捷方法 ====================

## 播放 UI 点击音效
func play_click() -> void:
	play_sfx("click")


## 播放成功音效
func play_success() -> void:
	play_sfx("success")


## 播放错误音效
func play_error() -> void:
	play_sfx("error")


## 播放通知音效
func play_notification() -> void:
	play_sfx("notification")
