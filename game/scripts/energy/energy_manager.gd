## energy_manager.gd
## 能量管理器 - 管理游戏内的能量系统
## 作为 AutoLoad 单例运行
extends Node

# ==================== 常量配置 ====================

## 默认最大能量
const DEFAULT_MAX_ENERGY: int = 1000

## 每级增加的能量
const ENERGY_PER_LEVEL: int = 100

## 能量恢复速率（每分钟）
const DEFAULT_REGEN_RATE: float = 1.0

# ==================== 能量数据 ====================

## 当前能量值
var current_energy: int = 0

## 最大能量值
var max_energy: int = DEFAULT_MAX_ENERGY

## 能量恢复速率（每分钟恢复量）
var energy_regen_rate: float = DEFAULT_REGEN_RATE

## 上次恢复时间戳
var last_regen_time: int = 0

## 能量恢复定时器
var regen_timer: Timer

# ==================== 信号定义 ====================

## 能量变化信号（新值，旧值）
signal energy_changed(new_value: int, old_value: int)

## 能量奖励信号（数量，来源）
signal energy_awarded(amount: int, source: String)

## 能量消耗信号（数量，成功标志）
signal energy_consumed(amount: int, success: bool)

## 能量达到上限信号
signal energy_max_reached()

## 能量耗尽信号
signal energy_depleted()

## 能量恢复信号（恢复数量）
signal energy_regened(amount: int)

# ==================== 初始化 ====================

func _ready() -> void:
	"""初始化能量管理器"""
	_setup_regen_timer()
	_load_energy_from_game_manager()
	print("[EnergyManager] 能量管理器已初始化，当前能量：", current_energy, "/", max_energy)


## 设置能量恢复定时器
func _setup_regen_timer() -> void:
	"""设置能量恢复定时器"""
	regen_timer = Timer.new()
	regen_timer.wait_time = 60.0  # 每分钟恢复一次
	regen_timer.autostart = true
	regen_timer.timeout.connect(_on_regen_tick)
	add_child(regen_timer)


## 从游戏管理器加载能量数据
func _load_energy_from_game_manager() -> void:
	"""从 GameManager 加载能量数据"""
	if GameManager and GameManager.has_method("get_energy"):
		current_energy = GameManager.get_energy()
		max_energy = GameManager.get_max_energy()
		last_regen_time = Time.get_unix_time_from_system()


# ==================== 能量管理核心方法 ====================

## 添加能量
func add_energy(amount: int, source: String = "") -> bool:
	"""添加能量，返回是否成功添加

	Args:
		amount: 能量数量
		source: 能量来源（如 "vibe_coding", "reward", "item" 等）

	Returns:
		bool: 是否成功添加（达到上限时返回 true 但实际未添加超额部分）
	"""
	if amount <= 0:
		push_warning("[EnergyManager] 尝试添加无效能量数量：", amount)
		return false

	var old_energy: int = current_energy
	var was_full: bool = current_energy >= max_energy
	var new_energy: int = mini(current_energy + amount, max_energy)

	current_energy = new_energy

	# 触发能量变化信号
	energy_changed.emit(current_energy, old_energy)

	# 触发能量奖励信号
	energy_awarded.emit(amount, source)

	# 如果从非满状态变为满状态
	if not was_full and current_energy >= max_energy:
		energy_max_reached.emit()
		print("[EnergyManager] 能量已达到上限：", max_energy)

	# 同步到 GameManager
	_sync_to_game_manager()

	# 通知 EventBus
	if EventBus:
		EventBus.energy_updated.emit(current_energy, max_energy)

	var added: int = current_energy - old_energy
	print("[EnergyManager] 添加能量：+", added, " (来源：", source, ") 当前能量：", current_energy, "/", max_energy)
	return true


## 消耗能量
func consume_energy(amount: int, source: String = "") -> bool:
	"""消耗能量，返回是否成功

	Args:
		amount: 能量数量
		source: 消耗来源（用于日志）

	Returns:
		bool: 是否成功消耗
	"""
	if amount <= 0:
		push_warning("[EnergyManager] 尝试消耗无效能量数量：", amount)
		return false

	var old_energy: int = current_energy
	var was_depleted: bool = current_energy == 0

	# 检查能量是否足够
	if current_energy < amount:
		print("[EnergyManager] 能量不足！需要：", amount, "，当前：", current_energy)
		energy_consumed.emit(amount, false)
		return false

	# 消耗能量
	current_energy -= amount

	# 触发能量变化信号
	energy_changed.emit(current_energy, old_energy)

	# 触发能量消耗信号
	energy_consumed.emit(amount, true)

	# 如果从非耗尽状态变为耗尽状态
	if not was_depleted and current_energy == 0:
		energy_depleted.emit()
		print("[EnergyManager] 能量已耗尽！")

	# 同步到 GameManager
	_sync_to_game_manager()

	# 通知 EventBus
	if EventBus:
		EventBus.energy_updated.emit(current_energy, max_energy)

	print("[EnergyManager] 消耗能量：-", amount, " (来源：", source, ") 当前能量：", current_energy, "/", max_energy)
	return true


## 设置当前能量（直接设置，不考虑上限检查）
func set_energy(value: int) -> void:
	"""直接设置能量值（用于加载存档）

	Args:
		value: 新的能量值
	"""
	var old_energy: int = current_energy
	current_energy = clampi(value, 0, max_energy)

	energy_changed.emit(current_energy, old_energy)

	if EventBus:
		EventBus.energy_updated.emit(current_energy, max_energy)


## 设置最大能量
func set_max_energy(new_max: int) -> void:
	"""设置最大能量值

	Args:
		new_max: 新的最大能量值
	"""
	if new_max <= 0:
		push_warning("[EnergyManager] 尝试设置无效的最大能量：", new_max)
		return

	var old_max: int = max_energy
	max_energy = new_max

	# 如果当前能量超过新的最大值，截断
	if current_energy > max_energy:
		var old_energy: int = current_energy
		current_energy = max_energy
		energy_changed.emit(current_energy, old_energy)

	if EventBus:
		EventBus.energy_updated.emit(current_energy, max_energy)

	print("[EnergyManager] 最大能量更新：", old_max, " -> ", max_energy)


## 检查是否能够支付指定能量
func can_afford(amount: int) -> bool:
	"""检查是否有足够的能量

	Args:
		amount: 需要的能量数量

	Returns:
		bool: 是否有足够的能量
	"""
	return current_energy >= amount


## 获取当前能量值
func get_energy() -> int:
	"""获取当前能量值

	Returns:
		int: 当前能量
	"""
	return current_energy


## 获取最大能量值
func get_max_energy() -> int:
	"""获取最大能量值

	Returns:
		int: 最大能量
	"""
	return max_energy


## 获取能量百分比（0.0 ~ 1.0）
func get_energy_percentage() -> float:
	"""获取能量百分比

	Returns:
		float: 能量百分比（0.0 ~ 1.0）
	"""
	if max_energy <= 0:
		return 0.0
	return float(current_energy) / float(max_energy)


## 获取能量恢复百分比（0.0 ~ 1.0）
func get_energy_regen_percentage() -> float:
	"""获取能量恢复进度百分比

	Returns:
		float: 恢复进度（0.0 ~ 1.0）
	"""
	return get_energy_percentage()


## 恢复能量（手动调用）
func regen_energy() -> void:
	"""立即恢复一次能量"""
	var energy_to_regen: int = int(energy_regen_rate)
	if energy_to_regen <= 0:
		return

	# 计算可恢复的能量量
	var can_regen: int = max_energy - current_energy
	if can_regen <= 0:
		return

	var actual_regen: int = mini(energy_to_regen, can_regen)

	if actual_regen > 0:
		add_energy(actual_regen, "regen")


# ==================== 私有方法 ====================

## 能量恢复定时器回调
func _on_regen_tick() -> void:
	"""定时恢复能量"""
	regen_energy()


## 同步到 GameManager
func _sync_to_game_manager() -> void:
	"""同步能量数据到 GameManager"""
	if GameManager and GameManager.has_method("get_player_data"):
		# 更新 GameManager 中的能量数据
		GameManager.player_data["energy"] = current_energy
		GameManager.player_data["max_energy"] = max_energy


# ==================== 游戏事件处理 ====================

## 从 VibeClient 接收能量
func on_vibe_energy_received(energy: int, breakdown: Dictionary) -> void:
	"""从 VibeHub 接收能量

	Args:
		energy: 能量数量
		breakdown: 能量细分数据（基础、时间、质量、心流）
	"""
	print("[EnergyManager] 从 VibeHub 接收能量：", energy)
	add_energy(energy, "vibe_coding")


## 玩家升级处理
func on_player_leveled_up(new_level: int) -> void:
	"""玩家升级时增加最大能量

	Args:
		new_level: 新等级
	"""
	var new_max: int = DEFAULT_MAX_ENERGY + (new_level * ENERGY_PER_LEVEL)
	print("[EnergyManager] 玩家升级到等级 ", new_level, "，最大能量：", max_energy, " -> ", new_max)
	set_max_energy(new_max)


# ==================== 调试方法 ====================

## 重置能量（仅用于开发调试）
func debug_reset_energy() -> void:
	"""重置能量为最大值（开发调试用）"""
	current_energy = max_energy
	energy_changed.emit(current_energy, 0)
	if EventBus:
		EventBus.energy_updated.emit(current_energy, max_energy)
	print("[EnergyManager] 能量已重置为：", current_energy)


## 调试信息
func debug_print_info() -> void:
	"""打印调试信息"""
	print("[EnergyManager] 调试信息：")
	print("  当前能量：", current_energy)
	print("  最大能量：", max_energy)
	print("  能量百分比：", get_energy_percentage() * 100, "%")
	print("  恢复速率：", energy_regen_rate, "/分钟")
