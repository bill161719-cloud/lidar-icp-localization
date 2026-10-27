# 项目进度

更新时间：2026-10-27（Asia/Shanghai）。当前阶段：A/B 首轮集成验收通过，准备启动模块 C。

## 当前结论

- A01、B01、B02、M01 均已由主对话完成代码审查、集成和实际测试，标记 DONE。
- 已存在真实可运行的 PCD 读取→NaN/Inf 清理→体素→ICP→独立质量判断→JSON 位姿链路。
- 原始 PCL converged 与应用 accepted 分开；未收敛、零/低内点、高 RMSE 或非法最终变换不能输出有效 pose。
- 不是完整 SLAM、FAST-LIO 或多帧里程计。真实道路、GUI 渲染/截图及系统鲁棒性实验尚未完成。

## Git 与审核

- 集成起点 main=4cfce35，工作区干净；保留 88279bf、015a535 及全部准备历史。
- A 原始提交：24fc23311b883283eb4a8d3877423050ad5c1d55；只修改约定 3 个文件，合并验收提交 cae8e11。
- B 原始提交：3236706361e11bccdde01d9043f9971ba58b2daf；只修改约定 6 个文件，合并验收提交 99b52c7。
- 模块公开签名、PointXYZ 类型和 T_target_source 方向一致。最终应用集成提交由 git log 查询，避免提交自引用哈希。
- 主对话新增 registration_pipeline、CLI 报告和端到端测试，并在 main 修复 B 的微小旋转误差，记录于 DECISIONS/INTEGRATION_AB。
- 未修改第三方库、未屏蔽编译警告、未重装或更换 GCC、未创建远程仓库或推送。

## 最近实际验证

| 阶段 | 结果 | 原始日志 |
|---|---|---|
| 仅 A 集成，全新 Release | CTest 5/5，模块 A 内部 6/6 组 | build/integration-a.log |
| A+B 集成，全新 Release | CTest 7/7 | build/integration-ab.log |
| 流水线首轮 | CTest 8/8，9 个真实 CLI 场景 | build/integration-pipeline.log |
| 微小旋转新增回归（修复前） | test_pose 实际失败，未跳过 | build/pose-angle-regression-before-fix.log |
| 数值修复后完整重新配置/构建 | CTest 8/8；9 个 CLI 场景全部通过 | build/integration-final.log |
| 关闭 PCL 的最小模式回归 | CTest 3/3；只提供帮助/版本 | build/bootstrap-final.log |
| C worktree 同步集成提交后独立构建 | Release CTest 8/8，9 个 CLI 场景通过 | build/module-c-after-integration.log |

使用 PCL 1.15.1、独立 Eigen 3.4.0、UCRT64 GCC 16.2.0、CMake/CTest 3.31.6，C++17、Release、Jobs=1。
最终验收命令：tools/verify_dependencies.ps1 -BuildDirectory build-integration-ab -Jobs 1。
完整 CTest 共 8 项：3 个 CLI 基础检查、dependency_check、test_cloud_processor、test_pose、test_icp、test_pipeline。
test_pipeline 是 1 项 CTest，内部 9 个 unittest 方法，不把内部场景数重复计入 CTest 总数。

端到端实际验证：PCD 读写与无效点、下采样统计、已知 SE(3)、source/target 对调的逆变换、
无对应点未收敛、收敛但零内点、低重叠、高 RMSE、轻噪声+源离群点、非法输入及报告保护。
被拒绝的报告 pose/T_target_source 为 null，零内点 RMSE 为 null；未提供真值的误差也为 null。
最终人工数据、命令、stdout/stderr/退出码保留在 build-integration-ab/test-pipeline/run-65yh8v6b，
汇总 build/integration-summary.json；真实数值、测试定义和限制详见 INTEGRATION_AB.md。

## 已知限制与后续任务

- GCC mismatched-new-delete 警告来自 Eigen/PCL/libstdc++ 分配器内联路径；已检查分配/释放配对与对齐配置，未发现应用直接混用。
  警告原样保留；未执行完整内存检测，不宣称全部诊断必然误报或内存安全已穷尽验证。
- PCL 达到迭代上限可能 converged=true，应用门禁现已拒绝零/低内点等情况；仍不能识别全部退化/对称错误匹配或局部最优。
- 单个受控噪声/离群点测试不替代系统实验；没有真实道路精度、GUI 截图或性能基准。
- A 的体素 int32 网格范围检查可能拒绝过小体素/过大范围，实验应记录尺度，不能绕过防护。
- C01/C02/C04/C03 仍 TODO；按数据许可、转换坐标、初值和质量拒绝规则开展后续实验。正式发布许可仍待确认。

## Worktree 状态与模块 C

| 模块 | 路径 | 分支 | 当前用途 |
|---|---|---|---|
| A | D:/CodexProgects/lidar-icp-module-a | feature/cloud-processing | 保留原交付提交，未改写 |
| B | D:/CodexProgects/lidar-icp-module-b | feature/icp-registration | 保留原交付提交，数值修复位于 main |
| C | D:/CodexProgects/lidar-icp-module-c | feature/experiments | 已从干净旧基线 4cfce35 快进至 be35e0c，并实际完成 8/8 复验 |

C 可正式启动；已同步包含 A/B、质量门禁、CLI 和数值修复的 main，且 C worktree 本身复验通过。
随后只同步本次进度文档提交，源码与 be35e0c 相同；最终启动 HEAD 以 git worktree list 为准。
同步前实际检查分支、旧 HEAD 和干净状态，未覆盖任何 C 工作；C 算法/生成器仍未开发。
各树复用主目录 .local-deps/.local-tools，不复制或重建 PCL；正确参数见 WORKTREES.md。

初始化、依赖安装和 worktree 准备的历史验收分别见 INITIALIZATION.md、ENVIRONMENT.md、WORKTREES.md。
只有主对话验收后才能更新任务 DONE；模块 C 不得修改共享 CMake、主程序、总体进度或 A/B 文件。
