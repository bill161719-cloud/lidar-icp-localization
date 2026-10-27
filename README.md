# 基于C++与PCL的LiDAR点云配准与相对位姿估计

*LiDAR Point Cloud Registration & Relative Pose Estimation*

## 项目简介

基于 **C++17、PCL 与 Eigen**，面向 LiDAR 相邻帧点云匹配，实现点云读取、异常点过滤、体素降采样、ICP 配准、相对位姿估计和配准质量评估。

项目以 **KITTI 真实道路点云**和**合成真值数据**验证完整处理链路，将点云几何匹配、SE(3) 位姿分析与 CMake/CTest 工程验证结合，提供可检查的 C++ 实现和可复现实验。

## 项目效果展示

![KITTI 真实道路点云配准前后对比](results/figures/module-c-v2/kitti_alignment.png)

左侧为配准前，右侧为配准后；橙色为 target，蓝色为 source 或变换后的 source。配准后道路边界等静态结构的空间重合程度提高。
图中前后视窗一致，显示抽样与裁剪仅用于可视化，ICP 使用清理和下采样后的完整点云。

数据：KITTI Raw `2011_09_26_drive_0005_sync`，source=帧1、target=帧0。图片由真实点云和估计矩阵绘制；[数据署名与派生图许可](results/figures/module-c-v2/ATTRIBUTION.md)。

## 核心功能与技术实现

| 工程环节 | 技术实现 | 代码入口 |
|---|---|---|
| 点云读取与清理 | C++17 输入校验、显式 NaN/Inf 过滤；通过 PCL 读取 PCD | [cloud_processor.cpp](src/cloud_processor.cpp) |
| 体素降采样 | 调用 PCL VoxelGrid，记录处理前后点数与范围 | [cloud_processor.cpp](src/cloud_processor.cpp) |
| 相邻帧配准 | 调用 PCL point-to-point ICP，支持初始变换与可配置迭代/距离参数 | [icp_registration.cpp](src/icp_registration.cpp) |
| 位姿表达与误差 | 使用 Eigen 表达 SE(3) 齐次变换，分解旋转/平移/四元数，计算已知真值误差 | [pose_utils.cpp](src/pose_utils.cpp) |
| 匹配质量评估 | 项目实现单向最近邻内点统计与 RMSE，结合收敛状态、内点数/比例执行质量门禁 | [registration_pipeline.cpp](src/registration_pipeline.cpp) |
| 结构化输出 | 命令行串联处理模块，输出 JSON 位姿、参数、点数和质量结果 | [main.cpp](src/main.cpp) |
| 自动化与实验 | CMake 构建、CTest 回归；独立工具完成数据转换、批量实验、绘图和归档核验 | [tests/](tests/)、[tools/](tools/) |

配准求解器使用 PCL ICP；项目自有实现集中于输入边界、处理链路、位姿工具、独立质量评估及工程验证。Python 实验脚本负责数据组织和结果分析，与 C++ 配准程序分开。

## 系统流程与技术架构

```text
PCD / KITTI BIN 输入
        ↓
格式转换与输入校验 → 有限点过滤 → VoxelGrid 降采样
        ↓
PCL ICP 配准 ← 初始位姿与配准参数
        ↓
匹配质量评估：收敛状态 / 内点数与比例 / 内点 RMSE
        ↓
Eigen 相对位姿 → JSON 输出 → 实验可视化与结果分析
```

采用右手坐标系、米和弧度，使用列向量约定：`p_target = T_target_source * p_source`。
4×4 齐次变换包含 3×3 旋转 R 和以 target 坐标表达的平移 t：

```text
                  [ r11 r12 r13 tx ]
T_target_source = [ r21 r22 r23 ty ]
                  [ r31 r32 r33 tz ]
                  [  0   0   0   1 ]
```

C++ 接口与算法实现在 `include/`、`src/`；自动化测试位于 `tests/`，实验工具和输出位于 `tools/`、`results/`。
[技术架构](docs/ARCHITECTURE.md)与[接口约定](docs/INTERFACES.md)说明各模块职责、变换方向和错误处理。

## 实验结果

人工实验使用固定种子的非对称三维点集，构造 `target=T_gt*source`；真值仅用于评分，不参与 ICP 求解或初始化。
道路实验对同一 KITTI 相邻帧对使用不同体素边长，比较局部匹配质量及质量门禁行为。

| 场景 / 体素边长 | 平移真值误差 m | 旋转真值误差 rad | 内点 RMSE m | 内点率 | 质量门禁 |
|---|---:|---:|---:|---:|---|
| 合成真值 / 0.02 m | 3.04785e-5 | 3.69360e-6 | 0.000798083 | 100% | 接受 |
| KITTI 道路 / 0.3 m | — | — | 0.169248 | 93.87% | 接受 |
| KITTI 道路 / 0.6 m | — | — | 0.225686 | 90.16% | 收敛，RMSE 超限后拒绝 |
| 重复结构 / 0.005 m | 5 | 2.58096e-8 | 7.87227e-8 | 100% | 接受，存在位置歧义 |

平移/旋转误差依据已知真值计算；“—”表示该道路实验未测真值误差。
内点 RMSE 是距离门限内的单向最近邻配准残差，内点率以处理后的 source 点数为分母；**KITTI 内点 RMSE 不等于车辆实际定位误差**。

0.6 m 体素案例展示了“ICP 收敛”与“质量接受”的区别；重复结构案例则用于分析局部残差与真实位姿唯一性的关系。
原始报告、配置、命令及 CSV 见 [实验归档](results/metrics/remediation/ATTRIBUTION.md)与[实验记录](docs/EXPERIMENTS.md)。

## 环境与快速运行

已验证环境：**Windows 11 · MSYS2 UCRT64 GCC 16.2.0 · PCL 1.15.1 · Eigen 3.4.0 · CMake 3.31.6**。
测试驱动使用 Python >=3.9；批量实验绘图另用 NumPy/Matplotlib。依赖安装和版本固定方式见[环境说明](docs/ENVIRONMENT.md)。

准备依赖后，在仓库根目录 PowerShell 构建并执行 CTest：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-release-ready -Jobs 1
```

现有自动化验证为 **CTest 10/10 通过**，覆盖点云处理、位姿/ICP、真实 CLI 数据链路及实验工具；普通 CTest 可离线运行。

首次获取 KITTI 两帧数据：

```powershell
python tools/fetch_kitti_pair.py --output data/kitti/drive_0005_pair
```

按[快速运行指南](docs/QUICKSTART.md)将两帧 BIN 转为 PCD，并配置当前 PowerShell 的 PCL/UCRT64 DLL 路径后，运行：

```powershell
$pair = 'data/kitti/drive_0005_pair'
./build-release-ready/lidar_icp.exe --source "$pair/0000000001.pcd" `
  --target "$pair/0000000000.pcd" --voxel-size 0.3 --max-iterations 100 `
  --evaluation-distance 0.5 --output build-release-ready/pair.json
```

JSON 中包含 `T_target_source`、位姿分量、配准指标、配置与 `converged` / `accepted`；拒绝结果的有效位姿为 null。
输出文件须尚不存在。完整 Windows 命令、参数和输入准备见[快速运行指南](docs/QUICKSTART.md)。

## 实验复现与项目文档

- [快速运行](docs/QUICKSTART.md)：依赖入口、数据转换、DLL 路径、CLI 与测试命令。
- [实验记录](docs/EXPERIMENTS.md)：36 组实验、体素/初值/扰动分析、真实报告与完整复现。
- [技术架构](docs/ARCHITECTURE.md) · [接口约定](docs/INTERFACES.md)：模块边界、SE(3) 方向、单位及错误处理。
- [测试与独立审查](docs/REVIEW_REPORT_V2.md)：构建与回归证据；[首轮审查](docs/REVIEW_REPORT.md)、[整改记录](docs/REMEDIATION_REPORT.md)及[发布记录](docs/PUBLICATION.md)完整保留。
- [第三方许可与数据归属](docs/THIRD_PARTY.md)：PCL/Eigen、KITTI 来源及派生成果范围。

## 适用范围与技术讨论

当前聚焦 **LiDAR 两帧点云配准与相对位姿估计**，适用于定位链路中几何匹配环节的学习、参数验证与工程实现分析。

ICP 匹配效果受到初值、几何结构、噪声及点云重叠程度影响。收敛状态与残差指标反映局部几何匹配质量，无法单独保证物理位姿的唯一正确性；解释车辆运动时还需确认帧序、静态场景假设及传感器外参。

重复结构实验中，target 包含两个相距 5 m 的相同结构，初值落在另一副本时出现低 RMSE、高内点率但平移真值误差 5 m 的结果。
后续可结合可信运动先验、几何约束和对应一致性检查增强可靠性，并通过更多帧对、初值和随机种子评估泛化表现。当前实验结论限定于已记录的场景和配置。

## 开源许可与致谢

项目维护：**王陈琦（Wang Chenqi）**。

项目原创代码、文档和纯合成测试成果采用 [MIT License](LICENSE)，版权署名为 `Copyright (c) 2026 Wang Chenqi`。
项目使用 Codex 辅助开发，代码、实验及验证记录可查阅。

感谢 **PCL** 提供点云处理与 ICP 实现，**Eigen** 提供矩阵与几何运算支持，**KITTI** 提供真实道路数据。
PCL/Eigen 等第三方依赖保留原有许可，PCL 修补脚本内上游匹配片段保留 BSD 通知。
KITTI 道路图、道路结果及混合 CSV/provenance/validation 按适用的 **CC BY-NC-SA 3.0** 署名、非商业和相同方式共享条件处理，原始道路点云不随仓库分发。
许可范围与作者/数据来源详见 [THIRD_PARTY](docs/THIRD_PARTY.md)及[结果图署名](results/figures/module-c-v2/ATTRIBUTION.md)，不以项目 MIT 重新授权第三方内容。
