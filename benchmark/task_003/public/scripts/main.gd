class_name EchoDashScene
extends Node2D

# The seed samples before the dash position/facing commit. Change only this
# phase to "after" to make each pooled trail use the immutable current tick.
const TRAIL_SAMPLE_PHASE := "before"
const PURPLE := Color("bd7bff")
const BLUE := Color("77b9ff")
var current_scenario := "RIGHT_TO_LEFT"

func _ready() -> void:
	queue_redraw()

func configure_scenario(value: String) -> void:
	current_scenario = value
	queue_redraw()

func frames() -> Array:
	match current_scenario:
		"LEFT_TO_RIGHT": return [-1,-1,-1,-1,1,1,1,1]
		"RIGHT": return [1,1,1,1,1,1,1,1]
		"LEFT": return [-1,-1,-1,-1,-1,-1,-1,-1]
		"INTERRUPTED": return [1,1,1,0,0,-1,-1,-1]
		"REPEATED": return [1,1,0,-1,-1,0,1,1]
		_: return [1,1,1,1,-1,-1,-1,-1]

func _draw() -> void:
	var values := frames()
	draw_rect(Rect2(Vector2.ZERO, Vector2(get_viewport_rect().size)), Color("071126"))
	draw_string(ThemeDB.fallback_font, Vector2(24, 30), "ECHO DASH // TRAIL PHASE CONTACT SHEET", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color("dbe7ff"))
	draw_string(ThemeDB.fallback_font, Vector2(24, 52), "Replay: %s  —  eight fixed physics frames" % current_scenario, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color("8295b8"))
	for index in values.size():
		_draw_frame(index, int(values[index]), int(values[max(0, index - 1)]))

func _draw_frame(index: int, facing: int, previous_facing: int) -> void:
	var column := index % 4
	var row := index / 4
	var origin := Vector2(42 + column * 230, 88 + row * 210)
	draw_style_box(_panel_style(), Rect2(origin, Vector2(202, 172)))
	draw_string(ThemeDB.fallback_font, origin + Vector2(12, 23), "TICK %02d" % index, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("9db3d5"))
	var player := origin + Vector2(104, 98)
	var trail_facing := previous_facing if TRAIL_SAMPLE_PHASE == "before" else facing
	if trail_facing == 0: trail_facing = facing
	var trail := player - Vector2(trail_facing * 44, 0)
	draw_circle(trail, 18, Color(PURPLE, 0.42))
	draw_circle(trail, 11, PURPLE)
	draw_circle(player, 16, BLUE)
	var arrow_end := player + Vector2(facing * 26, 0)
	draw_line(player, arrow_end, Color("e9f4ff"), 4)
	draw_circle(arrow_end, 4, Color("e9f4ff"))
	var label := "IDLE" if facing == 0 else ("RIGHT" if facing > 0 else "LEFT")
	draw_string(ThemeDB.fallback_font, origin + Vector2(12, 152), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("c9d8ed"))

func _panel_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new(); style.bg_color = Color("101d33"); style.border_color = Color("273b5e")
	style.set_border_width_all(2); style.set_corner_radius_all(8); return style
