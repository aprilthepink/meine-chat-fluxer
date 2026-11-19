param(
    [Parameter(Mandatory)][ValidateSet('pdl', 'ljs')][string]$Context,
    [string]$Repository = '',
    [string]$Commit = '',
    [string]$Version = ''
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Invoke-Native {
    param([string]$FilePath, [string[]]$ArgumentList = @())
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) { throw "$FilePath failed with exit code $LASTEXITCODE" }
}

$source = 'C:\b\src'
$output = 'C:\b\out'
New-Item -ItemType Directory -Force -Path $source, $output, 'C:\t', 'C:\ebcache' | Out-Null
if ($Repository) {
    Invoke-Native git.exe @('-C', $source, 'init', '--quiet')
    Invoke-Native git.exe @('-C', $source, 'config', 'core.eol', 'lf')
    Invoke-Native git.exe @('-C', $source, '-c', 'credential.helper=', 'fetch', '--quiet', '--depth', '1', $Repository, $Commit)
    Invoke-Native git.exe @('-C', $source, 'checkout', '--quiet', 'FETCH_HEAD')
} elseif (-not (Test-Path (Join-Path $source 'whitelabel'))) {
    throw "no -Repository given and no source in $source"
}

if (-not (Test-Path 'W:\')) { Invoke-Native subst.exe @('W:', $source) }
Set-Location 'W:\'
$env:TEMP = 'C:\t'
$env:TMP = 'C:\t'
$env:ELECTRON_BUILDER_CACHE = 'C:\ebcache'
$env:ELECTRON_ARCH = 'x64'
$env:BUILD_VERSION = $Version
$env:CI = 'true'
$env:pnpm_config_script_shell = 'C:\Program Files\Git\bin\bash.exe'

Import-Module 'C:\BuildTools\Common7\Tools\Microsoft.VisualStudio.DevShell.dll'
Enter-VsDevShell -VsInstallPath 'C:\BuildTools' -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
Set-Location 'W:\'

Invoke-Native pnpm.cmd @('install', '--frozen-lockfile')
Invoke-Native 'C:\Program Files\Git\bin\bash.exe' @('whitelabel/desktop/build.sh', $Context, '--win', '--x64')

$unpacked = Get-ChildItem -Directory -Path 'fluxer_desktop\dist-electron' -Filter 'win-*unpacked' | Select-Object -First 1
if (-not $unpacked) { throw 'electron-builder produced no win-unpacked directory' }
$name = "meine-$Context-windows-x64$(if ($Version) { "-$Version" }).zip"
Invoke-Native tar.exe @('-a', '-c', '-f', (Join-Path $output $name), '-C', $unpacked.FullName, '.')
Get-ChildItem $output | ForEach-Object { "{0} {1:N0} MB" -f $_.Name, ($_.Length / 1MB) }
