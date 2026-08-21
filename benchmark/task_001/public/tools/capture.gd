extends SceneTree


func _initialize() -> void:
	call_deferred("_capture")


func _capture() -> void:
	var scenario := _argument_value("--scenario", "BASELINE")
	var width := _argument_value("--width", "960").to_int()
	var height := _argument_value("--height", "540").to_int()
	var output_path := _argument_value("--output", "")
	if output_path.is_empty() or width <= 0 or height <= 0:
		push_error("CAPTURE invalid arguments")
		quit(2)
		return

	root.size = Vector2i(width, height)
	DisplayServer.window_set_size(Vector2i(width, height))
	var packed := load("res://scenes/main.tscn") as PackedScene
	if packed == null:
		push_error("CAPTURE cannot load main scene")
		quit(3)
		return
	var scene := packed.instantiate() as SignalCourierScene
	root.add_child(scene)
	await process_frame
	scene.configure_scenario(scenario)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw

	var image := root.get_texture().get_image()
	if image == null or image.is_empty():
		push_error("CAPTURE empty viewport image")
		quit(4)
		return
	var save_error := image.save_png(output_path)
	print("CAPTURE scenario=%s size=%dx%d path=%s error=%d" % [scenario, image.get_width(), image.get_height(), output_path, save_error])
	quit(0 if save_error == OK and image.get_size() == Vector2i(width, height) else 5)


func _argument_value(key: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for index in args.size():
		if args[index] == key and index + 1 < args.size():
			return args[index + 1]
	return fallback
