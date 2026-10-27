# 面向激光 SLAM 的 C++ 点云配准与相对位姿估计系统

`lidar-icp-localization` 面向有 Python、GIS 基础、正在学习 C++ 与 SLAM 的学生，
计划用 PCL ICP 对两帧 LiDAR 点云配准，用 Eigen 分析相对变换，并通过真值实验与少量道路数据验证。
这是点云配准与相对位姿估计工程，不是完整 SLAM 或 FAST-LIO。

**当前阶段：初始化骨架。只有 C++17 bootstrap CLI，尚未实现点云读取、ICP、可视化或真实道路实验。**
数值精度、截图与算法性能尚无结果。PCL/Eigen 安装是后续编译模块的前置条件。
本机已实际完成 Release 构建和 3/3 bootstrap 测试；PCL ON 配置因缺 Eigen3 失败。
详细命令与结果见 [初始化验证](docs/INITIALIZATION.md)。

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

## 完整依赖检查（安装 PCL/Eigen 后）

所有库必须匹配编译器、位数、运行时；GCC 不可链接 MSVC 预编译 PCL。
在本地设置包含同工具链安装前缀的 `LIDAR_DEPS_PREFIX` 后执行：

```powershell
cmake -S . -B build-pcl -G "MinGW Makefiles" -DLIDAR_ENABLE_PCL=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$env:LIDAR_DEPS_PREFIX"
cmake --build build-pcl --parallel 2
ctest --test-dir build-pcl --output-on-failure
```

缺依赖应明确配置失败。当前 dependency_check 仅检查头文件、基础链接和实例化，
不验证 GUI 窗口或完整算法。模块实现后主对话将接入库目标和功能测试。

## 目录与文档

```text
include/         共享点云类型及未来 A/B 公开头文件
src/             bootstrap 主程序及未来模块实现
tests/           CTest 与依赖检查；未来数值/错误处理测试
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
基础提交后主对话建立三个 feature 分支；用户启动模块对话前可在根目录执行以下命令。
这些命令创建同级目录，需要相应写入权限；本次初始化只创建分支，不创建 worktree 或启动模块。

```powershell
git worktree add ../lidar-icp-module-a feature/cloud-processing
git worktree add ../lidar-icp-module-b feature/icp-registration
git worktree add ../lidar-icp-module-c feature/experiments
```

各模块先检查分支/状态、读规范，只改自己拥有的文件。交付提交 ID、文件清单、实际测试及遗留问题。
主对话审查与集成后运行完整测试，才标记 DONE；模块不能自己修改共享任务表。

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
