extends Control
## HUD 脚本
## 显示玩家状态信息

## 顶部栏节点
@onready var energy_label: Label = $TopBar/EnergyPanel/VBox/HBox/EnergyLabel
@onready var energy_bar: ProgressBar = $TopBar/EnergyPanel/VBox/EnergyBar
@onready var level_label: Label = $TopBar/ExpPanel/VBox/HBox/LevelLabel
@onready var exp_bar: ProgressBar = $TopBar/ExpPanel/VBox/ExpBar
@onready var gold_label: Label = $TopBar/GoldPanel/HBox/GoldLabel
@onready var diamond_label: Label = $TopBar/DiamondPanel/HBox/DiamondLabel
@onready var vip_label: Label = $TopBar/VIPPanel/HBox/VIPLabel

## 心流指示器节点
@onready var flow_indicator: PanelContainer = $FlowIndicator
@onready var flow_label: Label = $FlowIndicator/VBox/HBox/FlowLabel
@onready var flow_bonus: Label = $FlowIndicator/VBox/FlowBonus

## 通知区域
@onready var notification_area: VBoxContainer = $NotificationArea

## 底部按钮
@onready var quest_button: Button = $BottomBar/QuestButton
@onready var achievement_button: Button = $BottomBar/AchievementButton
@onready var guild_button: Button = $BottomBar/GuildButton
@onready var pvp_button: Button = $BottomBar/PVPButton
@onready var decoration_button: Button = $BottomBar/DecorationButton
@onready var season_button: Button = $BottomBar/SeasonButton
@onready var settings_button: Button = $BottomBar/SettingsButton

## 头像相关节点
var avatar_display: Control = null
var avatar_selector: Control = null

## 面板实例
var quest_panel: Control = null
var achievement_panel: Control = null
var guild_panel: Control = null
var pvp_panel: Control = null
var decoration_panel: Control = null
var season_panel: Control = null
var settings_panel: Control = null

## 能量获取动画节点
var energy_popup_container: Control = null
var energy_popup_label: Label = null
var energy_animation_timer: Timer = null
var last_energy_popup_time: float = 0.0
const ENERGY_POPUP_COOLDOWN: float = 1.0  # 能量提示冷却时间（秒）

## 心流状态
var flow_time: float = 0.0
var is_in_flow: bool = false
var flow_pulse_tween: Tween = null

## 数值动画
var _target_energy: int = 0
var _target_exp: float = 0.0
var _target_gold: int = 0
var _target_diamonds: int = 0
var _display_energy: float = 0.0
var _display_exp: float = 0.0
var _display_gold: float = 0.0
var _display_diamonds: float = 0.0
const VALUE_LERP_SPEED: float = 8.0  # 数值变化速度

## 通知队列
var _notification_queue: Array[Dictionary] = []
var _active_notifications: Array[Control] = []
const MAX_NOTIFICATIONS: int = 5
const NOTIFICATION_DURATION: float = 3.0


func _ready() -> void:
	_setup_avatar_display()
	_setup_energy_popup()
	_setup_bottom_bar_buttons()
	_connect_signals()
	_init_display_values()
	_update_display()


## 设置头像显示组件
func _setup_avatar_display() -> void:
	"""创建头像显示组件，放置在TopBar左侧"""
	# 加载 AvatarDisplay 脚本
	var AvatarDisplayScript = load("res://scripts/avatar/avatar_display.gd")
	if not AvatarDisplayScript:
		push_warning("[HUD] 无法加载 AvatarDisplay 脚本")
		return

	# 创建头像显示组件
	avatar_display = AvatarDisplayScript.new()
	avatar_display.name = "AvatarDisplay"
	avatar_display.avatar_size = 1  # AvatarSize.MEDIUM = 48
	avatar_display.border_style = 2  # BorderStyle.RARITY
	avatar_display.clickable = true
	avatar_display.show_level_badge = true

	# 获取 TopBar 并插入头像
	var top_bar = get_node_or_null("TopBar")
	if top_bar:
		# 在 TopBar 最前面插入头像
		top_bar.add_child(avatar_display)
		top_bar.move_child(avatar_display, 0)

		# 连接点击信号
		if avatar_display.has_signal("avatar_clicked"):
			avatar_display.avatar_clicked.connect(_on_avatar_clicked)
	else:
		push_warning("[HUD] 未找到 TopBar 节点")
		avatar_display.queue_free()
		avatar_display = null


## 设置能量获取动画节点
func _setup_energy_popup() -> void:
	"""创建能量获取动画的UI节点"""
	# 创建容器，位于屏幕中心偏上位置
	energy_popup_container = Control.new()
	energy_popup_container.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	energy_popup_container.position = Vector2(0, -100)  # 距离顶部100像素
	energy_popup_container.z_index = 100  # 确保在最上层显示

	# 创建能量标签
	energy_popup_label = Label.new()
	energy_popup_label.text = "+0 能量"
	energy_popup_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	energy_popup_label.add_theme_font_size_override("font_size", 24)

	# 设置标签样式
	var stylebox = StyleBoxFlat.new()
	stylebox.bg_color = Color(0.2, 0.8, 0.2, 0.9)  # 深绿色背景
	stylebox.corner_radius_top_left = 8
	stylebox.corner_radius_top_right = 8
	stylebox.corner_radius_bottom_left = 8
	stylebox.corner_radius_bottom_right = 8
	energy_popup_label.add_theme_stylebox_override("panel", stylebox)

	# 初始隐藏
	energy_popup_container.visible = false
	energy_popup_container.add_child(energy_popup_label)
	add_child(energy_popup_container)


func _connect_signals() -> void:
	"""连接信号"""
	GameManager.energy_changed.connect(_on_energy_changed)
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.diamonds_changed.connect(_on_diamonds_changed)
	GameManager.exp_changed.connect(_on_exp_changed)
	GameManager.level_up.connect(_on_level_up)

	# 连接能量奖励信号（用于显示获取动画）
	if GameManager.has_signal("energy_awarded"):
		GameManager.energy_awarded.connect(_on_energy_awarded)

	EventBus.flow_state_entered.connect(_on_flow_entered)
	EventBus.flow_state_exited.connect(_on_flow_exited)

	# 成就解锁通知
	if EventBus.has_signal("achievement_unlocked"):
		EventBus.achievement_unlocked.connect(_on_achievement_unlocked)


## 初始化显示数值
func _init_display_values() -> void:
	"""初始化显示数值，避免动画从0开始"""
	_target_energy = GameManager.get_energy()
	_display_energy = float(_target_energy)

	_target_exp = GameManager.get_exp_progress()
	_display_exp = _target_exp

	_target_gold = GameManager.get_gold()
	_display_gold = float(_target_gold)

	_target_diamonds = GameManager.get_diamonds()
	_display_diamonds = float(_target_diamonds)


func _process(delta: float) -> void:
	# 心流计时
	if is_in_flow:
		flow_time += delta
		_update_flow_display()

	# 平滑数值动画
	_update_value_animations(delta)


## 更新数值动画
func _update_value_animations(delta: float) -> void:
	"""平滑更新显示数值"""
	var lerp_factor := 1.0 - exp(-VALUE_LERP_SPEED * delta)

	# 能量动画
	if abs(_display_energy - float(_target_energy)) > 0.5:
		_display_energy = lerpf(_display_energy, float(_target_energy), lerp_factor)
		_update_energy_display_value()

	# 经验动画
	if abs(_display_exp - _target_exp) > 0.001:
		_display_exp = lerpf(_display_exp, _target_exp, lerp_factor)
		_update_exp_display_value()

	# 金币动画
	if abs(_display_gold - float(_target_gold)) > 0.5:
		_display_gold = lerpf(_display_gold, float(_target_gold), lerp_factor)
		_update_gold_display_value()

	# 钻石动画
	if abs(_display_diamonds - float(_target_diamonds)) > 0.5:
		_display_diamonds = lerpf(_display_diamonds, float(_target_diamonds), lerp_factor)
		_update_diamond_display_value()


func _update_display() -> void:
	"""更新所有显示"""
	_update_energy_display()
	_update_exp_display()
	_update_gold_display()
	_update_diamond_display()
	_update_level_display()


func _update_energy_display() -> void:
	"""更新能量显示（设置目标值）"""
	_target_energy = GameManager.get_energy()
	var max_energy := GameManager.get_max_energy()
	if energy_bar:
		energy_bar.max_value = max_energy


func _update_energy_display_value() -> void:
	"""更新能量显示数值"""
	if energy_label:
		var max_energy := GameManager.get_max_energy()
		energy_label.text = "%d / %d" % [int(_display_energy), max_energy]
	if energy_bar:
		energy_bar.value = _display_energy


func _update_exp_display() -> void:
	"""更新经验显示（设置目标值）"""
	_target_exp = GameManager.get_exp_progress()


func _update_exp_display_value() -> void:
	"""更新经验显示数值"""
	if exp_bar:
		exp_bar.value = _display_exp * 100.0


func _update_gold_display() -> void:
	"""更新金币显示（设置目标值）"""
	_target_gold = GameManager.get_gold()


func _update_gold_display_value() -> void:
	"""更新金币显示数值"""
	if gold_label:
		gold_label.text = _format_number(int(_display_gold))


func _update_diamond_display() -> void:
	"""更新钻石显示（设置目标值）"""
	_target_diamonds = GameManager.get_diamonds()


func _update_diamond_display_value() -> void:
	"""更新钻石显示数值"""
	if diamond_label:
		diamond_label.text = _format_number(int(_display_diamonds))


func _update_level_display() -> void:
	"""更新等级显示"""
	if level_label:
		level_label.text = "Lv.%d" % GameManager.get_level()
	if vip_label:
		var vip_level := DataManager.player_data.vip_level if DataManager.player_data else 0
		vip_label.text = "VIP %d" % vip_level


## 格式化数字显示（大数字简化）
func _format_number(value: int) -> String:
	if value >= 1000000:
		return "%.1fM" % (value / 1000000.0)
	elif value >= 10000:
		return "%.1fK" % (value / 1000.0)
	else:
		return str(value)


func _update_flow_display() -> void:
	"""更新心流状态显示"""
	if flow_label:
		var minutes := int(flow_time) / 60
		var seconds := int(flow_time) % 60
		flow_label.text = "心流状态 %02d:%02d" % [minutes, seconds]

	# 更新心流加成显示
	if flow_bonus:
		var bonus := _calculate_flow_bonus()
		flow_bonus.text = "+%d%% 能量加成" % bonus


## 计算心流加成百分比
func _calculate_flow_bonus() -> int:
	# 基础加成 50%，每分钟额外 +5%，最高 200%
	var base_bonus := 50
	var time_bonus := int(flow_time / 60.0) * 5
	return mini(base_bonus + time_bonus, 200)


func _on_energy_changed(_current: int, _max_energy: int) -> void:
	_update_energy_display()


func _on_gold_changed(_value: int) -> void:
	_update_gold_display()


func _on_diamonds_changed(_value: int) -> void:
	_update_diamond_display()


func _on_exp_changed(_current: int, _needed: int) -> void:
	_update_exp_display()


func _on_level_up(new_level: int) -> void:
	_update_level_display()
	_update_exp_display()
	# 显示升级通知
	show_notification("🎉 升级！", "恭喜达到 Lv.%d" % new_level, Color(1.0, 0.84, 0.0))


func _on_flow_entered() -> void:
	"""进入心流状态"""
	is_in_flow = true
	flow_time = 0.0
	if flow_indicator:
		flow_indicator.visible = true
		_start_flow_pulse_animation()
	show_notification("🔥 心流状态", "进入心流，能量获取加成！", Color(1.0, 0.5, 0.0))


func _on_flow_exited(_duration: float) -> void:
	"""退出心流状态"""
	is_in_flow = false
	if flow_indicator:
		flow_indicator.visible = false
	_stop_flow_pulse_animation()
	var minutes := int(_duration) / 60
	show_notification("心流结束", "本次心流持续 %d 分钟" % minutes, Color(0.6, 0.6, 0.6))


## 开始心流脉冲动画
func _start_flow_pulse_animation() -> void:
	if flow_pulse_tween:
		flow_pulse_tween.kill()

	flow_pulse_tween = create_tween()
	flow_pulse_tween.set_loops()
	flow_pulse_tween.tween_property(flow_indicator, "modulate", Color(1.2, 1.0, 0.8, 1.0), 0.5)
	flow_pulse_tween.tween_property(flow_indicator, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.5)


## 停止心流脉冲动画
func _stop_flow_pulse_animation() -> void:
	if flow_pulse_tween:
		flow_pulse_tween.kill()
		flow_pulse_tween = null
	if flow_indicator:
		flow_indicator.modulate = Color(1.0, 1.0, 1.0, 1.0)


## 成就解锁处理
func _on_achievement_unlocked(achievement_id: String, achievement_name: String) -> void:
	show_notification("🏆 成就解锁", achievement_name, Color(1.0, 0.84, 0.0))


## ==================== 头像系统 ====================

## 头像点击处理
func _on_avatar_clicked() -> void:
	"""打开头像选择器"""
	_open_avatar_selector()


## 打开头像选择器
func _open_avatar_selector() -> void:
	"""创建并显示头像选择器"""
	if avatar_selector and is_instance_valid(avatar_selector):
		avatar_selector.open()
		return

	# 加载 AvatarSelector 脚本
	var AvatarSelectorScript = load("res://scripts/avatar/avatar_selector.gd")
	if not AvatarSelectorScript:
		push_warning("[HUD] 无法加载 AvatarSelector 脚本")
		return

	# 创建头像选择器
	avatar_selector = AvatarSelectorScript.new()
	avatar_selector.name = "AvatarSelector"

	# 连接信号
	avatar_selector.avatar_selected.connect(_on_avatar_selected)
	avatar_selector.closed.connect(_on_avatar_selector_closed)

	# 添加到场景树（作为 HUD 的子节点）
	add_child(avatar_selector)
	avatar_selector.open()


## 头像选择处理
func _on_avatar_selected(avatar_id: String) -> void:
	"""处理头像选择"""
	print("[HUD] 头像已选择: ", avatar_id)
	# 头像显示组件会自动更新（通过 AvatarManager 信号）


## 头像选择器关闭处理
func _on_avatar_selector_closed() -> void:
	"""处理头像选择器关闭"""
	# 可以选择销毁或保留选择器实例
	pass


## ==================== 能量获取动画 ====================

## 能量奖励处理
func _on_energy_awarded(amount: int, source: String) -> void:
	"""处理能量奖励事件，显示获取动画"""
	# 只显示大额能量获取（>=10），避免频繁提示
	if amount < 10:
		return

	var current_time := Time.get_unix_time_from_system()
	# 检查冷却时间
	if current_time - last_energy_popup_time < ENERGY_POPUP_COOLDOWN:
		return

	_show_energy_popup(amount)
	last_energy_popup_time = current_time


## 显示能量获取弹窗
func _show_energy_popup(amount: int) -> void:
	"""显示能量获取弹窗并播放动画"""
	if not energy_popup_container or not energy_popup_label:
		push_error("[HUD] 能量弹窗节点未初始化")
		return

	# 设置文本
	energy_popup_label.text = "+%d 能量" % amount

	# 显示并设置初始状态（透明度为0）
	energy_popup_container.modulate.a = 0.0
	energy_popup_container.position = Vector2(0, -100)  # 初始位置
	energy_popup_container.visible = true

	# 创建动画定时器
	if energy_animation_timer:
		energy_animation_timer.queue_free()

	energy_animation_timer = Timer.new()
	energy_animation_timer.wait_time = 0.02  # 每20ms更新一次
	energy_animation_timer.timeout.connect(_animate_energy_popup)
	energy_animation_timer.autostart = false

	# 手动触发第一次更新
	_animate_energy_popup()


## 能量弹窗动画帧更新
var _animation_progress: float = 0.0
var _animation_start_position: Vector2 = Vector2(0, -100)

func _animate_energy_popup() -> void:
	"""动画帧更新"""
	if not energy_popup_container or not energy_popup_container.visible:
		_clean_animation()
		return

	_animation_progress += 0.02

	# 淡入阶段（0.0 - 0.3秒）
	if _animation_progress <= 0.3:
		var alpha = _animation_progress / 0.3
		energy_popup_container.modulate.a = alpha

	# 上浮阶段（0.3 - 1.0秒）
	elif _animation_progress <= 1.0:
		var progress = (_animation_progress - 0.3) / 0.7
		# 向上移动 50 像素
		var target_y := -100 + (50 * progress)
		energy_popup_container.position = Vector2(0, target_y)

		# 淡出阶段
		var alpha = 1.0 - (progress * 0.5)  # 逐渐变半透明
		energy_popup_container.modulate.a = alpha

	# 动画完成，隐藏
	else:
		energy_popup_container.visible = false
		_clean_animation()


## 清理动画
func _clean_animation() -> void:
	"""清理动画资源"""
	if energy_animation_timer:
		energy_animation_timer.queue_free()
		energy_animation_timer = null
	_animation_progress = 0.0


## ==================== 底部按钮栏 ====================

## 设置底部按钮
func _setup_bottom_bar_buttons() -> void:
	"""连接底部按钮信号"""
	if quest_button:
		quest_button.pressed.connect(_on_quest_button_pressed)
	if achievement_button:
		achievement_button.pressed.connect(_on_achievement_button_pressed)
	if guild_button:
		guild_button.pressed.connect(_on_guild_button_pressed)
	if pvp_button:
		pvp_button.pressed.connect(_on_pvp_button_pressed)
	if decoration_button:
		decoration_button.pressed.connect(_on_decoration_button_pressed)
	if season_button:
		season_button.pressed.connect(_on_season_button_pressed)
	if settings_button:
		settings_button.pressed.connect(_on_settings_button_pressed)


## 任务按钮点击
func _on_quest_button_pressed() -> void:
	"""打开任务面板"""
	if quest_panel == null or not is_instance_valid(quest_panel):
		var panel_scene := load("res://scenes/ui/quest/quest_panel.tscn")
		if panel_scene:
			quest_panel = panel_scene.instantiate()
			add_child(quest_panel)
		else:
			push_warning("[HUD] 无法加载任务面板场景")
			return

	if quest_panel.visible:
		quest_panel.hide()
	else:
		_hide_all_panels()
		quest_panel.show()


## 装饰按钮点击
func _on_decoration_button_pressed() -> void:
	"""打开装饰面板"""
	if decoration_panel == null or not is_instance_valid(decoration_panel):
		var panel_scene := load("res://scenes/ui/decoration/decoration_panel.tscn")
		if panel_scene:
			decoration_panel = panel_scene.instantiate()
			add_child(decoration_panel)
		else:
			push_warning("[HUD] 无法加载装饰面板场景")
			return

	if decoration_panel.visible:
		decoration_panel.hide()
	else:
		_hide_all_panels()
		decoration_panel.show()


## 赛季按钮点击
func _on_season_button_pressed() -> void:
	"""打开赛季面板"""
	if season_panel == null or not is_instance_valid(season_panel):
		var panel_scene := load("res://scenes/ui/season/season_panel.tscn")
		if panel_scene:
			season_panel = panel_scene.instantiate()
			add_child(season_panel)
		else:
			push_warning("[HUD] 无法加载赛季面板场景")
			return

	if season_panel.visible:
		season_panel.hide()
	else:
		_hide_all_panels()
		season_panel.show()


## 设置按钮点击
func _on_settings_button_pressed() -> void:
	"""打开设置面板"""
	if settings_panel == null or not is_instance_valid(settings_panel):
		var panel_scene := load("res://scenes/ui/settings.tscn")
		if panel_scene:
			settings_panel = panel_scene.instantiate()
			add_child(settings_panel)
		else:
			push_warning("[HUD] 无法加载设置面板场景")
			return

	if settings_panel.visible:
		settings_panel.hide()
	else:
		_hide_all_panels()
		settings_panel.show()


## 隐藏所有面板
func _hide_all_panels() -> void:
	"""隐藏所有打开的面板"""
	if quest_panel and is_instance_valid(quest_panel):
		quest_panel.hide()
	if achievement_panel and is_instance_valid(achievement_panel):
		achievement_panel.hide()
	if guild_panel and is_instance_valid(guild_panel):
		guild_panel.hide()
	if pvp_panel and is_instance_valid(pvp_panel):
		pvp_panel.hide()
	if decoration_panel and is_instance_valid(decoration_panel):
		decoration_panel.hide()
	if season_panel and is_instance_valid(season_panel):
		season_panel.hide()
	if settings_panel and is_instance_valid(settings_panel):
		settings_panel.hide()


## ==================== 新增面板按钮 ====================

## 成就按钮点击
func _on_achievement_button_pressed() -> void:
	"""打开成就面板"""
	if achievement_panel == null or not is_instance_valid(achievement_panel):
		var panel_scene := load("res://scenes/ui/achievement/achievement_panel.tscn")
		if panel_scene:
			achievement_panel = panel_scene.instantiate()
			add_child(achievement_panel)
		else:
			push_warning("[HUD] 无法加载成就面板场景")
			return

	if achievement_panel.visible:
		achievement_panel.hide()
	else:
		_hide_all_panels()
		achievement_panel.show()


## 公会按钮点击
func _on_guild_button_pressed() -> void:
	"""打开公会面板"""
	if guild_panel == null or not is_instance_valid(guild_panel):
		var panel_scene := load("res://scenes/ui/guild/guild_panel.tscn")
		if panel_scene:
			guild_panel = panel_scene.instantiate()
			add_child(guild_panel)
		else:
			push_warning("[HUD] 无法加载公会面板场景")
			return

	if guild_panel.visible:
		guild_panel.hide()
	else:
		_hide_all_panels()
		guild_panel.show()


## PVP 按钮点击
func _on_pvp_button_pressed() -> void:
	"""打开 PVP 竞技场面板"""
	if pvp_panel == null or not is_instance_valid(pvp_panel):
		var panel_scene := load("res://scenes/ui/pvp/pvp_panel.tscn")
		if panel_scene:
			pvp_panel = panel_scene.instantiate()
			add_child(pvp_panel)
		else:
			push_warning("[HUD] 无法加载 PVP 面板场景")
			return

	if pvp_panel.visible:
		pvp_panel.hide()
	else:
		_hide_all_panels()
		pvp_panel.show()


## ==================== 通知系统 ====================

## 显示通知
func show_notification(title: String, message: String, color: Color = Color.WHITE) -> void:
	"""显示一条通知"""
	_notification_queue.append({
		"title": title,
		"message": message,
		"color": color
	})
	_process_notification_queue()


## 处理通知队列
func _process_notification_queue() -> void:
	"""处理等待中的通知"""
	while _notification_queue.size() > 0 and _active_notifications.size() < MAX_NOTIFICATIONS:
		var notif_data: Dictionary = _notification_queue.pop_front()
		_create_notification(notif_data)


## 创建通知UI
func _create_notification(data: Dictionary) -> void:
	"""创建通知面板"""
	if not notification_area:
		return

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(300, 60)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 2)

	var title_label := Label.new()
	title_label.text = data.get("title", "")
	title_label.add_theme_color_override("font_color", data.get("color", Color.WHITE))
	title_label.add_theme_font_size_override("font_size", 16)

	var msg_label := Label.new()
	msg_label.text = data.get("message", "")
	msg_label.add_theme_font_size_override("font_size", 14)
	msg_label.add_theme_color_override("font_color", Color(0.8, 0.8, 0.8))

	vbox.add_child(title_label)
	vbox.add_child(msg_label)
	panel.add_child(vbox)

	# 初始透明
	panel.modulate.a = 0.0
	notification_area.add_child(panel)
	_active_notifications.append(panel)

	# 淡入动画
	var tween := create_tween()
	tween.tween_property(panel, "modulate:a", 1.0, 0.3)
	tween.tween_interval(NOTIFICATION_DURATION)
	tween.tween_property(panel, "modulate:a", 0.0, 0.3)
	tween.tween_callback(_remove_notification.bind(panel))


## 移除通知
func _remove_notification(panel: Control) -> void:
	"""移除通知面板"""
	if panel in _active_notifications:
		_active_notifications.erase(panel)
	if is_instance_valid(panel):
		panel.queue_free()
	_process_notification_queue()
