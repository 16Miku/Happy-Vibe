## game_manager.gd
## 游戏核心管理器 - 管理玩家数据、游戏状态和核心游戏逻辑
## 作为 AutoLoad 单例运行
extends Node

# 游戏状态枚举
enum GameState {
	MENU,      # 主菜单
	PLAYING,   # 游戏中
	PAUSED,    # 暂停
	LOADING    # 加载中
}

# 信号定义
signal energy_changed(current: int, max_energy: int)
signal exp_changed(current: int, needed: int)
signal level_up(new_level: int)
signal gold_changed(amount: int)
signal diamonds_changed(amount: int)
signal game_state_changed(new_state: GameState)
signal player_data_loaded()
signal player_data_saved()

# 当前游戏状态
var current_state: GameState = GameState.MENU

# 玩家数据
var player_data: Dictionary = {}
var is_initialized := false

# VibeClient 引用
var vibe_client: Node = null

# 常量配置
const BASE_EXP_MULTIPLIER: float = 100.0
const EXP_GROWTH_RATE: float = 0.1
const MAX_LEVEL: int = 100
const BASE_MAX_ENERGY: int = 1000
const ENERGY_PER_LEVEL: int = 100

# 初始化
func _ready() -> void:
	load_player_data()
	is_initialized = true
	_setup_vibe_client()


## 加载玩家数据
func load_player_data() -> bool:
	if SaveManager:
		var data: Dictionary = SaveManager.load_game()
		if not data.is_empty():
			player_data = data
			player_data_loaded.emit()
			return true

	# 如果没有存档，创建默认数据
	player_data = _create_default_player()
	player_data_loaded.emit()
	return false


## 保存玩家数据
func save_player_data() -> bool:
	if SaveManager:
		var success: bool = SaveManager.save_game(player_data)
		if success:
			player_data_saved.emit()
		return success
	return false


## 创建默认玩家数据
func _create_default_player() -> Dictionary:
	return {
		"username": "Player",
		"level": 1,
		"exp": 0,
		"energy": 100,
		"max_energy": BASE_MAX_ENERGY,
		"gold": 500,
		"diamonds": 0,
		"consecutive_days": 0,
		"last_login": Time.get_unix_time_from_system(),
		"created_at": Time.get_unix_time_from_system(),
		"farm": {
			"plots": [],
			"buildings": [],
			"decorations": []
		},
		"inventory": [],
		"achievements": [],
		"titles": [],
		"equipped_title": "",
		"stats": {
			"total_energy_earned": 0,
			"total_coding_time": 0,
			"total_flow_time": 0,
			"crops_harvested": 0,
			"buildings_built": 0,
			"achievements_unlocked": 0,
			"flow_sessions": 0
		},
		"settings": {
			"music_volume": 1.0,
			"sfx_volume": 1.0,
			"notifications_enabled": true
		}
	}


## 切换游戏状态
func set_game_state(new_state: GameState) -> void:
	if current_state != new_state:
		current_state = new_state
		game_state_changed.emit(new_state)

		match new_state:
			GameState.PAUSED:
				get_tree().paused = true
			GameState.PLAYING:
				get_tree().paused = false
			_:
				pass


## 获取当前游戏状态
func get_game_state() -> GameState:
	return current_state


## 是否正在游戏中
func is_playing() -> bool:
	return current_state == GameState.PLAYING


# ==================== 能量系统 ====================

## 添加能量
func add_energy(amount: int) -> void:
	if amount <= 0:
		return

	var old_energy: int = player_data.get("energy", 0)
	var max_energy: int = player_data.get("max_energy", BASE_MAX_ENERGY)
	var new_energy: int = mini(old_energy + amount, max_energy)

	player_data["energy"] = new_energy
	player_data["stats"]["total_energy_earned"] = player_data["stats"].get("total_energy_earned", 0) + amount

	energy_changed.emit(new_energy, max_energy)

	# 通知事件总线
	if EventBus:
		EventBus.emit_signal("energy_updated", new_energy, max_energy)


## 消耗能量
func spend_energy(amount: int) -> bool:
	if amount <= 0:
		return false

	var current_energy: int = player_data.get("energy", 0)
	if current_energy < amount:
		return false

	player_data["energy"] = current_energy - amount
	var max_energy: int = player_data.get("max_energy", BASE_MAX_ENERGY)
	energy_changed.emit(player_data["energy"], max_energy)

	if EventBus:
		EventBus.emit_signal("energy_updated", player_data["energy"], max_energy)

	return true


## 获取当前能量
func get_energy() -> int:
	return player_data.get("energy", 0)


## 获取最大能量
func get_max_energy() -> int:
	return player_data.get("max_energy", BASE_MAX_ENERGY)


# ==================== 经验与等级系统 ====================

## 添加经验值
func add_exp(amount: int) -> void:
	if amount <= 0:
		return

	var current_level: int = player_data.get("level", 1)
	if current_level >= MAX_LEVEL:
		return

	player_data["exp"] = player_data.get("exp", 0) + amount

	# 检查是否升级
	var exp_needed: int = calculate_exp_needed(current_level)
	while player_data["exp"] >= exp_needed and current_level < MAX_LEVEL:
		player_data["exp"] -= exp_needed
		current_level += 1
		player_data["level"] = current_level
		_on_level_up(current_level)
		exp_needed = calculate_exp_needed(current_level)

	exp_changed.emit(player_data["exp"], exp_needed)


## 计算升级所需经验
## 公式: EXP = 100 * level * (1 + level / 10)
func calculate_exp_needed(level: int) -> int:
	return int(BASE_EXP_MULTIPLIER * level * (1.0 + level * EXP_GROWTH_RATE))


## 升级时的处理
func _on_level_up(new_level: int) -> void:
	# 增加最大能量
	player_data["max_energy"] = BASE_MAX_ENERGY + (new_level * ENERGY_PER_LEVEL)

	# 发送升级信号
	level_up.emit(new_level)

	# 通知事件总线
	if EventBus:
		EventBus.emit_signal("player_leveled_up", new_level)

	# 自动保存
	save_player_data()


## 获取当前等级
func get_level() -> int:
	return player_data.get("level", 1)


## 获取当前经验
func get_exp() -> int:
	return player_data.get("exp", 0)


## 获取升级所需经验
func get_exp_needed() -> int:
	return calculate_exp_needed(get_level())


## 获取经验进度百分比
func get_exp_progress() -> float:
	var needed: int = get_exp_needed()
	if needed <= 0:
		return 1.0
	return float(get_exp()) / float(needed)


# ==================== 货币系统 ====================

## 添加金币
func add_gold(amount: int) -> void:
	if amount <= 0:
		return

	player_data["gold"] = player_data.get("gold", 0) + amount
	gold_changed.emit(player_data["gold"])

	if EventBus:
		EventBus.emit_signal("gold_updated", player_data["gold"])


## 消耗金币
func spend_gold(amount: int) -> bool:
	if amount <= 0:
		return false

	var current_gold: int = player_data.get("gold", 0)
	if current_gold < amount:
		return false

	player_data["gold"] = current_gold - amount
	gold_changed.emit(player_data["gold"])

	if EventBus:
		EventBus.emit_signal("gold_updated", player_data["gold"])

	return true


## 获取金币数量
func get_gold() -> int:
	return player_data.get("gold", 0)


## 添加钻石
func add_diamonds(amount: int) -> void:
	if amount <= 0:
		return

	player_data["diamonds"] = player_data.get("diamonds", 0) + amount
	diamonds_changed.emit(player_data["diamonds"])

	if EventBus:
		EventBus.emit_signal("diamonds_updated", player_data["diamonds"])


## 消耗钻石
func spend_diamonds(amount: int) -> bool:
	if amount <= 0:
		return false

	var current_diamonds: int = player_data.get("diamonds", 0)
	if current_diamonds < amount:
		return false

	player_data["diamonds"] = current_diamonds - amount
	diamonds_changed.emit(player_data["diamonds"])

	if EventBus:
		EventBus.emit_signal("diamonds_updated", player_data["diamonds"])

	return true


## 获取钻石数量
func get_diamonds() -> int:
	return player_data.get("diamonds", 0)


# ==================== 统计系统 ====================

## 更新统计数据
func update_stat(stat_name: String, value: int) -> void:
	if not player_data.has("stats"):
		player_data["stats"] = {}

	player_data["stats"][stat_name] = player_data["stats"].get(stat_name, 0) + value


## 获取统计数据
func get_stat(stat_name: String) -> int:
	if not player_data.has("stats"):
		return 0
	return player_data["stats"].get(stat_name, 0)


## 记录编码时间
func record_coding_time(minutes: int) -> void:
	update_stat("total_coding_time", minutes)


## 记录心流时间
func record_flow_time(minutes: int) -> void:
	update_stat("total_flow_time", minutes)


# ==================== VibeClient 集成 ====================

## 初始化 VibeClient
func _setup_vibe_client() -> void:
	# 查找 VibeClient 节点
	vibe_client = get_node_or_null("/root/VibeClient")

	if vibe_client:
		print("[GameManager] VibeClient 已找到，开始连接")
		# 连接信号
		vibe_client.connection_status_changed.connect(_on_vibe_connection_changed)
		vibe_client.player_data_received.connect(_on_vibe_player_data)
		vibe_client.energy_received.connect(_on_vibe_energy_received)
		vibe_client.flow_state_changed.connect(_on_vibe_flow_state_changed)
		vibe_client.farm_data_received.connect(_on_vibe_farm_data)
		vibe_client.achievements_received.connect(_on_vibe_achievements)
	else:
		print("[GameManager] VibeClient 未找到，将使用本地存档")


## VibeClient 连接状态变化
func _on_vibe_connection_changed(connected: bool) -> void:
	if connected:
		print("[GameManager] 已连接到 VibeHub")
		# 连接成功后同步玩家数据
		vibe_client.call("get_player")
	else:
		print("[GameManager] VibeHub 连接断开")


## VibeClient 玩家数据接收
func _on_vibe_player_data(data: Dictionary) -> void:
	print("[GameManager] 从 VibeHub 接收玩家数据")
	# 更新玩家数据
	player_data = data.duplicate(true)
	player_data_loaded.emit()


## VibeClient 能量接收
func _on_vibe_energy_received(energy: int, breakdown: Dictionary) -> void:
	print("[GameManager] 收到能量: ", energy, " 细分: ", breakdown)
	add_energy(energy)


## VibeClient 心流状态变化
func _on_vibe_flow_state_changed(is_flow: bool) -> void:
	print("[GameManager] 心流状态: ", "进入" if is_flow else "退出")
	if is_flow:
		EventBus.flow_state_entered.emit()


## VibeClient 农场数据接收
func _on_vibe_farm_data(data: Dictionary) -> void:
	print("[GameManager] 收到农场数据")
	# 更新农场数据
	player_data["farm"] = data.duplicate(true)


## VibeClient 成就数据接收
func _on_vibe_achievements(achievements: Array) -> void:
	print("[GameManager] 收到成就数据: ", achievements.size(), " 个")
	player_data["achievements"] = achievements.duplicate(true)


## 同步玩家数据到 VibeHub
func sync_to_vibe() -> void:
	if vibe_client and vibe_client.has_method("update_player"):
		vibe_client.call("update_player", player_data.duplicate(true))
	else:
		print("[GameManager] VibeClient 不可用，无法同步数据")


# ==================== 工具方法 ====================

## 获取玩家用户名
func get_username() -> String:
	return player_data.get("username", "Player")


## 设置玩家用户名
func set_username(new_name: String) -> void:
	player_data["username"] = new_name


## 获取连续登录天数
func get_consecutive_days() -> int:
	return player_data.get("consecutive_days", 0)


## 更新登录状态
func update_login_status() -> void:
	var last_login: int = player_data.get("last_login", 0)
	var current_time: int = int(Time.get_unix_time_from_system())
	var one_day: int = 86400  # 24小时的秒数

	var days_since_last: int = (current_time - last_login) / one_day

	if days_since_last == 1:
		# 连续登录
		player_data["consecutive_days"] = player_data.get("consecutive_days", 0) + 1
	elif days_since_last > 1:
		# 断签，重置连续天数
		player_data["consecutive_days"] = 1
	# days_since_last == 0 表示今天已经登录过，不更新

	player_data["last_login"] = current_time


## 获取玩家数据的只读副本
func get_player_data() -> Dictionary:
	return player_data.duplicate(true)
