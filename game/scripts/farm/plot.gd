extends Area2D
## 地块脚本
## 管理单个种植地块的状态

signal crop_planted(crop_type: String)
signal crop_harvested(crop_data: Dictionary)
signal crop_ready()

@export var plot_id: String = ""

@onready var sprite: Sprite2D = $Sprite2D
@onready var crop_sprite: Sprite2D = $CropSprite

var current_crop: Dictionary = {}
var is_planted: bool = false
var growth_progress: float = 0.0


func _ready() -> void:
	if plot_id.is_empty():
		plot_id = str(get_instance_id())


func _process(delta: float) -> void:
	if is_planted and not current_crop.is_empty():
		_update_growth(delta)


func _update_growth(delta: float) -> void:
	"""更新作物生长"""
	var growth_time: float = current_crop.get("growth_time", 3600.0)
	growth_progress += delta / growth_time

	if growth_progress >= 1.0 and not current_crop.get("is_ready", false):
		current_crop["is_ready"] = true
		crop_ready.emit()
		EventBus.crop_ready.emit(plot_id)


func plant(crop_type: String, crop_data: Dictionary) -> bool:
	"""种植作物"""
	if is_planted:
		return false

	current_crop = crop_data.duplicate()
	current_crop["type"] = crop_type
	current_crop["planted_at"] = Time.get_unix_time_from_system()
	current_crop["is_ready"] = false

	is_planted = true
	growth_progress = 0.0

	crop_planted.emit(crop_type)
	EventBus.crop_planted.emit(plot_id, crop_type)
	return true


func harvest() -> Dictionary:
	"""收获作物"""
	if not is_planted or not current_crop.get("is_ready", false):
		return {}

	var harvested := current_crop.duplicate()
	harvested["quality"] = _calculate_quality()
	harvested["value"] = _calculate_value(harvested)

	# 重置地块
	current_crop = {}
	is_planted = false
	growth_progress = 0.0

	crop_harvested.emit(harvested)
	EventBus.crop_harvested.emit(plot_id, harvested)
	return harvested


func _calculate_quality() -> int:
	"""计算作物品质 (1-4)"""
	var rand := randf()
	if rand < 0.05:
		return 4  # 传说
	elif rand < 0.25:
		return 3  # 精品
	elif rand < 0.60:
		return 2  # 优良
	return 1  # 普通


func _calculate_value(crop_data: Dictionary) -> int:
	"""计算作物价值"""
	var base_value: int = crop_data.get("base_value", 10)
	var quality: int = crop_data.get("quality", 1)
	var multipliers := {1: 1.0, 2: 1.5, 3: 2.5, 4: 5.0}
	return int(base_value * multipliers.get(quality, 1.0))


func serialize() -> Dictionary:
	"""序列化地块数据"""
	return {
		"plot_id": plot_id,
		"position": {"x": position.x, "y": position.y},
		"is_planted": is_planted,
		"current_crop": current_crop,
		"growth_progress": growth_progress
	}


func deserialize(data: Dictionary) -> void:
	"""反序列化地块数据"""
	plot_id = data.get("plot_id", plot_id)
	is_planted = data.get("is_planted", false)
	current_crop = data.get("current_crop", {})
	growth_progress = data.get("growth_progress", 0.0)
