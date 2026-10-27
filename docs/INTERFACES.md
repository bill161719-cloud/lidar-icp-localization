# 接口契约 v1.1

本文件是模块开工依据。以下头文件由所属模块在功能阶段创建；初始化不提供伪实现。
共享类型已落盘于 include/cloud_types.h。所有声明均位于 `namespace lidar`。

## 点云与错误

`Point=pcl::PointXYZ; Cloud=pcl::PointCloud<Point>; CloudPtr=Cloud::Ptr; CloudConstPtr=Cloud::ConstPtr`。
第一版算法只使用 XYZ；KITTI intensity 转换时可保留在原始数据，但不得无记录改变坐标。
函数不修改输入；返回的点云独立分配。nullptr/空点云/无有限点、无效数值参数抛 `std::invalid_argument`；
读取/保存失败抛 `std::runtime_error`；主程序捕获并输出上下文、非零退出。
ICP 正常执行但未收敛通过结果状态表达，不抛异常；不得把单位矩阵默认值当成功结果。

## 模块 A：cloud_processor.h

```cpp
#include "cloud_types.h"
#include <cstddef>
#include <string>
namespace lidar {
struct PreprocessConfig { float voxel_size_m = 0.2F; };
struct PreprocessResult {
    CloudPtr cloud;
    std::size_t input_points = 0;
    std::size_t finite_points = 0;
    std::size_t output_points = 0;
};
CloudPtr loadPcd(const std::string& path);
CloudPtr removeNonFinite(const CloudConstPtr& input);
CloudPtr voxelDownsample(const CloudConstPtr& input, float voxel_size_m);
PreprocessResult preprocess(const CloudConstPtr& input,
                            const PreprocessConfig& config = {});
}
```

voxel_size_m 必须有限且 >0。loadPcd 保留非有限点供清理；至少有一个有限 XYZ。
removeNonFinite 显式检查每个 XYZ，即使 is_dense=true。voxelDownsample 输入必须全部有限；否则抛异常；
preprocess 串联清理和下采样。原始点数包括非法点，finite_points 为清理后数量。

## 模块 B：icp_registration.h

```cpp
#include "cloud_types.h"
#include <Eigen/Core>
#include <cstddef>
#include <limits>
namespace lidar {
struct IcpConfig {
    int max_iterations = 60;
    double max_correspondence_distance_m = 1.0;
    double transformation_epsilon = 1e-8;
    double euclidean_fitness_epsilon = 1e-6;
    double evaluation_distance_m = 1.0;
};
struct MatchMetrics {
    double rmse_m = std::numeric_limits<double>::quiet_NaN();
    std::size_t inliers = 0;
    double inlier_ratio = 0.0;
};
struct IcpResult {
    bool converged = false;
    Eigen::Matrix4f T_target_source = Eigen::Matrix4f::Identity();
    CloudPtr aligned;
    double fitness_m2 = std::numeric_limits<double>::quiet_NaN();
    MatchMetrics matches;
    double elapsed_ms = 0.0;
};
MatchMetrics evaluateAlignment(const CloudConstPtr& aligned_source,
                               const CloudConstPtr& target,
                               double max_distance_m);
IcpResult registerIcp(const CloudConstPtr& source, const CloudConstPtr& target,
                      const IcpConfig& config = {},
                      const Eigen::Matrix4f& initial_T_target_source =
                          Eigen::Matrix4f::Identity());
}
```

registerIcp 输入点云必须全部 XYZ 有限且各至少 3 点；NaN/Inf 不在 B 中隐式清理，出现则抛 invalid_argument。
evaluateAlignment 输入非空、全部 XYZ 有限，不要求 3 点；max_distance_m 有限且 >0。
配置迭代数 >0，距离 >0 且有限，epsilon >=0 且有限。
初值必须合法 SE(3)，结果包含初值累积后的最终变换，不是额外增量。
ICP 局部最优，hasConverged 不代表匹配正确。未收敛时矩阵和 aligned 只作诊断，主程序不得作为有效位姿。
fitness_m2 明确采用 PCL getFitnessScore() 默认无限范围的单向最近邻平方距离均值，单位 m²，
不可称为 RMSE。matches 单独计算 aligned source 到 target 的最近邻，在 evaluation_distance_m
以内的点对计算 sqrt(sum(d²)/inliers)；比例分母为 aligned source 点数，零内点返回 NaN。
elapsed_ms 只计 ICP align 调用，用 steady_clock；不含 IO、预处理与误差评估。
不得通过逼迫 ICP 在每个不重叠场景都返回 false 来测试；需同时检查几何误差/内点率。

## 模块 B：pose_utils.h

```cpp
#include <Eigen/Core>
#include <Eigen/Geometry>
namespace lidar {
struct PoseComponents {
    Eigen::Matrix3d rotation;
    Eigen::Vector3d translation_m;
    Eigen::Quaterniond quaternion;
};
bool isValidTransform(const Eigen::Matrix4f& T, double tolerance = 1e-4);
PoseComponents decomposeTransform(const Eigen::Matrix4f& T);
double translationErrorM(const Eigen::Matrix4f& estimated,
                         const Eigen::Matrix4f& ground_truth);
double rotationErrorRad(const Eigen::Matrix4f& estimated,
                        const Eigen::Matrix4f& ground_truth);
}
```

有效矩阵：全有限、末行 [0,0,0,1]、RᵀR≈I、det(R)≈+1；tolerance 有限且 >0，
否则 isValidTransform 返回 false；其余函数对非法变换抛 invalid_argument。
平移误差 ||t_est-t_gt||；旋转误差的 SO(3) 数学定义为 acos(clamp((trace(R_gtᵀR_est)-1)/2,-1,1))，返回弧度。
实现使用归一化四元数相对旋转的最短角（2*atan2(||v||,|w|)），与该定义数学等价，
避免 float32 矩阵的 trace 舍入使微小旋转误差丢失或产生数值底噪；先验合法性检查不变。
四元数输出标明 w,x,y,z；不强制欧拉角。需要欧拉角时明确轴顺序，不默认解释。

## 坐标、方向、真值

列向量，右手系，长度米，内部角度弧度；显示度数必须标记单位。
`p_target = T_target_source * p_source`，T=[R t; 0 1]，平移以 target 坐标表示。
人工实验先取 source，构造 target=T_gt*source，因此期望 ICP 结果就是 T_gt，不能用逆矩阵验收。
默认初值单位阵只适用于运动小、重叠充足的情况；实验需报告显式初值。

真实 KITTI Velodyne 常用 x 前、y 左、z 上。不得把相机坐标真值直接与 LiDAR 结果比较。
若 world<-lidar 的位姿为 W_prev、W_curr，source=curr、target=prev，
则 T_prev_curr = inverse(W_prev)*W_curr。相机位姿先用带方向的外参转换到 LiDAR 再计算。
变换点坐标与车辆主动运动是不同语义；须确认帧顺序、传感器安装和外参后才解释实际运动。

## 模块 C 与主程序

生成器 v1 必须支持 CLI：`generate_test_data --output <dir> --seed <uint>`，输出 source.pcd、target.pcd、
truth.txt（4×4 T_target_source，逐行空白分隔、无标题）和 metadata.json（种子、参数、单位、方向、许可）。
必须支持 --help；seed 为 uint32 十进制，同种子/配置在同一工具链下复现相同输出；
输出目录可新建，但存在同名输出文件时拒绝覆盖，返回非零。其他生成参数由 C 提建议给主对话。
真实 .bin 按每点四个小端 float32 x,y,z,intensity 读取；长度必须为 16 字节整数倍，验证有限性，禁止当文本。
记录数据集版本/序列/帧号/许可、转换、外参方向、是否去畸变；无标定不跨相机/LiDAR比较。
计划 CLI：`lidar_icp --source <pcd> --target <pcd> [--initial <matrix.txt>] [--visualize]`，尚未实现。
退出码约定：0 成功；2 参数/输入错误；3 运行或 IO 错误；4 ICP 未收敛或质量拒绝。
CSV 至少包含帧 ID、配置、点数、converged、fitness_m2、rmse_m、inliers、inlier_ratio、elapsed_ms、
有真值时的 translation_error_m、rotation_error_rad；未知写空值或 NaN，禁止写 0 伪装已测。

## 模块编译与自动测试入口

主对话已配置按源文件存在性启用目标；模块不改共享 CMakeLists.txt，不创建占位实现来伪装完成。
添加新文件后必须重新执行 CMake 配置（verify_dependencies.ps1 会自动配置），不能只执行旧 build。
所有库使用 C++17，公开继承 lidar_project_options 与 lidar_dependencies（含 Eigen/PCL 和 include/）。

| 模块 | 触发文件 | 库/程序目标 | CTest 可执行文件（需自带 main） |
|---|---|---|---|
| A | src/cloud_processor.cpp + include/cloud_processor.h | cloud_processing | tests/test_cloud_processor.cpp -> test_cloud_processor |
| B 位姿 | src/pose_utils.cpp + include/pose_utils.h | pose_utils | tests/test_pose.cpp -> test_pose |
| B 配准 | src/icp_registration.cpp + include/icp_registration.h；要求 pose_utils 已存在 | icp_registration，公开链接 pose_utils | tests/test_icp.cpp -> test_icp |
| C | tools/generate_test_data.cpp | generate_test_data | 本阶段不预注册未实现的实验测试；C 提交明确的生成器/实验验证命令 |

测试程序不依赖额外测试框架，使用显式条件判断和非零退出；测试工作目录固定为所属 worktree 根目录，
临时文件写入 build*/ 下（自建唯一子目录），不得修改 data/sample 原始数据或源码，也不得依赖其他 worktree 的模块文件。
A、B 可并行：B 测试自行构造有限点云，不依赖 A 的实现；B 先实现 B01，再实现 B02。
C01 生成器可独立开发；C03 真实完整实验依赖主对话集成 A/B/C01 和 C02 的数据准备。
当前 4 个依赖/bootstrap 测试不是 A/B/C 验收测试；模块交付后必须出现相应新测试并通过。

## 首轮集成补充：流水线、质量门禁与 CLI

主对话维护 include/registration_pipeline.h、src/registration_pipeline.cpp、src/main.cpp 和 tests/test_pipeline.py。
runRegistration(source_pcd, target_pcd, PipelineConfig, initial_T_target_source) 串联读取、清理、体素、ICP、质量检查，
返回 PipelineResult（source/target 预处理统计、原始 IcpResult、quality.accepted 和拒绝原因）。
assessRegistration(IcpResult, RegistrationQualityConfig) 将应用质量策略与 PCL converged 分开。

默认 RegistrationQualityConfig：min_inliers=3、min_inlier_ratio=0.5、max_rmse_m=0.2；参数必须有限、
最小内点数 >=3、比例在 [0,1]、RMSE 上限 >0。只有收敛、最终 SE(3)/点云/指标有效且全部门限通过才 accepted=true。
阈值应按尺度/噪声/重叠调整；质量通过也不能证明场景无退化或位姿必然正确。

CLI：lidar_icp --source <pcd> --target <pcd>，可选 --initial <matrix.txt>、--truth <matrix.txt>、--output <report.json>，
--voxel-size、--max-iterations、--max-correspondence-distance、--evaluation-distance、--min-inliers、--min-inlier-ratio、--max-rmse。
矩阵文件严格为 16 个逐行数字，无标题、无多余字段，必须为合法 SE(3)。--truth 只用于评分，不能参与 ICP 初值或质量决策。
PCD VIEWPOINT 仅保留为元信息，不隐式作为初始位姿或坐标转换；source/target 的 XYZ 须已经使用米和约定坐标系。

stdout 输出 schema_version=1 的 JSON，日志写 stderr；--output 可保存同一 JSON，拒绝覆盖已有文件。
主要键：source/target、configuration、source_points/target_points、initial_T_target_source、converged、accepted、
rejection_reason、fitness_m2、rmse_m、inliers、inlier_ratio、elapsed_ms、T_target_source、pose、diagnostic_T_target_source。
pose 含 rotation（3×3）、translation_m、quaternion_wxyz。elapsed_ms 仍仅为 ICP align 时间。
失败或质量拒绝时 T_target_source/pose 为 null，诊断矩阵不作为有效位姿；非有限 JSON 数字写 null，零内点 RMSE 不写 0。
仅在 accepted 且提供 --truth 时输出 translation_error_m/rotation_error_rad，否则为 null，禁止用零冒充未知真值误差。
退出码：0 已接受；2 参数/数据语义非法；3 读取/保存/运行错误；4 未收敛或质量拒绝。
输入/IO 失败不生成配准 JSON，实验脚本应保留退出码和 stderr，不能将其记录为成功。
