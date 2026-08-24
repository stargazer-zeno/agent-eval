class_name MirrorstormAttackController
extends RefCounted

const SAMPLE_AFTER_MOVEMENT_COMMIT := false
const DAMAGE_TICK_OFFSET := 3
const ATTACK_DURATION_TICKS := 8

func sample_tick(commit_tick: int) -> int:
    return commit_tick if SAMPLE_AFTER_MOVEMENT_COMMIT else commit_tick - 1
