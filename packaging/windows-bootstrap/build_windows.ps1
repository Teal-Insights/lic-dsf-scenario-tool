# Local-only recipe for an ALREADY INSTALLED x64 MSVC/Windows SDK environment.
# No install, login, network, signing, package-copy or publication operation.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or $env:VSCMD_ARG_TGT_ARCH -ne 'x64') { throw 'EXISTING_X64_MSVC_DEVELOPER_ENVIRONMENT_REQUIRED' }
if ([string]::IsNullOrWhiteSpace($env:VCToolsInstallDir) -or [string]::IsNullOrWhiteSpace($env:WindowsSDKVersion)) { throw 'EXISTING_MSVC_AND_SDK_REQUIRED' }
foreach ($name in @('CL', '_CL_', 'LINK', '_LINK_')) {
    if (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) { throw 'UNEXPECTED_TOOL_OPTIONS' }
}
$sdkVersion = $env:WindowsSDKVersion.TrimEnd('\')
if ([Version]$sdkVersion -lt [Version]'10.0.20348.0') { throw 'C17_SDK_TOO_OLD' }
$compiler = Get-Command cl.exe -CommandType Application
$dumpbin = Get-Command dumpbin.exe -CommandType Application
$toolRoot = [IO.Path]::GetFullPath($env:VCToolsInstallDir).TrimEnd('\') + '\'
if (-not $compiler.Source.StartsWith($toolRoot, [StringComparison]::OrdinalIgnoreCase) -or -not $dumpbin.Source.StartsWith($toolRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'TOOL_ORIGIN_OUTSIDE_SELECTED_MSVC' }
$out = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $out) { throw 'OUTPUT_DIRECTORY_ALREADY_EXISTS' }
$sources = @('launcher_win.c', 'launcher_plan.c', 'launcher_plan.h')
$sourcePins = @{}
foreach ($name in $sources) { $sourcePins[$name] = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name) -Algorithm SHA256).Hash.ToLowerInvariant() }
$compilerHash = (Get-FileHash -LiteralPath $compiler.Source -Algorithm SHA256).Hash.ToLowerInvariant()
$dumpbinHash = (Get-FileHash -LiteralPath $dumpbin.Source -Algorithm SHA256).Hash.ToLowerInvariant()
New-Item -ItemType Directory -Path $out | Out-Null
Push-Location -LiteralPath $out
try {
    $arguments = @('/nologo', '/TC', '/std:c17', '/W4', '/WX', '/O2', '/MT', '/utf-8', '/DUNICODE', '/D_UNICODE', '/Fe:launcher.exe', (Join-Path $PSScriptRoot 'launcher_win.c'), (Join-Path $PSScriptRoot 'launcher_plan.c'), '/link', '/MACHINE:X64', '/SUBSYSTEM:CONSOLE')
    & $compiler.Source @arguments *> 'compiler.log'
    if ($LASTEXITCODE -ne 0) { throw 'NATIVE_BUILD_FAILED_OUTPUT_RETAINED' }
    foreach ($name in $sources) { if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sourcePins[$name]) { throw 'SOURCE_CHANGED_DURING_BUILD' } }
    $raw = [IO.File]::ReadAllBytes((Join-Path $out 'launcher.exe'))
    if ($raw.Length -lt 512 -or $raw[0] -ne 77 -or $raw[1] -ne 90) { throw 'BUILD_OUTPUT_NOT_PE' }
    $pe = [BitConverter]::ToUInt32($raw, 60)
    if ($pe + 264 -gt $raw.Length -or [BitConverter]::ToUInt32($raw, $pe) -ne 17744 -or [BitConverter]::ToUInt16($raw, $pe + 4) -ne 34404 -or [BitConverter]::ToUInt16($raw, $pe + 24) -ne 523 -or [BitConverter]::ToUInt16($raw, $pe + 24 + 68) -ne 3) { throw 'BUILD_OUTPUT_NOT_X64_CONSOLE_PE' }
    if ([BitConverter]::ToUInt32($raw, $pe + 24 + 144) -ne 0 -or [BitConverter]::ToUInt32($raw, $pe + 24 + 148) -ne 0) { throw 'UNEXPECTED_PREEXISTING_SIGNATURE' }
    & $dumpbin.Source /DEPENDENTS launcher.exe *> 'dependencies.log'
    if ($LASTEXITCODE -ne 0) { throw 'DEPENDENCY_INSPECTION_FAILED' }
    & $dumpbin.Source /HEADERS launcher.exe *> 'headers.log'
    if ($LASTEXITCODE -ne 0) { throw 'HEADER_INSPECTION_FAILED' }
    Rename-Item -LiteralPath 'launcher.exe' -NewName 'Start LIC-DSF.exe'
    [ordered]@{
        schema = 'licdsf-unsigned-launcher-build-v1'
        status = 'NATIVE_UNSIGNED_BUILD_PENDING_ARTIFACT_REVIEW_AND_PROCESS_ACCEPTANCE'
        executable_sha256 = (Get-FileHash -LiteralPath 'Start LIC-DSF.exe' -Algorithm SHA256).Hash.ToLowerInvariant()
        source_sha256 = $sourcePins
        compiler_sha256 = $compilerHash
        compiler_version = $compiler.Version.ToString()
        dumpbin_sha256 = $dumpbinHash
        windows_sdk_version = $sdkVersion
        target = 'x64 console'
        runtime_link = 'MT static CRT'
        signed = $false
        native_process_tested = $false
        windows_first_launch_accepted = $false
        package_integrated = $false
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath 'unsigned-build-receipt.json' -Encoding UTF8
} finally { Pop-Location }
