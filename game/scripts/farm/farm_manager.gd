extends Node2D
## 农场管理器
## 管理农场的地块、建筑和装饰

signal plot_added(plot: Node2D)
signal building_added(building: Node2D)

@onready var plots_container: Node2D = $Plots
@onready var buildings_container: Node2D = $Buildings
@onready var decorations_container: Node2D = $Decorations

var plots: Array[Node2D] = []
var buildings: Array[Node2D] = []


func _ready() -> void:
	_load_farm_data()


func _load_farm_data() -> void:
	"""从 GameManager 加载农场数据"""
	var farm_data: Dictionary = GameManager.player_data.get("farm", {})
	load_from_data(farm_data)


func load_from_data(data: Dictionary) -> void:
	"""从数据字典加载农场状态"""
	# 清除现有地块
	for plot in plots:
		plot.queue_free()
	plots.clear()

	# 加载地块
	var plots_data: Array = data.get("plots", [])
	for plot_data in plots_data:
		if plot_data is Dictionary:
			var pos := Vector2(
				plot_data.get("x", 0),
				plot_data.get("y", 0)
			)
			var plot := add_plot(pos)
			if plot and plot.has_method("deserialize"):
				plot.deserialize(plot_data)

	# 如果没有地块，创建默认的 3x3 地块
	if plots.is_empty():
		_create_default_plots()


func save_farm_data() -> void:
	"""保存农场数据到 GameManager"""
	var farm_data := {
		"plots": _serialize_plots(),
		"buildings": _serialize_buildings()
	}
	GameManager.player_data["farm"] = farm_data
	GameManager.save_player_data()


func _serialize_plots() -> Array:
	"""序列化地块数据"""
	var data: Array = []
	for plot in plots:
		if plot.has_method("serialize"):
			data.append(plot.serialize())
	return data


func _serialize_buildings() -> Array:
	"""序列化建筑数据"""
	var data: Array = []
	for building in buildings:
		if building.has_method("serialize"):
			data.append(building.serialize())
	return data


func add_plot(position: Vector2) -> Node2D:
	"""添加新地块"""
	var plot_scene := preload("res://scenes/farm/plot.tscn")
	var plot := plot_scene.instantiate()
	plot.position = position
	plots_container.add_child(plot)
	plots.append(plot)
	plot_added.emit(plot)
	return plot


func get_plot_at(position: Vector2) -> Node2D:
	"""获取指定位置的地块"""
	for plot in plots:
		if plot.position.distance_to(position) < 32:  # 假设地块大小为 32x32
			return plot
	return null


func _create_default_plots() -> void:
	"""创建默认的 3x3 地块"""
	var start_pos := Vector2(0, 0)
	var plot_size := 64  # 地块间距

	for row in range(3):
		for col in range(3):
			var pos := start_pos + Vector2(col * plot_size, row * plot_size)
			add_plot(pos)
