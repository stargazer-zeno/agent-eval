extends SceneTree

const Registry = preload("res://scripts/minimap/landmark_registry.gd")
const ProjectionScript = preload("res://scripts/minimap/projection.gd")

func arg_value(name: String, fallback: String) -> String:
    var args := OS.get_cmdline_user_args()
    var index := args.find(name)
    return args[index + 1] if index >= 0 and index + 1 < args.size() else fallback

func draw_frame(image: Image, rect: Rect2i, color: Color) -> void:
    image.fill_rect(Rect2i(rect.position, Vector2i(rect.size.x, 2)), color)
    image.fill_rect(Rect2i(rect.position + Vector2i(0, rect.size.y - 2), Vector2i(rect.size.x, 2)), color)
    image.fill_rect(Rect2i(rect.position, Vector2i(2, rect.size.y)), color)
    image.fill_rect(Rect2i(rect.position + Vector2i(rect.size.x - 2, 0), Vector2i(2, rect.size.y)), color)

func stamp(target: Image, source_path: String, center: Vector2i, scale: int) -> void:
    var glyph := Image.load_from_file(source_path)
    glyph.resize(glyph.get_width() * scale, glyph.get_height() * scale, Image.INTERPOLATE_NEAREST)
    target.blit_rect(glyph, Rect2i(Vector2i.ZERO, glyph.get_size()), center - glyph.get_size() / 2)

func parse_order() -> Array[int]:
    var config := ConfigFile.new()
    if config.load("res://resources/landmark_bindings.cfg") != OK:
        return []
    var output: Array[int] = []
    for value in str(config.get_value("bindings", "minimap_order", "")).split(","):
        output.append(int(value))
    return output

func scenario_values(scenario: String) -> Dictionary:
    if scenario == "ROTATE_37": return {"angle": deg_to_rad(37.0), "mirror": false, "width": 960, "height": 540}
    if scenario == "PORTAL_MIRROR": return {"angle": deg_to_rad(37.0), "mirror": true, "width": 960, "height": 540}
    if scenario == "WIDE_VIEW": return {"angle": deg_to_rad(-23.0), "mirror": false, "width": 1280, "height": 720}
    return {"angle": 0.0, "mirror": false, "width": 960, "height": 540}

func _init() -> void:
    var scenario := arg_value("--scenario", "VERIFY_BASELINE")
    var settings := scenario_values(scenario)
    if arg_value("--angle", "") != "": settings.angle = deg_to_rad(float(arg_value("--angle", "0")))
    if arg_value("--mirror", "") != "": settings.mirror = arg_value("--mirror", "false") == "true"
    if arg_value("--width", "") != "": settings.width = int(arg_value("--width", "960"))
    if arg_value("--height", "") != "": settings.height = int(arg_value("--height", "540"))
    var output := arg_value("--output", "glyph_atlas.png")
    var image := Image.create(settings.width, settings.height, false, Image.FORMAT_RGBA8)
    image.fill(Color("101827"))
    var world_rect := Rect2i(28, 28, int(settings.width * 0.64), settings.height - 56)
    var map_rect := Rect2i(int(settings.width * 0.69), 42, int(settings.width * 0.27), int(settings.height * 0.46))
    draw_frame(image, world_rect, Color("395675"))
    draw_frame(image, map_rect, Color("d0a93b"))
    var world_center := Vector2(world_rect.get_center())
    var map_center := Vector2(map_rect.get_center())
    image.fill_rect(Rect2i(Vector2i(world_center) - Vector2i(8, 8), Vector2i(16, 16)), Color("55c9ff"))
    var order := parse_order()
    var projected: Array = []
    for index in range(8):
        var world_position: Vector2 = world_center + Registry.LANDMARK_OFFSETS[index]
        stamp(image, Registry.WORLD_ASSETS[index], Vector2i(world_position), 4)
        var relative: Vector2 = ProjectionScript.new().project(Registry.LANDMARK_OFFSETS[index], settings.angle, settings.mirror)
        var map_position := map_center + relative * 0.28
        projected.append([map_position.x, map_position.y])
        if order.size() == 8:
            stamp(image, Registry.MINIMAP_ASSETS[order[index]], Vector2i(map_position), 3)
    image.save_png(output)
    var metadata := {"scenario": scenario, "angle": settings.angle, "mirror": settings.mirror, "width": settings.width, "height": settings.height, "order": order, "projected": projected, "landmark_offsets": Registry.LANDMARK_OFFSETS.map(func(v): return [v.x, v.y])}
    var file := FileAccess.open(output.get_basename() + ".json", FileAccess.WRITE)
    file.store_string(JSON.stringify(metadata))
    file.close()
    quit(0)
