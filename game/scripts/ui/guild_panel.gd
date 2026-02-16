## guild_panel.gd
## 公会面板脚本
extends Control

## 面板状态枚举
enum PanelState {
	MY_GUILD,      # 我的公会
	GUILD_LIST,    # 公会列表
	CREATE_GUILD   # 创建公会
}

## 当前状态
var current_state: PanelState = PanelState.MY_GUILD

## 公会列表项场景
var guild_item_scene: PackedScene = null

@onready var close_button: Button = $Header/CloseButton
@onready var content_panel: Control = $Content
@onready var my_guild_panel: VBoxContainer = $Content/MyGuildPanel
@onready var guild_list_panel: VBoxContainer = $Content/GuildListPanel
@onready var create_guild_panel: VBoxContainer = $Content/CreateGuildPanel

## 我的公会面板节点
@onready var guild_name_label: Label = $Content/MyGuildPanel/GuildInfo/GuildNameLabel
@onready var guild_level_label: Label = $Content/MyGuildPanel/GuildInfo/GuildLevelLabel
@onready var guild_desc_label: Label = $Content/MyGuildPanel/GuildInfo/GuildDescLabel
@onready var guild_members_label: Label = $Content/MyGuildPanel/GuildInfo/GuildMembersLabel
@onready var guild_rank_label: Label = $Content/MyGuildPanel/GuildInfo/GuildRankLabel
@onready var member_list: VBoxContainer = $Content/MyGuildPanel/MemberList/ScrollContainer/MemberList
@onready var leave_button: Button = $Content/MyGuildPanel/LeaveButton

## 公会列表面板节点
@onready var guild_list: VBoxContainer = $Content/GuildListPanel/ScrollContainer/GuildList
@onready var refresh_button: Button = $Content/GuildListPanel/RefreshButton
@onready var create_button: Button = $Content/GuildListPanel/CreateButton
@onready var join_button: Button = $Content/GuildListPanel/JoinButton

## 创建公会面板节点
@onready var guild_name_input: LineEdit = $Content/CreateGuildPanel/Form/GuildNameInput
@onready var guild_desc_input: TextEdit = $Content/CreateGuildPanel/Form/GuildDescInput
@onready var confirm_create_button: Button = $Content/CreateGuildPanel/ConfirmButton
@onready var cancel_create_button: Button = $Content/CreateGuildPanel/CancelButton

## 当前选中的公会 ID
var selected_guild_id: String = ""

func _ready() -> void:
	_setup_buttons()
	_load_guild_item_scene()
	_check_guild_status()

	if DataManager:
		DataManager.guild_data_updated.connect(_on_guild_data_updated)


func _setup_buttons() -> void:
	"""设置按钮连接"""
	if close_button:
		close_button.pressed.connect(_on_close_pressed)

	if leave_button:
		leave_button.pressed.connect(_on_leave_guild)

	if refresh_button:
		refresh_button.pressed.connect(_on_refresh_list)

	if create_button:
		create_button.pressed.connect(_on_show_create_panel)

	if confirm_create_button:
		confirm_create_button.pressed.connect(_on_create_guild)

	if cancel_create_button:
		cancel_create_button.pressed.connect(_on_cancel_create)

	if join_button:
		join_button.pressed.connect(_on_join_guild)


func _load_guild_item_scene() -> void:
	"""加载公会列表项场景"""
	guild_item_scene = load("res://scenes/ui/guild/guild_item.tscn")


## 检查公会状态
func _check_guild_status() -> void:
	"""检查玩家是否有公会"""
	if not DataManager:
		return

	var my_guild = DataManager.get_my_guild()
	if my_guild and not my_guild.id.is_empty():
		_show_my_guild()
	else:
		_show_guild_list()


## 显示我的公会
func _show_my_guild() -> void:
	"""显示我的公会信息"""
	current_state = PanelState.MY_GUILD

	if my_guild_panel:
		my_guild_panel.visible = true
	if guild_list_panel:
		guild_list_panel.visible = false
	if create_guild_panel:
		create_guild_panel.visible = false

	_update_my_guild_display()


## 显示公会列表
func _show_guild_list() -> void:
	"""显示公会列表"""
	current_state = PanelState.GUILD_LIST

	if my_guild_panel:
		my_guild_panel.visible = false
	if guild_list_panel:
		guild_list_panel.visible = true
	if create_guild_panel:
		create_guild_panel.visible = false

	_refresh_guild_list()


## 显示创建公会面板
func _show_create_guild() -> void:
	"""显示创建公会面板"""
	current_state = PanelState.CREATE_GUILD

	if my_guild_panel:
		my_guild_panel.visible = false
	if guild_list_panel:
		guild_list_panel.visible = false
	if create_guild_panel:
		create_guild_panel.visible = true


## 更新我的公会显示
func _update_my_guild_display() -> void:
	"""更新我的公会信息显示"""
	if not DataManager:
		return

	var my_guild = DataManager.get_my_guild()
	if not my_guild:
		return

	if guild_name_label:
		guild_name_label.text = my_guild.name
	if guild_level_label:
		guild_level_label.text = "Lv.%d" % my_guild.level
	if guild_desc_label:
		guild_desc_label.text = my_guild.description
	if guild_members_label:
		guild_members_label.text = "成员: %d / %d" % [my_guild.member_count, my_guild.max_members]
	if guild_rank_label:
		guild_rank_label.text = "排名: #%d" % my_guild.rank if my_guild.rank > 0 else "排名: 未上榜"

	# TODO: 加载成员列表


## 刷新公会列表
func _refresh_guild_list() -> void:
	"""刷新公会列表"""
	if not DataManager:
		return

	DataManager.fetch_guild_list(1, func(success: bool, data: Dictionary):
		if success:
			_display_guild_list()
	)


## 显示公会列表
func _display_guild_list() -> void:
	"""显示公会列表"""
	if not guild_list:
		return

	# 清空现有列表
	for child in guild_list.get_children():
		child.queue_free()

	if not DataManager:
		return

	var guilds = DataManager.get_guild_list()
	for guild in guilds:
		if not guild_item_scene:
			continue

		var item = guild_item_scene.instantiate()
		item.set_guild_data(guild)
		item.guild_selected.connect(_on_guild_selected)
		guild_list.add_child(item)


## 离开公会
func _on_leave_guild() -> void:
	"""离开公会"""
	EventBus.request_confirm.emit(
		"离开公会",
		"确定要离开公会吗？离开后需要等待24小时才能加入新公会。",
		func():
			if DataManager:
				DataManager.leave_guild(func(success: bool, data: Dictionary):
					if success:
						EventBus.notify_success.call("已离开公会")
						_show_guild_list()
					else:
						EventBus.notify_error.call("离开公会失败")
				)
	)


## 刷新列表按钮
func _on_refresh_list() -> void:
	"""刷新公会列表"""
	_refresh_guild_list()


## 显示创建面板
func _on_show_create_panel() -> void:
	"""显示创建公会面板"""
	_show_create_guild()


## 创建公会
func _on_create_guild() -> void:
	"""创建公会"""
	var guild_name := guild_name_input.text if guild_name_input else ""
	var guild_desc := guild_desc_input.text if guild_desc_input else ""

	if guild_name.is_empty():
		EventBus.notify_warning("请输入公会名称")
		return

	if not ApiManager:
		return

	ApiManager.create_guild({
		"name": guild_name,
		"description": guild_desc
	}, func(success: bool, data: Dictionary):
		if success:
			EventBus.notify_success.call("公会创建成功")
			DataManager.sync_guilds()
			_show_my_guild()
		else:
			EventBus.notify_error.call("公会创建失败")
	)


## 取消创建
func _on_cancel_create() -> void:
	"""取消创建公会"""
	_show_guild_list()


## 加入公会
func _on_join_guild() -> void:
	"""加入选中的公会"""
	if selected_guild_id.is_empty():
		EventBus.notify_warning("请先选择一个公会")
		return

	if not DataManager:
		return

	DataManager.join_guild(selected_guild_id, func(success: bool, data: Dictionary):
		if success:
			EventBus.notify_success.call("已申请加入公会")
		else:
			EventBus.notify_error.call("加入公会失败")
	)


## 公会被选中
func _on_guild_selected(guild_id: String) -> void:
	"""处理公会选中"""
	selected_guild_id = guild_id

	# 更新选中状态
	if guild_list:
		for child in guild_list.get_children():
			if child.has_method("set_selected"):
				child.set_selected(child.guild_id == guild_id)


## 公会数据更新回调
func _on_guild_data_updated() -> void:
	"""当公会数据更新时刷新"""
	_check_guild_status()


## 关闭按钮点击
func _on_close_pressed() -> void:
	"""关闭面板"""
	hide()


## 打开面板
func open() -> void:
	"""打开面板并刷新数据"""
	show()
	if DataManager:
		DataManager.sync_guilds()
