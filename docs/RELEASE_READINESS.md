# GitHub 发布前准备记录

状态更新：用户已于2026-10-27自行创建Public仓库并明确授权推送，实际发布见 [PUBLICATION](PUBLICATION.md)。
以下保留准备阶段的检查与计划，不应将当时“未推送”误读为当前状态。

日期：2026-10-27（Asia/Shanghai）。计划名称：lidar-icp-localization；计划可见性：Public。
准备阶段当时仅完成本地整理、验证和提交；尚未创建远程、配置origin或push。
第二轮独立报告受审代码为3bdc6c4，本轮不改源码、测试、构建脚本或实验归档，只整理展示/状态及忽略规则。

## 发布依据与保留边界

- REVIEW_REPORT_V2 在教学与工程展示范围通过；两项原P1关闭，无新增P0/P1，验证器P2和版本策略通过。
- 重复结构P2是风险处置通过，仍保留5m错误匹配反例，不表述为算法已消除歧义。
- 准备阶段V01、R01由主对话核验证据后标DONE；R02当时保持TODO，后续实际状态以TASKS/PROGRESS为准。
- 不是完整SLAM/FAST-LIO；无LiDAR-IMU紧耦合、通用抗退化、真实轨迹精度或实时性能声明。
- KITTI单帧对的内点RMSE不等于车辆定位误差；PCL交互Render、其他平台等未验证事项保持限制。

两轮独立报告原文字节保留，SHA256：

| 文件 | SHA256 |
|---|---|
| REVIEW_REPORT.md | 3e18e926978b461dcaa10fd864d81044e601d23da2c43dc00037df748822f0b0 |
| REVIEW_REPORT_V2.md | 7a5569bfcb36d94c80555e08d02bd848cced9d7856e8471d1a54d3e111aaf580 |

## 本轮实际执行

| 检查 | 结果 | 本地证据（Git忽略） |
|---|---|---|
| 新目录Release配置/全量构建 | build-release-ready初始不存在；严格固定版本ON，成功 | build/release-ready-build.log |
| 完整CTest | 10/10，0失败，4.26s；依赖探针通过 | 上述日志、build-release-ready/Testing/Temporary/LastTest.log |
| 完整历史实验归档核验 | 36报告、46输入、16源码、6图、35参考案例及辅助几何检查通过 | build/release-ready-archive-validation.json |
| 新二进制人工/道路复跑 | synthetic0.02、KITTI0.3/0.6三案除耗时外与归档完全一致；退出0/0/4 | build/release-ready-cli-verification.json、build-release-ready/下各报告/command/stderr |
| .gitignore验证 | 20个正/反例通过，包含本地依赖、构建缓存、原始点云和应公开的文件 | build/release-ready-ignore-check.json |
| 原创许可/第三方通知/报告保护 | MIT署名和范围存在，PCL通知与固定上游去尾空白后相同，Eigen许可台账读取，两轮报告哈希未变 | build/release-ready-license-report-check.json |
| 文件及历史扫描 | 体积、原始数据/产物、隐私/凭据模式、绝对路径分类、Markdown链接和六PNG检查 | build/release-ready-publication-audit.json |

本轮没有重新生成全部36组或重新下载KITTI；完整36组由第二轮独立复审实际重跑。
本轮实际全量核对已有归档与输入，再用新构建二进制复跑三项代表性实验；不把归档检查写成36组重新运行。
没有新增算法、依赖安装或编译警告屏蔽；C++源码哈希保持受审版本。

## 文件、大小与许可

拟发布内容为源码、文档、六张PNG和小型实验归档；不包含本地依赖/原始道路点云或exe。
精确跟踪文件数、字节数、Git对象大小和扫描分类保存在本机publication-audit JSON；
最终提交后再读取Git状态和大小，不将整个含依赖/缓存的工作目录大小当作发布仓库大小。
最大图片kitti_alignment.png为1,117,186字节，GitHub无需为当前文件配置LFS。

当前WORKTREES已改用相对目录；ENVIRONMENT保留C:/msys64作为可覆盖的安装默认示例，
不是个人账户目录或运行硬编码。Git历史中原有非敏感项目路径保留，不重写历史；
历史路径记录不应被误报为“已彻底从历史抹除”。静态模式扫描不保证发现所有类型的秘密。

需要保留的许可文件：

- 根LICENSE：仅项目原创代码、文档及纯合成成果MIT，Copyright (c) 2026 Wang Chenqi。
- licenses/PCL-BSD-3-Clause.txt：上游CMake匹配上下文的BSD原通知；不受项目MIT重新授权。
- docs/THIRD_PARTY.md：PCL/Eigen/传递依赖范围及原始来源。
- results/figures/module-c-v2/ATTRIBUTION.md，以及各metrics归档的ATTRIBUTION.md：
  KITTI道路/混合成果按适用CC BY-NC-SA 3.0保留署名、来源和条件，不能统称MIT。

没有新发现的第三方权利冲突证据；不声称仅靠源码扫描能证明全部最终法律权属。
本次不分发二进制，未来打包exe/依赖或改变实际用途时需另核查分发范围及通知。

## 准备阶段拟定的发布步骤（后续执行见PUBLICATION）

按 [GitHub 官方导入本地仓库流程](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)：

1. 明确GitHub所属账户/组织及最终要发布的main提交；准备阶段未检查账户权限、仓库名占用或推送认证。
2. 获得用户明确批准后，创建名为lidar-icp-localization的空Public仓库；
   不勾选自动生成README、LICENSE或.gitignore，避免与本地历史冲突。
3. 在本项目根目录核对状态及remote，替换下面的OWNER为批准的账户名后执行：

```powershell
git status --short --branch
git log -1 --oneline
git remote -v
git remote add origin https://github.com/OWNER/lidar-icp-localization.git
git remote -v
git push -u origin main
```

若届时origin已存在，先核对实际URL，不直接覆盖；不重新init、不force push、不执行--all或--mirror。
4. 推送后核对远程Public可见性、main提交、README图片/链接和许可范围。
   建议描述：C++17/PCL/Eigen两帧LiDAR点云配准与相对位姿估计，附可复现实验及失败分析。

以上是准备阶段计划。之后用户网页创建仓库并授权，本地添加origin、普通推送和公开页面核验见PUBLICATION。
本地未重复创建仓库、重新init或重写历史。
