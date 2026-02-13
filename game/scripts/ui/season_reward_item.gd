## season_reward_item.gd
## 赛季奖励项 UI 组件 - 显示单个等级的免费和高级奖励
extends PanelContainer

signal free_claim_pressed()
signal premium_claim_pressed()

# 节点引用
@onready var level_label: Label = $VBoxContainer/LevelLabel
@onready var free_reward_panel: PanelContainer = $VBoxContainer/FreeReward
@onready var free_reward_text: Label = $VBoxContainer/FreeReward/FreeContent/FreeRewardText
@onready var free_claim_btn: Button = $VBoxContainer/FreeClaimBtn
@onready var premium_reward_panel: PanelContainer = $VBoxContainer/PremiumReward
@onready var premium_reward_text: Label = $VBoxContainer/PremiumReward/PremiumContent/PremiumRewardText
@onready var premium_claim_btn: Button = $VBoxContainer/PremiumClaimBtn

# 数据
var reward_level: int = 0
var is_unlocked: bool = false
var has_premium: bool = false


func _ready() -> void:
	free_claim_btn.pressed.connect(_on_free_claim_pressed)
	premium_claim_btn.pressed.connect(_on_premium_claim_pressed)


## 设置奖励数据
func setup(level: int, free_reward: Dictionary, premium_reward: Dictionary,
		current_level: int, player_has_premium: bool,
		free_claimed: bool, premium_claimed: bool) -> void:

	reward_level = level
	is_unlocked = current_level >= level
	has_premium = player_has_premium

	# 等级标签
	level_label.text = "Lv.%d" % level

	# 免费奖励
	free_reward_text.text = _format_reward(free_reward)

	# 高级奖励
	premium_reward_text.text = _format_reward(premium_reward)

	# 更新状态
	_update_free_state(free_claimed)
	_update_premium_state(premium_claimed)

	# 整体样式
	_update_panel_style()


## 格式化奖励文本
func _format_reward(reward: Dictionary) -> String:
	var parts: Array = []

	if reward.has("gold"):
		parts.append("%d金" % reward["gold"])
	if reward.has("diamonds"):
		parts.append("%d钻" % reward["diamonds"])
	if reward.has("exp"):
		parts.append("%d经验" % reward["exp"])
	if reward.has("decoration"):
		parts.append("装饰")
	if reward.has("items"):
		parts.append("物品x%d" % reward["items"].size())
	if reward.has("title"):
		parts.append("称号")

	if parts.is_empty():
		return "-"

	return "\n".join(parts)


## 更新免费奖励状态
func _update_free_state(claimed: bool) -> void:
	if claimed:
		free_claim_btn.text = "已领取"
		free_claim_btn.disabled = true
		free_reward_panel.modulate = Color(0.6, 0.6, 0.6)
	elif is_unlocked:
		free_claim_btn.text = "领取"
		free_claim_btn.disabled = false
		free_reward_panel.modulate = Color.WHITE
	else:
		free_claim_btn.text = "未解锁"
		free_claim_btn.disabled = true
		free_reward_panel.modulate = Color(0.5, 0.5, 0.5)


## 更新高级奖励状态
func _update_premium_state(claimed: bool) -> void:
	if claimed:
		premium_claim_btn.text = "已领取"
		premium_claim_btn.disabled = true
		premium_reward_panel.modulate = Color(0.6, 0.6, 0.6)
	elif not has_premium:
		premium_claim_btn.text = "需高级"
		premium_claim_btn.disabled = true
		premium_reward_panel.modulate = Color(0.4, 0.4, 0.4)
	elif is_unlocked:
		premium_claim_btn.text = "领取"
		premium_claim_btn.disabled = false
		premium_reward_panel.modulate = Color.WHITE
	else:
		premium_claim_btn.text = "未解锁"
		premium_claim_btn.disabled = true
		premium_reward_panel.modulate = Color(0.5, 0.5, 0.5)


## 更新面板样式
func _update_panel_style() -> void:
	var style := StyleBoxFlat.new()
	style.set_corner_radius_all(6)
	style.content_margin_left = 5
	style.content_margin_right = 5
	style.content_margin_top = 5
	style.content_margin_bottom = 5

	if is_unlocked:
		style.bg_color = Color(0.2, 0.22, 0.25)
		style.border_color = Color(0.4, 0.5, 0.4)
		style.border_width_bottom = 2
	else:
		style.bg_color = Color(0.15, 0.15, 0.18)
		modulate = Color(0.7, 0.7, 0.7)

	add_theme_stylebox_override("panel", style)

	# 免费奖励面板样式
	var free_style := StyleBoxFlat.new()
	free_style.set_corner_radius_all(4)
	free_style.bg_color = Color(0.18, 0.2, 0.22)
	free_reward_panel.add_theme_stylebox_override("panel", free_style)

	# 高级奖励面板样式
	var premium_style := StyleBoxFlat.new()
	premium_style.set_corner_radius_all(4)
	premium_style.bg_color = Color(0.25, 0.2, 0.15)
	premium_style.border_color = Color(0.6, 0.5, 0.2)
	premium_style.border_width_left = 1
	premium_style.border_width_right = 1
	premium_style.border_width_top = 1
	premium_style.border_width_bottom = 1
	premium_reward_panel.add_theme_stylebox_override("panel", premium_style)


## 免费领取按钮点击
func _on_free_claim_pressed() -> void:
	free_claim_pressed.emit()


## 高级领取按钮点击
func _on_premium_claim_pressed() -> void:
	premium_claim_pressed.emit()
