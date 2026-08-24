class_name MinimapProjection
extends RefCounted

func project(relative: Vector2, camera_angle: float, portal_mirrored: bool) -> Vector2:
    var transformed := relative
    if portal_mirrored:
        transformed.x = -transformed.x
    transformed = transformed.rotated(-camera_angle)
    return transformed
