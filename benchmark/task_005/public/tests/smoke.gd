extends SceneTree

func parse_route() -> Array[int]:
    var config := ConfigFile.new()
    if config.load("res://resources/route_bindings.cfg") != OK:
        return []
    var output: Array[int] = []
    var raw = config.get_value("bindings", "door_order", "")
    for value in str(raw).split(","):
        output.append(int(value))
    return output

func valid_permutation(values: Array[int]) -> bool:
    var copy := values.duplicate()
    copy.sort()
    return copy == [0, 1, 2, 3]

func _init() -> void:
    var migrator = load("res://scripts/save/slot_migrator.gd")
    var hints = load("res://scripts/hud/restore_hints.gd")
    var registry = load("res://scripts/seals/seal_registry.gd")
    var scene = load("res://scenes/main.tscn")
    var ok := migrator != null and hints != null and registry != null and scene != null
    ok = ok and valid_permutation(parse_route())
    for asset in registry.ASSETS:
        ok = ok and FileAccess.file_exists(asset)
    print("CHECKPOINT_MOSAIC_SMOKE:", "PASS" if ok else "FAIL")
    quit(0 if ok else 1)
