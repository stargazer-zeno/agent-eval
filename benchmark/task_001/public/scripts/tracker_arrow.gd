class_name TrackerArrow
extends Sprite2D

@export var profile: TrackerProfile

var tracked_source: Node2D
var tracked_target: Node2D


func _ready() -> void:
	if profile != null:
		texture = profile.icon
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	centered = true
	refresh_direction()


func bind_world_nodes(source: Node2D, target: Node2D) -> void:
	tracked_source = source
	tracked_target = target
	refresh_direction()


func refresh_direction() -> void:
	if profile == null or tracked_source == null or tracked_target == null:
		return
	var target_direction := tracked_target.global_position - tracked_source.global_position
	if target_direction.length_squared() <= 0.000001:
		return
	rotation = target_direction.angle() + profile.art_forward_offset


func target_direction() -> Vector2:
	if tracked_source == null or tracked_target == null:
		return Vector2.ZERO
	return (tracked_target.global_position - tracked_source.global_position).normalized()
