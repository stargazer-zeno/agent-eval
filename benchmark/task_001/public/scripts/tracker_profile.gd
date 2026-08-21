class_name TrackerProfile
extends Resource

@export var tracker_label: String = "Tracker"
@export var panel_color: Color = Color.WHITE
@export var icon: Texture2D
@export_range(-TAU, TAU, 0.001) var art_forward_offset: float = 0.0
