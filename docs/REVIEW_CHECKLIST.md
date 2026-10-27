# 独立质量审查入口

首次独立报告不通过的结论原样保留；整改自检已完成，V01 等待独立复审，不能把本文或主对话报告当独立结论。
打开主项目目录，默认只读源码，测试产物写入新的 build*/；不要在 feature worktree 里切换 main。

1. 实际检查 git status、git log、WORKTREES、TASKS、PROGRESS，确认待审提交和干净状态。
2. 审查 A/B 算法、变换方向/单位、初值、独立 RMSE 和 accepted/converged 区分；验证 --truth 不参与求解。
3. 执行 tools/verify_dependencies.ps1 -BuildDirectory build-independent-review -Jobs 1，预期完整 CTest 10/10。
   普通测试不下载数据、不导入 NumPy/Matplotlib，不把内部5/10/11组重复计数为 CTest。
4. 执行 README 的离线归档校验，预期35报告/6图通过，skip-inputs 时不得声称原始数据已验。
5. 可选按 EXPERIMENTS 的 main 步骤重新获取/转换/复跑，使用三个新的实验目录，核对42输入哈希、原10案例和六图。
   下载约4.15MB、只接受HTTP206，不允许整包降级；已有输入/结果不覆盖。
6. 审查 KITTI坐标、无真值/未去畸变/无相机外参假设、动态物体局限和单帧对范围。
7. 检查直线90°与对称平面180°的 accepted=true 反例，不允许从低RMSE推导真实定位精度。
8. 实际查看六图，核对PNG来源/哈希、固定视窗与显示抽样；不能把Matplotlib图冒称PCL交互截图。
9. 检查发布文件和历史：原始BIN/PCD、缓存/二进制、个人路径/凭据、大文件、署名许可分离。
10. 核查 PROJECT_SPEC 的保留项：交互PCL窗口尚未验收；原创MIT/署名已确认但第三方范围须保持；公开发布需用户明确批准。

本轮复审先读 REVIEW_REPORT.md 与 REMEDIATION_REPORT.md，核查原报告哈希未变。
重点复现foo/数值尾缀PCD不输出位姿、正常三种编码和NaN/Inf行为、5m重复位置反例、
无参考保护的新案例全零T/假argv拒绝、显式源码快照哈希，以及根LICENSE/各署名的适用范围。
整改归档离线命令：

    python tools/validate_experiments.py --metrics results/metrics/remediation --figures results/figures/module-c-v2 --reference results/metrics/main-review --skip-inputs --source-root .

预期36报告/6图/16源码哈希/35参考案例通过；不声称已验46个原始输入。
需要完整复验时按 EXPERIMENTS 使用新目录运行 --sweep --repeated-structure，并核验46输入及初值/truth。

输出逐项通过/未通过/未执行、实际命令和日志，问题注明文件位置、严重性、复现步骤和影响。
不得自己把 V01 标 DONE、改算法或推送；由主对话集成必要修复后复验。
