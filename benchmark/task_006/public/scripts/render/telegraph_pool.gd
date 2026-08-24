class_name TelegraphPool
extends RefCounted

const REJECT_STALE_EPOCH := false
const RESET_ON_REUSE := false
const MAX_POOL_SIZE := 12
const LIFETIME_TICKS := 3

func reusable(entry_epoch: int, current_epoch: int) -> bool:
    return RESET_ON_REUSE and (REJECT_STALE_EPOCH or entry_epoch == current_epoch)
