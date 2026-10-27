# 模块 Worktree 启动约定

本机主目录为 `D:/CodexProgects/lidar-icp-localization`，三个模块使用同级独立目录，不嵌套工作树。
本文件由主对话维护；实际验证结果以 PROGRESS.md 为准。

| 模块 | 目录 | 已有分支 | 负责范围 |
|---|---|---|---|
| A | D:/CodexProgects/lidar-icp-module-a | feature/cloud-processing | cloud_processor 头文件、实现和所属测试 |
| B | D:/CodexProgects/lidar-icp-module-b | feature/icp-registration | pose_utils、icp_registration 头文件、实现和所属测试 |
| C | D:/CodexProgects/lidar-icp-module-c | feature/experiments | generate_test_data、独立实验代码、results、EXPERIMENTS.md |

创建前主对话检查了 main 工作区干净、三个分支精确指向 015a535；接口和构建入口准备提交后统一快进。
各分支保留 015a535 与 88279bf 历史，不重新建分支、不改写已有提交。
不要在主目录或其他模块目录切换分支；不要复制整个 .git 或依赖目录。

## 在各自目录运行

在 Codex 中分别打开上表的文件夹。先读 AGENTS.md、README.md、docs/PROJECT_SPEC.md、
ARCHITECTURE.md、INTERFACES.md、TASKS.md、PROGRESS.md、ENVIRONMENT.md（后六项在 docs/）。

```powershell
git status --short --branch
git log -3 --oneline
# Git common-dir 指向主目录的 .git；不依赖当前目录名称猜测依赖位置。
$sharedRoot = Split-Path -Parent ((git rev-parse --path-format=absolute --git-common-dir).Trim())
./tools/verify_dependencies.ps1 `
  -DependencyRoot (Join-Path $sharedRoot '.local-deps') `
  -CMake (Join-Path $sharedRoot '.local-tools/python/cmake/data/bin/cmake.exe') `
  -Jobs 1
```

脚本从自身位置确定所属 worktree 源码目录，每棵树独立使用 build-pcl/，只从主目录读取 PCL/Eigen。
PCL_DIR 最终必须指向主目录 `.local-deps/pcl-1.15.1/share/pcl-1.15`；
Eigen3_DIR 必须指向主目录 `.local-deps/eigen-3.4.0/share/eigen3/cmake`，不能自动选系统 Eigen 5。
运行时 PATH 由脚本临时加入共享 PCL bin 和 UCRT64 bin，脚本结束恢复，不修改全局 PATH。
各模块不下载或重新构建 PCL；共享依赖仅由主对话维护。内存紧张时不要同时启动三轮编译。

初始应有 4 项 bootstrap/依赖测试全部通过，依赖程序输出 PCL 1.15.1、Eigen 3.4.0。
这不代表模块算法完成；添加实现和测试后重跑同一脚本，CMake 自动启用 INTERFACES.md 指定目标。

## 文件边界与验收

- A：仅修改 include/cloud_processor.h、src/cloud_processor.cpp、tests/test_cloud_processor.cpp；验收 PCD/无效输入/NaN/Inf/体素参数与点数。
- B：仅修改 include/icp_registration.h、src/icp_registration.cpp、include/pose_utils.h、src/pose_utils.cpp、tests/test_icp.cpp、tests/test_pose.cpp；先 B01 后 B02，验收 SE(3)、已知真值、初值、失败和误差指标。
- C：修改 tools/generate_test_data.cpp、独立实验代码、results 和 docs/EXPERIMENTS.md；数据源/许可和生成器契约依接口，完整实验等待集成。
- 主对话独占 CMakeLists.txt、主程序、共享类型、总体管理文档和 Git 集成；模块提出跨边界建议，不直接修改。

模块实现提交必须附任务编号、文件清单、分支/提交、实际构建与测试结果、遗留问题。
模块不得修改 TASKS/PROGRESS 自行标 DONE；主对话审核与完整测试后更新状态。
模块代码和实验尚未开始，只有环境准备可标 DONE。
