# 本地环境与依赖方案

检查日期：2026-10-27（Asia/Shanghai）。本机绝对路径只存在本地配置/日志，不写入公共构建配置。

| 项目 | 实际检查结果 |
|---|---|
| OS | Windows build 26200.9711，25H2，64 位；版本号对应 Windows 11，旧注册表 ProductName 仍写 Windows 10 Home China |
| 编译器 | MSYS2 UCRT64 GCC 16.2.0（Rev6），target x86_64-w64-mingw32 |
| C++17 | 已以 -std=c++17 编译 static_assert、std::optional、std::string_view，通过 |
| Git | 2.55.0.windows.5；未配置 user.name / user.email |
| Make | mingw32-make 已存在，包记录 4.4.1-5 |
| CMake / CTest | 初始未发现；已安装项目内 3.31.6，配置/编译/3 项 CTest 通过 |
| PCL | pacman 当前 UCRT64 数据库未提供包；PCL 1.15.1 已用现有 GCC 源码构建、安装并通过项目依赖检查 |
| Eigen | pacman Eigen 5.0.1-1 已安装；项目实际固定 Eigen 3.4.0，详见下文 |
| MSVC | cl/vswhere 未发现；存在旧 Visual Studio 目录不等于可用 C++ 工具链 |
| 依赖管理 | MSYS2 pacman 已安装；Python 3.11/pip 26.0.1 可用；winget 可执行文件存在但未验证服务；vcpkg/conda 未发现 |
| 物理内存 | 16,890,716,160 字节（15.73 GiB），检查时可用约 3.84 GiB，属动态值 |
| 磁盘 | 检查时 C 盘约 79.31 GiB 可用，D 盘约 486.63 GiB 可用 |

Get-CimInstance 被环境拒绝，使用 RuntimeInformation/注册表和 GlobalMemoryStatusEx 交叉读取。
没有修改全局 PATH、未升级 GCC 或 MSYS2、未替换工具链。初始缺失依赖的状态见 INITIALIZATION.md；下文记录本次依赖配置。

## 先安装最小构建工具

在项目根目录 PowerShell 执行（需要网络；本地目录已被 Git 忽略）：

```powershell
python -m pip install --disable-pip-version-check --no-warn-script-location --target .local-tools/python cmake==3.31.6
$env:Path = "$((Resolve-Path .local-tools/python/cmake/data/bin).Path);$env:Path"
cmake --version
```

此 wheel 的 CMake 是构建工具，不是用来链接的 MSVC C++ 库，可用 MinGW Makefiles 生成器调用已有 GCC。

## 2026-10-27：实际依赖配置

仓库根目录用 `$Repo` 表示；默认依赖根 `$Repo/.local-deps`。本机 MSYS2 根为 `C:/msys64`。
pacman 6.1.0-25 在受控权限执行时可用；原沙箱内 MSYS 命名对象受限，不是 pacman 安装损坏。
使用本机 2026-10-22 的 UCRT64 同步库查询和安装，未运行系统升级、未更换 GCC。

实际查询：`pacman -Q`、`pacman -Si <包名>`、`pacman -Ss pcl`、`pacman -Sp --needed <包名>`。
`-Ss pcl` 只命中 Python pipcl，无 Point Cloud Library 包；不能用 PDAL 替代 PCL。

实际安装命令（在有权限的终端调用既有 pacman）：

```powershell
& C:/msys64/usr/bin/pacman.exe -S --needed --noconfirm mingw-w64-ucrt-x86_64-eigen3
& C:/msys64/usr/bin/pacman.exe -S --needed --noconfirm mingw-w64-ucrt-x86_64-boost mingw-w64-ucrt-x86_64-flann mingw-w64-ucrt-x86_64-vtk
& C:/msys64/usr/bin/pacman.exe -S --needed --noconfirm mingw-w64-ucrt-x86_64-nlohmann-json mingw-w64-ucrt-x86_64-exprtk mingw-w64-ucrt-x86_64-utf8cpp mingw-w64-ucrt-x86_64-cjson
```

共新增 45 个包（Eigen 1 个、主要依赖及传递依赖 40 个、补充头文件/cJSON 4 个），pacman 校验签名和完整性。
主要依赖组下载计划 140.21 MiB、安装体积 1203.54 MiB，另有小型头文件包；均为实际 pacman 输出。

| 依赖 | 来源与版本 | 安装位置 |
|---|---|---|
| 系统 Eigen | UCRT64 eigen3 5.0.1-1 | C:/msys64/ucrt64/include/eigen3；share/eigen3/cmake |
| 项目 Eigen | 官方 GitLab tag 3.4.0，commit 3147391d946bb4b6c68edd901f2add6ac1f31f8c；只安装头文件与 CMake 配置 | $Repo/.local-deps/eigen-3.4.0 |
| PCL | 官方 GitHub tag pcl-1.15.1，commit 3346843ea6b97697a1577293aa9cdf236b5c7ffb；同一 GCC 源码构建，带下述 VTK 发现补丁 | $Repo/.local-deps/pcl-1.15.1；配置 share/pcl-1.15/PCLConfig.cmake |
| Boost | UCRT64 1.92.0-4，动态链接 | C:/msys64/ucrt64 |
| FLANN | UCRT64 1.9.2-2 | C:/msys64/ucrt64 |
| VTK | UCRT64 9.6.2-8，OpenGL2 | C:/msys64/ucrt64；配置 lib/cmake/vtk |
| cJSON | UCRT64 1.7.19-1 | C:/msys64/ucrt64 |
| nlohmann-json / ExprTk / utf8cpp | UCRT64 3.12.0-1 / 0.0.3-1 / 4.2.1-1 | C:/msys64/ucrt64 |

Eigen 5.0.1 的 Eigen3ConfigVersion.cmake 实际拒绝 `find_package(Eigen3 3.3)`，已运行失败验证。
不绕过版本检查或覆盖系统包；项目和 PCL 均显式设置 Eigen3_DIR 到独立 3.4.0 前缀。
VTK 内部使用何种数学库不改变项目公开 Eigen 接口，禁止消费者意外选回系统 Eigen 5。

## 方案成本与选择

| 方案 | 实际成本和限制 | 决策 |
|---|---|---|
| 现有 GCC + UCRT64 依赖 + PCL 源码 | 复用 VTK 等预编译库；只编译 PCL；需要固定配置和小型构建发现补丁 | 本次选用并实际构建 |
| vcpkg MinGW triplet | 仍需 GCC 源码构建 PCL/VTK；MinGW 为社区维护配置，并非所有 port 均受 CI 验证 | 无明显成本收益，不引入第二套库管理 |
| MSVC + vcpkg/PCL 预编译 | 常见 Windows 路线，但需要新增编译器与独立库体系，不能和现有 GCC ABI 混用 | 未获准变更工具链，不执行 |
| WSL/Linux | 需另一套环境及编译器；不能作为当前 Windows GCC 的依赖 | 本次不执行 |

## 可复现构建与验证

`tools/dependency_sources.json` 锁定两个源码提交；`tools/dependencies-msys2.lock.json` 记录 54 个新增/关键基线包的版本、下载 URL 和本机缓存 SHA256。
其中 45 个是新增依赖，9 个是保留的编译器/运行时等关键包。该清单不是完整系统快照。
滚动仓库将来可能移除旧包；重新安装前核查可下载性和签名，不能承诺旧 URL 永久有效。
脚本检查已安装版本，发现漂移就失败；本次实际安装的包缓存仍保留在 MSYS2 中。

PCL 配置使用 C++17、Release、共享库、Boost 动态链接、核心点类型；禁用 CUDA、Qt、相机驱动、QHull 和无关子系统。
保留 common/io/filters/registration/visualization 及必要的 kdtree/octree/search/sample_consensus/features/2d/geometry。
关闭额外 SSE/AVX 探测，保持默认 x86_64 指令集；不启用 march=native。
若修改向量化配置，必须重新探测 PCL_USES_EIGEN_HANDMADE_ALIGNED_MALLOC，防止旧缓存造成对齐 ABI 不一致。

`tools/prepare_pcl_source.py` 只修正 PCL 的 VTK CMake 发现：请求所需模块、遵守 WITH_QT=NO，
不修改算法源码、不安装无关 Qt/VR 后端。脚本可重复执行且检查原始内容是否符合预期。

以下脚本已经实际执行通过：

```powershell
# 先具备清单中的 UCRT64 包；脚本不会升级系统或自动调用 pacman。
./tools/build_dependencies.ps1
./tools/verify_dependencies.ps1
# 在全新目录再次验证，排除之前失败配置的缓存影响。
./tools/verify_dependencies.ps1 -BuildDirectory build-pcl-clean
```

可通过 -MsysRoot、-CMake、-DependencyRoot 显式指定位置；后者也可用环境变量 LIDAR_DEPS_ROOT。
验证脚本只修改自身进程的 PATH，结束后恢复，确保运行时加载 PCL bin 和 UCRT64 bin 的 DLL。
后续 worktree 可复用主目录依赖，传入 -DependencyRoot 和 -CMake，无需复制库或修改共享源码。

## 实际验证结果

| 操作 | 结果 |
|---|---|
| pacman 安装与版本比较 | 45 个新增包，已有包版本变化 0，GCC 保留 16.2.0-6 |
| verify_msys2_packages.py | 54 个记录版本全部匹配 |
| PCL 源码配置、Release 编译 | 退出 0，所选组件全部完成 |
| build_dependencies.ps1 | 退出 0；源码 commit 检查、包版本检查、配置/构建/安装均成功 |
| verify_dependencies.ps1 | PCL ON 配置/构建退出 0，CTest 4/4 通过，直接运行检查程序退出 0 |
| 全新 build-pcl-clean | 配置/编译成功，CTest 4/4 通过，直接运行退出 0 |
| 依赖程序输出 | PCL 1.15.1; Eigen 3.4.0; filter/ICP/VTK scene OK (no render) |
| 头文件/编译器确认 | 实际响应文件仅指向项目 Eigen 3.4.0；C++17、UCRT64 c++.exe，无系统 Eigen 5 头文件路径混入 |

4 项 CTest：bootstrap_help、bootstrap_version、bootstrap_rejects_unknown、dependency_check。
检查程序实际调用 PCL VoxelGrid、恒等 ICP，并构造 PCLVisualizer/点云场景但不 Render/spin。
这验证了所需 API、链接、DLL 和基础执行，不代表完整 GUI 渲染、道路实验或全部第三方 API 已验证。

日志（不提交）：build/pcl-source-configure.log、build/pcl-source-build.log、build/dependency-bootstrap.log、
build/dependency-verify.log、build/dependency-clean-verify.log；CTest 原始记录位于两个构建目录的 Testing/Temporary/。
初次手动构建后执行脚本会增量复用已编译依赖；全新目录复验的是项目本身，未声称二次全量重编 PCL。

保留的诊断：PCL/Eigen/Boost 源码在 GCC 16 的 Release 优化下有 array-bounds、maybe-uninitialized、
Windows 宏重复、整数比较以及 OpenMP/VTK 弃用警告。未屏蔽，也未据此宣称全部第三方代码正确。
Eigen 3.4 CMake 的可选 git ls-remote 修订号探测还会触发沙箱 MSYS 命名对象错误；
该探测不决定安装成功与否，脚本另用 git rev-parse 核实固定 commit，配置/安装退出码为 0。
PCL 对齐探测显示 Failed 是预期分支：最终 PCL_USES_EIGEN_HANDMADE_ALIGNED_MALLOC=0，与消费者一致，
不是构建失败；初始对齐警告已通过重新探测消除。

依据：[MSYS2 环境](https://www.msys2.org/docs/environments/)、
[MSYS2 Eigen 包](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-eigen3)、
[PCL Windows 源码构建及编译器兼容要求](https://pointclouds.org/documentation/tutorials/compiling_pcl_windows.html)。
vcpkg 评估依据：[MinGW 平台支持范围](https://learn.microsoft.com/en-us/vcpkg/users/platforms/mingw)。

## A/B 首轮集成后的验证状态

以上 4/4 为依赖准备阶段的历史结果。A/B 集成后已完成 Release 完整 CTest 8/8，含 9 个 CLI 端到端场景；
最小 PCL OFF 模式另有 3/3 回归通过。依赖版本、安装前缀、GCC 和对齐设置未改变。
test_pipeline 使用 Python >=3.9 的标准库驱动真实 C++ 进程，不依赖 Python PCL 绑定或第三方 Python 包。
JSON 与日志、具体数值及警告分析见 INTEGRATION_AB.md；不将人工 smoke check 当真实道路验收。

## 模块 C 集成后（2026-10-27）

全新 build-final-c Release 构建成功，接入离线工具与损坏检测后完整CTest10/10。
CPython3.11.5 + NumPy2.4.4 + Matplotlib3.10.8 已有环境实际执行35组实验并重绘六图，未新装包或更换编译器。
绘图可选版本锁在 tools/requirements-experiments.txt，普通CTest无需这些包或KITTI原始数据。
main独立数据获取/转换、42输入哈希、35报告与六图复验记录见 EXPERIMENTS.md 和 results/metrics/main-review。
