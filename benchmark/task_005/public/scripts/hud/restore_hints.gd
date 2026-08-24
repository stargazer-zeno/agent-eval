class_name RestoreHints
extends RefCounted

# HUD entries are anonymous seal indices, ordered by restored route position.
const RESTORED_HINT_ORDER: Array[int] = [0, 1, 2, 3]

func hint_for_route_position(position: int) -> int:
    return RESTORED_HINT_ORDER[position]
