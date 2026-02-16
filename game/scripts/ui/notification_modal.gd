## notification_modal.gd
## 通知弹窗脚本
extends Control

## 通知类型
var notification_type: String = "info"

## 通知持续时间
var duration: float = 3.0

@onready var icon_label: Label = $Panel/HBox/IconLabel
@onready var message_label: Label = $Panel/HBox/MessageLabel
@onready var animation_player: AnimationPlayer = $AnimationPlayer

## 类型配置
var type_config := {
	"info": {"icon": "ℹ️", "color": Color(0.3, 0.6, 1.0)},
	"success": {"icon": "✅", "color": Color(0.2, 0.8, 0.2)},
	"warning": {"icon": "⚠️", "color": Color(1.0, 0.6, 0.0)},
	"error": {"icon": "❌", "color": Color(0.8, 0.2, 0.2)}
}

func _ready() -> void:
	# 设置位置到屏幕顶部中央
	position = Vector2(
		(get_viewport_rect().size.x - custom_minimum_size.x) / 2,
		50
	)

	# 播放进入动画
	if animation_player and animation_player.has_animation("show"):
		animation_player.play("show")


## 设置消息
func set_message(message: String) -> void:
	if message_label:
		message_label.text = message


## 设置类型
func set_type(type: String) -> void:
	notification_type = type
	_update_style()


## 更新样式
func _update_style() -> void:
	if not type_config.has(notification_type):
		notification_type = "info"

	var config = type_config[notification_type]

	if icon_label:
		icon_label.text = config["icon"]

	if message_label:
		message_label.modulate = config["color"]
