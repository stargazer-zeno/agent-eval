extends SceneTree

const PATTERNS := [
    ["10101", "01110", "11011", "01110", "10101"],
    ["11100", "00110", "10101", "01100", "00111"],
    ["01010", "11111", "00100", "10101", "11011"],
    ["11001", "01011", "11100", "00110", "10011"],
]
const NAMES := ["mark_c", "mark_h", "mark_p", "mark_w"]

func _init() -> void:
    var root := arg_value("--root", "res://assets/seals")
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(root))
    for index in range(4):
        var image := Image.create(7, 7, false, Image.FORMAT_RGBA8)
        image.fill(Color("142235"))
        for y in range(5):
            for x in range(5):
                var color := Color("f2cc67") if PATTERNS[index][y][x] == "1" else Color("4f89b8")
                image.set_pixel(x + 1, y + 1, color)
        image.save_png(root.path_join(NAMES[index] + ".png"))
    quit(0)

func arg_value(name: String, fallback: String) -> String:
    var args := OS.get_cmdline_user_args()
    var index := args.find(name)
    return args[index + 1] if index >= 0 and index + 1 < args.size() else fallback
