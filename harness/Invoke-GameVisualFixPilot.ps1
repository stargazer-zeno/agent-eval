[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [ValidateSet('Preflight', 'Fixture', 'ExecuteModel')][string]$Mode = 'Preflight',
    [switch]$ConfirmModelExecution,
    [switch]$FixtureFailFirstInfrastructure
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$harnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $harnessRoot 'Harness.Core.psm1') -Force -DisableNameChecking
$schemaPath = Join-Path $harnessRoot 'action.schema.json'

function Require-ConfigValue {
    param($Config, [string]$Name)
    $value = Get-OptionalProperty -Object $Config -Name $Name -Default $null
    if ($null -eq $value -or ([string]$value).Trim() -eq '') { throw "Missing required config value: $Name" }
    return $value
}

function Add-HarnessEvent {
    param(
        [string]$Path,
        [string]$RunId,
        [int]$Attempt,
        [int]$Turn,
        [string]$Type,
        $Data
    )
    [void](Add-TrajectoryEvent -Path $Path -Event ([pscustomobject]@{
        sequence = 'h-' + [guid]::NewGuid().ToString('N')
        captured_at_utc = [DateTime]::UtcNow.ToString('o')
        run_id = $RunId
        attempt = $Attempt
        turn = $Turn
        source = 'harness'
        payload = [pscustomobject]@{ type = $Type; data = $Data }
    }))
}

function Get-PublicToolReceipt {
    param($PrivateReceipt)
    return [pscustomobject]@{
        role = $PrivateReceipt.role
        sha256 = $PrivateReceipt.sha256
        archive_allowed = $false
    }
}

function Get-ProductionCodexInvocation {
    param(
        $Config,
        [string]$Workspace,
        [string]$RunCodexHome,
        [string]$PublicToolDirectory,
        [int]$Turn,
        [string]$ThreadId,
        [string]$Image,
        [string]$Prompt
    )
    $childEnvironment = New-MinimalChildEnvironment -CodexHome $RunCodexHome -PublicToolDirectory $PublicToolDirectory
    $shellPath = [string]$childEnvironment['PATH']
    if ($shellPath.Contains("'")) { throw 'Minimal child PATH cannot be encoded as a TOML literal string.' }
    $common = @(
        '-a', 'never',
        '-s', 'workspace-write',
        '-C', $Workspace,
        '-m', [string]$Config.model,
        '-c', 'model_reasoning_effort="ultra"',
        '-c', 'sandbox_workspace_write.network_access=false',
        '-c', 'shell_environment_policy.inherit="none"',
        '-c', ("shell_environment_policy.set.PATH='" + $shellPath + "'"),
        '-c', 'shell_environment_policy.ignore_default_excludes=false',
        '-c', 'tools.web_search=false',
        '-c', 'allow_login_shell=false',
        '-c', 'cli_auth_credentials_store="file"',
        '--disable', 'multi_agent',
        '--disable', 'plugins',
        '--disable', 'apps',
        '--disable', 'browser_use',
        '--disable', 'computer_use',
        '--disable', 'skill_mcp_dependency_install'
    )
    if ($Turn -eq 0) {
        $arguments = $common + @(
            'exec', '--ignore-user-config', '--ignore-rules', '--strict-config', '--json', '--color', 'never',
            '--image', $Image, '--output-schema', $schemaPath, $Prompt
        )
    }
    else {
        if (-not $ThreadId) { throw 'Explicit thread UUID is required for resume.' }
        $arguments = $common + @(
            'exec', 'resume', '--ignore-user-config', '--ignore-rules', '--strict-config', '--json',
            '--image', $Image, '--output-schema', $schemaPath, $ThreadId, $Prompt
        )
    }
    if (($arguments -contains '--last') -or ($arguments -contains '--ephemeral')) {
        throw 'Forbidden Codex session flag was generated.'
    }
    return [pscustomobject]@{
        file_path = [string]$Config.codex_exe
        arguments = @($arguments)
        environment = $childEnvironment
        clear_environment = $true
    }
}

function Get-FixtureCodexInvocation {
    param(
        [int]$Attempt,
        [int]$Turn,
        [string]$Workspace,
        [string]$ThreadId,
        [string]$Image,
        [string]$RunCodexHome,
        [string]$PublicToolDirectory,
        [string]$ExpectedGodotVersion,
        [bool]$FailFirst
    )
    $powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $fixture = Join-Path $harnessRoot 'fixtures\fake_codex.ps1'
    $kind = if ($Turn -eq 0) { 'initial' } else { 'resume' }
    $arguments = @(
        '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $fixture,
        '-InvocationKind', $kind, '-Attempt', [string]$Attempt, '-Turn', [string]$Turn,
        '-Workspace', $Workspace, '-Image', $Image, '-ExpectedGodotVersion', $ExpectedGodotVersion
    )
    if ($ThreadId) { $arguments += @('-ThreadId', $ThreadId) }
    if ($FailFirst -and $Attempt -eq 1 -and $Turn -eq 0) { $arguments += '-FailInfrastructure' }
    return [pscustomobject]@{
        file_path = $powershell
        arguments = @($arguments)
        environment = New-MinimalChildEnvironment -CodexHome $RunCodexHome -PublicToolDirectory $PublicToolDirectory
        clear_environment = $true
    }
}

function Complete-AttemptAudit {
    param(
        [string]$RunRoot,
        [string]$AttemptRoot,
        [string]$AttemptId,
        [string]$Workspace,
        [string]$PrivateRoot,
        [string]$CodexHome,
        [string]$Receipts,
        [string]$Classification,
        [string]$Outcome,
        [int]$Attempt
    )
    $finalManifest = @(Get-TreeManifest $Workspace)
    Write-JsonFile -Path (Join-Path $Receipts 'final-workspace-manifest.json') -Value $finalManifest
    $status = Invoke-GitChecked -Workspace $Workspace -Arguments @('status', '--porcelain=v1')
    $diff = Invoke-GitChecked -Workspace $Workspace -Arguments @('diff', '--binary', '--no-ext-diff', 'HEAD', '--')
    Write-Utf8NoBomText -Path (Join-Path $AttemptRoot 'submission.patch') -Text ($diff + $(if ($diff) { [Environment]::NewLine } else { '' }))
    Write-Utf8NoBomText -Path (Join-Path $AttemptRoot 'git-status.txt') -Text ($status + $(if ($status) { [Environment]::NewLine } else { '' }))

    $findings = @(Find-CredentialIndicators -Root $AttemptRoot -ExcludedRoots @($PrivateRoot, $CodexHome))
    Write-JsonFile -Path (Join-Path $Receipts 'credential-scan.json') -Value ([pscustomobject]@{
        scanned_at_utc = [DateTime]::UtcNow.ToString('o')
        excluded_private_roots = @('control/codex_home', 'control/private_tools')
        findings = $findings
    })
    if ($findings.Count -gt 0) {
        return [pscustomobject]@{
            classification = 'security_invalid'
            outcome = 'credential_indicator_detected'
            archive_path = $null
            archive_manifest = @()
            git_status = $status
        }
    }

    $archive = Join-Path $RunRoot ('archive\attempt-' + $Attempt)
    $archiveManifest = @(New-SafeArchiveCopy -AttemptRoot $AttemptRoot -ArchiveRoot $archive)
    $archiveFindings = @(Find-CredentialIndicators -Root $archive)
    if ($archiveFindings.Count -gt 0) { throw 'Credential indicator appeared in archive after clean pre-scan.' }
    if (@(Get-ChildItem -LiteralPath $archive -Filter 'auth.json' -File -Recurse -Force).Count -ne 0) {
        throw 'Archive invariant failed: auth.json was copied.'
    }
    if (Test-Path -LiteralPath (Join-Path $archive 'control\private_tools')) {
        throw 'Archive invariant failed: private tools were copied.'
    }
    Write-JsonFile -Path (Join-Path $RunRoot ('archive-manifest-attempt-' + $Attempt + '.json')) -Value $archiveManifest
    return [pscustomobject]@{
        classification = $Classification
        outcome = $Outcome
        archive_path = $archive
        archive_manifest = $archiveManifest
        git_status = $status
    }
}

function Invoke-OneAttempt {
    param(
        $Config,
        [string]$RunRoot,
        [string]$RunId,
        [int]$Attempt,
        [string]$Mode,
        [bool]$FailFirst
    )

    $attemptRoot = Ensure-Directory (Join-Path $RunRoot ('attempt-' + $Attempt))
    $workspace = Ensure-Directory (Join-Path $attemptRoot 'workspace')
    $control = Ensure-Directory (Join-Path $attemptRoot 'control')
    $privateRoot = Ensure-Directory (Join-Path $control 'private_tools')
    $codexHome = Join-Path $control 'codex_home'
    $raw = Ensure-Directory (Join-Path $attemptRoot 'raw')
    $normalized = Ensure-Directory (Join-Path $attemptRoot 'normalized')
    $receipts = Ensure-Directory (Join-Path $attemptRoot 'receipts')
    $observations = Ensure-Directory (Join-Path $attemptRoot 'observations')
    $publicTools = Ensure-Directory (Join-Path $attemptRoot 'public_tools')
    $trajectory = Join-Path $normalized 'trajectory.jsonl'
    Write-Utf8NoBomText -Path $trajectory -Text ''

    $classification = 'completed'
    $outcome = 'unknown'
    $turnsUsed = 0
    $imageAttachments = 1
    $freshImagesUsed = 0
    $commandsUsed = 0
    $codexWallUsed = 0.0
    $inputTokensUsed = [int64]0
    $outputTokensUsed = [int64]0
    $threadId = $null
    $attemptStart = [DateTime]::UtcNow

    try {
        Add-HarnessEvent -Path $trajectory -RunId $RunId -Attempt $Attempt -Turn -1 -Type 'attempt.started' -Data ([pscustomobject]@{})
        [void](Copy-SanitizedTree -Source ([string]$Config.seed_path) -Destination $workspace -ReceiptPath (Join-Path $receipts 'sanitization.json'))
        $baselineManifest = @(Get-TreeManifest $workspace)
        Write-JsonFile -Path (Join-Path $receipts 'baseline-workspace-manifest.json') -Value $baselineManifest
        $gitReceipt = Initialize-SingleCommitWorkspace $workspace
        Write-JsonFile -Path (Join-Path $receipts 'baseline-git.json') -Value $gitReceipt
        $authReceipt = Initialize-RunCodexHome -SourceCodexHome ([string]$Config.source_codex_home) -RunCodexHome $codexHome
        Write-JsonFile -Path (Join-Path $receipts 'codex-home-policy.json') -Value $authReceipt
        $godotCommandReceipt = Initialize-PublicGodotCommand -GodotExe ([string]$Config.godot_exe) -PublicToolDirectory $publicTools
        Write-JsonFile -Path (Join-Path $receipts 'public-godot-command.json') -Value $godotCommandReceipt

        $initialImage = Get-FullPathSafe ([string]$Config.initial_image)
        Write-JsonFile -Path (Join-Path $receipts 'public-inputs.json') -Value ([pscustomobject]@{
            prompt_sha256 = Get-Sha256 ([string]$Config.prompt_path)
            initial_image_sha256 = Get-Sha256 $initialImage
            initial_image_counts_toward_limit = $true
        })

        $rendererPrivate = Copy-PrivateAdapter -SourceScript ([string]$Config.renderer_script) -PrivateDirectory $privateRoot -Role renderer
        Write-JsonFile -Path (Join-Path $receipts 'renderer-adapter.json') -Value (Get-PublicToolReceipt $rendererPrivate)

        $publicPrompt = [System.IO.File]::ReadAllText((Get-FullPathSafe ([string]$Config.prompt_path)), [System.Text.Encoding]::UTF8)
        $protocolPrompt = @'


Harness protocol: Work only in the current workspace. Return exactly one JSON object matching the supplied schema. Use action "observe" only when a fresh rendered screenshot is necessary to continue; use "submit" when the patch is ready. Never search for hidden tests, an evaluator, an oracle, credentials, or files outside this workspace.
'@
        $nextPrompt = $publicPrompt + $protocolPrompt
        $nextImage = $initialImage
        $maxTurns = [int]$Config.budgets.max_turns
        $maxFreshImages = [int]$Config.budgets.max_fresh_images
        $maxCommands = [int]$Config.budgets.max_commands
        $maxWall = [int]$Config.budgets.max_codex_wall_seconds
        $maxRun = [int]$Config.budgets.max_run_seconds

        for ($turn = 0; $turn -lt $maxTurns; $turn++) {
            $runElapsed = [int][Math]::Floor(([DateTime]::UtcNow - $attemptStart).TotalSeconds)
            $remainingRun = $maxRun - $runElapsed
            $remainingWall = $maxWall - [int][Math]::Ceiling($codexWallUsed)
            if ($remainingRun -le 0) { $outcome = 'full_run_budget_exhausted'; break }
            if ($remainingWall -le 0) { $outcome = 'codex_wall_budget_exhausted'; break }
            if ($commandsUsed -ge $maxCommands) { $outcome = 'command_budget_exhausted'; break }

            if ($Mode -eq 'Fixture') {
                $invocation = Get-FixtureCodexInvocation -Attempt $Attempt -Turn $turn -Workspace $workspace -ThreadId $threadId -Image $nextImage -RunCodexHome $codexHome -PublicToolDirectory $publicTools -ExpectedGodotVersion ([string]$Config.expected_godot_version) -FailFirst $FailFirst
            }
            else {
                $invocation = Get-ProductionCodexInvocation -Config $Config -Workspace $workspace -RunCodexHome $codexHome -PublicToolDirectory $publicTools -Turn $turn -ThreadId $threadId -Image $nextImage -Prompt $nextPrompt
            }
            $auditArguments = @($invocation.arguments)
            if ($Mode -ne 'Fixture' -and $auditArguments.Count -gt 0) {
                $auditArguments[$auditArguments.Count - 1] = '<PROMPT REDACTED; see public-inputs receipt>'
            }
            Write-JsonFile -Path (Join-Path $receipts ('invocation-turn-' + $turn + '.json')) -Value ([pscustomobject]@{
                mode = $Mode
                executable_sha256 = Get-Sha256 $invocation.file_path
                arguments = $auditArguments
                environment_keys = @($invocation.environment.Keys | Sort-Object)
                prompt_inline_redacted = $true
            })
            Add-HarnessEvent -Path $trajectory -RunId $RunId -Attempt $Attempt -Turn $turn -Type 'turn.started' -Data ([pscustomobject]@{ image_sha256 = Get-Sha256 $nextImage })

            $perTurnCap = if ($turn -eq 0) { 600 } else { 300 }
            $turnTimeout = [Math]::Min($remainingRun, [Math]::Min($remainingWall, $perTurnCap))
            $turnResult = Invoke-JsonlProcess -FilePath $invocation.file_path -Arguments $invocation.arguments `
                -WorkingDirectory $workspace -RawStdoutPath (Join-Path $raw ('codex-turn-' + $turn + '.stdout.jsonl')) `
                -RawStderrPath (Join-Path $raw ('codex-turn-' + $turn + '.stderr.log')) -NormalizedPath $trajectory `
                -RunId $RunId -Attempt $Attempt -Turn $turn -TimeoutSeconds $turnTimeout `
                -RemainingCommandBudget ($maxCommands - $commandsUsed) -Environment $invocation.environment `
                -ClearEnvironment:$invocation.clear_environment
            $turnsUsed++
            $commandsUsed += [int]$turnResult.command_count
            $codexWallUsed += [double]$turnResult.duration_seconds
            $inputTokensUsed += [int64]$turnResult.input_tokens
            $outputTokensUsed += [int64]$turnResult.output_tokens
            Add-HarnessEvent -Path $trajectory -RunId $RunId -Attempt $Attempt -Turn $turn -Type 'turn.finished' -Data ([pscustomobject]@{
                exit_code = $turnResult.exit_code; stop_reason = $turnResult.stop_reason; commands = $turnResult.command_count
            })

            if (-not $turnResult.started -or $turnResult.stop_reason -eq 'process_launch' -or
                $turnResult.stop_reason -eq 'nonzero_exit' -or $turnResult.stop_reason -eq 'malformed_jsonl') {
                $classification = 'infrastructure_invalid'
                $outcome = [string]$turnResult.stop_reason
                break
            }
            if ($turnResult.stop_reason -eq 'wall_timeout') { $outcome = 'codex_wall_budget_exhausted'; break }
            if ($turnResult.stop_reason -eq 'command_budget') { $outcome = 'command_budget_exhausted'; break }
            if ($inputTokensUsed -gt [int64]$Config.budgets.max_input_tokens -or
                $outputTokensUsed -gt [int64]$Config.budgets.max_output_tokens) {
                $outcome = 'token_telemetry_gate_exceeded'
                break
            }
            if ($turn -eq 0) {
                if (-not $turnResult.thread_id) {
                    $classification = 'infrastructure_invalid'; $outcome = 'missing_thread_id'; break
                }
                $threadId = [string]$turnResult.thread_id
            }
            elseif ($turnResult.thread_id -and $turnResult.thread_id -ne $threadId) {
                $classification = 'infrastructure_invalid'; $outcome = 'thread_id_changed'; break
            }
            if ($null -eq $turnResult.action) {
                $classification = 'model_invalid'; $outcome = 'missing_or_invalid_action'; break
            }
            $actionName = [string]$turnResult.action.action
            if ($actionName -eq 'submit') { $outcome = 'submitted'; break }
            if ($turn -ge ($maxTurns - 1)) { $outcome = 'turn_budget_exhausted'; break }
            if ($freshImagesUsed -ge $maxFreshImages) { $outcome = 'image_budget_exhausted'; break }

            $snapshot = Ensure-Directory (Join-Path $attemptRoot ('render\turn-' + $turn + '\workspace'))
            [void](Copy-SanitizedTree -Source $workspace -Destination $snapshot)
            $freshImage = Join-Path $observations ('fresh-after-turn-' + $turn + '.png')
            $rendererReceiptPath = Join-Path $receipts ('renderer-turn-' + $turn + '-native.json')
            $renderRemaining = $maxRun - [int][Math]::Floor(([DateTime]::UtcNow - $attemptStart).TotalSeconds)
            if ($renderRemaining -le 0) { $outcome = 'full_run_budget_exhausted'; break }
            $renderResult = Invoke-RendererAdapter -AdapterScript $rendererPrivate.private_path -Workspace $snapshot `
                -OutputImage $freshImage -ReceiptPath $rendererReceiptPath -TimeoutSeconds ([Math]::Min([int]$Config.budgets.capture_timeout_seconds, $renderRemaining))
            Write-JsonFile -Path (Join-Path $receipts ('renderer-turn-' + $turn + '.json')) -Value ([pscustomobject]@{
                adapter_sha256 = $rendererPrivate.sha256
                snapshot_manifest = @(Get-TreeManifest $snapshot)
                success = $renderResult.success
                failure_class = $renderResult.failure_class
                exit_code = $renderResult.exit_code
                timed_out = $renderResult.timed_out
                image_sha256 = $renderResult.image_sha256
            })
            Add-HarnessEvent -Path $trajectory -RunId $RunId -Attempt $Attempt -Turn $turn -Type 'render.finished' -Data ([pscustomobject]@{
                success = $renderResult.success; failure_class = $renderResult.failure_class; image_sha256 = $renderResult.image_sha256
            })
            if (-not $renderResult.success) {
                if ($renderResult.failure_class -eq 'submission') {
                    $classification = 'model_invalid'; $outcome = 'submission_render_failure'
                }
                else {
                    $classification = 'infrastructure_invalid'; $outcome = 'renderer_infrastructure_failure'
                }
                break
            }
            $freshImagesUsed++
            $imageAttachments++
            $nextImage = $freshImage
            $nextPrompt = 'A fresh screenshot rendered from your current workspace is attached. Continue from the same session. Return exactly one schema-valid observe or submit action.'
        }

        if ($outcome -eq 'unknown') { $outcome = 'turn_budget_exhausted' }

        if ($classification -ne 'infrastructure_invalid') {
            # Hidden evaluator enters the run only after every Codex process has stopped.
            $evaluatorPrivate = Copy-PrivateAdapter -SourceScript ([string]$Config.evaluator_script) -PrivateDirectory $privateRoot -Role evaluator
            Write-JsonFile -Path (Join-Path $receipts 'evaluator-adapter.json') -Value (Get-PublicToolReceipt $evaluatorPrivate)
            $evaluationWorkspace = Ensure-Directory (Join-Path $attemptRoot 'evaluation\workspace')
            [void](Copy-SanitizedTree -Source $workspace -Destination $evaluationWorkspace)
            $resultDirectory = Ensure-Directory (Join-Path $attemptRoot 'evaluation\result')
            $resultPath = Join-Path $resultDirectory 'result.json'
            $evaluatorRemaining = $maxRun - [int][Math]::Floor(([DateTime]::UtcNow - $attemptStart).TotalSeconds)
            if ($evaluatorRemaining -le 0) { throw 'Full run deadline reached before hidden evaluator.' }
            $evaluation = Invoke-EvaluatorAdapter -AdapterScript $evaluatorPrivate.private_path -Workspace $evaluationWorkspace -ResultPath $resultPath `
                -TimeoutSeconds ([Math]::Min([int]$Config.budgets.evaluator_timeout_seconds, $evaluatorRemaining))
            Write-JsonFile -Path (Join-Path $receipts 'evaluation.json') -Value ([pscustomobject]@{
                adapter_sha256 = $evaluatorPrivate.sha256
                workspace_manifest = @(Get-TreeManifest $evaluationWorkspace)
                success = $evaluation.success
                exit_code = $evaluation.exit_code
                timed_out = $evaluation.timed_out
                result_sha256 = $evaluation.result_sha256
            })
            if (-not $evaluation.success) {
                $classification = 'infrastructure_invalid'
                $outcome = 'evaluator_infrastructure_failure'
            }
        }
    }
    catch {
        $classification = 'infrastructure_invalid'
        $outcome = 'controller_exception'
        Write-Utf8NoBomText -Path (Join-Path $raw 'controller-error.log') -Text ($_.Exception.ToString() + [Environment]::NewLine)
    }

    Write-JsonFile -Path (Join-Path $receipts 'budget.json') -Value ([pscustomobject]@{
        turns_used = $turnsUsed
        initial_images = 1
        fresh_images = $freshImagesUsed
        image_attachments = $imageAttachments
        commands_observed = $commandsUsed
        input_tokens_observed = $inputTokensUsed
        output_tokens_observed = $outputTokensUsed
        codex_wall_seconds = [Math]::Round($codexWallUsed, 3)
        full_run_wall_seconds = [Math]::Round(([DateTime]::UtcNow - $attemptStart).TotalSeconds, 3)
        limits = $Config.budgets
    })
    Add-HarnessEvent -Path $trajectory -RunId $RunId -Attempt $Attempt -Turn $turnsUsed -Type 'attempt.finished' -Data ([pscustomobject]@{
        classification = $classification; outcome = $outcome
    })
    $chainReceipt = Test-TrajectoryHashChain $trajectory
    Write-JsonFile -Path (Join-Path $receipts 'trajectory-chain.json') -Value $chainReceipt
    if (-not $chainReceipt.valid) {
        $classification = 'infrastructure_invalid'
        $outcome = 'trajectory_hash_chain_invalid'
    }
    $audit = Complete-AttemptAudit -RunRoot $RunRoot -AttemptRoot $attemptRoot -AttemptId ('attempt-' + $Attempt) `
        -Workspace $workspace -PrivateRoot $privateRoot -CodexHome $codexHome -Receipts $receipts `
        -Classification $classification -Outcome $outcome -Attempt $Attempt
    return [pscustomobject]@{
        attempt = $Attempt
        classification = $audit.classification
        outcome = $audit.outcome
        turns_used = $turnsUsed
        initial_images = 1
        fresh_images = $freshImagesUsed
        image_attachments = $imageAttachments
        commands_observed = $commandsUsed
        input_tokens_observed = $inputTokensUsed
        output_tokens_observed = $outputTokensUsed
        thread_id = $threadId
        attempt_root = $attemptRoot
        archive_path = $audit.archive_path
    }
}

$configFull = Get-FullPathSafe $ConfigPath
if (-not (Test-Path -LiteralPath $configFull -PathType Leaf)) { throw "Config not found: $configFull" }
$config = [System.IO.File]::ReadAllText($configFull, [System.Text.Encoding]::UTF8) | ConvertFrom-Json -ErrorAction Stop
foreach ($name in @('seed_path', 'initial_image', 'prompt_path', 'model', 'reasoning_effort', 'codex_exe', 'expected_codex_version',
        'expected_codex_sha256', 'godot_exe', 'expected_godot_version', 'expected_godot_sha256', 'godot_companion_exe',
        'expected_godot_companion_sha256', 'source_codex_home', 'renderer_script', 'evaluator_script', 'output_root', 'budgets')) {
    [void](Require-ConfigValue -Config $config -Name $name)
}
foreach ($pathName in @('seed_path', 'source_codex_home')) {
    $candidate = [string](Get-OptionalProperty -Object $config -Name $pathName)
    if (-not (Test-Path -LiteralPath (Get-FullPathSafe $candidate) -PathType Container)) { throw "Configured directory does not exist ($pathName): $candidate" }
}
foreach ($pathName in @('initial_image', 'prompt_path', 'codex_exe', 'godot_exe', 'godot_companion_exe', 'renderer_script', 'evaluator_script')) {
    $candidate = [string](Get-OptionalProperty -Object $config -Name $pathName)
    if (-not (Test-Path -LiteralPath (Get-FullPathSafe $candidate) -PathType Leaf)) { throw "Configured file does not exist ($pathName): $candidate" }
}
if (-not (Test-Path -LiteralPath $schemaPath -PathType Leaf)) { throw 'Action schema is missing.' }
[void]([System.IO.File]::ReadAllText($schemaPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json -ErrorAction Stop)
if ([string]$config.reasoning_effort -ne 'ultra') { throw 'reasoning_effort is frozen to ultra for this pilot.' }

$budgets = $config.budgets
if ([int]$budgets.max_turns -lt 1 -or [int]$budgets.max_turns -gt 4) { throw 'max_turns must be in [1,4].' }
if ([int]$budgets.max_fresh_images -lt 0 -or [int]$budgets.max_fresh_images -gt 3) { throw 'max_fresh_images must be in [0,3]; initial image is separate.' }
if ([int]$budgets.max_codex_wall_seconds -lt 1 -or [int]$budgets.max_codex_wall_seconds -gt 1500) { throw 'max_codex_wall_seconds must be in [1,1500].' }
if ([int]$budgets.max_run_seconds -lt [int]$budgets.max_codex_wall_seconds -or [int]$budgets.max_run_seconds -gt 2100) { throw 'max_run_seconds must cover Codex time and be at most 2100.' }
if ([int]$budgets.max_commands -lt 1 -or [int]$budgets.max_commands -gt 60) { throw 'max_commands must be in [1,60].' }
if ([int64]$budgets.max_input_tokens -lt 1 -or [int64]$budgets.max_input_tokens -gt 150000) { throw 'max_input_tokens must be in [1,150000].' }
if ([int64]$budgets.max_output_tokens -lt 1 -or [int64]$budgets.max_output_tokens -gt 20000) { throw 'max_output_tokens must be in [1,20000].' }
if ([int]$budgets.capture_timeout_seconds -lt 1 -or [int]$budgets.capture_timeout_seconds -gt 90) { throw 'capture_timeout_seconds must be in [1,90].' }
if ([int]$budgets.evaluator_timeout_seconds -lt 1 -or [int]$budgets.evaluator_timeout_seconds -gt 180) { throw 'evaluator_timeout_seconds must be in [1,180].' }

$nativeReceipt = Assert-NativeCodexBinary -CodexExe ([string]$config.codex_exe) `
    -ExpectedVersion ([string]$config.expected_codex_version) -ExpectedSha256 ([string]$config.expected_codex_sha256)
$godotReceipt = Assert-GodotRuntime -GodotExe ([string]$config.godot_exe) -ExpectedVersion ([string]$config.expected_godot_version) `
    -ExpectedSha256 ([string]$config.expected_godot_sha256) -CompanionExe ([string]$config.godot_companion_exe) `
    -ExpectedCompanionSha256 ([string]$config.expected_godot_companion_sha256)

if ($Mode -eq 'ExecuteModel' -and -not $ConfirmModelExecution) {
    throw 'ExecuteModel is blocked unless -ConfirmModelExecution is supplied explicitly.'
}

if ($Mode -eq 'Preflight') {
    [pscustomobject]@{
        mode = 'Preflight'
        model_called = $false
        native_codex = $nativeReceipt
        godot_runtime = $godotReceipt
        model = [string]$config.model
        reasoning_effort = [string]$config.reasoning_effort
        service_tier = '<default; no override>'
        schema_sha256 = Get-Sha256 $schemaPath
        production_canary_required = $true
    } | ConvertTo-Json -Depth 10
    exit 0
}

$outputRoot = Ensure-Directory ([string]$config.output_root)
$runId = 'run-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 10)
$runRoot = Ensure-Directory (Join-Path $outputRoot $runId)
Write-JsonFile -Path (Join-Path $runRoot 'native-codex.json') -Value $nativeReceipt
Write-JsonFile -Path (Join-Path $runRoot 'godot-runtime.json') -Value $godotReceipt
Write-JsonFile -Path (Join-Path $runRoot 'run-policy.json') -Value ([pscustomobject]@{
    run_id = $runId
    mode = $Mode
    model = [string]$config.model
    reasoning_effort = [string]$config.reasoning_effort
    service_tier_override = $null
    limits = $budgets
    max_infrastructure_reruns = 1
    fresh_image_limit_excludes_initial = $true
})

$attempts = New-Object System.Collections.ArrayList
$final = $null
for ($attempt = 1; $attempt -le 2; $attempt++) {
    $result = Invoke-OneAttempt -Config $config -RunRoot $runRoot -RunId $runId -Attempt $attempt -Mode $Mode -FailFirst ([bool]$FixtureFailFirstInfrastructure)
    [void]$attempts.Add($result)
    $final = $result
    if ($result.classification -ne 'infrastructure_invalid') { break }
    if ($attempt -eq 1) {
        Write-JsonFile -Path (Join-Path $runRoot 'rerun-lineage.json') -Value ([pscustomobject]@{
            parent_attempt = 1
            child_attempt = 2
            reason = $result.outcome
            policy = 'one_fresh_attempt_for_infrastructure_only'
        })
    }
}

$summary = [pscustomobject]@{
    run_id = $runId
    mode = $Mode
    model_called = $Mode -eq 'ExecuteModel'
    run_root = $runRoot
    attempts = @($attempts)
    final_classification = $final.classification
    final_outcome = $final.outcome
    infrastructure_reruns = [Math]::Max(0, $attempts.Count - 1)
}
Write-JsonFile -Path (Join-Path $runRoot 'summary.json') -Value $summary
$summary | ConvertTo-Json -Depth 20

if ($final.classification -eq 'completed') { exit 0 }
if ($final.classification -eq 'model_invalid') { exit 20 }
if ($final.classification -eq 'security_invalid') { exit 30 }
exit 40
