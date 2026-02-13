## test_quest_manager.gd
## 任务系统测试脚本
extends Control

@onready var status_label: Label = $VBoxContainer/StatusLabel
@onready var quest_list: RichTextLabel = $VBoxContainer/QuestList
@onready var load_daily_btn: Button = $VBoxContainer/ButtonGrid/LoadDailyBtn
@onready var load_weekly_btn: Button = $VBoxContainer/ButtonGrid/LoadWeeklyBtn
@onready var load_achievement_btn: Button = $VBoxContainer/ButtonGrid/LoadAchievementBtn
@onready var simulate_harvest_btn: Button = $VBoxContainer/ButtonGrid/SimulateHarvestBtn
@onready var simulate_energy_btn: Button = $VBoxContainer/ButtonGrid/SimulateEnergyBtn
@onready var simulate_flow_btn: Button = $VBoxContainer/ButtonGrid/SimulateFlowBtn
@onready var simulate_coding_btn: Button = $VBoxContainer/ButtonGrid/SimulateCodingBtn
@onready var open_quest_panel_btn: Button = $VBoxContainer/ButtonGrid/OpenQuestPanelBtn

var quest_panel: Control = null


func _ready() -> void:
	_connect_buttons()
	_connect_quest_signals()
	_update_status("任务系统测试就绪")


func _connect_buttons() -> void:
	load_daily_btn.pressed.connect(_on_load_daily_pressed)
	load_weekly_btn.pressed.connect(_on_load_weekly_pressed)
	load_achievement_btn.pressed.connect(_on_load_achievement_pressed)
	simulate_harvest_btn.pressed.connect(_on_simulate_harvest_pressed)
	simulate_energy_btn.pressed.connect(_on_simulate_energy_pressed)
	simulate_flow_btn.pressed.connect(_on_simulate_flow_pressed)
	simulate_coding_btn.pressed.connect(_on_simulate_coding_pressed)
	open_quest_panel_btn.pressed.connect(_on_open_quest_panel_pressed)


func _connect_quest_signals() -> void:
	if QuestManager:
		QuestManager.quest_accepted.connect(_on_quest_accepted)
		QuestManager.quest_progress_updated.connect(_on_quest_progress_updated)
		QuestManager.quest_completed.connect(_on_quest_completed)
		QuestManager.quest_reward_claimed.connect(_on_quest_reward_claimed)
		QuestManager.daily_quests_refreshed.connect(_on_daily_quests_refreshed)
		QuestManager.weekly_quests_refreshed.connect(_on_weekly_quests_refreshed)


func _update_status(text: String) -> void:
	status_label.text = "状态: " + text


func _display_quests(quests: Array, title: String) -> void:
	var text := "[b]%s[/b] (%d 个)\n\n" % [title, quests.size()]

	for quest in quests:
		var status_text := _get_status_text(quest.get("status", 0))
		var progress: int = quest.get("progress", 0)
		var target: int = quest.get("target", 1)
		var rewards: Dictionary = quest.get("rewards", {})

		text += "[color=#88aaff]● %s[/color]\n" % quest.get("name", "未知")
		text += "  %s\n" % quest.get("description", "")
		text += "  进度: [color=#ffcc44]%d/%d[/color] | 状态: %s\n" % [progress, target, status_text]
		text += "  奖励: [color=#ffdd66]%s[/color]\n\n" % QuestData.get_reward_text(rewards)

	quest_list.text = text


func _get_status_text(status: int) -> String:
	match status:
		0: return "[color=#666666]未解锁[/color]"
		1: return "[color=#88ff88]可接取[/color]"
		2: return "[color=#ffaa44]进行中[/color]"
		3: return "[color=#44ff44]已完成[/color]"
		4: return "[color=#888888]已领取[/color]"
		_: return "未知"


# ==================== 按钮事件 ====================

func _on_load_daily_pressed() -> void:
	if not QuestManager:
		_update_status("QuestManager 未加载")
		return

	var quests: Array = QuestManager.get_daily_quests()
	_display_quests(quests, "日常任务")
	_update_status("已加载 %d 个日常任务" % quests.size())


func _on_load_weekly_pressed() -> void:
	if not QuestManager:
		_update_status("QuestManager 未加载")
		return

	var quests: Array = QuestManager.get_weekly_quests()
	_display_quests(quests, "周常任务")
	_update_status("已加载 %d 个周常任务" % quests.size())


func _on_load_achievement_pressed() -> void:
	if not QuestManager:
		_update_status("QuestManager 未加载")
		return

	var quests: Array = QuestManager.get_achievement_quests()
	_display_quests(quests, "成就任务")
	_update_status("已加载 %d 个成就任务" % quests.size())


func _on_simulate_harvest_pressed() -> void:
	_update_status("模拟收获作物...")
	if EventBus:
		EventBus.crop_harvested.emit("plot_1", {"type": "variable_grass", "quality": 2, "value": 15})
		_update_status("已触发作物收获事件")
	else:
		_update_status("EventBus 未加载")


func _on_simulate_energy_pressed() -> void:
	_update_status("模拟获得能量...")
	if EventBus:
		EventBus.vibe_energy_received.emit(50, 5, false)
		_update_status("已触发能量获得事件 (+50)")
	else:
		_update_status("EventBus 未加载")


func _on_simulate_flow_pressed() -> void:
	_update_status("模拟进入心流状态...")
	if EventBus:
		EventBus.flow_state_achieved.emit()
		_update_status("已触发心流状态事件")
	else:
		_update_status("EventBus 未加载")


func _on_simulate_coding_pressed() -> void:
	_update_status("模拟编码 30 分钟...")
	if EventBus:
		EventBus.coding_session_ended.emit(30, 300)
		_update_status("已触发编码会话结束事件 (30分钟)")
	else:
		_update_status("EventBus 未加载")


func _on_open_quest_panel_pressed() -> void:
	if quest_panel == null:
		var panel_scene := load("res://scenes/ui/quest/quest_panel.tscn")
		if panel_scene:
			quest_panel = panel_scene.instantiate()
			add_child(quest_panel)
		else:
			_update_status("无法加载任务面板场景")
			return

	quest_panel.show()
	_update_status("已打开任务面板")


# ==================== 任务信号回调 ====================

func _on_quest_accepted(quest_id: String) -> void:
	_update_status("任务已接取: " + quest_id)


func _on_quest_progress_updated(quest_id: String, current: int, target: int) -> void:
	_update_status("任务进度更新: %s (%d/%d)" % [quest_id, current, target])


func _on_quest_completed(quest_id: String) -> void:
	_update_status("任务完成: " + quest_id)


func _on_quest_reward_claimed(quest_id: String, rewards: Dictionary) -> void:
	_update_status("奖励已领取: %s - %s" % [quest_id, QuestData.get_reward_text(rewards)])


func _on_daily_quests_refreshed() -> void:
	_update_status("日常任务已刷新")


func _on_weekly_quests_refreshed() -> void:
	_update_status("周常任务已刷新")
