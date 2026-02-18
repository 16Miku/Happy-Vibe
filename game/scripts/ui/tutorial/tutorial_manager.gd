## tutorial_manager.gd
## 新手引导管理器 - 管理新手引导流程
## 作为 AutoLoad 单例运行
extends Node

# ==================== 信号定义 ====================

## 引导开始
signal tutorial_started()

## 引导步骤变化
signal tutorial_step_changed(step_index: int, step_data: Dictionary)

## 引导完成
signal tutorial_completed()

## 引导跳过
signal tutorial_skipped()

# ==================== 常量 ====================

const SAVE_PATH := "user://tutorial_done.save"

# ==================== 引导步骤定义 ====================

var tutorial_steps: Array[Dictionary] = [
	{
		"id": "welcome",
		"title": "欢迎来到 Happy Vibe！",
		"content": "这是一款将 Vibe-Coding 体验游戏化的养成游戏。\n\n在这里，你的编码活动会转化为游戏内的能量，帮助你的农场成长！",
		"highlight_target": "",
		"position": "center"
	},
	{
		"id": "energy_system",
		"title": "能量系统",
		"content": "当你使用 Claude Code 进行编码时，VibeHub 会记录你的活动并转化为能量。\n\n能量是游戏的核心资源，用于种植、建造和升级。",
		"highlight_target": "TopBar/EnergyPanel",
		"position": "below"
	},
	{
		"id": "flow_state",
		"title": "心流状态",
		"content": "当你专注编码一段时间后，会进入「心流状态」。\n\n心流状态下获得的能量会有额外加成！",
		"highlight_target": "FlowIndicator",
		"position": "below"
	},
	{
		"id": "planting",
		"title": "种植作物",
		"content": "点击农场中的空地块，选择种子进行种植。\n\n不同作物需要不同的生长时间和能量。",
		"highlight_target": "",
		"position": "center"
	},
	{
		"id": "harvesting",
		"title": "收获作物",
		"content": "作物成熟后会显示收获图标。\n\n点击成熟的作物即可收获，获得金币和经验！",
		"highlight_target": "",
		"position": "center"
	},
	{
		"id": "achievements",
		"title": "成就系统",
		"content": "完成各种目标可以解锁成就，获得丰厚奖励。\n\n点击底部的「成就」按钮查看所有成就。",
		"highlight_target": "BottomBar/AchievementButton",
		"position": "above"
	},
	{
		"id": "complete",
		"title": "准备就绪！",
		"content": "现在你已经了解了基本玩法。\n\n开始你的 Vibe-Coding 之旅吧！\n\n提示：可以在设置中重新查看引导。",
		"highlight_target": "",
		"position": "center"
	}
]

# ==================== 状态变量 ====================

## 是否已完成引导
var is_tutorial_completed: bool = false

## 当前引导步骤索引
var current_step_index: int = -1

## 是否正在显示引导
var is_showing_tutorial: bool = false

## 引导 UI 实例
var tutorial_ui: Control = null

## HUD 引用（用于高亮）
var hud_reference: Control = null


func _ready() -> void:
	_load_tutorial_state()


# ==================== 公共方法 ====================

## 检查是否需要显示引导
func should_show_tutorial() -> bool:
	return not is_tutorial_completed


## 开始引导
func start_tutorial(hud: Control = null) -> void:
	if is_showing_tutorial:
		return

	hud_reference = hud
	is_showing_tutorial = true
	current_step_index = 0

	_create_tutorial_ui()
	_show_current_step()

	tutorial_started.emit()


## 下一步
func next_step() -> void:
	if not is_showing_tutorial:
		return

	current_step_index += 1

	if current_step_index >= tutorial_steps.size():
		_complete_tutorial()
	else:
		_show_current_step()


## 上一步
func previous_step() -> void:
	if not is_showing_tutorial or current_step_index <= 0:
		return

	current_step_index -= 1
	_show_current_step()


## 跳过引导
func skip_tutorial() -> void:
	if not is_showing_tutorial:
		return

	_cleanup_tutorial_ui()
	is_showing_tutorial = false
	is_tutorial_completed = true
	_save_tutorial_state()

	tutorial_skipped.emit()


## 重置引导（用于设置中的"重新查看引导"）
func reset_tutorial() -> void:
	is_tutorial_completed = false
	current_step_index = -1
	_save_tutorial_state()


## 获取当前步骤数据
func get_current_step() -> Dictionary:
	if current_step_index >= 0 and current_step_index < tutorial_steps.size():
		return tutorial_steps[current_step_index]
	return {}


## 获取总步骤数
func get_total_steps() -> int:
	return tutorial_steps.size()


## 获取当前步骤索引（从1开始，用于显示）
func get_current_step_number() -> int:
	return current_step_index + 1


# ==================== 私有方法 ====================

## 创建引导 UI
func _create_tutorial_ui() -> void:
	if tutorial_ui and is_instance_valid(tutorial_ui):
		return

	var TutorialDialogScript = load("res://scripts/ui/tutorial/tutorial_dialog.gd")
	if TutorialDialogScript:
		tutorial_ui = TutorialDialogScript.new()
		tutorial_ui.name = "TutorialDialog"

		# 连接信号
		tutorial_ui.next_pressed.connect(next_step)
		tutorial_ui.skip_pressed.connect(skip_tutorial)
		tutorial_ui.previous_pressed.connect(previous_step)

		# 添加到场景
		var root = get_tree().current_scene
		if root:
			root.add_child(tutorial_ui)
		else:
			get_tree().root.add_child(tutorial_ui)
	else:
		push_error("[TutorialManager] 无法加载 TutorialDialog 脚本")


## 显示当前步骤
func _show_current_step() -> void:
	if not tutorial_ui or not is_instance_valid(tutorial_ui):
		return

	var step_data := get_current_step()
	if step_data.is_empty():
		return

	# 更新 UI
	tutorial_ui.show_step(
		step_data,
		current_step_index,
		tutorial_steps.size(),
		hud_reference
	)

	tutorial_step_changed.emit(current_step_index, step_data)


## 完成引导
func _complete_tutorial() -> void:
	_cleanup_tutorial_ui()
	is_showing_tutorial = false
	is_tutorial_completed = true
	_save_tutorial_state()

	tutorial_completed.emit()

	# 显示完成通知
	if EventBus:
		EventBus.notify_success("新手引导完成！")


## 清理引导 UI
func _cleanup_tutorial_ui() -> void:
	if tutorial_ui and is_instance_valid(tutorial_ui):
		tutorial_ui.queue_free()
		tutorial_ui = null
	hud_reference = null


## 加载引导状态
func _load_tutorial_state() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
		if file:
			var data := file.get_var()
			if data is Dictionary:
				is_tutorial_completed = data.get("completed", false)
			file.close()


## 保存引导状态
func _save_tutorial_state() -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		var data := {
			"completed": is_tutorial_completed,
			"timestamp": Time.get_unix_time_from_system()
		}
		file.store_var(data)
		file.close()
