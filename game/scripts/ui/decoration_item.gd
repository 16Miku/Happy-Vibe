## decoration_item.gd
## 装饰项 UI 组件 - 显示单个装饰物的信息
extends PanelContainer

signal clicked()

# 节点引用
@onready var image: TextureRect = $VBoxContainer/ImageContainer/Image
@onready var name_label: Label = $VBoxContainer/NameLabel
@onready var price_label: Label = $VBoxContainer/PriceLabel
@onready var owned_badge: Label = $OwnedBadge

# 装饰数据
var decoration_id: String = ""
var decoration_data: Dictionary = {}


func _ready() -> void:
	gui_input.connect(_on_gui_input)
	mouse_entered.connect(_on_mouse_entered)
	mouse_exited.connect(_on_mouse_exited)


## 设置装饰数据
func setup(data: Dictionary) -> void:
	decoration_data = data
	decoration_id = data.get("id", "")

	name_label.text = data.get("name", "未知")
	price_label.text = "%d 金币" % data.get("price", 0)

	# 加载图片
	var texture_path: String = "res://assets/sprites/decorations/%s.png" % decoration_id
	if ResourceLoader.exists(texture_path):
		image.texture = load(texture_path)
	else:
		image.texture = _create_placeholder()

	# 显示拥有数量
	var owned_count: int = data.get("owned_count", 0)
	if owned_count <= 0 and DecorationManager:
		owned_count = DecorationManager.get_owned_decorations().get(decoration_id, 0)

	if owned_count > 0:
		owned_badge.text = "x%d" % owned_count
		owned_badge.visible = true
	else:
		owned_badge.visible = false

	# 检查是否已解锁
	_update_lock_state()


## 创建占位符纹理
func _create_placeholder() -> ImageTexture:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var color: Color = DecorationData.get_type_color(decoration_data.get("type", 0))
	img.fill(color)

	# 边框
	for i in range(64):
		img.set_pixel(i, 0, Color.WHITE)
		img.set_pixel(i, 63, Color.WHITE)
		img.set_pixel(0, i, Color.WHITE)
		img.set_pixel(63, i, Color.WHITE)

	return ImageTexture.create_from_image(img)


## 更新锁定状态
func _update_lock_state() -> void:
	var unlock_level: int = decoration_data.get("unlock_level", 1)
	var player_level: int = 1

	if GameManager:
		player_level = GameManager.get_level()

	if player_level < unlock_level:
		modulate = Color(0.5, 0.5, 0.5, 1)
		price_label.text = "等级 %d 解锁" % unlock_level
	else:
		modulate = Color.WHITE


## 输入事件
func _on_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
			clicked.emit()


## 鼠标进入
func _on_mouse_entered() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.25, 0.25, 0.3, 1)
	style.set_corner_radius_all(8)
	add_theme_stylebox_override("panel", style)


## 鼠标离开
func _on_mouse_exited() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.18, 0.18, 0.22, 1)
	style.set_corner_radius_all(8)
	add_theme_stylebox_override("panel", style)
