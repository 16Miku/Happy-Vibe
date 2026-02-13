## 头像选择器
## 弹窗界面，允许玩家浏览和选择头像
class_name AvatarSelector
extends Control

## 信号
signal avatar_selected(avatar_id: String)
signal closed()

## 常量
const GRID_COLUMNS := 4
const AVATAR_ITEM_SIZE := 80
const ITEM_SPACING := 10

## 内部节点
var _background: ColorRect
var _panel: Panel
var _title_label: Label
var _close_button: Button
var _tab_container: TabContainer
var _unlocked_grid: GridContainer
var _locked_grid: GridContainer
var _preview_container: VBoxContainer
var _preview_avatar: AvatarDisplay
var _preview_name: Label
var _preview_description: Label
var _preview_rarity: Label
var _preview_unlock_info: Label
var _equip_button: Button
var _purchase_button: Button

## 当前选中的头像ID
var _selected_avatar_id: String = ""


func _ready() -> void:
	_setup_ui()
	_connect_signals()
	_populate_avatars()


func _setup_ui() -> void:
	# 设置全屏覆盖
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	# 半透明背景
	_background = ColorRect.new()
	_background.name = "Background"
	_background.set_anchors_preset(Control.PRESET_FULL_RECT)
	_background.color = Color(0, 0, 0, 0.7)
	add_child(_background)

	# 主面板
	_panel = Panel.new()
	_panel.name = "MainPanel"
	_panel.custom_minimum_size = Vector2(600, 500)
	_panel.set_anchors_preset(Control.PRESET_CENTER)
	_panel.size = Vector2(600, 500)
	_panel.position = Vector2(-300, -250)
	_setup_panel_style(_panel)
	add_child(_panel)

	# 标题
	_title_label = Label.new()
	_title_label.name = "Title"
	_title_label.text = "选择头像"
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.position = Vector2(0, 15)
	_title_label.size = Vector2(600, 30)
	_title_label.add_theme_font_size_override("font_size", 24)
	_panel.add_child(_title_label)

	# 关闭按钮
	_close_button = Button.new()
	_close_button.name = "CloseButton"
	_close_button.text = "✕"
	_close_button.position = Vector2(555, 10)
	_close_button.size = Vector2(35, 35)
	_close_button.flat = true
	_panel.add_child(_close_button)

	# 创建主要内容区域（左右分栏）
	var content_hbox := HBoxContainer.new()
	content_hbox.name = "ContentHBox"
	content_hbox.position = Vector2(15, 55)
	content_hbox.size = Vector2(570, 430)
	_panel.add_child(content_hbox)

	# 左侧：头像网格
	var left_container := VBoxContainer.new()
	left_container.name = "LeftContainer"
	left_container.custom_minimum_size = Vector2(380, 0)
	content_hbox.add_child(left_container)

	# 标签页容器
	_tab_container = TabContainer.new()
	_tab_container.name = "TabContainer"
	_tab_container.custom_minimum_size = Vector2(380, 420)
	left_container.add_child(_tab_container)

	# 已解锁标签页
	var unlocked_scroll := ScrollContainer.new()
	unlocked_scroll.name = "已解锁"
	unlocked_scroll.custom_minimum_size = Vector2(370, 380)
	_tab_container.add_child(unlocked_scroll)

	_unlocked_grid = GridContainer.new()
	_unlocked_grid.name = "UnlockedGrid"
	_unlocked_grid.columns = GRID_COLUMNS
	_unlocked_grid.add_theme_constant_override("h_separation", ITEM_SPACING)
	_unlocked_grid.add_theme_constant_override("v_separation", ITEM_SPACING)
	unlocked_scroll.add_child(_unlocked_grid)

	# 未解锁标签页
	var locked_scroll := ScrollContainer.new()
	locked_scroll.name = "未解锁"
	locked_scroll.custom_minimum_size = Vector2(370, 380)
	_tab_container.add_child(locked_scroll)

	_locked_grid = GridContainer.new()
	_locked_grid.name = "LockedGrid"
	_locked_grid.columns = GRID_COLUMNS
	_locked_grid.add_theme_constant_override("h_separation", ITEM_SPACING)
	_locked_grid.add_theme_constant_override("v_separation", ITEM_SPACING)
	locked_scroll.add_child(_locked_grid)

	# 右侧：预览区域
	_preview_container = VBoxContainer.new()
	_preview_container.name = "PreviewContainer"
	_preview_container.custom_minimum_size = Vector2(170, 0)
	_preview_container.add_theme_constant_override("separation", 10)
	content_hbox.add_child(_preview_container)

	# 预览头像
	var avatar_center := CenterContainer.new()
	avatar_center.custom_minimum_size = Vector2(170, 110)
	_preview_container.add_child(avatar_center)

	_preview_avatar = AvatarDisplay.new()
	_preview_avatar.avatar_size = AvatarDisplay.AvatarSize.XLARGE
	_preview_avatar.border_style = AvatarDisplay.BorderStyle.GLOW
	avatar_center.add_child(_preview_avatar)

	# 预览名称
	_preview_name = Label.new()
	_preview_name.name = "PreviewName"
	_preview_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_preview_name.add_theme_font_size_override("font_size", 18)
	_preview_container.add_child(_preview_name)

	# 预览稀有度
	_preview_rarity = Label.new()
	_preview_rarity.name = "PreviewRarity"
	_preview_rarity.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_preview_rarity.add_theme_font_size_override("font_size", 14)
	_preview_container.add_child(_preview_rarity)

	# 预览描述
	_preview_description = Label.new()
	_preview_description.name = "PreviewDescription"
	_preview_description.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_preview_description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_preview_description.custom_minimum_size = Vector2(160, 60)
	_preview_description.add_theme_font_size_override("font_size", 12)
	_preview_description.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7))
	_preview_container.add_child(_preview_description)

	# 解锁信息
	_preview_unlock_info = Label.new()
	_preview_unlock_info.name = "PreviewUnlockInfo"
	_preview_unlock_info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_preview_unlock_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_preview_unlock_info.custom_minimum_size = Vector2(160, 40)
	_preview_unlock_info.add_theme_font_size_override("font_size", 11)
	_preview_unlock_info.add_theme_color_override("font_color", Color(1.0, 0.8, 0.3))
	_preview_container.add_child(_preview_unlock_info)

	# 装备按钮
	_equip_button = Button.new()
	_equip_button.name = "EquipButton"
	_equip_button.text = "装备"
	_equip_button.custom_minimum_size = Vector2(160, 40)
	_equip_button.visible = false
	_preview_container.add_child(_equip_button)

	# 购买按钮
	_purchase_button = Button.new()
	_purchase_button.name = "PurchaseButton"
	_purchase_button.text = "购买"
	_purchase_button.custom_minimum_size = Vector2(160, 40)
	_purchase_button.visible = false
	_preview_container.add_child(_purchase_button)


func _setup_panel_style(panel: Panel) -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.12, 0.12, 0.18, 0.95)
	style.corner_radius_top_left = 12
	style.corner_radius_top_right = 12
	style.corner_radius_bottom_left = 12
	style.corner_radius_bottom_right = 12
	style.border_width_top = 2
	style.border_width_bottom = 2
	style.border_width_left = 2
	style.border_width_right = 2
	style.border_color = Color(0.4, 0.35, 0.6, 0.8)
	panel.add_theme_stylebox_override("panel", style)


func _connect_signals() -> void:
	_close_button.pressed.connect(_on_close_pressed)
	_background.gui_input.connect(_on_background_input)
	_equip_button.pressed.connect(_on_equip_pressed)
	_purchase_button.pressed.connect(_on_purchase_pressed)

	if AvatarManager:
		AvatarManager.avatar_unlocked.connect(_on_avatar_unlocked)


func _populate_avatars() -> void:
	_clear_grids()

	if not AvatarManager:
		return

	# 填充已解锁头像
	var unlocked := AvatarManager.get_unlocked_avatars()
	for config in unlocked:
		var item := _create_avatar_item(config, true)
		_unlocked_grid.add_child(item)

	# 填充未解锁头像
	var locked := AvatarManager.get_locked_avatars()
	for config in locked:
		var item := _create_avatar_item(config, false)
		_locked_grid.add_child(item)

	# 默认选中当前头像
	if AvatarManager:
		_select_avatar(AvatarManager.get_current_avatar_id())


func _clear_grids() -> void:
	for child in _unlocked_grid.get_children():
		child.queue_free()
	for child in _locked_grid.get_children():
		child.queue_free()


func _create_avatar_item(config: Dictionary, unlocked: bool) -> Control:
	var container := PanelContainer.new()
	container.custom_minimum_size = Vector2(AVATAR_ITEM_SIZE, AVATAR_ITEM_SIZE)

	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.2, 0.2, 0.25, 0.5)
	style.corner_radius_top_left = 8
	style.corner_radius_top_right = 8
	style.corner_radius_bottom_left = 8
	style.corner_radius_bottom_right = 8
	container.add_theme_stylebox_override("panel", style)

	var avatar_display := AvatarDisplay.new()
	avatar_display.avatar_size = AvatarDisplay.AvatarSize.LARGE
	avatar_display.border_style = AvatarDisplay.BorderStyle.RARITY
	avatar_display.clickable = true
	avatar_display.set_avatar(config.id)
	avatar_display.set_rarity(config.get("rarity", "common"))
	container.add_child(avatar_display)

	# 未解锁的头像添加锁定遮罩
	if not unlocked:
		var lock_overlay := ColorRect.new()
		lock_overlay.color = Color(0, 0, 0, 0.6)
		lock_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		lock_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
		container.add_child(lock_overlay)

		var lock_label := Label.new()
		lock_label.text = "🔒"
		lock_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lock_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		lock_label.set_anchors_preset(Control.PRESET_FULL_RECT)
		lock_label.add_theme_font_size_override("font_size", 24)
		lock_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		container.add_child(lock_label)

	# 连接点击信号
	avatar_display.avatar_clicked.connect(_on_avatar_item_clicked.bind(config.id))

	# 存储配置数据
	container.set_meta("avatar_id", config.id)
	container.set_meta("unlocked", unlocked)

	return container


func _select_avatar(avatar_id: String) -> void:
	_selected_avatar_id = avatar_id

	if not AvatarManager:
		return

	var config := AvatarManager.get_avatar_config(avatar_id)
	if config.is_empty():
		return

	# 更新预览
	_preview_avatar.set_avatar(avatar_id)
	_preview_avatar.set_rarity(config.get("rarity", "common"))
	_preview_name.text = config.get("name", "未知")
	_preview_description.text = config.get("description", "")

	# 更新稀有度显示
	var rarity: String = config.get("rarity", "common")
	var rarity_name := AvatarManager.get_rarity_name(rarity)
	var rarity_color := AvatarManager.get_rarity_color(rarity)
	_preview_rarity.text = "[%s]" % rarity_name
	_preview_rarity.add_theme_color_override("font_color", rarity_color)

	# 更新按钮状态
	var is_unlocked := AvatarManager.is_avatar_unlocked(avatar_id)
	var is_current := AvatarManager.get_current_avatar_id() == avatar_id

	_equip_button.visible = is_unlocked and not is_current
	_equip_button.text = "装备"

	# 处理购买按钮
	_purchase_button.visible = false
	_preview_unlock_info.text = ""

	if not is_unlocked:
		var unlock_type: String = config.get("unlock_type", "")
		match unlock_type:
			"level":
				var required_level: int = config.get("unlock_value", 0)
				_preview_unlock_info.text = "需要等级 %d 解锁" % required_level
			"achievement":
				var achievement_id: String = config.get("unlock_value", "")
				_preview_unlock_info.text = "完成成就解锁"
			"purchase":
				var purchase_info: Dictionary = config.get("unlock_value", {})
				var currency: String = purchase_info.get("currency", "gold")
				var amount: int = purchase_info.get("amount", 0)
				var currency_name := "金币" if currency == "gold" else "钻石"
				var currency_icon := "🪙" if currency == "gold" else "💎"
				_purchase_button.text = "购买 %s %d" % [currency_icon, amount]
				_purchase_button.visible = true
				_preview_unlock_info.text = "使用 %d %s 购买" % [amount, currency_name]

	if is_current:
		_preview_unlock_info.text = "✓ 当前使用中"
		_preview_unlock_info.add_theme_color_override("font_color", Color(0.3, 0.9, 0.3))
	elif is_unlocked:
		_preview_unlock_info.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7))
	else:
		_preview_unlock_info.add_theme_color_override("font_color", Color(1.0, 0.8, 0.3))

	# 高亮选中项
	_update_selection_highlight()


func _update_selection_highlight() -> void:
	# 更新已解锁网格
	for child in _unlocked_grid.get_children():
		var avatar_id: String = child.get_meta("avatar_id", "")
		var style: StyleBoxFlat = child.get_theme_stylebox("panel").duplicate()
		if avatar_id == _selected_avatar_id:
			style.border_width_top = 3
			style.border_width_bottom = 3
			style.border_width_left = 3
			style.border_width_right = 3
			style.border_color = Color(0.5, 0.8, 1.0)
		else:
			style.border_width_top = 0
			style.border_width_bottom = 0
			style.border_width_left = 0
			style.border_width_right = 0
		child.add_theme_stylebox_override("panel", style)

	# 更新未解锁网格
	for child in _locked_grid.get_children():
		var avatar_id: String = child.get_meta("avatar_id", "")
		var style: StyleBoxFlat = child.get_theme_stylebox("panel").duplicate()
		if avatar_id == _selected_avatar_id:
			style.border_width_top = 3
			style.border_width_bottom = 3
			style.border_width_left = 3
			style.border_width_right = 3
			style.border_color = Color(0.5, 0.8, 1.0)
		else:
			style.border_width_top = 0
			style.border_width_bottom = 0
			style.border_width_left = 0
			style.border_width_right = 0
		child.add_theme_stylebox_override("panel", style)


func _on_avatar_item_clicked(avatar_id: String) -> void:
	_select_avatar(avatar_id)


func _on_equip_pressed() -> void:
	if _selected_avatar_id.is_empty():
		return

	if AvatarManager and AvatarManager.set_avatar(_selected_avatar_id):
		avatar_selected.emit(_selected_avatar_id)
		_select_avatar(_selected_avatar_id)  # 刷新显示

		if EventBus:
			EventBus.emit_signal("show_notification", "头像已更换")


func _on_purchase_pressed() -> void:
	if _selected_avatar_id.is_empty():
		return

	if AvatarManager and AvatarManager.try_purchase_avatar(_selected_avatar_id):
		_populate_avatars()  # 刷新列表
		_select_avatar(_selected_avatar_id)

		if EventBus:
			EventBus.emit_signal("show_notification", "购买成功！")
	else:
		if EventBus:
			EventBus.emit_signal("show_notification", "货币不足")


func _on_close_pressed() -> void:
	close()


func _on_background_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			close()


func _on_avatar_unlocked(_avatar_id: String) -> void:
	_populate_avatars()


## 打开选择器
func open() -> void:
	visible = true
	_populate_avatars()


## 关闭选择器
func close() -> void:
	visible = false
	closed.emit()


func _input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		close()
		get_viewport().set_input_as_handled()
