extends SceneTree

const SIZE := Vector2i(64, 32)
const OBJECTIVE_BODY := Color8(76, 230, 161, 255)
const OBJECTIVE_TIP := Color8(176, 255, 210, 255)
const THREAT_BODY := Color8(236, 78, 92, 255)
const THREAT_TIP := Color8(255, 190, 197, 255)


func _initialize() -> void:
	var output_dir := _argument_value("--output-dir", "")
	if output_dir.is_empty():
		push_error("ASSET_GENERATION missing private output directory")
		quit(2)
		return
	var objective := _make_arrow(true, OBJECTIVE_BODY, OBJECTIVE_TIP)
	var threat := _make_arrow(false, THREAT_BODY, THREAT_TIP)
	var objective_error := objective.save_png(output_dir.path_join("objective_arrow.png"))
	var threat_error := threat.save_png(output_dir.path_join("threat_arrow.png"))
	print("ASSET_GENERATION objective=%d threat=%d" % [objective_error, threat_error])
	quit(0 if objective_error == OK and threat_error == OK else 1)


func _make_arrow(points_right: bool, body_color: Color, tip_color: Color) -> Image:
	var image := Image.create(SIZE.x, SIZE.y, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	for y in SIZE.y:
		for x in SIZE.x:
			var canonical_x := x if points_right else SIZE.x - 1 - x
			var body := canonical_x >= 7 and canonical_x <= 39 and y >= 12 and y <= 19
			var head_half_width := maxi(0, int(round((55 - canonical_x) * 0.58)))
			var head := canonical_x >= 34 and canonical_x <= 55 and absf(float(y) - 15.5) <= head_half_width
			if body or head:
				var is_tip := canonical_x >= 47 and head
				image.set_pixel(x, y, tip_color if is_tip else body_color)
	return image


func _argument_value(key: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for index in args.size():
		if args[index] == key and index + 1 < args.size():
			return args[index + 1]
	return fallback
