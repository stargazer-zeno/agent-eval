class_name OrbitRelayScene
extends Node2D

# A camera-space HUD indicator.  The Objective path is intentionally wrong in
# this seed: its source remains in world space while its target is camera-space.
const SAFE_MARGIN := 42.0
const OBJECTIVE_SPACE_MODE := "mixed" # Change to "camera" for a behavioral fix.
const SCENARIOS := {
	"BASELINE": [30.0, 1.25, Vector2(520, -170)],
	"ROTATE_LEFT": [-55.0, 1.25, Vector2(520, -170)],
	"ZOOMED_OUT": [30.0, 0.72, Vector2(520, -170)],
}
var camera_rotation_deg := 30.0
var camera_zoom := 1.25
var player_world := Vector2(300, 200)
var objective_world := Vector2(600, -110)
var threat_world := Vector2(-260, 320)
var objective_direction := Vector2.RIGHT
var threat_direction := Vector2.RIGHT
var objective_tip := Vector2.ZERO
var threat_tip := Vector2.ZERO

func _ready() -> void:
	configure_scenario("BASELINE")

func _process(_delta: float) -> void:
	refresh_indicators()

func configure_scenario(name: String) -> void:
	var data: Array = SCENARIOS.get(name, SCENARIOS["BASELINE"])
	camera_rotation_deg = float(data[0])
	camera_zoom = float(data[1])
	objective_world = player_world + data[2]
	threat_world = player_world + Vector2(-310, 260)
	refresh_indicators()
	queue_redraw()

func camera_space(point: Vector2) -> Vector2:
	return (point - player_world).rotated(deg_to_rad(-camera_rotation_deg)) * camera_zoom

func refresh_indicators() -> void:
	var target := camera_space(objective_world)
	var source := player_world if OBJECTIVE_SPACE_MODE == "mixed" else camera_space(player_world)
	objective_direction = (target - source).normalized()
	threat_direction = (camera_space(threat_world) - camera_space(player_world)).normalized()
	objective_tip = _clamp_tip(objective_direction)
	threat_tip = _clamp_tip(threat_direction)

func _clamp_tip(direction: Vector2) -> Vector2:
	var size := Vector2(get_viewport_rect().size)
	var center := size * 0.5
	var half := center - Vector2(SAFE_MARGIN, SAFE_MARGIN)
	var scale := minf(half.x / maxf(absf(direction.x), 0.0001), half.y / maxf(absf(direction.y), 0.0001))
	return center + direction * scale

func _draw() -> void:
	var size := Vector2(get_viewport_rect().size)
	draw_rect(Rect2(Vector2.ZERO, size), Color("071126"))
	draw_string(ThemeDB.fallback_font, Vector2(25, 30), "ORBIT RELAY // EDGE INDICATOR", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color("dbe7ff"))
	draw_string(ThemeDB.fallback_font, Vector2(25, 55), "Camera rotation %.0f°  zoom %.2f" % [camera_rotation_deg, camera_zoom], HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color("8295b8"))
	var center := size * 0.5
	draw_circle(center, 14, Color("79a7ff"))
	draw_arc(center, 120, 0, TAU, 48, Color("1b3b63"), 2)
	# The world-space beacons are represented inside the camera ring. The HUD
	# indicators must agree with these camera-space relationships.
	var objective_world_direction := (camera_space(objective_world) - camera_space(player_world)).normalized()
	var threat_world_direction := (camera_space(threat_world) - camera_space(player_world)).normalized()
	draw_dashed_line(center, center + objective_world_direction * 112, Color("f5c451", 0.45), 2.0, 6.0)
	draw_dashed_line(center, center + threat_world_direction * 112, Color("ee6474", 0.45), 2.0, 6.0)
	draw_circle(center + objective_world_direction * 112, 7.0, Color("f5c451"))
	draw_circle(center + threat_world_direction * 112, 7.0, Color("ee6474"))
	_draw_indicator(objective_tip, objective_direction, Color("f5c451"), "OBJECTIVE")
	_draw_indicator(threat_tip, threat_direction, Color("ee6474"), "THREAT")

func _draw_indicator(tip: Vector2, direction: Vector2, color: Color, label: String) -> void:
	var normal := Vector2(-direction.y, direction.x)
	var base := tip - direction * 26.0
	# Lines are deliberately used instead of a polygon here: hidden-window GL
	# capture on the target AMD driver is stable for CanvasItem primitives.
	draw_line(base + normal * 10, tip, color, 5.0, true)
	draw_line(base - normal * 10, tip, color, 5.0, true)
	draw_line(base + normal * 10, base - normal * 10, color, 4.0, true)
	draw_circle(tip, 4.0, color)
	draw_string(ThemeDB.fallback_font, base - direction * 8 - normal * 22, label, HORIZONTAL_ALIGNMENT_CENTER, 110, 13, color)

func public_state() -> Dictionary:
	var expected := (camera_space(objective_world) - camera_space(player_world)).normalized()
	return {"objective_dot": objective_direction.dot(expected), "threat_dot": threat_direction.dot((camera_space(threat_world) - camera_space(player_world)).normalized()), "objective_tip": [objective_tip.x, objective_tip.y], "threat_tip": [threat_tip.x, threat_tip.y], "camera_rotation": camera_rotation_deg, "camera_zoom": camera_zoom, "safe_margin": SAFE_MARGIN}
