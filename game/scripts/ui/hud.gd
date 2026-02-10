extends Control
## HUD 脚本
## 显示玩家状态信息

@onready var energy_label: Label = $TopBar/EnergyPanel/HBox/EnergyLabel
@onready var gold_label: Label = $TopBar/GoldPanel/HBox/GoldLabel
@onready var level_label: Label = $TopBar/LevelPanel/HBox/LevelLabel
@onready var flow_indicator: PanelContainer = $FlowIndicator
@onready var flow_label: Label = $FlowIndicator/HBox/FlowLabel

var flow_time: float = 0.0
var is_in_flow: bool = false


func _ready() -> void:
	_connect_signals()
	_update_display()


func _connect_signals() -> void:
	"""连接信号"""
	GameManager.energy_changed.connect(_on_energy_changed)
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.level_up.connect(_on_level_up)
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
