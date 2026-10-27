# 工程协作规范

本工程是 C++17 点云配准与相对位姿估计项目，不是完整 SLAM 或 FAST-LIO。
所有解释、文档用中文；代码、函数、文件名用英文。只报告实际执行的测试。

## 开工必读

先读 README.md、docs/PROJECT_SPEC.md、ARCHITECTURE.md、INTERFACES.md、TASKS.md、PROGRESS.md、DECISIONS.md（后六项均位于 docs/）。
执行 `git status --short --branch`、`git log -5 --oneline`。工作区有未知改动时保留，不覆盖、不清理。
A/B/C 已集成，第二轮独立复审在教学/工程展示范围通过，现已公开发布；没有用户授权不新增算法模块，不自行派生开发对话。
两轮独立报告均保留原文；首轮历史结论不得改成通过。V01已依据REVIEW_REPORT_V2验收。
用户已于2026-10-27明确授权普通推送到 https://github.com/bill161719-cloud/lidar-icp-localization.git；该授权已落实，不为同一发布重复索要批准。
本轮用户已明确授权原创MIT、Copyright (c) 2026 Wang Chenqi，第三方及KITTI范围见LICENSE/THIRD_PARTY。
不要再次把同一署名/许可选择当待决问题，也不要将第三方内容归入MIT。

## 所有权

| 负责人 | 分支 | 可修改文件 |
|---|---|---|
| 模块 A | feature/cloud-processing | include/cloud_processor.h、src/cloud_processor.cpp、tests/test_cloud_processor.cpp |
| 模块 B | feature/icp-registration | include/icp_registration.h、src/icp_registration.cpp、include/pose_utils.h、src/pose_utils.cpp、tests/test_icp.cpp、tests/test_pose.cpp |
| 模块 C | feature/experiments | tools/generate_test_data.cpp、独立实验脚本/代码、results/、docs/EXPERIMENTS.md；data/sample/ 新增数据须先提交来源建议给主对话 |
| 主对话 | main | CMakeLists.txt、src/main.cpp、include/cloud_types.h、tests/dependency_check.cpp、README.md、AGENTS.md、其余总体管理文档、构建工具、许可证、Git 集成 |
| 验收对话 | 独立审查分支 | 默认只读；提出带文件位置的审查意见，不直接改 main |

跨边界改动先说明理由和建议补丁，由主对话审批、实施；模块不得直接改共享 CMake 或进度表。
首轮集成新增 include/registration_pipeline.h、src/registration_pipeline.cpp、tests/test_pipeline.py 归主对话维护。
本轮集成的 tools/validate_experiments.py、test_experiment_validation.py、绘图版本锁与总体验收记录也由主对话维护。
集成层的必要修复可由主对话实施，须记录原因、补回归并重新测试；本轮已修复 pose_utils 的微小旋转误差精度问题。
使用独立 worktree，禁止多个对话在同一工作目录切换分支。接口变更由主对话统一发布。
模块交付必须列任务编号、修改文件、分支、提交 ID、编译和测试命令/结果、遗留问题、下一步。

## 工程与测试

公开类型遵循 include/cloud_types.h；签名以 docs/INTERFACES.md 为准。长度米，角度弧度，右手坐标。
禁止混用 MSVC 与 GCC C++ 库、不同运行时或位数的预编译依赖。不得未经用户确认更换工具链。
最小 bootstrap 的通过不代表 PCL/ICP 通过。模块验收需要 LIDAR_ENABLE_PCL=ON，注册相应 CTest。
当前固定 PCL 1.15.1 和独立 Eigen 3.4.0；系统 pacman Eigen 5 不用于项目。先读 docs/ENVIRONMENT.md。
用 tools/verify_dependencies.ps1 构建验证；独立 worktree 需传入共享 DependencyRoot/CMake 路径，避免重复安装或误选依赖。
具体启动方式见 docs/WORKTREES.md。每个 worktree 独占自身 build*/，共享主目录依赖仅供读取；
模块不得调用 build_dependencies.ps1、升级 pacman 包或改写共享依赖。
主 CMake 已按文件存在性启用 A/B/C 库和 A/B 测试；添加文件后重跑验证脚本即可，不必改 CMake。
禁止用 assert 作为唯一测试判断（Release 可能禁用）；失败返回非零并输出原因。
ICP 测试包含已知真值、初值、不收敛和非法输入；可视化测试与无显示单元测试分离。
应用有效位姿以 quality.accepted/CLI accepted 为准，不能只检查 PCL converged；被拒绝的诊断矩阵不得用于累计里程计。

## Git 与状态

状态仅 TODO / IN_PROGRESS / BLOCKED / REVIEW / DONE，只有主对话验收后改 DONE。
各模块自行提交所属文件，主对话审查后合并，完整构建、CTest 后更新 TASKS/PROGRESS。
未实际运行、缺依赖、失败必须明确记录。不得 reset --hard、force push 或删除未知文件。
构建缓存、工具包、本机路径配置、原始 KITTI 数据不提交。提交前检查 diff、隐私、体积与数据许可。
没有用户明确确认，不创建公开远程仓库、不推送 GitHub。发布前确认 LICENSE 的最终选择及版权归属。
