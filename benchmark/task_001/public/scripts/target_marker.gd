class_name TargetMarker
extends Node2D

@export var marker_label: String = "Target"
@export var marker_color: Color = Color.WHITE
@export var is_threat: bool = false

var completed := false


func _ready() -> void:
	queue_redraw()


func _draw() -> void:
	var draw_color := marker_color.darkened(0.45) if completed else marker_color
	if is_threat:
		var diamond := PackedVector2Array([
			Vector2(0, -17),
			Vector2(17, 0),
			Vector2(0, 17),
			Vector2(-17, 0),
		])
		draw_colored_polygon(diamond, draw_color)
		draw_polyline(diamond + PackedVector2Array([diamond[0]]), Color("371923"), 3.0)
		draw_circle(Vector2.ZERO, 5.0, Color("fff3f4"))
	else:
		draw_circle(Vector2.ZERO, 17.0, draw_color)
		draw_arc(Vector2.ZERO, 17.0, 0.0, TAU, 32, Color("15382d"), 3.0)
		draw_circle(Vector2.ZERO, 6.0, Color("eafff6"))

	var font := ThemeDB.fallback_font
	draw_string(
		font,
		Vector2(-80, -25),
		marker_label,
		HORIZONTAL_ALIGNMENT_CENTER,
		160.0,
		16,
		Color("f2f7ff")
	)
	if completed:
		draw_string(font, Vector2(-58, 42), "SECURED", HORIZONTAL_ALIGNMENT_CENTER, 116.0, 14, Color("ffd166"))


func set_completed(value: bool) -> void:
	completed = value
	queue_redraw()
