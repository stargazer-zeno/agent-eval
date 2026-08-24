extends SceneTree

func _init() -> void:
    var attack = load("res://scripts/combat/attack_controller.gd")
    var sample = load("res://scripts/combat/telegraph_sample.gd")
    var renderer = load("res://scripts/render/telegraph_renderer.gd")
    var pool = load("res://scripts/render/telegraph_pool.gd")
    var scene = load("res://scenes/main.tscn")
    var ok := attack != null and sample != null and renderer != null and pool != null and scene != null
    ok = ok and attack.DAMAGE_TICK_OFFSET == 3 and attack.ATTACK_DURATION_TICKS == 8
    ok = ok and renderer.TELEGRAPH_VISIBLE and renderer.ALPHA >= 0.95
    ok = ok and pool.MAX_POOL_SIZE == 12 and pool.LIFETIME_TICKS == 3
    print("MIRRORSTORM_SMOKE:", "PASS" if ok else "FAIL")
    quit(0 if ok else 1)
