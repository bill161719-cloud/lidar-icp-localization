param(
    [int]$Port = 8765,
    [string]$BuildDirectory = 'build-release-ready',
    [string]$DependencyRoot = '',
    [string]$MsysRoot = 'C:/msys64',
    [switch]$OpenBrowser
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not [System.IO.Path]::IsPathRooted($BuildDirectory)) {
    $BuildDirectory = Join-Path $projectRoot $BuildDirectory
}
if (-not $DependencyRoot) { $DependencyRoot = Join-Path $projectRoot '.local-deps' }
$binary = Join-Path $BuildDirectory 'lidar_icp.exe'
if (-not (Test-Path -LiteralPath $binary)) {
    throw 'Missing lidar_icp.exe. Run tools/verify_dependencies.ps1 first.'
}
$demoArgs = @((Join-Path $projectRoot 'web_demo/server.py'), '--port', "$Port",
    '--binary', $binary, '--dependency-root', $DependencyRoot, '--msys-root', $MsysRoot)
if ($OpenBrowser) { $demoArgs += '--open-browser' }
& python @demoArgs
exit $LASTEXITCODE
