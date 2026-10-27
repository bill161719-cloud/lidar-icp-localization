# 面向激光 SLAM 的 C++ 点云配准与相对位姿估计系统

`lidar-icp-localization` 是一个可编译、可测试、可复现的 **两帧 LiDAR 点云配准与相对位姿估计**项目。
使用 **C++17、PCL、Eigen、CMake、Git**，覆盖点云输入、预处理、PCL point-to-point ICP、SE(3) 位姿分析、质量判定和实验溯源。

**不是完整 SLAM 系统；未实现 FAST-LIO 或 LiDAR–IMU 紧耦合融合。**
[第二轮独立复审](docs/REVIEW_REPORT_V2.md)已在教学与工程展示范围通过：全新 Release、**CTest 10/10**、**36 组实验**及六张结果图核验。
项目已发布至 [GitHub：bill161719-cloud/lidar-icp-localization](https://github.com/bill161719-cloud/lidar-icp-localization)。
发布验证与历史记录见 [PUBLICATION](docs/PUBLICATION.md)。

![KITTI 相邻帧配准前后](results/figures/module-c-v2/kitti_alignment.png)

上图由真实 KITTI 点云及接受的估计矩阵绘制，前后视窗一致；图片显示裁剪和稀疏不改变 ICP 运算输入。
六张图均是实际数据的 Matplotlib 图，不是 PCL 交互窗口截图。

## 实测结果

| 场景 / 体素边长 | 平移真值误差 m | 旋转真值误差 rad | 内点 RMSE m | 内点率 | 质量判定 |
|---|---:|---:|---:|---:|---|
| 人工 / 0.02 m | 3.04785e-5 | 3.69360e-6 | 0.000798083 | 100% | 接受 |
| KITTI / 0.3 m | 未测 | 未测 | 0.169248 | 93.87% | 接受 |
| KITTI / 0.6 m | 未测 | 未测 | 0.225686 | 90.16% | 收敛但 RMSE 超限，拒绝 |
| 重复结构 / 0.005 m | **5** | 2.58096e-8 | 7.87227e-8 | 100% | 接受，展示错误位姿风险 |

**KITTI 内点 RMSE 不等于车辆真实定位精度。** 当前仅验证一个道路帧对，没有参考轨迹真值。
重复结构说明：即使 ICP 收敛、RMSE 很低、内点率很高，仍可能配准到错误位置；`accepted=true` 也不保证位姿真实正确。

![人工已知刚体变换配准前后](results/figures/module-c-v2/synthetic_alignment.png)

另四图：[人工原始点云](results/figures/module-c-v2/synthetic_raw.png)、[道路原始点云](results/figures/module-c-v2/kitti_raw.png)、
[人工真值误差](results/figures/module-c-v2/synthetic_errors.png)、[体素参数对比](results/figures/module-c-v2/voxel_comparison.png)。
指标、命令、stderr、CSV、输入/源码/图像哈希见 [实验记录](docs/EXPERIMENTS.md)及 [最新实验归档](results/metrics/remediation/ATTRIBUTION.md)。

## 流程与位姿约定

```text
PCD / KITTI BIN → XYZI PCD → XYZ 有限点清理 → 体素下采样
               → 带初值的 PCL ICP → 独立质量门禁 → Eigen 位姿 / JSON
               → 已知真值误差、CSV、配准前后图、输入/源码/图像溯源
```

- 严格检查 ASCII PCD 数字词元；损坏坐标不静默变成零。显式 NaN/Inf 留给清理，不信任错误的 is_dense。
- 预处理记录输入、有限点和下采样点数；PCL 执行 ICP，项目没有重写完整 ICP 求解器。
- 分开报告 `converged` 与 `accepted`，输出 fitness（m²）、单向最近邻内点 RMSE（m）、内点率及单次 align 耗时。
- 未收敛、非法变换、零/低内点率、高 RMSE 等结果不输出有效位姿，只保留诊断。

统一右手系、米、弧度、列向量；**source 到 target** 的变换定义为：

```text
p_target = T_target_source * p_source

                  [ r11 r12 r13 tx ]
T_target_source = [ r21 r22 r23 ty ] = [ R  t ]
                  [ r31 r32 r33 tz ]   [ 0  1 ]
                  [  0   0   0   1 ]
```

R 为 SO(3) 旋转，t 用 target 坐标表示；输出旋转矩阵、平移和归一化四元数（w,x,y,z）。
该坐标变换不能无条件解释为车辆实际运动，需确认帧序、静态场景和外参。
人工实验 `target=T_gt*source`；`--truth` 只评分，不参与初值或求解。详细契约见 [INTERFACES](docs/INTERFACES.md)。

## 环境与构建

| 项目 | 实际验证版本 |
|---|---|
| 系统 / 编译器 | Windows 11，MSYS2 UCRT64 GCC 16.2.0，x86_64，C++17 |
| 核心库 | PCL 1.15.1、Eigen 3.4.0 |
| PCL 传递依赖 | Boost 1.92.0、FLANN 1.9.2、VTK 9.6.2 |
| 构建 / 测试 | CMake/CTest 3.31.6（项目要求 >=3.20），Python >=3.9 标准库 |
| 可选实验绘图 | CPython 3.11.5、NumPy 2.4.4、Matplotlib 3.10.8，Agg |

依赖不随仓库分发。首次克隆先按 [ENVIRONMENT](docs/ENVIRONMENT.md)准备同工具链依赖；
固定源码、包版本及 `tools/build_dependencies.ps1` 均有记录。已配置依赖时无需重新下载或构建 PCL。
不能链接 MSVC 预编译 PCL；系统 Eigen 5 不用于本项目。其他平台未实机验收。

在仓库根目录 PowerShell 执行：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-release-ready -Jobs 1
```

脚本显式使用 Release、PCL ON 和已测固定版本组合，完成配置、编译及 CTest；临时设置 DLL PATH 后恢复。
依赖/CMake 不在默认位置时传 `-DependencyRoot`、`-CMake`、`-MsysRoot`。
普通 CTest 共 **10 项**，不下载道路数据、不依赖 NumPy/Matplotlib；包含 A/B、5 组工具检查、10 组归档检查及11个 CLI 场景，内部组数不重复计入总数。
本次发布前日志见本机 `build/release-ready-build.log`。

直接 CMake 的默认 PCL OFF 构建只有帮助/版本入口，不能据此宣称配准验证通过。
标准脚本启用 `LIDAR_REQUIRE_VALIDATED_VERSIONS=ON`；最低发现版本不代表已测兼容范围。

## 运行与数据准备

人工数据为固定种子20261027的2400个非对称三维点，
`R=Rz(0.12)*Ry(-0.035)*Rx(0.02)`、`t=(0.3,-0.15,0.08) m`，生成器输出PCD、真值和元信息。
真实数据来自 [KITTI Raw](https://www.cvlibs.net/datasets/kitti/raw_data.php) 的 `2011_09_26_drive_0005_sync`：source=帧1、target=帧0，间隔约0.103288s。
按 [AWS 公共登记](https://registry.opendata.aws/kitti/)的桶用HTTP Range获取两帧和时间戳约4.15MB，不下载约646MB整包。

首次获取和转换（已有文件不重复覆盖）：

```powershell
python tools/fetch_kitti_pair.py --output data/kitti/drive_0005_pair
python tools/kitti_bin_to_pcd.py --input data/kitti/drive_0005_pair/0000000000.bin --output data/kitti/drive_0005_pair/0000000000.pcd
python tools/kitti_bin_to_pcd.py --input data/kitti/drive_0005_pair/0000000001.bin --output data/kitti/drive_0005_pair/0000000001.pcd
```

BIN 按小端 float32 XYZI 处理，长度须为16的整数倍且字段有限，转换保留 payload 和强度；ICP只消费XYZ。
Velodyne 坐标 x前/y左/z上，未改轴/缩放，未做额外逐点去畸变或跨相机/IMU标定转换。原始BIN/PCD不提交Git。

用真实两帧运行（输出文件须尚不存在）：

```powershell
$savedPath = $env:Path
try {
  $ucrtBin = Split-Path -Parent (Get-Command g++.exe).Source
  $env:Path = "$((Resolve-Path .local-deps/pcl-1.15.1/bin).Path);$ucrtBin;$savedPath"
  ./build-release-ready/lidar_icp.exe --source data/kitti/drive_0005_pair/0000000001.pcd --target data/kitti/drive_0005_pair/0000000000.pcd --voxel-size 0.3 --max-iterations 100 --max-correspondence-distance 1 --evaluation-distance 0.5 --max-rmse 0.2 --output build-release-ready/road-manual.json
} finally {
  $env:Path = $savedPath
}
```

stdout/输出文件为JSON，日志为stderr；`--initial`/`--truth`接受严格16个数的4×4 SE(3)文本矩阵。
退出码：0接受，2参数/语义错误，3读取/运行错误，4未收敛或质量拒绝。拒绝报告的有效pose/T为null，诊断矩阵不可用于累计轨迹。

## 测试与完整实验复现

无需道路数据即可核验36组公开归档及六图，并显式核查当前受审源码：

```powershell
python tools/validate_experiments.py --metrics results/metrics/remediation --figures results/figures/module-c-v2 --reference results/metrics/main-review --skip-inputs --source-root .
```

此模式不声称已检查未提供的原始输入。完整36组运行命令、DLL PATH和绘图解释器设置见 [EXPERIMENTS](docs/EXPERIMENTS.md)；
驱动显式加 `--sweep --repeated-structure`，为work/output/figures选三个新目录。绘图版本锁在 `tools/requirements-experiments.txt`。
完整输入核验还读取初值/truth，核对46个输入；源码核验需显式 `--source-root`，历史归档应使用其对应源码快照。

审查链：[首轮问题](docs/REVIEW_REPORT.md) → [整改记录](docs/REMEDIATION_REPORT.md) → [第二轮通过结论](docs/REVIEW_REPORT_V2.md)。
首轮报告原文及当时“不通过”结论保留，当前发布前证据见 [RELEASE_READINESS](docs/RELEASE_READINESS.md)。

## 局限与后续方向

- ICP是局部优化，依赖初值、结构、噪声、动态物体和可匹配区域；accepted只检查局部数值质量，不保证对应唯一或物理位姿正确。
- 重复位置5m错误、直线约90°及对称网格约180°歧义均已披露；未实现通用退化检测或鲁棒自动驾驶定位。
- 一个真实道路帧对和固定种子的有界扫描不构成全部道路、全部参数/随机种子的证明；无真值轨迹、多帧漂移或实时FPS证据。
- 无地图、回环、IMU融合/紧耦合、FAST-LIO、ROS或GPU加速；PCL交互Render、其他平台及完整内存检测器未验收。
- 纯人工0.3m粗体素虽accepted，旋转误差约0.26557°，未达到0.1°真值标准；质量阈值与真值正确性不同。
- 第三方GCC/Eigen/PCL分配器警告保留，未屏蔽或冒险修改依赖。

后续可独立评估更多道路帧对、三轴初值和多种随机种子、可信运动先验、对应一致性检查及同环境CI；这些是改进方向，当前未实现或验证。

## 目录与许可

```text
include/ src/     C++模块、ICP/位姿工具、命令行流水线
tests/ tools/     自动化测试、生成/下载/转换、实验驱动与验证
data/kitti/      本地道路点云（Git忽略）
results/         六图、原始实验报告与溯源/署名
docs/            接口、环境、实验、审查、任务和发布记录
build*/          构建及本地完整日志（Git忽略）
```

原创代码、文档和纯合成成果采用 [MIT](LICENSE)，Copyright (c) 2026 Wang Chenqi。
PCL/Eigen等保留原许可；PCL修补脚本中上游匹配上下文保留BSD通知。
KITTI道路图、道路报告及混合CSV/provenance/validation另按相应CC BY-NC-SA 3.0范围处理，不能将整个混合仓库统称MIT。
具体来源、署名和范围见 [THIRD_PARTY](docs/THIRD_PARTY.md)及各目录ATTRIBUTION.md。
项目使用Codex辅助开发，实际代码、测试、实验和个人贡献可检查；不据此认定第三方权利已被法律保证。

当前通过教学/工程展示范围的独立复审，已按用户明确授权推送至Public仓库。
发布采用普通Git推送，保留完整main历史；[发布记录](docs/PUBLICATION.md)与[发布前检查](docs/RELEASE_READINESS.md)均可追溯。
