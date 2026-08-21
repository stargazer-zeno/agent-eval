[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Workspace,
    [Parameter(Mandatory = $true)][string]$OutputImage,
    [Parameter(Mandatory = $true)][string]$ReceiptPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) { throw 'Renderer workspace missing.' }
$imageParent = Split-Path -Parent $OutputImage
$receiptParent = Split-Path -Parent $ReceiptPath
[void][System.IO.Directory]::CreateDirectory($imageParent)
[void][System.IO.Directory]::CreateDirectory($receiptParent)
$png = [Convert]::FromBase64String('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
[System.IO.File]::WriteAllBytes($OutputImage, $png)
$receipt = [ordered]@{
    adapter = 'fixture-renderer'
    failure_class = $null
    image_bytes = $png.Length
}
[System.IO.File]::WriteAllText($ReceiptPath, (($receipt | ConvertTo-Json -Depth 5) + [Environment]::NewLine), $utf8NoBom)
exit 0
