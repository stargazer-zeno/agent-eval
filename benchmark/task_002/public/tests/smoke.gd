extends SceneTree
func _initialize() -> void:
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	if not scene.has_method("public_state"): push_error("missing state"); quit(2); return
	print("SMOKE OK")
	quit(0)
