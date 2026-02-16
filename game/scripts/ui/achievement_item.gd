## achievement_item.gd
## 成就项 UI 组件
extends Control

## 成就数据
var achievement_data: DataManager.AchievementDefinition = null

## 成就进度数据
var progress_data: DataManager.AchievementProgress = null

@onready var icon_label: Label = $HBox/IconLabel
@onready var name_label: Label = $HBox/VBox/NameLabel
@onready var description_label: Label = $HBox/VBox/DescriptionLabel
@onready var progress_bar: ProgressBar = $HBox/VBox/ProgressBar
@onready var reward_label: Label = $HBox/VBox/RewardLabel
@onready var claim_button: Button = $HBox/ClaimButton
@onready var tier_icon: Label = $HBox/TierIcon

## 成就等级对应的颜色和图标
var tier_config := {
	"bronze": {"color": Color(0.72, 0.45, 0.2), "icon": "🥉"},
	"silver": {"color": Color(0.75, 0.75, 0.75), "icon": "🥈"},
	"gold": {"color": Color(1.0, 0.84, 0.0), "icon": "🥇"},
	"platinum": {"color": Color(0.82, 0.89, 0.93), "icon": "💎"},
	"legendary": {"color": Color(1.0, 0.5, 0.0), "icon": "🏆"}
}

func _ready() -> void:
	if claim_button:
		claim_button.pressed.connect(_on_claim_pressed)


## 设置成就数据
func set_achievement_data(achievement: DataManager.AchievementDefinition, progress: DataManager.AchievementProgress) -> void:
	achievement_data = achievement
	progress_data = progress
	_update_display()


## 更新显示
func _update_display() -> void:
	if not achievement_data:
		return

	# 设置名称
	if name_label:
		name_label.text = achievement_data.name

	# 设置描述
	if description_label:
		description_label.text = achievement_data.description

	# 设置进度条
	if progress_bar and achievement_data:
		var current_value := progress_data.current_value if progress_data else 0
		var target_value := achievement_data.target_value
		progress_bar.max_value = target_value
		progress_bar.value = current_value

	# 设置奖励文本
	if reward_label and achievement_data.rewards:
		var rewards_text := ""
		if achievement_data.rewards.has("gold"):
			rewards_text += "🪙 %d " % achievement_data.rewards["gold"]
		if achievement_data.rewards.has("exp"):
			rewards_text += "⭐ %d " % achievement_data.rewards["exp"]
		if achievement_data.rewards.has("diamonds"):
			rewards_text += "💎 %d " % achievement_data.rewards["diamonds"]
		reward_label.text = rewards_text.strip_edges()

	# 设置等级图标和颜色
	if tier_icon and tier_config.has(achievement_data.tier):
		var config = tier_config[achievement_data.tier]
		tier_icon.text = config["icon"]
		tier_icon.modulate = config["color"]

	# 设置领取按钮状态
	_update_claim_button()


## 更新领取按钮状态
func _update_claim_button() -> void:
	if not claim_button or not progress_data:
		return

	if progress_data.claimed:
		claim_button.text = "已领取"
		claim_button.disabled = true
	elif progress_data.completed:
		claim_button.text = "领取奖励"
		claim_button.disabled = false
	else:
		claim_button.text = "未完成"
		claim_button.disabled = true


## 领取奖励点击
func _on_claim_pressed() -> void:
	if not achievement_data or not DataManager:
		return

	DataManager.claim_achievement(achievement_data.id, func(success: bool, data: Dictionary)
		if success:
			print("[AchievementItem] 成就奖励领取成功: ", achievement_data.id)
			# 刷新按钮状态
			if progress_data:
				progress_data.claimed = true
			_update_claim_button()
			# 显示奖励弹窗
			if data.has("rewards"):
				EventBus.show_rewards.emit(data["rewards"])
		else:
			push_error("[AchievementItem] 成就奖励领取失败")
	)
)
