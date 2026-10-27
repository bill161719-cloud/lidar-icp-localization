# 项目进度

更新时间：2026-10-27（Asia/Shanghai）。当前阶段：模块 C 正式集成与有界功能实验自检通过，等待独立质量审查。

## 当前结论

- A01、B01、B02、M01、C01、C02、C03、C04、M02 均经主对话实际复验，按 TASKS 所列范围 DONE。
- 已运行完整 PCD/BIN→预处理→ICP→质量判定→JSON/CSV→真实结果图链路。
- V01 为 REVIEW，等待另一独立审查；R01 因源码 LICENSE/版权署名未确认且独立审查未完成为 BLOCKED。
- 不推送 GitHub、不创建公开仓库、不再新增算法模块。不是完整 SLAM，也不是 FAST-LIO。

## Git 与文件审查

- main 集成起点 9fc3057，工作区干净；C 输入提交 f85214f9788b5b7f2bb3687694230db99ddad434，C worktree 干净。
- 原提交 48 文件全在约定边界：5 个工具源码、1 个实验文档、6 张 PNG、其余为小型指标/命令/来源/署名归档。
- 未擅改 A/B、主程序或公共接口；主对话负责 CMake 接入、可重复验证器和补充实验。
- 最大提交图片 1,117,186 字节；初审无原始 BIN/PCD、构建缓存、可执行文件、个人用户目录路径或 >10 MiB 文件。
- main 补充 25 组扫描和独立结果归档到 results/metrics/main-review，不覆盖原 module-c-v2 证据。
- 原 A/B/C 分支和所有历史保留。最终合并提交 ID 以 git log 查询，不在本提交内自引用。

## 实际构建与自动测试

固定 PCL 1.15.1、Eigen 3.4.0、UCRT64 GCC 16.2.0、C++17、Release、CMake/CTest 3.31.6，Jobs=1。
build-final-c 最初为不存在的新目录：全新配置/编译成功，接入工具测试后 9/9。
补充一致性验证器及损坏检测后再次配置/构建，最终完整 CTest **10/10**。
10 项包含 A/B、9 个内部 CLI 场景、5 个实验工具检查及5 个归档验证器检查；内部组数不重复计入 CTest 总数。
普通 CTest 不下载 KITTI，不依赖 NumPy/Matplotlib。完整外部数据实验独立执行。

| 项目 | 实际结果 | 本地原始日志 |
|---|---|---|
| 全新 Release 配置/构建 | 成功，无依赖重新安装 | build/final-c-build.log |
| 最终完整配置/构建/CTest | 10/10，退出 0 | build/final-c-final-tests.log |
| main 独立 HTTP Range 下载 | 两帧 + timestamps，4,152,294 字节 | build/final-c-kitti-download.log |
| main 独立 BIN→PCD | payload 保持、五个文件哈希与原提交相同 | build/final-c-convert-0.log / final-c-convert-1.log |
| 10 原案例 + 25 扫描 | 35 个真实 CLI 进程结果 | build/final-c-experiments-v2.log |
| 输入/报告/图像/几何核验 | 35 报告、42 输入哈希、6 图、10 参考案例通过 | build/final-c-consistency-v2.log |

公开复验归档包含 provenance、二进制/源码/输入哈希、CSV、35 组 JSON/命令/stderr 和 validation.json。
provenance 明确记录待合并工作区 dirty=true，不伪称 C 代码已经属于旧 base_commit。
数据和原始构建日志仍在本地 Git 忽略目录。六张复绘 PNG 与原提交逐字节一致，已逐图查看，PNG 元信息无个人路径。

## 关键实测与限制

- 人工 0.02 m 体素：平移误差 3.04784994e-5 m、旋转误差 3.693598627e-6 rad，达到干净真值标准。
- KITTI 0.3 m：accepted=true，内点 RMSE 0.1692475275 m，内点率 0.9386925795；无参考轨迹误差，不宣称车辆定位精度。
- KITTI 0.6 m：converged=true，但 RMSE 0.2256860548 m 超限，正确拒绝，有效 pose 为 null；严格门限案例也正确拒绝。
- 原 10 个报告除 source/target 路径与耗时外完全相同；原始数据、转换文件、时间戳哈希均相同。
- 原始几何固定抽样最近邻 RMSE：人工 0.316986→0.0000262796 m，KITTI 0.274307→0.173437 m，支持前后图的对齐改善。
- 补充 C04：4 档噪声、4 档离群点、5 档目标采样比例、5 档空间裁剪比例、5 档初值、直线/对称平面两个反例，共25组。
  两个几何反例在门禁通过时仍分别约90°/180°姿态歧义，实际记录为局限，没有篡改 accepted。
- 只验证一个道路帧对、有界单因素扫描；没有通用鲁棒性证明、参考轨迹、多帧漂移、完整内存检测器或交互 PCL 窗口渲染验收。
- 六图为 Matplotlib 真实数据图，不冒称 PCL GUI 截图；PCL/VTK 场景构造 smoke 仍通过。
- 第三方 GCC/Eigen/PCL 分配器警告保留，未用 -Wno-* 消音或改依赖。

## 复验中修复与失败记录

- 中文归档读取的 Windows 默认 GBK 失败已改为显式 UTF-8，失败未计作实验成功。
- 验证器初版把十进制 voxel 与 float32 回显差异当作损坏；只对 voxel 配置使用 float32 精度容差，其余指标/参考矩阵保持严格核对。
  修复前日志 build/final-c-validator-before-fix.log 保留；修复后损坏检测5/5及完整10/10通过。
- 原 10 案例、六图和核心 A/B 算法未改写；新增内容是实验扫描、溯源与验证，非新算法模块。

## 数据许可与下一步

- 2026-10-27 重新核查 KITTI 官方与 AWS 条目：CC BY-NC-SA 3.0；道路派生图/结果保留署名、改动说明和许可。
- 原始道路数据不提交；个人路径/大文件/缓存初审通过。混合仓库不能笼统标为 MIT。
- 自有源码最终 LICENSE/版权署名仍需用户确认；V01 独立审查尚未执行，因此不能宣布已完成公开交付。
- 独立审查打开主目录，先读 AGENTS、INTERFACES、TASKS、本文及 REVIEW_CHECKLIST.md，执行全新构建与离线归档核验。
- A/B worktree 保留原交付提交，C worktree 保留 f85214f；本轮不改写分支、不覆盖模块工作。
