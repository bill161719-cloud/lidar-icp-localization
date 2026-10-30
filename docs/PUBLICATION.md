# GitHub 公开发布记录

日期：2026-10-27（Asia/Shanghai）。
仓库：[bill161719-cloud/lidar-icp-localization](https://github.com/bill161719-cloud/lidar-icp-localization)。
origin（fetch/push）：https://github.com/bill161719-cloud/lidar-icp-localization.git

## 授权、基线与执行

- 用户自行在网页创建空Public仓库，并明确授权本地main推送；本地没有重复创建仓库或重新初始化Git。
- 开始时main工作区干净，HEAD=a1b9bd10f57fef88e67c1728a8d43c5535c495db，发布准备和第二轮独立报告齐备。
- Git ls-remote首次成功返回零refs；GitHub接口核对所有者、名称、clone_url、Public可见性及空仓库元信息。
- 当时未配置origin，按用户给定的完整地址添加并精确核对。
- 普通执行git push -u origin main成功，建立origin/main跟踪；没有--force、重建README、rebase或历史重写。
- GitHub接口确认首次远程main=a1b9bd1，与本地相同；该提交保留此前全部14个可达提交。
- 随后更新README及当前进度/任务/许可状态，发布本记录，并将该文档提交再次普通推送。
  包含本记录的最终提交由仓库main和本地git log/ls-remote核对，不在记录中写入自引用哈希。

本轮没有请求密码或Token。Git使用现有认证完成推送，没有要求用户提交凭据。
只推送main及其完整祖先历史，未推送其他开发分支，不创建额外Release或Tag。

## 远程内容与页面核验

| 检查 | 实际结果 / 方法 |
|---|---|
| 仓库身份/可见性 | GitHub接口确认bill161719-cloud/lidar-icp-localization、Public和main |
| main提交 | 首次GitHub API与本地HEAD一致；文档提交同步后再次核对远程指针 |
| 文件树 | 首次325个远程文件blob SHA与本地提交逐个一致；最终文档提交再核对完整文件树 |
| README展示 | 公开首页HTTP 200，markdown-body已渲染，真实道路与人工两张对比图标签存在 |
| 六张PNG | 公开raw地址HTTP 200，内容与Git提交逐字节一致，PNG解码完整性检查通过 |
| 许可与署名 | LICENSE、THIRD_PARTY、PCL BSD通知及图/指标署名文件公开可读，内容与提交一致 |
| README内许可链接 | 首页存在LICENSE与docs/THIRD_PARTY链接 |

本地原始证据保存在Git忽略的build/：

- github-initial-push.log、github-final-push.log：两次普通push输出。
- github-first-tree-comparison.json：首次325文件blob核对。
- github-first-curl-http-verification.json、github-final-curl-http-verification.json：公开HTML/12文件/六PNG核验。
- github-first-curl-page.html、github-final-curl-page.html：实际读取的公开首页HTML。
- github-final-git-state.json：最终本地/远程main、上游、干净状态和Git历史核对。
- github-final-tree-comparison.json：最终全文件blob及可达提交集合核对。

公开HTTP检查初次Python客户端读取超时，改用curl后成功复验；
失败日志github-first-http-verification.log保留，不算作通过证据。
页面检查为实际公开HTML、渲染标签及图片/文件HTTP内容检查，不冒称已做全部浏览器/设备的截图验收。

## 工程验收与范围

本次只改发布状态文档，受审C++源码、测试、构建脚本、六图及实验原件保持不变，没有重新编译或重跑全部实验。
最近发布前全新Release/CTest10/10及36报告/46输入/16源码/六图核验见RELEASE_READINESS；
完整36组独立重跑结论见REVIEW_REPORT_V2，首轮问题及整改记录完整保留。

原创内容MIT，Copyright (c) 2026 Wang Chenqi；PCL/Eigen保留原许可，
KITTI道路与混合成果按THIRD_PARTY及ATTRIBUTION中的范围处理，未上传原始点云或本地依赖/编译产物。

当前发布限两帧点云配准/相对位姿估计的教学与工程展示。
不是完整SLAM/FAST-LIO或LiDAR-IMU紧耦合；KITTI内点RMSE不是车辆定位精度。
重复结构5m错误及其他歧义仍存在，即使收敛和低RMSE也不保证真实位姿。
没有新增通用抗退化、多帧轨迹、实时性能或交互PCL Render能力声明。

## 2026-10-30 本地交互网页更新

用户确认本地演示界面后，明确授权将该版本更新至现有GitHub仓库。
推送前main工作区干净；远程main为efe315a，本地c68640b领先1个提交、无远程独有提交。
精确origin仍为https://github.com/bill161719-cloud/lidar-icp-localization.git。
13个修改/新增文件检查通过：不含原始道路数据、编译产物、本地依赖、个人目录或匹配到的密钥模式；新增文件均小于100KB。
普通git push origin main成功，将efe315a推进到c68640b，保留历史且未强制推送。
随后同步本发布记录与PROGRESS；最终远程提交、文件内容与工作区状态以build/web-demo-publish-final-verification.json为准。

本次发布复用上一轮实际执行的Release构建、CTest10/10、新网页独立测试8/8与浏览器交互验证，
证据见WEB_DEMO及build/web-demo-*；仅推送和更新状态文档，没有重新运行36组实验或声称完成新的独立审查。
发布的是本地网页源代码和启动说明，实际PCL计算仍需本机运行服务；未部署GitHub Pages或在线C++服务。
原算法、历史指标、六图及审查原文保持不变，第三方与KITTI许可范围继续适用。
