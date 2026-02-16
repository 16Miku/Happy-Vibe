## api_manager.gd
## HTTP API 管理器 - 处理所有与 VibeHub 后端的 API 通信
## 作为 AutoLoad 单例运行
extends Node

# ==================== 配置 ====================

## API 基础地址
const BASE_URL := "http://127.0.0.1:8765"

## API 版本
const API_VERSION := "api"

## 认证 Token
var auth_token: String = ""

## 默认玩家 ID
var player_id: String = "default"

## 请求超时时间（秒）
const REQUEST_TIMEOUT: float = 30.0

# ==================== 信号定义 ====================

## 请求完成信号
signal request_completed(endpoint: String, data: Dictionary, success: bool)

## 请求失败信号
signal request_failed(endpoint: String, error: String)

## 认证状态变化
signal auth_status_changed(is_authenticated: bool)

# ==================== 私有变量 ====================

var _http_request: HTTPRequest
var _pending_requests: Dictionary = {}  # 请求 ID 到回调的映射
var _request_id_counter: int = 0

# ==================== 生命周期 ====================

func _ready() -> void:
	_create_http_request()
	print("[ApiManager] API 管理器已初始化")


func _create_http_request() -> void:
	"""创建 HTTP 请求节点"""
	if _http_request:
		_http_request.queue_free()

	_http_request = HTTPRequest.new()
	_http_request.timeout = REQUEST_TIMEOUT
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


# ==================== HTTP 请求处理 ====================

## 发送 GET 请求
func get(endpoint: String, params: Dictionary = {}, callback: Callable = Callable()) -> int:
	var url := _build_url(endpoint, params)
	return _send_request(url, HTTPClient.METHOD_GET, "", callback)


## 发送 POST 请求
func post(endpoint: String, data: Dictionary = {}, callback: Callable = Callable()) -> int:
	var url := _build_url(endpoint)
	var body := JSON.stringify(data)
	var headers := _get_headers()
	return _send_request(url, HTTPClient.METHOD_POST, body, callback, headers)


## 发送 PUT 请求
func put(endpoint: String, data: Dictionary = {}, callback: Callable = Callable()) -> int:
	var url := _build_url(endpoint)
	var body := JSON.stringify(data)
	var headers := _get_headers()
	return _send_request(url, HTTPClient.METHOD_PUT, body, callback, headers)


## 发送 DELETE 请求
func delete(endpoint: String, callback: Callable = Callable()) -> int:
	var url := _build_url(endpoint)
	var headers := _get_headers()
	return _send_request(url, HTTPClient.METHOD_DELETE, "", callback, headers)


## 内部发送请求
func _send_request(url: String, method: HTTPClient.Method, body: String, callback: Callable, headers: PackedStringArray = []) -> int:
	if not _http_request:
		_create_http_request()

	var request_id := _request_id_counter
	_request_id_counter += 1

	_pending_requests[request_id] = {
		"callback": callback,
		"endpoint": url,
		"method": method
	}

	var error := _http_request.request(url, headers, method, body)
	if error != OK:
		push_error("[ApiManager] 请求失败: %s" % url)
		_pending_requests.erase(request_id)
		request_failed.emit(url, "HTTP 请求创建失败")
		return -1

	return request_id


## 请求完成回调
func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		_handle_error("网络请求失败")
		return

	var response_text := body.get_string_from_utf8()
	var json := JSON.new()
	var parse_result := json.parse(response_text)

	if parse_result != OK:
		_handle_error("JSON 解析失败: %s" % response_text)
		return

	var data: Dictionary = json.data
	var success := response_code >= 200 and response_code < 300

	# 调用回调
	for request_id in _pending_requests.keys():
		var request_info: Dictionary = _pending_requests[request_id]
		if request_info["callback"].is_valid():
			request_info["callback"].call(success, data)

		# 发射全局信号
		if success:
			request_completed.emit(request_info["endpoint"], data, true)
		else:
			request_failed.emit(request_info["endpoint"], data.get("detail", "未知错误"))

		_pending_requests.erase(request_id)
		break


## 处理错误
func _handle_error(error_message: String) -> void:
	push_error("[ApiManager] %s" % error_message)
	for request_id in _pending_requests.keys():
		var request_info: Dictionary = _pending_requests[request_id]
		request_failed.emit(request_info["endpoint"], error_message)
		_pending_requests.erase(request_id)


## 构建完整 URL
func _build_url(endpoint: String, params: Dictionary = {}) -> String:
	var url := "%s/%s/%s" % [BASE_URL, API_VERSION, endpoint.trim_prefix("/")]

	# 添加查询参数
	if params.size() > 0:
		var query_parts: PackedStringArray = []
		for key in params:
			var value := str(params[key])
			query_parts.append("%s=%s" % [key, value.uri_encode()])
		url += "?" + "&".join(query_parts)

	return url


## 获取请求头
func _get_headers() -> PackedStringArray:
	var headers := PackedStringArray([
		"Content-Type: application/json"
	])

	if not auth_token.is_empty():
		headers.append("Authorization: Bearer %s" % auth_token)

	return headers


# ==================== 认证管理 ====================

## 设置认证 Token
func set_auth_token(token: String) -> void:
	auth_token = token
	auth_status_changed.emit(not token.is_empty())
	print("[ApiManager] 认证 Token 已%s" % ("设置" if not token.is_empty() else "清除"))


## 清除认证
func clear_auth() -> void:
	auth_token = ""
	auth_status_changed.emit(false)


# ==================== API 端点方法 ====================

# ---------- 健康检查 ----------

## 健康检查
func health_check(callback: Callable = Callable()) -> int:
	return get("/health", {}, callback)


# ---------- 玩家 API ----------

## 获取玩家数据
func get_player(callback: Callable = Callable()) -> int:
	return get("/player", {}, callback)


## 创建或更新玩家
func update_player(player_data: Dictionary, callback: Callable = Callable()) -> int:
	return post("/player", player_data, callback)


## 获取能量数据
func get_energy(callback: Callable = Callable()) -> int:
	return get("/energy", {}, callback)


## 收集能量
func collect_energy(callback: Callable = Callable()) -> int:
	return post("/energy/collect", {}, callback)


## 添加能量
func add_energy(amount: int, callback: Callable = Callable()) -> int:
	return post("/player/energy", {"amount": amount}, callback)


## 添加经验
func add_exp(amount: int, callback: Callable = Callable()) -> int:
	return post("/player/exp", {"amount": amount}, callback)


## 每日签到
func daily_checkin(callback: Callable = Callable()) -> int:
	return post("/checkin", {}, callback)


## 获取签到状态
func get_checkin_status(callback: Callable = Callable()) -> int:
	return get("/checkin", {}, callback)


# ---------- 成就 API ----------

## 获取所有成就定义
func get_achievements(callback: Callable = Callable()) -> int:
	return get("/achievements", {}, callback)


## 获取玩家成就进度
func get_achievement_progress(callback: Callable = Callable()) -> int:
	return get("/achievements/progress", {}, callback)


## 领取成就奖励
func claim_achievement_reward(achievement_id: String, callback: Callable = Callable()) -> int:
	return post("/achievements/%s/claim" % achievement_id, {}, callback)


# ---------- 公会 API ----------

## 获取公会列表
func get_guilds(page: int = 1, page_size: int = 20, callback: Callable = Callable()) -> int:
	return get("/guilds", {"page": page, "page_size": page_size}, callback)


## 创建公会
func create_guild(guild_data: Dictionary, callback: Callable = Callable()) -> int:
	return post("/guilds", guild_data, callback)


## 获取公会详情
func get_guild(guild_id: String, callback: Callable = Callable()) -> int:
	return get("/guilds/%s" % guild_id, {}, callback)


## 加入公会
func join_guild(guild_id: String, callback: Callable = Callable()) -> int:
	return post("/guilds/%s/join" % guild_id, {}, callback)


## 离开公会
func leave_guild(callback: Callable = Callable()) -> int:
	return post("/guilds/leave", {}, callback)


## 获取公会成员列表
func get_guild_members(guild_id: String, callback: Callable = Callable()) -> int:
	return get("/guilds/%s/members" % guild_id, {}, callback)


## 踢出公会成员
func kick_guild_member(guild_id: String, player_id: String, callback: Callable = Callable()) -> int:
	return post("/guilds/%s/members/%s/kick" % [guild_id, player_id], {}, callback)


## 获取我的公会信息
func get_my_guild(callback: Callable = Callable()) -> int:
	return get("/guilds/my", {}, callback)


# ---------- 排行榜 API ----------

## 获取排行榜列表
func get_leaderboards(callback: Callable = Callable()) -> int:
	return get("/leaderboards", {}, callback)


## 获取指定排行榜
func get_leaderboard(lb_type: String, page: int = 1, page_size: int = 50, callback: Callable = Callable()) -> int:
	return get("/leaderboards/%s" % lb_type, {"page": page, "page_size": page_size}, callback)


## 获取玩家排名
func get_player_rank(lb_type: String, callback: Callable = Callable()) -> int:
	return get("/leaderboards/%s/my-rank" % lb_type, {}, callback)


# ---------- 赛季 API ----------

## 获取当前赛季信息
func get_current_season(callback: Callable = Callable()) -> int:
	return get("/seasons/current", {}, callback)


## 获取赛季排行
func get_season_leaderboard(season_id: String, callback: Callable = Callable()) -> int:
	return get("/seasons/%s/leaderboard" % season_id, {}, callback)


# ---------- PVP 竞技场 API ----------

## 获取 PVP 玩家信息
func get_pvp_info(callback: Callable = Callable()) -> int:
	return get("/pvp/me", {}, callback)


## 获取 PVP 排行榜
func get_pvp_leaderboard(page: int = 1, page_size: int = 50, callback: Callable = Callable()) -> int:
	return get("/pvp/leaderboard", {"page": page, "page_size": page_size}, callback)


## 发起 PVP 匹配
func start_pvp_matchmaking(callback: Callable = Callable()) -> int:
	return post("/pvp/matchmaking", {}, callback)


## 获取 PVP 匹配状态
func get_match_status(match_id: String, callback: Callable = Callable()) -> int:
	return get("/pvp/matches/%s" % match_id, {}, callback)


## 提交 PVP 战斗结果
func submit_pvp_result(match_id: String, result_data: Dictionary, callback: Callable = Callable()) -> int:
	return post("/pvp/matches/%s/result" % match_id, result_data, callback)


## 获取 PVP 战斗历史
func get_pvp_history(page: int = 1, page_size: int = 20, callback: Callable = Callable()) -> int:
	return get("/pvp/history", {"page": page, "page_size": page_size}, callback)


# ---------- 商城 API ----------

## 获取商城商品
func get_shop_items(shop_type: String = "general", callback: Callable = Callable()) -> int:
	return get("/shops/%s/items" % shop_type, {}, callback)


## 购买商品
func buy_item(shop_type: String, item_id: String, callback: Callable = Callable()) -> int:
	return post("/shops/%s/buy" % shop_type, {"item_id": item_id}, callback)


# ---------- 拍卖行 API ----------

## 获取拍卖行列表
func get_auction_items(page: int = 1, callback: Callable = Callable()) -> int:
	return get("/auctions", {"page": page}, callback)


## 发布拍卖
func create_auction(item_data: Dictionary, callback: Callable = Callable()) -> int:
	return post("/auctions", item_data, callback)


## 竞拍
func bid_auction(auction_id: String, bid_amount: int, callback: Callable = Callable()) -> int:
	return post("/auctions/%s/bid" % auction_id, {"amount": bid_amount}, callback)


## 获取我的拍卖
func get_my_auctions(callback: Callable = Callable()) -> int:
	return get("/auctions/my", {}, callback)


# ---------- 活动 API ----------

## 开始活动追踪
func start_activity(source: String, callback: Callable = Callable()) -> int:
	return post("/activity/start", {"source": source}, callback)


## 更新活动
func update_activity(session_id: String, data: Dictionary, callback: Callable = Callable()) -> int:
	return post("/activity/update", {"session_id": session_id}.merge(data), callback)


## 结束活动
func end_activity(session_id: String, callback: Callable = Callable()) -> int:
	return post("/activity/end", {"session_id": session_id}, callback)


## 获取当前活动状态
func get_current_activity(callback: Callable = Callable()) -> int:
	return get("/activity/current", {}, callback)


## 获取心流状态
func get_flow_status(callback: Callable = Callable()) -> int:
	return get("/activity/flow-status", {}, callback)


# ---------- 农场 API ----------

## 获取农场数据
func get_farm(callback: Callable = Callable()) -> int:
	return get("/farm", {}, callback)


## 更新农场数据
func update_farm(farm_data: Dictionary, callback: Callable = Callable()) -> int:
	return post("/farm", farm_data, callback)


# ---------- 任务 API ----------

## 获取日常任务
func get_daily_quests(callback: Callable = Callable()) -> int:
	return get("/quest/daily", {}, callback)


## 获取周常任务
func get_weekly_quests(callback: Callable = Callable()) -> int:
	return get("/quest/weekly", {}, callback)


## 完成任务
func complete_quest(quest_id: String, callback: Callable = Callable()) -> int:
	return post("/quest/%s/complete" % quest_id, {}, callback)


## 获取任务进度
func get_quest_progress(quest_id: String, callback: Callable = Callable()) -> int:
	return get("/quest/%s/progress" % quest_id, {}, callback)


# ==================== 工具方法 ====================

## 设置玩家 ID
func set_player_id(id: String) -> void:
	player_id = id
	print("[ApiManager] 玩家 ID 已设置: %s" % id)


## 检查是否已认证
func is_authenticated() -> bool:
	return not auth_token.is_empty()


## 获取基础 URL
func get_base_url() -> String:
	return BASE_URL
