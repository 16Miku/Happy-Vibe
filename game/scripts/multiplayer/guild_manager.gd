## guild_manager.gd
## 公会系统管理器
## 处理公会相关的 HTTP API 调用
extends Node

# ==================== 信号定义 ====================

## 公会列表更新
signal guilds_list_updated(guilds: Array)

## 公会详情更新
signal guild_details_updated(guild: Dictionary, members: Array)

## 玩家公会信息更新
signal player_guild_updated(has_guild: bool, guild_info: Dictionary, membership: Dictionary)

## 公会创建成功
signal guild_created(guild_id: String)

## 加入申请发送成功
signal join_request_sent(request_id: String)

## 加入申请列表更新
signal join_requests_updated(requests: Array)

## 贡献成功
signal contribution_completed(energy: int, exp_gained: int, level_up: bool)

## 操作失败
signal operation_failed(error: String)

# ==================== 常量 ====================

const API_BASE := "http://127.0.0.1:8765/api/guilds"

# ==================== 变量 ====================

var _http_request: HTTPRequest
var _current_request_type: String = ""
var _player_id: String = ""

# 缓存
var _current_guild: Dictionary = {}
var _current_guild_members: Array = []
var _player_guild_id: String = ""

# ==================== 生命周期 ====================

func _ready() -> void:
	_http_request = HTTPRequest.new()
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


func set_player_id(player_id: String) -> void:
	"""设置当前玩家 ID"""
	_player_id = player_id


# ==================== 公会列表 ====================

func get_guilds_list(page: int = 1, page_size: int = 20, search: String = "") -> void:
	"""获取公会列表

	Args:
		page: 页码
		page_size: 每页数量
		search: 搜索关键词
	"""
	_current_request_type = "guilds_list"
	var url := "%s/list?page=%d&page_size=%d" % [API_BASE, page, page_size]
	if not search.is_empty():
		url += "&search=%s" % search.uri_encode()
	_http_request.request(url)


func get_guild_details(guild_id: String) -> void:
	"""获取公会详情

	Args:
		guild_id: 公会 ID
	"""
	_current_request_type = "guild_details"
	var url := "%s/%s" % [API_BASE, guild_id]
	_http_request.request(url)


func get_player_guild() -> void:
	"""获取玩家所属公会"""
	if _player_id.is_empty():
		return

	_current_request_type = "player_guild"
	var url := "%s/player/%s" % [API_BASE, _player_id]
	_http_request.request(url)


# ==================== 公会操作 ====================

func create_guild(name: String, description: String = "", icon: String = "") -> void:
	"""创建公会

	Args:
		name: 公会名称
		description: 公会描述
		icon: 公会图标
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "create_guild"
	var url := "%s/create" % API_BASE
	var body := JSON.stringify({
		"name": name,
		"description": description,
		"icon": icon,
		"founder_id": _player_id
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func update_guild(guild_id: String, name: String = "", description: String = "", icon: String = "") -> void:
	"""更新公会信息

	Args:
		guild_id: 公会 ID
		name: 新名称
		description: 新描述
		icon: 新图标
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "update_guild"
	var url := "%s/%s?operator_id=%s" % [API_BASE, guild_id, _player_id]
	var data := {}
	if not name.is_empty():
		data["name"] = name
	if not description.is_empty():
		data["description"] = description
	if not icon.is_empty():
		data["icon"] = icon

	var body := JSON.stringify(data)
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_PUT, body)


func request_join_guild(guild_id: String, message: String = "") -> void:
	"""申请加入公会

	Args:
		guild_id: 公会 ID
		message: 申请消息
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "join_guild"
	var url := "%s/join" % API_BASE
	var body := JSON.stringify({
		"player_id": _player_id,
		"guild_id": guild_id,
		"message": message
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func respond_join_request(request_id: String, accept: bool) -> void:
	"""处理加入申请

	Args:
		request_id: 申请 ID
		accept: 是否接受
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "respond_join"
	var url := "%s/join/%s/respond?accept=%s&operator_id=%s" % [
		API_BASE, request_id, str(accept).to_lower(), _player_id
	]
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, "")


func leave_guild(guild_id: String) -> void:
	"""退出公会

	Args:
		guild_id: 公会 ID
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "leave_guild"
	var url := "%s/%s/members/%s?operator_id=%s" % [API_BASE, guild_id, _player_id, _player_id]
	_http_request.request(url, [], HTTPClient.METHOD_DELETE)


func kick_member(guild_id: String, target_id: String) -> void:
	"""踢出成员

	Args:
		guild_id: 公会 ID
		target_id: 目标成员 ID
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "kick_member"
	var url := "%s/%s/members/%s?operator_id=%s" % [API_BASE, guild_id, target_id, _player_id]
	_http_request.request(url, [], HTTPClient.METHOD_DELETE)


func update_member_role(guild_id: String, target_id: String, new_role: String) -> void:
	"""更新成员角色

	Args:
		guild_id: 公会 ID
		target_id: 目标成员 ID
		new_role: 新角色 (leader, officer, member)
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "update_role"
	var url := "%s/%s/role" % [API_BASE, guild_id]
	var body := JSON.stringify({
		"operator_id": _player_id,
		"target_id": target_id,
		"new_role": new_role
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func contribute_energy(guild_id: String, energy_amount: int) -> void:
	"""向公会贡献能量

	Args:
		guild_id: 公会 ID
		energy_amount: 能量数量
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "contribute"
	var url := "%s/%s/contribute" % [API_BASE, guild_id]
	var body := JSON.stringify({
		"player_id": _player_id,
		"guild_id": guild_id,
		"energy_amount": energy_amount
	})
	var headers := ["Content-Type: application/json"]
	_http_request.request(url, headers, HTTPClient.METHOD_POST, body)


func get_join_requests(guild_id: String) -> void:
	"""获取加入申请列表

	Args:
		guild_id: 公会 ID
	"""
	if _player_id.is_empty():
		return

	_current_request_type = "join_requests"
	var url := "%s/%s/requests?operator_id=%s" % [API_BASE, guild_id, _player_id]
	_http_request.request(url)


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
		"guilds_list":
			var guilds: Array = data.get("guilds", [])
			guilds_list_updated.emit(guilds)

		"guild_details":
			_current_guild = data.get("guild", {})
			_current_guild_members = data.get("members", [])
			guild_details_updated.emit(_current_guild, _current_guild_members)

		"player_guild":
			var has_guild: bool = data.get("has_guild", false)
			var guild_info: Dictionary = data.get("guild", {})
			var membership: Dictionary = data.get("membership", {})
			if has_guild:
				_player_guild_id = guild_info.get("guild_id", "")
			else:
				_player_guild_id = ""
			player_guild_updated.emit(has_guild, guild_info, membership)

		"create_guild":
			if data.get("success", false):
				var guild_id: String = data.get("guild_id", "")
				_player_guild_id = guild_id
				guild_created.emit(guild_id)
				EventBus.notify_success("公会创建成功！")

		"join_guild":
			if data.get("success", false):
				var request_id: String = data.get("request_id", "")
				join_request_sent.emit(request_id)
				EventBus.notify_success("加入申请已发送")

		"respond_join":
			if data.get("success", false):
				EventBus.notify_success(data.get("message", "操作成功"))
				# 刷新公会详情
				if not _player_guild_id.is_empty():
					get_guild_details(_player_guild_id)

		"leave_guild":
			if data.get("success", false):
				_player_guild_id = ""
				EventBus.notify_success("已退出公会")
				get_player_guild()

		"kick_member":
			if data.get("success", false):
				EventBus.notify_success("成员已移除")
				if not _player_guild_id.is_empty():
					get_guild_details(_player_guild_id)

		"update_role":
			if data.get("success", false):
				EventBus.notify_success(data.get("message", "角色已更新"))
				if not _player_guild_id.is_empty():
					get_guild_details(_player_guild_id)

		"contribute":
			if data.get("success", false):
				var energy: int = data.get("energy_contributed", 0)
				var exp_gained: int = data.get("exp_gained", 0)
				var level_up: bool = data.get("level_up", false)
				contribution_completed.emit(energy, exp_gained, level_up)
				if level_up:
					EventBus.notify_success("公会升级了！")
				else:
					EventBus.notify_success("贡献成功，公会经验 +%d" % exp_gained)

		"join_requests":
			var requests: Array = data.get("requests", [])
			join_requests_updated.emit(requests)

		"update_guild":
			if data.get("success", false):
				EventBus.notify_success("公会信息已更新")
				if not _player_guild_id.is_empty():
					get_guild_details(_player_guild_id)


# ==================== 工具方法 ====================

func get_current_guild() -> Dictionary:
	"""获取当前公会信息"""
	return _current_guild


func get_current_guild_members() -> Array:
	"""获取当前公会成员列表"""
	return _current_guild_members


func get_player_guild_id() -> String:
	"""获取玩家所属公会 ID"""
	return _player_guild_id


func has_guild() -> bool:
	"""检查玩家是否有公会"""
	return not _player_guild_id.is_empty()


func is_guild_leader() -> bool:
	"""检查玩家是否是公会会长"""
	for member in _current_guild_members:
		if member.get("player_id", "") == _player_id:
			return member.get("role", "") == "leader"
	return false


func is_guild_officer() -> bool:
	"""检查玩家是否是公会管理员"""
	for member in _current_guild_members:
		if member.get("player_id", "") == _player_id:
			var role: String = member.get("role", "")
			return role == "leader" or role == "officer"
	return false
