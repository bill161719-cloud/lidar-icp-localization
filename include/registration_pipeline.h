#pragma once

#include "cloud_processor.h"
#include "icp_registration.h"
#include <cstddef>
#include <string>

namespace lidar {
// Application policy, independent of PCL's convergence flag. Units: metres.
struct RegistrationQualityConfig {
    std::size_t min_inliers = 3;
    double min_inlier_ratio = 0.5;
    double max_rmse_m = 0.2;
};

struct RegistrationQuality {
    bool accepted = false;
    std::string reason;
};

struct PipelineConfig {
    PreprocessConfig preprocessing;
    IcpConfig icp;
    RegistrationQualityConfig quality;
};

struct PipelineResult {
    PreprocessResult source;
    PreprocessResult target;
    IcpResult registration;
    RegistrationQuality quality;
};

RegistrationQuality assessRegistration(const IcpResult& result,
                                        const RegistrationQualityConfig& config = {});
PipelineResult runRegistration(const std::string& source_pcd,
                                const std::string& target_pcd,
                                const PipelineConfig& config = {},
                                const Eigen::Matrix4f& initial_T_target_source =
                                    Eigen::Matrix4f::Identity());
}  // namespace lidar
