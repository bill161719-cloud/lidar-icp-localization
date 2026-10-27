param(
    [string]$DependencyRoot = $env:LIDAR_DEPS_ROOT,
    [string]$MsysRoot = $env:MSYS2_ROOT,
    [string]$CMake = '',
    [string]$BuildDirectory = 'build-pcl',
    [ValidateRange(1, 8)][int]$Jobs = 2
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $DependencyRoot) { $DependencyRoot = Join-Path $projectRoot '.local-deps' }
$DependencyRoot = (Resolve-Path -LiteralPath $DependencyRoot).Path.Replace('\', '/')
if (-not $MsysRoot) {
    $gccBin = Split-Path -Parent (Get-Command g++.exe -ErrorAction Stop).Source
    if ((Split-Path -Leaf (Split-Path -Parent $gccBin)) -ne 'ucrt64') {
        throw 'Expected MSYS2 UCRT64 GCC on PATH. Set -MsysRoot explicitly.'
    }
    $MsysRoot = Split-Path -Parent (Split-Path -Parent $gccBin)
}
if (-not $CMake) {
    $CMake = Join-Path $projectRoot '.local-tools/python/cmake/data/bin/cmake.exe'
    if (-not (Test-Path -LiteralPath $CMake)) { $CMake = (Get-Command cmake.exe).Source }
}
$CMake = (Resolve-Path -LiteralPath $CMake).Path
$ctest = Join-Path (Split-Path -Parent $CMake) 'ctest.exe'
if (-not [System.IO.Path]::IsPathRooted($BuildDirectory)) {
    $BuildDirectory = Join-Path $projectRoot $BuildDirectory
}
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
$savedPath = $env:Path
try {
    $ucrtPrefix = (Join-Path $MsysRoot 'ucrt64').Replace('\', '/')
    $pclPrefix = "$DependencyRoot/pcl-1.15.1"
    $env:Path = "$pclPrefix/bin;$(Join-Path $ucrtPrefix 'bin');$savedPath"
    Invoke-Checked 'python' @((Join-Path $PSScriptRoot 'verify_msys2_packages.py'), $MsysRoot)
    Invoke-Checked $CMake @('-S', $projectRoot, '-B', $BuildDirectory, '-G', 'MinGW Makefiles',
        "-DCMAKE_C_COMPILER=$ucrtPrefix/bin/cc.exe", "-DCMAKE_CXX_COMPILER=$ucrtPrefix/bin/c++.exe",
        '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_TESTING=ON', '-DLIDAR_ENABLE_PCL=ON', '-DLIDAR_REQUIRE_VALIDATED_VERSIONS=ON',
        "-DEigen3_DIR=$DependencyRoot/eigen-3.4.0/share/eigen3/cmake",
        "-DCMAKE_PREFIX_PATH=$pclPrefix;$ucrtPrefix")
    Invoke-Checked $CMake @('--build', $BuildDirectory, '--parallel', "$Jobs")
    Invoke-Checked $ctest @('--test-dir', $BuildDirectory, '--output-on-failure')
    Invoke-Checked (Join-Path $BuildDirectory 'lidar_dependency_check.exe') @()
} finally {
    $env:Path = $savedPath
}
