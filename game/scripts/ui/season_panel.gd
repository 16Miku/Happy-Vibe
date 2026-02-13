## season_panel.gd
## 赛季面板 UI - 显示赛季通行证、季节效果、奖励领取
extends Control

# 枚举引用
const Season = preload("res://scripts/season/season_manager.gd").Season
const SeasonPassTier = preload("res://scripts/season/season_manager.gd").SeasonPassTier

# 节点引用
@onready var season_icon: TextureRect = $MarginContainer/VBoxContainer/Header/SeasonIcon
@onready var season_name_label: Label = $MarginContainer/VBoxContainer/Header/TitleContainer/SeasonName
@onready var time_remaining_label: Label = $MarginContainer/VBoxContainer/Header/TimeRemaining
@onready var close_button: Button = $MarginContainer/VBoxContainer/Header/CloseButton
@onready var level_label: Label = $MarginContainer/VBoxContainer/LevelContainer/LevelInfo/LevelLabel
@onready var exp_label: Label = $MarginContainer/VBoxContainer/LevelContainer/LevelInfo/ExpLabel
@onready var exp_progress_bar: ProgressBar = $MarginContainer/VBoxContainer/LevelContainer/ExpProgressBar
@onready var premium_button: Button = $MarginContainer/VBoxContainer/LevelContainer/PremiumButton
@onready var crop_bonus_label: Label = $MarginContainer/VBoxContainer/SeasonEffects/CropBonus
@onready var energy_bonus_label: Label = $MarginContainer/VBoxContainer/SeasonEffects/EnergyBonus
@onready var gold_bonus_label: Label = $MarginContainer/VBoxContainer/SeasonEffects/GoldBonus
@onready var reward_track: HBoxContainer = $MarginContainer/VBoxContainer/RewardScrollContainer/RewardTrack
@onready var claim_all_button: Button = $MarginContainer/VBoxContainer/ClaimAllButton

# 奖励项场景
var reward_item_scene: PackedScene = preload("res://scenes/ui/season/season_reward_item.tscn")

# 刷新计时器
var refresh_timer: Timer


func _ready() -> void:
	_setup_ui()
	_connect_signals()
	_update_display()
	_load_reward_track()
	_start_refresh_timer()


func _setup_ui() -> void:
	close_button.pressed.connect(_on_close_pressed)
	premium_button.pressed.connect(_on_premium_pressed)
	claim_all_button.pressed.connect(_on_claim_all_pressed)


func _connect_signals() -> void:
	if SeasonManager:
		SeasonManager.season_changed.connect(_on_season_changed)
		SeasonManager.season_pass_level_up.connect(_on_level_up)
		SeasonManager.season_pass_reward_claimed.connect(_on_reward_claimed)
		SeasonManager.season_pass_purchased.connect(_on_premium_purchased)


func _start_refresh_timer() -> void:
	refresh_timer = Timer.new()
	refresh_timer.wait_time = 60.0  # 每分钟更新一次
	refresh_timer.autostart = true
	refresh_timer.timeout.connect(_update_time_remaining)
	add_child(refresh_timer)


## 更新显示
func _update_display() -> void:
	if not SeasonManager:
		return

	# 季节信息
	var current_season: int = SeasonManager.get_current_season()
	season_name_label.text = "当前季节: " + SeasonManager.get_season_name()

	# 季节图标
	var icon_path: String = SeasonData.get_season_icon_path(current_season)
	if ResourceLoader.exists(icon_path):
		season_icon.texture = load(icon_path)

	# 等级信息
	var level: int = SeasonManager.get_season_pass_level()
	var exp: int = SeasonManager.get_season_pass_exp()
	var exp_needed: int = SeasonManager.get_exp_needed()

	level_label.text = "等级 %d" % level
	exp_label.text = "%d / %d 经验" % [exp, exp_needed]
	exp_progress_bar.max_value = exp_needed
	exp_progress_bar.value = exp

	# 高级通行证按钮
	if SeasonManager.has_premium_pass():
		premium_button.text = "已拥有高级通行证"
		premium_button.disabled = true
	else:
		premium_button.text = "购买高级通行证\n980 钻石"
		premium_button.disabled = false

	# 季节效果
	_update_season_effects()

	# 剩余时间
	_update_time_remaining()

	# 一键领取按钮
	var claimable: int = SeasonManager.get_claimable_rewards_count()
	if claimable > 0:
		claim_all_button.text = "一键领取所有奖励 (%d)" % claimable
		claim_all_button.disabled = false
	else:
		claim_all_button.text = "暂无可领取奖励"
		claim_all_button.disabled = true


## 更新季节效果显示
func _update_season_effects() -> void:
	if not SeasonManager:
		return

	var crop_bonus: float = SeasonManager.get_crop_growth_bonus()
	var energy_bonus: float = SeasonManager.get_energy_bonus()
	var gold_bonus: float = SeasonManager.get_gold_bonus()

	crop_bonus_label.text = "作物生长 %+d%%" % [int((crop_bonus - 1.0) * 100)]
	energy_bonus_label.text = "能量获取 %+d%%" % [int((energy_bonus - 1.0) * 100)]
	gold_bonus_label.text = "金币收益 %+d%%" % [int((gold_bonus - 1.0) * 100)]

	# 根据加成值设置颜色
	crop_bonus_label.modulate = Color(0.5, 0.9, 0.5) if crop_bonus >= 1.0 else Color(0.9, 0.5, 0.5)
	energy_bonus_label.modulate = Color(0.5, 0.9, 0.5) if energy_bonus >= 1.0 else Color(0.9, 0.5, 0.5)
	gold_bonus_label.modulate = Color(0.5, 0.9, 0.5) if gold_bonus >= 1.0 else Color(0.9, 0.5, 0.5)


## 更新剩余时间
func _update_time_remaining() -> void:
	if not SeasonManager:
		return

	var remaining_days: int = SeasonManager.get_season_remaining_days()
	if remaining_days > 0:
		time_remaining_label.text = "剩余: %d 天" % remaining_days
	else:
		time_remaining_label.text = "赛季即将结束"
		time_remaining_label.modulate = Color(0.9, 0.3, 0.3)


## 加载奖励轨道
func _load_reward_track() -> void:
	# 清空现有奖励项
	for child in reward_track.get_children():
		child.queue_free()

	if not SeasonManager:
		return

	var current_level: int = SeasonManager.get_season_pass_level()
	var has_premium: bool = SeasonManager.has_premium_pass()
	var all_rewards: Array = SeasonData.get_all_season_pass_rewards()

	for reward_data in all_rewards:
		var level: int = reward_data.get("level", 0)
		var item: Control = reward_item_scene.instantiate()

		var free_reward: Dictionary = reward_data.get("free", {})
		var premium_reward: Dictionary = reward_data.get("premium", {})

		var free_claimed: bool = SeasonManager.is_reward_claimed(level, SeasonPassTier.FREE)
		var premium_claimed: bool = SeasonManager.is_reward_claimed(level, SeasonPassTier.PREMIUM)

		item.setup(level, free_reward, premium_reward, current_level, has_premium, free_claimed, premium_claimed)
		item.free_claim_pressed.connect(_on_free_claim_pressed.bind(level))
		item.premium_claim_pressed.connect(_on_premium_claim_pressed.bind(level))

		reward_track.add_child(item)


# ==================== 事件处理 ====================

func _on_close_pressed() -> void:
	hide()
	if EventBus:
		EventBus.close_panel.emit("season")


func _on_premium_pressed() -> void:
	if SeasonManager:
		# 显示确认对话框
		if EventBus:
			EventBus.request_confirm(
				"购买高级通行证",
				"确定花费 980 钻石购买高级通行证吗？\n\n高级通行证包含额外奖励和独家装饰！",
				_confirm_premium_purchase
			)


func _confirm_premium_purchase() -> void:
	if SeasonManager:
		SeasonManager.purchase_premium_pass()


func _on_claim_all_pressed() -> void:
	if not SeasonManager:
		return

	var current_level: int = SeasonManager.get_season_pass_level()
	var has_premium: bool = SeasonManager.has_premium_pass()

	for level in range(1, current_level + 1):
		# 领取免费奖励
		if not SeasonManager.is_reward_claimed(level, SeasonPassTier.FREE):
			SeasonManager.claim_season_reward(level, SeasonPassTier.FREE)

		# 领取高级奖励
		if has_premium and not SeasonManager.is_reward_claimed(level, SeasonPassTier.PREMIUM):
			SeasonManager.claim_season_reward(level, SeasonPassTier.PREMIUM)

	_load_reward_track()
	_update_display()


func _on_free_claim_pressed(level: int) -> void:
	if SeasonManager:
		SeasonManager.claim_season_reward(level, SeasonPassTier.FREE)
		_load_reward_track()
		_update_display()


func _on_premium_claim_pressed(level: int) -> void:
	if SeasonManager:
		SeasonManager.claim_season_reward(level, SeasonPassTier.PREMIUM)
		_load_reward_track()
		_update_display()


func _on_season_changed(_new_season: int) -> void:
	_update_display()
	_load_reward_track()


func _on_level_up(_new_level: int) -> void:
	_update_display()
	_load_reward_track()


func _on_reward_claimed(_level: int, _tier: int) -> void:
	_update_display()


func _on_premium_purchased() -> void:
	_update_display()
	_load_reward_track()


## 显示面板
func show_panel() -> void:
	_update_display()
	_load_reward_track()
	show()


## 隐藏面板
func hide_panel() -> void:
	hide()
