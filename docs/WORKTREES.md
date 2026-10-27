# 模块 Worktree 启动约定

主目录以 `<workspace>/lidar-icp-localization` 表示，三个模块使用同级独立目录，不嵌套工作树。
公开文档使用相对位置，当前机器上的真实映射用 `git worktree list` 查询；此处不要求固定磁盘或用户名。
本文件由主对话维护；实际验证结果以 PROGRESS.md 为准。

| 模块 | 目录 | 已有分支 | 负责范围 |
|---|---|---|---|
| A | ../lidar-icp-module-a | feature/cloud-processing | cloud_processor 头文件、实现和所属测试 |
| B | ../lidar-icp-module-b | feature/icp-registration | pose_utils、icp_registration 头文件、实现和所属测试 |
| C | ../lidar-icp-module-c | feature/experiments | generate_test_data、独立实验代码、results、EXPERIMENTS.md |

创建前主对话检查了 main 工作区干净、三个分支精确指向 015a535；接口和构建入口准备提交后统一快进。
各分支保留 015a535 与 88279bf 历史，不重新建分支、不改写已有提交。
不要在主目录或其他模块目录切换分支；不要复制整个 .git 或依赖目录。

2026-10-27 已实际完成：三个 worktree 在准备提交 70b448a（015a535 的后继）上分别配置、编译、
执行 CTest 4/4 和直接运行依赖程序，全部成功；随后仅同步最终进度文档提交。
准备阶段曾将三个分支与 main 统一快进；模块交付后各分支有独立提交，当前以各树 `git log -1 --oneline` 为准，不自引用哈希。
验证日志在主目录 build/lidar-icp-module-a-verify.log、lidar-icp-module-b-verify.log、lidar-icp-module-c-verify.log。
各树原始 CTest 日志在其 build-pcl/Testing/Temporary/LastTest.log。

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

准备阶段有4项基础检查，A/B阶段为8项；最新main集成C后完整CTest应有10项通过，依赖程序输出PCL1.15.1、Eigen3.4.0。
这不代表模块算法完成；添加实现和测试后重跑同一脚本，CMake 自动启用 INTERFACES.md 指定目标。

## 文件边界与验收

- A：仅修改 include/cloud_processor.h、src/cloud_processor.cpp、tests/test_cloud_processor.cpp；验收 PCD/无效输入/NaN/Inf/体素参数与点数。
- B：仅修改 include/icp_registration.h、src/icp_registration.cpp、include/pose_utils.h、src/pose_utils.cpp、tests/test_icp.cpp、tests/test_pose.cpp；先 B01 后 B02，验收 SE(3)、已知真值、初值、失败和误差指标。
- C：修改 tools/generate_test_data.cpp、独立实验代码、results 和 docs/EXPERIMENTS.md；数据源/许可和生成器契约依接口，完整实验等待集成。
- 主对话独占 CMakeLists.txt、主程序、共享类型、总体管理文档和 Git 集成；模块提出跨边界建议，不直接修改。

模块实现提交必须附任务编号、文件清单、分支/提交、实际构建与测试结果、遗留问题。
模块不得修改 TASKS/PROGRESS 自行标 DONE；主对话审核与完整测试后更新状态。
准备阶段当时只有环境可标DONE；当前集成状态以末节和PROGRESS为准，不能把基础检查当作算法验收。

## A/B 首轮集成后的状态

A/B 已完成交付并被 main 合并；A worktree 保留 24fc233、B 保留 3236706，未改写它们的原始提交。
main 的应用流水线、质量门禁、微小旋转误差修复和 9 个 CLI 场景验收位于 be35e0c。
C worktree 已从 4cfce35 快进到该集成提交，自身重新配置/编译/CTest 8/8 通过；日志在主目录 build/module-c-after-integration.log。
最终进度文档随后快进同步，最终 HEAD 以 git 命令为准。C 可以直接在原文件夹启动，无需重建 worktree 或 PCL。
后续若 A/B 继续开发，先由主对话协调同步 main 的集成修复，不能从旧交付提交继续覆盖数值修复。

## 模块 C 正式交付之后

C 原交付分支为 f85214f，已由主对话在 main 正式集成、全新构建并独立复跑35组实验，完整CTest10/10。
本轮不改写 C 分支或 worktree；需要后续修改时先由主对话协调同步最新main。
独立质量审查应打开主目录、读 REVIEW_CHECKLIST.md，用新的build-independent-review目录，不在原模块树里切换分支。
