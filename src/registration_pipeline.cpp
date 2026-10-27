#include "registration_pipeline.h"
#include "pose_utils.h"

#include <cmath>
#include <stdexcept>

namespace lidar {
namespace {
void validateQualityConfig(const RegistrationQualityConfig& config) {
    if (config.min_inliers < 3 || !std::isfinite(config.min_inlier_ratio) ||
        config.min_inlier_ratio < 0.0 || config.min_inlier_ratio > 1.0 ||
        !std::isfinite(config.max_rmse_m) || config.max_rmse_m <= 0.0) {
        throw std::invalid_argument("Quality thresholds require min_inliers >= 3, "
                                    "min_inlier_ratio in [0,1], and finite max_rmse > 0");
    }
}
}  // namespace

RegistrationQuality assessRegistration(const IcpResult& result,
                                        const RegistrationQualityConfig& config) {
    validateQualityConfig(config);
    if (!result.converged) return {false, "icp_not_converged"};
    if (!isValidTransform(result.T_target_source)) return {false, "invalid_final_transform"};
    if (!result.aligned || result.aligned->empty()) return {false, "empty_alignment"};
    for (const auto& point : *result.aligned) {
        if (!std::isfinite(point.x) || !std::isfinite(point.y) || !std::isfinite(point.z)) {
            return {false, "non_finite_alignment"};
        }
    }
    if (!std::isfinite(result.fitness_m2) || result.fitness_m2 < 0.0 ||
        !std::isfinite(result.matches.inlier_ratio) || result.matches.inlier_ratio < 0.0 ||
        result.matches.inlier_ratio > 1.0 || result.matches.inliers > result.aligned->size()) {
        return {false, "invalid_match_metrics"};
    }
    if (result.matches.inliers < config.min_inliers) return {false, "insufficient_inliers"};
    if (result.matches.inlier_ratio < config.min_inlier_ratio) return {false, "low_inlier_ratio"};
    if (!std::isfinite(result.matches.rmse_m) || result.matches.rmse_m < 0.0 ||
        result.matches.rmse_m > config.max_rmse_m) {
        return {false, "invalid_or_high_rmse"};
    }
    return {true, ""};
}

PipelineResult runRegistration(const std::string& source_pcd,
                                const std::string& target_pcd,
                                const PipelineConfig& config,
                                const Eigen::Matrix4f& initial_T_target_source) {
    validateQualityConfig(config.quality);
    PipelineResult result;
    result.source = preprocess(loadPcd(source_pcd), config.preprocessing);
    result.target = preprocess(loadPcd(target_pcd), config.preprocessing);
    result.registration = registerIcp(result.source.cloud, result.target.cloud,
                                      config.icp, initial_T_target_source);
    result.quality = assessRegistration(result.registration, config.quality);
    return result;
}
}  // namespace lidar
