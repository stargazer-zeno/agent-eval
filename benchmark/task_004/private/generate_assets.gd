extends SceneTree

const PATTERNS := [
    ["10101","01110","11011","00100","11101"], ["11001","00111","10100","01101","10011"],
    ["01101","11000","10111","00010","11100"], ["10011","01100","11101","00110","01001"],
    ["11100","00101","10010","01111","11001"], ["01011","11100","00111","10100","11010"],
    ["10110","01001","11110","00101","10011"], ["11010","00101","01110","10001","11100"],
]
const WORLD_NAMES := ["stone_a","stone_c","stone_f","stone_h","stone_k","stone_m","stone_q","stone_v"]
const MIN_NAMES := ["signal_b","signal_e","signal_g","signal_j","signal_n","signal_r","signal_t","signal_x"]
const MIN_PATTERN_ORDER := [3, 6, 1, 7, 0, 4, 2, 5]

func glyph(pattern: Array, foreground: Color, background: Color) -> Image:
    var image := Image.create(7, 7, false, Image.FORMAT_RGBA8)
    image.fill(background)
    for y in range(5):
        for x in range(5):
            if pattern[y][x] == "1": image.set_pixel(x + 1, y + 1, foreground)
    return image

func _init() -> void:
    var root := arg_value("--root", "res://../public")
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(root + "/assets/world"))
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(root + "/assets/minimap"))
    for index in range(8):
        glyph(PATTERNS[index], Color("67e8f9"), Color("172554")).save_png(ProjectSettings.globalize_path(root + "/assets/world/" + WORLD_NAMES[index] + ".png"))
        var pattern_index: int = MIN_PATTERN_ORDER[index]
        glyph(PATTERNS[pattern_index], Color("fde047"), Color("3f2208")).save_png(ProjectSettings.globalize_path(root + "/assets/minimap/" + MIN_NAMES[index] + ".png"))
    quit(0)

func arg_value(name: String, fallback: String) -> String:
    var args := OS.get_cmdline_user_args()
    var index := args.find(name)
    return args[index + 1] if index >= 0 and index + 1 < args.size() else fallback
