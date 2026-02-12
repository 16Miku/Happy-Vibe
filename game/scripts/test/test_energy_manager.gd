extends Control
## EnergyManager 能量管理器测试场景

var logs: Array[String] = []

func _ready() -> void:
	"""初始化测试场景"""
	_log("测试场景已加载")
	_setup_buttons()

	# 等待 EnergyManager 初始化
	await get_tree().process_frame
	_setup_energy_manager_signals()
	_update_display()
	_log("EnergyManager 测试场景已就绪")


## 设置按钮连接
func _setup_buttons() -> void:
	"""设置按钮点击事件"""
	$VBoxContainer/Add100Btn.pressed.connect(func(): _test_add_energy(100))
	$VBoxContainer/Add50Btn.pressed.connect(func(): _test_add_energy(50))
	$VBoxContainer/Add10Btn.pressed.connect(func(): _test_add_energy(10))
	$VBoxContainer/Consume100Btn.pressed.connect(func(): _test_consume_energy(100))
	$VBoxContainer/Consume50Btn.pressed.connect(func(): _test_consume_energy(50))
	$VBoxContainer/Consume10Btn.pressed.connect(func(): _test_consume_energy(10))
	$VBoxContainer/RegenBtn.pressed.connect(_test_regen_energy)
	$VBoxContainer/ResetBtn.pressed.connect(_test_reset_energy)
	$VBoxContainer/DebugBtn.pressed.connect(_test_debug_info)


## 设置 EnergyManager 信号
func _setup_energy_manager_signals() -> void:
	"""连接 EnergyManager 信号"""
	if EnergyManager:
		EnergyManager.energy_changed.connect(_on_energy_changed)
		EnergyManager.energy_awarded.connect(_on_energy_awarded)
		EnergyManager.energy_consumed.connect(_on_energy_consumed)
		EnergyManager.energy_max_reached.connect(_on_energy_max_reached)
		EnergyManager.energy_depleted.connect(_on_energy_depleted)
		EnergyManager.energy_regened.connect(_on_energy_regened)
		_log("EnergyManager 信号已连接")
	else:
		_log("错误：EnergyManager 未加载！")


## 测试添加能量
func _test_add_energy(amount: int) -> void:
	"""测试添加能量"""
	_log("尝试添加 %d 能量..." % amount)
	if EnergyManager:
		var success: bool = EnergyManager.add_energy(amount, "test")
		if success:
			_log("  ✓ 添加成功")
		else:
			_log("  ✗ 添加失败")
		_update_display()


## 测试消耗能量
func _test_consume_energy(amount: int) -> void:
	"""测试消耗能量"""
	_log("尝试消耗 %d 能量..." % amount)
	if EnergyManager:
		var can_afford: bool = EnergyManager.can_afford(amount)
		if not can_afford:
			_log("  ⚠ 能量不足！")
			return

		var success: bool = EnergyManager.consume_energy(amount, "test")
		if success:
			_log("  ✓ 消耗成功")
		else:
			_log("  ✗ 消耗失败")
		_update_display()


## 测试恢复能量
func _test_regen_energy() -> void:
	"""测试能量恢复"""
	_log("尝试恢复能量...")
	if EnergyManager:
		EnergyManager.regen_energy()
		_log("  ✓ 恢复调用成功")
		_update_display()


## 测试重置能量
func _test_reset_energy() -> void:
	"""测试重置能量"""
	_log("重置能量为最大值...")
	if EnergyManager:
		EnergyManager.debug_reset_energy()
		_log("  ✓ 重置成功")
		_update_display()


## 测试调试信息
func _test_debug_info() -> void:
	"""测试调试信息"""
	if EnergyManager:
		_log("调试信息：")
		_log("  当前能量: %d" % EnergyManager.get_energy())
		_log("  最大能量: %d" % EnergyManager.get_max_energy())
		_log("  能量百分比: %.2f%%" % (EnergyManager.get_energy_percentage() * 100))


## 能量变化信号处理
func _on_energy_changed(new_value: int, old_value: int) -> void:
	"""能量变化信号"""
	_log("能量变化: %d → %d (差值: %+d)" % [old_value, new_value, new_value - old_value])
	_update_display()


## 能量奖励信号处理
func _on_energy_awarded(amount: int, source: String) -> void:
	"""能量奖励信号"""
	_log("能量奖励: +%d (来源: %s)" % [amount, source])


## 能量消耗信号处理
func _on_energy_consumed(amount: int, success: bool) -> void:
	"""能量消耗信号"""
	_log("能量消耗: %d (成功: %s)" % [amount, success])


## 能量达到上限信号处理
func _on_energy_max_reached() -> void:
	"""能量达到上限信号"""
	_log("⚡ 能量已达到上限！")


## 能量耗尽信号处理
func _on_energy_depleted() -> void:
	"""能量耗尽信号"""
	_log("⚠ 能量已耗尽！")


## 能量恢复信号处理
func _on_energy_regened(amount: int) -> void:
	"""能量恢复信号"""
	_log("能量恢复: +%d" % amount)


## 更新显示
func _update_display() -> void:
	"""更新能量显示"""
	if EnergyManager:
		var current: int = EnergyManager.get_energy()
		var max_val: int = EnergyManager.get_max_energy()
		var percentage: float = EnergyManager.get_energy_percentage() * 100.0
		$VBoxContainer/EnergyDisplay.text = "能量: %d / %d (%.1f%%)" % [current, max_val, percentage]


## 添加日志
func _log(message: String) -> void:
	"""添加日志消息"""
	var timestamp = _get_timestamp()
	var log_line: String = "[%s] %s" % [timestamp, message]
	logs.append(log_line)

	# 保持最多 20 条日志
	if logs.size() > 20:
		logs.remove_at(0)

	# 更新日志显示
	$VBoxContainer/LogContainer/LogLabel.text = "\n".join(logs)


## 获取时间戳
func _get_timestamp() -> String:
	"""获取当前时间戳"""
	var datetime_dict = Time.get_datetime_dict_from_system()
	return "%02d:%02d:%02d" % [datetime_dict.hour, datetime_dict.minute, datetime_dict.second]
