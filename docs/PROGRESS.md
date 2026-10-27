# 项目进度

更新时间：2026-10-27（Asia/Shanghai）。当前阶段：首次独立审查问题整改自检通过，等待独立复审。

## 当前结论

- main整改起点4bc4e1346288b150e367c04576cae8f6c86c1ce7；开始时仅docs/REVIEW_REPORT.md未跟踪，无已跟踪修改。
- 首次独立报告P0=0、P1=2、P2=2、P3=1，原结论未修改；报告SHA256为3e18e926978b461dcaa10fd864d81044e601d23da2c43dc00037df748822f0b0。
- FIX01/FIX02/FIX04/FIX05修复自检通过；FIX03为重复结构风险处置/反例归档完成，不等于算法已消除歧义。
- 用户已明确选择原创MIT、Copyright (c) 2026 Wang Chenqi；LICENSE与第三方范围已落盘，无同一许可决定待答。
- V01仍为REVIEW，R01为REVIEW；不宣布独立审查全部通过，不创建远程、不推送、不新增算法模块。

## 逐项整改

- P1-01：loadPcd对ASCII词元/列/点数严格校验，正常数值/NaN/Inf清理和三种编码保留。
  原foo对照旧程序退出0/接受，新程序退出3/无stdout、无有效位姿；source/target两侧都覆盖。
- P1-02：原创代码、文档、纯合成成果MIT；KITTI道路和混合成果不纳入MIT。
  检查发现prepare_pcl_source.py引用上游匹配上下文，已标注并保留完整PCL BSD通知；未发现vendored库或第三方ICP求解器。
- P2-01（报告顺序）：所有归档案例验证SE(3)、pose/diagnostic、argv/参数/输入溯源；完整输入时读初值/truth，显式source-root检查源码。
  原全零T+伪造命令组合在旧验证器通过、新验证器拒绝；未默认把历史源码与当前版本混比。
- P2-02：5m重复副本精确复现，低RMSE/内点率1仍接受错误位置。保留持续回归/说明，不添加任意阈值或声称退化检测。
- P3-01：标准验证脚本启用严格固定版本模式；直接CMake对未测组合给出警告，可显式开启严格模式。

## 真实构建、测试与实验

保持Windows11/UCRT64 GCC16.2.0/PCL1.15.1/Eigen3.4.0/CMake3.31.6/C++17，不新装或重建依赖。
build-remediation初始不存在，全新Release配置和全部C++目标编译通过。
后续完整配置/构建/CTest最终10/10、退出0、3.95s；内部A7/7、工具5/5、验证器10/10、CLI11/11，不重复计为CTest总数。

| 检查 | 结果 | 本地日志 |
|---|---|---|
| 全新Release/PCL ON/严格固定版本 | 成功 | build/remediation-release.log |
| 最终完整回归 | CTest10/10 | build/remediation-final-regression-v2.log |
| 36组CLI实验 | 原35+重复位置，实际重跑完成 | build/remediation-experiments-v2.log |
| 输入/源码/图像/参考/几何核验 | 46输入、16源码、6图、35参考报告通过 | build/remediation-validation-v2.log |
| 旧归档兼容性 | 历史35报告、42输入、6图通过；未要求当前源码等于旧源码 | build/remediation-historical-validation.log |
| 缺陷修复前后及版本诊断 | 旧错误被接受/新拒绝；严格与告警逻辑正反例通过 | build/remediation-before-after.json、remediation-version-diagnostics.json |

公开证据results/metrics/remediation/保留36组原始JSON/command/stderr、CSV、provenance、validation、acceptance及对照摘要。
原module-c-v2/main-review指标、图片与元信息保持不变，仅署名文件追加当前许可确认。
本次使用既有本地道路数据并核对46输入哈希，重新执行实际C++实验；未重复下载PCL或借旧报告伪装新运行。

- 干净人工0.02m：平移误差3.04784994e-5m，旋转误差3.693598627e-6rad。
- KITTI0.3m：accepted=true，内点RMSE0.1692475275m，内点率0.9386925795。
- KITTI0.6m：converged=true/accepted=false，RMSE0.2256860548m；有效位姿null。
- 重复位置：accepted=true，RMSE7.872274178e-8m，内点率1，真值平移误差5m。
- 原35报告除路径/耗时外完全一致，六张重新绘图与原PNG逐字节一致；KITTI匹配RMSE不是车辆定位误差。

## 失败、限制与下一步

验证器初稿误认历史identity字段、后续离线测试试读缺少的历史truth路径，均保留失败日志并修正，最终完整测试通过。
没有放松SE(3)/指标门限、跳过失败、屏蔽第三方警告或修改依赖源码。
项目仍非完整SLAM/FAST-LIO；没有通用退化检测、参考轨迹/多帧漂移或PCL交互Render验收。
源码许可选择已解决；第三方NC/SA范围、实际用途及未来二进制通知仍需按发布内容核对。
下一步：独立对话读取原REVIEW_REPORT、REMEDIATION_REPORT、INTERFACES和REVIEW_CHECKLIST，使用新build目录复审。
复审前不把V01标DONE；最终提交ID用git log查询，工作树/既有分支历史均保留。
