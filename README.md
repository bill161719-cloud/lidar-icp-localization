# 面向激光 SLAM 的 C++ 点云配准与相对位姿估计系统

`lidar-icp-localization` 面向有 Python、GIS 基础、正在学习 C++ 与 SLAM 的学生，
计划用 PCL ICP 对两帧 LiDAR 点云配准，用 Eigen 分析相对变换，并通过真值实验与少量道路数据验证。
这是点云配准与相对位姿估计工程，不是完整 SLAM 或 FAST-LIO。

**当前阶段：模块 A/B 首轮集成通过。已有“PCD 读取→有限点清理→体素→ICP→质量判断→JSON 位姿”命令行流程。**
固定 PCL 1.15.1、Eigen 3.4.0 和现有 UCRT64 GCC，Release 完整 CTest 8/8（含 9 个真实 CLI 场景）。
已验证人工真值、反向变换、失败拒绝及单个受控噪声/离群点场景；尚无真实道路、GUI 截图或性能基准。
审核、修复、原始日志和人工结果见 [A/B 集成验收](docs/INTEGRATION_AB.md)。
历史记录见 [初始化验证](docs/INITIALIZATION.md)，安装和依赖版本见 [环境记录](docs/ENVIRONMENT.md)。

## 构建最小工程

要求 CMake >=3.20、C++17 编译器、Make 或 Ninja。当前使用已有 MSYS2 UCRT64 GCC，详细环境见
[环境记录](docs/ENVIRONMENT.md)。PowerShell 在仓库根目录运行：

```powershell
# 若系统已有 CMake，可跳过这两行。
python -m pip install --disable-pip-version-check --no-warn-script-location --target .local-tools/python cmake==3.31.6
$env:Path = "$((Resolve-Path .local-tools/python/cmake/data/bin).Path);$env:Path"
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
.\build\lidar_icp.exe --help
.\build\lidar_icp.exe --version
```

Linux 等已有工具链可省略 `-G "MinGW Makefiles"`，运行 `./build/lidar_icp --help`；该平台本次未测试。
默认不需要 PCL/Eigen，仅验证基础构建；bootstrap 测试不证明算法正确性。

## 完整依赖检查

所有库必须匹配编译器、位数、运行时；GCC 不可链接 MSVC 预编译 PCL。
本项目固定 PCL 1.15.1、Eigen 3.4.0，使用 UCRT64 GCC 和匹配的 pacman Boost/FLANN/VTK。
系统 pacman Eigen 5.0.1 与当前 PCL 配置检查不兼容，不能让 CMake 自动选它。
先按环境记录安装依赖包，再使用脚本构建和验证：

```powershell
./tools/build_dependencies.ps1
./tools/verify_dependencies.ps1
```

缺依赖或包版本不匹配应明确失败。脚本只修改当前进程 DLL 搜索路径，完成后恢复，不更改全局配置。
dependency_check 直接调用第三方体素滤波、恒等 ICP 和 VTK 场景构建，不打开渲染窗口；
它不验证 GUI 实际渲染、真实点云精度或模块实现。模块新增所属源文件和测试后，CMake 会自动启用对应库/测试目标。
共享依赖时设置 LIDAR_DEPS_ROOT 或传 -DependencyRoot；CMake 不在 PATH 时可传 -CMake。

## 运行配准与复现集成测试

实际验收命令（配置、Release 编译、完整 CTest；不会重新构建 PCL）：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-integration-ab -Jobs 1
```

测试会在 build-integration-ab/test-pipeline/run-*/ 保存 PCD、真值矩阵、每次 CLI 命令、JSON 报告、stderr 和退出码。
以下命令使用最近生成的实际测试文件，可在主项目根目录运行，无需下载数据：

```powershell
$sampleRun = Get-ChildItem build-integration-ab/test-pipeline -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$savedPath = $env:Path
try {
  $ucrtBin = Split-Path -Parent (Get-Command g++.exe).Source
  $env:Path = "$((Resolve-Path .local-deps/pcl-1.15.1/bin).Path);$ucrtBin;$savedPath"
  ./build-integration-ab/lidar_icp.exe --source (Join-Path $sampleRun.FullName 'source cloud.pcd') --target (Join-Path $sampleRun.FullName 'target cloud.pcd') --initial (Join-Path $sampleRun.FullName 'initial.txt') --truth (Join-Path $sampleRun.FullName 'truth.txt') --voxel-size 0.005 --evaluation-distance 0.03 --max-rmse 0.01
} finally {
  $env:Path = $savedPath
}
```

stdout 为 JSON；处理日志在 stderr。--output <report.json> 可保存报告，已有文件会被拒绝覆盖。
--initial/--truth 是逐行 4×4、无标题的 SE(3) 矩阵；truth 只评分，不参与 ICP。无真值误差输出 null。
可调参数和报告键见 [接口](docs/INTERFACES.md)，--help 列出 CLI 选项。

**消费结果必须检查 accepted。** PCL 的 converged=true 也可能没有内点。
默认要求至少 3 内点、内点率 >=0.5、内点 RMSE <=0.2 m 及合法 SE(3)；阈值需按实验调整。
被拒绝时有效矩阵和 pose 为 null，只保留诊断矩阵。退出码：0 接受；2 输入非法；3 IO/运行错误；4 未收敛或质量拒绝。
质量通过仍可能是局部最优；不能将 source→target 无条件当车辆运动，也不能由人工数据误差宣称实车精度。

## 目录与文档

```text
include/         共享点云类型及未来 A/B 公开头文件
src/             CLI、A/B 实现与 registration_pipeline
tests/           依赖、A/B 单测与 CLI 端到端测试
tools/           未来数据生成与实验脚本
data/sample/     未来可公开小型数据（当前为空）
data/kitti/      本地道路数据（不提交）
results/figures/ 未来真实运行图片（当前为空）
results/metrics/ 未来实验指标（当前为空）
docs/            架构、接口、进度、实验、环境与许可台账
build/           本地构建产物（不提交）
```

开工先读 [AGENTS.md](AGENTS.md)、[需求](docs/PROJECT_SPEC.md)、[架构](docs/ARCHITECTURE.md)、
[接口](docs/INTERFACES.md)、[任务](docs/TASKS.md)、[进度](docs/PROGRESS.md)、[决策](docs/DECISIONS.md)。
实验归档见 [EXPERIMENTS](docs/EXPERIMENTS.md)，许可状态见 [THIRD_PARTY](docs/THIRD_PARTY.md)。

统一方向：`p_target = T_target_source * p_source`，米、弧度、右手系。
ICP 受初值、重叠率、场景退化和动态物体影响，收敛不代表匹配正确。
source 到 target 的坐标变换不能无条件当作车辆实际运动。

## 多对话开发

主对话独占共享 CMake、主程序和总体管理文件，各模块使用独立 worktree。
三个 feature 分支及同级独立 worktree 已创建，分别完成 PCL ON 配置、构建和 CTest 4/4。
启动模块对话时直接打开对应目录，不重复创建 worktree：

```powershell
../lidar-icp-module-a    feature/cloud-processing
../lidar-icp-module-b    feature/icp-registration
../lidar-icp-module-c    feature/experiments
```

各模块先检查分支/状态、读规范，只改自己拥有的文件。交付提交 ID、文件清单、实际测试及遗留问题。
主对话审查与集成后运行完整测试，才标记 DONE；模块不能自己修改共享任务表。
共享依赖验证的正确参数和本机目录见 [WORKTREES](docs/WORKTREES.md)；模块不重新安装 PCL，独占自己的 build-pcl/。

## GitHub 发布流程（尚未执行）

先完成真实模块和验收，确认源码 LICENSE、第三方许可和数据再分发条件；检查 `git status`、
`git diff --check`、待提交文件和历史中的大文件、个人信息、绝对本机路径、缓存及原始数据。
将环境、构建、测试、合法数据获取、真实图片/指标与局限更新到 README。
用户设置自己的 Git 作者信息并明确批准公开发布后，再在 GitHub 创建空仓库并运行：

```powershell
git remote add origin <approved-repository-url>
git push -u origin main
```

目前未创建远程仓库、未推送；许可证待确认，本仓库当前不是已完成的开源交付。
