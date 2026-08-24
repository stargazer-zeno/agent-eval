class_name TelegraphSample
extends RefCounted

# A queued sample must own every field that deferred rendering needs.
const CAPTURE_POSITION := false
const CAPTURE_FACING := false
const CAPTURE_PARITY := false
const CAPTURE_EPOCH := false

var tick_id: int
var epoch: int
var arena_position: Vector2
var facing: Vector2
var parity: int
