extends SceneTree
const ROTATIONS := [0.0, 30.0, -55.0]
const ZOOMS := [0.72, 1.25]
const SIZES := [Vector2i(960,540), Vector2i(1280,720), Vector2i(1024,600)]
func _initialize() -> void:
	print("TASK002_SUITE initialize")
	call_deferred("_run")
func _run() -> void:
	print("TASK002_SUITE run")
	var result := {"cases": [], "errors": []}
	for size in SIZES:
		print("TASK002_SUITE size=%s" % str(size))
		root.size = size
		DisplayServer.window_set_size(size)
		print("TASK002_SUITE sized")
		for rotation in ROTATIONS:
			for zoom in ZOOMS:
				print("TASK002_SUITE case")
				var scene = load("res://scenes/main.tscn").instantiate()
				root.add_child(scene)
				scene.camera_rotation_deg = rotation
				scene.camera_zoom = zoom
				scene.objective_world = scene.player_world + Vector2(520, -170)
				scene.refresh_indicators()
				var item: Dictionary = scene.public_state()
				item["width"] = size.x
				item["height"] = size.y
				result.cases.append(item)
				scene.free()
	var out := _arg("--output-dir", "")
	DirAccess.make_dir_recursive_absolute(out)
	var file := FileAccess.open(out.path_join("suite_result.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(result))
	file.close()
	quit(0)
func _arg(key:String, fallback:String)->String:
	var args:=OS.get_cmdline_user_args()
	for i in args.size():
		if args[i]==key and i+1<args.size(): return args[i+1]
	return fallback
