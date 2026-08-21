[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$EvaluatorScript,
    [Parameter(Mandatory = $true)][string]$SubmissionWorkspace,
    [Parameter(Mandatory = $true)][string]$EvaluationRoot,
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$harnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $harnessRoot 'Harness.Core.psm1') -Force -DisableNameChecking

if ($TimeoutSeconds -lt 1 -or $TimeoutSeconds -gt 180) { throw 'TimeoutSeconds must be in [1,180].' }
$source = Get-FullPathSafe $SubmissionWorkspace
$root = Get-FullPathSafe $EvaluationRoot
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw "Submission workspace not found: $source" }
if (Test-Path -LiteralPath $root) {
    if (@(Get-ChildItem -LiteralPath $root -Force).Count -ne 0) { throw "EvaluationRoot must be empty: $root" }
}
[void](Ensure-Directory $root)
$private = Ensure-Directory (Join-Path $root 'private_tools')
$workspace = Ensure-Directory (Join-Path $root 'workspace')
$resultDirectory = Ensure-Directory (Join-Path $root 'result')
$receipts = Ensure-Directory (Join-Path $root 'receipts')

# This entry point must be launched only after the Agent/Codex process has stopped.
$adapter = Copy-PrivateAdapter -SourceScript $EvaluatorScript -PrivateDirectory $private -Role evaluator
[void](Copy-SanitizedTree -Source $source -Destination $workspace -ReceiptPath (Join-Path $receipts 'evaluation-copy.json'))
$resultPath = Join-Path $resultDirectory 'result.json'
$evaluation = Invoke-EvaluatorAdapter -AdapterScript $adapter.private_path -Workspace $workspace -ResultPath $resultPath -TimeoutSeconds $TimeoutSeconds
$publicReceipt = [pscustomobject]@{
    evaluator_sha256 = $adapter.sha256
    evaluator_archivable = $false
    workspace_manifest = @(Get-TreeManifest $workspace)
    success = $evaluation.success
    exit_code = $evaluation.exit_code
    timed_out = $evaluation.timed_out
    result_sha256 = $evaluation.result_sha256
}
Write-JsonFile -Path (Join-Path $receipts 'evaluation.json') -Value $publicReceipt
$findings = @(Find-CredentialIndicators -Root $root -ExcludedRoots @($private))
Write-JsonFile -Path (Join-Path $receipts 'credential-scan.json') -Value ([pscustomobject]@{ findings = $findings })
if ($findings.Count -gt 0) { throw 'Credential indicator detected in evaluator artifacts.' }
$publicReceipt | ConvertTo-Json -Depth 20
if ($evaluation.success) { exit 0 }
exit 40
