## decoration_panel.gd
## 装饰面板 UI - 显示装饰商店和已拥有的装饰
extends Control

# 装饰类型枚举引用
const DecorationType = preload("res://scripts/decoration/decoration_manager.gd").DecorationType

# 节点引用
@onready var beauty_label: Label = $MarginContainer/VBoxContainer/Header/BeautyLabel
@onready var close_button: Button = $MarginContainer/VBoxContainer/Header/CloseButton
@onready var item_grid: GridContainer = $MarginContainer/VBoxContainer/ContentContainer/ItemScrollContainer/ItemGrid
@onready var detail_name: Label = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailName
@onready var detail_image: TextureRect = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailImage
@onready var detail_description: Label = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailDescription
@onready var size_label: Label = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailStats/SizeLabel
@onready var detail_beauty_label: Label = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailStats/BeautyLabel
@onready var price_label: Label = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailStats/PriceLabel
@onready var owned_label: Label = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/DetailStats/OwnedLabel
@onready var buy_button: Button = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/ButtonContainer/BuyButton
@onready var place_button: Button = $MarginContainer/VBoxContainer/ContentContainer/DetailPanel/DetailContent/ButtonContainer/PlaceButton

# 分类按钮
@onready var furniture_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/FurnitureBtn
@onready var plant_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/PlantBtn
@onready var fence_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/FenceBtn
@onready var path_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/PathBtn
@onready var lighting_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/LightingBtn
@onready var statue_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/StatueBtn
@onready var seasonal_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/SeasonalBtn
@onready var owned_btn: Button = $MarginContainer/VBoxContainer/ContentContainer/CategoryList/OwnedBtn

# 当前状态
var current_category: int = DecorationType.FURNITURE
var selected_decoration_id: String = ""
var show_owned_only: bool = false

# 装饰项场景
var decoration_item_scene: PackedScene = preload("res://scenes/ui/decoration/decoration_item.tscn")


func _ready() -> void:
	_setup_ui()
	_connect_signals()
	_load_category(DecorationType.FURNITURE)
	_update_beauty_display()


func _setup_ui() -> void:
	close_button.pressed.connect(_on_close_pressed)
	buy_button.pressed.connect(_on_buy_pressed)
	place_button.pressed.connect(_on_place_pressed)

	# 分类按钮
	furniture_btn.pressed.connect(_on_category_pressed.bind(DecorationType.FURNITURE))
	plant_btn.pressed.connect(_on_category_pressed.bind(DecorationType.PLANT))
	fence_btn.pressed.connect(_on_category_pressed.bind(DecorationType.FENCE))
	path_btn.pressed.connect(_on_category_pressed.bind(DecorationType.PATH))
	lighting_btn.pressed.connect(_on_category_pressed.bind(DecorationType.LIGHTING))
	statue_btn.pressed.connect(_on_category_pressed.bind(DecorationType.STATUE))
	seasonal_btn.pressed.connect(_on_category_pressed.bind(DecorationType.SEASONAL))
	owned_btn.pressed.connect(_on_owned_pressed)

	# 初始状态
	buy_button.disabled = true
	place_button.disabled = true


func _connect_signals() -> void:
	if DecorationManager:
		DecorationManager.farm_beauty_changed.connect(_on_beauty_changed)
		DecorationManager.decoration_placed.connect(_on_decoration_placed)


## 加载分类
func _load_category(category: int) -> void:
	current_category = category
	show_owned_only = false
	_clear_grid()

	var decorations: Array = DecorationData.get_decorations_by_type(category)
	for deco in decorations:
		_add_decoration_item(deco)

	_update_category_buttons()
	_clear_detail()


## 加载已拥有的装饰
func _load_owned() -> void:
	show_owned_only = true
	_clear_grid()

	if not DecorationManager:
		return

	var owned: Dictionary = DecorationManager.get_owned_decorations()
	for deco_id in owned.keys():
		var deco: Dictionary = DecorationData.get_decoration(deco_id)
		if not deco.is_empty():
			deco["owned_count"] = owned[deco_id]
			_add_decoration_item(deco)

	_update_category_buttons()
	_clear_detail()


## 清空网格
func _clear_grid() -> void:
	for child in item_grid.get_children():
		child.queue_free()


## 添加装饰项
func _add_decoration_item(deco: Dictionary) -> void:
	var item: Control = decoration_item_scene.instantiate()
	item.setup(deco)
	item.clicked.connect(_on_item_clicked.bind(deco.get("id", "")))
	item_grid.add_child(item)


## 更新分类按钮状态
func _update_category_buttons() -> void:
	furniture_btn.button_pressed = current_category == DecorationType.FURNITURE and not show_owned_only
	plant_btn.button_pressed = current_category == DecorationType.PLANT and not show_owned_only
	fence_btn.button_pressed = current_category == DecorationType.FENCE and not show_owned_only
	path_btn.button_pressed = current_category == DecorationType.PATH and not show_owned_only
	lighting_btn.button_pressed = current_category == DecorationType.LIGHTING and not show_owned_only
	statue_btn.button_pressed = current_category == DecorationType.STATUE and not show_owned_only
	seasonal_btn.button_pressed = current_category == DecorationType.SEASONAL and not show_owned_only
	owned_btn.button_pressed = show_owned_only


## 更新美观度显示
func _update_beauty_display() -> void:
	if DecorationManager:
		beauty_label.text = "农场美观度: %d" % DecorationManager.get_farm_beauty()


## 清空详情面板
func _clear_detail() -> void:
	selected_decoration_id = ""
	detail_name.text = "选择一个装饰"
	detail_description.text = "点击左侧装饰查看详情"
	detail_image.texture = null
	size_label.text = "尺寸: -"
	detail_beauty_label.text = "美观度: -"
	price_label.text = "价格: -"
	owned_label.text = "拥有: 0"
	buy_button.disabled = true
	place_button.disabled = true


## 显示装饰详情
func _show_detail(decoration_id: String) -> void:
	selected_decoration_id = decoration_id
	var deco: Dictionary = DecorationData.get_decoration(decoration_id)

	if deco.is_empty():
		_clear_detail()
		return

	detail_name.text = deco.get("name", "未知")
	detail_description.text = deco.get("description", "")

	var size: Vector2i = deco.get("size", Vector2i(1, 1))
	size_label.text = "尺寸: %dx%d" % [size.x, size.y]
	detail_beauty_label.text = "美观度: +%d" % deco.get("beauty", 0)
	price_label.text = "价格: %d 金币" % deco.get("price", 0)

	var owned_count: int = 0
	if DecorationManager:
		owned_count = DecorationManager.get_owned_decorations().get(decoration_id, 0)
	owned_label.text = "拥有: %d" % owned_count

	# 加载图片
	var texture_path: String = "res://assets/sprites/decorations/%s.png" % decoration_id
	if ResourceLoader.exists(texture_path):
		detail_image.texture = load(texture_path)
	else:
		detail_image.texture = null

	# 更新按钮状态
	buy_button.disabled = false
	place_button.disabled = owned_count <= 0

	# 检查等级限制
	var unlock_level: int = deco.get("unlock_level", 1)
	if GameManager and GameManager.get_level() < unlock_level:
		buy_button.text = "需要等级 %d" % unlock_level
		buy_button.disabled = true
	else:
		buy_button.text = "购买"


# ==================== 事件处理 ====================

func _on_close_pressed() -> void:
	hide()
	if EventBus:
		EventBus.close_panel.emit("decoration")


func _on_category_pressed(category: int) -> void:
	_load_category(category)


func _on_owned_pressed() -> void:
	_load_owned()


func _on_item_clicked(decoration_id: String) -> void:
	_show_detail(decoration_id)


func _on_buy_pressed() -> void:
	if selected_decoration_id.is_empty():
		return

	if DecorationManager:
		if DecorationManager.buy_decoration(selected_decoration_id, 1):
			_show_detail(selected_decoration_id)  # 刷新详情
			if show_owned_only:
				_load_owned()  # 刷新已拥有列表


func _on_place_pressed() -> void:
	if selected_decoration_id.is_empty():
		return

	if DecorationManager:
		if DecorationManager.enter_placement_mode(selected_decoration_id):
			hide()  # 关闭面板进入放置模式
			if EventBus:
				EventBus.notify("进入放置模式，点击农场放置装饰")


func _on_beauty_changed(new_value: int) -> void:
	beauty_label.text = "农场美观度: %d" % new_value


func _on_decoration_placed(_decoration_id: String, _position: Vector2) -> void:
	# 刷新详情显示
	if not selected_decoration_id.is_empty():
		_show_detail(selected_decoration_id)


## 显示面板
func show_panel() -> void:
	_update_beauty_display()
	if show_owned_only:
		_load_owned()
	else:
		_load_category(current_category)
	show()


## 隐藏面板
func hide_panel() -> void:
	hide()
