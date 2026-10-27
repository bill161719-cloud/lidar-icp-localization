#include "icp_registration.h"
#include "pose_utils.h"

#include <pcl/common/transforms.h>
#include <cmath>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>

namespace {
void check(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}
template <class Function>
void rejects(Function function) {
    try { function(); } catch (const std::invalid_argument&) { return; }
    throw std::runtime_error("预期 invalid_argument");
}
lidar::CloudPtr makeCloud() {
    lidar::CloudPtr cloud(new lidar::Cloud);
    std::mt19937 generator(20261027);
    std::uniform_real_distribution<float> sample(-1.0F, 1.0F);
    for (int i = 0; i < 400; ++i) {
        const float x = sample(generator), y = sample(generator), z = sample(generator);
        cloud->push_back(lidar::Point(2.5F * x + 0.2F * y * y, 1.3F * y, 0.8F * z + 0.1F * x));
    }
    return cloud;
}
lidar::CloudPtr transformed(const lidar::CloudConstPtr& cloud, const Eigen::Matrix4f& T) {
    lidar::CloudPtr output(new lidar::Cloud);
    pcl::transformPointCloud(*cloud, *output, T);
    return output;
}
Eigen::Matrix4f makeTransform(float angle, const Eigen::Vector3f& translation) {
    Eigen::Matrix4f T = Eigen::Matrix4f::Identity();
    T.topLeftCorner<3, 3>() = Eigen::AngleAxisf(angle, Eigen::Vector3f(1, 2, 3).normalized()).toRotationMatrix();
    T.topRightCorner<3, 1>() = translation;
    return T;
}
void verifyTruth(const lidar::CloudConstPtr& source, const Eigen::Matrix4f& truth,
                 const Eigen::Matrix4f& initial, const char* label) {
    const auto target = transformed(source, truth);
    const lidar::Cloud sourceBefore = *source, targetBefore = *target;
    lidar::IcpConfig config;
    config.max_correspondence_distance_m = 0.6;
    config.evaluation_distance_m = 0.05;
    config.max_iterations = 100;
    const auto result = lidar::registerIcp(source, target, config, initial);
    const double translation = lidar::translationErrorM(result.T_target_source, truth);
    const double rotation = lidar::rotationErrorRad(result.T_target_source, truth);
    std::cout << label << ": translation_error_m=" << translation
              << " rotation_error_rad=" << rotation << " fitness_m2=" << result.fitness_m2
              << " rmse_m=" << result.matches.rmse_m << " inlier_ratio=" << result.matches.inlier_ratio
              << " elapsed_ms=" << result.elapsed_ms << '\n';
    check(result.converged, "干净真值场景应收敛");
    check(lidar::isValidTransform(result.T_target_source), "输出 SE(3)");
    check(translation < 0.01 && rotation < std::acos(-1.0) / 1800.0, "真值误差 <0.01m、0.1度");
    check(result.matches.inliers == source->size() && result.matches.inlier_ratio == 1.0
          && result.matches.rmse_m < 0.001, "真值独立 RMSE/内点");
    check(result.fitness_m2 >= 0 && result.fitness_m2 < 1e-6, "fitness 单位 m²");
    check(std::isfinite(result.elapsed_ms) && result.elapsed_ms >= 0, "align 耗时");
    check(result.aligned && result.aligned.get() != source.get() && result.aligned.get() != target.get(), "输出独立分配");
    const auto expected = transformed(source, result.T_target_source);
    for (std::size_t i = 0; i < source->size(); ++i) {
        check((source->at(i).getVector3fMap() - sourceBefore.at(i).getVector3fMap()).norm() == 0, "source 未修改");
        check((target->at(i).getVector3fMap() - targetBefore.at(i).getVector3fMap()).norm() == 0, "target 未修改");
        check((result.aligned->at(i).getVector3fMap() - expected->at(i).getVector3fMap()).norm() < 1e-6F,
              "aligned 与最终累积矩阵一致");
    }
}
void testMetrics() {
    lidar::CloudPtr source(new lidar::Cloud), target(new lidar::Cloud);
    target->push_back(lidar::Point(0, 0, 0));
    source->push_back(lidar::Point(0, 0, 0));
    source->push_back(lidar::Point(1, 0, 0));
    source->push_back(lidar::Point(3, 0, 0));
    auto metrics = lidar::evaluateAlignment(source, target, 1.0);
    check(metrics.inliers == 2 && std::abs(metrics.inlier_ratio - 2.0 / 3) < 1e-12
          && std::abs(metrics.rmse_m - std::sqrt(0.5)) < 1e-12, "手算门限 RMSE，包含边界");
    metrics = lidar::evaluateAlignment(target, source, 1.0);
    check(metrics.inliers == 1 && metrics.inlier_ratio == 1 && metrics.rmse_m == 0, "单向指标与小点云");
    lidar::CloudPtr far(new lidar::Cloud);
    far->push_back(lidar::Point(10, 0, 0));
    metrics = lidar::evaluateAlignment(far, target, 1.0);
    check(metrics.inliers == 0 && metrics.inlier_ratio == 0 && std::isnan(metrics.rmse_m), "零内点 NaN");
}
void testInvalid(const lidar::CloudPtr& cloud) {
    lidar::CloudPtr empty(new lidar::Cloud), small(new lidar::Cloud);
    small->push_back(lidar::Point(0, 0, 0)); small->push_back(lidar::Point(1, 0, 0));
    for (const auto& invalid : {lidar::CloudPtr{}, empty, small}) {
        rejects([&] { lidar::registerIcp(invalid, cloud); });
        rejects([&] { lidar::registerIcp(cloud, invalid); });
    }
    for (const auto& invalid : {lidar::CloudPtr{}, empty}) {
        rejects([&] { lidar::evaluateAlignment(invalid, cloud, 1); });
        rejects([&] { lidar::evaluateAlignment(cloud, invalid, 1); });
    }
    for (float value : {std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity()}) {
        for (int axis = 0; axis < 3; ++axis) {
            lidar::CloudPtr invalid(new lidar::Cloud(*cloud));
            invalid->is_dense = true;
            invalid->at(0).getVector3fMap()[axis] = value;
            rejects([&] { lidar::registerIcp(invalid, cloud); });
            rejects([&] { lidar::registerIcp(cloud, invalid); });
            rejects([&] { lidar::evaluateAlignment(invalid, cloud, 1); });
            rejects([&] { lidar::evaluateAlignment(cloud, invalid, 1); });
        }
    }
    for (double value : {0.0, -1.0, std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::infinity()}) {
        rejects([&] { lidar::evaluateAlignment(cloud, cloud, value); });
        lidar::IcpConfig config;
        config.max_correspondence_distance_m = value;
        rejects([&] { lidar::registerIcp(cloud, cloud, config); });
        config = {}; config.evaluation_distance_m = value;
        rejects([&] { lidar::registerIcp(cloud, cloud, config); });
    }
    for (double value : {-1.0, std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::infinity()}) {
        lidar::IcpConfig config;
        config.transformation_epsilon = value;
        rejects([&] { lidar::registerIcp(cloud, cloud, config); });
        config = {}; config.euclidean_fitness_epsilon = value;
        rejects([&] { lidar::registerIcp(cloud, cloud, config); });
    }
    for (int count : {0, -1}) {
        lidar::IcpConfig config; config.max_iterations = count;
        rejects([&] { lidar::registerIcp(cloud, cloud, config); });
    }
    for (int type = 0; type < 4; ++type) {
        Eigen::Matrix4f invalid = Eigen::Matrix4f::Identity();
        if (type == 0) invalid(0, 0) = -1;
        if (type == 1) invalid(3, 0) = 1;
        if (type == 2) invalid(1, 1) = 2;
        if (type == 3) invalid(0, 3) = std::numeric_limits<float>::quiet_NaN();
        rejects([&] { lidar::registerIcp(cloud, cloud, {}, invalid); });
    }
    lidar::IcpConfig zeroEpsilon;
    zeroEpsilon.transformation_epsilon = zeroEpsilon.euclidean_fitness_epsilon = 0;
    check(lidar::registerIcp(cloud, cloud, zeroEpsilon).aligned != nullptr, "允许零 epsilon");
}
void testFailures(const lidar::CloudPtr& cloud) {
    const auto far = transformed(cloud, makeTransform(0, Eigen::Vector3f(100, 20, 0)));
    lidar::IcpConfig config;
    config.max_correspondence_distance_m = 0.01;
    config.evaluation_distance_m = 0.01;
    const auto failed = lidar::registerIcp(cloud, far, config);
    check(!failed.converged && failed.aligned && failed.aligned->size() == cloud->size(), "无对应点正常返回未收敛诊断");
    check(failed.matches.inliers == 0 && std::isnan(failed.matches.rmse_m) && failed.fitness_m2 > 100,
          "失败几何指标及无限范围 fitness");

    // 一个迭代可能被 PCL 标记为收敛，检查质量而不强迫其返回 false。
    const Eigen::Matrix4f truth = makeTransform(0.3F, Eigen::Vector3f(0.4F, -0.2F, 0.15F));
    config.max_iterations = 1;
    config.max_correspondence_distance_m = 1;
    config.evaluation_distance_m = 0.002;
    const auto limited = lidar::registerIcp(cloud, transformed(cloud, truth), config);
    check(limited.matches.inlier_ratio < 0.5 && lidar::translationErrorM(limited.T_target_source, truth) > 0.01,
          "迭代受限的差质量不能仅凭 converged 验收");
    std::cout << "受限迭代: converged=" << limited.converged << " inlier_ratio=" << limited.matches.inlier_ratio << '\n';
}
}  // namespace
int main() {
    try {
        const auto source = makeCloud();
        verifyTruth(source, Eigen::Matrix4f::Identity(), Eigen::Matrix4f::Identity(), "恒等");
        verifyTruth(source, makeTransform(0.05F, Eigen::Vector3f(0.08F, -0.04F, 0.03F)),
                    Eigen::Matrix4f::Identity(), "小运动/单位初值");
        verifyTruth(source, makeTransform(0.55F, Eigen::Vector3f(2, -1, 0.7F)),
                    makeTransform(0.52F, Eigen::Vector3f(1.96F, -0.98F, 0.68F)), "大运动/显式近初值");
        testMetrics();
        testInvalid(source);
        testFailures(source);
        std::cout << "B02 ICP 测试通过，固定种子 20261027，无显示窗口\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "B02 失败: " << error.what() << '\n'; return 1;
    }
}
