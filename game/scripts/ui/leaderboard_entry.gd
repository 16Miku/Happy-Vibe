## leaderboard_entry.gd
## 排行榜条目 UI 组件
extends Control

## 排行榜数据
var entry_data: Dictionary = {}

## 排名
var rank: int = 0

## 是否是玩家自己
var is_myself: bool = false

@onready var rank_label: Label = $HBox/RankLabel
@onready var rank_icon: Label = $HBox/RankIcon
@onready var avatar_label: Label = $HBox/AvatarLabel
@onready var name_label: Label = $HBox/VBox/NameLabel
@onready var value_label: Label = $HBox/VBox/ValueLabel

## 前三名排名图标
var rank_icons := {
	1: "🥇",
	2: "🥈",
	3: "🥉"
}

func _ready() -> void:
	pass


## 设置条目数据
func set_entry_data(data: Dictionary) -> void:
	entry_data = data
	rank = data.get("rank", 0)

	# 检查是否是自己
	var player_id := ""
	if DataManager and DataManager.player_data:
		player_id = DataManager.player_data.id
	is_myself = (data.get("player_id", "") == player_id)

	_update_display()


## 更新显示
func _update_display() -> void:
	if entry_data.is_empty():
		return

	# 设置排名
	if rank_label:
		rank_label.text = "#%d" % rank

	# 设置排名图标
	if rank_icon:
		if rank_icons.has(rank):
			rank_icon.text = rank_icons[rank]
			rank_icon.visible = true
			if rank_label:
				rank_label.visible = false
		else:
			rank_icon.visible = false
			if rank_label:
				rank_label.visible = true

	# 设置头像
	if avatar_label:
		avatar_label.text = entry_data.get("avatar", "👤")

	# 设置名称
	if name_label:
		name_label.text = entry_data.get("username", "Player")

	# 设置数值
	if value_label:
		value_label.text = str(entry_data.get("value", 0))

	# 如果是自己，高亮显示
	if is_myself:
		modulate = Color(1.0, 1.0, 0.8)  # 淡黄色高亮
	else:
		modulate = Color(1.0, 1.0, 1.0)
