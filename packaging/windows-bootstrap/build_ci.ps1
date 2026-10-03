# Initializes the runner's existing toolchain; no installation.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'EXISTING_WINDOWS_RUNNER_REQUIRED' }
$pins = @{
    'launcher_plan.c' = '13bcc898bf893cbcb756b67af80e8fb53cf2496058461be3539512b8e6725345'
    'launcher_plan.h' = '5faa6ec8293f96e63576c1d64b609c842d72acf43fea89adea97f42bc37365a8'
    'launcher_win.c' = 'a08310a689ff900cf9793835f8191ce304324847d5d2ce0f77072e50f8ddf4a8'
    'build_windows.ps1' = '91791f138e830958f827bab4996883b9aa58fff6fc4ac527b60a7d51255cbaf0'
}
function Require-Pins {
    foreach ($name in $pins.Keys) {
        if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pins[$name]) { throw 'REVIEWED_BOOTSTRAP_SOURCE_CHANGED' }
    }
}
Require-Pins
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) { throw 'EXISTING_VSWHERE_REQUIRED' }
$installation = @(& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath)
if ($LASTEXITCODE -ne 0 -or $installation.Count -ne 1 -or [string]::IsNullOrWhiteSpace($installation[0])) { throw 'EXISTING_MSVC_INSTALLATION_REQUIRED' }
$developerShell = Join-Path $installation[0] 'Common7\Tools\Launch-VsDevShell.ps1'
if (-not (Test-Path -LiteralPath $developerShell -PathType Leaf)) { throw 'EXISTING_DEVELOPER_SHELL_REQUIRED' }
$toolSelection = [ordered]@{
    schema = 'licdsf-existing-runner-toolchain-v1'
    image_os = $env:ImageOS
    image_version = $env:ImageVersion
    vswhere_sha256 = (Get-FileHash -LiteralPath $vswhere -Algorithm SHA256).Hash.ToLowerInvariant()
    developer_shell_sha256 = (Get-FileHash -LiteralPath $developerShell -Algorithm SHA256).Hash.ToLowerInvariant()
}
& $developerShell -Arch amd64 -HostArch amd64 -SkipAutomaticLocation
Require-Pins
& (Join-Path $PSScriptRoot 'build_windows.ps1') -OutputDirectory $OutputDirectory
Require-Pins
$toolSelection | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'runner-toolchain.json') -Encoding UTF8
