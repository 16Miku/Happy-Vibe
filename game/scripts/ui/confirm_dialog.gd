## confirm_dialog.gd
## 确认对话框脚本
extends Control

signal confirmed()
signal canceled()

@onready var title_label: Label = $Panel/VBox/TitleLabel
@onready var message_label: Label = $Panel/VBox/MessageLabel
@onready var confirm_button: Button = $Panel/VBox/ButtonContainer/ConfirmButton
@onready var cancel_button: Button = $Panel/VBox/ButtonContainer/CancelButton

func _ready() -> void:
	if confirm_button:
		confirm_button.pressed.connect(func(): confirmed.emit())
	if cancel_button:
		cancel_button.pressed.connect(func(): canceled.emit())


## 设置标题
func set_title(title: String) -> void:
	if title_label:
		title_label.text = title


## 设置消息
func set_message(message: String) -> void:
	if message_label:
		message_label.text = message
