## decoration_manager.gd
## 装饰管理器 - 管理农场装饰物的放置、移动、存储
## 作为 AutoLoad 单例运行
extends Node

# 装饰类型枚举
enum DecorationType {
	FURNITURE,    # 家具
	PLANT,        # 植物装饰
	FENCE,        # 围栏
	PATH,         # 道路
	LIGHTING,     # 灯光
	STATUE,       # 雕像
	SEASONAL      # 季节限定
}

# 放置模式枚举
enum PlacementMode {
	NONE,         # 无
	PLACING,      # 放置中
	MOVING,       # 移动中
	REMOVING      # 移除中
}

# 信号定义
signal decoration_placed(decoration_id: String, position: Vector2)
signal decoration_moved(decoration_id: String, old_pos: Vector2, new_pos: Vector2)
signal decoration_removed(decoration_id: String)
signal decoration_unlocked(decoration_id: String)
signal placement_mode_changed(mode: PlacementMode)
signal farm_beauty_changed(new_value: int)

# 当前放置模式
var current_mode: PlacementMode = PlacementMode.NONE
var selected_decoration_id: String = ""
var selected_instance_id: String = ""

# 玩家装饰数据
var owned_decorations: Dictionary = {}  # {decoration_id: quantity}
var placed_decorations: Array = []       # [{instance_id, decoration_id, position, rotation}]
var unlocked_decorations: Array = []     # 已解锁的装饰ID列表

# 农场美观度
var farm_beauty: int = 0

# 网格设置
const GRID_SIZE: int = 32
const FARM_WIDTH: int = 20   # 网格宽度
const FARM_HEIGHT: int = 15  # 网格高度

# 占用网格
var occupied_grid: Array = []  # 2D数组，标记已占用的格子


func _ready() -> void:
	_init_grid()
	_load_decoration_data()
	_connect_signals()


## 初始化网格
func _init_grid() -> void:
	occupied_grid.clear()
	for x in range(FARM_WIDTH):
		var row: Array = []
		for y in range(FARM_HEIGHT):
			row.append(false)
		occupied_grid.append(row)


## 加载装饰数据
func _load_decoration_data() -> void:
	if SaveManager:
		var save_data: Dictionary = SaveManager.load_game()
		if save_data.has("decorations"):
			var deco_data: Dictionary = save_data["decorations"]
			owned_decorations = deco_data.get("owned", {})
			placed_decorations = deco_data.get("placed", [])
			unlocked_decorations = deco_data.get("unlocked", [])
			farm_beauty = deco_data.get("beauty", 0)
			_rebuild_grid()
		else:
			_init_default_decorations()
	else:
		_init_default_decorations()


## 初始化默认装饰
func _init_default_decorations() -> void:
	# 新玩家默认解锁一些基础装饰
	unlocked_decorations = [
		"wooden_fence",
		"stone_path",
		"flower_pot",
		"small_lamp"
	]
	# 赠送一些初始装饰
	owned_decorations = {
		"wooden_fence": 10,
		"stone_path": 20,
		"flower_pot": 3
	}


## 重建占用网格
func _rebuild_grid() -> void:
	_init_grid()
	for deco in placed_decorations:
		var pos: Vector2 = deco.get("position", Vector2.ZERO)
		var deco_id: String = deco.get("decoration_id", "")
		var deco_def: Dictionary = DecorationData.get_decoration(deco_id)
		var size: Vector2i = deco_def.get("size", Vector2i(1, 1))
		_mark_grid(pos, size, true)


## 连接信号
func _connect_signals() -> void:
	if EventBus:
		EventBus.item_added.connect(_on_item_added)


## 保存装饰数据
func _save_decoration_data() -> void:
	if SaveManager and GameManager:
		var player_data: Dictionary = GameManager.player_data.duplicate(true)
		player_data["decorations"] = {
			"owned": owned_decorations,
			"placed": placed_decorations,
			"unlocked": unlocked_decorations,
			"beauty": farm_beauty
		}
		SaveManager.save_game(player_data)


# ==================== 放置模式控制 ====================

## 进入放置模式
func enter_placement_mode(decoration_id: String) -> bool:
	if not unlocked_decorations.has(decoration_id):
		if EventBus:
			EventBus.notify_warning("该装饰尚未解锁")
		return false

	var owned: int = owned_decorations.get(decoration_id, 0)
	if owned <= 0:
		if EventBus:
			EventBus.notify_warning("没有足够的装饰物")
		return false

	current_mode = PlacementMode.PLACING
	selected_decoration_id = decoration_id
	selected_instance_id = ""
	placement_mode_changed.emit(current_mode)
	return true


## 进入移动模式
func enter_move_mode(instance_id: String) -> bool:
	var deco := _find_placed_decoration(instance_id)
	if deco.is_empty():
		return false

	current_mode = PlacementMode.MOVING
	selected_instance_id = instance_id
	selected_decoration_id = deco.get("decoration_id", "")
	placement_mode_changed.emit(current_mode)
	return true


## 进入移除模式
func enter_remove_mode() -> void:
	current_mode = PlacementMode.REMOVING
	selected_decoration_id = ""
	selected_instance_id = ""
	placement_mode_changed.emit(current_mode)


## 退出放置模式
func exit_placement_mode() -> void:
	current_mode = PlacementMode.NONE
	selected_decoration_id = ""
	selected_instance_id = ""
	placement_mode_changed.emit(current_mode)


## 获取当前放置模式
func get_placement_mode() -> PlacementMode:
	return current_mode


# ==================== 放置操作 ====================

## 放置装饰
func place_decoration(grid_position: Vector2i) -> bool:
	if current_mode != PlacementMode.PLACING:
		return false

	if selected_decoration_id.is_empty():
		return false

	var deco_def: Dictionary = DecorationData.get_decoration(selected_decoration_id)
	if deco_def.is_empty():
		return false

	var size: Vector2i = deco_def.get("size", Vector2i(1, 1))

	# 检查是否可以放置
	if not _can_place_at(grid_position, size):
		if EventBus:
			EventBus.notify_warning("无法在此位置放置")
		return false

	# 扣除库存
	owned_decorations[selected_decoration_id] -= 1
	if owned_decorations[selected_decoration_id] <= 0:
		owned_decorations.erase(selected_decoration_id)

	# 创建实例
	var instance_id: String = _generate_instance_id()
	var world_pos: Vector2 = Vector2(grid_position) * GRID_SIZE

	var placed_data: Dictionary = {
		"instance_id": instance_id,
		"decoration_id": selected_decoration_id,
		"position": world_pos,
		"grid_position": grid_position,
		"rotation": 0
	}
	placed_decorations.append(placed_data)

	# 标记网格占用
	_mark_grid(world_pos, size, true)

	# 更新美观度
	_update_farm_beauty()

	decoration_placed.emit(selected_decoration_id, world_pos)
	_save_decoration_data()

	# 如果没有更多库存，退出放置模式
	if owned_decorations.get(selected_decoration_id, 0) <= 0:
		exit_placement_mode()

	return true


## 移动装饰
func move_decoration(new_grid_position: Vector2i) -> bool:
	if current_mode != PlacementMode.MOVING:
		return false

	var deco := _find_placed_decoration(selected_instance_id)
	if deco.is_empty():
		return false

	var deco_def: Dictionary = DecorationData.get_decoration(deco.get("decoration_id", ""))
	var size: Vector2i = deco_def.get("size", Vector2i(1, 1))
	var old_pos: Vector2 = deco.get("position", Vector2.ZERO)
	var old_grid: Vector2i = deco.get("grid_position", Vector2i.ZERO)

	# 先释放旧位置
	_mark_grid(old_pos, size, false)

	# 检查新位置是否可用
	if not _can_place_at(new_grid_position, size):
		# 恢复旧位置占用
		_mark_grid(old_pos, size, true)
		if EventBus:
			EventBus.notify_warning("无法移动到此位置")
		return false

	# 更新位置
	var new_world_pos: Vector2 = Vector2(new_grid_position) * GRID_SIZE
	deco["position"] = new_world_pos
	deco["grid_position"] = new_grid_position

	# 标记新位置占用
	_mark_grid(new_world_pos, size, true)

	decoration_moved.emit(selected_instance_id, old_pos, new_world_pos)
	_save_decoration_data()

	return true


## 移除装饰
func remove_decoration(instance_id: String) -> bool:
	var deco := _find_placed_decoration(instance_id)
	if deco.is_empty():
		return false

	var decoration_id: String = deco.get("decoration_id", "")
	var pos: Vector2 = deco.get("position", Vector2.ZERO)
	var deco_def: Dictionary = DecorationData.get_decoration(decoration_id)
	var size: Vector2i = deco_def.get("size", Vector2i(1, 1))

	# 释放网格
	_mark_grid(pos, size, false)

	# 从已放置列表移除
	placed_decorations.erase(deco)

	# 返还库存
	owned_decorations[decoration_id] = owned_decorations.get(decoration_id, 0) + 1

	# 更新美观度
	_update_farm_beauty()

	decoration_removed.emit(instance_id)
	_save_decoration_data()

	return true


# ==================== 查询方法 ====================

## 获取已拥有的装饰
func get_owned_decorations() -> Dictionary:
	return owned_decorations.duplicate()


## 获取已放置的装饰
func get_placed_decorations() -> Array:
	return placed_decorations.duplicate()


## 获取已解锁的装饰
func get_unlocked_decorations() -> Array:
	return unlocked_decorations.duplicate()


## 获取农场美观度
func get_farm_beauty() -> int:
	return farm_beauty


## 检查装饰是否已解锁
func is_decoration_unlocked(decoration_id: String) -> bool:
	return unlocked_decorations.has(decoration_id)


## 获取指定位置的装饰
func get_decoration_at(grid_position: Vector2i) -> Dictionary:
	for deco in placed_decorations:
		var deco_grid: Vector2i = deco.get("grid_position", Vector2i.ZERO)
		var deco_def: Dictionary = DecorationData.get_decoration(deco.get("decoration_id", ""))
		var size: Vector2i = deco_def.get("size", Vector2i(1, 1))

		if grid_position.x >= deco_grid.x and grid_position.x < deco_grid.x + size.x:
			if grid_position.y >= deco_grid.y and grid_position.y < deco_grid.y + size.y:
				return deco

	return {}


# ==================== 解锁和购买 ====================

## 解锁装饰
func unlock_decoration(decoration_id: String) -> bool:
	if unlocked_decorations.has(decoration_id):
		return false

	var deco_def: Dictionary = DecorationData.get_decoration(decoration_id)
	if deco_def.is_empty():
		return false

	unlocked_decorations.append(decoration_id)
	decoration_unlocked.emit(decoration_id)
	_save_decoration_data()

	if EventBus:
		EventBus.notify_success("解锁装饰: " + deco_def.get("name", decoration_id))

	return true


## 添加装饰到库存
func add_decoration(decoration_id: String, quantity: int = 1) -> void:
	if quantity <= 0:
		return

	owned_decorations[decoration_id] = owned_decorations.get(decoration_id, 0) + quantity

	# 自动解锁
	if not unlocked_decorations.has(decoration_id):
		unlock_decoration(decoration_id)

	_save_decoration_data()


## 购买装饰
func buy_decoration(decoration_id: String, quantity: int = 1) -> bool:
	var deco_def: Dictionary = DecorationData.get_decoration(decoration_id)
	if deco_def.is_empty():
		return false

	var price: int = deco_def.get("price", 0) * quantity

	if not GameManager:
		return false

	if GameManager.get_gold() < price:
		if EventBus:
			EventBus.notify_warning("金币不足")
		return false

	if GameManager.spend_gold(price):
		add_decoration(decoration_id, quantity)
		if EventBus:
			EventBus.notify_success("购买成功: %s x%d" % [deco_def.get("name", ""), quantity])
		return true

	return false


# ==================== 内部方法 ====================

## 检查是否可以在指定位置放置
func _can_place_at(grid_position: Vector2i, size: Vector2i) -> bool:
	# 检查边界
	if grid_position.x < 0 or grid_position.y < 0:
		return false
	if grid_position.x + size.x > FARM_WIDTH:
		return false
	if grid_position.y + size.y > FARM_HEIGHT:
		return false

	# 检查占用
	for x in range(size.x):
		for y in range(size.y):
			var check_x: int = grid_position.x + x
			var check_y: int = grid_position.y + y
			if occupied_grid[check_x][check_y]:
				return false

	return true


## 标记网格占用状态
func _mark_grid(world_pos: Vector2, size: Vector2i, occupied: bool) -> void:
	var grid_pos: Vector2i = Vector2i(world_pos / GRID_SIZE)

	for x in range(size.x):
		for y in range(size.y):
			var mark_x: int = grid_pos.x + x
			var mark_y: int = grid_pos.y + y
			if mark_x >= 0 and mark_x < FARM_WIDTH and mark_y >= 0 and mark_y < FARM_HEIGHT:
				occupied_grid[mark_x][mark_y] = occupied


## 查找已放置的装饰
func _find_placed_decoration(instance_id: String) -> Dictionary:
	for deco in placed_decorations:
		if deco.get("instance_id", "") == instance_id:
			return deco
	return {}


## 生成实例ID
func _generate_instance_id() -> String:
	return "deco_%d_%d" % [Time.get_unix_time_from_system(), randi() % 10000]


## 更新农场美观度
func _update_farm_beauty() -> void:
	var total_beauty: int = 0

	for deco in placed_decorations:
		var deco_id: String = deco.get("decoration_id", "")
		var deco_def: Dictionary = DecorationData.get_decoration(deco_id)
		total_beauty += deco_def.get("beauty", 0)

	farm_beauty = total_beauty
	farm_beauty_changed.emit(farm_beauty)


## 物品添加事件（用于从商店购买）
func _on_item_added(item_id: String, quantity: int) -> void:
	# 检查是否是装饰物品
	if item_id.begins_with("deco_"):
		var decoration_id: String = item_id.substr(5)  # 去掉 "deco_" 前缀
		add_decoration(decoration_id, quantity)
