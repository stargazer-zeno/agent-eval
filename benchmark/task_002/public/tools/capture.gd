extends SceneTree
func _initialize() -> void:
	call_deferred("_capture")
func _capture() -> void:
	var output := _arg("--output", "")
	var scenario := _arg("--scenario", "BASELINE")
	var width := _arg("--width", "960").to_int()
	var height := _arg("--height", "540").to_int()
	if output.is_empty(): quit(2); return
	# Match the validated Task 001 capture lifecycle. A zero-sized root viewport
	# can crash the Windows Compatibility renderer before script diagnostics.
	root.size = Vector2i(width, height)
	DisplayServer.window_set_size(Vector2i(width, height))
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.configure_scenario(scenario)
	var rotation_override := _arg("--rotation", "")
	var zoom_override := _arg("--zoom", "")
	if not rotation_override.is_empty():
		scene.camera_rotation_deg = rotation_override.to_float()
	if not zoom_override.is_empty():
		scene.camera_zoom = zoom_override.to_float()
	if not rotation_override.is_empty() or not zoom_override.is_empty():
		scene.refresh_indicators()
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var err := image.save_png(output) if image != null else ERR_CANT_CREATE
	print("CAPTURE scenario=%s err=%d" % [scenario, err])
	quit(0 if err == OK else 3)
func _arg(key: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for i in args.size():
		if args[i] == key and i + 1 < args.size(): return args[i + 1]
	return fallback
