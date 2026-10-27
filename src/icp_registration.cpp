#include "icp_registration.h"
#include "pose_utils.h"

#include <pcl/kdtree/kdtree_flann.h>
#include <pcl/registration/icp.h>
#include <chrono>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

namespace lidar {
namespace {
void requireCloud(const CloudConstPtr& cloud, std::size_t minimum, const char* name) {
    if (!cloud || cloud->size() < minimum) {
        throw std::invalid_argument(std::string(name) + " 点云为空或点数不足");
    }
    // 不相信 is_dense 标志，也不隐式清理输入。
    for (const auto& point : *cloud) {
        if (!std::isfinite(point.x) || !std::isfinite(point.y) || !std::isfinite(point.z)) {
            throw std::invalid_argument(std::string(name) + " XYZ 必须全部有限");
        }
    }
}
void requirePositive(double value, const char* name) {
    if (!std::isfinite(value) || value <= 0.0) {
        throw std::invalid_argument(std::string(name) + " 必须有限且大于零");
    }
}
void requireEpsilon(double value, const char* name) {
    if (!std::isfinite(value) || value < 0.0) {
        throw std::invalid_argument(std::string(name) + " 必须有限且非负");
    }
}
}  // namespace

MatchMetrics evaluateAlignment(const CloudConstPtr& aligned_source,
                               const CloudConstPtr& target,
                               double max_distance_m) {
    requireCloud(aligned_source, 1, "aligned_source");
    requireCloud(target, 1, "target");
    requirePositive(max_distance_m, "max_distance_m");
    pcl::KdTreeFLANN<Point> tree;
    tree.setInputCloud(target);
    std::vector<int> indices(1);
    std::vector<float> distances(1);
    const double threshold_squared = max_distance_m * max_distance_m;
    double sum_squared = 0.0;
    MatchMetrics metrics;
    for (const auto& point : *aligned_source) {
        if (tree.nearestKSearch(point, 1, indices, distances) == 1
            && std::isfinite(distances[0]) && distances[0] <= threshold_squared) {
            sum_squared += static_cast<double>(distances[0]);
            ++metrics.inliers;
        }
    }
    metrics.inlier_ratio = static_cast<double>(metrics.inliers) / aligned_source->size();
    if (metrics.inliers != 0) {
        metrics.rmse_m = std::sqrt(sum_squared / metrics.inliers);
    }
    return metrics;
}

IcpResult registerIcp(const CloudConstPtr& source, const CloudConstPtr& target,
                      const IcpConfig& config,
                      const Eigen::Matrix4f& initial_T_target_source) {
    requireCloud(source, 3, "source");
    requireCloud(target, 3, "target");
    if (config.max_iterations <= 0) {
        throw std::invalid_argument("max_iterations 必须大于零");
    }
    requirePositive(config.max_correspondence_distance_m, "max_correspondence_distance_m");
    requirePositive(config.evaluation_distance_m, "evaluation_distance_m");
    requireEpsilon(config.transformation_epsilon, "transformation_epsilon");
    requireEpsilon(config.euclidean_fitness_epsilon, "euclidean_fitness_epsilon");
    if (!isValidTransform(initial_T_target_source)) {
        throw std::invalid_argument("initial_T_target_source 必须为合法 SE(3)");
    }
    pcl::IterativeClosestPoint<Point, Point> icp;
    icp.setInputSource(source);
    icp.setInputTarget(target);
    icp.setMaximumIterations(config.max_iterations);
    icp.setMaxCorrespondenceDistance(config.max_correspondence_distance_m);
    icp.setTransformationEpsilon(config.transformation_epsilon);
    icp.setEuclideanFitnessEpsilon(config.euclidean_fitness_epsilon);
    IcpResult result;
    result.aligned = CloudPtr(new Cloud);
    const auto start = std::chrono::steady_clock::now();
    icp.align(*result.aligned, initial_T_target_source);
    const auto finish = std::chrono::steady_clock::now();
    result.elapsed_ms = std::chrono::duration<double, std::milli>(finish - start).count();
    result.converged = icp.hasConverged();
    result.T_target_source = icp.getFinalTransformation();
    result.fitness_m2 = icp.getFitnessScore();
    result.matches = evaluateAlignment(result.aligned, target, config.evaluation_distance_m);
    return result;
}
}  // namespace lidar
