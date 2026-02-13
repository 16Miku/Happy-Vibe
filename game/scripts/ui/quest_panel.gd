## quest_panel.gd
## 任务面板 UI - 显示日常、周常、成就任务
extends Control

# 节点引用
@onready var tab_container: TabContainer = $MarginContainer/VBoxContainer/TabContainer
@onready var daily_quest_list: VBoxContainer = $"MarginContainer/VBoxContainer/TabContainer/日常任务/DailyQuestList"
@onready var weekly_quest_list: VBoxContainer = $"MarginContainer/VBoxContainer/TabContainer/周常任务/WeeklyQuestList"
@onready var achievement_list: VBoxContainer = $"MarginContainer/VBoxContainer/TabContainer/成就/AchievementList"
@onready var close_button: Button = $MarginContainer/VBoxContainer/Header/CloseButton
@onready var daily_refresh_label: Label = $MarginContainer/VBoxContainer/RefreshInfo/DailyRefreshLabel
@onready var weekly_refresh_label: Label = $MarginContainer/VBoxContainer/RefreshInfo/WeeklyRefreshLabel

# 任务项场景
var quest_item_scene: PackedScene = preload("res://scenes/ui/quest/quest_item.tscn")

# 刷新计时器
var refresh_timer: Timer


func _ready() -> void:
	_setup_ui()
	_connect_signals()
	_load_quests()
	_start_refresh_timer()


func _setup_ui() -> void:
	close_button.pressed.connect(_on_close_pressed)
	tab_container.tab_changed.connect(_on_tab_changed)


func _connect_signals() -> void:
	if QuestManager:
		QuestManager.quest_progress_updated.connect(_on_quest_progress_updated)
		QuestManager.quest_completed.connect(_on_quest_completed)
		QuestManager.quest_reward_claimed.connect(_on_quest_reward_claimed)
		QuestManager.daily_quests_refreshed.connect(_on_daily_quests_refreshed)
		QuestManager.weekly_quests_refreshed.connect(_on_weekly_quests_refreshed)


func _load_quests() -> void:
	_load_daily_quests()
	_load_weekly_quests()
	_load_achievement_quests()


func _start_refresh_timer() -> void:
	refresh_timer = Timer.new()
	refresh_timer.wait_time = 1.0
	refresh_timer.autostart = true
	refresh_timer.timeout.connect(_update_refresh_labels)
	add_child(refresh_timer)
	_update_refresh_labels()


## 加载日常任务
func _load_daily_quests() -> void:
	_clear_list(daily_quest_list)

	if not QuestManager:
		return

	var quests: Array = QuestManager.get_daily_quests()
	for quest in quests:
		_add_quest_item(daily_quest_list, quest)


## 加载周常任务
func _load_weekly_quests() -> void:
	_clear_list(weekly_quest_list)

	if not QuestManager:
		return

	var quests: Array = QuestManager.get_weekly_quests()
	for quest in quests:
		_add_quest_item(weekly_quest_list, quest)


## 加载成就任务
func _load_achievement_quests() -> void:
	_clear_list(achievement_list)

	if not QuestManager:
		return

	var quests: Array = QuestManager.get_achievement_quests()
	for quest in quests:
		_add_quest_item(achievement_list, quest)


## 清空列表
func _clear_list(list: VBoxContainer) -> void:
	for child in list.get_children():
		child.queue_free()


## 添加任务项
func _add_quest_item(list: VBoxContainer, quest: Dictionary) -> void:
	var item: Control = quest_item_scene.instantiate()
	item.setup(quest)
	item.claim_pressed.connect(_on_claim_pressed.bind(quest.get("id", "")))
	list.add_child(item)


## 更新刷新时间标签
func _update_refresh_labels() -> void:
	if not QuestManager:
		return

	var daily_remaining: int = QuestManager.get_daily_refresh_remaining()
	var weekly_remaining: int = QuestManager.get_weekly_refresh_remaining()

	daily_refresh_label.text = "日常刷新: " + _format_time(daily_remaining)
	weekly_refresh_label.text = "周常刷新: " + _format_time(weekly_remaining)


## 格式化时间
func _format_time(seconds: int) -> String:
	var hours: int = seconds / 3600
	var minutes: int = (seconds % 3600) / 60
	var secs: int = seconds % 60

	if hours > 24:
		var days: int = hours / 24
		hours = hours % 24
		return "%d天 %02d:%02d:%02d" % [days, hours, minutes, secs]

	return "%02d:%02d:%02d" % [hours, minutes, secs]


## 关闭按钮点击
func _on_close_pressed() -> void:
	hide()
	if EventBus:
		EventBus.close_panel.emit("quest")


## 标签页切换
func _on_tab_changed(tab: int) -> void:
	match tab:
		0:
			_load_daily_quests()
		1:
			_load_weekly_quests()
		2:
			_load_achievement_quests()


## 领取奖励按钮点击
func _on_claim_pressed(quest_id: String) -> void:
	if QuestManager:
		QuestManager.claim_quest_reward(quest_id)


## 任务进度更新
func _on_quest_progress_updated(quest_id: String, _current: int, _target: int) -> void:
	_refresh_quest_item(quest_id)


## 任务完成
func _on_quest_completed(quest_id: String) -> void:
	_refresh_quest_item(quest_id)


## 任务奖励领取
func _on_quest_reward_claimed(quest_id: String, _rewards: Dictionary) -> void:
	_refresh_quest_item(quest_id)


## 日常任务刷新
func _on_daily_quests_refreshed() -> void:
	if tab_container.current_tab == 0:
		_load_daily_quests()


## 周常任务刷新
func _on_weekly_quests_refreshed() -> void:
	if tab_container.current_tab == 1:
		_load_weekly_quests()


## 刷新单个任务项
func _refresh_quest_item(quest_id: String) -> void:
	# 根据当前标签页刷新对应列表
	match tab_container.current_tab:
		0:
			_load_daily_quests()
		1:
			_load_weekly_quests()
		2:
			_load_achievement_quests()


## 显示面板
func show_panel() -> void:
	_load_quests()
	show()


## 隐藏面板
func hide_panel() -> void:
	hide()
