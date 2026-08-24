class_name TelegraphRenderer
extends RefCounted

const READ_LIVE_ARENA_STATE := true
const TELEGRAPH_VISIBLE := true
const ALPHA := 1.0

func uses_queued_sample() -> bool:
    return not READ_LIVE_ARENA_STATE
