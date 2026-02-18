extends CharacterBody2D
## 玩家角色脚本

signal interacted(target: Node2D)

@export var move_speed: float = 200.0

@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer

var current_direction: Vector2 = Vector2.DOWN
var is_moving: bool = false

# 方向精灵纹理
var direction_textures: Dictionary = {}


func _ready() -> void:
	_load_direction_textures()


func _load_direction_textures() -> void:
	"""加载各方向的精灵纹理"""
	direction_textures = {
		"down": [
			load("res://assets/sprites/player/player_down_1.png"),
			load("res://assets/sprites/player/player_down_2.png"),
			load("res://assets/sprites/player/player_down_3.png")
		],
		"up": [
			load("res://assets/sprites/player/player_up_1.png"),
			load("res://assets/sprites/player/player_up_2.png"),
			load("res://assets/sprites/player/player_up_3.png")
		],
		"left": [
			load("res://assets/sprites/player/player_left_1.png"),
			load("res://assets/sprites/player/player_left_2.png"),
			load("res://assets/sprites/player/player_left_3.png")
		],
		"right": [
			load("res://assets/sprites/player/player_right_1.png"),
			load("res://assets/sprites/player/player_right_2.png"),
			load("res://assets/sprites/player/player_right_3.png")
		]
	}


func _physics_process(_delta: float) -> void:
	_handle_movement()
	_handle_interaction()
	_update_animation()


func _handle_movement() -> void:
	"""处理移动输入"""
	var input_direction := Vector2.ZERO

	if Input.is_action_pressed("move_up"):
		input_direction.y -= 1
	if Input.is_action_pressed("move_down"):
		input_direction.y += 1
	if Input.is_action_pressed("move_left"):
		input_direction.x -= 1
	if Input.is_action_pressed("move_right"):
		input_direction.x += 1

	is_moving = input_direction != Vector2.ZERO

	if is_moving:
		input_direction = input_direction.normalized()
		current_direction = input_direction

	velocity = input_direction * move_speed
	move_and_slide()


func _update_animation() -> void:
	"""更新动画状态"""
	if not sprite:
		return

	var direction_name := _get_direction_name()
	var textures: Array = direction_textures.get(direction_name, [])

	if textures.is_empty():
		return

	if is_moving:
		# 简单的帧动画：根据时间切换帧
		var frame_index := int(Time.get_ticks_msec() / 150) % textures.size()
		sprite.texture = textures[frame_index]
	else:
		# 静止时显示第一帧
		sprite.texture = textures[0]


func _get_direction_name() -> String:
	"""根据当前方向获取方向名称"""
	if abs(current_direction.x) > abs(current_direction.y):
		return "right" if current_direction.x > 0 else "left"
	else:
		return "down" if current_direction.y >= 0 else "up"


func _handle_interaction() -> void:
	"""处理交互输入"""
	if Input.is_action_just_pressed("interact"):
		_try_interact()


func _try_interact() -> void:
	"""尝试与附近物体交互"""
	# 检测交互范围内的物体
	var space_state := get_world_2d().direct_space_state
	var query := PhysicsRayQueryParameters2D.create(
		global_position,
		global_position + current_direction * 50.0
	)
	query.exclude = [self]

	var result := space_state.intersect_ray(query)
	if result and result.collider:
		var target := result.collider
		if target.has_method("interact"):
			target.interact(self)
			interacted.emit(target)
