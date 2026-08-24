extends SceneTree

func _init() -> void:
    var registry = load("res://scripts/minimap/landmark_registry.gd")
    var projection = load("res://scripts/minimap/projection.gd")
    var config := ConfigFile.new()
    var ok := registry != null and projection != null and config.load("res://resources/landmark_bindings.cfg") == OK
    if ok:
        var values := str(config.get_value("bindings", "minimap_order", "")).split(",")
        ok = values.size() == 8
        for value in values:
            ok = ok and int(value) >= 0 and int(value) < 8
    print("GLYPH_ATLAS_SMOKE:", "PASS" if ok else "FAIL")
    quit(0 if ok else 1)
