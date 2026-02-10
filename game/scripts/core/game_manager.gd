extends Node
## 游戏管理器 - 全局单例
## 管理玩家数据、游戏状态和存档

signal energy_changed(value: int)
signal gold_changed(value: int)
signal exp_changed(value: int)
signal level_up(new_level: int)

const SAVE_PATH := "user://player.dat"
const BASE_EXP_PER_LEVEL := 100

var player_data: Dictionary = {}
var is_initialized := false


func _ready() -> void:
	load_player_data()
	is_initialized = true


func load_player_data() -> void:
	"""加载玩家数据"""
	if FileAccess.file_exists(SAVE_PATH):
		var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
		if file:
			var data = file.get_var()
			if data is Dictionary:
				player_data = data
			file.close()

	if player_data.is_empty():
		player_data = create_default_player()


func create_default_player() -> Dictionary:
	"""创建默认玩家数据"""
	return {
		"username": "Player",
		"level": 1,
		"exp": 0,
		"energy": 100,
		"max_energy": 1000,
		"gold": 500,
		"diamonds": 0,
		"farm": {
			"plots": [],
			"buildings": []
		},
		"achievements": [],
		"stats": {
			"total_energy_earned": 0,
			"total_coding_time": 0,
			"crops_harvested": 0,
			"flow_sessions": 0
		}
	}


func save_player_data() -> void:
	"""保存玩家数据"""
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_var(player_data)
		file.close()


func add_energy(amount: int) -> void:
	"""添加能量"""
	var old_energy: int = player_data.get("energy", 0)
	var max_energy: int = player_data.get("max_energy", 1000)
	player_data["energy"] = mini(old_energy + amount, max_energy)
	player_data["stats"]["total_energy_earned"] += amount
	energy_changed.emit(player_data["energy"])
	save_player_data()


func spend_energy(amount: int) -> bool:
	"""消耗能量，返回是否成功"""
	var current: int = player_data.get("energy", 0)
	if current >= amount:
		player_data["energy"] = current - amount
		energy_changed.emit(player_data["energy"])
		save_player_data()
		return true
	return false


func add_gold(amount: int) -> void:
	"""添加金币"""
	player_data["gold"] = player_data.get("gold", 0) + amount
	gold_changed.emit(player_data["gold"])
	save_player_data()


func spend_gold(amount: int) -> bool:
	"""消耗金币，返回是否成功"""
	var current: int = player_data.get("gold", 0)
	if current >= amount:
		player_data["gold"] = current - amount
		gold_changed.emit(player_data["gold"])
		save_player_data()
		return true
	return false


func add_exp(amount: int) -> void:
	"""添加经验值"""
	player_data["exp"] = player_data.get("exp", 0) + amount
	var exp_needed := calculate_exp_needed(player_data.get("level", 1))

	while player_data["exp"] >= exp_needed:
		player_data["exp"] -= exp_needed
		_level_up()
		exp_needed = calculate_exp_needed(player_data["level"])

	exp_changed.emit(player_data["exp"])
	save_player_data()


func _level_up() -> void:
	"""升级"""
	player_data["level"] = player_data.get("level", 1) + 1
	player_data["max_energy"] = 1000 + (player_data["level"] * 100)
	level_up.emit(player_data["level"])


func calculate_exp_needed(level: int) -> int:
	"""计算升级所需经验"""
	return int(BASE_EXP_PER_LEVEL * level * (1.0 + level / 10.0))


func get_energy() -> int:
	return player_data.get("energy", 0)


func get_max_energy() -> int:
	return player_data.get("max_energy", 1000)


func get_gold() -> int:
	return player_data.get("gold", 0)


func get_level() -> int:
	return player_data.get("level", 1)


func get_exp() -> int:
	return player_data.get("exp", 0)
