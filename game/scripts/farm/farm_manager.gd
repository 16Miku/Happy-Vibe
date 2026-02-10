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
	# TODO: 根据保存的数据恢复农场状态


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
