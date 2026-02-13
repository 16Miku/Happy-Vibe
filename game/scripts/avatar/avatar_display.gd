## 头像显示组件
## 用于在 UI 中显示玩家头像，支持不同尺寸和样式
@tool
class_name AvatarDisplay
extends Control

## 信号
signal avatar_clicked()

## 头像尺寸预设
enum AvatarSize {
	SMALL = 32,   # 小尺寸，用于列表项
	MEDIUM = 48,  # 中等尺寸，用于 HUD
	LARGE = 64,   # 大尺寸，用于个人资料
	XLARGE = 96,  # 超大尺寸，用于头像选择器
}

## 边框样式
enum BorderStyle {
	NONE,      # 无边框
	SIMPLE,    # 简单边框
	RARITY,    # 根据稀有度显示边框颜色
	GLOW,      # 发光边框
}

## 导出属性
@export var avatar_size: AvatarSize = AvatarSize.MEDIUM:
	set(value):
		avatar_size = value
		_update_size()

@export var border_style: BorderStyle = BorderStyle.SIMPLE:
	set(value):
		border_style = value
		_update_border()

@export var border_width: float = 2.0:
	set(value):
		border_width = value
		_update_border()

@export var border_color: Color = Color(0.6, 0.5, 0.8, 1.0):
	set(value):
		border_color = value
		_update_border()

@export var clickable: bool = false:
	set(value):
		clickable = value
		_update_clickable()

@export var show_level_badge: bool = false:
	set(value):
		show_level_badge = value
		_update_level_badge()

## 内部节点
var _texture_rect: TextureRect
var _border_panel: Panel
var _level_badge: Label
var _click_button: Button
var _hover_highlight: ColorRect

## 当前显示的头像ID
var _current_avatar_id: String = ""

## 稀有度（用于边框颜色）
var _rarity: String = "common"


func _ready() -> void:
	_setup_ui()
	_update_size()

	if not Engine.is_editor_hint():
		_connect_signals()
		_load_current_avatar()


func _setup_ui() -> void:
	# 设置根节点
	custom_minimum_size = Vector2(avatar_size, avatar_size)

	# 创建边框面板
	_border_panel = Panel.new()
	_border_panel.name = "BorderPanel"
	add_child(_border_panel)

	# 创建头像纹理
	_texture_rect = TextureRect.new()
	_texture_rect.name = "AvatarTexture"
	_texture_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_texture_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	add_child(_texture_rect)

	# 创建悬停高亮
	_hover_highlight = ColorRect.new()
	_hover_highlight.name = "HoverHighlight"
	_hover_highlight.color = Color(1, 1, 1, 0.1)
	_hover_highlight.visible = false
	_hover_highlight.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hover_highlight)

	# 创建点击按钮（透明覆盖层）
	_click_button = Button.new()
	_click_button.name = "ClickButton"
	_click_button.flat = true
	_click_button.mouse_filter = Control.MOUSE_FILTER_STOP if clickable else Control.MOUSE_FILTER_IGNORE
	add_child(_click_button)

	# 创建等级徽章
	_level_badge = Label.new()
	_level_badge.name = "LevelBadge"
	_level_badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_level_badge.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_level_badge.visible = show_level_badge
	add_child(_level_badge)

	_update_border()


func _connect_signals() -> void:
	_click_button.pressed.connect(_on_click)
	_click_button.mouse_entered.connect(_on_mouse_entered)
	_click_button.mouse_exited.connect(_on_mouse_exited)

	# 监听头像变化
	if AvatarManager:
		AvatarManager.avatar_changed.connect(_on_avatar_changed)


func _update_size() -> void:
	var size_value := float(avatar_size)
	custom_minimum_size = Vector2(size_value, size_value)
	size = Vector2(size_value, size_value)

	if _border_panel:
		_border_panel.position = Vector2.ZERO
		_border_panel.size = Vector2(size_value, size_value)

	if _texture_rect:
		var padding := border_width * 2
		_texture_rect.position = Vector2(padding, padding)
		_texture_rect.size = Vector2(size_value - padding * 2, size_value - padding * 2)

	if _hover_highlight:
		_hover_highlight.position = Vector2.ZERO
		_hover_highlight.size = Vector2(size_value, size_value)

	if _click_button:
		_click_button.position = Vector2.ZERO
		_click_button.size = Vector2(size_value, size_value)

	if _level_badge:
		var badge_size := size_value * 0.35
		_level_badge.position = Vector2(size_value - badge_size, size_value - badge_size)
		_level_badge.size = Vector2(badge_size, badge_size)
		_level_badge.add_theme_font_size_override("font_size", int(badge_size * 0.6))


func _update_border() -> void:
	if not _border_panel:
		return

	var style := StyleBoxFlat.new()
	style.corner_radius_top_left = int(float(avatar_size) * 0.15)
	style.corner_radius_top_right = int(float(avatar_size) * 0.15)
	style.corner_radius_bottom_left = int(float(avatar_size) * 0.15)
	style.corner_radius_bottom_right = int(float(avatar_size) * 0.15)

	match border_style:
		BorderStyle.NONE:
			style.bg_color = Color.TRANSPARENT
			style.border_width_top = 0
			style.border_width_bottom = 0
			style.border_width_left = 0
			style.border_width_right = 0

		BorderStyle.SIMPLE:
			style.bg_color = Color(0.15, 0.15, 0.2, 0.8)
			style.border_width_top = int(border_width)
			style.border_width_bottom = int(border_width)
			style.border_width_left = int(border_width)
			style.border_width_right = int(border_width)
			style.border_color = border_color

		BorderStyle.RARITY:
			style.bg_color = Color(0.15, 0.15, 0.2, 0.8)
			style.border_width_top = int(border_width)
			style.border_width_bottom = int(border_width)
			style.border_width_left = int(border_width)
			style.border_width_right = int(border_width)
			style.border_color = _get_rarity_border_color()

		BorderStyle.GLOW:
			style.bg_color = Color(0.15, 0.15, 0.2, 0.8)
			style.border_width_top = int(border_width)
			style.border_width_bottom = int(border_width)
			style.border_width_left = int(border_width)
			style.border_width_right = int(border_width)
			style.border_color = _get_rarity_border_color()
			style.shadow_color = _get_rarity_border_color() * Color(1, 1, 1, 0.5)
			style.shadow_size = int(border_width * 2)

	_border_panel.add_theme_stylebox_override("panel", style)


func _update_clickable() -> void:
	if _click_button:
		_click_button.mouse_filter = Control.MOUSE_FILTER_STOP if clickable else Control.MOUSE_FILTER_IGNORE


func _update_level_badge() -> void:
	if _level_badge:
		_level_badge.visible = show_level_badge
		if show_level_badge and GameManager:
			_level_badge.text = str(GameManager.player_data.get("level", 1))


func _get_rarity_border_color() -> Color:
	if AvatarManager:
		return AvatarManager.get_rarity_color(_rarity)

	match _rarity:
		"common":
			return Color(0.7, 0.7, 0.7)
		"rare":
			return Color(0.3, 0.5, 1.0)
		"epic":
			return Color(0.6, 0.3, 0.9)
		"legendary":
			return Color(1.0, 0.7, 0.2)
		_:
			return border_color


func _load_current_avatar() -> void:
	if AvatarManager:
		var avatar_id := AvatarManager.get_current_avatar_id()
		set_avatar(avatar_id)


## 设置显示的头像
func set_avatar(avatar_id: String) -> void:
	_current_avatar_id = avatar_id

	if AvatarManager:
		var config := AvatarManager.get_avatar_config(avatar_id)
		if not config.is_empty():
			_rarity = config.get("rarity", "common")

		var texture := AvatarManager.load_avatar_texture(avatar_id)
		if _texture_rect:
			_texture_rect.texture = texture

	if border_style == BorderStyle.RARITY or border_style == BorderStyle.GLOW:
		_update_border()


## 设置头像纹理（直接设置，不通过 AvatarManager）
func set_texture(texture: Texture2D) -> void:
	if _texture_rect:
		_texture_rect.texture = texture


## 设置稀有度（影响边框颜色）
func set_rarity(rarity: String) -> void:
	_rarity = rarity
	if border_style == BorderStyle.RARITY or border_style == BorderStyle.GLOW:
		_update_border()


## 设置等级徽章
func set_level(level: int) -> void:
	if _level_badge:
		_level_badge.text = str(level)


## 获取当前头像ID
func get_avatar_id() -> String:
	return _current_avatar_id


func _on_click() -> void:
	avatar_clicked.emit()


func _on_mouse_entered() -> void:
	if clickable and _hover_highlight:
		_hover_highlight.visible = true


func _on_mouse_exited() -> void:
	if _hover_highlight:
		_hover_highlight.visible = false


func _on_avatar_changed(avatar_id: String) -> void:
	set_avatar(avatar_id)
