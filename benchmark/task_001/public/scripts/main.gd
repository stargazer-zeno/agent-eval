class_name SignalCourierScene
extends Node2D

const DIRECTIONS := {
	"E": Vector2(1, 0),
	"N": Vector2(0, -1),
	"W": Vector2(-1, 0),
	"S": Vector2(0, 1),
	"NE": Vector2(0.7071067811865476, -0.7071067811865476),
}
const BASELINE_THREAT_DIRECTION := Vector2(-0.7071067811865476, -0.7071067811865476)
const COMPLETION_DISTANCE := 24.0

@onready var player: CourierPlayer = $Player
@onready var objective_beacon: Node2D = $ObjectiveBeacon
@onready var threat_drone: Node2D = $ThreatDrone
@onready var objective_panel: Node2D = $HUD/ObjectivePanel
@onready var threat_panel: Node2D = $HUD/ThreatPanel
@onready var objective_arrow: TrackerArrow = $HUD/ObjectivePanel/ObjectiveArrow
@onready var threat_arrow: TrackerArrow = $HUD/ThreatPanel/ThreatArrow

var current_scenario := "BASELINE"
var objective_completed := false


func _ready() -> void:
	get_viewport().size_changed.connect(_layout_scene)
	objective_arrow.bind_world_nodes(player, objective_beacon)
	threat_arrow.bind_world_nodes(player, threat_drone)
	_layout_scene()
	configure_scenario(current_scenario)


func _process(_delta: float) -> void:
	objective_arrow.refresh_direction()
	threat_arrow.refresh_direction()
	complete_objective_if_overlapping()


func configure_scenario(scenario_name: String) -> void:
	if scenario_name == "BASELINE":
		current_scenario = scenario_name
		_set_target_directions(Vector2.RIGHT, BASELINE_THREAT_DIRECTION)
		return
	if not DIRECTIONS.has(scenario_name):
		push_error("Unknown scenario: %s" % scenario_name)
		return
	current_scenario = scenario_name
	var objective_direction: Vector2 = DIRECTIONS[scenario_name]
	var threat_direction := Vector2(-objective_direction.y, objective_direction.x)
	_set_target_directions(objective_direction, threat_direction)


func set_target_directions(objective_direction: Vector2, threat_direction: Vector2) -> void:
	_set_target_directions(objective_direction.normalized(), threat_direction.normalized())


func _set_target_directions(objective_direction: Vector2, threat_direction: Vector2) -> void:
	var viewport_size := Vector2(get_viewport_rect().size)
	var play_height := maxf(220.0, viewport_size.y - 150.0)
	var radius := minf(viewport_size.x * 0.22, play_height * 0.34)
	objective_beacon.position = player.position + objective_direction * radius
	threat_drone.position = player.position + threat_direction * radius
	objective_arrow.refresh_direction()
	threat_arrow.refresh_direction()
	queue_redraw()


func _layout_scene() -> void:
	var viewport_size := Vector2(get_viewport_rect().size)
	player.position = Vector2(viewport_size.x * 0.5, (viewport_size.y - 145.0) * 0.52)
	player.set_movement_bounds(Rect2(40, 55, viewport_size.x - 80, viewport_size.y - 205))
	objective_panel.position = Vector2(160.0, viewport_size.y - 68.0)
	threat_panel.position = Vector2(viewport_size.x - 160.0, viewport_size.y - 68.0)
	configure_scenario(current_scenario)
	queue_redraw()


func complete_objective_if_overlapping() -> bool:
	if not objective_completed and player.global_position.distance_to(objective_beacon.global_position) <= COMPLETION_DISTANCE:
		objective_completed = true
		objective_beacon.set_completed(true)
	return objective_completed


func reset_objective_completion() -> void:
	objective_completed = false
	objective_beacon.set_completed(false)


func expected_tracker_centers() -> Dictionary:
	return {
		"objective": objective_panel.position,
		"threat": threat_panel.position,
	}


func _draw() -> void:
	var viewport_size := Vector2(get_viewport_rect().size)
	draw_rect(Rect2(Vector2.ZERO, viewport_size), Color("071126"))
	draw_rect(Rect2(18, 48, viewport_size.x - 36, viewport_size.y - 178), Color("0d1d35"))

	for x in range(40, int(viewport_size.x), 40):
		draw_line(Vector2(x, 48), Vector2(x, viewport_size.y - 130), Color("142b49"), 1.0)
	for y in range(70, int(viewport_size.y - 130), 40):
		draw_line(Vector2(18, y), Vector2(viewport_size.x - 18, y), Color("142b49"), 1.0)

	draw_dashed_line(player.position, objective_beacon.position, Color("3f9874"), 2.0, 7.0)
	draw_dashed_line(player.position, threat_drone.position, Color("a94352"), 2.0, 7.0)

	draw_circle(player.position, 21.0, Color("79a7ff"))
	draw_circle(player.position, 9.0, Color("dbe7ff"))
	draw_arc(player.position, 21.0, 0.0, TAU, 36, Color("203b6d"), 3.0)

	_draw_tracker_panel(objective_panel.position, Color("4ce6a1"))
	_draw_tracker_panel(threat_panel.position, Color("ec4e5c"))

	var font := ThemeDB.fallback_font
	draw_string(font, Vector2(24, 31), "SIGNAL COURIER // TRACKER CALIBRATION", HORIZONTAL_ALIGNMENT_LEFT, -1.0, 19, Color("dbe7ff"))
	draw_string(font, objective_panel.position + Vector2(-78, -39), "OBJECTIVE TRACKER", HORIZONTAL_ALIGNMENT_CENTER, 156.0, 15, Color("aef6d5"))
	draw_string(font, threat_panel.position + Vector2(-70, -39), "THREAT TRACKER", HORIZONTAL_ALIGNMENT_CENTER, 140.0, 15, Color("ffc0c5"))
	draw_string(font, Vector2(24, viewport_size.y - 16), "Both tracker cards read direction from the courier at center.", HORIZONTAL_ALIGNMENT_LEFT, -1.0, 14, Color("8295b8"))


func _draw_tracker_panel(center: Vector2, accent: Color) -> void:
	draw_style_box(_panel_style(), Rect2(center - Vector2(105, 45), Vector2(210, 90)))
	draw_circle(center, 29.0, Color("081120"))
	draw_arc(center, 30.0, 0.0, TAU, 40, accent, 2.0)
	draw_circle(center, 3.0, Color("f7fbff"))


func _panel_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("101d33")
	style.border_color = Color("273b5e")
	style.set_border_width_all(2)
	style.set_corner_radius_all(8)
	return style
