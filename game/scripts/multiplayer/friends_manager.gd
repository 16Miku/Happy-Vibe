## friends_manager.gd
## 好友系统管理器
## 处理好友相关的 HTTP API 调用
extends Node

# ==================== 信号定义 ====================

## 好友列表更新
signal friends_list_updated(friends: Array)

## 好友请求列表更新
signal friend_requests_updated(received: Array, sent: Array)

## 好友添加成功
signal friend_added(friend_id: String)

## 好友删除成功
signal friend_removed(friend_id: String)

## 礼物发送成功
signal gift_sent(friend_id: String, affinity_gained: int)

## 帮忙成功
signal help_completed(friend_id: String, help_type: String, affinity_gained: int)

## 访问好友农场
signal farm_visit_started(friend_id: String)

## 操作失败
signal operation_failed(error: String)

# ==================== 常量 ====================

const API_BASE := "http://127.0.0.1:8765/api/friends"

# ==================== 变量 ====================

var _http_request: HTTPRequest
var _current_request_type: String = ""
var _player_id: String = ""

# 好友列表缓存
var _friends_cache: Array = []
var _online_friends_cache: Array = []

# ==================== 生命周期 ====================

func _ready() -> void:
	_http_request = HTTPRequest.new()
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


func set_player_id(player_id: String) -> void:
	"""设置当前玩家 ID"""
	_player_id = player_id


# ==================== 好友列表 ====================

func get_friends_list(include_offline: bool = true) -> void:
	"""获取好友列表

	Args:
		include_offline: 是否包含离线好友
	"""
	if _player_id.is_empty():
		push_warning("[FriendsManager] Player ID not set")
		return

	_current_request_type = "friends_list"
	var url := "%s/list/%s?include_offline=%s" % [API_BASE, _player_id, str(include_offline).to_lower()]
	_http_request.request(url)


func get_online_friends() -> void:
	"""获取在线好友列表"""
	if _player_id.is_empty():
		return

	_current_request_type = "online_friends"
	var url := "%s/online/%s" % [API_BASE, _player_id]
	_http_request.request(url)


# ==================== 好友请求 ====================

func send_friend_request(to_player_id: String, message: String = "") -> void:
	"""发送好友请求

	Args:
		to_player_id: 目标玩家 ID
		message: 附加消息
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "send_request"
	var url := "%s/request" % API_BASE
	var body := JSON.stringify({
		"from_player_id": _player_id,
		"to_player_id": to_player_id,
		"message": message
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func get_friend_requests(status: String = "") -> void:
	"""获取好友请求列表

	Args:
		status: 筛选状态 (pending, accepted, rejected)
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "get_requests"
	var url := "%s/requests/%s" % [API_BASE, _player_id]
	if not status.is_empty():
		url += "?status=%s" % status
	_http_request.request(url)


func respond_to_request(request_id: String, accept: bool) -> void:
	"""响应好友请求

	Args:
		request_id: 请求 ID
		accept: 是否接受
	"""
	_current_request_type = "respond_request"
	var url := "%s/request/respond" % API_BASE
	var body := JSON.stringify({
		"request_id": request_id,
		"accept": accept
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


# ==================== 好友操作 ====================

func remove_friend(friend_id: String) -> void:
	"""删除好友

	Args:
		friend_id: 好友 ID
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "remove_friend"
	var url := "%s/%s/%s" % [API_BASE, _player_id, friend_id]
	_http_request.request(url, [], HTTPClient.METHOD_DELETE)


func send_gift(friend_id: String, item_id: String, item_name: String, quantity: int = 1) -> void:
	"""发送礼物

	Args:
		friend_id: 好友 ID
		item_id: 物品 ID
		item_name: 物品名称
		quantity: 数量
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "send_gift"
	var url := "%s/gift" % API_BASE
	var body := JSON.stringify({
		"from_player_id": _player_id,
		"to_player_id": friend_id,
		"item_id": item_id,
		"item_name": item_name,
		"quantity": quantity
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func help_friend(friend_id: String, action_type: String) -> void:
	"""帮助好友

	Args:
		friend_id: 好友 ID
		action_type: 操作类型 (water, harvest, fertilize)
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "help_friend"
	var url := "%s/help" % API_BASE
	var body := JSON.stringify({
		"from_player_id": _player_id,
		"to_player_id": friend_id,
		"action_type": action_type
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func visit_friend_farm(friend_id: String) -> void:
	"""访问好友农场

	Args:
		friend_id: 好友 ID
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "visit_farm"
	var url := "%s/visit/%s/%s" % [API_BASE, _player_id, friend_id]
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, "")


# ==================== 响应处理 ====================

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	"""HTTP 请求完成回调"""
	if result != HTTPRequest.RESULT_SUCCESS:
		operation_failed.emit("Network error")
		return

	var json := JSON.new()
	var parse_result := json.parse(body.get_string_from_utf8())
	if parse_result != OK:
		operation_failed.emit("Invalid response")
		return

	var data: Dictionary = json.data

	if response_code != 200:
		var error_msg: String = data.get("detail", "Unknown error")
		operation_failed.emit(error_msg)
		return

	match _current_request_type:
		"friends_list":
			_friends_cache = data.get("friends", [])
			friends_list_updated.emit(_friends_cache)

		"online_friends":
			_online_friends_cache = data.get("online_friends", [])
			friends_list_updated.emit(_online_friends_cache)

		"get_requests":
			var received: Array = data.get("received", [])
			var sent: Array = data.get("sent", [])
			friend_requests_updated.emit(received, sent)

		"send_request":
			EventBus.notify_success("好友请求已发送")

		"respond_request":
			if data.get("success", false):
				var friend_id: String = data.get("friend_id", "")
				if not friend_id.is_empty():
					friend_added.emit(friend_id)
					EventBus.notify_success("已添加好友")
				get_friends_list()

		"remove_friend":
			if data.get("success", false):
				EventBus.notify_success("已删除好友")
				get_friends_list()

		"send_gift":
			if data.get("success", false):
				var affinity: int = data.get("affinity_gained", 0)
				gift_sent.emit("", affinity)
				EventBus.notify_success("礼物已送出，好友度 +%d" % affinity)

		"help_friend":
			if data.get("success", false):
				var affinity: int = data.get("affinity_gained", 0)
				help_completed.emit("", "", affinity)
				EventBus.notify_success("帮忙成功，好友度 +%d" % affinity)

		"visit_farm":
			if data.get("success", false):
				var affinity: int = data.get("affinity_gained", 0)
				farm_visit_started.emit("")
				EventBus.notify_success("访问好友农场，好友度 +%d" % affinity)


# ==================== 工具方法 ====================

func get_cached_friends() -> Array:
	"""获取缓存的好友列表"""
	return _friends_cache


func get_cached_online_friends() -> Array:
	"""获取缓存的在线好友列表"""
	return _online_friends_cache


func is_friend(player_id: String) -> bool:
	"""检查是否是好友"""
	for friend in _friends_cache:
		if friend.get("player_id", "") == player_id:
			return true
	return false


func get_friend_info(player_id: String) -> Dictionary:
	"""获取好友信息"""
	for friend in _friends_cache:
		if friend.get("player_id", "") == player_id:
			return friend
	return {}
