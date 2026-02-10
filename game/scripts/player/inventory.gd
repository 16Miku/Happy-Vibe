extends Node
## 库存系统
## 管理玩家物品

signal item_added(item_id: String, quantity: int)
signal item_removed(item_id: String, quantity: int)
signal inventory_changed()

const MAX_SLOTS := 50

var items: Dictionary = {}  # item_id -> {type, quantity, metadata}


func _ready() -> void:
	_load_inventory()


func _load_inventory() -> void:
	"""从 GameManager 加载库存"""
	# TODO: 实现库存加载


func save_inventory() -> void:
	"""保存库存到 GameManager"""
	# TODO: 实现库存保存


func add_item(item_id: String, item_type: String, quantity: int = 1, metadata: Dictionary = {}) -> bool:
	"""添加物品"""
	if items.has(item_id):
		items[item_id]["quantity"] += quantity
	else:
		if items.size() >= MAX_SLOTS:
			return false  # 库存已满
		items[item_id] = {
			"type": item_type,
			"quantity": quantity,
			"metadata": metadata
		}

	item_added.emit(item_id, quantity)
	inventory_changed.emit()
	save_inventory()
	return true


func remove_item(item_id: String, quantity: int = 1) -> bool:
	"""移除物品"""
	if not items.has(item_id):
		return false

	var current_quantity: int = items[item_id]["quantity"]
	if current_quantity < quantity:
		return false

	items[item_id]["quantity"] -= quantity
	if items[item_id]["quantity"] <= 0:
		items.erase(item_id)

	item_removed.emit(item_id, quantity)
	inventory_changed.emit()
	save_inventory()
	return true


func has_item(item_id: String, quantity: int = 1) -> bool:
	"""检查是否有足够的物品"""
	if not items.has(item_id):
		return false
	return items[item_id]["quantity"] >= quantity


func get_item_count(item_id: String) -> int:
	"""获取物品数量"""
	if not items.has(item_id):
		return 0
	return items[item_id]["quantity"]


func get_all_items() -> Dictionary:
	"""获取所有物品"""
	return items.duplicate(true)


func get_items_by_type(item_type: String) -> Array:
	"""按类型获取物品"""
	var result: Array = []
	for item_id in items:
		if items[item_id]["type"] == item_type:
			result.append({
				"id": item_id,
				"data": items[item_id]
			})
	return result
