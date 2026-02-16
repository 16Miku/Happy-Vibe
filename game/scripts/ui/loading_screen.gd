## loading_screen.gd
## 加载界面脚本 - 显示加载进度和状态
extends Control

## 加载进度
var loading_progress: float = 0.0

## 加载状态文本
var status_text: String = "加载中..."

## 是否自动关闭
var auto_close: bool = true

## 最小显示时间（秒）
var min_display_time: float = 1.0

var _display_timer: float = 0.0
var _is_loading: bool = false
var _target_scene_path: String = ""

@onready var progress_bar: ProgressBar = $CenterContainer/VBoxContainer/ProgressBar
@onready var status_label: Label = $CenterContainer/VBoxContainer/StatusLabel
@onready var tips_label: Label = $CenterContainer/VBoxContainer/TipsLabel
@onready var animation_player: AnimationPlayer = $AnimationPlayer

## 加载提示数组
var _loading_tips: PackedStringArray = [
	"编码能产生能量，能量能让你的农场繁荣！",
	"保持心流状态可以获得额外的能量加成！",
	"完成日常任务可以获得大量奖励！",
	"加入公会可以与好友一起参与公会战！",
	"在 PVP 竞技场中挑战其他玩家证明实力！",
	"记得每天签到获取签到奖励！",
	"装饰你的农场，展示你的独特风格！",
	"赛季通行证提供大量专属奖励！",
]

func _ready() -> void:
	_show_random_tip()
	if animation_player:
		animation_player.play("spin")


func _process(delta: float) -> void:
	if _is_loading:
		_display_timer += delta
		_update_progress()


## 开始加载
func start_loading(target_scene: String = "") -> void:
	_target_scene_path = target_scene
	_is_loading = true
	_display_timer = 0.0
	loading_progress = 0.0
	_show_random_tip()
	visible = true


## 设置加载进度
func set_progress(value: float) -> void:
	loading_progress = clamp(value, 0.0, 1.0)


## 设置状态文本
func set_status(text: String) -> void:
	status_text = text
	if status_label:
		status_label.text = text


## 显示随机提示
func _show_random_tip() -> void:
	if tips_label and _loading_tips.size() > 0:
		var random_index := randi() % _loading_tips.size()
		tips_label.text = _loading_tips[random_index]


## 更新进度显示
func _update_progress() -> void:
	if progress_bar:
		progress_bar.value = loading_progress
	if status_label:
		status_label.text = status_text + " (%d%%)" % int(loading_progress * 100)

	# 检查是否完成
	if loading_progress >= 1.0 and _display_timer >= min_display_time:
		_finish_loading()


## 完成加载
func _finish_loading() -> void:
	_is_loading = false

	if not auto_close:
		return

	if not _target_scene_path.is_empty():
		get_tree().change_scene_to_file(_target_scene_path)
	else:
		queue_free()


## 显示加载界面
func show_loading() -> void:
	visible = true
	_is_loading = true
	_display_timer = 0.0
	loading_progress = 0.0


## 隐藏加载界面
func hide_loading() -> void:
	visible = false
	_is_loading = false
