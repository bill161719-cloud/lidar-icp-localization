#pragma once

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
    // 列向量：p_target = T_target_source * p_source，包含初值累积。
    Eigen::Matrix4f T_target_source = Eigen::Matrix4f::Identity();
    CloudPtr aligned;
    // PCL 默认无限范围单向最近邻平方距离均值，单位 m²，不是 RMSE。
    double fitness_m2 = std::numeric_limits<double>::quiet_NaN();
    MatchMetrics matches;
    // 只计 align 调用，steady_clock；不含误差评估。
    double elapsed_ms = 0.0;
};
// 单向最近邻，门限包含等号；零内点时 RMSE 为 NaN，比例分母为 source 点数。
MatchMetrics evaluateAlignment(const CloudConstPtr& aligned_source,
                               const CloudConstPtr& target,
                               double max_distance_m);
// 输入必须全部有限且各至少三点；无效输入抛 invalid_argument。
// 未收敛时矩阵和 aligned 仅供诊断；收敛也不保证正确匹配。
// source=curr、target=prev，且静态场景/帧顺序/安装外参成立时：
// T_prev_curr = inverse(W_prev) * W_curr，其中 W 为 world<-lidar 位姿。
// 平移以 target 坐标表示，不能无条件解释为车辆主动运动。
IcpResult registerIcp(const CloudConstPtr& source, const CloudConstPtr& target,
                      const IcpConfig& config = {},
                      const Eigen::Matrix4f& initial_T_target_source =
                          Eigen::Matrix4f::Identity());
}  // namespace lidar
