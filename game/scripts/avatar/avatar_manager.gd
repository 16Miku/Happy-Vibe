## 头像管理器
## 负责管理玩家头像的加载、解锁和切换
class_name AvatarManager
extends Node

## 头像数据结构
## {
##   "id": String,           # 唯一标识
##   "name": String,         # 显示名称
##   "description": String,  # 描述
##   "path": String,         # 资源路径
##   "unlock_type": String,  # 解锁类型: "default", "level", "achievement", "purchase"
##   "unlock_value": Variant,# 解锁条件值
##   "rarity": String,       # 稀有度: "common", "rare", "epic", "legendary"
## }

## 信号
signal avatar_changed(avatar_id: String)
signal avatar_unlocked(avatar_id: String)
signal avatars_loaded()

## 常量
const AVATARS_PATH := "res://assets/avatars/"
const DEFAULT_AVATAR_ID := "default_coder"

## 所有可用头像配置
var _avatar_configs: Dictionary = {}

## 已解锁的头像ID列表
var _unlocked_avatars: Array[String] = []

## 当前装备的头像ID
var _current_avatar_id: String = DEFAULT_AVATAR_ID

## 头像纹理缓存
var _texture_cache: Dictionary = {}


func _ready() -> void:
	_register_default_avatars()
	_load_unlocked_avatars()
	avatars_loaded.emit()


## 注册默认头像配置
func _register_default_avatars() -> void:
	# 默认头像（所有玩家都有）
	_register_avatar({
		"id": "default_coder",
		"name": "初心程序员",
		"description": "每个伟大的程序员都从这里开始",
		"path": "default/coder.png",
		"unlock_type": "default",
		"unlock_value": null,
		"rarity": "common"
	})

	_register_avatar({
		"id": "default_hacker",
		"name": "神秘黑客",
		"description": "戴着帽衫的神秘人物",
		"path": "default/hacker.png",
		"unlock_type": "default",
		"unlock_value": null,
		"rarity": "common"
	})

	_register_avatar({
		"id": "default_robot",
		"name": "代码机器人",
		"description": "永不疲倦的编程伙伴",
		"path": "default/robot.png",
		"unlock_type": "default",
		"unlock_value": null,
		"rarity": "common"
	})

	# 等级解锁头像
	_register_avatar({
		"id": "level_junior",
		"name": "初级开发者",
		"description": "达到5级解锁",
		"path": "unlockable/junior.png",
		"unlock_type": "level",
		"unlock_value": 5,
		"rarity": "common"
	})

	_register_avatar({
		"id": "level_senior",
		"name": "高级开发者",
		"description": "达到15级解锁",
		"path": "unlockable/senior.png",
		"unlock_type": "level",
		"unlock_value": 15,
		"rarity": "rare"
	})

	_register_avatar({
		"id": "level_architect",
		"name": "架构师",
		"description": "达到30级解锁",
		"path": "unlockable/architect.png",
		"unlock_type": "level",
		"unlock_value": 30,
		"rarity": "epic"
	})

	_register_avatar({
		"id": "level_master",
		"name": "代码大师",
		"description": "达到50级解锁",
		"path": "unlockable/master.png",
		"unlock_type": "level",
		"unlock_value": 50,
		"rarity": "legendary"
	})

	# 成就解锁头像
	_register_avatar({
		"id": "achievement_flow",
		"name": "心流达人",
		"description": "累计进入心流状态100次解锁",
		"path": "unlockable/flow_master.png",
		"unlock_type": "achievement",
		"unlock_value": "flow_master_100",
		"rarity": "epic"
	})

	_register_avatar({
		"id": "achievement_farmer",
		"name": "农场主",
		"description": "收获1000次作物解锁",
		"path": "unlockable/farmer.png",
		"unlock_type": "achievement",
		"unlock_value": "harvest_1000",
		"rarity": "rare"
	})

	_register_avatar({
		"id": "achievement_marathon",
		"name": "编程马拉松",
		"description": "累计编程100小时解锁",
		"path": "unlockable/marathon.png",
		"unlock_type": "achievement",
		"unlock_value": "coding_100h",
		"rarity": "epic"
	})

	# 购买头像
	_register_avatar({
		"id": "purchase_golden",
		"name": "黄金程序员",
		"description": "使用1000金币购买",
		"path": "unlockable/golden.png",
		"unlock_type": "purchase",
		"unlock_value": {"currency": "gold", "amount": 1000},
		"rarity": "rare"
	})

	_register_avatar({
		"id": "purchase_diamond",
		"name": "钻石精英",
		"description": "使用100钻石购买",
		"path": "unlockable/diamond.png",
		"unlock_type": "purchase",
		"unlock_value": {"currency": "diamonds", "amount": 100},
		"rarity": "legendary"
	})


## 注册单个头像
func _register_avatar(config: Dictionary) -> void:
	_avatar_configs[config.id] = config
	# 默认头像自动解锁
	if config.unlock_type == "default":
		if config.id not in _unlocked_avatars:
			_unlocked_avatars.append(config.id)


## 从存档加载已解锁头像
func _load_unlocked_avatars() -> void:
	if GameManager and GameManager.player_data.has("avatar"):
		var avatar_data: Dictionary = GameManager.player_data.avatar
		if avatar_data.has("unlocked"):
			for avatar_id in avatar_data.unlocked:
				if avatar_id not in _unlocked_avatars:
					_unlocked_avatars.append(avatar_id)
		if avatar_data.has("current"):
			_current_avatar_id = avatar_data.current


## 保存头像数据到存档
func _save_avatar_data() -> void:
	if GameManager:
		GameManager.player_data.avatar = {
			"current": _current_avatar_id,
			"unlocked": _unlocked_avatars.duplicate()
		}
		SaveManager.save_game()


## 获取所有头像配置
func get_all_avatars() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for config in _avatar_configs.values():
		result.append(config)
	return result


## 获取已解锁的头像
func get_unlocked_avatars() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for avatar_id in _unlocked_avatars:
		if _avatar_configs.has(avatar_id):
			result.append(_avatar_configs[avatar_id])
	return result


## 获取未解锁的头像
func get_locked_avatars() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for avatar_id in _avatar_configs:
		if avatar_id not in _unlocked_avatars:
			result.append(_avatar_configs[avatar_id])
	return result


## 获取指定头像配置
func get_avatar_config(avatar_id: String) -> Dictionary:
	return _avatar_configs.get(avatar_id, {})


## 获取当前头像ID
func get_current_avatar_id() -> String:
	return _current_avatar_id


## 获取当前头像配置
func get_current_avatar() -> Dictionary:
	return get_avatar_config(_current_avatar_id)


## 检查头像是否已解锁
func is_avatar_unlocked(avatar_id: String) -> bool:
	return avatar_id in _unlocked_avatars


## 切换头像
func set_avatar(avatar_id: String) -> bool:
	if not is_avatar_unlocked(avatar_id):
		push_warning("尝试装备未解锁的头像: %s" % avatar_id)
		return false

	if not _avatar_configs.has(avatar_id):
		push_warning("头像不存在: %s" % avatar_id)
		return false

	_current_avatar_id = avatar_id
	_save_avatar_data()
	avatar_changed.emit(avatar_id)

	if EventBus:
		EventBus.emit_signal("avatar_changed", avatar_id)

	return true


## 解锁头像
func unlock_avatar(avatar_id: String) -> bool:
	if avatar_id in _unlocked_avatars:
		return false  # 已解锁

	if not _avatar_configs.has(avatar_id):
		push_warning("头像不存在: %s" % avatar_id)
		return false

	_unlocked_avatars.append(avatar_id)
	_save_avatar_data()
	avatar_unlocked.emit(avatar_id)

	if EventBus:
		EventBus.emit_signal("avatar_unlocked", avatar_id)
		EventBus.emit_signal("show_notification", "解锁新头像: %s" % _avatar_configs[avatar_id].name)

	return true


## 尝试购买头像
func try_purchase_avatar(avatar_id: String) -> bool:
	if not _avatar_configs.has(avatar_id):
		return false

	var config: Dictionary = _avatar_configs[avatar_id]
	if config.unlock_type != "purchase":
		return false

	if is_avatar_unlocked(avatar_id):
		return false

	var purchase_info: Dictionary = config.unlock_value
	var currency: String = purchase_info.currency
	var amount: int = purchase_info.amount

	# 检查货币是否足够
	if GameManager:
		var current_amount: int = GameManager.player_data.get(currency, 0)
		if current_amount >= amount:
			# 扣除货币
			GameManager.player_data[currency] = current_amount - amount
			# 解锁头像
			unlock_avatar(avatar_id)
			return true

	return false


## 检查等级解锁
func check_level_unlocks(level: int) -> void:
	for avatar_id in _avatar_configs:
		var config: Dictionary = _avatar_configs[avatar_id]
		if config.unlock_type == "level" and config.unlock_value <= level:
			if not is_avatar_unlocked(avatar_id):
				unlock_avatar(avatar_id)


## 检查成就解锁
func check_achievement_unlock(achievement_id: String) -> void:
	for avatar_id in _avatar_configs:
		var config: Dictionary = _avatar_configs[avatar_id]
		if config.unlock_type == "achievement" and config.unlock_value == achievement_id:
			if not is_avatar_unlocked(avatar_id):
				unlock_avatar(avatar_id)


## 加载头像纹理
func load_avatar_texture(avatar_id: String) -> Texture2D:
	# 检查缓存
	if _texture_cache.has(avatar_id):
		return _texture_cache[avatar_id]

	var config: Dictionary = get_avatar_config(avatar_id)
	if config.is_empty():
		return _get_placeholder_texture()

	var full_path: String = AVATARS_PATH + config.path

	# 尝试加载纹理
	if ResourceLoader.exists(full_path):
		var texture: Texture2D = load(full_path)
		_texture_cache[avatar_id] = texture
		return texture

	# 返回占位纹理
	return _get_placeholder_texture()


## 获取当前头像纹理
func get_current_avatar_texture() -> Texture2D:
	return load_avatar_texture(_current_avatar_id)


## 生成占位纹理（程序化生成）
func _get_placeholder_texture() -> Texture2D:
	if _texture_cache.has("_placeholder"):
		return _texture_cache["_placeholder"]

	# 创建一个简单的占位图像
	var image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color(0.3, 0.3, 0.4, 1.0))

	# 绘制简单的头像轮廓
	var center := Vector2i(32, 32)
	var radius := 24

	# 绘制圆形背景
	for x in range(64):
		for y in range(64):
			var dist := Vector2(x - center.x, y - center.y).length()
			if dist <= radius:
				image.set_pixel(x, y, Color(0.5, 0.4, 0.6, 1.0))
			elif dist <= radius + 2:
				image.set_pixel(x, y, Color(0.7, 0.6, 0.8, 1.0))

	# 绘制简单的人形图标
	# 头部
	for x in range(26, 38):
		for y in range(18, 30):
			var dist := Vector2(x - 32, y - 24).length()
			if dist <= 6:
				image.set_pixel(x, y, Color(0.8, 0.7, 0.6, 1.0))

	# 身体
	for x in range(24, 40):
		for y in range(32, 48):
			if abs(x - 32) <= 8 - (y - 32) * 0.3:
				image.set_pixel(x, y, Color(0.4, 0.5, 0.7, 1.0))

	var texture := ImageTexture.create_from_image(image)
	_texture_cache["_placeholder"] = texture
	return texture


## 获取稀有度颜色
func get_rarity_color(rarity: String) -> Color:
	match rarity:
		"common":
			return Color(0.7, 0.7, 0.7)  # 灰色
		"rare":
			return Color(0.3, 0.5, 1.0)  # 蓝色
		"epic":
			return Color(0.6, 0.3, 0.9)  # 紫色
		"legendary":
			return Color(1.0, 0.7, 0.2)  # 金色
		_:
			return Color.WHITE


## 获取稀有度名称
func get_rarity_name(rarity: String) -> String:
	match rarity:
		"common":
			return "普通"
		"rare":
			return "稀有"
		"epic":
			return "史诗"
		"legendary":
			return "传说"
		_:
			return "未知"
