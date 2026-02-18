## tutorial_dialog.gd
## 引导对话框 UI 组件
## 显示引导步骤内容，支持高亮遮罩
extends Control

# ==================== 信号定义 ====================

signal next_pressed()
signal skip_pressed()
signal previous_pressed()

# ==================== 节点引用 ====================

var overlay: ColorRect = null
var highlight_mask: Control = null
var dialog_panel: PanelContainer = null
var title_label: Label = null
var content_label: RichTextLabel = null
var step_label: Label = null
var prev_button: Button = null
var next_button: Button = null
var skip_button: Button = null
var arrow_indicator: Control = null

# ==================== 状态变量 ====================

var current_highlight_target: Control = null
var arrow_tween: Tween = null


func _ready() -> void:
	_create_ui()
	_connect_signals()


func _create_ui() -> void:
	"""创建 UI 结构"""
	# 设置为全屏
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	z_index = 1000

	# 创建半透明遮罩层
	overlay = ColorRect.new()
	overlay.name = "Overlay"
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	overlay.color = Color(0, 0, 0, 0.7)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(overlay)

	# 创建高亮遮罩容器
	highlight_mask = Control.new()
	highlight_mask.name = "HighlightMask"
	highlight_mask.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	highlight_mask.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(highlight_mask)

	# 创建指示箭头
	_create_arrow_indicator()

	# 创建对话框面板
	_create_dialog_panel()


func _create_arrow_indicator() -> void:
	"""创建指示箭头"""
	arrow_indicator = Control.new()
	arrow_indicator.name = "ArrowIndicator"
	arrow_indicator.custom_minimum_size = Vector2(40, 40)
	arrow_indicator.visible = false

	var arrow_label := Label.new()
	arrow_label.text = "▼"
	arrow_label.add_theme_font_size_override("font_size", 32)
	arrow_label.add_theme_color_override("font_color", Color(1.0, 0.84, 0.0))
	arrow_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	arrow_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	arrow_indicator.add_child(arrow_label)

	add_child(arrow_indicator)


func _create_dialog_panel() -> void:
	"""创建对话框面板"""
	dialog_panel = PanelContainer.new()
	dialog_panel.name = "DialogPanel"
	dialog_panel.custom_minimum_size = Vector2(500, 200)

	# 设置面板样式
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.12, 0.12, 0.18, 0.98)
	style.border_color = Color(0.3, 0.5, 0.8, 1.0)
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.corner_radius_top_left = 12
	style.corner_radius_top_right = 12
	style.corner_radius_bottom_left = 12
	style.corner_radius_bottom_right = 12
	style.content_margin_left = 20
	style.content_margin_top = 15
	style.content_margin_right = 20
	style.content_margin_bottom = 15
	dialog_panel.add_theme_stylebox_override("panel", style)

	# 内容容器
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)

	# 标题
	title_label = Label.new()
	title_label.name = "TitleLabel"
	title_label.add_theme_font_size_override("font_size", 24)
	title_label.add_theme_color_override("font_color", Color(1.0, 0.84, 0.0))
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(title_label)

	# 分隔线
	var separator := HSeparator.new()
	vbox.add_child(separator)

	# 内容
	content_label = RichTextLabel.new()
	content_label.name = "ContentLabel"
	content_label.bbcode_enabled = true
	content_label.fit_content = true
	content_label.custom_minimum_size = Vector2(460, 80)
	content_label.add_theme_font_size_override("normal_font_size", 16)
	vbox.add_child(content_label)

	# 底部栏
	var bottom_bar := HBoxContainer.new()
	bottom_bar.add_theme_constant_override("separation", 10)

	# 步骤指示
	step_label = Label.new()
	step_label.name = "StepLabel"
	step_label.add_theme_font_size_override("font_size", 14)
	step_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.7))
	step_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bottom_bar.add_child(step_label)

	# 跳过按钮
	skip_button = Button.new()
	skip_button.name = "SkipButton"
	skip_button.text = "跳过引导"
	skip_button.custom_minimum_size = Vector2(90, 35)
	skip_button.flat = true
	skip_button.add_theme_color_override("font_color", Color(0.5, 0.5, 0.6))
	bottom_bar.add_child(skip_button)

	# 上一步按钮
	prev_button = Button.new()
	prev_button.name = "PrevButton"
	prev_button.text = "上一步"
	prev_button.custom_minimum_size = Vector2(80, 35)
	bottom_bar.add_child(prev_button)

	# 下一步按钮
	next_button = Button.new()
	next_button.name = "NextButton"
	next_button.text = "下一步"
	next_button.custom_minimum_size = Vector2(80, 35)
	bottom_bar.add_child(next_button)

	vbox.add_child(bottom_bar)
	dialog_panel.add_child(vbox)
	add_child(dialog_panel)


func _connect_signals() -> void:
	"""连接信号"""
	if next_button:
		next_button.pressed.connect(_on_next_pressed)
	if prev_button:
		prev_button.pressed.connect(_on_previous_pressed)
	if skip_button:
		skip_button.pressed.connect(_on_skip_pressed)


# ==================== 公共方法 ====================

## 显示引导步骤
func show_step(step_data: Dictionary, step_index: int, total_steps: int, hud: Control = null) -> void:
	"""显示指定的引导步骤"""
	# 更新标题和内容
	if title_label:
		title_label.text = step_data.get("title", "")

	if content_label:
		content_label.text = step_data.get("content", "")

	# 更新步骤指示
	if step_label:
		step_label.text = "步骤 %d / %d" % [step_index + 1, total_steps]

	# 更新按钮状态
	if prev_button:
		prev_button.visible = step_index > 0

	if next_button:
		if step_index >= total_steps - 1:
			next_button.text = "完成"
		else:
			next_button.text = "下一步"

	# 处理高亮目标
	var highlight_target := step_data.get("highlight_target", "") as String
	_update_highlight(highlight_target, hud)

	# 定位对话框
	var position_hint := step_data.get("position", "center") as String
	_position_dialog(position_hint)

	# 显示
	visible = true


## 隐藏对话框
func hide_dialog() -> void:
	visible = false
	_clear_highlight()


# ==================== 私有方法 ====================

func _update_highlight(target_path: String, hud: Control) -> void:
	"""更新高亮目标"""
	_clear_highlight()

	if target_path.is_empty() or hud == null:
		overlay.color = Color(0, 0, 0, 0.7)
		arrow_indicator.visible = false
		return

	# 查找目标节点
	var target := hud.get_node_or_null(target_path)
	if target == null or not target is Control:
		overlay.color = Color(0, 0, 0, 0.7)
		arrow_indicator.visible = false
		return

	current_highlight_target = target

	# 创建高亮效果（通过在遮罩上开洞）
	_create_highlight_hole(target)

	# 显示并动画化箭头
	_show_arrow_at_target(target)


func _create_highlight_hole(target: Control) -> void:
	"""在遮罩上创建高亮洞"""
	# 获取目标的全局位置和大小
	var target_rect := target.get_global_rect()

	# 扩大一点边距
	var padding := 8.0
	target_rect = target_rect.grow(padding)

	# 使用 Shader 或多个 ColorRect 来创建洞效果
	# 这里使用简单的方法：4个 ColorRect 围绕目标
	overlay.visible = false

	# 清理旧的高亮遮罩
	for child in highlight_mask.get_children():
		child.queue_free()

	var screen_size := get_viewport_rect().size

	# 上方遮罩
	var top_rect := ColorRect.new()
	top_rect.color = Color(0, 0, 0, 0.7)
	top_rect.position = Vector2.ZERO
	top_rect.size = Vector2(screen_size.x, target_rect.position.y)
	highlight_mask.add_child(top_rect)

	# 下方遮罩
	var bottom_rect := ColorRect.new()
	bottom_rect.color = Color(0, 0, 0, 0.7)
	bottom_rect.position = Vector2(0, target_rect.end.y)
	bottom_rect.size = Vector2(screen_size.x, screen_size.y - target_rect.end.y)
	highlight_mask.add_child(bottom_rect)

	# 左侧遮罩
	var left_rect := ColorRect.new()
	left_rect.color = Color(0, 0, 0, 0.7)
	left_rect.position = Vector2(0, target_rect.position.y)
	left_rect.size = Vector2(target_rect.position.x, target_rect.size.y)
	highlight_mask.add_child(left_rect)

	# 右侧遮罩
	var right_rect := ColorRect.new()
	right_rect.color = Color(0, 0, 0, 0.7)
	right_rect.position = Vector2(target_rect.end.x, target_rect.position.y)
	right_rect.size = Vector2(screen_size.x - target_rect.end.x, target_rect.size.y)
	highlight_mask.add_child(right_rect)

	# 添加高亮边框
	var border := ReferenceRect.new()
	border.position = target_rect.position
	border.size = target_rect.size
	border.border_color = Color(1.0, 0.84, 0.0, 0.8)
	border.border_width = 3.0
	border.editor_only = false
	highlight_mask.add_child(border)


func _show_arrow_at_target(target: Control) -> void:
	"""在目标位置显示箭头"""
	var target_rect := target.get_global_rect()

	# 箭头位置在目标上方
	arrow_indicator.position = Vector2(
		target_rect.position.x + target_rect.size.x / 2 - 20,
		target_rect.position.y - 50
	)
	arrow_indicator.visible = true

	# 箭头上下浮动动画
	_start_arrow_animation()


func _start_arrow_animation() -> void:
	"""开始箭头动画"""
	if arrow_tween:
		arrow_tween.kill()

	arrow_tween = create_tween()
	arrow_tween.set_loops()

	var start_y := arrow_indicator.position.y
	arrow_tween.tween_property(arrow_indicator, "position:y", start_y + 10, 0.4)
	arrow_tween.tween_property(arrow_indicator, "position:y", start_y, 0.4)


func _clear_highlight() -> void:
	"""清除高亮效果"""
	current_highlight_target = null
	overlay.visible = true
	overlay.color = Color(0, 0, 0, 0.7)

	for child in highlight_mask.get_children():
		child.queue_free()

	if arrow_tween:
		arrow_tween.kill()
		arrow_tween = null

	arrow_indicator.visible = false


func _position_dialog(position_hint: String) -> void:
	"""定位对话框"""
	if not dialog_panel:
		return

	var screen_size := get_viewport_rect().size
	var dialog_size := dialog_panel.size

	match position_hint:
		"center":
			dialog_panel.position = (screen_size - dialog_size) / 2
		"above":
			if current_highlight_target:
				var target_rect := current_highlight_target.get_global_rect()
				dialog_panel.position = Vector2(
					(screen_size.x - dialog_size.x) / 2,
					target_rect.position.y - dialog_size.y - 60
				)
			else:
				dialog_panel.position = (screen_size - dialog_size) / 2
		"below":
			if current_highlight_target:
				var target_rect := current_highlight_target.get_global_rect()
				dialog_panel.position = Vector2(
					(screen_size.x - dialog_size.x) / 2,
					target_rect.end.y + 60
				)
			else:
				dialog_panel.position = (screen_size - dialog_size) / 2
		_:
			dialog_panel.position = (screen_size - dialog_size) / 2

	# 确保对话框在屏幕内
	dialog_panel.position.x = clampf(dialog_panel.position.x, 20, screen_size.x - dialog_size.x - 20)
	dialog_panel.position.y = clampf(dialog_panel.position.y, 20, screen_size.y - dialog_size.y - 20)


# ==================== 事件处理 ====================

func _on_next_pressed() -> void:
	next_pressed.emit()


func _on_previous_pressed() -> void:
	previous_pressed.emit()


func _on_skip_pressed() -> void:
	skip_pressed.emit()


func _input(event: InputEvent) -> void:
	# ESC 键跳过引导
	if event.is_action_pressed("ui_cancel"):
		skip_pressed.emit()
		get_viewport().set_input_as_handled()
	# 空格或回车下一步
	elif event.is_action_pressed("ui_accept"):
		next_pressed.emit()
		get_viewport().set_input_as_handled()
