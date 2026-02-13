## quest_item.gd
## 任务项 UI 组件 - 显示单个任务的信息和状态
extends PanelContainer

signal claim_pressed()

# 节点引用
@onready var type_indicator: ColorRect = $HBoxContainer/TypeIndicator
@onready var quest_name: Label = $HBoxContainer/Content/Header/QuestName
@onready var type_label: Label = $HBoxContainer/Content/Header/TypeLabel
@onready var description: Label = $HBoxContainer/Content/Description
@onready var progress_bar: ProgressBar = $HBoxContainer/Content/ProgressContainer/ProgressBar
@onready var progress_label: Label = $HBoxContainer/Content/ProgressContainer/ProgressLabel
@onready var reward_label: Label = $HBoxContainer/Content/RewardLabel
@onready var claim_button: Button = $HBoxContainer/ClaimButton

# 任务数据
var quest_data: Dictionary = {}
var quest_id: String = ""

# 状态枚举引用
const QuestStatus = preload("res://scripts/quest/quest_manager.gd").QuestStatus
const QuestType = preload("res://scripts/quest/quest_manager.gd").QuestType


func _ready() -> void:
	claim_button.pressed.connect(_on_claim_button_pressed)


## 设置任务数据
func setup(data: Dictionary) -> void:
	quest_data = data
	quest_id = data.get("id", "")

	_update_display()


## 更新显示
func _update_display() -> void:
	var name_text: String = quest_data.get("name", "未知任务")
	var desc_text: String = quest_data.get("description", "")
	var quest_type: int = quest_data.get("type", QuestType.DAILY)
	var target: int = quest_data.get("target", 1)
	var progress: int = quest_data.get("progress", 0)
	var status: int = quest_data.get("status", QuestStatus.AVAILABLE)
	var rewards: Dictionary = quest_data.get("rewards", {})

	# 设置名称和描述
	quest_name.text = name_text
	description.text = desc_text

	# 设置类型标签和颜色
	type_label.text = "[%s]" % QuestData.get_type_name(quest_type)
	var type_color: Color = QuestData.get_type_color(quest_type)
	type_label.modulate = type_color
	type_indicator.color = type_color

	# 设置进度
	progress_bar.max_value = target
	progress_bar.value = progress
	progress_label.text = "%d/%d" % [progress, target]

	# 设置奖励文本
	reward_label.text = "奖励: " + QuestData.get_reward_text(rewards)

	# 根据状态更新按钮
	_update_button_state(status, progress, target)

	# 根据状态更新整体样式
	_update_style(status)


## 更新按钮状态
func _update_button_state(status: int, progress: int, target: int) -> void:
	match status:
		QuestStatus.LOCKED:
			claim_button.text = "未解锁"
			claim_button.disabled = true
		QuestStatus.AVAILABLE:
			claim_button.text = "进行中"
			claim_button.disabled = true
		QuestStatus.IN_PROGRESS:
			if progress >= target:
				claim_button.text = "领取"
				claim_button.disabled = false
			else:
				claim_button.text = "进行中"
				claim_button.disabled = true
		QuestStatus.COMPLETED:
			claim_button.text = "领取"
			claim_button.disabled = false
		QuestStatus.CLAIMED:
			claim_button.text = "已领取"
			claim_button.disabled = true


## 更新样式
func _update_style(status: int) -> void:
	var style := StyleBoxFlat.new()
	style.set_corner_radius_all(8)
	style.content_margin_left = 15
	style.content_margin_right = 15
	style.content_margin_top = 10
	style.content_margin_bottom = 10

	match status:
		QuestStatus.LOCKED:
			style.bg_color = Color(0.15, 0.15, 0.18, 1)
			modulate = Color(0.6, 0.6, 0.6, 1)
		QuestStatus.AVAILABLE, QuestStatus.IN_PROGRESS:
			style.bg_color = Color(0.18, 0.18, 0.22, 1)
			modulate = Color.WHITE
		QuestStatus.COMPLETED:
			style.bg_color = Color(0.2, 0.25, 0.2, 1)
			style.border_color = Color(0.4, 0.7, 0.4, 1)
			style.border_width_left = 2
			style.border_width_right = 2
			style.border_width_top = 2
			style.border_width_bottom = 2
			modulate = Color.WHITE
		QuestStatus.CLAIMED:
			style.bg_color = Color(0.15, 0.15, 0.18, 1)
			modulate = Color(0.7, 0.7, 0.7, 1)

	add_theme_stylebox_override("panel", style)


## 领取按钮点击
func _on_claim_button_pressed() -> void:
	claim_pressed.emit()


## 更新进度
func update_progress(current: int, target: int) -> void:
	quest_data["progress"] = current
	progress_bar.value = current
	progress_label.text = "%d/%d" % [current, target]

	# 检查是否完成
	if current >= target and quest_data.get("status", 0) == QuestStatus.IN_PROGRESS:
		quest_data["status"] = QuestStatus.COMPLETED
		_update_button_state(QuestStatus.COMPLETED, current, target)
		_update_style(QuestStatus.COMPLETED)


## 设置为已领取状态
func set_claimed() -> void:
	quest_data["status"] = QuestStatus.CLAIMED
	_update_button_state(QuestStatus.CLAIMED, quest_data.get("progress", 0), quest_data.get("target", 1))
	_update_style(QuestStatus.CLAIMED)
