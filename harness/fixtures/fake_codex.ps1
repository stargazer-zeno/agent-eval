[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('initial', 'resume')][string]$InvocationKind,
    [Parameter(Mandatory = $true)][int]$Attempt,
    [Parameter(Mandatory = $true)][int]$Turn,
    [Parameter(Mandatory = $true)][string]$Workspace,
    [Parameter(Mandatory = $true)][string]$Image,
    [Parameter(Mandatory = $true)][string]$ExpectedGodotVersion,
    [string]$ThreadId,
    [switch]$FailInfrastructure
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
[Console]::InputEncoding = $utf8NoBom

function Emit-Event {
    param($Value)
    [Console]::Out.WriteLine(($Value | ConvertTo-Json -Compress -Depth 20))
    [Console]::Out.Flush()
}

if ($FailInfrastructure) {
    [Console]::Error.WriteLine('fixture infrastructure failure before a usable model action')
    exit 70
}
if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) { throw 'Fixture workspace missing.' }
if (-not (Test-Path -LiteralPath $Image -PathType Leaf)) { throw 'Fixture image missing.' }
if ($InvocationKind -eq 'resume' -and -not $ThreadId) { throw 'Fixture resume requires explicit ThreadId.' }
if ($InvocationKind -eq 'initial' -and $ThreadId) { throw 'Fixture initial invocation must not receive ThreadId.' }

if (-not $ThreadId) {
    $ThreadId = '00000000-0000-0000-0000-' + $Attempt.ToString('000000000000')
}
$commandId = 'fixture-command-' + $Attempt + '-' + $Turn
$messageId = 'fixture-message-' + $Attempt + '-' + $Turn

Emit-Event ([pscustomobject]@{ type = 'thread.started'; thread_id = $ThreadId })
Emit-Event ([pscustomobject]@{ type = 'turn.started' })
Emit-Event ([pscustomobject]@{
    type = 'item.started'
    item = [pscustomobject]@{ id = $commandId; type = 'command_execution'; command = 'godot --version; fixture-edit'; status = 'in_progress' }
})

$changePath = Join-Path $Workspace 'agent_change.txt'
if ($Turn -eq 0) {
    $godotOutput = @(& godot --version 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "godot --version failed in fixture child PATH: $($godotOutput -join ' ')" }
    $godotVersion = ($godotOutput -join '').Trim()
    if ($godotVersion -ne $ExpectedGodotVersion) { throw "Fixture Godot version mismatch: $godotVersion" }
    [System.IO.File]::WriteAllText($changePath, "fixture attempt $Attempt turn $Turn godot=$godotVersion`r`n", $utf8NoBom)
}
else {
    [System.IO.File]::AppendAllText($changePath, "fixture attempt $Attempt turn $Turn`r`n", $utf8NoBom)
}

Emit-Event ([pscustomobject]@{
    type = 'item.completed'
    item = [pscustomobject]@{ id = $commandId; type = 'command_execution'; command = 'godot --version; fixture-edit'; status = 'completed'; exit_code = 0 }
})

if ($Turn -eq 0) {
    $action = [ordered]@{ action = 'observe'; summary = 'Fixture edit complete; request one fresh render.' }
}
else {
    $action = [ordered]@{ action = 'submit'; summary = 'Fixture visual loop complete.' }
}
Emit-Event ([pscustomobject]@{
    type = 'item.completed'
    item = [pscustomobject]@{ id = $messageId; type = 'agent_message'; text = ($action | ConvertTo-Json -Compress) }
})
Emit-Event ([pscustomobject]@{
    type = 'turn.completed'
    usage = [pscustomobject]@{ input_tokens = 10; cached_input_tokens = 0; output_tokens = 5 }
})
exit 0
