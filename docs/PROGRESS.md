# 项目进度

更新时间：2026-10-27（Asia/Shanghai）。当前阶段：教学与工程展示范围独立审查通过，GitHub本地发布准备完成。

## 当前结论

- 本轮起点main=3bdc6c40c54da00ff1a0e0b5a8fb18c16277dd2a；开始时仅REVIEW_REPORT_V2.md未跟踪，无已跟踪修改。
- 第二轮独立报告明确：两项P1关闭，无新P0/P1，验证器P2及版本策略通过；重复结构歧义保留为已披露局限。
- 主对话读取并核对复审及本轮实测证据后，将V01、R01标DONE；R02保持TODO，等待用户明确公开发布批准。
- 未创建GitHub仓库、未添加origin、未push；账户/组织、仓库名占用和推送权限未检查，不标为完成。
- 本轮仅整理README、管理文档、忽略规则和纳入复审原报告；C++源码、测试、工具/构建脚本和实验原件未改。

## 审查链与许可

1. 首轮REVIEW_REPORT.md在4bc4e13发现P1/P2/P3，历史“不通过”结论原样保留。
2. 3bdc6c4完成工程整改，REMEDIATION_REPORT记录实际修复与反例；未将重复结构风险虚称已消除。
3. REVIEW_REPORT_V2.md独立重建、CTest10/10、36组复现、六图核验和额外篡改检查通过，允许按当前范围进入发布流程。

两轮报告SHA256均保持不变：

- V1：3e18e926978b461dcaa10fd864d81044e601d23da2c43dc00037df748822f0b0
- V2：7a5569bfcb36d94c80555e08d02bd848cced9d7856e8471d1a54d3e111aaf580

用户确认原创MIT、Copyright (c) 2026 Wang Chenqi；LICENSE已具备。
PCL匹配上下文保留BSD通知，PCL/Eigen等依赖和KITTI道路/混合成果不纳入项目MIT；范围见THIRD_PARTY及各ATTRIBUTION。
当前无新的技术/许可文件阻断项，不表示对全部最终法律权属、任何商业用途或未来二进制分发作保证。

## 本轮发布前实际验证

保持Windows11、UCRT64 GCC16.2.0、C++17、PCL1.15.1、Eigen3.4.0、CMake3.31.6。

| 检查 | 实际结果 | 本地证据（Git忽略） |
|---|---|---|
| 新目录build-release-ready | 全新Release配置/构建通过，严格固定版本ON | build/release-ready-build.log |
| 完整CTest | 10/10，0失败，4.26s；依赖探针通过 | 同上及新构建LastTest.log |
| 原36组归档全量核验 | 36报告、46输入、16源码、6图、35参考案例及辅助几何检查通过 | build/release-ready-archive-validation.json |
| 新二进制代表性端到端实验 | 人工0.02、KITTI0.3/0.6，除耗时外全字段一致，退出0/0/4 | build/release-ready-cli-verification.json |
| 忽略规则 | 20个正反例通过 | build/release-ready-ignore-check.json |
| 许可/报告保护 | 原创署名/范围、上游通知及两轮SHA核对通过 | build/release-ready-license-report-check.json |
| 当前文件及可达历史扫描 | 无原始点云/编译产物/超10MiB文件，常见隐私与凭据模式无匹配，链接/六PNG检查通过 | build/release-ready-publication-audit.json |

本轮没有重跑全部36组或重新下载KITTI：完整重跑证据来自第二轮独立报告，本轮重核归档并实际复跑三案。
KITTI0.3m：accepted=true、内点RMSE0.1692475275m、内点率0.9386925795；
0.6m：converged=true但拒绝、RMSE0.2256860548m、有效pose/T为null。
人工0.02m真值平移误差3.04784994e-5m、旋转误差3.693598627e-6rad。

## 展示、文件与限制

README首屏展示真实道路配准图、技术栈、审查范围和结果，补齐4×4变换、复现、局限和后续方向。
当前WORKTREES改为相对目录；保留ENVIRONMENT的可覆盖MSYS2默认安装示例。
历史中非敏感项目路径保留，不重写Git历史；没有声称所有绝对路径从历史消失。
发布对象为源码/文档/小型结果，不含本地依赖、原始道路点云或exe；大小以最终本机audit和git ls-tree结果为准。
静态模式扫描不是所有类型隐私/密钥的完整性证明。

仍不是完整SLAM或FAST-LIO，无LiDAR-IMU紧耦合；KITTI匹配RMSE不是车辆真实定位精度。
重复位置5m错误、直线/对称网格歧义仍存在，accepted/converged不保证物理位姿正确。
只有单道路帧对和有界实验；交互PCL Render、其他平台、完整内存检测、多帧轨迹/漂移未验收。

## 下一步

本轮最终main提交及干净状态由git log/status实际查询。全部既有提交和两轮审查记录保留。
收到用户明确批准后，确认所属账户/组织，按RELEASE_READINESS创建空Public仓库并只推送main；
在此之前不执行任何远程创建、remote add或push。远程展示与可见性验收届时再实际完成。
