## reward_popup.gd
## 奖励弹窗脚本
extends Control

signal popup_closed()

@onready var title_label: Label = $Panel/VBox/TitleLabel
@onready var rewards_container: VBoxContainer = $Panel/VBox/ScrollContainer/RewardsContainer
@onready var confirm_button: Button = $Panel/VBox/ConfirmButton

func _ready() -> void:
	if confirm_button:
		confirm_button.pressed.connect(_on_confirm_pressed)


## 设置奖励
func set_rewards(rewards: Dictionary) -> void:
	if not rewards_container:
		return

	# 清空现有内容
	for child in rewards_container.get_children():
		child.queue_free()

	# 添加奖励项
	if rewards.has("gold") and rewards["gold"] > 0:
		_add_reward_item("🪙", "金币", str(rewards["gold"]))
	if rewards.has("exp") and rewards["exp"] > 0:
		_add_reward_item("⭐", "经验", str(rewards["exp"]))
	if rewards.has("energy") and rewards["energy"] > 0:
		_add_reward_item("💜", "能量", str(rewards["energy"]))
	if rewards.has("diamonds") and rewards["diamonds"] > 0:
		_add_reward_item("💎", "钻石", str(rewards["diamonds"]))


## 添加奖励项
func _add_reward_item(icon: String, name: String, value: String) -> void:
	if not rewards_container:
		return

	var hbox := HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 15)

	var icon_label := Label.new()
	icon_label.text = icon
	icon_label.add_theme_font_size_override("font_size", 32)
	hbox.add_child(icon_label)

	var name_label := Label.new()
	name_label.text = name
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(name_label)

	var value_label := Label.new()
	value_label.text = value
	value_label.add_theme_font_size_override("font_size", 18)
	value_label.add_theme_color_override("font_color", Color(0.8, 0.8, 0.6))
	hbox.add_child(value_label)

	rewards_container.add_child(hbox)


## 确认按钮点击
func _on_confirm_pressed() -> void:
	popup_closed.emit()
	queue_free()
