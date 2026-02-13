## multiplayer_client.gd
## 多人联机客户端
## 处理 WebSocket 连接和实时通信
extends Node

# ==================== 信号定义 ====================

## 连接状态变化
signal connection_changed(connected: bool)

## 收到聊天消息
signal chat_message_received(from_id: String, from_name: String, content: String)

## 好友上线
signal friend_online(friend_id: String, friend_name: String)

## 好友下线
signal friend_offline(friend_id: String)

## 收到好友请求
signal friend_request_received(request_id: String, from_id: String, from_name: String, message: String)

## 好友请求被接受
signal friend_request_accepted(friend_id: String, friend_name: String)

## 收到礼物
signal gift_received(from_id: String, from_name: String, item_id: String, item_name: String)

## 收到帮忙通知
signal help_received(from_id: String, from_name: String, help_type: String)

## 农场被访问
signal farm_visited(visitor_id: String, visitor_name: String)

## 公会消息
signal guild_message_received(from_id: String, from_name: String, content: String)

## 公会成员加入
signal guild_member_joined(player_id: String, player_name: String)

## 公会升级
signal guild_level_up(new_level: int, new_features: Array)

## 被踢出公会
signal guild_kicked()

## 加入公会申请被接受
signal guild_join_accepted(guild_id: String, guild_name: String)

## 房间消息
signal room_message_received(room_id: String, from_id: String, content: String)

## 加入房间成功
signal room_joined(room_id: String, members: Array)

## 离开房间
signal room_left(room_id: String)

## 玩家加入房间
signal player_joined_room(room_id: String, player_id: String, player_info: Dictionary)

## 玩家离开房间
signal player_left_room(room_id: String, player_id: String)

# ==================== 常量 ====================

const DEFAULT_HOST := "127.0.0.1"
const DEFAULT_PORT := 8765
const RECONNECT_DELAY := 5.0
const PING_INTERVAL := 30.0

# ==================== 变量 ====================

var _socket: WebSocketPeer
var _is_connected: bool = false
var _player_id: String = ""
var _username: String = ""
var _level: int = 1
var _reconnect_timer: Timer
var _ping_timer: Timer
var _pending_messages: Array[Dictionary] = []

# ==================== 生命周期 ====================

func _ready() -> void:
	_setup_timers()


func _process(_delta: float) -> void:
	if _socket:
		_socket.poll()

		var state := _socket.get_ready_state()

		match state:
			WebSocketPeer.STATE_OPEN:
				if not _is_connected:
					_on_connected()
				_process_messages()
			WebSocketPeer.STATE_CLOSING:
				pass
			WebSocketPeer.STATE_CLOSED:
				if _is_connected:
					_on_disconnected()


func _setup_timers() -> void:
	# 重连定时器
	_reconnect_timer = Timer.new()
	_reconnect_timer.wait_time = RECONNECT_DELAY
	_reconnect_timer.one_shot = true
	_reconnect_timer.timeout.connect(_attempt_reconnect)
	add_child(_reconnect_timer)

	# 心跳定时器
	_ping_timer = Timer.new()
	_ping_timer.wait_time = PING_INTERVAL
	_ping_timer.timeout.connect(_send_ping)
	add_child(_ping_timer)


# ==================== 连接管理 ====================

func connect_to_server(player_id: String, username: String = "", level: int = 1) -> void:
	"""连接到多人服务器

	Args:
		player_id: 玩家 ID
		username: 用户名
		level: 玩家等级
	"""
	_player_id = player_id
	_username = username if username else "Player_%s" % player_id.substr(0, 8)
	_level = level

	_socket = WebSocketPeer.new()

	var url := "ws://%s:%d/ws/connect?player_id=%s&username=%s&level=%d" % [
		DEFAULT_HOST, DEFAULT_PORT, player_id, _username.uri_encode(), level
	]

	var err := _socket.connect_to_url(url)
	if err != OK:
		push_error("[MultiplayerClient] Failed to connect: %s" % err)
		_schedule_reconnect()


func disconnect_from_server() -> void:
	"""断开连接"""
	if _socket:
		_socket.close()
		_socket = null

	_is_connected = false
	_ping_timer.stop()
	_reconnect_timer.stop()


func is_connected() -> bool:
	"""检查是否已连接"""
	return _is_connected


func _on_connected() -> void:
	"""连接成功回调"""
	_is_connected = true
	_ping_timer.start()
	_reconnect_timer.stop()

	print("[MultiplayerClient] Connected to server")
	connection_changed.emit(true)
	EventBus.vibehub_connected.emit()

	# 发送待发送的消息
	for msg in _pending_messages:
		_send_message(msg)
	_pending_messages.clear()


func _on_disconnected() -> void:
	"""断开连接回调"""
	_is_connected = false
	_ping_timer.stop()

	print("[MultiplayerClient] Disconnected from server")
	connection_changed.emit(false)
	EventBus.vibehub_disconnected.emit()

	_schedule_reconnect()


func _schedule_reconnect() -> void:
	"""安排重连"""
	if not _reconnect_timer.is_stopped():
		return

	print("[MultiplayerClient] Reconnecting in %.1f seconds..." % RECONNECT_DELAY)
	_reconnect_timer.start()


func _attempt_reconnect() -> void:
	"""尝试重连"""
	if _player_id:
		connect_to_server(_player_id, _username, _level)


# ==================== 消息处理 ====================

func _process_messages() -> void:
	"""处理接收到的消息"""
	while _socket.get_available_packet_count() > 0:
		var packet := _socket.get_packet()
		var text := packet.get_string_from_utf8()

		var json := JSON.new()
		var err := json.parse(text)
		if err != OK:
			push_warning("[MultiplayerClient] Failed to parse message: %s" % text)
			continue

		var data: Dictionary = json.data
		_handle_message(data)


func _handle_message(data: Dictionary) -> void:
	"""处理单条消息"""
	var msg_type: String = data.get("type", "")

	match msg_type:
		# 连接确认
		"connected":
			print("[MultiplayerClient] Connection confirmed, online: %d" % data.get("online_count", 0))

		# 心跳响应
		"pong":
			pass

		# 状态变化
		"status_change":
			var player_id: String = data.get("player_id", "")
			var status: String = data.get("status", "")
			if status == "offline":
				friend_offline.emit(player_id)
			else:
				friend_online.emit(player_id, data.get("username", ""))

		# 聊天消息
		"chat_message":
			var from_id: String = data.get("from_player_id", "")
			var content: String = data.get("content", "")
			var from_name: String = data.get("from_username", "Player")
			chat_message_received.emit(from_id, from_name, content)

		# 好友请求
		"friend_request":
			var request_id: String = data.get("request_id", "")
			var from_id: String = data.get("from_player_id", "")
			var from_name: String = data.get("from_username", "")
			var message: String = data.get("message", "")
			friend_request_received.emit(request_id, from_id, from_name, message)
			EventBus.friend_request_received.emit(from_id, from_name)

		# 好友请求被接受
		"friend_request_accepted":
			var friend_id: String = data.get("friend_id", "")
			var friend_name: String = data.get("friend_username", "")
			friend_request_accepted.emit(friend_id, friend_name)

		# 收到礼物
		"gift_received":
			var from_id: String = data.get("from_player_id", "")
			var from_name: String = data.get("from_username", "")
			var item_id: String = data.get("item_id", "")
			var item_name: String = data.get("item_name", "")
			gift_received.emit(from_id, from_name, item_id, item_name)
			EventBus.gift_received.emit(from_id, item_id)

		# 收到帮忙
		"help_received":
			var from_id: String = data.get("from_player_id", "")
			var from_name: String = data.get("from_username", "")
			var help_type: String = data.get("help_type", "")
			help_received.emit(from_id, from_name, help_type)

		# 农场被访问
		"farm_visited":
			var visitor_id: String = data.get("visitor_id", "")
			var visitor_name: String = data.get("visitor_username", "")
			farm_visited.emit(visitor_id, visitor_name)

		# 公会消息
		"broadcast_message":
			var room_id: String = data.get("room_id", "")
			var from_id: String = data.get("from_player_id", "")
			var content: String = data.get("content", "")
			if room_id.begins_with("guild_"):
				guild_message_received.emit(from_id, "", content)
			else:
				room_message_received.emit(room_id, from_id, content)

		# 公会成员加入
		"guild_member_joined":
			var player_id: String = data.get("player_id", "")
			var player_name: String = data.get("player_username", "")
			guild_member_joined.emit(player_id, player_name)

		# 公会升级
		"guild_level_up":
			var new_level: int = data.get("new_level", 1)
			var new_features: Array = data.get("new_features", [])
			guild_level_up.emit(new_level, new_features)

		# 被踢出公会
		"guild_kicked":
			guild_kicked.emit()

		# 加入公会被接受
		"guild_join_accepted":
			var guild_id: String = data.get("guild_id", "")
			var guild_name: String = data.get("guild_name", "")
			guild_join_accepted.emit(guild_id, guild_name)

		# 加入房间成功
		"room_joined":
			var room_id: String = data.get("room_id", "")
			var members: Array = data.get("members", [])
			room_joined.emit(room_id, members)

		# 离开房间
		"room_left":
			var room_id: String = data.get("room_id", "")
			room_left.emit(room_id)

		# 玩家加入房间
		"room_join":
			var room_id: String = data.get("room_id", "")
			var player_id: String = data.get("player_id", "")
			var player_info: Dictionary = data.get("player_info", {})
			player_joined_room.emit(room_id, player_id, player_info)

		# 玩家离开房间
		"room_leave":
			var room_id: String = data.get("room_id", "")
			var player_id: String = data.get("player_id", "")
			player_left_room.emit(room_id, player_id)

		# 在线好友列表
		"online_friends":
			pass  # 由调用方处理

		# 错误
		"error":
			push_warning("[MultiplayerClient] Server error: %s" % data.get("message", ""))

		_:
			print("[MultiplayerClient] Unknown message type: %s" % msg_type)


func _send_message(data: Dictionary) -> bool:
	"""发送消息到服务器"""
	if not _is_connected:
		_pending_messages.append(data)
		return false

	var json_str := JSON.stringify(data)
	var err := _socket.send_text(json_str)
	return err == OK


func _send_ping() -> void:
	"""发送心跳"""
	_send_message({"action": "ping"})


# ==================== 公共 API ====================

## 更新状态
func update_status(status: String) -> void:
	"""更新在线状态

	Args:
		status: 状态 (online, coding, away)
	"""
	_send_message({
		"action": "status",
		"data": {"status": status}
	})


## 发送私聊消息
func send_chat_message(target_id: String, content: String) -> void:
	"""发送私聊消息

	Args:
		target_id: 目标玩家 ID
		content: 消息内容
	"""
	_send_message({
		"action": "chat",
		"data": {
			"target_id": target_id,
			"content": content
		}
	})


## 发送礼物通知
func send_gift_notification(target_id: String, item_id: String, item_name: String) -> void:
	"""发送礼物通知

	Args:
		target_id: 目标玩家 ID
		item_id: 物品 ID
		item_name: 物品名称
	"""
	_send_message({
		"action": "send_gift",
		"data": {
			"target_id": target_id,
			"item_id": item_id,
			"item_name": item_name
		}
	})


## 发送帮忙通知
func send_help_notification(target_id: String, help_type: String) -> void:
	"""发送帮忙通知

	Args:
		target_id: 目标玩家 ID
		help_type: 帮忙类型 (water, harvest, fertilize)
	"""
	_send_message({
		"action": "help_action",
		"data": {
			"target_id": target_id,
			"help_type": help_type
		}
	})


## 加入房间
func join_room(room_id: String) -> void:
	"""加入房间/频道

	Args:
		room_id: 房间 ID
	"""
	_send_message({
		"action": "join_room",
		"data": {"room_id": room_id}
	})


## 离开房间
func leave_room(room_id: String) -> void:
	"""离开房间/频道

	Args:
		room_id: 房间 ID
	"""
	_send_message({
		"action": "leave_room",
		"data": {"room_id": room_id}
	})


## 发送房间消息
func send_room_message(room_id: String, content: String) -> void:
	"""发送房间消息

	Args:
		room_id: 房间 ID
		content: 消息内容
	"""
	_send_message({
		"action": "broadcast",
		"data": {
			"room_id": room_id,
			"content": content
		}
	})


## 加入公会频道
func join_guild_channel(guild_id: String) -> void:
	"""加入公会聊天频道

	Args:
		guild_id: 公会 ID
	"""
	join_room("guild_%s" % guild_id)


## 离开公会频道
func leave_guild_channel(guild_id: String) -> void:
	"""离开公会聊天频道

	Args:
		guild_id: 公会 ID
	"""
	leave_room("guild_%s" % guild_id)


## 发送公会消息
func send_guild_message(guild_id: String, content: String) -> void:
	"""发送公会消息

	Args:
		guild_id: 公会 ID
		content: 消息内容
	"""
	send_room_message("guild_%s" % guild_id, content)


## 请求在线好友列表
func request_online_friends(friend_ids: Array) -> void:
	"""请求在线好友列表

	Args:
		friend_ids: 好友 ID 列表
	"""
	_send_message({
		"action": "get_online_friends",
		"data": {"friend_ids": friend_ids}
	})
