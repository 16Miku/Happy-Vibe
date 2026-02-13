## season_manager.gd
## 赛季管理器 - 管理游戏赛季、季节效果、赛季奖励
## 作为 AutoLoad 单例运行
extends Node

# 季节枚举
enum Season {
	SPRING,  # 春季
	SUMMER,  # 夏季
	AUTUMN,  # 秋季
	WINTER   # 冬季
}

# 赛季状态枚举
enum SeasonPassTier {
	FREE,     # 免费通行证
	PREMIUM   # 高级通行证
}

# 信号定义
signal season_changed(new_season: Season)
signal season_pass_level_up(new_level: int)
signal season_pass_reward_claimed(level: int, tier: SeasonPassTier)
signal season_pass_purchased()
signal season_event_started(event_id: String)
signal season_event_ended(event_id: String)

# 当前季节
var current_season: Season = Season.SPRING

# 赛季通行证数据
var season_pass_data: Dictionary = {
	"level": 1,
	"exp": 0,
	"has_premium": false,
	"claimed_free": [],    # 已领取的免费奖励等级
	"claimed_premium": [], # 已领取的高级奖励等级
	"season_id": "",       # 当前赛季ID
	"start_time": 0,
	"end_time": 0
}

# 季节效果
var season_effects: Dictionary = {}

# 常量
const SEASON_DURATION_DAYS: int = 90        # 赛季持续天数
const MAX_SEASON_PASS_LEVEL: int = 50       # 赛季通行证最大等级
const EXP_PER_LEVEL: int = 1000             # 每级所需经验
const PREMIUM_PASS_PRICE: int = 980         # 高级通行证价格（钻石）


func _ready() -> void:
	_load_season_data()
	_update_current_season()
	_apply_season_effects()
	_connect_signals()


## 加载赛季数据
func _load_season_data() -> void:
	if SaveManager:
		var save_data: Dictionary = SaveManager.load_game()
		if save_data.has("season_pass"):
			season_pass_data = save_data["season_pass"]
		else:
			_init_new_season()
	else:
		_init_new_season()


## 初始化新赛季
func _init_new_season() -> void:
	var current_time: int = int(Time.get_unix_time_from_system())
	var season_id: String = _generate_season_id()

	season_pass_data = {
		"level": 1,
		"exp": 0,
		"has_premium": false,
		"claimed_free": [],
		"claimed_premium": [],
		"season_id": season_id,
		"start_time": current_time,
		"end_time": current_time + (SEASON_DURATION_DAYS * 86400)
	}
	_save_season_data()


## 生成赛季ID
func _generate_season_id() -> String:
	var datetime := Time.get_datetime_dict_from_system()
	var quarter: int = (datetime.month - 1) / 3 + 1
	return "S%d_Q%d" % [datetime.year, quarter]


## 更新当前季节
func _update_current_season() -> void:
	var datetime := Time.get_datetime_dict_from_system()
	var month: int = datetime.month

	var old_season: Season = current_season

	if month >= 3 and month <= 5:
		current_season = Season.SPRING
	elif month >= 6 and month <= 8:
		current_season = Season.SUMMER
	elif month >= 9 and month <= 11:
		current_season = Season.AUTUMN
	else:
		current_season = Season.WINTER

	if old_season != current_season:
		season_changed.emit(current_season)


## 应用季节效果
func _apply_season_effects() -> void:
	season_effects = SeasonData.get_season_effects(current_season)


## 连接信号
func _connect_signals() -> void:
	if EventBus:
		EventBus.vibe_energy_received.connect(_on_energy_received)
		EventBus.quest_completed.connect(_on_quest_completed)
		EventBus.crop_harvested.connect(_on_crop_harvested)


## 保存赛季数据
func _save_season_data() -> void:
	if SaveManager and GameManager:
		var player_data: Dictionary = GameManager.player_data.duplicate(true)
		player_data["season_pass"] = season_pass_data
		SaveManager.save_game(player_data)


# ==================== 赛季通行证 ====================

## 获取当前赛季通行证等级
func get_season_pass_level() -> int:
	return season_pass_data.get("level", 1)


## 获取当前赛季通行证经验
func get_season_pass_exp() -> int:
	return season_pass_data.get("exp", 0)


## 获取升级所需经验
func get_exp_needed() -> int:
	return EXP_PER_LEVEL


## 获取经验进度百分比
func get_exp_progress() -> float:
	return float(get_season_pass_exp()) / float(EXP_PER_LEVEL)


## 是否拥有高级通行证
func has_premium_pass() -> bool:
	return season_pass_data.get("has_premium", false)


## 添加赛季经验
func add_season_exp(amount: int) -> void:
	if amount <= 0:
		return

	var current_level: int = season_pass_data.get("level", 1)
	if current_level >= MAX_SEASON_PASS_LEVEL:
		return

	season_pass_data["exp"] = season_pass_data.get("exp", 0) + amount

	# 检查升级
	while season_pass_data["exp"] >= EXP_PER_LEVEL and current_level < MAX_SEASON_PASS_LEVEL:
		season_pass_data["exp"] -= EXP_PER_LEVEL
		current_level += 1
		season_pass_data["level"] = current_level
		season_pass_level_up.emit(current_level)

		if EventBus:
			EventBus.notify_success("赛季通行证升级! 等级 %d" % current_level)

	_save_season_data()


## 购买高级通行证
func purchase_premium_pass() -> bool:
	if season_pass_data.get("has_premium", false):
		if EventBus:
			EventBus.notify_warning("已拥有高级通行证")
		return false

	if not GameManager:
		return false

	if GameManager.get_diamonds() < PREMIUM_PASS_PRICE:
		if EventBus:
			EventBus.notify_warning("钻石不足")
		return false

	if GameManager.spend_diamonds(PREMIUM_PASS_PRICE):
		season_pass_data["has_premium"] = true
		season_pass_purchased.emit()
		_save_season_data()

		if EventBus:
			EventBus.notify_success("成功购买高级通行证!")
		return true

	return false


## 领取赛季奖励
func claim_season_reward(level: int, tier: SeasonPassTier) -> Dictionary:
	if level < 1 or level > MAX_SEASON_PASS_LEVEL:
		return {}

	if level > season_pass_data.get("level", 1):
		if EventBus:
			EventBus.notify_warning("等级不足")
		return {}

	var claimed_key: String = "claimed_free" if tier == SeasonPassTier.FREE else "claimed_premium"

	if level in season_pass_data.get(claimed_key, []):
		if EventBus:
			EventBus.notify_warning("已领取该奖励")
		return {}

	if tier == SeasonPassTier.PREMIUM and not has_premium_pass():
		if EventBus:
			EventBus.notify_warning("需要高级通行证")
		return {}

	# 获取奖励
	var rewards: Dictionary = SeasonData.get_season_pass_reward(level, tier)
	if rewards.is_empty():
		return {}

	# 发放奖励
	_grant_rewards(rewards)

	# 标记已领取
	if not season_pass_data.has(claimed_key):
		season_pass_data[claimed_key] = []
	season_pass_data[claimed_key].append(level)

	season_pass_reward_claimed.emit(level, tier)
	_save_season_data()

	if EventBus:
		EventBus.show_rewards(rewards)

	return rewards


## 发放奖励
func _grant_rewards(rewards: Dictionary) -> void:
	if not GameManager:
		return

	if rewards.has("gold"):
		GameManager.add_gold(rewards["gold"])

	if rewards.has("diamonds"):
		GameManager.add_diamonds(rewards["diamonds"])

	if rewards.has("energy"):
		GameManager.add_energy(rewards["energy"])

	if rewards.has("exp"):
		GameManager.add_exp(rewards["exp"])

	if rewards.has("items"):
		for item in rewards["items"]:
			if EventBus:
				EventBus.item_added.emit(item.get("id", ""), item.get("quantity", 1))

	if rewards.has("decoration"):
		if DecorationManager:
			DecorationManager.add_decoration(rewards["decoration"], 1)


## 检查奖励是否已领取
func is_reward_claimed(level: int, tier: SeasonPassTier) -> bool:
	var claimed_key: String = "claimed_free" if tier == SeasonPassTier.FREE else "claimed_premium"
	return level in season_pass_data.get(claimed_key, [])


## 获取可领取的奖励数量
func get_claimable_rewards_count() -> int:
	var count: int = 0
	var current_level: int = get_season_pass_level()

	for level in range(1, current_level + 1):
		if not is_reward_claimed(level, SeasonPassTier.FREE):
			count += 1
		if has_premium_pass() and not is_reward_claimed(level, SeasonPassTier.PREMIUM):
			count += 1

	return count


# ==================== 季节效果 ====================

## 获取当前季节
func get_current_season() -> Season:
	return current_season


## 获取季节名称
func get_season_name() -> String:
	return SeasonData.get_season_name(current_season)


## 获取作物生长加成
func get_crop_growth_bonus() -> float:
	return season_effects.get("crop_growth_bonus", 1.0)


## 获取能量加成
func get_energy_bonus() -> float:
	return season_effects.get("energy_bonus", 1.0)


## 获取金币加成
func get_gold_bonus() -> float:
	return season_effects.get("gold_bonus", 1.0)


## 获取当前季节的特殊作物
func get_seasonal_crops() -> Array:
	return SeasonData.get_seasonal_crops(current_season)


## 检查作物是否是当季作物
func is_seasonal_crop(crop_id: String) -> bool:
	return crop_id in get_seasonal_crops()


# ==================== 赛季剩余时间 ====================

## 获取赛季剩余时间（秒）
func get_season_remaining_time() -> int:
	var current_time: int = int(Time.get_unix_time_from_system())
	var end_time: int = season_pass_data.get("end_time", current_time)
	return maxi(0, end_time - current_time)


## 获取赛季剩余天数
func get_season_remaining_days() -> int:
	return get_season_remaining_time() / 86400


## 检查赛季是否结束
func is_season_ended() -> bool:
	return get_season_remaining_time() <= 0


# ==================== 事件处理 ====================

## 能量获得事件
func _on_energy_received(energy: int, _exp: int, _is_flow: bool) -> void:
	# 每获得 100 能量，获得 10 赛季经验
	var season_exp: int = energy / 10
	if season_exp > 0:
		add_season_exp(season_exp)


## 任务完成事件
func _on_quest_completed(_quest_id: String) -> void:
	# 完成任务获得赛季经验
	add_season_exp(50)


## 作物收获事件
func _on_crop_harvested(_plot_id: String, crop_data: Dictionary) -> void:
	# 收获当季作物获得额外赛季经验
	var crop_type: String = crop_data.get("type", "")
	if is_seasonal_crop(crop_type):
		add_season_exp(20)
	else:
		add_season_exp(5)
