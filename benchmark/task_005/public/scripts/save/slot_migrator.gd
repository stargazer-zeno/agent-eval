class_name SlotMigrator
extends RefCounted

# v1 stored route positions; v2 stores anonymous checkpoint slots.
const V1_TO_V2: Array[int] = [0, 1, 2, 3]

func migrate_slot(v1_route_position: int) -> int:
    return V1_TO_V2[v1_route_position]
