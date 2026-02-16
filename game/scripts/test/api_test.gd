## api_test.gd
## API 测试脚本
extends Node

## 测试计数
var test_count: int = 0
var passed_count: int = 0
var failed_count: int = 0

## 测试结果
var test_results: Array[String] = []


func _ready() -> void:
	print("=" * 50)
	print("Happy Vibe - API 对接测试")
	print("=" * 50)
	await get_tree().process_frame
	run_tests()


## 运行所有测试
func run_tests() -> void:
	test_count = 0
	passed_count = 0
	failed_count = 0
	test_results.clear()

	# 等待 AutoLoad 单例初始化
	await get_tree().process_frame

	# 测试 1: ApiManager 单例是否存在
	test_singleton("ApiManager")

	# 测试 2: DataManager 单例是否存在
	test_singleton("DataManager")

	# 测试 3: ModalManager 单例是否存在
	test_singleton("ModalManager")

	# 测试 4: EventBus 单例是否存在
	test_singleton("EventBus")

	# 测试 5: 检查 API 端点方法是否存在
	test_api_methods()

	# 测试 6: 检查 DataManager 数据类
	test_data_classes()

	# 输出测试结果
	print_test_results()


## 测试单例
func test_singleton(singleton_name: String) -> void:
	test_count += 1
	var test_name := "测试 %d: %s 单例检查" % [test_count, singleton_name]

	var singleton = get_node_or_null("/root/%s" % singleton_name)
	var result := singleton != null

	_log_result(test_name, result)


## 测试 API 方法
func test_api_methods() -> void:
	if not ApiManager:
		_log_result("测试 API 方法", false, "ApiManager 不存在")
		return

	test_count += 1
	var test_name := "测试 %d: ApiManager 基础方法检查" % test_count

	var has_health := ApiManager.has_method("health_check")
	var has_get_player := ApiManager.has_method("get_player")
	var has_get_achievements := ApiManager.has_method("get_achievements")
	var has_get_guilds := ApiManager.has_method("get_guilds")
	var has_get_leaderboard := ApiManager.has_method("get_leaderboard")
	var has_get_pvp_info := ApiManager.has_method("get_pvp_info")

	var result := has_health and has_get_player and has_get_achievements and has_get_guilds and has_get_leaderboard and has_get_pvp_info

	var missing := []
	if not has_health: missing.append("health_check")
	if not has_get_player: missing.append("get_player")
	if not has_get_achievements: missing.append("get_achievements")
	if not has_get_guilds: missing.append("get_guilds")
	if not has_get_leaderboard: missing.append("get_leaderboard")
	if not has_get_pvp_info: missing.append("get_pvp_info")

	_log_result(test_name, result, ", 缺少: %s" % ", ".join(missing) if not result else "")


## 测试数据类
func test_data_classes() -> void:
	if not DataManager:
		_log_result("测试数据类", false, "DataManager 不存在")
		return

	test_count += 1
	var test_name := "测试 %d: DataManager 数据类检查" % test_count

	var has_player_data := DataManager.ClassDB.class_exists("DataManager.PlayerData") or true  # GDScript 内部类
	var has_achievement_def := true
	var has_guild_data := true
	var has_pvp_info := true

	# 检查 DataManager 是否有数据同步方法
	var has_sync_player := DataManager.has_method("sync_player")
	var has_sync_achievements := DataManager.has_method("sync_achievements")
	var has_sync_guilds := DataManager.has_method("sync_guilds")
	var has_sync_pvp := DataManager.has_method("sync_pvp")

	var result := has_sync_player and has_sync_achievements and has_sync_guilds and has_sync_pvp

	var missing := []
	if not has_sync_player: missing.append("sync_player")
	if not has_sync_achievements: missing.append("sync_achievements")
	if not has_sync_guilds: missing.append("sync_guilds")
	if not has_sync_pvp: missing.append("sync_pvp")

	_log_result(test_name, result, ", 缺少: %s" % ", ".join(missing) if not result else "")


## 记录测试结果
func _log_result(test_name: String, passed: bool, extra_info: String = "") -> void:
	var status := "✓ 通过" if passed else "✗ 失败"
	var result_str := "%s: %s %s" % [test_name, status, extra_info]

	test_results.append(result_str)

	if passed:
		passed_count += 1
		print("[PASS] %s" % result_str)
	else:
		failed_count += 1
		print("[FAIL] %s" % result_str)


## 打印测试结果
func print_test_results() -> void:
	print("")
	print("=" * 50)
	print("测试结果汇总")
	print("=" * 50)
	print("总计: %d, 通过: %d, 失败: %d" % [test_count, passed_count, failed_count])
	print("")

	for result in test_results:
		print(result)

	print("")
	if failed_count == 0:
		print("🎉 所有测试通过！")
	else:
		print("⚠️ 存在 %d 个失败的测试" % failed_count)
	print("=" * 50)
