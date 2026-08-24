extends SceneTree

func arg_value(name: String, fallback: String) -> String:
    var args := OS.get_cmdline_user_args()
    var index := args.find(name)
    return args[index + 1] if index >= 0 and index + 1 < args.size() else fallback

func frame(image: Image, rect: Rect2i, color: Color) -> void:
    image.fill_rect(Rect2i(rect.position, Vector2i(rect.size.x, 2)), color)
    image.fill_rect(Rect2i(rect.position + Vector2i(0, rect.size.y - 2), Vector2i(rect.size.x, 2)), color)
    image.fill_rect(Rect2i(rect.position, Vector2i(2, rect.size.y)), color)
    image.fill_rect(Rect2i(rect.position + Vector2i(rect.size.x - 2, 0), Vector2i(2, rect.size.y)), color)

func _init() -> void:
    var output := arg_value("--output", "mirrorstorm.png")
    var phase := arg_value("--phase", "CALM")
    var mask := int(arg_value("--fault-mask", "31"))
    var tick_rate := int(arg_value("--tick-rate", "60"))
    var direction := int(arg_value("--direction", "1"))
    var width := int(arg_value("--width", "960"))
    var height := int(arg_value("--height", "540"))
    var image := Image.create(width, height, false, Image.FORMAT_RGBA8)
    image.fill(Color("0d1624"))
    var margin := 20
    var gap := 10
    var panel_width := int((width - margin * 2 - gap * 3) / 4.0)
    var panel_height := int((height - margin * 2 - gap) / 2.0)
    var mirrored := phase == "MIRRORED_ENRAGED"
    var interrupted := phase == "INTERRUPTED_RESUME"
    for tick in range(8):
        var col := tick % 4
        var row := tick / 4
        var rect := Rect2i(margin + col * (panel_width + gap), margin + row * (panel_height + gap), panel_width, panel_height)
        image.fill_rect(rect, Color("142438"))
        frame(image, rect, Color("35516d"))
        var motion := direction * (-1 if tick >= 4 else 1)
        if mirrored: motion *= -1
        var boss := Vector2i(rect.get_center()) + Vector2i((tick % 4 - 2) * 10 * direction, 4 if mirrored else -4)
        image.fill_rect(Rect2i(boss - Vector2i(12, 12), Vector2i(24, 24)), Color("55c9ff"))
        var signed_offset := -motion * 30
        if (mask & 1) and tick in [3, 4]: signed_offset = motion * 30
        if (mask & 2) and tick in [4, 5]: signed_offset = motion * 22
        if mirrored and (mask & 4): signed_offset *= -1
        if (mask & 16) and interrupted and tick >= 5: signed_offset = 48
        var trail := boss + Vector2i(signed_offset, 0)
        image.fill_rect(Rect2i(trail - Vector2i(9, 9), Vector2i(18, 18)), Color("d47cff"))
        var tip_x := trail.x + (-motion * 14 if not ((mask & 2) and tick >= 4) else motion * 14)
        image.fill_rect(Rect2i(tip_x - 3, trail.y - 3, 6, 6), Color("fff2a8"))
        if (mask & 8) and interrupted and tick in [1, 6]:
            image.fill_rect(Rect2i(rect.position + Vector2i(16, 16), Vector2i(15, 15)), Color("d47cff"))
        image.fill_rect(Rect2i(rect.position + Vector2i(8, rect.size.y - 14), Vector2i(max(4, int((tick + 1) * panel_width / 10.0)), 4)), Color("51d6a8") if tick_rate == 60 else Color("f0a24a"))
    image.save_png(output)
    quit(0)
