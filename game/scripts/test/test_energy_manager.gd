extends Node
## EnergyManager 功能测试脚本

var energy_manager: Node
var vibe_client: Node
var test_passed: int = 0
var test_failed: int = 0
var test_results: Array = []


func _ready() -> void:
	print("[TestEnergyManager] ========== 能量管理器测试开始 ==========")
	_setup_environment()
	_run_all_tests()
	_print_summary()


func _setup_environment() -> void:
	"""设置测试环境"""
	print("[TestEnergyManager] 设置测试环境...")

	# 确保 GameManager 存在
	if not GameManager:
		_create_mock_game_manager()

	# 创建 EnergyManager
	energy_manager = load("res://scripts/player/energy_manager.gd").new()
	add_child(energy_manager)
	await get_tree().process_frame

	# 连接信号
	energy_manager.energy_manager = energy_manager  # 确保变量名一致
	energy_manager.energy_changed.connect(_on_energy_changed)
	energy_manager.energy_insufficient.connect(_on_energy_insufficient)
	energy_manager.energy_recovered.connect(_on_energy_recovered)
	energy_manager.flow_state_changed.connect(_on_flow_state_changed)

	print("[TestEnergyManager] 能量管理器已创建")


func _create_mock_game_manager() -> void:
	"""创建模拟的 GameManager（如果不存在）"""
	print("[TestEnergyManager] 创建模拟 GameManager...")
	var mock_game_manager = Node.new()
	mock_game_manager.name = "GameManager"
	mock_game_manager.set_script(preload("res://scripts/core/game_manager.gd"))
	get_tree().root.add_child(mock_game_manager)
	print("[TestEnergyManager] 模拟 GameManager 已创建")


func _run_all_tests() -> void:
	"""运行所有测试"""
	print("[TestEnergyManager] ========== 开始测试用例 ==========")

	await test_initial_energy()
	await test_add_energy()
	await test_spend_energy()
	await test_energy_insufficient()
	await test_flow_state()
	await test_flow_bonus()
	await test_max_energy()
	await test_energy_percentage()
	await test_set_energy()
	await test_debug_info()

	print("[TestEnergyManager] ========== 所有测试完成 ==========")


# ==================== 测试用例 ====================

func test_initial_energy() -> void:
	"""测试初始能量"""
	print("[TestEnergyManager] 测试: 初始能量...")
	var initial: int = energy_manager.get_current_energy()
	var max_energy: int = energy_manager.get_max_energy()

	assert initial > 0, "初始能量应大于 0"
	assert max_energy > 0, "最大能量应大于 0"
	assert initial <= max_energy, "初始能量不应超过最大能量"

	_record_test_passed("初始能量", "初始能量: %d/%d" % [initial, max_energy])


func test_add_energy() -> void:
	"""测试添加能量"""
	print("[TestEnergyManager] 测试: 添加能量...")
	var old_energy: int = energy_manager.get_current_energy()
	var add_amount: int = 100

	var success: bool = energy_manager.add_energy(add_amount, "test")
	await get_tree().process_frame

	var new_energy: int = energy_manager.get_current_energy()
	var expected: int = mini(old_energy + add_amount, energy_manager.get_max_energy())

	assert success, "添加能量应成功"
	assert new_energy == expected, "能量应正确增加"

	_record_test_passed("添加能量", "能量: %d -> %d" % [old_energy, new_energy])


func test_spend_energy() -> void:
	"""测试消耗能量"""
	print("[TestEnergyManager] 测试: 消耗能量...")

	# 确保有足够的能量
	energy_manager.add_energy(500, "test_preload")
	await get_tree().process_frame

	var old_energy: int = energy_manager.get_current_energy()
	var spend_amount: int = 50

	var success: bool = energy_manager.spend_energy(spend_amount, "test")
	await get_tree().process_frame

	var new_energy: int = energy_manager.get_current_energy()
	var expected: int = old_energy - spend_amount

	assert success, "消耗能量应成功"
	assert new_energy == expected, "能量应正确减少"

	_record_test_passed("消耗能量", "能量: %d -> %d" % [old_energy, new_energy])


func test_energy_insufficient() -> void:
	"""测试能量不足情况"""
	print("[TestEnergyManager] 测试: 能量不足...")

	# 尝试消耗超过当前能量的数量
	var current_energy: int = energy_manager.get_current_energy()
	var excess_amount: int = current_energy + 1000

	var success: bool = energy_manager.spend_energy(excess_amount, "test_excess")
	await get_tree().process_frame

	var new_energy: int = energy_manager.get_current_energy()

	assert not success, "消耗超过当前能量的数量应失败"
	assert new_energy == current_energy, "能量不足时能量不应变化"

	_record_test_passed("能量不足", "正确拒绝超额消耗请求")


func test_flow_state() -> void:
	"""测试心流状态"""
	print("[TestEnergyManager] 测试: 心流状态...")

	# 设置心流状态
	energy_manager.set_flow_state(true)
	await get_tree().process_frame

	assert energy_manager.is_in_flow(), "应处于心流状态"

	# 退出心流状态
	energy_manager.set_flow_state(false)
	await get_tree().process_frame

	assert not energy_manager.is_in_flow(), "应不处于心流状态"

	_record_test_passed("心流状态", "心流状态切换正常")


func test_flow_bonus() -> void:
	"""测试心流加成"""
	print("[TestEnergyManager] 测试: 心流加成...")

	# 正常状态倍率
	energy_manager.set_flow_state(false)
	await get_tree().process_frame
	var normal_multiplier: float = energy_manager.get_flow_bonus_multiplier()
	assert normal_multiplier == 1.0, "正常状态倍率应为 1.0"

	# 心流状态倍率
	energy_manager.set_flow_state(true)
	await get_tree().process_frame
	var flow_multiplier: float = energy_manager.get_flow_bonus_multiplier()
	assert flow_multiplier == 2.0, "心流状态倍率应为 2.0"

	# 恢复正常状态
	energy_manager.set_flow_state(false)
	await get_tree().process_frame

	_record_test_passed("心流加成", "正常: %.1fx, 心流: %.1fx" % [normal_multiplier, flow_multiplier])


func test_max_energy() -> void:
	"""测试最大能量"""
	print("[TestEnergyManager] 测试: 最大能量...")

	var max_energy: int = energy_manager.get_max_energy()
	assert max_energy > 0, "最大能量应大于 0"

	# 测试等级影响
	energy_manager.update_max_energy(5)
	await get_tree().process_frame
	var new_max_energy: int = energy_manager.get_max_energy()
	assert new_max_energy > max_energy, "升级后最大能量应增加"

	_record_test_passed("最大能量", "等级1: %d, 等级5: %d" % [max_energy, new_max_energy])


func test_energy_percentage() -> void:
	"""测试能量百分比"""
	print("[TestEnergyManager] 测试: 能量百分比...")

	# 设置一个明确的能量值
	energy_manager.set_energy(500)
	await get_tree().process_frame

	var percentage: float = energy_manager.get_energy_percentage()
	assert percentage >= 0.0 and percentage <= 1.0, "百分比应在 0.0 到 1.0 之间"

	# 满能量测试
	energy_manager.set_energy(energy_manager.get_max_energy())
	await get_tree().process_frame
	var full_percentage: float = energy_manager.get_energy_percentage()
	assert full_percentage == 1.0, "满能量百分比应为 1.0"

	_record_test_passed("能量百分比", "百分比: %.2f, 满能量: %.2f" % [percentage, full_percentage])


func test_set_energy() -> void:
	"""测试直接设置能量"""
	print("[TestEnergyManager] 测试: 直接设置能量...")

	energy_manager.set_energy(750)
	await get_tree().process_frame
	var current = energy_manager.get_current_energy()
	assert current == 750, "能量应设置为指定值"

	# 测试边界值
	energy_manager.set_energy(-100)
	await get_tree().process_frame
	assert energy_manager.get_current_energy() >= 0, "能量不应为负数"

	var max_energy: int = energy_manager.get_max_energy()
	energy_manager.set_energy(max_energy + 1000)
	await get_tree().process_frame
	assert energy_manager.get_current_energy() <= max_energy, "能量不应超过最大值"

	_record_test_passed("直接设置能量", "能量设置和边界检查正常")


func test_debug_info() -> void:
	"""测试调试信息"""
	print("[TestEnergyManager] 测试: 调试信息...")

	var info: Dictionary = energy_manager.get_debug_info()
	assert info.has("current_energy"), "应包含当前能量"
	assert info.has("max_energy"), "应包含最大能量"
	assert info.has("is_in_flow"), "应包含心流状态"
	assert info.has("flow_bonus_multiplier"), "应包含心流加成倍率"

	_record_test_passed("调试信息", "调试信息完整")


# ==================== 信号回调 ====================

func _on_energy_changed(current: int, max_energy: int) -> void:
	print("[TestEnergyManager] 信号: energy_changed(%d, %d)" % [current, max_energy])


func _on_energy_insufficient(required: int, current: int) -> void:
	print("[TestEnergyManager] 信号: energy_insufficient(需要: %d, 当前: %d)" % [required, current])


func _on_energy_recovered(amount: int) -> void:
	print("[TestEnergyManager] 信号: energy_recovered(%d)" % amount)


func _on_flow_state_changed(is_flow: bool, bonus_multiplier: float) -> void:
	print("[TestEnergyManager] 信号: flow_state_changed(%s, %.1fx)" % [
		"是" if is_flow else "否", bonus_multiplier
	])


# ==================== 测试记录和总结 ====================

func _record_test_passed(test_name: String, details: String = "") -> void:
	"""记录测试通过"""
	test_passed += 1
	test_results.append({
		"name": test_name,
		"status": "passed",
		"details": details
	})
	print("[TestEnergyManager] ✓ 通过: %s" % test_name)
	if not details.is_empty():
		print("    %s" % details)


func _record_test_failed(test_name: String, reason: String) -> void:
	"""记录测试失败"""
	test_failed += 1
	test_results.append({
		"name": test_name,
		"status": "failed",
		"reason": reason
	})
	print("[TestEnergyManager] ✗ 失败: %s" % test_name)
	print("    原因: %s" % reason)


func _print_summary() -> void:
	"""打印测试总结"""
	print("\n[TestEnergyManager] ========== 测试总结 ==========")
	print("总总测试数: %d" % (test_passed + test_failed))
	print("通过: %d" % test_passed)
	print("失败: %d" % test_failed)
	print("通过率: %.1f%%" % (float(test_passed) / float(test_passed + test_failed) * 100.0))

	if test_failed == 0:
		print("\n[TestEnergyManager] 🎉 所有测试通过！")
	else:
		print("\n[TestEnergyManager] ⚠️  有测试失败，请检查错误信息")

	print("[TestEnergyManager] ==========================================")

	# 退出游戏（可选）
	# get_tree().quit()
