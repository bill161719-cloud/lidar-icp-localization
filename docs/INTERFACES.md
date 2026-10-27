# 接口契约 v1

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

输入至少各 3 个有限点；配置迭代数 >0，距离 >0 且有限，epsilon >=0 且有限。
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
平移误差 ||t_est-t_gt||；旋转误差 acos(clamp((trace(R_gtᵀR_est)-1)/2,-1,1))，返回弧度。
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

生成器建议 CLI：`generate_test_data --output <dir> --seed <uint>`，输出 source.pcd、target.pcd、
truth.txt（4×4 T_target_source）和元信息（种子、参数、单位、方向、许可）。最终参数由主对话接入。
真实 .bin 按每点四个小端 float32 x,y,z,intensity 读取；长度必须为 16 字节整数倍，验证有限性，禁止当文本。
记录数据集版本/序列/帧号/许可、转换、外参方向、是否去畸变；无标定不跨相机/LiDAR比较。
计划 CLI：`lidar_icp --source <pcd> --target <pcd> [--initial <matrix.txt>] [--visualize]`，尚未实现。
退出码约定：0 成功；2 参数/输入错误；3 运行或 IO 错误；4 ICP 未收敛或质量拒绝。
CSV 至少包含帧 ID、配置、点数、converged、fitness_m2、rmse_m、inliers、inlier_ratio、elapsed_ms、
有真值时的 translation_error_m、rotation_error_rad；未知写空值或 NaN，禁止写 0 伪装已测。
