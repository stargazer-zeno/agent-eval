extends SceneTree
func _initialize() -> void:
	var scene = load("res://scenes/main.tscn").instantiate(); root.add_child(scene)
	await process_frame
	if not scene.has_method("configure_scenario"): push_error("missing replay adapter"); quit(2); return
	print("SMOKE OK"); quit(0)
