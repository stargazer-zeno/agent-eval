extends SceneTree

const Registry = preload("res://scripts/seals/seal_registry.gd")

func arg_value(name: String, fallback: String) -> String:
    var args := OS.get_cmdline_user_args()
    var index := args.find(name)
    return args[index + 1] if index >= 0 and index + 1 < args.size() else fallback

func parse_values(text: String) -> Array[int]:
    var output: Array[int] = []
    for value in text.split(","):
        output.append(int(value))
    return output

func stamp(target: Image, seal_index: int, center: Vector2i, scale: int) -> void:
    var seal := Image.load_from_file(Registry.ASSETS[seal_index])
    seal.resize(seal.get_width() * scale, seal.get_height() * scale, Image.INTERPOLATE_NEAREST)
    target.blit_rect(seal, Rect2i(Vector2i.ZERO, seal.get_size()), center - seal.get_size() / 2)

func frame(image: Image, rect: Rect2i, color: Color) -> void:
    image.fill_rect(Rect2i(rect.position, Vector2i(rect.size.x, 3)), color)
    image.fill_rect(Rect2i(rect.position + Vector2i(0, rect.size.y - 3), Vector2i(rect.size.x, 3)), color)
    image.fill_rect(Rect2i(rect.position, Vector2i(3, rect.size.y)), color)
    image.fill_rect(Rect2i(rect.position + Vector2i(rect.size.x - 3, 0), Vector2i(3, rect.size.y)), color)

func _init() -> void:
    var output := arg_value("--output", "checkpoint.png")
    var phase := arg_value("--phase", "LOBBY")
    var expected := parse_values(arg_value("--expected", "0,1,2,3"))
    var actual := parse_values(arg_value("--actual", "0,1,2,3"))
    var width := int(arg_value("--width", "960"))
    var height := int(arg_value("--height", "540"))
    var image := Image.create(width, height, false, Image.FORMAT_RGBA8)
    image.fill(Color("101827"))
    var panel := Rect2i(36, 36, width - 72, height - 72)
    frame(image, panel, Color("496682"))
    # Two image-only rows: cyan is the persisted/recorded identity, amber is current runtime output.
    for index in range(4):
        var x := int(width * (0.2 + index * 0.2))
        image.fill_rect(Rect2i(x - 62, 150, 124, 210), Color("17283a"))
        frame(image, Rect2i(x - 62, 150, 124, 210), Color("304c66"))
        stamp(image, expected[index], Vector2i(x, 118), 5)
        stamp(image, actual[index], Vector2i(x, 255), 5)
        var ok := expected[index] == actual[index]
        image.fill_rect(Rect2i(x - 44, 324, 88, 8), Color("51d6a8") if ok else Color("e85d75"))
    var phase_colors := {"LOBBY": Color("4aa3ff"), "RESTORED_MIDPOINT": Color("9e7bff"), "POST_ELEVATOR": Color("ffad4a"), "FINAL_RESTORE": Color("51d6a8")}
    image.fill_rect(Rect2i(60, 64, width - 120, 14), phase_colors.get(phase, Color.WHITE))
    # Encode phase without answer text: one lit cell per reached state.
    var phase_index := ["LOBBY", "RESTORED_MIDPOINT", "POST_ELEVATOR", "FINAL_RESTORE"].find(phase)
    for cell in range(4):
        image.fill_rect(Rect2i(72 + cell * 30, height - 92, 20, 20), Color("62d9bf") if cell <= phase_index else Color("26384b"))
    image.save_png(output)
    quit(0)
