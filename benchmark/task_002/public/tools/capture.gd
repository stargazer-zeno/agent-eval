extends SceneTree
func _initialize() -> void:
	call_deferred("_capture")
func _capture() -> void:
	var output := _arg("--output", "")
	var scenario := _arg("--scenario", "BASELINE")
	if output.is_empty(): quit(2); return
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.configure_scenario(scenario)
	await process_frame
	await process_frame
	var image := root.get_texture().get_image()
	var err := image.save_png(output) if image != null else ERR_CANT_CREATE
	print("CAPTURE scenario=%s err=%d" % [scenario, err])
	quit(0 if err == OK else 3)
func _arg(key: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for i in args.size():
		if args[i] == key and i + 1 < args.size(): return args[i + 1]
	return fallback
