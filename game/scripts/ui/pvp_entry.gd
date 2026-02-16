## pvp_entry.gd
## PVP 排行榜条目 UI 组件
extends Control

## 条目数据
var entry_data: DataManager.PVPEntry = null

## 历史记录数据
var history_data: DataManager.PVPMatchRecord = null

## 是否是历史记录模式
var is_history_mode: bool = false

@onready var rank_label: Label = $HBox/RankLabel
@onready var tier_icon: Label = $HBox/TierIcon
@onready var name_label: Label = $HBox/VBox/NameLabel
@onready var rating_label: Label = $HBox/VBox/RatingLabel
@onready var stats_label: Label = $HBox/VBox/StatsLabel
@onready var result_label: Label = $HBox/ResultLabel

## 结果文本配置
var result_config := {
	"win": {"text": "胜利", "color": Color(0.2, 0.8, 0.2)},
	"loss": {"text": "失败", "color": Color(0.8, 0.2, 0.2)},
	"draw": {"text": "平局", "color": Color(0.8, 0.8, 0.8)}
}

func _ready() -> void:
	pass


## 设置排行榜条目数据
func set_entry_data(entry: DataManager.PVPEntry) -> void:
	is_history_mode = false
	entry_data = entry
	history_data = null
	_update_display()


## 设置历史记录数据
func set_history_data(record: DataManager.PVPMatchRecord) -> void:
	is_history_mode = true
	history_data = record
	entry_data = null
	_update_display()


## 更新显示
func _update_display() -> void:
	if is_history_mode:
		_update_history_display()
	else:
		_update_rank_display()


## 更新排行榜显示
func _update_rank_display() -> void:
	if not entry_data:
		return

	if rank_label:
		rank_label.text = "#%d" % entry_data.rank
		rank_label.visible = true

	if tier_icon:
		tier_icon.text = _get_tier_icon(entry_data.tier)

	if name_label:
		name_label.text = entry_data.username

	if rating_label:
		rating_label.text = "积分: %d" % entry_data.rating

	if stats_label:
		stats_label.text = "%d胜 %d负" % [entry_data.wins, entry_data.losses]

	if result_label:
		result_label.visible = false


## 更新历史记录显示
func _update_history_display() -> void:
	if not history_data:
		return

	if rank_label:
		rank_label.visible = false

	if tier_icon:
		tier_icon.visible = false

	if name_label:
		name_label.text = "VS %s" % history_data.opponent_name

	if rating_label:
		var change_text := "+%d" % history_data.rating_change if history_data.rating_change > 0 else str(history_data.rating_change)
		rating_label.text = "积分变化: %s" % change_text
		rating_label.modulate = Color(0.2, 0.8, 0.2) if history_data.rating_change > 0 else Color(0.8, 0.2, 0.2)

	if stats_label:
		var datetime = Time.get_datetime_dict_from_unix_time(history_data.timestamp)
		stats_label.text = "%02d/%02d %02d:%02d" % [datetime.month, datetime.day, datetime.hour, datetime.minute]

	if result_label:
		result_label.visible = true
		if result_config.has(history_data.result):
			var config = result_config[history_data.result]
			result_label.text = config["text"]
			result_label.modulate = config["color"]


## 获取段位图标
func _get_tier_icon(tier: String) -> String:
	match tier:
		"bronze":
			return "🥉"
		"silver":
			return "🥈"
		"gold":
			return "🥇"
		"platinum":
			return "💎"
		"diamond":
			return "💠"
		"master":
			return "👑"
		"challenger":
			return "🔥"
		_:
			return "🏅"
