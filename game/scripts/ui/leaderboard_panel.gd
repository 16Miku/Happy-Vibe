## leaderboard_panel.gd
## 排行榜面板脚本
extends Control

## 排行榜类型
enum LeaderboardType {
	LEVEL,      # 等级排行
	ENERGY,     # 能量排行
	GOLD,       # 金币排行
	ACHIEVEMENT,# 成就排行
	FARM        # 农场排行
}

## 当前排行榜类型
var current_type: LeaderboardType = LeaderboardType.LEVEL

## 排行榜类型配置
var type_config := {
	LeaderboardType.LEVEL: {"name": "等级排行", "icon": "⭐", "api_type": "level"},
	LeaderboardType.ENERGY: {"name": "能量排行", "icon": "💜", "api_type": "energy"},
	LeaderboardType.GOLD: {"name": "财富排行", "icon": "🪙", "api_type": "gold"},
	LeaderboardType.ACHIEVEMENT: {"name": "成就排行", "icon": "🏆", "api_type": "achievement"},
	LeaderboardType.FARM: {"name": "农场排行", "icon": "🌾", "api_type": "farm"}
}

## 排行榜条目场景
var entry_item_scene: PackedScene = null

@onready var close_button: Button = $Header/CloseButton
@onready var title_label: Label = $Header/TitleLabel
@onready var my_rank_label: Label = $Header/MyRankLabel

## 类型切换按钮
@onready var level_button: Button = $Content/TypeButtons/LevelButton
@onready var energy_button: Button = $Content/TypeButtons/EnergyButton
@onready var gold_button: Button = $Content/TypeButtons/GoldButton
@onready var achievement_button: Button = $Content/TypeButtons/AchievementButton
@onready var farm_button: Button = $Content/TypeButtons/FarmButton

@onready var entry_list: VBoxContainer = $Content/ScrollContainer/EntryList

func _ready() -> void:
	_setup_buttons()
	_load_entry_item_scene()
	_switch_leaderboard(LeaderboardType.LEVEL)

	if DataManager:
		DataManager.leaderboard_updated.connect(_on_leaderboard_updated)


func _setup_buttons() -> void:
	"""设置按钮连接"""
	if close_button:
		close_button.pressed.connect(_on_close_pressed)

	if level_button:
		level_button.pressed.connect(func(): _switch_leaderboard(LeaderboardType.LEVEL))
	if energy_button:
		energy_button.pressed.connect(func(): _switch_leaderboard(LeaderboardType.ENERGY))
	if gold_button:
		gold_button.pressed.connect(func(): _switch_leaderboard(LeaderboardType.GOLD))
	if achievement_button:
		achievement_button.pressed.connect(func(): _switch_leaderboard(LeaderboardType.ACHIEVEMENT))
	if farm_button:
		farm_button.pressed.connect(func(): _switch_leaderboard(LeaderboardType.FARM))


func _load_entry_item_scene() -> void:
	"""加载排行榜条目场景"""
	entry_item_scene = load("res://scenes/ui/leaderboard/leaderboard_entry.tscn")


## 切换排行榜
func _switch_leaderboard(type: LeaderboardType) -> void:
	"""切换排行榜类型"""
	current_type = type

	# 更新标题
	if title_label and type_config.has(type):
		var config = type_config[type]
		title_label.text = "%s %s" % [config["icon"], config["name"]]

	# 更新按钮状态
	_update_button_states()

	# 加载数据
	_load_leaderboard_data()


## 更新按钮状态
func _update_button_states() -> void:
	"""更新按钮选中状态"""
	if level_button:
		level_button.button_pressed = (current_type == LeaderboardType.LEVEL)
	if energy_button:
		energy_button.button_pressed = (current_type == LeaderboardType.ENERGY)
	if gold_button:
		gold_button.button_pressed = (current_type == LeaderboardType.GOLD)
	if achievement_button:
		achievement_button.button_pressed = (current_type == LeaderboardType.ACHIEVEMENT)
	if farm_button:
		farm_button.button_pressed = (current_type == LeaderboardType.FARM)


## 加载排行榜数据
func _load_leaderboard_data() -> void:
	"""从 DataManager 获取排行榜数据"""
	if not DataManager or not type_config.has(current_type):
		return

	var api_type = type_config[current_type]["api_type"]
	DataManager.sync_leaderboard(api_type, 1, func(success: bool, data: Dictionary):
		if success:
			_display_leaderboard()
	)


## 显示排行榜
func _display_leaderboard() -> void:
	"""显示排行榜数据"""
	if not entry_list or not DataManager:
		return

	# 清空现有列表
	for child in entry_list.get_children():
		child.queue_free()

	var leaderboard = DataManager.get_leaderboard(type_config[current_type]["api_type"])
	if not leaderboard:
		return

	# 添加条目
	for entry_dict in leaderboard.entries:
		if not entry_item_scene:
			break

		var item = entry_item_scene.instantiate()
		item.set_entry_data(entry_dict)
		entry_list.add_child(item)

	# 更新我的排名
	if my_rank_label:
		var my_rank = DataManager.get_my_rank(type_config[current_type]["api_type"])
		my_rank_label.text = "我的排名: #%d" % my_rank if my_rank > 0 else "我的排名: 未上榜"


## 排行榜数据更新回调
func _on_leaderboard_updated(lb_type: String) -> void:
	"""当排行榜数据更新时刷新"""
	var current_api_type = type_config[current_type]["api_type"]
	if lb_type == current_api_type:
		_display_leaderboard()


## 关闭按钮点击
func _on_close_pressed() -> void:
	"""关闭面板"""
	hide()


## 打开面板
func open() -> void:
	"""打开面板并刷新数据"""
	show()
	_load_leaderboard_data()
