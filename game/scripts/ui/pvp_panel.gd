## pvp_panel.gd
## PVP 竞技场面板脚本
extends Control

## 面板状态
enum PanelState {
	INFO,      # 我的信息
	LEADERBOARD, # 排行榜
	MATCHMAKING, # 匹配中
	HISTORY    # 历史记录
}

## 当前状态
var current_state: PanelState = PanelState.INFO

## PVP 段位配置
var tier_config := {
	"bronze": {"name": "青铜", "icon": "🥉", "color": Color(0.72, 0.45, 0.2)},
	"silver": {"name": "白银", "icon": "🥈", "color": Color(0.75, 0.75, 0.75)},
	"gold": {"name": "黄金", "icon": "🥇", "color": Color(1.0, 0.84, 0.0)},
	"platinum": {"name": "铂金", "icon": "💎", "color": Color(0.82, 0.89, 0.93)},
	"diamond": {"name": "钻石", "icon": "💠", "color": Color(0.5, 0.8, 1.0)},
	"master": {"name": "大师", "icon": "👑", "color": Color(1.0, 0.5, 0.0)},
	"challenger": {"name": "挑战者", "icon": "🔥", "color": Color(1.0, 0.2, 0.0)}
}

## 排行榜条目场景
var entry_item_scene: PackedScene = null

## 当前匹配 ID
var current_match_id: String = ""

@onready var close_button: Button = $Header/CloseButton

## 信息面板节点
@onready var info_panel: VBoxContainer = $Content/InfoPanel
@onready var rating_label: Label = $Content/InfoPanel/StatsContainer/RatingLabel
@onready var tier_label: Label = $Content/InfoPanel/StatsContainer/TierLabel
@onready var wins_label: Label = $Content/InfoPanel/StatsContainer/WinsLabel
@onready var losses_label: Label = $Content/InfoPanel/StatsContainer/LossesLabel
@onready var streak_label: Label = $Content/InfoPanel/StatsContainer/StreakLabel
@onready var max_rating_label: Label = $Content/InfoPanel/StatsContainer/MaxRatingLabel
@onready var match_button: Button = $Content/InfoPanel/MatchButton

## 排行榜面板节点
@onready var leaderboard_panel: VBoxContainer = $Content/LeaderboardPanel
@onready var leaderboard_list: VBoxContainer = $Content/LeaderboardPanel/ScrollContainer/LeaderboardList

## 匹配面板节点
@onready var matchmaking_panel: VBoxContainer = $Content/MatchmakingPanel
@onready var matchmaking_label: Label = $Content/MatchmakingPanel/MatchmakingLabel
@onready var cancel_match_button: Button = $Content/MatchmakingPanel/CancelButton

## 历史记录面板节点
@onready var history_panel: VBoxContainer = $Content/HistoryPanel
@onready var history_list: VBoxContainer = $Content/HistoryPanel/ScrollContainer/HistoryList

## 导航按钮
@onready var info_tab_button: Button = $Content/TabContainer/InfoTab
@onready var leaderboard_tab_button: Button = $Content/TabContainer/LeaderboardTab
@onready var history_tab_button: Button = $Content/TabContainer/HistoryTab

func _ready() -> void:
	_setup_buttons()
	_load_entry_item_scene()
	_show_info()

	if DataManager:
		DataManager.pvp_data_updated.connect(_on_pvp_data_updated)


func _setup_buttons() -> void:
	"""设置按钮连接"""
	if close_button:
		close_button.pressed.connect(_on_close_pressed)

	if match_button:
		match_button.pressed.connect(_on_start_matchmaking)

	if cancel_match_button:
		cancel_match_button.pressed.connect(_on_cancel_matchmaking)

	if info_tab_button:
		info_tab_button.pressed.connect(func(): _show_panel(PanelState.INFO))
	if leaderboard_tab_button:
		leaderboard_tab_button.pressed.connect(func(): _show_panel(PanelState.LEADERBOARD))
	if history_tab_button:
		history_tab_button.pressed.connect(func(): _show_panel(PanelState.HISTORY))


func _load_entry_item_scene() -> void:
	"""加载排行榜条目场景"""
	entry_item_scene = load("res://scenes/ui/pvp/pvp_entry.tscn")


## 显示面板
func _show_panel(state: PanelState) -> void:
	"""切换显示的面板"""
	current_state = state

	# 隐藏所有面板
	if info_panel:
		info_panel.visible = false
	if leaderboard_panel:
		leaderboard_panel.visible = false
	if matchmaking_panel:
		matchmaking_panel.visible = false
	if history_panel:
		history_panel.visible = false

	# 显示当前面板
	match state:
		PanelState.INFO:
			_show_info()
		PanelState.LEADERBOARD:
			_show_leaderboard()
		PanelState.MATCHMAKING:
			_show_matchmaking()
		PanelState.HISTORY:
			_show_history()

	# 更新标签按钮状态
	_update_tab_buttons()


## 显示信息面板
func _show_info() -> void:
	"""显示我的 PVP 信息"""
	if info_panel:
		info_panel.visible = true

	_update_info_display()


## 更新信息显示
func _update_info_display() -> void:
	"""更新 PVP 信息显示"""
	if not DataManager:
		return

	var pvp_info = DataManager.get_pvp_info()
	if not pvp_info:
		return

	if rating_label:
		rating_label.text = "积分: %d" % pvp_info.rating

	if tier_label and tier_config.has(pvp_info.tier):
		var config = tier_config[pvp_info.tier]
		tier_label.text = "%s %s" % [config["icon"], config["name"]]
		tier_label.modulate = config["color"]

	if wins_label:
		wins_label.text = "胜场: %d" % pvp_info.wins

	if losses_label:
		losses_label.text = "败场: %d" % pvp_info.losses

	if streak_label:
		var streak_text := "连胜: %d" % pvp_info.current_streak if pvp_info.current_streak > 0 else "连败: %d" % absi(pvp_info.current_streak)
		streak_label.text = streak_text
		streak_label.modulate = Color(0.2, 0.8, 0.2) if pvp_info.current_streak > 0 else Color(0.8, 0.2, 0.2)

	if max_rating_label:
		max_rating_label.text = "最高积分: %d" % pvp_info.max_rating


## 显示排行榜面板
func _show_leaderboard() -> void:
	"""显示 PVP 排行榜"""
	if leaderboard_panel:
		leaderboard_panel.visible = true

	_display_leaderboard()


## 显示排行榜数据
func _display_leaderboard() -> void:
	"""显示 PVP 排行榜数据"""
	if not leaderboard_list or not DataManager:
		return

	# 清空现有列表
	for child in leaderboard_list.get_children():
		child.queue_free()

	var leaderboard = DataManager.get_pvp_leaderboard()
	for entry in leaderboard:
		if not entry_item_scene:
			break

		var item = entry_item_scene.instantiate()
		item.set_entry_data(entry)
		leaderboard_list.add_child(item)


## 显示匹配面板
func _show_matchmaking() -> void:
	"""显示匹配中面板"""
	if matchmaking_panel:
		matchmaking_panel.visible = true


## 显示历史记录面板
func _show_history() -> void:
	"""显示历史记录面板"""
	if history_panel:
		history_panel.visible = true

	_display_history()


## 显示历史记录
func _display_history() -> void:
	"""显示历史记录数据"""
	if not history_list or not DataManager:
		return

	# 清空现有列表
	for child in history_list.get_children():
		child.queue_free()

	var history = DataManager.pvp_history
	for record in history:
		if not entry_item_scene:
			break

		var item = entry_item_scene.instantiate()
		item.set_history_data(record)
		history_list.add_child(item)


## 开始匹配
func _on_start_matchmaking() -> void:
	"""开始 PVP 匹配"""
	if not DataManager:
		return

	DataManager.start_pvp_matchmaking(func(success: bool, data: Dictionary):
		if success:
			current_match_id = data.get("match_id", "")
			_show_panel(PanelState.MATCHMAKING)
			_start_matchmaking_animation()
		else:
			EventBus.notify_error.call("匹配失败，请稍后重试")
	)


## 取消匹配
func _on_cancel_matchmaking() -> void:
	"""取消 PVP 匹配"""
	_show_panel(PanelState.INFO)
	current_match_id = ""


## 匹配动画
func _start_matchmaking_animation() -> void:
	"""开始匹配动画"""
	if not matchmaking_label:
		return

	var dots := 0
	var timer := Timer.new()
	timer.wait_time = 0.5
	timer.timeout.connect(func():
		dots = (dots + 1) % 4
		matchmaking_label.text = "正在匹配对手" + ".".repeat(dots)
	)
	add_child(timer)
	timer.start()


## 更新标签按钮状态
func _update_tab_buttons() -> void:
	"""更新标签按钮状态"""
	if info_tab_button:
		info_tab_button.button_pressed = (current_state == PanelState.INFO)
	if leaderboard_tab_button:
		leaderboard_tab_button.button_pressed = (current_state == PanelState.LEADERBOARD)
	if history_tab_button:
		history_tab_button.button_pressed = (current_state == PanelState.HISTORY)


## PVP 数据更新回调
func _on_pvp_data_updated() -> void:
	"""当 PVP 数据更新时刷新"""
	if current_state == PanelState.INFO:
		_update_info_display()
	elif current_state == PanelState.LEADERBOARD:
		_display_leaderboard()


## 关闭按钮点击
func _on_close_pressed() -> void:
	"""关闭面板"""
	hide()


## 打开面板
func open() -> void:
	"""打开面板并刷新数据"""
	show()
	if DataManager:
		DataManager.sync_pvp()
