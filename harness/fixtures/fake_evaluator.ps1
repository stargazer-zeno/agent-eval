[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Workspace,
    [Parameter(Mandatory = $true)][string]$ResultPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) { throw 'Evaluator workspace missing.' }
$changed = Test-Path -LiteralPath (Join-Path $Workspace 'agent_change.txt') -PathType Leaf
$parent = Split-Path -Parent $ResultPath
[void][System.IO.Directory]::CreateDirectory($parent)
$result = [ordered]@{
    evaluator = 'fixture-hidden-evaluator'
    passed = [bool]$changed
    score = if ($changed) { 1.0 } else { 0.0 }
}
[System.IO.File]::WriteAllText($ResultPath, (($result | ConvertTo-Json -Depth 5) + [Environment]::NewLine), $utf8NoBom)
if ($changed) { exit 0 }
exit 2
