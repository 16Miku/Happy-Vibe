extends Node
## 事件总线 - 全局单例
## 用于解耦的事件通信系统

# 编码活动相关信号
signal coding_started(source: String)
signal coding_ended(duration: float, energy_earned: int)
signal flow_state_entered()
signal flow_state_exited(duration: float)

# 农场相关信号
signal crop_planted(plot_id: String, crop_type: String)
signal crop_harvested(plot_id: String, crop_data: Dictionary)
signal crop_ready(plot_id: String)

# 建造相关信号
signal building_placed(building_type: String, position: Vector2)
signal building_upgraded(building_id: String, new_level: int)

# 成就相关信号
signal achievement_unlocked(achievement_id: String)
signal achievement_progress(achievement_id: String, progress: int, target: int)

# UI 相关信号
signal show_notification(message: String, type: String)
signal show_popup(title: String, content: String)

# 游戏状态信号
signal game_paused()
signal game_resumed()
signal day_changed(new_day: int)


func _ready() -> void:
	pass


## 发送通知的便捷方法
func notify(message: String, type: String = "info") -> void:
	show_notification.emit(message, type)


## 发送弹窗的便捷方法
func popup(title: String, content: String) -> void:
	show_popup.emit(title, content)
