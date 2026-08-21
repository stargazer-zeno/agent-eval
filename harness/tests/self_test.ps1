[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$testsRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$harnessRoot = [System.IO.Path]::GetFullPath((Join-Path $testsRoot '..'))
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $harnessRoot '..'))
$controller = Join-Path $harnessRoot 'Invoke-GameVisualFixPilot.ps1'
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Assert-Condition {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "SELF-TEST ASSERTION FAILED: $Message" }
}

function Write-FixtureText {
    param([string]$Path, [string]$Text)
    [void][System.IO.Directory]::CreateDirectory((Split-Path -Parent $Path))
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Invoke-ControllerFixture {
    param([string]$ConfigPath, [switch]$FailFirst)
    $arguments = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $controller,
        '-ConfigPath', $ConfigPath, '-Mode', 'Fixture')
    if ($FailFirst) { $arguments += '-FixtureFailFirstInfrastructure' }
    $output = @(& $powershell @arguments 2>&1)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) { throw "Fixture controller exited ${exitCode}:`n$($output -join [Environment]::NewLine)" }
    return (($output -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop)
}

Push-Location $repoRoot
try {
    $statusBefore = @(git status --porcelain=v1)
    & git check-ignore -q -- '.cache/staging/harness/probe'
    Assert-Condition ($LASTEXITCODE -eq 0) '.cache/staging/harness must be ignored before any test writes.'

    $caseRoot = Join-Path $repoRoot ('.cache\staging\harness\selftest-case-' + [guid]::NewGuid().ToString('N'))
    $seed = Join-Path $caseRoot 'inputs\seed'
    $sourceCodexHome = Join-Path $caseRoot 'inputs\source-codex-home'
    $outputRoot = Join-Path $caseRoot 'runs'
    [void][System.IO.Directory]::CreateDirectory($seed)
    [void][System.IO.Directory]::CreateDirectory($sourceCodexHome)
    [void][System.IO.Directory]::CreateDirectory($outputRoot)

    Write-FixtureText (Join-Path $seed 'project.godot') "[application]`r`nconfig/name=`"Fixture`"`r`n"
    Write-FixtureText (Join-Path $seed 'public\scene.txt') "public fixture seed`r`n"
    Write-FixtureText (Join-Path $seed '.env') "THIS_MUST_NOT_BE_COPIED=fixture-only`r`n"
    Write-FixtureText (Join-Path $seed 'AGENTS.md') "not agent-visible`r`n"
    Write-FixtureText (Join-Path $seed 'oracle\answer.txt') "not agent-visible`r`n"
    Write-FixtureText (Join-Path $seed 'hidden_evaluator\score.ps1') "not agent-visible`r`n"
    Write-FixtureText (Join-Path $seed 'results\old.json') "{}`r`n"
    Write-FixtureText (Join-Path $seed '.git\config') "not copied`r`n"
    Write-FixtureText (Join-Path $sourceCodexHome 'auth.json') "{\"fixture_auth\":true}`r`n"

    $prompt = Join-Path $caseRoot 'inputs\task.md'
    Write-FixtureText $prompt "Repair the public fixture and use one fresh visual observation before submitting.`r`n"
    $initialImage = Join-Path $caseRoot 'inputs\initial.png'
    $png = [Convert]::FromBase64String('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
    [System.IO.File]::WriteAllBytes($initialImage, $png)

    $npmRoot = (& npm root -g).Trim()
    Assert-Condition (-not [string]::IsNullOrWhiteSpace($npmRoot)) 'Global npm package root must be discoverable.'
    $nativeCodex = Join-Path $npmRoot '@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe'
    Assert-Condition (Test-Path -LiteralPath $nativeCodex -PathType Leaf) 'Pinned native codex.exe must exist for hash/version preflight.'
    $config = [ordered]@{
        seed_path = $seed
        initial_image = $initialImage
        prompt_path = $prompt
        model = 'fixture-do-not-call'
        reasoning_effort = 'ultra'
        codex_exe = $nativeCodex
        expected_codex_version = 'codex-cli 0.149.0'
        expected_codex_sha256 = '14B7E6B2356E82D1D9275579EAA588757B4E0A501B65DCC19FCCDF77BD83DC00'
        godot_exe = Join-Path $repoRoot '.cache\tools\godot-4.7.1\Godot_v4.7.1-stable_win64_console.exe'
        expected_godot_version = '4.7.1.stable.official.a13da4feb'
        expected_godot_sha256 = '35DAB11E04ECE16A2B93035E65204F4A944A3E00B020D43E54409193379D5EEF'
        godot_companion_exe = Join-Path $repoRoot '.cache\tools\godot-4.7.1\Godot_v4.7.1-stable_win64.exe'
        expected_godot_companion_sha256 = '323F9C4CC5DB674E98815CDD8E69DA007D5EFC779ABEDC8C0E42883B7FDEA12A'
        source_codex_home = $sourceCodexHome
        renderer_script = Join-Path $harnessRoot 'fixtures\fake_renderer.ps1'
        evaluator_script = Join-Path $harnessRoot 'fixtures\fake_evaluator.ps1'
        output_root = $outputRoot
        budgets = [ordered]@{
            max_turns = 4; max_fresh_images = 3; max_codex_wall_seconds = 1500; max_run_seconds = 2100;
            max_commands = 60; max_input_tokens = 150000; max_output_tokens = 20000;
            capture_timeout_seconds = 90; evaluator_timeout_seconds = 180
        }
    }
    $configPath = Join-Path $caseRoot 'config.json'
    Write-FixtureText $configPath (($config | ConvertTo-Json -Depth 10) + [Environment]::NewLine)

    $preflightOutput = @(& $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $controller -ConfigPath $configPath -Mode Preflight 2>&1)
    Assert-Condition ($LASTEXITCODE -eq 0) 'Preflight must pass without a model call.'
    $preflight = ($preflightOutput -join [Environment]::NewLine) | ConvertFrom-Json
    Assert-Condition (-not [bool]$preflight.model_called) 'Preflight must report model_called=false.'
    Assert-Condition ($preflight.native_codex.version -eq 'codex-cli 0.149.0') 'Preflight must pin Codex 0.149.0.'
    Assert-Condition ($preflight.godot_runtime.version -eq '4.7.1.stable.official.a13da4feb') 'Preflight must pin Godot 4.7.1.'
    Assert-Condition ($preflight.reasoning_effort -eq 'ultra') 'Preflight must freeze ultra reasoning.'

    $normal = Invoke-ControllerFixture -ConfigPath $configPath
    Assert-Condition (-not [bool]$normal.model_called) 'Fixture mode must report model_called=false.'
    Assert-Condition ($normal.final_classification -eq 'completed') 'Normal fixture run must complete.'
    Assert-Condition ($normal.final_outcome -eq 'submitted') 'Normal fixture run must submit.'
    Assert-Condition (@($normal.attempts).Count -eq 1) 'Normal fixture run must not rerun.'
    $attempt = @($normal.attempts)[0]
    Assert-Condition ([int]$attempt.turns_used -eq 2) 'Observe/submit loop must use two turns.'
    Assert-Condition ([int]$attempt.initial_images -eq 1) 'One initial image must be recorded separately.'
    Assert-Condition ([int]$attempt.fresh_images -eq 1) 'One fresh image must be counted.'
    Assert-Condition ([int]$attempt.image_attachments -eq 2) 'Initial plus one fresh image must produce two attachments.'
    Assert-Condition ([int]$attempt.commands_observed -eq 2) 'Unique command items must be counted once each.'
    Assert-Condition ([int64]$attempt.input_tokens_observed -eq 20) 'Turn input-token telemetry must be accumulated.'
    Assert-Condition ([int64]$attempt.output_tokens_observed -eq 10) 'Turn output-token telemetry must be accumulated.'

    $workspace = Join-Path ([string]$attempt.attempt_root) 'workspace'
    Assert-Condition (Test-Path -LiteralPath (Join-Path $workspace 'agent_change.txt')) 'Fixture agent edit must survive.'
    Assert-Condition (([System.IO.File]::ReadAllText((Join-Path $workspace 'agent_change.txt'))).Contains('godot=4.7.1.stable.official.a13da4feb')) 'Fixture child PATH must resolve godot --version.'
    foreach ($forbidden in @('.env', 'AGENTS.md', 'oracle', 'hidden_evaluator', 'results')) {
        Assert-Condition (-not (Test-Path -LiteralPath (Join-Path $workspace $forbidden))) "Sanitizer must exclude $forbidden."
    }
    $commitCount = (& git -C $workspace rev-list --count HEAD).Trim()
    $branch = (& git -C $workspace branch --show-current).Trim()
    $remotes = @(& git -C $workspace remote)
    Assert-Condition ($commitCount -eq '1') 'Agent workspace must start from one commit.'
    Assert-Condition ($branch -eq 'main') 'Agent workspace branch must be main.'
    Assert-Condition ($remotes.Count -eq 0) 'Agent workspace must have no remote.'

    $trajectory = Join-Path ([string]$attempt.attempt_root) 'normalized\trajectory.jsonl'
    $rawTurn0 = Join-Path ([string]$attempt.attempt_root) 'raw\codex-turn-0.stdout.jsonl'
    Assert-Condition (Test-Path -LiteralPath $trajectory -PathType Leaf) 'Normalized trajectory must exist.'
    Assert-Condition (Test-Path -LiteralPath $rawTurn0 -PathType Leaf) 'Raw Codex JSONL must exist.'
    foreach ($line in @(Get-Content -LiteralPath $trajectory)) { [void]($line | ConvertFrom-Json -ErrorAction Stop) }
    foreach ($line in @(Get-Content -LiteralPath $rawTurn0)) { [void]($line | ConvertFrom-Json -ErrorAction Stop) }

    $archive = [string]$attempt.archive_path
    Assert-Condition (Test-Path -LiteralPath $archive -PathType Container) 'Safe archive copy must exist.'
    Assert-Condition (@(Get-ChildItem -LiteralPath $archive -Filter auth.json -File -Recurse -Force).Count -eq 0) 'auth.json must never enter archive.'
    Assert-Condition (-not (Test-Path -LiteralPath (Join-Path $archive 'control\private_tools'))) 'Private evaluator/renderer code must never enter archive.'
    $scan = Get-Content -LiteralPath (Join-Path ([string]$attempt.attempt_root) 'receipts\credential-scan.json') -Raw | ConvertFrom-Json
    Assert-Condition (@($scan.findings).Count -eq 0) 'Credential scan must be clean.'
    $evaluation = Get-Content -LiteralPath (Join-Path ([string]$attempt.attempt_root) 'evaluation\result\result.json') -Raw | ConvertFrom-Json
    Assert-Condition ([bool]$evaluation.passed) 'Fixture hidden evaluator must pass the edited workspace.'

    $rerun = Invoke-ControllerFixture -ConfigPath $configPath -FailFirst
    Assert-Condition ($rerun.final_classification -eq 'completed') 'One infrastructure rerun must recover.'
    Assert-Condition ([int]$rerun.infrastructure_reruns -eq 1) 'Exactly one infrastructure rerun must be recorded.'
    Assert-Condition (@($rerun.attempts).Count -eq 2) 'Infrastructure fixture must have two fresh attempts.'
    Assert-Condition (@($rerun.attempts)[0].classification -eq 'infrastructure_invalid') 'First simulated attempt must be infrastructure-invalid.'
    Assert-Condition (@($rerun.attempts)[1].classification -eq 'completed') 'Second simulated attempt must complete.'
    Assert-Condition (Test-Path -LiteralPath (Join-Path ([string]$rerun.run_root) 'rerun-lineage.json')) 'Rerun lineage receipt must exist.'

    $controllerText = [System.IO.File]::ReadAllText($controller)
    foreach ($requiredSyntax in @("'exec', 'resume'", "'--image'", "'--json'", "'--output-schema'", "'--ignore-user-config'", "'--ignore-rules'", "'--disable', 'multi_agent'")) {
        Assert-Condition ($controllerText.Contains($requiredSyntax)) "Production command builder must contain $requiredSyntax."
    }
    Assert-Condition (-not $controllerText.Contains("'--last'" + ',')) 'Production command builder must not add --last.'
    Assert-Condition (-not $controllerText.Contains("'--ephemeral'" + ',')) 'Production command builder must not add --ephemeral.'

    $statusAfter = @(git status --porcelain=v1)
    Assert-Condition (($statusBefore -join "`n") -eq ($statusAfter -join "`n")) 'Tracked/untracked visible git status must be unchanged.'

    [pscustomobject]@{
        passed = $true
        model_called = $false
        fixture_case_root = $caseRoot
        normal_run = $normal.run_root
        rerun_case = $rerun.run_root
        assertions = @(
            'ignored staging gate', 'native Codex version/hash', 'sanitized single-commit workspace',
            'observe/submit image loop', 'raw and normalized JSONL', 'command/image/turn accounting',
            'private auth/evaluator archive exclusion', 'credential scan', 'single infra rerun',
            'unchanged repository status'
        )
    } | ConvertTo-Json -Depth 10
}
finally {
    Pop-Location
}
