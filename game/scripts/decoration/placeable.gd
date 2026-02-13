## placeable.gd
## 可放置物体基类 - 用于农场中的装饰物显示和交互
extends Node2D
class_name Placeable

# 信号
signal clicked(instance_id: String)
signal hovered(instance_id: String)
signal unhovered(instance_id: String)

# 装饰数据
var instance_id: String = ""
var decoration_id: String = ""
var decoration_data: Dictionary = {}
var grid_position: Vector2i = Vector2i.ZERO

# 状态
var is_selected: bool = false
var is_hovered: bool = false
var is_preview: bool = false  # 预览模式（放置前）
var can_place: bool = true    # 是否可以放置在当前位置

# 节点引用
@onready var sprite: Sprite2D = $Sprite2D
@onready var collision: Area2D = $Area2D
@onready var highlight: Sprite2D = $Highlight


func _ready() -> void:
	_setup_collision()
	_update_visual()


func _setup_collision() -> void:
	if collision:
		collision.mouse_entered.connect(_on_mouse_entered)
		collision.mouse_exited.connect(_on_mouse_exited)
		collision.input_event.connect(_on_input_event)


## 初始化装饰物
func setup(data: Dictionary) -> void:
	instance_id = data.get("instance_id", "")
	decoration_id = data.get("decoration_id", "")
	grid_position = data.get("grid_position", Vector2i.ZERO)

	decoration_data = DecorationData.get_decoration(decoration_id)

	position = data.get("position", Vector2.ZERO)
	rotation_degrees = data.get("rotation", 0)

	_update_visual()
	_update_collision_shape()


## 设置为预览模式
func set_preview_mode(enabled: bool) -> void:
	is_preview = enabled
	_update_visual()

	if collision:
		collision.monitoring = not enabled
		collision.monitorable = not enabled


## 设置是否可放置
func set_can_place(can: bool) -> void:
	can_place = can
	_update_visual()


## 设置选中状态
func set_selected(selected: bool) -> void:
	is_selected = selected
	_update_visual()


## 更新视觉效果
func _update_visual() -> void:
	if not sprite:
		return

	# 加载精灵纹理
	var texture_path: String = "res://assets/sprites/decorations/%s.png" % decoration_id
	if ResourceLoader.exists(texture_path):
		sprite.texture = load(texture_path)
	else:
		# 使用占位符纹理
		sprite.texture = _create_placeholder_texture()

	# 更新高亮显示
	if highlight:
		if is_preview:
			highlight.visible = true
			highlight.modulate = Color(0.3, 0.9, 0.3, 0.5) if can_place else Color(0.9, 0.3, 0.3, 0.5)
		elif is_selected:
			highlight.visible = true
			highlight.modulate = Color(0.3, 0.6, 0.9, 0.5)
		elif is_hovered:
			highlight.visible = true
			highlight.modulate = Color(1.0, 1.0, 1.0, 0.3)
		else:
			highlight.visible = false

	# 预览模式半透明
	if is_preview:
		modulate.a = 0.7
	else:
		modulate.a = 1.0


## 创建占位符纹理
func _create_placeholder_texture() -> ImageTexture:
	var size: Vector2i = decoration_data.get("size", Vector2i(1, 1))
	var pixel_size: int = 32

	var image := Image.create(size.x * pixel_size, size.y * pixel_size, false, Image.FORMAT_RGBA8)
	var color: Color = DecorationData.get_type_color(decoration_data.get("type", 0))

	image.fill(color)

	# 添加边框
	for x in range(image.get_width()):
		image.set_pixel(x, 0, Color.WHITE)
		image.set_pixel(x, image.get_height() - 1, Color.WHITE)
	for y in range(image.get_height()):
		image.set_pixel(0, y, Color.WHITE)
		image.set_pixel(image.get_width() - 1, y, Color.WHITE)

	return ImageTexture.create_from_image(image)


## 更新碰撞形状
func _update_collision_shape() -> void:
	if not collision:
		return

	var collision_shape: CollisionShape2D = collision.get_node_or_null("CollisionShape2D")
	if not collision_shape:
		return

	var size: Vector2i = decoration_data.get("size", Vector2i(1, 1))
	var rect := RectangleShape2D.new()
	rect.size = Vector2(size) * 32

	collision_shape.shape = rect
	collision_shape.position = rect.size / 2


## 鼠标进入
func _on_mouse_entered() -> void:
	if is_preview:
		return

	is_hovered = true
	_update_visual()
	hovered.emit(instance_id)


## 鼠标离开
func _on_mouse_exited() -> void:
	if is_preview:
		return

	is_hovered = false
	_update_visual()
	unhovered.emit(instance_id)


## 输入事件
func _on_input_event(_viewport: Node, event: InputEvent, _shape_idx: int) -> void:
	if is_preview:
		return

	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
			clicked.emit(instance_id)


## 获取装饰信息
func get_decoration_info() -> Dictionary:
	return {
		"instance_id": instance_id,
		"decoration_id": decoration_id,
		"name": decoration_data.get("name", ""),
		"description": decoration_data.get("description", ""),
		"beauty": decoration_data.get("beauty", 0),
		"position": position,
		"grid_position": grid_position
	}


## 播放放置动画
func play_place_animation() -> void:
	var tween := create_tween()
	tween.set_ease(Tween.EASE_OUT)
	tween.set_trans(Tween.TRANS_BACK)

	scale = Vector2(0.5, 0.5)
	tween.tween_property(self, "scale", Vector2.ONE, 0.3)


## 播放移除动画
func play_remove_animation() -> void:
	var tween := create_tween()
	tween.set_ease(Tween.EASE_IN)
	tween.set_trans(Tween.TRANS_BACK)

	tween.tween_property(self, "scale", Vector2(0.5, 0.5), 0.2)
	tween.parallel().tween_property(self, "modulate:a", 0.0, 0.2)
	tween.tween_callback(queue_free)
