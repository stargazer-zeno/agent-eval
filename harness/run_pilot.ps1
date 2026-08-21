[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [ValidateSet('Preflight', 'Fixture', 'ExecuteModel')][string]$Mode = 'Preflight',
    [switch]$ConfirmModelExecution,
    [switch]$FixtureFailFirstInfrastructure
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$controller = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'Invoke-GameVisualFixPilot.ps1'
& $controller @PSBoundParameters
exit $LASTEXITCODE
