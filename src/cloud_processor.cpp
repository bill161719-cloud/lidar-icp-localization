#include "cloud_processor.h"

#include <pcl/common/common.h>
#include <pcl/conversions.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/io/pcd_io.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace lidar {
namespace {
bool finite(const Point& point) {
    return std::isfinite(point.x) && std::isfinite(point.y) && std::isfinite(point.z);
}

void requireCloud(const CloudConstPtr& input) {
    if (!input || input->empty()) {
        throw std::invalid_argument("点云为空或指针为 nullptr");
    }
}

void requireLeaf(float size) {
    if (!std::isfinite(size) || size <= 0.0F) {
        throw std::invalid_argument("voxel_size_m 必须有限且大于零");
    }
}

void appendBounds(std::ostream& out, const Cloud& cloud) {
    Point minimum, maximum;
    pcl::getMinMax3D(cloud, minimum, maximum);
    out << "x=[" << minimum.x << ", " << maximum.x << "] y=["
        << minimum.y << ", " << maximum.y << "] z=["
        << minimum.z << ", " << maximum.z << "] (m)";
}

// PCL 使用 float 倒数和 int32 网格，提前拒绝越界，避免原样返回或未定义转换。
void requireRepresentableGrid(const Cloud& cloud, float size) {
    const float inverse = 1.0F / size;
    if (!std::isfinite(inverse)) {
        throw std::invalid_argument("voxel_size_m 过小，PCL 无法表示其倒数");
    }
    Point minimum, maximum;
    pcl::getMinMax3D(cloud, minimum, maximum);
    const float low[] = {minimum.x, minimum.y, minimum.z};
    const float high[] = {maximum.x, maximum.y, maximum.z};
    const double limit = std::numeric_limits<std::int32_t>::max();
    double cells = 1.0;
    for (int axis = 0; axis < 3; ++axis) {
        const double first = std::floor(low[axis] * inverse);
        const double last = std::floor(high[axis] * inverse);
        const float span = (high[axis] - low[axis]) * inverse;
        if (!std::isfinite(first) || !std::isfinite(last) || !std::isfinite(span) ||
            first < std::numeric_limits<std::int32_t>::min() || last > limit) {
            throw std::invalid_argument("点云坐标与体素大小超出 PCL 网格索引范围");
        }
        cells *= std::max(last - first + 1.0, std::floor(static_cast<double>(span)) + 1.0);
        if (cells > limit) {
            throw std::invalid_argument("点云范围与体素大小导致 PCL 网格溢出");
        }
    }
}
}  // namespace

CloudPtr loadPcd(const std::string& path) {
    pcl::PCLPointCloud2 encoded;
    auto output = pcl::make_shared<Cloud>();
    if (pcl::io::loadPCDFile(path, encoded, output->sensor_origin_,
                             output->sensor_orientation_) < 0) {
        throw std::runtime_error("PCD 读取失败: " + path);
    }
    for (const auto* name : {"x", "y", "z"}) {
        bool found = false;
        for (const auto& field : encoded.fields) {
            if (field.name == name && field.count == 1) {
                found = true;
            }
        }
        if (!found) {
            throw std::runtime_error("PCD 缺少单值 XYZ 字段: " + path);
        }
    }
    if (encoded.width == 0 || encoded.height == 0) {
        throw std::invalid_argument("PCD 点云为空: " + path);
    }
    pcl::fromPCLPointCloud2(encoded, *output);
    for (const auto& point : *output) {
        if (finite(point)) {
            return output;
        }
    }
    throw std::invalid_argument("PCD 中没有有限 XYZ 点: " + path);
}

CloudPtr removeNonFinite(const CloudConstPtr& input) {
    requireCloud(input);
    auto output = pcl::make_shared<Cloud>();
    output->header = input->header;
    output->sensor_origin_ = input->sensor_origin_;
    output->sensor_orientation_ = input->sensor_orientation_;
    output->reserve(input->size());
    for (const auto& point : *input) {
        if (finite(point)) {
            output->push_back(point);
        }
    }
    if (output->empty()) {
        throw std::invalid_argument("点云中没有有限 XYZ 点");
    }
    output->is_dense = true;
    return output;
}

CloudPtr voxelDownsample(const CloudConstPtr& input, float voxel_size_m) {
    requireCloud(input);
    requireLeaf(voxel_size_m);
    for (const auto& point : *input) {
        if (!finite(point)) {
            throw std::invalid_argument("体素下采样要求所有 XYZ 点有限，请先清理点云");
        }
    }
    requireRepresentableGrid(*input, voxel_size_m);
    auto output = pcl::make_shared<Cloud>();
    pcl::VoxelGrid<Point> filter;
    filter.setInputCloud(input);
    filter.setLeafSize(voxel_size_m, voxel_size_m, voxel_size_m);
    filter.filter(*output);
    if (output->empty()) {
        throw std::runtime_error("PCL 体素下采样返回空点云");
    }
    for (const auto& point : *output) {
        if (!finite(point)) {
            throw std::runtime_error("PCL 体素质心计算溢出");
        }
    }
    output->is_dense = true;
    return output;
}

PreprocessResult preprocess(const CloudConstPtr& input, const PreprocessConfig& config) {
    requireLeaf(config.voxel_size_m);
    const auto cleaned = removeNonFinite(input);
    PreprocessResult result;
    result.input_points = input->size();
    result.finite_points = cleaned->size();
    result.cloud = voxelDownsample(cleaned, config.voxel_size_m);
    result.output_points = result.cloud->size();
    std::ostringstream summary;
    summary << "点云预处理: input_points=" << result.input_points
            << " finite_points=" << result.finite_points
            << " output_points=" << result.output_points << "\n有限点范围: ";
    appendBounds(summary, *cleaned);
    summary << "\n输出点范围: ";
    appendBounds(summary, *result.cloud);
    std::clog << summary.str() << '\n';
    return result;
}
}  // namespace lidar
