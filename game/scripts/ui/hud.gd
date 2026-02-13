extends Control
## HUD 脚本
## 显示玩家状态信息

@onready var energy_label: Label = $TopBar/EnergyPanel/HBox/EnergyLabel
@onready var gold_label: Label = $TopBar/GoldPanel/HBox/GoldLabel
@onready var level_label: Label = $TopBar/LevelPanel/HBox/LevelLabel
@onready var flow_indicator: PanelContainer = $FlowIndicator
@onready var flow_label: Label = $FlowIndicator/HBox/FlowLabel

## 能量获取动画节点
var energy_popup_container: Control = null
var energy_popup_label: Label = null
var energy_animation_timer: Timer = null
var last_energy_popup_time: float = 0.0
const ENERGY_POPUP_COOLDONN: float = 1.0  # 能量提示冷却时间（秒）

var flow_time: float = 0.0
var is_in_flow: bool = false


func _ready() -> void:
	_setup_energy_popup()
	_connect_signals()
	_update_display()


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
	GameManager.level_up.connect(_on_level_up)

	# 连接能量奖励信号（用于显示获取动画）
	if GameManager.has_signal("energy_awarded"):
		GameManager.energy_awarded.connect(_on_energy_awarded)

	EventBus.flow_state_entered.connect(_on_flow_entered)
	EventBus.flow_state_exited.connect(_on_flow_exited)


func _process(delta: float) -> void:
	if is_in_flow:
		flow_time += delta
		_update_flow_display()


func _update_display() -> void:
	"""更新所有显示"""
	_update_energy_display()
	_update_gold_display()
	_update_level_display()


func _update_energy_display() -> void:
	"""更新能量显示"""
	if energy_label:
		var energy := GameManager.get_energy()
		var max_energy := GameManager.get_max_energy()
		energy_label.text = "能量: %d/%d" % [energy, max_energy]


func _update_gold_display() -> void:
	"""更新金币显示"""
	if gold_label:
		gold_label.text = str(GameManager.get_gold())


func _update_level_display() -> void:
	"""更新等级显示"""
	if level_label:
		level_label.text = "Lv.%d" % GameManager.get_level()


func _update_flow_display() -> void:
	"""更新心流状态显示"""
	if flow_label:
		var minutes := int(flow_time) / 60
		var seconds := int(flow_time) % 60
		flow_label.text = "心流状态 %02d:%02d" % [minutes, seconds]


func _on_energy_changed(_value: int) -> void:
	_update_energy_display()


func _on_gold_changed(_value: int) -> void:
	_update_gold_display()


func _on_level_up(_new_level: int) -> void:
	_update_level_display()


func _on_flow_entered() -> void:
	"""进入心流状态"""
	is_in_flow = true
	flow_time = 0.0
	if flow_indicator:
		flow_indicator.visible = true


func _on_flow_exited(_duration: float) -> void:
	"""退出心流状态"""
	is_in_flow = false
	if flow_indicator:
		flow_indicator.visible = false


## ==================== 能量获取动画 ====================

## 能量奖励处理
func _on_energy_awarded(amount: int, source: String) -> void:
	"""处理能量奖励事件，显示获取动画"""
	# 只显示大额能量获取（>=10），避免频繁提示
	if amount < 10:
		return

	var current_time := Time.get_unix_time_from_system()
	# 检查冷却时间
	if current_time - last_energy_popup_time < ENERGY_POPUP_COOLDONN:
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
