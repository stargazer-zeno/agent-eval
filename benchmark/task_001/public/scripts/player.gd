class_name CourierPlayer
extends Node2D

@export var movement_speed := 180.0

var movement_bounds := Rect2(40, 55, 880, 335)


func _physics_process(delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	move_in_direction(direction, delta)


func move_in_direction(direction: Vector2, delta: float) -> void:
	if direction.length_squared() <= 0.000001:
		return
	position += direction.normalized() * movement_speed * delta
	position.x = clampf(position.x, movement_bounds.position.x, movement_bounds.end.x)
	position.y = clampf(position.y, movement_bounds.position.y, movement_bounds.end.y)


func set_movement_bounds(bounds: Rect2) -> void:
	movement_bounds = bounds
