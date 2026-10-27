# 模块 C 实验记录与交付

日期：2026-10-27（Asia/Shanghai）。分支 `feature/experiments`，实验基线 `9fc3057d54d7072dbbbf7affdf07ac8cd3663e8d`。
本轮按用户任务编号 C01（生成/验证）、C02（道路）、C03（图片）、C04（文档）交付，状态 **REVIEW**，等待主对话验收。
项目原 TASKS 中 C04 指系统鲁棒性扫描；本轮仅提供几个受控扰动/失败案例，不能将它标为完整 DONE。

本项目是两帧点云配准与相对变换估计，不是完整 SLAM。真实道路实验没有参考轨迹，**没有测得真实定位精度**。

## 数据来源、许可与坐标

人工数据由 `tools/generate_test_data.cpp` 生成：2400 点、固定种子 20261027，不等大小的地面/墙面加抬升曲面，打破几何对称性。
以 source 构造 `target=T_gt*source`，米、弧度、右手系；
`R=Rz(0.12)*Ry(-0.035)*Rx(0.02)`，`t=(0.3,-0.15,0.08)` m。
生成器保存 source.pcd、target.pcd、truth.txt、metadata.json；同工具链同种子字节可复现，拒绝覆盖同名文件。
人工数据没有第三方数据来源，源码和自有成果的最终许可证仍由主对话确认，本模块不擅自选定。

真实数据为 KITTI Raw synced+rectified，序列 `2011_09_26_drive_0005_sync`，连续 Velodyne 帧 0000000000、0000000001。
核查来源日期同上：

- [KITTI Raw 官方入口](https://www.cvlibs.net/datasets/kitti/raw_data.php)：网页下载当前要求登录；Raw 含约 10 Hz 的 Velodyne 数据。
- [AWS Open Data Registry](https://registry.opendata.aws/kitti/)：由 Max Planck Campus Tübingen 管理的 `avg-kitti` 公共桶，无需 AWS 账号。
- [实际官方公共存储 ZIP](https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/2011_09_26_drive_0005/2011_09_26_drive_0005_sync.zip)：大小 645,940,900 字节。
- [KITTI 版权说明](https://www.cvlibs.net/datasets/kitti/)与 [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/)：署名、非商业、相同方式共享。不能将道路数据/派生图笼统标成项目 MIT。

署名：Andreas Geiger、Philip Lenz、Christoph Stiller、Raquel Urtasun，*Vision meets Robotics: The KITTI Dataset*，IJRR，2013。
本次通过公共桶提供的匿名访问获取数据，没有使用登录凭据或绕过访问控制。
获取程序只接受 HTTP 206 和准确的 Content-Range，固定 ETag，提取指定两帧及 timestamps.txt，验证 CRC32。
正式获取共传输 4,152,294 字节（另有一次 65,536 字节可达性探测），未下载整个 ZIP。
获取请求、ETag、条目 CRC、SHA256 已归档到 `results/metrics/module-c-v2/provenance.json`。
不提交原始 .bin、转换 PCD 或时间戳全集，均保留于被忽略的 `data/kitti/`。
公开结果中的道路图及道路结果归档附 CC BY-NC-SA 3.0 署名说明，见对应目录 ATTRIBUTION.md。
这不决定整个项目源码许可；公开发布仍由主对话按工程规范审核。

| 帧 | 用途 | 时间戳 | 原始点数 | BIN SHA256 |
|---|---|---|---:|---|
| 0000000000 | target（前帧） | 2011-09-26 13:04:32.335337762 | 123397 | 956976a1b391b18a17c42719212ef5de5e91e8ab986f7b79717343b126373ad3 |
| 0000000001 | source（后帧） | 2011-09-26 13:04:32.438625628 | 123683 | 31e07ff7ffd67c2347a2cec3c8504d1d5fb35a2d22b6b02e2998470a230f188f |

相邻间隔 0.103287866 s。输入按每点四个小端 float32 XYZI 解释；非空、16 字节整数倍、所有四字段有限，否则转换失败。
`kitti_bin_to_pcd.py` 写 binary PCD，原始 payload 逐字节保持，包括 intensity；已有核心只消费 XYZ。
XYZ 为米，Velodyne 约定 x 前、y 左、z 上，没有改轴、缩放或使用相机坐标。
未使用相机/IMU外参，未获得/核验参考轨迹；本工具没有额外去畸变，也不把 synced+rectified 称为已完成逐点运动补偿。
`T_target_source=T_0_1` 仅表示后帧坐标映射到前帧坐标，不能无条件解释为车辆真实运动。

## 环境与复现命令

实际环境：Windows 11、UCRT64 GCC 16.2.0、C++17、Release、PCL 1.15.1、独立 Eigen 3.4.0、CMake/CTest 3.31.6。
实验驱动：已有 CPython 3.11.5、NumPy 2.4.4、Matplotlib 3.10.8；本轮未安装新依赖、未改变工具链。
绘图用 Agg 后端，无 GUI；中文字体使用系统 Microsoft YaHei。其他系统需可用中文字体以避免缺字。

以下从模块 C 根目录运行。共享依赖位置依据 `WORKTREES.md`，不重新安装依赖。
Python 必须在加入 UCRT64 PATH **之前**解析，避免误选 UCRT64 自带且缺少绘图库的另一解释器。

```powershell
$sharedRoot = Split-Path -Parent ((git rev-parse --path-format=absolute --git-common-dir).Trim())
$pythonExe = (Get-Command python.exe).Source
$ucrtBin = Split-Path -Parent (Get-Command g++.exe).Source
./tools/verify_dependencies.ps1 `
  -DependencyRoot (Join-Path $sharedRoot '.local-deps') `
  -CMake (Join-Path $sharedRoot '.local-tools/python/cmake/data/bin/cmake.exe') `
  -BuildDirectory build-c-review -Jobs 1

# 首次获取与转换；已有文件会拒绝覆盖，不需要重复执行。
& $pythonExe tools/fetch_kitti_pair.py --output data/kitti/drive_0005_pair
& $pythonExe tools/kitti_bin_to_pcd.py --input data/kitti/drive_0005_pair/0000000000.bin --output data/kitti/drive_0005_pair/0000000000.pcd
& $pythonExe tools/kitti_bin_to_pcd.py --input data/kitti/drive_0005_pair/0000000001.bin --output data/kitti/drive_0005_pair/0000000001.pcd

$savedPath = $env:Path
try {
  $env:Path = "$(Join-Path $sharedRoot '.local-deps/pcl-1.15.1/bin');$ucrtBin;$savedPath"
  & $pythonExe tools/test_experiment_tools.py --generator build-c-review/generate_test_data.exe --workdir build-c-review/tool-tests -v
  # 输出和工作子目录必须是新的；再次复现时换一个名称。
  & $pythonExe tools/run_experiments.py --exe build-c-review/lidar_icp.exe --generator build-c-review/generate_test_data.exe `
    --work build-c-review/reproduce-inputs --output build-c-review/reproduce-metrics --figures build-c-review/reproduce-figures
  if ($LASTEXITCODE -ne 0) { throw 'Module C experiment failed' }
} finally { $env:Path = $savedPath }
```

归档结果的实际驱动命令使用 `build-pcl` 可执行文件：

```powershell
& $pythonExe tools/run_experiments.py --work build-pcl/experiments-v2 --output results/metrics/module-c-v2 --figures results/figures/module-c-v2
```

驱动直接调用现有 CLI，不重新实现 ICP/误差计算。所有逐次命令和退出码在 `*.command.json`，原始 CLI 报告在 `*.json`，stderr 在 `*.stderr.txt`。
报告文件与 stdout 经 JSON 逐项比较；CSV 从同一报告提取，无真值用空值，拒绝位姿为 null。
`provenance.json` 保存输入和 PNG 的 SHA256、Python 库版本、下载与转换记录。
输入由生成器/扰动代码再生，不需要提交人工 PCD。跨平台换行、浮点和字体可能改变哈希；数值指标应在合理容差内比较，耗时不要求相同。

单次道路基准调用为：

```powershell
./build-pcl/lidar_icp.exe --source data/kitti/drive_0005_pair/0000000001.pcd --target data/kitti/drive_0005_pair/0000000000.pcd --output build-pcl/road-manual.json --voxel-size 0.3 --max-iterations 100 --max-correspondence-distance 1 --evaluation-distance 0.5 --max-rmse 0.2
```

以上单次形式是已归档 `kitti_v0.3.command.json` 的等效命令，单独输出文件须不存在。运行仍需上述 DLL PATH。
`--voxel-size` 是体素边长；`--max-correspondence-distance` 是 ICP 建立对应点的距离上限；`--evaluation-distance` 是独立最近邻评估的内点门限。
`--max-rmse` 是应用接受阈值，与评估距离不同。未覆写的参数为 min_inliers=3、min_inlier_ratio=0.5、transformation_epsilon=1e-8、euclidean_fitness_epsilon=1e-6。
所有正常案例初值为单位阵；真值仅通过 `--truth` 评分，不作为初值。

## C01：人工真值与受控失败

目的：验证 source→target 方向、三维旋转和平移误差，观察体素与扰动影响。
最大迭代 100、对应距离 1 m、评估距离 0.2 m、RMSE 接受上限 0.1 m；坏初值案例改用评估 0.5 m、RMSE 上限 0.2 m。

| 案例 | source/target 下采样点数 | accepted | fitness m² | 内点 RMSE m | 内点率 | 平移误差 m | 旋转误差 rad |
|---|---|---|---:|---:|---:|---:|---:|
| 体素 0.02 m | 2379/2377 | true | 6.36928e-7 | 0.000798083 | 1 | 3.04785e-5 | 3.69360e-6 |
| 体素 0.1 m | 2005/2020 | true | 0.000219432 | 0.0148132 | 1 | 0.00214196 | 0.000345272 |
| 体素 0.3 m | 776/830 | true | 0.0101322 | 0.0988983 | 0.989691 | 0.0304634 | 0.00463508 |
| 噪声与离群点，体素 0.1 m | 2245/2069 | true | 43.9802 | 0.0363657 | 0.893096 | 0.00105501 | 0.000291699 |
| 远离初值，体素 0.1 m | 2005/2020 | false | 2267.12 | 未定义 | 0 | 未输出 | 未输出 |
| 目标仅保留首 240 点，体素 0.1 m | 2005/235 | false | 0.883808 | 0.152918 | 0.101247 | 未输出 | 未输出 |

第一行平移 <0.01 m、旋转 <0.1°（实际约 0.00021163°），满足人工精度要求，即使本轮用了单位阵初值。
0.3 m 体素虽然 accepted，却未满足上述人工精度要求（约 0.26557°）：**门禁通过不能替代真值验收**。
体素分别在两个坐标系中形成质心，降采样后点集不再严格一一对应，粗体素偏差增大，不能只以速度选参数。

扰动使用 NumPy default_rng(20261027)，target 加每轴标准差 0.02 m 的高斯噪声；source 新增 240 点，均匀分布于 x/y=[15,20]、z=[10,15] m。
这是一个固定种子的组合扰动案例，不能由此推断系统鲁棒性。
fitness 是全 source 到 target 的无限距离最近邻均方距离，离群点会使它很大；独立内点 RMSE 只计算距离门限内的对应点，二者不可混用。
部分目标是前 240 点地面点，不是空间均匀的“10% 几何重叠率”；其内点率来自最终估计，不能当精确真实重叠率。
坏初值为纯平移 (30,30,30) m，未收敛退出 4；部分目标 converged=true 但低内点率，退出 4。
两者有效矩阵和 pose 均为 null，保留诊断供分析，没有累计为里程计。

## C02：真实道路相邻帧

目的：验证公开道路 BIN→PCD→预处理→ICP→质量判定完整链路，并比较体素参数。
最大迭代 100、对应距离 1 m、评估距离 0.5 m、初值单位阵；未输入 truth。

| 体素 m / 门限 | source/target 下采样点数 | converged / accepted | fitness m² | 内点 RMSE m | 内点数 / 内点率 | align 单次 ms | 退出码 |
|---|---|---|---:|---:|---|---:|---:|
| 0.1 / RMSE≤0.2 | 62228/62215 | true / true | 0.0568651 | 0.129406 | 60104 / 0.965867 | 10410.2547 | 0 |
| 0.3 / RMSE≤0.2 | 22640/22607 | true / true | 0.106150 | 0.169248 | 21252 / 0.938693 | 3456.8562 | 0 |
| 0.6 / RMSE≤0.2 | 9709/9670 | true / false | 0.177835 | 0.225686 | 8754 / 0.901638 | 1108.1586 | 4 |
| 0.3 / RMSE≤0.01 | 22640/22607 | true / false | 0.106150 | 0.169248 | 21252 / 0.938693 | 3394.9945 | 4 |

0.3 m 展示案例的 `T_0_1`（完整精度见 kitti_v0.3.json）：

```text
 0.9998945594  -0.01453070156  0.001249131863   0.392264694
 0.01453052554  0.9998955131  -0.000025715621  -0.029250741
-0.001248643268 0.000043854117 1.000002027     -0.002407779451
 0             0             0                1
```

相邻帧约 94% 的最终单向内点率支持本案例有充分可匹配区域；这不是独立测得的真实重叠率。
0.1 m 保留更多点，单次耗时更高、匹配 RMSE 更小；不意味着已证明其实际位姿更准确。
0.6 m 的收敛结果和严格门限的 0.3 m 结果均被拒绝，有效 pose/T 为 null，未用于展示对齐或累计运动。
没有 OXTS/轨迹/外参真值验证，所有道路 translation_error_m、rotation_error_rad 为 null。
耗时仅 align 调用，不含 IO/预处理/评估；没有重复计时或统计置信度，不能称为性能基准。

## C03：真实数据图像与证据

所有 PNG 来自上述实际输入和 accepted 的估计矩阵，经 Matplotlib Agg 绘制；没有 AI 图片或冒充实验的示意图。

| 文件（results/figures/module-c-v2/） | 内容 |
|---|---|
| synthetic_raw.png | 人工 source 原始三维结构 |
| synthetic_alignment.png | 人工前后 XY/XZ，同坐标范围、同视角 |
| synthetic_errors.png | 人工真值平移/旋转误差随体素变化 |
| kitti_raw.png | KITTI 帧 1 原始三维点云、z 着色 |
| kitti_alignment.png | KITTI 帧 1→0 前后 XY/XZ，同坐标范围、同视角 |
| voxel_comparison.png | 人工与道路的体素—内点 RMSE 对比 |

道路 raw 图每 5 点取 1 点并裁剪到 x=(-20,40)、|y|<25、z<8 m；前后图每 3 点显示 1 点，XY 范围 x=(-20,40)、y=(-25,25)，XZ 的 z=(-4,8)。
裁剪/稀疏只用于显示；ICP 使用全帧清理/体素后的数据。对齐图对原始 source 施加 accepted 的最终矩阵。
PNG 是数据绘图，不是 PCL/VTK GUI 截图；没有运行交互窗口验证。

![道路配准前后](../results/figures/module-c-v2/kitti_alignment.png)

![人工真值误差](../results/figures/module-c-v2/synthetic_errors.png)

## 实际验证与局限

本轮已实际执行：

- 原 build-pcl 重新配置/Release 构建，CTest 8/8 通过，依赖检查输出 PCL 1.15.1 / Eigen 3.4.0。
- `test_experiment_tools.py` 5/5：同种子字节相同及 target 真值验证、uint32 边界/非法参数/拒绝覆盖、转换 XYZI payload 字节保持、非法长度/NaN/Inf 拒绝、HTTP 200 不读取整包。
- 10 组真实 CLI 实验及 stdout/保存报告一致性、退出码与 accepted、未知真值/null、拒绝有效位姿/null 检查。
- 全新 build-c-review 目录 Release 构建与 CTest 8/8 通过；工具检查再次 5/5 通过。
- 使用全新二进制复跑全部 10 组实验；除输入路径和 elapsed_ms 外，完整 CLI JSON 的其余字段与归档逐项完全相同。
- 输入/六图 SHA256、CSV/JSON 指标逐项一致性检查通过；六张 PNG 均实际查看通过。
- 精简验证记录见 `results/metrics/module-c-v2/validation.json`，复现原始输出在 `build-c-review/reproduce-metrics/`。

本地原始构建日志 `build-pcl/module-c-build.txt`、工具测试 `build-pcl/experiment-tools-tests.txt`、实验执行 `build-pcl/experiment-run-v2.txt`；
未解决前的绘图库解释器/PCD 换行试跑失败也保留于 build-pcl/experiment-run.txt，本轮未将其算作通过。
提交目录只保留不含机器绝对路径的报告和精简验证台账，不提交构建日志/缓存/二进制。

局限：仅一个道路帧对；未剔除动态物体、未显式去地面/去畸变、没有参考轨迹精度，没有多帧漂移分析。
人工几何/种子有限，未完成系统噪声、初值、重叠率扫描或对称/退化场景识别。阈值在单案例上通过，不构成通用定位保证。
现有第三方 Eigen/PCL 编译诊断未屏蔽；没有执行内存检测器。下载依赖公共桶可达性与 Range 支持，不承诺链接永久有效。

主对话集成不需要修改核心接口或 CLI；生成器由现有文件存在性入口自动启用。
建议主对话审查后将 5 组独立工具检查接入 CTest（本模块无权修改 CMake），审核来源署名并选择成果加入 README。
TASKS/PROGRESS、源码 LICENSE、GitHub 发布仍由主对话维护，本轮未合并 main、未推送。
