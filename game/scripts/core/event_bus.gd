## event_bus.gd
## 全局事件总线 - 用于解耦各系统之间的通信
## 作为 AutoLoad 单例运行
extends Node

# ==================== 玩家相关信号 ====================

## 能量更新
signal energy_updated(current: int, max_energy: int)

## 金币更新
signal gold_updated(amount: int)

## 钻石更新
signal diamonds_updated(amount: int)

## 玩家升级
signal player_leveled_up(new_level: int)

## 玩家数据加载完成
signal player_data_ready()

# ==================== Vibe-Coding 相关信号 ====================

## 从 VibeHub 接收到能量
signal vibe_energy_received(energy: int, exp: int, is_flow: bool)

## 进入心流状态
signal flow_state_achieved()

## 退出心流状态
signal flow_state_ended(duration_minutes: int)

## 编码会话开始
signal coding_session_started()

## 编码会话结束
signal coding_session_ended(duration_minutes: int, energy_earned: int)

# ==================== 农场相关信号 ====================

## 作物种植
signal crop_planted(plot_id: String, crop_type: String)

## 作物成熟
signal crop_ready(plot_id: String)

## 作物收获
signal crop_harvested(plot_id: String, crop_data: Dictionary)

## 地块浇水
signal plot_watered(plot_id: int)

## 地块施肥
signal plot_fertilized(plot_id: int)

# ==================== 建筑相关信号 ====================

## 建筑放置
signal building_placed(building_type: String, position: Vector2)

## 建筑开始建造
signal building_started(building_id: int, building_type: String)

## 建筑完成
signal building_completed(building_id: int, building_type: String)

## 建筑升级
signal building_upgraded(building_id: String, new_level: int)

# ==================== 库存相关信号 ====================

## 物品添加
signal item_added(item_id: String, quantity: int)

## 物品移除
signal item_removed(item_id: String, quantity: int)

## 物品使用
signal item_used(item_id: String)

## 库存已满
signal inventory_full()

# ==================== 头像相关信号 ====================

## 头像更换
signal avatar_changed(avatar_id: String)

## 头像解锁
signal avatar_unlocked(avatar_id: String)

# ==================== 成就相关信号 ====================

## 成就解锁
signal achievement_unlocked(achievement_id: String)

## 成就进度更新
signal achievement_progress(achievement_id: String, current: int, target: int)

## 称号获得
signal title_earned(title_id: String)

# ==================== 任务相关信号 ====================

## 任务接取
signal quest_accepted(quest_id: String)

## 任务进度更新
signal quest_progress_updated(quest_id: String, current: int, target: int)

## 任务完成
signal quest_completed(quest_id: String)

## 任务奖励领取
signal quest_reward_claimed(quest_id: String, rewards: Dictionary)

## 日常任务刷新
signal daily_quests_refreshed()

## 周常任务刷新
signal weekly_quests_refreshed()

## 进入心流状态（用于任务系统）
signal flow_state_entered()

# ==================== UI 相关信号 ====================

## 显示通知
signal show_notification(message: String, type: String)

## 显示弹窗
signal show_popup(title: String, content: String)

## 显示奖励弹窗
signal show_reward_popup(rewards: Dictionary)

## 显示确认对话框
signal show_confirm_dialog(title: String, message: String, callback: Callable)

## 打开界面
signal open_panel(panel_name: String)

## 关闭界面
signal close_panel(panel_name: String)

# ==================== 游戏状态相关信号 ====================

## 游戏暂停
signal game_paused()

## 游戏恢复
signal game_resumed()

## 游戏保存
signal game_saved()

## 游戏加载
signal game_loaded()

## 新的一天开始（游戏内时间）
signal new_day_started(day: int)

## 日期变化
signal day_changed(new_day: int)

# ==================== 社交相关信号（预留） ====================

## 好友上线
signal friend_online(friend_id: String)

## 好友离线
signal friend_offline(friend_id: String)

## 收到好友请求
signal friend_request_received(from_id: String, from_name: String)

## 好友请求被接受
signal friend_request_accepted(friend_id: String, friend_name: String)

## 收到礼物
signal gift_received(from_id: String, item_id: String)

## 收到帮忙通知
signal help_received(from_id: String, help_type: String)

## 农场被访问
signal farm_visited(visitor_id: String, visitor_name: String)

## 好友列表更新
signal friends_list_updated(friends: Array)

# ==================== 公会相关信号 ====================

## 加入公会
signal guild_joined(guild_id: String, guild_name: String)

## 离开公会
signal guild_left()

## 被踢出公会
signal guild_kicked()

## 公会升级
signal guild_level_up(new_level: int)

## 公会消息
signal guild_message_received(from_id: String, content: String)

## 公会成员加入
signal guild_member_joined(player_id: String, player_name: String)

## 公会成员离开
signal guild_member_left(player_id: String)

# ==================== 排行榜相关信号 ====================

## 排行榜更新
signal leaderboard_updated(lb_type: String, entries: Array)

## 玩家排名变化
signal player_rank_changed(lb_type: String, old_rank: int, new_rank: int)

# ==================== 网络相关信号 ====================

## 连接到 VibeHub
signal vibehub_connected()

## 与 VibeHub 断开连接
signal vibehub_disconnected()

## VibeHub 数据同步完成
signal vibehub_synced()

## 网络错误
signal network_error(error_message: String)


func _ready() -> void:
	pass


# ==================== 工具方法 ====================

## 发送通知的便捷方法
func notify(message: String, type: String = "info") -> void:
	show_notification.emit(message, type)


## 发送成功通知
func notify_success(message: String) -> void:
	notify(message, "success")


## 发送警告通知
func notify_warning(message: String) -> void:
	notify(message, "warning")


## 发送错误通知
func notify_error(message: String) -> void:
	notify(message, "error")


## 发送弹窗的便捷方法
func popup(title: String, content: String) -> void:
	show_popup.emit(title, content)


## 显示奖励
func show_rewards(rewards: Dictionary) -> void:
	show_reward_popup.emit(rewards)


## 请求确认
func request_confirm(title: String, message: String, callback: Callable) -> void:
	show_confirm_dialog.emit(title, message, callback)
