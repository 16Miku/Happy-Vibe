## modal_manager.gd
## 弹窗管理器 - 管理所有弹窗和对话框
## 作为 AutoLoad 单例运行
extends Node

## 当前显示的弹窗
var current_modal: Control = null

## 弹窗队列
var modal_queue: Array[Dictionary] = []

## 是否正在显示弹窗
var is_showing_modal: bool = false

# ==================== 信号定义 ====================

## 弹窗显示
signal modal_shown(modal_type: String)

## 弹窗关闭
signal modal_closed(modal_type: String, result: Variant)

# ==================== 弹窗预制体 ====================

var notification_scene: PackedScene = null
var confirm_dialog_scene: PackedScene = null
var reward_popup_scene: PackedScene = null

func _ready() -> void:
	_load_scenes()

	# 连接 EventBus 信号
	if EventBus:
		EventBus.show_notification.connect(_on_show_notification)
		EventBus.show_popup.connect(_on_show_popup)
		EventBus.show_reward_popup.connect(_on_show_reward_popup)
		EventBus.show_confirm_dialog.connect(_on_show_confirm_dialog)
		EventBus.open_panel.connect(_on_open_panel)
		EventBus.close_panel.connect(_on_close_panel)


func _load_scenes() -> void:
	"""加载弹窗场景"""
	notification_scene = load("res://scenes/ui/modals/notification_modal.tscn")
	confirm_dialog_scene = load("res://scenes/ui/modals/confirm_dialog.tscn")
	reward_popup_scene = load("res://scenes/ui/modals/reward_popup.tscn")


# ==================== 通知弹窗 ====================

## 显示通知
## message: 通知内容
## type: 通知类型 (info, success, warning, error)
## duration: 持续时间（秒），0 表示不自动关闭
func show_notification(message: String, type: String = "info", duration: float = 3.0) -> void:
	var modal_data := {
		"type": "notification",
		"message": message,
		"notification_type": type,
		"duration": duration
	}

	_add_modal_to_queue(modal_data)


## 处理通知弹窗
func _process_notification(data: Dictionary) -> void:
	if not notification_scene:
		push_error("[ModalManager] 通知场景未加载")
		return

	var notification = notification_scene.instantiate()
	notification.set_message(data["message"])
	notification.set_type(data["notification_type"])

	# 添加到当前场景
	_get_current_scene_root().add_child(notification)

	current_modal = notification
	is_showing_modal = true
	modal_shown.emit("notification")

	# 如果设置了持续时间，自动关闭
	var duration := data.get("duration", 3.0)
	if duration > 0:
		var timer := get_tree().create_timer(duration)
		timer.timeout.connect(func():
			if is_instance_valid(notification):
				_close_current_modal()
		)


# ==================== 确认对话框 ====================

## 显示确认对话框
## title: 标题
## message: 内容
## callback: 确认回调函数
func show_confirm_dialog(title: String, message: String, callback: Callable) -> void:
	var modal_data := {
		"type": "confirm",
		"title": title,
		"message": message,
		"callback": callback
	}

	_add_modal_to_queue(modal_data)


## 处理确认对话框
func _process_confirm_dialog(data: Dictionary) -> void:
	if not confirm_dialog_scene:
		push_error("[ModalManager] 确认对话框场景未加载")
		return

	var dialog = confirm_dialog_scene.instantiate()
	dialog.set_title(data["title"])
	dialog.set_message(data["message"])

	# 连接确认和取消信号
	dialog.confirmed.connect(func():
		var callback = data.get("callback")
		if callback.is_valid():
			callback.call()
		_close_current_modal(true)
	)

	dialog.canceled.connect(func():
		_close_current_modal(false)
	)

	_get_current_scene_root().add_child(dialog)

	current_modal = dialog
	is_showing_modal = true
	modal_shown.emit("confirm")


# ==================== 奖励弹窗 ====================

## 显示奖励弹窗
## rewards: 奖励数据 {"gold": 100, "exp": 50, ...}
func show_reward_popup(rewards: Dictionary) -> void:
	var modal_data := {
		"type": "reward",
		"rewards": rewards
	}

	_add_modal_to_queue(modal_data)


## 处理奖励弹窗
func _process_reward_popup(data: Dictionary) -> void:
	if not reward_popup_scene:
		push_error("[ModalManager] 奖励弹窗场景未加载")
		return

	var popup = reward_popup_scene.instantiate()
	popup.set_rewards(data["rewards"])

	# 连接关闭信号
	popup.popup_closed.connect(func():
		_close_current_modal()
	)

	_get_current_scene_root().add_child(popup)

	current_modal = popup
	is_showing_modal = true
	modal_shown.emit("reward")


# ==================== 弹窗队列管理 ====================

## 添加弹窗到队列
func _add_modal_to_queue(data: Dictionary) -> void:
	modal_queue.append(data)

	if not is_showing_modal:
		_process_next_modal()


## 处理队列中的下一个弹窗
func _process_next_modal() -> void:
	if modal_queue.is_empty():
		return

	var data = modal_queue.pop_front()

	match data["type"]:
		"notification":
			_process_notification(data)
		"confirm":
			_process_confirm_dialog(data)
		"reward":
			_process_reward_popup(data)
		_:
			push_warning("[ModalManager] 未知弹窗类型: %s" % data["type"])


## 关闭当前弹窗
func _close_current_modal(result: Variant = null) -> void:
	if current_modal and is_instance_valid(current_modal):
		var modal_type := current_meta.get("type", "unknown") if current_meta else "unknown"

		current_modal.queue_free()
		current_modal = null
		is_showing_modal = false

		modal_closed.emit(modal_type, result)

		# 处理队列中的下一个弹窗
		_process_next_modal()


var current_meta: Dictionary = {}

## 强制关闭所有弹窗
func close_all_modals() -> void:
	if current_modal and is_instance_valid(current_modal):
		current_modal.queue_free()
		current_modal = null

	is_showing_modal = false
	modal_queue.clear()


# ==================== EventBus 回调 ====================

func _on_show_notification(message: String, type: String) -> void:
	show_notification(message, type)


func _on_show_popup(title: String, content: String) -> void:
	# 使用通用通知显示
	show_notification(content, "info")


func _on_show_reward_popup(rewards: Dictionary) -> void:
	show_reward_popup(rewards)


func _on_show_confirm_dialog(title: String, message: String, callback: Callable) -> void:
	show_confirm_dialog(title, message, callback)


func _on_open_panel(panel_name: String) -> void:
	# 通过 HUD 打开对应面板
	var hud = _get_hud()
	if hud and hud.has_method("open_panel_by_name"):
		hud.open_panel_by_name(panel_name)


func _on_close_panel(panel_name: String) -> void:
	# 通过 HUD 关闭对应面板
	var hud = _get_hud()
	if hud and hud.has_method("close_panel_by_name"):
		hud.close_panel_by_name(panel_name)


# ==================== 工具方法 ====================

## 获取当前场景根节点
func _get_current_scene_root() -> Node:
	var root = get_tree().current_scene
	if root:
		return root
	return get_tree().root


## 获取 HUD 节点
func _get_hud() -> Control:
	var root = _get_current_scene_root()
	# 查找 HUD 节点
	return root.find_child("HUD", true, false)


## 是否正在显示弹窗
func has_active_modal() -> bool:
	return is_showing_modal and is_instance_valid(current_modal)
