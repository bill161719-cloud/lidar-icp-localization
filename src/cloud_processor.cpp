#include "cloud_processor.h"

#include <pcl/common/common.h>
#include <pcl/conversions.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/io/pcd_io.h>
#include <algorithm>
#include <charconv>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace lidar {
namespace {
// PCL's ASCII reader can silently turn malformed tokens into zero. Validate
// before passing the body to PCL; binary encodings keep PCL's decoding path.
void validateAscii(const std::string& path, const pcl::PCLPointCloud2& header,
                   unsigned int offset) {
    std::ifstream input(path, std::ios::binary);
    input.seekg(offset);
    const auto fail = [&] { throw std::runtime_error("PCD ASCII 数字或行格式非法: " + path); };
    static const std::regex decimal(R"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)");
    std::size_t points = 0;
    const auto expected = static_cast<std::size_t>(header.width) * header.height;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream row(line);
        row >> std::ws;
        if (row.eof() || row.peek() == '#') continue;
        if (++points > expected) fail();
        for (const auto& field : header.fields) {
            for (std::uint32_t component = 0; component < field.count; ++component) {
                std::string token;
                if (!(row >> token)) fail();
                std::string lower = token;
                std::transform(lower.begin(), lower.end(), lower.begin(),
                               [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
                const auto first = lower.find_first_not_of("+-");
                const bool special = first != std::string::npos && first <= 1 &&
                    (lower.substr(first) == "nan" || lower.substr(first) == "inf" ||
                     lower.substr(first) == "infinity");
                const bool floating = field.datatype == pcl::PCLPointField::FLOAT32 ||
                                      field.datatype == pcl::PCLPointField::FLOAT64;
                if (special) {
                    if (!floating) fail();
                    continue; // Explicit NaN/Inf are intentionally cleaned later.
                }
                if (!std::regex_match(token, decimal)) fail();
                const char* begin = token.data() + (token.front() == '+' ? 1 : 0);
                double value = 0;
                const auto parsed = std::from_chars(begin, token.data() + token.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != token.data() + token.size() ||
                    !std::isfinite(value)) fail();
                if (field.datatype == pcl::PCLPointField::FLOAT32 &&
                    (std::abs(value) > std::numeric_limits<float>::max() ||
                     (value != 0 && static_cast<float>(value) == 0))) fail();
                if (!floating) {
                    // Integer auxiliary fields must not be parsed as decimal floats.
                    const bool isSigned = field.datatype == pcl::PCLPointField::INT8 ||
                        field.datatype == pcl::PCLPointField::INT16 || field.datatype == pcl::PCLPointField::INT32;
                    const int bits = 8 * pcl::getFieldSize(field.datatype);
                    if (bits <= 0 || bits > 32 || std::floor(value) != value ||
                        token.find_first_of(".eE") != std::string::npos ||
                        value < (isSigned ? -std::ldexp(1.0, bits-1) : 0.0) ||
                        value >= std::ldexp(1.0, isSigned ? bits-1 : bits)) fail();
                }
            }
        }
        row >> std::ws;
        if (!row.eof()) fail();
    }
    if (input.bad() || points != expected) fail();
}

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
    int version = 0, dataType = 0;
    unsigned int offset = 0;
    pcl::PCDReader reader;
    if (reader.readHeader(path, encoded, output->sensor_origin_,
                          output->sensor_orientation_, version, dataType, offset) < 0) {
        throw std::runtime_error("PCD 读取失败: " + path);
    }
    for (const auto* name : {"x", "y", "z"}) {
        bool found = false;
        for (const auto& field : encoded.fields) {
            if (field.name == name && field.count == 1 &&
                (field.datatype == pcl::PCLPointField::FLOAT32 ||
                 field.datatype == pcl::PCLPointField::FLOAT64)) {
                found = true;
            }
        }
        if (!found) {
            throw std::runtime_error("PCD 缺少单值浮点 XYZ 字段: " + path);
        }
    }
    if (encoded.width == 0 || encoded.height == 0) {
        throw std::invalid_argument("PCD 点云为空: " + path);
    }
    if (dataType == 0) validateAscii(path, encoded, offset);
    if (pcl::io::loadPCDFile(path, encoded, output->sensor_origin_,
                            output->sensor_orientation_) < 0) {
        throw std::runtime_error("PCD 读取失败: " + path);
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
