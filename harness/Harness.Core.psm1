Set-StrictMode -Version 2.0

$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Get-FullPathSafe {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Path))
}

function Assert-PathWithin {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root,
        [switch]$AllowRoot
    )
    $fullPath = Get-FullPathSafe $Path
    $fullRoot = (Get-FullPathSafe $Root).TrimEnd('\', '/')
    if ($AllowRoot -and $fullPath.Equals($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath
    }
    $prefix = $fullRoot + [System.IO.Path]::DirectorySeparatorChar
    if (-not $fullPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes allowed root: '$fullPath' is not under '$fullRoot'."
    }
    return $fullPath
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $full = Get-FullPathSafe $Path
    [void][System.IO.Directory]::CreateDirectory($full)
    return $full
}

function Write-Utf8NoBomText {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowEmptyString()][string]$Text
    )
    $parent = Split-Path -Parent (Get-FullPathSafe $Path)
    if ($parent) { [void](Ensure-Directory $parent) }
    [System.IO.File]::WriteAllText((Get-FullPathSafe $Path), $Text, $script:Utf8NoBom)
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value,
        [int]$Depth = 20
    )
    $json = $Value | ConvertTo-Json -Depth $Depth
    Write-Utf8NoBomText -Path $Path -Text ($json + [Environment]::NewLine)
}

function Add-JsonLine {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value,
        [int]$Depth = 30
    )
    $parent = Split-Path -Parent (Get-FullPathSafe $Path)
    if ($parent) { [void](Ensure-Directory $parent) }
    $line = ($Value | ConvertTo-Json -Compress -Depth $Depth) + [Environment]::NewLine
    [System.IO.File]::AppendAllText((Get-FullPathSafe $Path), $line, $script:Utf8NoBom)
}

$script:TrajectoryGenesisHash = '0000000000000000000000000000000000000000000000000000000000000000'

function Get-TextSha256 {
    param([AllowEmptyString()][string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $script:Utf8NoBom.GetBytes($Text)
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToUpperInvariant()
    }
    finally { $sha.Dispose() }
}

function Get-TrajectoryCanonicalRecord {
    param(
        [Parameter(Mandatory = $true)]$Event,
        [Parameter(Mandatory = $true)][int64]$ChainIndex
    )
    return [ordered]@{
        chain_index = $ChainIndex
        sequence = [string](Get-OptionalProperty -Object $Event -Name 'sequence' -Default '')
        captured_at_utc = [string](Get-OptionalProperty -Object $Event -Name 'captured_at_utc' -Default '')
        run_id = [string](Get-OptionalProperty -Object $Event -Name 'run_id' -Default '')
        attempt = [int](Get-OptionalProperty -Object $Event -Name 'attempt' -Default 0)
        turn = [int](Get-OptionalProperty -Object $Event -Name 'turn' -Default 0)
        source = [string](Get-OptionalProperty -Object $Event -Name 'source' -Default '')
        payload = Get-OptionalProperty -Object $Event -Name 'payload' -Default $null
    }
}

function Add-TrajectoryEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Event
    )
    $full = Get-FullPathSafe $Path
    $lines = @()
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $lines = @([System.IO.File]::ReadAllLines($full, [System.Text.Encoding]::UTF8) | Where-Object { $_.Trim() -ne '' })
    }
    $previous = $script:TrajectoryGenesisHash
    if ($lines.Count -gt 0) {
        $last = $lines[$lines.Count - 1] | ConvertFrom-Json -ErrorAction Stop
        $previous = [string](Get-OptionalProperty -Object $last -Name 'event_hash' -Default '')
        if ($previous -notmatch '^[A-F0-9]{64}$') { throw 'Existing normalized trajectory has no valid hash-chain head.' }
    }
    $base = Get-TrajectoryCanonicalRecord -Event $Event -ChainIndex ([int64]$lines.Count)
    $canonical = $base | ConvertTo-Json -Compress -Depth 50
    $eventHash = Get-TextSha256 ("GameVisualFix-Trajectory-v1`n$previous`n$canonical")
    $chained = [ordered]@{
        chain_index = $base.chain_index
        sequence = $base.sequence
        captured_at_utc = $base.captured_at_utc
        run_id = $base.run_id
        attempt = $base.attempt
        turn = $base.turn
        source = $base.source
        payload = $base.payload
        previous_hash = $previous
        event_hash = $eventHash
    }
    Add-JsonLine -Path $full -Value $chained -Depth 50
    return [pscustomobject]$chained
}

function Test-TrajectoryHashChain {
    param([Parameter(Mandatory = $true)][string]$Path)
    $full = Get-FullPathSafe $Path
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        return [pscustomobject]@{ valid = $false; count = 0; head = $null; genesis = $script:TrajectoryGenesisHash; error = 'missing_file' }
    }
    $lines = @([System.IO.File]::ReadAllLines($full, [System.Text.Encoding]::UTF8) | Where-Object { $_.Trim() -ne '' })
    $previous = $script:TrajectoryGenesisHash
    for ($index = 0; $index -lt $lines.Count; $index++) {
        try { $event = $lines[$index] | ConvertFrom-Json -ErrorAction Stop }
        catch { return [pscustomobject]@{ valid = $false; count = $index; head = $previous; genesis = $script:TrajectoryGenesisHash; error = 'invalid_json' } }
        if ([int64](Get-OptionalProperty -Object $event -Name 'chain_index' -Default -1) -ne $index) {
            return [pscustomobject]@{ valid = $false; count = $index; head = $previous; genesis = $script:TrajectoryGenesisHash; error = 'index_mismatch' }
        }
        $recordedPrevious = [string](Get-OptionalProperty -Object $event -Name 'previous_hash' -Default '')
        if ($recordedPrevious -ne $previous) {
            return [pscustomobject]@{ valid = $false; count = $index; head = $previous; genesis = $script:TrajectoryGenesisHash; error = 'previous_hash_mismatch' }
        }
        $base = Get-TrajectoryCanonicalRecord -Event $event -ChainIndex ([int64]$index)
        $canonical = $base | ConvertTo-Json -Compress -Depth 50
        $expected = Get-TextSha256 ("GameVisualFix-Trajectory-v1`n$previous`n$canonical")
        $recorded = [string](Get-OptionalProperty -Object $event -Name 'event_hash' -Default '')
        if ($recorded -ne $expected) {
            return [pscustomobject]@{ valid = $false; count = $index; head = $previous; genesis = $script:TrajectoryGenesisHash; error = 'event_hash_mismatch' }
        }
        $previous = $recorded
    }
    return [pscustomobject]@{
        valid = $true
        count = $lines.Count
        head = $previous
        genesis = $script:TrajectoryGenesisHash
        algorithm = 'SHA-256(GameVisualFix-Trajectory-v1 LF previous_hash LF canonical-json)'
        error = $null
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath (Get-FullPathSafe $Path) -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativePathWithin {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )
    $fullRoot = (Get-FullPathSafe $Root).TrimEnd('\', '/')
    $fullPath = Assert-PathWithin -Path $Path -Root $fullRoot
    return $fullPath.Substring($fullRoot.Length).TrimStart('\', '/')
}

function Get-OptionalProperty {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        $Default = $null
    )
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Test-ExcludedRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $normalized = $RelativePath.Replace('/', '\')
    $segments = @($normalized.Split('\') | Where-Object { $_ -ne '' })
    $blockedSegments = @(
        '.git', '.codex', '.godot', '.cache', '__pycache__', '.pytest_cache',
        'trajectories', 'results', 'oracle', 'oracles', 'hidden', 'hidden_tests',
        'evaluator', 'evaluators', 'reference_patch', 'reference-patch', 'reference-patches'
    )
    foreach ($segment in $segments) {
        if ($blockedSegments -contains $segment.ToLowerInvariant()) { return $true }
        if ($segment -match '^(?i:AGENTS)(\..+)?$') { return $true }
        if ($segment -match '^(?i:\.env)(\..+)?$') { return $true }
    }
    if ($normalized -match '(?i)(^|\\)(oracle|hidden|evaluator|reference[_-]?patch)([^\\]*)(\\|$)') {
        return $true
    }
    if ($normalized -match '(?i)\.(pyc|pyo|tmp|temp|bak|swp|swo)$') { return $true }
    return $false
}

function Get-SanitizedFileInventory {
    param([Parameter(Mandatory = $true)][string]$Source)

    $sourceFull = Get-FullPathSafe $Source
    if (-not (Test-Path -LiteralPath $sourceFull -PathType Container)) {
        throw "Seed/source directory does not exist: $sourceFull"
    }
    $sourceItem = Get-Item -LiteralPath $sourceFull -Force
    if (($sourceItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Seed/source root cannot be a reparse point: $sourceFull"
    }

    $queue = New-Object 'System.Collections.Generic.Queue[System.IO.DirectoryInfo]'
    $queue.Enqueue($sourceItem)
    $included = New-Object System.Collections.ArrayList
    $excluded = New-Object System.Collections.ArrayList

    while ($queue.Count -gt 0) {
        $directory = $queue.Dequeue()
        foreach ($item in @(Get-ChildItem -LiteralPath $directory.FullName -Force -ErrorAction Stop)) {
            $relative = Get-RelativePathWithin -Path $item.FullName -Root $sourceFull
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                [void]$excluded.Add([pscustomobject]@{ path = $relative; reason = 'reparse_point' })
                continue
            }
            if (Test-ExcludedRelativePath $relative) {
                [void]$excluded.Add([pscustomobject]@{ path = $relative; reason = 'denylist' })
                continue
            }
            if ($item.PSIsContainer) {
                $queue.Enqueue([System.IO.DirectoryInfo]$item)
            }
            else {
                [void]$included.Add([System.IO.FileInfo]$item)
            }
        }
    }

    return [pscustomobject]@{
        source = $sourceFull
        files = @($included)
        excluded = @($excluded | Sort-Object path)
    }
}

function Copy-SanitizedTree {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string]$ReceiptPath
    )

    $sourceFull = Get-FullPathSafe $Source
    $destinationFull = Get-FullPathSafe $Destination
    if ($destinationFull.StartsWith($sourceFull.TrimEnd('\', '/') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Destination cannot be nested inside source.'
    }
    if (Test-Path -LiteralPath $destinationFull) {
        $destinationItem = Get-Item -LiteralPath $destinationFull -Force
        if (($destinationItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Destination cannot be a reparse point: $destinationFull"
        }
        if (@(Get-ChildItem -LiteralPath $destinationFull -Force).Count -ne 0) {
            throw "Destination must be empty: $destinationFull"
        }
    }
    [void](Ensure-Directory $destinationFull)

    $inventory = Get-SanitizedFileInventory $sourceFull
    foreach ($file in @($inventory.files)) {
        $relative = Get-RelativePathWithin -Path $file.FullName -Root $sourceFull
        $target = Assert-PathWithin -Path (Join-Path $destinationFull $relative) -Root $destinationFull
        [void](Ensure-Directory (Split-Path -Parent $target))
        [System.IO.File]::Copy($file.FullName, $target, $false)
    }

    $receipt = [pscustomobject]@{
        source = $sourceFull
        destination = $destinationFull
        included_file_count = @($inventory.files).Count
        excluded = @($inventory.excluded)
    }
    if ($ReceiptPath) { Write-JsonFile -Path $ReceiptPath -Value $receipt }
    return $receipt
}

function Get-TreeManifest {
    param([Parameter(Mandatory = $true)][string]$Root)

    $rootFull = Get-FullPathSafe $Root
    $entries = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $rootFull -PathType Container)) { return @() }
    foreach ($file in @(Get-ChildItem -LiteralPath $rootFull -File -Recurse -Force | Sort-Object FullName)) {
        $relative = Get-RelativePathWithin -Path $file.FullName -Root $rootFull
        if ($relative -eq '.git' -or $relative.StartsWith('.git\', [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        if (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Manifest refuses reparse point: $relative"
        }
        [void]$entries.Add([pscustomobject]@{
            path = $relative.Replace('\', '/')
            bytes = [int64]$file.Length
            sha256 = Get-Sha256 $file.FullName
        })
    }
    return @($entries)
}

function ConvertTo-WindowsCommandLineArgument {
    param([AllowEmptyString()][string]$Argument)

    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') { return $Argument }
    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }
        if ($character -eq '"') {
            [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            [void]$builder.Append(('\' * $backslashes))
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashes -gt 0) { [void]$builder.Append(('\' * ($backslashes * 2))) }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Join-WindowsCommandLine {
    param([string[]]$Arguments)
    return (@($Arguments | ForEach-Object { ConvertTo-WindowsCommandLineArgument ([string]$_) }) -join ' ')
}

function Stop-ProcessTreeSafe {
    param([Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process)
    try {
        if (-not $Process.HasExited) {
            & "$env:SystemRoot\System32\taskkill.exe" /PID $Process.Id /T /F 2>&1 | Out-Null
        }
    }
    catch {
        try { if (-not $Process.HasExited) { $Process.Kill() } } catch { }
    }
}

function Get-MinimalChildPath {
    param([Parameter(Mandatory = $true)][string]$PublicToolDirectory)
    $gitDirectory = Split-Path -Parent (Get-Command git.exe -ErrorAction Stop).Source
    $candidates = @(
        (Get-FullPathSafe $PublicToolDirectory),
        "$env:SystemRoot\System32",
        $env:SystemRoot,
        "$env:SystemRoot\System32\Wbem",
        "$env:SystemRoot\System32\WindowsPowerShell\v1.0",
        $gitDirectory
    )
    $unique = New-Object System.Collections.ArrayList
    foreach ($candidate in $candidates) {
        if ($candidate -and -not (@($unique) -contains $candidate)) { [void]$unique.Add($candidate) }
    }
    return (@($unique) -join ';')
}

function New-MinimalChildEnvironment {
    param(
        [Parameter(Mandatory = $true)][string]$CodexHome,
        [Parameter(Mandatory = $true)][string]$PublicToolDirectory
    )
    $names = @('SystemRoot', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP', 'APPDATA', 'LOCALAPPDATA')
    $result = @{}
    foreach ($name in $names) {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ($value) { $result[$name] = $value }
    }
    $result['PATH'] = Get-MinimalChildPath $PublicToolDirectory
    $result['CODEX_HOME'] = Get-FullPathSafe $CodexHome
    $result['NO_COLOR'] = '1'
    return $result
}

function Invoke-ProcessCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [int]$TimeoutSeconds = 60,
        [hashtable]$Environment,
        [switch]$ClearEnvironment
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = Get-FullPathSafe $FilePath
    $psi.Arguments = Join-WindowsCommandLine @($Arguments)
    $psi.WorkingDirectory = Get-FullPathSafe $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8NoBom
    $psi.StandardErrorEncoding = $script:Utf8NoBom
    if ($ClearEnvironment) { $psi.EnvironmentVariables.Clear() }
    if ($Environment) {
        foreach ($key in $Environment.Keys) { $psi.EnvironmentVariables[[string]$key] = [string]$Environment[$key] }
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    try {
        if (-not $process.Start()) { throw 'Process.Start returned false.' }
    }
    catch {
        return [pscustomobject]@{ started = $false; exit_code = $null; timed_out = $false; stdout = ''; stderr = $_.Exception.Message }
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $finished = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) {
        Stop-ProcessTreeSafe $process
        [void]$process.WaitForExit(5000)
    }
    try { $stdout = $stdoutTask.Result } catch { $stdout = '' }
    try { $stderr = $stderrTask.Result } catch { $stderr = $_.Exception.Message }
    return [pscustomobject]@{
        started = $true
        exit_code = if ($process.HasExited) { $process.ExitCode } else { $null }
        timed_out = -not $finished
        stdout = $stdout
        stderr = $stderr
    }
}

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)][string]$Workspace,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $git = (Get-Command git.exe -ErrorAction Stop).Source
    $result = Invoke-ProcessCapture -FilePath $git -Arguments (@('-C', (Get-FullPathSafe $Workspace)) + $Arguments) -WorkingDirectory $Workspace -TimeoutSeconds 60
    if (-not $result.started -or $result.timed_out -or $result.exit_code -ne 0) {
        throw "git failed: $($Arguments -join ' ')`n$($result.stderr)"
    }
    return $result.stdout.TrimEnd()
}

function Initialize-SingleCommitWorkspace {
    param([Parameter(Mandatory = $true)][string]$Workspace)
    [void](Invoke-GitChecked -Workspace $Workspace -Arguments @('init', '-b', 'main'))
    [void](Invoke-GitChecked -Workspace $Workspace -Arguments @('config', 'user.name', 'GameVisualFix Harness'))
    [void](Invoke-GitChecked -Workspace $Workspace -Arguments @('config', 'user.email', 'harness.invalid@example.invalid'))
    [void](Invoke-GitChecked -Workspace $Workspace -Arguments @('config', 'core.autocrlf', 'false'))
    [void](Invoke-GitChecked -Workspace $Workspace -Arguments @('add', '--all'))
    [void](Invoke-GitChecked -Workspace $Workspace -Arguments @('commit', '--allow-empty', '-m', 'seed: sanitized benchmark workspace'))

    $branch = Invoke-GitChecked -Workspace $Workspace -Arguments @('branch', '--show-current')
    $count = Invoke-GitChecked -Workspace $Workspace -Arguments @('rev-list', '--count', 'HEAD')
    $status = Invoke-GitChecked -Workspace $Workspace -Arguments @('status', '--porcelain=v1')
    $remotes = Invoke-GitChecked -Workspace $Workspace -Arguments @('remote')
    if ($branch -ne 'main' -or $count -ne '1' -or $status -ne '' -or $remotes -ne '') {
        throw "Workspace git invariant failed (branch=$branch, commits=$count, status='$status', remotes='$remotes')."
    }
    return [pscustomobject]@{
        branch = $branch
        commit_count = [int]$count
        baseline_commit = Invoke-GitChecked -Workspace $Workspace -Arguments @('rev-parse', 'HEAD')
        clean = $true
        remotes = @()
    }
}

function Assert-NativeCodexBinary {
    param(
        [Parameter(Mandatory = $true)][string]$CodexExe,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256
    )
    $full = Get-FullPathSafe $CodexExe
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Native Codex binary not found: $full" }
    $actualHash = Get-Sha256 $full
    if ($actualHash -ne $ExpectedSha256.ToUpperInvariant()) {
        throw "Native Codex SHA-256 mismatch. Expected $ExpectedSha256; got $actualHash."
    }
    $result = Invoke-ProcessCapture -FilePath $full -Arguments @('--version') -WorkingDirectory (Split-Path -Parent $full) -TimeoutSeconds 20
    $actualVersion = $result.stdout.Trim()
    if (-not $result.started -or $result.timed_out -or $result.exit_code -ne 0 -or $actualVersion -ne $ExpectedVersion) {
        throw "Native Codex version mismatch. Expected '$ExpectedVersion'; got '$actualVersion'."
    }
    return [pscustomobject]@{ path = $full; version = $actualVersion; sha256 = $actualHash }
}

function Assert-GodotRuntime {
    param(
        [Parameter(Mandatory = $true)][string]$GodotExe,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [Parameter(Mandatory = $true)][string]$CompanionExe,
        [Parameter(Mandatory = $true)][string]$ExpectedCompanionSha256
    )
    $command = Get-FullPathSafe $GodotExe
    $companion = Get-FullPathSafe $CompanionExe
    if (-not (Test-Path -LiteralPath $command -PathType Leaf)) { throw "Godot command executable not found: $command" }
    if (-not (Test-Path -LiteralPath $companion -PathType Leaf)) { throw "Godot companion executable not found: $companion" }
    if ((Split-Path -Parent $command) -ne (Split-Path -Parent $companion)) { throw 'Godot command and companion executable must share one portable directory.' }
    $commandHash = Get-Sha256 $command
    $companionHash = Get-Sha256 $companion
    if ($commandHash -ne $ExpectedSha256.ToUpperInvariant()) { throw "Godot command SHA-256 mismatch: $commandHash" }
    if ($companionHash -ne $ExpectedCompanionSha256.ToUpperInvariant()) { throw "Godot companion SHA-256 mismatch: $companionHash" }
    $versionResult = Invoke-ProcessCapture -FilePath $command -Arguments @('--version') -WorkingDirectory (Split-Path -Parent $command) -TimeoutSeconds 30
    $actualVersion = $versionResult.stdout.Trim()
    if (-not $versionResult.started -or $versionResult.timed_out -or $versionResult.exit_code -ne 0 -or $actualVersion -ne $ExpectedVersion) {
        throw "Godot version mismatch. Expected '$ExpectedVersion'; got '$actualVersion'."
    }
    return [pscustomobject]@{
        command_path = $command
        command_sha256 = $commandHash
        companion_path = $companion
        companion_sha256 = $companionHash
        version = $actualVersion
        public_runtime_dependency = $true
    }
}

function Initialize-PublicGodotCommand {
    param(
        [Parameter(Mandatory = $true)][string]$GodotExe,
        [Parameter(Mandatory = $true)][string]$PublicToolDirectory
    )
    $exe = Get-FullPathSafe $GodotExe
    if ($exe.Contains('%') -or $exe.Contains('"')) { throw 'Godot path cannot be represented safely in the command shim.' }
    $directory = Ensure-Directory $PublicToolDirectory
    $shim = Join-Path $directory 'godot.cmd'
    $body = "@echo off`r`n`"$exe`" %*`r`n"
    Write-Utf8NoBomText -Path $shim -Text $body
    return [pscustomobject]@{
        command = 'godot'
        shim_path = $shim
        shim_sha256 = Get-Sha256 $shim
        target_sha256 = Get-Sha256 $exe
        public_runtime_dependency = $true
    }
}

function Protect-PrivatePathAcl {
    param([Parameter(Mandatory = $true)][string]$Path)
    $full = Get-FullPathSafe $Path
    try {
        $isDirectory = Test-Path -LiteralPath $full -PathType Container
        if ($isDirectory) {
            $acl = New-Object System.Security.AccessControl.DirectorySecurity
            $inheritance = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
        }
        else {
            $acl = New-Object System.Security.AccessControl.FileSecurity
            $inheritance = [System.Security.AccessControl.InheritanceFlags]::None
        }
        $acl.SetAccessRuleProtection($true, $false)
        $propagation = [System.Security.AccessControl.PropagationFlags]::None
        $allow = [System.Security.AccessControl.AccessControlType]::Allow
        $rights = [System.Security.AccessControl.FileSystemRights]::FullControl
        $identities = @(
            [System.Security.Principal.WindowsIdentity]::GetCurrent().User,
            (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @('S-1-5-18')),
            (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @('S-1-5-32-544'))
        )
        foreach ($identity in $identities) {
            $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($identity, $rights, $inheritance, $propagation, $allow)
            [void]$acl.AddAccessRule($rule)
        }
        Set-Acl -LiteralPath $full -AclObject $acl -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Initialize-RunCodexHome {
    param(
        [Parameter(Mandatory = $true)][string]$SourceCodexHome,
        [Parameter(Mandatory = $true)][string]$RunCodexHome
    )
    $source = Get-FullPathSafe $SourceCodexHome
    $target = Get-FullPathSafe $RunCodexHome
    $sourceAuth = Join-Path $source 'auth.json'
    if (-not (Test-Path -LiteralPath $sourceAuth -PathType Leaf)) { throw "auth.json not found in source CODEX_HOME: $source" }
    [void](Ensure-Directory $target)
    $targetAuth = Join-Path $target 'auth.json'
    [System.IO.File]::Copy($sourceAuth, $targetAuth, $false)
    $directoryAcl = Protect-PrivatePathAcl $target
    $fileAcl = Protect-PrivatePathAcl $targetAuth
    if (-not $directoryAcl -or -not $fileAcl) {
        throw 'Could not apply restrictive ACL to run-local CODEX_HOME/auth.json.'
    }
    if ((Get-Sha256 $sourceAuth) -ne (Get-Sha256 $targetAuth)) { throw 'auth.json copy hash mismatch.' }
    return [pscustomobject]@{
        copied_files = @('auth.json')
        acl_restricted = $true
        archive_allowed = $false
    }
}

function Invoke-JsonlProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$RawStdoutPath,
        [Parameter(Mandatory = $true)][string]$RawStderrPath,
        [Parameter(Mandatory = $true)][string]$NormalizedPath,
        [Parameter(Mandatory = $true)][string]$RunId,
        [Parameter(Mandatory = $true)][int]$Attempt,
        [Parameter(Mandatory = $true)][int]$Turn,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds,
        [Parameter(Mandatory = $true)][int]$RemainingCommandBudget,
        [hashtable]$Environment,
        [switch]$ClearEnvironment
    )

    $invocationStartedAt = [DateTime]::UtcNow
    Write-Utf8NoBomText -Path $RawStdoutPath -Text ''
    Write-Utf8NoBomText -Path $RawStderrPath -Text ''
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = Get-FullPathSafe $FilePath
    $psi.Arguments = Join-WindowsCommandLine @($Arguments)
    $psi.WorkingDirectory = Get-FullPathSafe $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8NoBom
    $psi.StandardErrorEncoding = $script:Utf8NoBom
    if ($ClearEnvironment) { $psi.EnvironmentVariables.Clear() }
    if ($Environment) {
        foreach ($key in $Environment.Keys) { $psi.EnvironmentVariables[[string]$key] = [string]$Environment[$key] }
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    try {
        if (-not $process.Start()) { throw 'Process.Start returned false.' }
    }
    catch {
        return [pscustomobject]@{
            started = $false; exit_code = $null; stop_reason = 'process_launch';
            malformed_lines = 0; command_count = 0; thread_id = $null; action = $null;
            stderr = $_.Exception.Message; duration_seconds = ([DateTime]::UtcNow - $invocationStartedAt).TotalSeconds;
            input_tokens = 0; output_tokens = 0
        }
    }

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $stdoutTask = $process.StandardOutput.ReadLineAsync()
    $stdoutClosed = $false
    $lineNumber = 0
    $malformed = 0
    $threadId = $null
    $action = $null
    $commandIds = @{}
    $inputTokens = [int64]0
    $outputTokens = [int64]0
    $stopReason = $null

    while (-not $stdoutClosed) {
        if ([DateTime]::UtcNow -ge $deadline) {
            $stopReason = 'wall_timeout'
            Stop-ProcessTreeSafe $process
            break
        }

        $completed = $false
        try { $completed = $stdoutTask.Wait(100) } catch { $completed = $true }
        if (-not $completed) {
            if ($process.HasExited -and $stdoutTask.IsCompleted) { $completed = $true } else { continue }
        }

        try { $line = $stdoutTask.Result } catch { $line = $null; $malformed++ }
        if ($null -eq $line) {
            $stdoutClosed = $true
            break
        }

        $lineNumber++
        [System.IO.File]::AppendAllText((Get-FullPathSafe $RawStdoutPath), $line + [Environment]::NewLine, $script:Utf8NoBom)
        $payload = $null
        try { $payload = $line | ConvertFrom-Json -ErrorAction Stop } catch { $malformed++ }
        if ($null -ne $payload) {
            [void](Add-TrajectoryEvent -Path $NormalizedPath -Event ([pscustomobject]@{
                sequence = ('{0}.{1}.{2}' -f $Attempt, $Turn, $lineNumber)
                captured_at_utc = [DateTime]::UtcNow.ToString('o')
                run_id = $RunId
                attempt = $Attempt
                turn = $Turn
                source = 'codex'
                payload = $payload
            }))

            $type = [string](Get-OptionalProperty -Object $payload -Name 'type' -Default '')
            if ($type -eq 'thread.started') {
                $candidate = [string](Get-OptionalProperty -Object $payload -Name 'thread_id' -Default '')
                $parsedGuid = [guid]::Empty
                if ($candidate -and [guid]::TryParse($candidate, [ref]$parsedGuid)) {
                    if ($threadId -and $threadId -ne $candidate) { $malformed++ }
                    else { $threadId = $candidate }
                }
                elseif ($candidate) { $malformed++ }
            }
            if ($type -eq 'item.started' -or $type -eq 'item.completed') {
                $item = Get-OptionalProperty -Object $payload -Name 'item' -Default $null
                if ($null -ne $item) {
                    $itemType = [string](Get-OptionalProperty -Object $item -Name 'type' -Default '')
                    $itemId = [string](Get-OptionalProperty -Object $item -Name 'id' -Default ('line-' + $lineNumber))
                    if ($itemType -eq 'command_execution' -and -not $commandIds.ContainsKey($itemId)) {
                        $commandIds[$itemId] = $true
                        if ($commandIds.Count -gt $RemainingCommandBudget) {
                            $stopReason = 'command_budget'
                            Stop-ProcessTreeSafe $process
                            break
                        }
                    }
                    if ($type -eq 'item.completed' -and $itemType -eq 'agent_message') {
                        $text = [string](Get-OptionalProperty -Object $item -Name 'text' -Default '')
                        if ($text) {
                            try {
                                $candidateAction = $text | ConvertFrom-Json -ErrorAction Stop
                                $actionName = [string](Get-OptionalProperty -Object $candidateAction -Name 'action' -Default '')
                                $summary = [string](Get-OptionalProperty -Object $candidateAction -Name 'summary' -Default '')
                                $allowedProperties = @('action', 'summary')
                                $unknown = @($candidateAction.PSObject.Properties.Name | Where-Object { $allowedProperties -notcontains $_ })
                                if (($actionName -eq 'observe' -or $actionName -eq 'submit') -and
                                    $summary.Length -ge 1 -and $summary.Length -le 2000 -and
                                    $unknown.Count -eq 0) {
                                    $action = $candidateAction
                                }
                            }
                            catch { }
                        }
                    }
                }
            }
            if ($type -eq 'turn.completed') {
                $usage = Get-OptionalProperty -Object $payload -Name 'usage' -Default $null
                if ($null -ne $usage) {
                    $inputTokens = [int64](Get-OptionalProperty -Object $usage -Name 'input_tokens' -Default 0)
                    $outputTokens = [int64](Get-OptionalProperty -Object $usage -Name 'output_tokens' -Default 0)
                }
            }
        }

        $stdoutTask = $process.StandardOutput.ReadLineAsync()
    }

    if ($stopReason) {
        try { [void]$process.WaitForExit(5000) } catch { }
    }
    else {
        $remainingMilliseconds = [Math]::Max(1, [int]([DateTime]::UtcNow.Subtract($deadline).Negate().TotalMilliseconds))
        if (-not $process.WaitForExit($remainingMilliseconds)) {
            $stopReason = 'wall_timeout'
            Stop-ProcessTreeSafe $process
            try { [void]$process.WaitForExit(5000) } catch { }
        }
    }

    try { $stderr = $stderrTask.Result } catch { $stderr = $_.Exception.Message }
    Write-Utf8NoBomText -Path $RawStderrPath -Text $stderr
    $exitCode = $null
    if ($process.HasExited) { $exitCode = $process.ExitCode }
    if (-not $stopReason -and $exitCode -ne 0) { $stopReason = 'nonzero_exit' }
    if (-not $stopReason -and $malformed -gt 0) { $stopReason = 'malformed_jsonl' }

    return [pscustomobject]@{
        started = $true
        exit_code = $exitCode
        stop_reason = $stopReason
        malformed_lines = $malformed
        command_count = $commandIds.Count
        thread_id = $threadId
        action = $action
        stderr = $stderr
        duration_seconds = ([DateTime]::UtcNow - $invocationStartedAt).TotalSeconds
        input_tokens = $inputTokens
        output_tokens = $outputTokens
    }
}

function Copy-PrivateAdapter {
    param(
        [Parameter(Mandatory = $true)][string]$SourceScript,
        [Parameter(Mandatory = $true)][string]$PrivateDirectory,
        [Parameter(Mandatory = $true)][ValidateSet('renderer', 'evaluator')][string]$Role
    )
    $source = Get-FullPathSafe $SourceScript
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "$Role adapter not found: $source" }
    $private = Ensure-Directory $PrivateDirectory
    $target = Join-Path $private ($Role + '.ps1')
    [System.IO.File]::Copy($source, $target, $false)
    if (-not (Protect-PrivatePathAcl $private)) { throw "Could not protect private $Role adapter directory." }
    if ((Get-Sha256 $source) -ne (Get-Sha256 $target)) { throw "$Role adapter copy hash mismatch." }
    return [pscustomobject]@{
        role = $Role
        private_path = $target
        sha256 = Get-Sha256 $target
        archive_allowed = $false
    }
}

function Invoke-RendererAdapter {
    param(
        [Parameter(Mandatory = $true)][string]$AdapterScript,
        [Parameter(Mandatory = $true)][string]$Workspace,
        [Parameter(Mandatory = $true)][string]$OutputImage,
        [Parameter(Mandatory = $true)][string]$ReceiptPath,
        [int]$TimeoutSeconds = 180
    )
    $powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $arguments = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', (Get-FullPathSafe $AdapterScript),
        '-Workspace', (Get-FullPathSafe $Workspace), '-OutputImage', (Get-FullPathSafe $OutputImage),
        '-ReceiptPath', (Get-FullPathSafe $ReceiptPath))
    $result = Invoke-ProcessCapture -FilePath $powershell -Arguments $arguments -WorkingDirectory $Workspace -TimeoutSeconds $TimeoutSeconds
    $failureClass = 'infrastructure'
    if (Test-Path -LiteralPath $ReceiptPath -PathType Leaf) {
        try {
            $receipt = [System.IO.File]::ReadAllText((Get-FullPathSafe $ReceiptPath), [System.Text.Encoding]::UTF8) | ConvertFrom-Json -ErrorAction Stop
            $declared = [string](Get-OptionalProperty -Object $receipt -Name 'failure_class' -Default '')
            if ($declared -eq 'submission') { $failureClass = 'submission' }
        }
        catch { }
    }
    $validImage = (Test-Path -LiteralPath $OutputImage -PathType Leaf) -and ((Get-Item -LiteralPath $OutputImage).Length -gt 0)
    return [pscustomobject]@{
        success = $result.started -and -not $result.timed_out -and $result.exit_code -eq 0 -and $validImage
        failure_class = if ($result.started -and -not $result.timed_out -and $result.exit_code -eq 0 -and $validImage) { $null } else { $failureClass }
        exit_code = $result.exit_code
        timed_out = $result.timed_out
        stdout = $result.stdout
        stderr = $result.stderr
        image_sha256 = if ($validImage) { Get-Sha256 $OutputImage } else { $null }
    }
}

function Invoke-EvaluatorAdapter {
    param(
        [Parameter(Mandatory = $true)][string]$AdapterScript,
        [Parameter(Mandatory = $true)][string]$Workspace,
        [Parameter(Mandatory = $true)][string]$ResultPath,
        [int]$TimeoutSeconds = 300
    )
    $powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $arguments = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', (Get-FullPathSafe $AdapterScript),
        '-Workspace', (Get-FullPathSafe $Workspace), '-ResultPath', (Get-FullPathSafe $ResultPath))
    $result = Invoke-ProcessCapture -FilePath $powershell -Arguments $arguments -WorkingDirectory $Workspace -TimeoutSeconds $TimeoutSeconds
    $validJson = $false
    if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
        try {
            $parsed = [System.IO.File]::ReadAllText((Get-FullPathSafe $ResultPath), [System.Text.Encoding]::UTF8) | ConvertFrom-Json -ErrorAction Stop
            $validJson = $null -ne $parsed
        }
        catch { }
    }
    return [pscustomobject]@{
        success = $result.started -and -not $result.timed_out -and $result.exit_code -eq 0 -and $validJson
        exit_code = $result.exit_code
        timed_out = $result.timed_out
        stdout = $result.stdout
        stderr = $result.stderr
        result_sha256 = if ($validJson) { Get-Sha256 $ResultPath } else { $null }
    }
}

function Find-CredentialIndicators {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string[]]$ExcludedRoots = @()
    )
    $rootFull = Get-FullPathSafe $Root
    $excluded = @($ExcludedRoots | ForEach-Object { (Get-FullPathSafe $_).TrimEnd('\', '/') + '\' })
    $binaryExtensions = @('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.zip', '.7z', '.exe', '.dll', '.pdb')
    $patterns = @(
        [pscustomobject]@{ name = 'openai_key'; regex = 'sk-[A-Za-z0-9_-]{20,}' },
        [pscustomobject]@{ name = 'github_token'; regex = '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})' },
        [pscustomobject]@{ name = 'bearer_token'; regex = '(?i)Bearer\s+[A-Za-z0-9._-]{20,}' },
        [pscustomobject]@{ name = 'assigned_secret'; regex = '(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[=:]\s*["'']?(?!placeholder|example|fake|redacted|null)[A-Za-z0-9._-]{16,}' }
    )
    $findings = New-Object System.Collections.ArrayList
    foreach ($file in @(Get-ChildItem -LiteralPath $rootFull -File -Recurse -Force -ErrorAction Stop)) {
        $fileFull = Get-FullPathSafe $file.FullName
        $relativeForScan = (Get-RelativePathWithin -Path $fileFull -Root $rootFull).Replace('/', '\')
        if ($relativeForScan -match '(^|\\)\.git(\\|$)') { continue }
        $skip = $false
        foreach ($prefix in $excluded) {
            if ($fileFull.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { $skip = $true; break }
        }
        if ($skip -or $binaryExtensions -contains $file.Extension.ToLowerInvariant() -or $file.Length -gt 10485760) { continue }
        try { $lines = @([System.IO.File]::ReadAllLines($fileFull, [System.Text.Encoding]::UTF8)) } catch { continue }
        for ($index = 0; $index -lt $lines.Count; $index++) {
            foreach ($pattern in $patterns) {
                if ([regex]::IsMatch([string]$lines[$index], $pattern.regex)) {
                    [void]$findings.Add([pscustomobject]@{
                        path = (Get-RelativePathWithin -Path $fileFull -Root $rootFull).Replace('\', '/')
                        line = $index + 1
                        indicator = $pattern.name
                    })
                }
            }
        }
    }
    return @($findings)
}

function New-SafeArchiveCopy {
    param(
        [Parameter(Mandatory = $true)][string]$AttemptRoot,
        [Parameter(Mandatory = $true)][string]$ArchiveRoot
    )
    $source = Get-FullPathSafe $AttemptRoot
    $destination = Get-FullPathSafe $ArchiveRoot
    if ($destination.StartsWith($source.TrimEnd('\', '/') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Archive destination cannot be nested inside attempt root.'
    }
    [void](Ensure-Directory $destination)
    foreach ($file in @(Get-ChildItem -LiteralPath $source -File -Recurse -Force | Sort-Object FullName)) {
        $relative = Get-RelativePathWithin -Path $file.FullName -Root $source
        $normalized = $relative.Replace('/', '\')
        if ($normalized -match '^(?i:control\\(codex_home|private_tools))(\\|$)') { continue }
        if ($normalized -match '(^|\\)(?i:auth\.json)$') { continue }
        if ($normalized -match '^(?i:workspace\\\.git)(\\|$)') { continue }
        if ($normalized -match '^(?i:(render|evaluation)\\.+\\\.git)(\\|$)') { continue }
        $target = Assert-PathWithin -Path (Join-Path $destination $relative) -Root $destination
        [void](Ensure-Directory (Split-Path -Parent $target))
        [System.IO.File]::Copy($file.FullName, $target, $false)
    }
    return @(Get-TreeManifest $destination)
}

Export-ModuleMember -Function *
