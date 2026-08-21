extends SceneTree

const SCENARIOS := ["E", "N", "W", "S", "NE"]
const RESOLUTIONS := [Vector2i(960, 540), Vector2i(1280, 720)]


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var output_dir := _argument_value("--output-dir", "")
	if output_dir.is_empty():
		push_error("PRIVATE_SUITE missing --output-dir")
		quit(2)
		return
	var mkdir_error := DirAccess.make_dir_recursive_absolute(output_dir)
	if mkdir_error != OK and mkdir_error != ERR_ALREADY_EXISTS:
		push_error("PRIVATE_SUITE cannot create output directory")
		quit(3)
		return

	var packed := load("res://scenes/main.tscn") as PackedScene
	if packed == null:
		push_error("PRIVATE_SUITE cannot load main scene")
		quit(4)
		return

	var result := {
		"godot_version": Engine.get_version_info(),
		"display_server": DisplayServer.get_name(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"cases": [],
		"dynamic": {},
		"behavior": {},
		"suite_errors": [],
	}

	for resolution in RESOLUTIONS:
		root.size = resolution
		DisplayServer.window_set_size(resolution)
		await process_frame
		await process_frame
		for scenario in SCENARIOS:
			var scene = packed.instantiate()
			root.add_child(scene)
			await process_frame
			if not scene.has_method("configure_scenario"):
				result.suite_errors.append("main scene lacks configure_scenario")
			else:
				scene.configure_scenario(scenario)
			await process_frame
			await process_frame
			# A fixed pair of rendered frames is more reliable than waiting on
			# frame_post_draw in a hidden Windows Compatibility window: the signal
			# may not fire again when the scene becomes visually idle.
			await process_frame
			await process_frame

			var case_data := _inspect_scene(scene)
			case_data["scenario"] = scenario
			case_data["width"] = resolution.x
			case_data["height"] = resolution.y
			var capture_path := output_dir.path_join("%dx%d_%s.png" % [resolution.x, resolution.y, scenario])
			var image := root.get_texture().get_image()
			if image == null or image.is_empty():
				case_data["capture_error"] = "empty viewport image"
				result.suite_errors.append("empty image for %s" % capture_path)
			else:
				case_data["image_width"] = image.get_width()
				case_data["image_height"] = image.get_height()
				case_data["capture_error"] = image.save_png(capture_path)
			case_data["capture_path"] = capture_path
			result.cases.append(case_data)
			scene.free()
	print("PRIVATE_SUITE_PHASE matrix_complete")

	# Keep the final matrix resolution. Resizing a hidden Windows/OpenGL window
	# back to 960x540 can block after the ten captures have already completed.
	var dynamic_scene = packed.instantiate()
	print("PRIVATE_SUITE_PHASE dynamic_start")
	root.add_child(dynamic_scene)
	await process_frame
	dynamic_scene.configure_scenario("E")
	await process_frame
	var before := _inspect_scene(dynamic_scene)
	var objective_update := Vector2(0.6, 0.8)
	var threat_update := Vector2(-0.8, 0.6)
	dynamic_scene.set_target_directions(objective_update, threat_update)
	var after := _inspect_scene(dynamic_scene)
	var dynamic_capture := output_dir.path_join("1280x720_DYNAMIC.png")
	var dynamic_image := root.get_texture().get_image()
	var dynamic_capture_error := ERR_CANT_CREATE
	if dynamic_image != null and not dynamic_image.is_empty():
		dynamic_capture_error = dynamic_image.save_png(dynamic_capture)
	result.dynamic = {
		"before": before,
		"after": after,
		"expected_objective_direction": _vector(objective_update),
		"expected_threat_direction": _vector(threat_update),
		"capture_path": dynamic_capture,
		"capture_error": dynamic_capture_error,
	}
	print("PRIVATE_SUITE_PHASE dynamic_complete")
	dynamic_scene.free()

	var behavior_scene = packed.instantiate()
	print("PRIVATE_SUITE_PHASE behavior_start")
	root.add_child(behavior_scene)
	await process_frame
	behavior_scene.configure_scenario("BASELINE")
	await process_frame
	var behavior_player := behavior_scene.get_node_or_null("Player") as Node2D
	var behavior_objective := behavior_scene.get_node_or_null("ObjectiveBeacon") as Node2D
	var movement_results := {}
	var action_expectations := {
		"move_up": Vector2.UP,
		"move_left": Vector2.LEFT,
		"move_down": Vector2.DOWN,
		"move_right": Vector2.RIGHT,
	}
	var initial_player_position := behavior_player.position if behavior_player != null else Vector2.ZERO
	for action in action_expectations:
		if behavior_player == null:
			movement_results[action] = {"delta": [0.0, 0.0], "event_codes": []}
			continue
		behavior_player.position = initial_player_position
		Input.action_press(action, 1.0)
		behavior_player.call("_physics_process", 1.0 / 60.0)
		Input.action_release(action)
		var movement_delta: Vector2 = behavior_player.position - initial_player_position
		var event_codes := []
		for event in InputMap.action_get_events(action):
			if event is InputEventKey:
				event_codes.append(event.physical_keycode)
		movement_results[action] = {
			"delta": _vector(movement_delta),
			"event_codes": event_codes,
		}

	var completion_before := bool(behavior_scene.get("objective_completed"))
	if behavior_scene.has_method("reset_objective_completion"):
		behavior_scene.reset_objective_completion()
	if behavior_player != null and behavior_objective != null:
		behavior_player.position = behavior_objective.position
	if behavior_scene.has_method("complete_objective_if_overlapping"):
		behavior_scene.complete_objective_if_overlapping()
	var completion_after := bool(behavior_scene.get("objective_completed"))
	var marker_completed := bool(behavior_objective.get("completed")) if behavior_objective != null else false
	result.behavior = {
		"required_nodes_present": behavior_player != null and behavior_objective != null,
		"movement": movement_results,
		"completion_before": completion_before,
		"completion_after": completion_after,
		"marker_completed": marker_completed,
	}
	print("PRIVATE_SUITE_PHASE behavior_complete")
	behavior_scene.free()

	var result_path := output_dir.path_join("suite_result.json")
	print("PRIVATE_SUITE_PHASE result_write_start")
	var result_file := FileAccess.open(result_path, FileAccess.WRITE)
	if result_file == null:
		push_error("PRIVATE_SUITE cannot write result")
		quit(5)
		return
	result_file.store_string(JSON.stringify(result, "  "))
	result_file.close()
	print("PRIVATE_SUITE cases=%d errors=%d result=%s" % [result.cases.size(), result.suite_errors.size(), result_path])
	quit(0 if result.suite_errors.is_empty() else 6)


func _inspect_scene(scene: Node) -> Dictionary:
	var player := scene.get_node_or_null("Player") as Node2D
	var objective := scene.get_node_or_null("ObjectiveBeacon") as Node2D
	var threat := scene.get_node_or_null("ThreatDrone") as Node2D
	var objective_arrow := scene.get_node_or_null("HUD/ObjectivePanel/ObjectiveArrow") as Sprite2D
	var threat_arrow := scene.get_node_or_null("HUD/ThreatPanel/ThreatArrow") as Sprite2D
	if player == null or objective == null or threat == null or objective_arrow == null or threat_arrow == null:
		return {"missing_required_node": true}

	var objective_direction := (objective.global_position - player.global_position).normalized()
	var threat_direction := (threat.global_position - player.global_position).normalized()
	var objective_forward := Vector2.RIGHT.rotated(objective_arrow.global_rotation).normalized()
	var threat_forward := Vector2.LEFT.rotated(threat_arrow.global_rotation).normalized()
	var objective_tracked_target = objective_arrow.get("tracked_target")
	var threat_tracked_target = threat_arrow.get("tracked_target")
	var objective_profile = objective_arrow.get("profile")
	var threat_profile = threat_arrow.get("profile")
	return {
		"missing_required_node": false,
		"player_position": _vector(player.global_position),
		"objective_position": _vector(objective.global_position),
		"threat_position": _vector(threat.global_position),
		"objective_center": _vector(objective_arrow.global_position),
		"threat_center": _vector(threat_arrow.global_position),
		"objective_target_direction": _vector(objective_direction),
		"threat_target_direction": _vector(threat_direction),
		"objective_visible_forward": _vector(objective_forward),
		"threat_visible_forward": _vector(threat_forward),
		"objective_dot": objective_forward.dot(objective_direction),
		"threat_dot": threat_forward.dot(threat_direction),
		"objective_visible": objective_arrow.is_visible_in_tree() and objective_arrow.modulate.a > 0.99,
		"threat_visible": threat_arrow.is_visible_in_tree() and threat_arrow.modulate.a > 0.99,
		"objective_global_scale": _vector(objective_arrow.global_scale),
		"threat_global_scale": _vector(threat_arrow.global_scale),
		"objective_effective_alpha": objective_arrow.modulate.a * objective_arrow.self_modulate.a,
		"threat_effective_alpha": threat_arrow.modulate.a * threat_arrow.self_modulate.a,
		"objective_texture": objective_arrow.texture.resource_path if objective_arrow.texture != null else "",
		"threat_texture": threat_arrow.texture.resource_path if threat_arrow.texture != null else "",
		"objective_bound_target": str(objective_tracked_target.name) if objective_tracked_target is Node else "",
		"threat_bound_target": str(threat_tracked_target.name) if threat_tracked_target is Node else "",
		"objective_offset": float(objective_profile.get("art_forward_offset")) if objective_profile != null else NAN,
		"threat_offset": float(threat_profile.get("art_forward_offset")) if threat_profile != null else NAN,
	}


func _vector(value: Vector2) -> Array:
	return [value.x, value.y]


func _argument_value(key: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for index in args.size():
		if args[index] == key and index + 1 < args.size():
			return args[index + 1]
	return fallback
