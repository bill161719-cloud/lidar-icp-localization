#pragma once

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

// 保留非有限点；读取失败抛 runtime_error，空点云/无有限点抛 invalid_argument。
CloudPtr loadPcd(const std::string& path);
// 不信任 is_dense，始终逐点检查 XYZ；输出独立分配。
CloudPtr removeNonFinite(const CloudConstPtr& input);
// 输入必须全部有限；体素边长单位为米，必须有限且大于零。
CloudPtr voxelDownsample(const CloudConstPtr& input, float voxel_size_m);
// 清理后下采样；通过 std::clog 输出点数及有限点/输出点的 XYZ 范围（米）。
PreprocessResult preprocess(const CloudConstPtr& input,
                            const PreprocessConfig& config = {});
}  // namespace lidar
