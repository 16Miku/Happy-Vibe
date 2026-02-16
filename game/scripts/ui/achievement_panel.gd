## achievement_panel.gd
## 成就面板脚本
extends Control

## 成就分类枚举
enum AchievementCategory {
	ALL,
	CODING,
	FARM,
	SOCIAL,
	COLLECTION,
	PVP
}

## 当前选择的分类
var current_category: AchievementCategory = AchievementCategory.ALL

## 成就项场景
var achievement_item_scene: PackedScene = null

@onready var close_button: Button = $Header/CloseButton
@onready var category_tabs: TabContainer = $Content/CategoryTabs
@onready var all_tab: VBoxContainer = $Content/CategoryTabs/All
@onready var coding_tab: VBoxContainer = $Content/CategoryTabs/Coding
@onready var farm_tab: VBoxContainer = $Content/CategoryTabs/Farm
@onready var social_tab: VBoxContainer = $Content/CategoryTabs/Social
@onready var collection_tab: VBoxContainer = $Content/CategoryTabs/Collection
@onready var pvp_tab: VBoxContainer = $Content/CategoryTabs/PVP
@onready var stats_label: Label = $Header/StatsLabel

func _ready() -> void:
	_setup_buttons()
	_load_achievement_item_scene()
	_refresh_achievements()

	if DataManager:
		DataManager.achievements_updated.connect(_on_achievements_updated)


func _setup_buttons() -> void:
	"""设置按钮连接"""
	if close_button:
		close_button.pressed.connect(_on_close_pressed)


func _load_achievement_item_scene() -> void:
	"""加载成就项场景"""
	achievement_item_scene = load("res://scenes/ui/achievement/achievement_item.tscn")
	if not achievement_item_scene:
		push_warning("[AchievementPanel] 无法加载成就项场景")


## 刷新成就列表
func _refresh_achievements() -> void:
	"""从 DataManager 获取并显示成就数据"""
	_clear_all_tabs()

	if not DataManager:
		return

	var achievements = DataManager.get_achievements()
	var progress = DataManager.get_achievement_progress()

	var completed_count := 0
	var total_count := achievements.size()

	for achievement_id in achievements:
		var achievement = achievements[achievement_id]
		var player_progress = progress.get(achievement_id)

		if player_progress and player_progress.completed:
			completed_count += 1

		# 添加到对应的标签页
		_add_achievement_to_tab(achievement, player_progress)

	# 更新统计
	if stats_label:
		stats_label.text = "已完成: %d / %d" % [completed_count, total_count]


## 清空所有标签页
func _clear_all_tabs() -> void:
	"""清空所有标签页的内容"""
	if all_tab:
		for child in all_tab.get_children():
			child.queue_free()
	if coding_tab:
		for child in coding_tab.get_children():
			child.queue_free()
	if farm_tab:
		for child in farm_tab.get_children():
			child.queue_free()
	if social_tab:
		for child in social_tab.get_children():
			child.queue_free()
	if collection_tab:
		for child in collection_tab.get_children():
			child.queue_free()
	if pvp_tab:
		for child in pvp_tab.get_children():
			child.queue_free()


## 添加成就到标签页
func _add_achievement_to_tab(achievement: DataManager.AchievementDefinition, progress: DataManager.AchievementProgress) -> void:
	"""根据成就分类添加到对应标签页"""
	if not achievement_item_scene:
		return

	var item = achievement_item_scene.instantiate()
	item.set_achievement_data(achievement, progress)

	# 添加到"全部"标签页
	if all_tab:
		all_tab.add_child(item)

	# 根据分类添加到对应标签页
	match achievement.category:
		"coding":
			if coding_tab:
				coding_tab.add_child(item.duplicate())
		"farm":
			if farm_tab:
				farm_tab.add_child(item.duplicate())
		"social":
			if social_tab:
				social_tab.add_child(item.duplicate())
		"collection":
			if collection_tab:
				collection_tab.add_child(item.duplicate())
		"pvp":
			if pvp_tab:
				pvp_tab.add_child(item.duplicate())


## 成就数据更新回调
func _on_achievements_updated() -> void:
	"""当成就数据更新时刷新"""
	_refresh_achievements()


## 从服务器同步成就数据
func sync_from_server() -> void:
	"""从服务器同步成就数据"""
	if DataManager:
		DataManager.sync_achievements(func(success: bool, data: Dictionary):
			if success:
				print("[AchievementPanel] 成就数据同步成功")
			else:
				push_error("[AchievementPanel] 成就数据同步失败")
		)


## 关闭按钮点击
func _on_close_pressed() -> void:
	"""关闭面板"""
	hide()


## 打开面板
func open() -> void:
	"""打开面板并刷新数据"""
	show()
	sync_from_server()
