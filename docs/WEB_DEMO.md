# 本地网页演示与面试操作

本页对应新增的本地演示层；原有 C++ 模块、CLI 接口、36组历史实验和审查报告保持不变。
网页是新增功能，不包含在原第二轮独立审查结论内，本轮自检结果单独记录。

## 启动

在项目根目录 PowerShell 执行：

```powershell
./tools/start_web_demo.ps1 -OpenBrowser
```

浏览器访问 `http://127.0.0.1:8765/`，保留终端运行，结束时在终端按 Ctrl+C。
端口已被占用时指定 `-Port 8770`，浏览器地址相应改变。
可用 `-BuildDirectory`、`-DependencyRoot`、`-MsysRoot` 指定已有构建和依赖位置。
直接启动方式：`python web_demo/server.py --port 8765 --open-browser`。

需要 Python >=3.9、现代 Chrome/Edge，以及已构建的 `lidar_icp.exe` 和 `generate_test_data.exe`。
不需要 npm 安装、不加载 CDN、不安装新 PCL、不修改系统 PATH。
服务为 C++ 子进程临时设置 DLL 路径。默认使用 build-release-ready；勿误用早期只有帮助入口的 bootstrap 二进制。
道路场景需要本地已有两帧 PCD，首次数据获取和转换见 [QUICKSTART](QUICKSTART.md)。
服务启动时通过现有 C++ 生成器构造固定种子20261027的合成点云，写到被Git忽略的 build-web-demo/synthetic，已有输入不覆盖。
没有道路数据时仍能展示合成场景；不会在启动时自动联网下载 KITTI。

## 界面操作

1. 选择 KITTI 道路相邻帧或合成真值场景，检查 source/target 标签。
2. 设置体素边长、迭代次数；展开可调整匹配距离、内点距离和 RMSE 门限。单位米。
3. 点击“运行 C++ 配准”，等待本机程序输出。没有伪造迭代进度或历史指标占位。
4. 查看收敛状态、质量门禁、RMSE、内点率、点数、平移和4×4矩阵。
5. 通过“配准前/后”切换，拖动旋转、滚轮缩放，Shift+拖动平移，可俯视、复位和全屏。
6. “导出本次 JSON”保存包含 live/replay 标志的结果封装；原始 C++ JSON 和执行日志另存本地运行目录。

橙色 target，蓝色 source。浏览器 Canvas 对三维 XYZ 点执行相机旋转和正交投影，
这次新增了交互显示；不是 PCL 实时窗口，也不是播放采集中的 LiDAR 数据流。
每帧最多显示18000个原始点，等间距抽样，初始视窗按中心96%坐标范围适配；远处点可通过缩放查看。
显示抽样不参与 ICP，前后切换对同一组显示点应用有效 T；C++ 使用完整输入完成有限点清理和 VoxelGrid 后求解。

修改参数或切换场景会清除旧结果，避免旧矩阵被误认为对应新配置。
初始变换固定单位矩阵；该版不提供上传任意文件、修改真值或运动先验的操作。
默认质量参数仍由原 CLI 定义：内点至少3、内点率至少0.5，RMSE上限取界面输入。
被拒绝结果仍可查看诊断指标并导出 JSON，但有效位姿/T 为 null，不能切换到有效配准后视图。
JSON 内的 diagnostic_T_target_source 仅供诊断，不能用于累计位姿。

## 建议的三分钟展示

- **约一分钟：道路配准。** 选择 KITTI，0.3m体素，点击实际运行。旋转到道路视角，切换前后并解释 source 帧1到 target 帧0。
- **约一分钟：质量与参数。** 解释 RMSE 是几何残差而非车辆定位精度。将体素改为0.6m实际运行，展示“收敛但质量拒绝”；下方历史曲线仅代表该帧对和当前配置。
- **约一分钟：有真值的验证。** 切换合成场景实际运行，解释平移/旋转误差及4×4变换。说明 PCL 提供 ICP，项目实现处理链路、质量评估、测试和工程集成。

现场先做一次完整彩排，确认电脑电源、浏览器、DLL、数据和窗口缩放。
“加载已验证实验”可作为备用：有醒目的“已验证实验回放”标志，耗时来自历史记录，本次不执行 ICP。
回放前校验本地 source/target 与原始 provenance 的 SHA256；不匹配则拒绝叠加旧矩阵。
道路0.6m回放入口同样明确标志拒绝。不得将回放介绍为现场重新计算。

## 实现边界与保存位置

```text
浏览器 HTML/CSS/JS（无外部前端依赖）
    ↓ 本机 HTTP，固定数据集和允许参数
Python 标准库服务 → 既有 C++ lidar_icp.exe → 原始 JSON
    ↓
点云交互显示 / 有效变换 / 质量指标 / JSON导出
```

只绑定127.0.0.1；Host、Origin和POST会话标记校验；不开放远程文件浏览或任意命令执行。
参数范围限制用于演示操作边界，不是新增算法质量门禁。
每次实际运行创建 build-web-demo/runs/唯一ID/，不覆盖历史报告。
report.json 是 C++ 输出；execution.json 保存 UTC 开始时间、argv、退出码、stdout/stderr、二进制/输入哈希。
最长60秒、同一服务仅允许一个配准；超时终止本次直接启动的 C++ 进程并记录失败。
这些文件包含本机路径，已被 build*/ 忽略，不提交到Git。

KITTI来源、作者和道路派生展示的CC BY-NC-SA 3.0见 [THIRD_PARTY](THIRD_PARTY.md)及[图片署名](../results/figures/module-c-v2/ATTRIBUTION.md)。
网页展示的参数曲线直接复用已归档 PNG，不修改图像和指标。
本地网页不意味着 GitHub Pages 能运行 PCL，当前没有部署在线 C++ 服务。

## 自检（2026-10-30，Asia/Shanghai）

```powershell
python web_demo/test_server.py
node --check web_demo/static/app.js
```

新增8项HTTP/真实CLI测试通过，含KITTI0.3接受、0.6拒绝、合成真值、回放输入哈希防错、非法参数、Host/Origin/POST标记和PCD显示读取。
该独立测试默认使用 build-release-ready；KITTI缺席时对应测试明确skip，不伪称道路通过。
普通原工程CTest不新增网络或数据下载前提，仍为10项。
既有build-release-ready的Release/PCL ON增量完整构建和CTest10/10通过，0失败，11.69秒；未声称本轮全新目录编译。
对应日志build/web-demo-core-build.log、web-demo-core-ctest.log。
本轮机器已准备KITTI，因此8项测试无skip。
Chrome无界面实际点击验证：道路/合成实际运行、前后切换像素改变、鼠标旋转、拒绝位姿不可用、切换场景清空结果、800/390px无横向溢出、无浏览器运行时异常。
参数修改清除旧结果的补验通过；tools/start_web_demo.ps1实际启动后页面HTTP200、标题正确，记录build/web-demo-launcher-check.json。
证据在Git忽略的 build/web-demo-tests-authorized.log、web-demo-browser-check.json、web-demo-kitti.png。
初次沙箱测试因本机socket权限失败，已保留build/web-demo-tests.log，获得执行权限后重新测试通过；不将失败记录记为通过。

新网页不改变原算法局限：重复结构仍可能出现低残差错误位姿，不具备通用退化检测、完整SLAM或LiDAR-IMU融合能力。
