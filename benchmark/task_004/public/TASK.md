# Glyph Atlas — Multi-View Landmark Registration

The attached captures come from Glyph Atlas. Several minimap landmarks do not stay registered with their world landmarks across viewpoints. Repair the public Godot project so every minimap glyph preserves the correct landmark identity and spatial relationship under camera rotation, portal mirroring, and viewport changes.

The glyphs are intentionally unlabeled; the runtime images are the source of truth. Explore the repository through Controller actions, use the available public observation scenarios to disambiguate the defect, keep unrelated gameplay and assets unchanged, run the public smoke check, and inspect successful fresh post-patch observations before submitting. Do not hide markers, replace glyph art, disable camera/mirror behavior, move landmarks, or hardcode a scenario or resolution.

Public observation scenarios: `ROTATE_37`, `PORTAL_MIRROR`, `WIDE_VIEW`, `VERIFY_BASELINE`.
