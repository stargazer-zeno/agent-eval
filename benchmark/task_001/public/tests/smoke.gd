extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://scenes/main.tscn") as PackedScene
	if packed == null:
		push_error("SMOKE main scene failed to load")
		quit(1)
		return
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame

	var required_paths := [
		"Player",
		"ObjectiveBeacon",
		"ThreatDrone",
		"HUD/ObjectivePanel/ObjectiveArrow",
		"HUD/ThreatPanel/ThreatArrow",
	]
	for path in required_paths:
		if scene.get_node_or_null(path) == null:
			push_error("SMOKE missing required runtime node")
			quit(2)
			return

	var objective_arrow = scene.get_node("HUD/ObjectivePanel/ObjectiveArrow")
	var threat_arrow = scene.get_node("HUD/ThreatPanel/ThreatArrow")
	if objective_arrow.texture == null or threat_arrow.texture == null:
		push_error("SMOKE tracker texture missing")
		quit(3)
		return
	if objective_arrow.tracked_target == null or threat_arrow.tracked_target == null:
		push_error("SMOKE tracker target binding missing")
		quit(4)
		return
	for action in ["move_up", "move_left", "move_down", "move_right"]:
		if not InputMap.has_action(action) or InputMap.action_get_events(action).is_empty():
			push_error("SMOKE movement action missing")
			quit(5)
			return
	if not scene.has_method("complete_objective_if_overlapping"):
		push_error("SMOKE objective completion pipeline missing")
		quit(6)
		return

	print("SMOKE PASS project, movement, completion, and both tracker pipelines are connected")
	quit(0)
