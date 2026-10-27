param(
    [string]$DependencyRoot = $env:LIDAR_DEPS_ROOT,
    [string]$MsysRoot = $env:MSYS2_ROOT,
    [string]$CMake = '',
    [ValidateRange(1, 8)][int]$Jobs = 2
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $DependencyRoot) { $DependencyRoot = Join-Path $projectRoot '.local-deps' }
if (-not $MsysRoot) {
    $gccBin = Split-Path -Parent (Get-Command g++.exe -ErrorAction Stop).Source
    if ((Split-Path -Leaf (Split-Path -Parent $gccBin)) -ne 'ucrt64') {
        throw 'Expected the existing MSYS2 UCRT64 GCC on PATH. Set -MsysRoot explicitly.'
    }
    $MsysRoot = Split-Path -Parent (Split-Path -Parent $gccBin)
}
if (-not $CMake) {
    $CMake = Join-Path $projectRoot '.local-tools/python/cmake/data/bin/cmake.exe'
    if (-not (Test-Path -LiteralPath $CMake)) { $CMake = (Get-Command cmake.exe).Source }
}
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
$savedPath = $env:Path
try {
    $ucrtPrefix = (Join-Path $MsysRoot 'ucrt64').Replace('\', '/')
    $env:Path = "$(Join-Path $ucrtPrefix 'bin');$savedPath"
    Invoke-Checked 'python' @((Join-Path $PSScriptRoot 'verify_msys2_packages.py'), $MsysRoot)
    New-Item -ItemType Directory -Path $DependencyRoot -Force | Out-Null
    $DependencyRoot = (Resolve-Path -LiteralPath $DependencyRoot).Path.Replace('\', '/')
    $pins = Get-Content (Join-Path $PSScriptRoot 'dependency_sources.json') -Raw | ConvertFrom-Json
    foreach ($component in @('eigen', 'pcl')) {
        $pin = $pins.$component
        $version = if ($component -eq 'eigen') { '3.4.0' } else { '1.15.1' }
        $source = "$DependencyRoot/src/$component-$version"
        if (-not (Test-Path -LiteralPath $source)) {
            Invoke-Checked 'git' @('clone', '--depth', '1', '--branch', $pin.tag, $pin.url, $source)
        }
        $actual = & git -C $source rev-parse HEAD
        if ($LASTEXITCODE -ne 0 -or $actual -ne $pin.commit) { throw "Unexpected $component revision: $actual" }
    }
    $eigenSource = "$DependencyRoot/src/eigen-3.4.0"
    $eigenBuild = "$DependencyRoot/build/eigen-3.4.0"
    $eigenPrefix = "$DependencyRoot/eigen-3.4.0"
    Invoke-Checked $CMake @('-S', $eigenSource, '-B', $eigenBuild, '-G', 'MinGW Makefiles',
        "-DCMAKE_C_COMPILER=$ucrtPrefix/bin/cc.exe", "-DCMAKE_CXX_COMPILER=$ucrtPrefix/bin/c++.exe",
        '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_TESTING=OFF', '-DEIGEN_BUILD_DOC=OFF',
        '-DCMAKE_EXPORT_NO_PACKAGE_REGISTRY=ON', "-DCMAKE_INSTALL_PREFIX=$eigenPrefix")
    Invoke-Checked $CMake @('--install', $eigenBuild)
    $pclSource = "$DependencyRoot/src/pcl-1.15.1"
    $pclBuild = "$DependencyRoot/build/pcl-1.15.1"
    Invoke-Checked 'python' @((Join-Path $PSScriptRoot 'prepare_pcl_source.py'), $pclSource)
    $configure = @('-S', $pclSource, '-B', $pclBuild, '-G', 'MinGW Makefiles',
        "-DCMAKE_C_COMPILER=$ucrtPrefix/bin/cc.exe", "-DCMAKE_CXX_COMPILER=$ucrtPrefix/bin/c++.exe",
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_STANDARD=17',
        "-DCMAKE_INSTALL_PREFIX=$DependencyRoot/pcl-1.15.1",
        "-DEigen3_DIR=$eigenPrefix/share/eigen3/cmake", "-DCMAKE_PREFIX_PATH=$ucrtPrefix",
        '-DPCL_ONLY_CORE_POINT_TYPES=ON', '-DPCL_BUILD_WITH_BOOST_DYNAMIC_LINKING_WIN32=ON',
        '-DPCL_ALLOW_BOTH_SHARED_AND_STATIC_DEPENDENCIES=ON',
        '-DPCL_ENABLE_SSE=OFF', '-DPCL_ENABLE_AVX=OFF', '-UPCL_USES_EIGEN_HANDMADE_ALIGNED_MALLOC',
        '-DWITH_CUDA=OFF', '-DWITH_OPENNI=OFF', '-DWITH_OPENNI2=OFF', '-DWITH_QHULL=OFF',
        '-DWITH_LIBUSB=OFF', '-DWITH_PCAP=OFF', '-DWITH_QT=NO', '-DWITH_VTK=ON', '-DWITH_OPENGL=ON')
    foreach ($component in @('apps', 'examples', 'tools', 'global_tests', 'surface', 'keypoints',
        'tracking', 'segmentation', 'recognition', 'stereo', 'people', 'outofcore', 'simulation', 'ml')) {
        $configure += "-DBUILD_$component=OFF"
    }
    foreach ($component in @('common', 'io', 'filters', 'registration', 'visualization', 'features', '2d')) {
        $configure += "-DBUILD_$component=ON"
    }
    Invoke-Checked $CMake $configure
    Invoke-Checked $CMake @('--build', $pclBuild, '--parallel', "$Jobs")
    Invoke-Checked $CMake @('--install', $pclBuild)
} finally {
    $env:Path = $savedPath
}
