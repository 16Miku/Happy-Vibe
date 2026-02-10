extends CharacterBody2D
## 玩家角色脚本

signal interacted(target: Node2D)

@export var move_speed: float = 200.0

var current_direction: Vector2 = Vector2.DOWN


func _physics_process(_delta: float) -> void:
	_handle_movement()
	_handle_interaction()


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

	if input_direction != Vector2.ZERO:
		input_direction = input_direction.normalized()
		current_direction = input_direction

	velocity = input_direction * move_speed
	move_and_slide()


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
