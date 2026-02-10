## save_manager.gd
## 存档管理器 - 负责游戏数据的保存和加载
## 作为 AutoLoad 单例运行
## 使用 user:// 目录存储数据，支持 JSON 序列化
extends Node

# 信号定义
signal save_completed(success: bool)
signal load_completed(success: bool)
signal save_error(error_message: String)

# 存档配置
const SAVE_DIR: String = "user://saves/"
const SAVE_FILE: String = "player_save.json"
const BACKUP_FILE: String = "player_save_backup.json"
const SETTINGS_FILE: String = "settings.json"
const SAVE_VERSION: int = 1

# 自动保存配置
const AUTO_SAVE_INTERVAL: float = 300.0  # 5分钟自动保存
var _auto_save_timer: Timer = null
var _auto_save_enabled: bool = true

# 初始化
func _ready() -> void:
	_ensure_save_directory()
	_setup_auto_save()


## 确保存档目录存在
func _ensure_save_directory() -> void:
	var dir := DirAccess.open("user://")
	if dir:
		if not dir.dir_exists("saves"):
			dir.make_dir("saves")


## 设置自动保存定时器
func _setup_auto_save() -> void:
	_auto_save_timer = Timer.new()
	_auto_save_timer.wait_time = AUTO_SAVE_INTERVAL
	_auto_save_timer.one_shot = false
	_auto_save_timer.timeout.connect(_on_auto_save_timeout)
	add_child(_auto_save_timer)

	if _auto_save_enabled:
		_auto_save_timer.start()


## 自动保存回调
func _on_auto_save_timeout() -> void:
	if GameManager and GameManager.is_playing():
		save_game(GameManager.player_data)
		if EventBus:
			EventBus.notify("游戏已自动保存", "info")


## 启用/禁用自动保存
func set_auto_save_enabled(enabled: bool) -> void:
	_auto_save_enabled = enabled
	if enabled:
		_auto_save_timer.start()
	else:
		_auto_save_timer.stop()


# ==================== 主要存档方法 ====================

## 保存游戏数据
func save_game(data: Dictionary) -> bool:
	if data.is_empty():
		save_error.emit("保存数据为空")
		return false

	# 添加元数据
	var save_data: Dictionary = {
		"version": SAVE_VERSION,
		"timestamp": Time.get_unix_time_from_system(),
		"datetime": Time.get_datetime_string_from_system(),
		"data": data
	}

	# 先备份现有存档
	_backup_save()

	# 写入存档文件
	var save_path: String = SAVE_DIR + SAVE_FILE
	var success: bool = _write_json_file(save_path, save_data)

	save_completed.emit(success)

	if success and EventBus:
		EventBus.game_saved.emit()

	return success


## 加载游戏数据
func load_game() -> Dictionary:
	var save_path: String = SAVE_DIR + SAVE_FILE

	# 检查存档是否存在
	if not FileAccess.file_exists(save_path):
		# 尝试从备份恢复
		if _restore_from_backup():
			return load_game()
		load_completed.emit(false)
		return {}

	# 读取存档
	var save_data: Dictionary = _read_json_file(save_path)

	if save_data.is_empty():
		save_error.emit("存档文件损坏")
		# 尝试从备份恢复
		if _restore_from_backup():
			return load_game()
		load_completed.emit(false)
		return {}

	# 版本检查和迁移
	var version: int = save_data.get("version", 0)
	if version < SAVE_VERSION:
		save_data = _migrate_save(save_data, version)

	load_completed.emit(true)

	if EventBus:
		EventBus.game_loaded.emit()

	return save_data.get("data", {})


## 检查是否存在存档
func has_save() -> bool:
	return FileAccess.file_exists(SAVE_DIR + SAVE_FILE)


## 删除存档
func delete_save() -> bool:
	var save_path: String = SAVE_DIR + SAVE_FILE
	var backup_path: String = SAVE_DIR + BACKUP_FILE

	var dir := DirAccess.open(SAVE_DIR)
	if not dir:
		return false

	var success: bool = true

	if FileAccess.file_exists(save_path):
		if dir.remove(SAVE_FILE) != OK:
			success = false

	if FileAccess.file_exists(backup_path):
		if dir.remove(BACKUP_FILE) != OK:
			success = false

	return success


# ==================== 设置存储 ====================

## 保存设置
func save_settings(settings: Dictionary) -> bool:
	var settings_path: String = SAVE_DIR + SETTINGS_FILE
	return _write_json_file(settings_path, settings)


## 加载设置
func load_settings() -> Dictionary:
	var settings_path: String = SAVE_DIR + SETTINGS_FILE

	if not FileAccess.file_exists(settings_path):
		return _get_default_settings()

	var settings: Dictionary = _read_json_file(settings_path)

	if settings.is_empty():
		return _get_default_settings()

	return settings


## 获取默认设置
func _get_default_settings() -> Dictionary:
	return {
		"music_volume": 1.0,
		"sfx_volume": 1.0,
		"notifications_enabled": true,
		"auto_save_enabled": true,
		"language": "zh_CN",
		"fullscreen": false,
		"vsync": true
	}


# ==================== 备份与恢复 ====================

## 备份当前存档
func _backup_save() -> bool:
	var save_path: String = SAVE_DIR + SAVE_FILE
	var backup_path: String = SAVE_DIR + BACKUP_FILE

	if not FileAccess.file_exists(save_path):
		return false

	# 读取当前存档
	var file := FileAccess.open(save_path, FileAccess.READ)
	if not file:
		return false

	var content: String = file.get_as_text()
	file.close()

	# 写入备份
	var backup := FileAccess.open(backup_path, FileAccess.WRITE)
	if not backup:
		return false

	backup.store_string(content)
	backup.close()

	return true


## 从备份恢复
func _restore_from_backup() -> bool:
	var save_path: String = SAVE_DIR + SAVE_FILE
	var backup_path: String = SAVE_DIR + BACKUP_FILE

	if not FileAccess.file_exists(backup_path):
		return false

	# 读取备份
	var backup := FileAccess.open(backup_path, FileAccess.READ)
	if not backup:
		return false

	var content: String = backup.get_as_text()
	backup.close()

	# 写入存档
	var file := FileAccess.open(save_path, FileAccess.WRITE)
	if not file:
		return false

	file.store_string(content)
	file.close()

	if EventBus:
		EventBus.notify_warning("已从备份恢复存档")

	return true


# ==================== 存档迁移 ====================

## 迁移旧版本存档
func _migrate_save(save_data: Dictionary, from_version: int) -> Dictionary:
	var data: Dictionary = save_data.duplicate(true)

	# 版本迁移逻辑
	# 当存档格式变化时，在这里添加迁移代码

	# 示例：从版本 0 迁移到版本 1
	if from_version < 1:
		# 添加新字段的默认值
		if data.has("data"):
			var player_data: Dictionary = data["data"]
			if not player_data.has("consecutive_days"):
				player_data["consecutive_days"] = 0
			if not player_data.has("titles"):
				player_data["titles"] = []
			if not player_data.has("equipped_title"):
				player_data["equipped_title"] = ""

	# 更新版本号
	data["version"] = SAVE_VERSION

	return data


# ==================== 文件操作工具 ====================

## 写入 JSON 文件
func _write_json_file(path: String, data: Dictionary) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if not file:
		var error: int = FileAccess.get_open_error()
		save_error.emit("无法打开文件进行写入: " + str(error))
		return false

	var json_string: String = JSON.stringify(data, "\t")
	file.store_string(json_string)
	file.close()

	return true


## 读取 JSON 文件
func _read_json_file(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if not file:
		return {}

	var content: String = file.get_as_text()
	file.close()

	if content.is_empty():
		return {}

	var json := JSON.new()
	var error: int = json.parse(content)

	if error != OK:
		save_error.emit("JSON 解析错误: " + json.get_error_message())
		return {}

	var result = json.get_data()
	if result is Dictionary:
		return result

	return {}


# ==================== 存档信息 ====================

## 获取存档信息（不加载完整数据）
func get_save_info() -> Dictionary:
	var save_path: String = SAVE_DIR + SAVE_FILE

	if not FileAccess.file_exists(save_path):
		return {}

	var save_data: Dictionary = _read_json_file(save_path)

	if save_data.is_empty():
		return {}

	var player_data: Dictionary = save_data.get("data", {})

	return {
		"exists": true,
		"version": save_data.get("version", 0),
		"timestamp": save_data.get("timestamp", 0),
		"datetime": save_data.get("datetime", ""),
		"username": player_data.get("username", "Player"),
		"level": player_data.get("level", 1),
		"play_time": player_data.get("stats", {}).get("total_coding_time", 0)
	}


## 获取存档文件大小
func get_save_size() -> int:
	var save_path: String = SAVE_DIR + SAVE_FILE

	if not FileAccess.file_exists(save_path):
		return 0

	var file := FileAccess.open(save_path, FileAccess.READ)
	if not file:
		return 0

	var size: int = file.get_length()
	file.close()

	return size


# ==================== 导出/导入 ====================

## 导出存档到指定路径
func export_save(export_path: String) -> bool:
	var save_path: String = SAVE_DIR + SAVE_FILE

	if not FileAccess.file_exists(save_path):
		save_error.emit("没有可导出的存档")
		return false

	var file := FileAccess.open(save_path, FileAccess.READ)
	if not file:
		return false

	var content: String = file.get_as_text()
	file.close()

	var export_file := FileAccess.open(export_path, FileAccess.WRITE)
	if not export_file:
		save_error.emit("无法写入导出文件")
		return false

	export_file.store_string(content)
	export_file.close()

	return true


## 从指定路径导入存档
func import_save(import_path: String) -> bool:
	if not FileAccess.file_exists(import_path):
		save_error.emit("导入文件不存在")
		return false

	var file := FileAccess.open(import_path, FileAccess.READ)
	if not file:
		return false

	var content: String = file.get_as_text()
	file.close()

	# 验证 JSON 格式
	var json := JSON.new()
	if json.parse(content) != OK:
		save_error.emit("导入文件格式无效")
		return false

	# 备份当前存档
	_backup_save()

	# 写入新存档
	var save_path: String = SAVE_DIR + SAVE_FILE
	var save_file := FileAccess.open(save_path, FileAccess.WRITE)
	if not save_file:
		return false

	save_file.store_string(content)
	save_file.close()

	if EventBus:
		EventBus.notify_success("存档导入成功")

	return true
