## guild_item.gd
## 公会列表项 UI 组件
extends Control

## 公会数据
var guild_data: DataManager.GuildData = null

## 公会 ID
var guild_id: String = ""

## 是否被选中
var is_selected: bool = false

signal guild_selected(guild_id: String)

@onready var name_label: Label = $HBox/VBox/NameLabel
@onready var level_label: Label = $HBox/VBox/LevelLabel
@onready var members_label: Label = $HBox/VBox/MembersLabel
@onready var rank_label: Label = $HBox/RankLabel
@onready var select_button: Button = $HBox/SelectButton

func _ready() -> void:
	if select_button:
		select_button.pressed.connect(_on_select_pressed)


## 设置公会数据
func set_guild_data(guild: DataManager.GuildData) -> void:
	guild_data = guild
	guild_id = guild.id
	_update_display()


## 更新显示
func _update_display() -> void:
	if not guild_data:
		return

	if name_label:
		name_label.text = guild_data.name
	if level_label:
		level_label.text = "Lv.%d" % guild_data.level
	if members_label:
		members_label.text = "成员: %d/%d" % [guild_data.member_count, guild_data.max_members]
	if rank_label:
		rank_label.text = "#%d" % guild_data.rank if guild_data.rank > 0 else "未上榜"


## 设置选中状态
func set_selected(selected: bool) -> void:
	is_selected = selected

	# 更新按钮状态
	if select_button:
		select_button.disabled = selected
		select_button.text = "已选择" if selected else "加入"


## 选择按钮点击
func _on_select_pressed() -> void:
	guild_selected.emit(guild_id)
