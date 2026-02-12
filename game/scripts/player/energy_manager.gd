extends Node
## 能量管理器
## 负责管理玩家的能量系统，包括能量获取、消耗、恢复和心流状态加成

signal energy_changed(current_energy: int, max_energy: int)
signal energy_insufficient(required: int, current: int)
signal energy_recovered(amount: int)
signal flow_state_changed(is_flow: bool, bonus_multiplier: float)
signal daily_energy_reset()

# ==================== 配置常量 ====================

const BASE_MAX_ENERGY: int = 1000
const ENERGY_PER_LEVEL: int = 100
const FLOW_ENERGY_MULTIPLIER: float = 2.0  # 心流状态下能量获取翻倍
const ENERGY_REGEN_DELAY: float = 300.0  # 能量恢复延迟（秒）
const AUTO_SAVE_INTERVAL: float = 60.0  # 自动保存间隔（秒）

# ==================== 成员变量 ====================

var _current_energy: int = 100
var _max_energy: int = BASE_MAX_ENERGY
var _is_in_flow: bool = false
var _energy_regen_timer: Timer
var _auto_save_timer: Timer
var _vibe_client: Node = null
var _energy_buffer: int = 0  # 缓冲区，用于存储从 VibeHub 接收到的能量
var _last_energy_time: int = 0  # 上次能量获取时间


func _ready() -> void:
	_current_energy = _load_initial_energy()
	_max_energy = _calculate_max_energy()
	_setup_timers()
	_connect_to_event_bus()
	_find_vibe_client()
	_connect_vibe_signals()
	print("[EnergyManager] 初始化完成，当前能量: %d/%d" % [_current_energy, _max_energy])


func _load_initial_energy() -> int:
	"""从 GameManager 加载初始能量"""
	if GameManager:
		return GameManager.get_energy()
	return 100


func _setup_timers() -> void:
	"""设置定时器"""
	# 能量恢复定时器
	_energy_regen_timer = Timer.new()
	_energy_regen_timer.wait_time = ENERGY_REGEN_DELAY
	_energy_regen_timer.one_shot = true
	_energy_regen_timer.timeout.connect(_on_energy_regen)
	add_child(_energy_regen_timer)

	# 自动保存定时器
	_auto_save_timer = Timer.new()
	_auto_save_timer.wait_time = AUTO_SAVE_INTERVAL
	_auto_save_timer.autostart = true
	_auto_save_timer.timeout.connect(_auto_save)
	add_child(_auto_save_timer)


func _connect_to_event_bus() -> void:
	"""连接 EventBus 信号"""
	if EventBus:
		EventBus.vibe_energy_received.connect(_on_on_vibe_energy_received)
		EventBus.flow_state_achieved.connect(_on_flow_state_entered)
		EventBus.flow_state_ended.connect(_on_flow_state_exited)
		EventBus.coding_session_started.connect(_on_coding_session_started)
		EventBus.coding_session_ended.connect(_on_coding_session_ended)


func _find_vibe_client() -> void:
	"""查找 VibeClient 节点"""
	_vibe_client = get_node_or_null("/root/VibeClient")
	if _vibe_client:
		print("[EnergyManager] 找到 VibeClient")
	else:
		print("[EnergyManager] 未找到 VibeClient，将使用本地能量系统")


func _connect_vibe_signals() -> void:
	"""连接 VibeClient 信号"""
	if _vibe_client:
		_vibe_client.energy_received.connect(_on_vibe_energy_direct)
		_vibe_client.flow_state_changed.connect(_on_vibe_flow_state_changed)


# ==================== 能量获取与消耗 ====================

func get_current_energy() -> int:
	"""获取当前能量"""
	return _current_energy


func get_max_energy() -> int:
	"""获取最大能量"""
	return _max_energy


func get_energy_percentage() -> float:
	"""获取能量百分比"""
	if _max_energy <= 0:
		return 0.0
	return float(_current_energy) / float(_max_energy)


func add_energy(amount: int, source: String = "unknown") -> bool:
	"""添加能量

	Args:
		amount: 要添加的能量值
		source: 能量来源（用于日志和统计）

	Returns:
		bool: 是否成功添加
	"""
	if amount <= 0:
		return false

	var old_energy: int = _current_energy
	var new_energy: int = mini(_current_energy + amount, _max_energy)
	var actual_added: int = new_energy - old_energy

	if actual_added <= 0:
		# 能量已满
		_energy_buffer += amount
		return true

	_current_energy = new_energy

	# 触发信号
	energy_changed.emit(_current_energy, _max_energy)
	if actual_added > 0:
		energy_recovered.emit(actual_added)

	# 同步到 GameManager
	if GameManager:
		GameManager.add_energy(actual_added)

	# 记录日志
	print("[EnergyManager] 能量 +%d (来源: %s, 当前: %d/%d)" % [
		actual_added, source, _current_energy, _max_energy
	])

	return true


func spend_energy(amount: int, reason: String = "unknown") -> bool:
	"""消耗能量

	Args:
		amount: 要消耗的能量值
		reason: 消耗原因（用于日志和验证）

	Returns:
		bool: 是否成功消耗
	"""
	if amount <= 0:
		return false

	if _current_energy < amount:
		energy_insufficient.emit(amount, _current_energy)
		print("[EnergyManager] 能量不足，需要 %d，当前 %d (原因: %s)" % [
			amount, _current_energy, reason
		])
		return false

	var old_energy: int = _current_energy
	_current_energy -= amount

	# 触发信号
	energy_changed.emit(_current_energy, _max_energy)

	# 同步到 GameManager
	if GameManager:
		GameManager.spend_energy(amount)

	# 记录日志
	print("[EnergyManager] 能量 -%d (原因: %s, 当前: %d/%d)" % [
		amount, reason, _current_energy, _max_energy
	])

	return true


func set_energy(amount: int) -> void:
	"""直接设置能量值（用于加载存档或调试）"""
	_current_energy = clampi(amount, 0, _max_energy)
	energy_changed.emit(_current_energy, _max_energy)


# ==================== 心流状态处理 ====================

func is_in_flow() -> bool:
	"""检查是否处于心流状态"""
	return _is_in_flow


func get_flow_bonus_multiplier() -> float:
	"""获取心流状态能量加成倍率"""
	return FLOW_ENERGY_MULTIPLIER if _is_in_flow else 1.0


func set_flow_state(is_flow: bool) -> void:
	"""设置心流状态"""
	if _is_in_flow == is_flow:
		return

	_is_in_flow = is_flow
	var bonus: float = get_flow_bonus_multiplier()
	flow_state_changed.emit(_is_in_flow, bonus)

	if _is_in_flow:
		print("[EnergyManager] 进入心流状态，能量加成: %.1fx" % bonus)
	else:
		print("[EnergyManager] 退出心流状态，能量加成恢复")


# ==================== 能量恢复 ====================

func start_energy_regen() -> void:
	"""开始能量恢复倒计时"""
	if not _energy_regen_timer.is_stopped():
		return
	_energy_regen_timer.start()
	print("[EnergyManager] 能量恢复倒计时开始: %.1f 秒" % ENERGY_REGEN_DELAY)


func stop_energy_regen() -> void:
	"""停止能量恢复倒计时"""
	if not _energy_regen_timer.is_stopped():
		_energy_regen_timer.stop()
		print("[EnergyManager] 能量恢复倒计时已停止")


func _on_energy_regen() -> void:
	"""能量恢复定时器回调"""
	var regen_amount: int = int(_max_energy * 0.1)  # 恢复 10%
	add_energy(regen_amount, "energy_regen")
	print("[EnergyManager] 能量恢复 +%d" % regen_amount)


# ==================== VibeClient 通信 ====================

func _on_vibe_energy_direct(energy: int, breakdown: Dictionary) -> void:
	"""直接从 VibeClient 接收能量

	Args:
		energy: 能量值
		breakdown: 能量细分明细（包含基础能量、时间加成、质量加成、心流加成等）
	"""
	if energy <= 0:
		return

	# 应用心流加成
	var bonus_multiplier: float = get_flow_bonus_multiplier()
	var final_energy: int = int(energy * bonus_multiplier)

	# 添加能量
	add_energy(final_energy, "vibe_coding")

	# 记录详细的细分明细
	if breakdown.size() > 0:
		print("[EnergyManager] 能量细分明细:")
		if breakdown.has("base_energy"):
			print("  - 基础能量: %d" % breakdown["base_energy"])
		if breakdown.has("time_bonus"):
			print("  - 时间加成: %d" % breakdown["time_bonus"])
		if breakdown.has("quality_bonus"):
			print("  - 质量加成: %d" % breakdown["quality_bonus"])
		if breakdown.has("flow_bonus"):
			print("  - 心流加成: %d" % breakdown["flow_bonus"])
		print("  - 心流状态倍率: %.1fx" % bonus_multiplier)


func _on_vibe_flow_state_changed(is_flow: bool) -> void:
	"""从 VibeClient 接收心流状态变化"""
	set_flow_state(is_flow)


# ==================== EventBus 信号处理 ====================

func _on_on_vibe_energy_received(energy: int, exp: int, is_flow: bool) -> void:
	"""处理 EventBus 的 Vibe 能量接收信号"""
	var breakdown: Dictionary = {
		"base_energy": energy,
		"time_bonus": 0,
		"quality_bonus": 0,
		"flow_bonus": 0
	}
	_on_vibe_energy_direct(energy, breakdown)


func _on_flow_state_entered() -> void:
	"""处理心流状态进入"""
	set_flow_state(true)


func _on_flow_state_exited(duration_minutes: int) -> void:
	"""处理心流状态退出"""
	set_flow_state(false)


func _on_coding_session_started() -> void:
	"""处理编码会话开始"""
	print("[EnergyManager] 编码会话开始")
	stop_energy_regen()  # 编码时停止自动恢复


func _on_coding_session_ended(duration_minutes: int, energy_earned: int) -> void:
	"""处理编码会话结束"""
	print("[EnergyManager] 编码会话结束，时长: %d 分钟，获得能量: %d" % [
		duration_minutes, energy_earned
	])
	start_energy_regen()  # 编码结束后开始恢复


# ==================== 等级系统 ====================

func update_max_energy(level: int) -> void:
	"""根据等级更新最大能量"""
	var new_max: int = _calculate_max_energy(level)
	if new_max != _max_energy:
		_max_energy = new_max
		print("[EnergyManager] 最大能量更新: %d (等级: %d)" % [_max_energy, level])
		energy_changed.emit(_current_energy, _max_energy)


func _calculate_max_energy(level: int = 1) -> int:
	"""计算指定等级的最大能量"""
	if GameManager:
		level = GameManager.get_level()
	return BASE_MAX_ENERGY + (level * ENERGY_PER_LEVEL)


# ==================== 自动保存 ====================

func _auto_save() -> void:
	"""自动保存能量数据"""
	if GameManager:
		GameManager.save_player_data()
	# print("[EnergyManager] 能量数据已自动保存")


# ==================== 调试和工具方法 ====================

func reset_daily_energy() -> void:
	"""重置每日能量（用于每日首次登录）"""
	_current_energy = int(_max_energy * 0.5)  # 恢复到 50%
	daily_energy_reset.emit()
	print("[EnergyManager] 每日能量重置，当前: %d/%d" % [_current_energy, _max_energy])


func get_debug_info() -> Dictionary:
	"""获取调试信息"""
	return {
		"current_energy": _current_energy,
		"max_energy": _max_energy,
		"is_in_flow": _is_in_flow,
		"flow_bonus_multiplier": get_flow_bonus_multiplier(),
		"energy_buffer": _energy_buffer,
		"energy_percentage": get_energy_percentage()
	}


func print_debug_info() -> void:
	"""打印调试信息"""
	var info: Dictionary = get_debug_info()
	print("[EnergyManager] 调试信息:")
	print("  当前能量: %d/%d" % [info["current_energy"], info["max_energy"]])
	print("  能量百分比: %.1f%%" % [info["energy_percentage"] * 100.0])
	print("  心流状态: %s" % ("是" if info["is_in_flow"] else "否"))
	print("  心流加成倍率: %.1fx" % info["flow_bonus_multiplier"])
	print("  能量缓冲: %d" % info["energy_buffer"])
