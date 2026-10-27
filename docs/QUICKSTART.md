# 快速构建与运行

从仓库根目录的PowerShell执行。已验证Windows 11、MSYS2 UCRT64 GCC 16.2.0、PCL 1.15.1、Eigen 3.4.0。
以下是运行说明；固定环境的实际验证记录在ENVIRONMENT、EXPERIMENTS和REVIEW_REPORT_V2中。

## 1. 准备依赖并构建

首次克隆按 [ENVIRONMENT](ENVIRONMENT.md)准备UCRT64依赖和固定版本PCL/Eigen。
项目依赖不随Git分发，不能将MSVC预编译PCL与当前GCC混用。
已配置依赖时直接执行，不需要重复编译PCL：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-release-ready -Jobs 1
```

脚本实际完成Release/PCL ON配置、全量构建、CTest和依赖探针，临时设置运行路径后恢复。
默认读取项目.local-deps；依赖或工具另置时传-DependencyRoot、-CMake、-MsysRoot。
严格版本模式使用已验证的PCL1.15.1/Eigen3.4.0。

## 2. 获取并转换KITTI两帧

数据与派生成果的来源、署名和许可范围见 [THIRD_PARTY](THIRD_PARTY.md)。
下面仅用于首次获取；工具拒绝覆盖同名输入/输出，已有文件时直接复用。

```powershell
python tools/fetch_kitti_pair.py --output data/kitti/drive_0005_pair
python tools/kitti_bin_to_pcd.py --input data/kitti/drive_0005_pair/0000000000.bin --output data/kitti/drive_0005_pair/0000000000.pcd
python tools/kitti_bin_to_pcd.py --input data/kitti/drive_0005_pair/0000000001.bin --output data/kitti/drive_0005_pair/0000000001.pcd
```

脚本用HTTP Range获取两帧和时间戳约4.15MB，检查ZIP条目与CRC；BIN按小端float32 XYZI转换，payload与强度保留。
原始BIN/转换PCD保存在Git忽略的data/kitti，不提交仓库。ICP使用XYZ，Velodyne坐标x前、y左、z上。

## 3. 配置DLL路径并运行真实帧对

source为帧1，target为帧0；0.3m体素、最大迭代100、评估距离0.5m，与README道路实验配置一致。
输出路径pair.json必须尚不存在；重复运行时换一个新文件名。

```powershell
$pair = 'data/kitti/drive_0005_pair'
$savedPath = $env:Path
try {
  $ucrtBin = Split-Path -Parent (Get-Command g++.exe).Source
  $env:Path = "$((Resolve-Path .local-deps/pcl-1.15.1/bin).Path);$ucrtBin;$savedPath"
  ./build-release-ready/lidar_icp.exe --source "$pair/0000000001.pcd" --target "$pair/0000000000.pcd" --voxel-size 0.3 --max-iterations 100 --evaluation-distance 0.5 --output build-release-ready/pair.json
} finally {
  $env:Path = $savedPath
}
```

自定义依赖路径时，将上面PCL bin路径替换为实际DependencyRoot下的pcl-1.15.1/bin。
PATH只在当前进程内临时修改，不要求复制DLL到源码或系统目录。

JSON同时写stdout及--output文件；日志写stderr。主要字段：

- initial_T_target_source、T_target_source及pose：source到target，长度米、角度弧度。
- converged、accepted和rejection_reason：求解器收敛与应用质量判定分开。
- fitness_m2、rmse_m、inliers、inlier_ratio：不同含义的几何匹配指标。
- configuration和source_points/target_points：实际配置、原始/有限/输出点数。

默认质量参数为min_inliers=3、min_inlier_ratio=0.5、max_rmse_m=0.2。
拒绝结果的有效pose/T为null，diagnostic_T_target_source只作诊断。
退出码0=接受、2=参数/语义错误、3=读取/运行错误、4=未收敛或质量拒绝。
truth仅参与评分；没有提供真值时位姿误差为null。完整选项与矩阵文件约定见 [INTERFACES](INTERFACES.md)。

## 4. 合成数据与实验复现

在相同DLL PATH环境中，可运行生成器：

```powershell
./build-release-ready/generate_test_data.exe --output build-release-ready/synthetic-demo --seed 20261027
```

输出source.pcd、target.pcd、truth.txt和metadata.json；truth为4×4 T_target_source。
已知变换实验应显式传--truth评分，--initial作为独立的初始化输入，二者语义不同。
完整人工/道路实验驱动、绘图库版本和36组复现命令见 [EXPERIMENTS](EXPERIMENTS.md)。
驱动使用--sweep --repeated-structure；work/output/figures每次使用三个新目录。

## 5. 测试与归档核验

第一步的verify_dependencies.ps1已经执行完整CTest。普通测试离线运行，不下载道路数据。
现有固定环境验证结果为CTest10/10；内部场景组数不重复计入CTest总数。

无需道路数据即可核对公开归档、六图和受审源码：

```powershell
python tools/validate_experiments.py --metrics results/metrics/remediation --figures results/figures/module-c-v2 --reference results/metrics/main-review --skip-inputs --source-root .
```

此模式不核查缺席的原始输入文件。需要完整输入检查时去掉--skip-inputs，并按原运行路径准备相应文件；
重新运行实验生成的新归档应使用自身work目录和provenance核验。历史源码归档须显式指定对应快照。
配置/二进制/输入/图像溯源、辅助几何检查及审查记录见 [EXPERIMENTS](EXPERIMENTS.md)和 [REVIEW_REPORT_V2](REVIEW_REPORT_V2.md)。
