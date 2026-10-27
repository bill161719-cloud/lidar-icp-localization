# 项目进度

更新时间：2026-10-27（Asia/Shanghai）。当前阶段：已按用户授权发布至GitHub Public仓库。

## README展示更新

以5ca6c34为基线，README按技术作品展示重组为九部分；KITTI效果靠前、实现与库调用分工明确，技术讨论放在后部。
新增QUICKSTART承接较长Windows命令；审查/整改原文、算法、实验原件和LICENSE保持不变。
GitHub原始README/许可证署名确认为Wang Chenqi；README明确维护者王陈琦（Wang Chenqi），不按浏览器译文改动许可证。
四行实验数字、文档/图片链接、六图哈希检查通过；代表性KITTI CLI实际运行结果与归档一致。
本次未重跑全部36组或完整CTest，既有验收结果保持原意义；修改前后摘要见README_REDESIGN。
用户已授权该文档优化提交正常推送至origin/main；最终同步与公开页面检查证据保存在build/readme-redesign-*。

## 当前状态

- 仓库：https://github.com/bill161719-cloud/lidar-icp-localization
- 用户网页创建仓库并明确授权推送；本地只添加精确origin、普通push，不重新init、不重写历史。
- 首次发布基线a1b9bd10f57fef88e67c1728a8d43c5535c495db；GitHub接口确认main与本地一致，origin/main上游已建立。
- V01、R01、R02均DONE：第二轮独立复审通过、本地准备完成、远程发布与公开内容核验完成。
- 发布状态文档单独提交后同步普通推送，最终远程main/本地HEAD一致及干净状态以build/github-final-git-state.json和git实际查询为准。

## 本次远程检查

| 检查 | 结果 | 本地证据（Git忽略） |
|---|---|---|
| 目标与空仓库 | 首次ls-remote零refs；接口核对Public、所有者、名称和完整clone_url | 推送前实际命令/接口响应 |
| 首次普通push | main新分支成功，无强制覆盖，上游建立 | build/github-initial-push.log |
| 首次远程文件树 | 325文件blob与本地a1b9bd1完全相同 | build/github-first-tree-comparison.json |
| 公开首页及文件 | HTTP200，README渲染两张对比图；12文件含六PNG与Git提交逐字节相同、PNG校验通过 | build/github-first-curl-http-verification.json |
| 最终状态同步 | 文档提交再push，远程main/文件树/全部祖先提交核对；公开页面与文件再次校验 | build/github-final-push.log、github-final-git-state.json、github-final-tree-comparison.json、github-final-curl-http-verification.json |

Python公开HTTP检查初次读取超时，改用curl成功复验；失败日志保留，不将其计为成功。
没有要求用户提供密码/Token；没有创建额外Tag/Release或推送其他feature分支。

## 既有工程验收与审查链

本次没有改受审代码、测试、构建脚本或实验原件，没有再次重建依赖/重跑全部实验。
最近发布前全新build-release-ready：Release/PCL ON/严格固定版本，CTest10/10，0失败，4.26s。
36报告、46输入、16源码及六图全量核验通过；新二进制另复跑人工0.02、KITTI0.3/0.6三案，除耗时外一致。
证据见RELEASE_READINESS、build/release-ready-build.log、release-ready-archive-validation.json和release-ready-cli-verification.json。

- 第一轮REVIEW_REPORT的问题和不通过历史结论保留；3bdc6c4整改自检见REMEDIATION_REPORT。
- 第二轮REVIEW_REPORT_V2在教学/工程展示范围通过：两个P1关闭，无新P0/P1；验证器P2和版本策略通过。
- 重复位置反例的风险处置通过，不等于已消除算法歧义。
- 两轮报告原文SHA仍为3e18e926978b461dcaa10fd864d81044e601d23da2c43dc00037df748822f0b0及7a5569bfcb36d94c80555e08d02bd848cced9d7856e8471d1a54d3e111aaf580。

KITTI0.3m：accepted=true、RMSE0.1692475275m、内点率0.9386925795；0.6m收敛但RMSE0.2256860548m超限被拒绝。
人工0.02m真值平移误差3.04784994e-5m、旋转误差3.693598627e-6rad；六图有真实输入/矩阵/哈希溯源。

## 发布范围与后续

原创内容MIT，Copyright (c) 2026 Wang Chenqi；第三方依赖和KITTI道路/混合成果保留原许可，不上传原始道路点云、依赖或exe。
不是完整SLAM/FAST-LIO，无LiDAR-IMU紧耦合；KITTI内点RMSE不代表车辆定位精度。
重复位置5m错误、直线/对称网格歧义仍存在，收敛/accepted不保证物理位置正确。
交互PCL Render、其他平台、完整内存检测器、多帧漂移及通用鲁棒性仍未验收。
后续只在用户要求的新任务范围维护；发布事实和远程验证见PUBLICATION。
