#include "cloud_processor.h"

#include <pcl/io/pcd_io.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
namespace fs = std::filesystem;
using namespace lidar;

void check(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

template <typename Exception, typename Action>
void expectThrow(Action action) {
    try {
        action();
    } catch (const Exception&) {
        return;
    }
    throw std::runtime_error("未抛出预期类型的异常");
}

bool coordinatesNear(float actual, float expected) {
    return std::abs(actual - expected) < 1e-5F;
}

CloudPtr sample() {
    auto cloud = pcl::make_shared<Cloud>();
    cloud->push_back(Point(0.1F, 0.2F, 0.3F));
    cloud->push_back(Point(0.3F, 0.4F, 0.5F));
    cloud->push_back(Point(1.2F, -0.2F, 2.4F));
    cloud->header.frame_id = "test_frame";
    cloud->sensor_origin_[0] = 4.0F;
    return cloud;
}

struct Fixtures {
    fs::path root;
    Fixtures() {
        fs::create_directories("build-test-cloud");
        const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
        for (int attempt = 0; attempt < 100; ++attempt) {
            root = fs::path("build-test-cloud") /
                   ("run-" + std::to_string(stamp) + "-" + std::to_string(attempt));
            if (fs::create_directory(root)) {
                return;
            }
        }
        throw std::runtime_error("无法创建独立测试目录");
    }
    ~Fixtures() {
        std::error_code error;
        for (const auto& entry : fs::directory_iterator(root)) {
            fs::remove(entry.path(), error);
        }
        fs::remove(root, error);
    }
    std::string path(const std::string& name) const { return (root / name).string(); }
    void write(const std::string& name, const std::string& content) const {
        std::ofstream file(path(name), std::ios::binary);
        file << content;
        check(static_cast<bool>(file), "写入测试 PCD 失败");
    }
};

std::string header(int count) {
    return "# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\n"
           "COUNT 1 1 1\nWIDTH " + std::to_string(count) +
           "\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS " + std::to_string(count) +
           "\nDATA ascii\n";
}

void testPcd(Fixtures& fixtures) {
    const auto original = sample();
    check(pcl::io::savePCDFileASCII(fixtures.path("ascii.pcd"), *original) == 0,
          "生成 ASCII PCD 失败");
    check(pcl::io::savePCDFileBinary(fixtures.path("binary.pcd"), *original) == 0,
          "生成 binary PCD 失败");
    check(pcl::io::savePCDFileBinaryCompressed(fixtures.path("compressed.pcd"), *original) == 0,
          "生成 compressed PCD 失败");
    for (const auto* name : {"ascii.pcd", "binary.pcd", "compressed.pcd"}) {
        const auto loaded = loadPcd(fixtures.path(name));
        check(loaded->size() == original->size(), "PCD 点数不符");
        for (std::size_t i = 0; i < loaded->size(); ++i) {
            check(coordinatesNear((*loaded)[i].x, (*original)[i].x) &&
                  coordinatesNear((*loaded)[i].y, (*original)[i].y) &&
                  coordinatesNear((*loaded)[i].z, (*original)[i].z), "PCD 坐标不符");
        }
        check(coordinatesNear(loaded->sensor_origin_[0], 4.0F), "PCD VIEWPOINT 未保留");
    }
    fixtures.write("double.pcd",
        "VERSION 0.7\nFIELDS x y z\nSIZE 8 8 8\nTYPE F F F\nCOUNT 1 1 1\n"
        "WIDTH 1\nHEIGHT 1\nPOINTS 1\nDATA ascii\n1.25 -2.5 3.75\n");
    const auto doubleCloud = loadPcd(fixtures.path("double.pcd"));
    check(doubleCloud->size() == 1 && coordinatesNear((*doubleCloud)[0].x, 1.25F) &&
          coordinatesNear((*doubleCloud)[0].y, -2.5F) &&
          coordinatesNear((*doubleCloud)[0].z, 3.75F), "float64 XYZ 转换失败");
    fixtures.write("mixed.pcd", header(3) + "0.1 0.2 0.3\nnan 1 2\n1 inf 2\n");
    const auto mixed = loadPcd(fixtures.path("mixed.pcd"));
    check(mixed->size() == 3 && std::isnan((*mixed)[1].x) &&
          std::isinf((*mixed)[2].y), "读取阶段未保留非有限点");
    check(removeNonFinite(mixed)->size() == 1, "读取后的无效点清理失败");
}

void testPcdErrors(Fixtures& fixtures) {
    expectThrow<std::runtime_error>([&] { loadPcd(fixtures.path("missing.pcd")); });
    fixtures.write("empty.pcd", "");
    expectThrow<std::runtime_error>([&] { loadPcd(fixtures.path("empty.pcd")); });
    fixtures.write("malformed.pcd", "this is not a point cloud\n");
    expectThrow<std::runtime_error>([&] { loadPcd(fixtures.path("malformed.pcd")); });
    fixtures.write("invalid.pcd", header(2) + "nan 0 0\n0 0 -inf\n");
    expectThrow<std::invalid_argument>([&] { loadPcd(fixtures.path("invalid.pcd")); });
    fixtures.write("missing-z.pcd",
        "VERSION 0.7\nFIELDS x y\nSIZE 4 4\nTYPE F F\nCOUNT 1 1\n"
        "WIDTH 1\nHEIGHT 1\nPOINTS 1\nDATA ascii\n0 0\n");
    expectThrow<std::runtime_error>([&] { loadPcd(fixtures.path("missing-z.pcd")); });
    fixtures.write("zero.pcd", header(0));
    expectThrow<std::invalid_argument>([&] { loadPcd(fixtures.path("zero.pcd")); });
}

void testCleaning() {
    const float nan = std::numeric_limits<float>::quiet_NaN();
    const float inf = std::numeric_limits<float>::infinity();
    for (bool dense : {false, true}) {
        auto cloud = sample();
        for (int axis = 0; axis < 3; ++axis) {
            for (float value : {nan, inf, -inf}) {
                Point bad(0, 0, 0);
                bad.data[axis] = value;
                cloud->push_back(bad);
            }
        }
        cloud->is_dense = dense;
        const auto cleaned = removeNonFinite(cloud);
        check(cleaned->size() == 3 && cleaned->is_dense, "未逐 XYZ 清理 NaN/Inf");
        check(cleaned->header.frame_id == "test_frame" &&
              coordinatesNear(cleaned->sensor_origin_[0], 4), "清理丢失坐标系元数据");
        check(cloud->size() == 12 && cloud->is_dense == dense &&
              std::isnan((*cloud)[3].x), "清理修改了输入");
        (*cleaned)[0].x = 42;
        check(coordinatesNear((*cloud)[0].x, 0.1F), "清理输出与输入共享数据");
    }
}

void testVoxel() {
    auto cloud = sample();
    cloud->is_dense = false;
    const auto output = voxelDownsample(cloud, 1.0F);
    check(output->size() == 2 && output->is_dense, "体素合并数量错误");
    bool centroid = false;
    bool isolated = false;
    for (const auto& point : *output) {
        centroid |= coordinatesNear(point.x, 0.2F) && coordinatesNear(point.y, 0.3F) && coordinatesNear(point.z, 0.4F);
        isolated |= coordinatesNear(point.x, 1.2F) && coordinatesNear(point.y, -0.2F) && coordinatesNear(point.z, 2.4F);
    }
    check(centroid && isolated, "体素质心或孤立点坐标错误");
    check(cloud->size() == 3 && coordinatesNear((*cloud)[0].x, 0.1F) && !cloud->is_dense,
          "体素滤波修改输入");
    (*output)[0].x = 42;
    check(coordinatesNear((*cloud)[0].x, 0.1F), "体素滤波输出未独立分配");
    const auto small = voxelDownsample(cloud, 0.05F);
    check(small->size() == cloud->size(), "小体素错误合并不同网格点");
    auto negative = pcl::make_shared<Cloud>();
    negative->push_back(Point(-0.1F, 0, 0));
    negative->push_back(Point(0.1F, 0, 0));
    check(voxelDownsample(negative, 1.0F)->size() == 2, "负坐标未按 floor 划分体素");
    auto singleton = pcl::make_shared<Cloud>();
    singleton->push_back(Point(1, 2, 3));
    check(voxelDownsample(singleton, 0.2F)->size() == 1, "单点云下采样失败");
}

void testInvalidInputs() {
    const CloudConstPtr null;
    const auto empty = pcl::make_shared<Cloud>();
    auto invalid = pcl::make_shared<Cloud>();
    invalid->push_back(Point(std::numeric_limits<float>::quiet_NaN(), 0, 0));
    for (const CloudConstPtr& cloud : {null, CloudConstPtr(empty), CloudConstPtr(invalid)}) {
        expectThrow<std::invalid_argument>([&] { removeNonFinite(cloud); });
        expectThrow<std::invalid_argument>([&] { voxelDownsample(cloud, 0.2F); });
        expectThrow<std::invalid_argument>([&] { preprocess(cloud); });
    }
    auto mixed = sample();
    mixed->push_back((*invalid)[0]);
    mixed->is_dense = true;
    expectThrow<std::invalid_argument>([&] { voxelDownsample(mixed, 0.2F); });
    for (float size : {0.0F, -0.1F, std::numeric_limits<float>::quiet_NaN(),
                       std::numeric_limits<float>::infinity(),
                       -std::numeric_limits<float>::infinity(),
                       std::numeric_limits<float>::denorm_min()}) {
        expectThrow<std::invalid_argument>([&] { voxelDownsample(sample(), size); });
        expectThrow<std::invalid_argument>([&] { preprocess(sample(), {size}); });
    }
    expectThrow<std::invalid_argument>([&] { voxelDownsample(sample(), 1e-8F); });
    auto extreme = pcl::make_shared<Cloud>();
    extreme->push_back(Point(1e20F, 0, 0));
    expectThrow<std::invalid_argument>([&] { voxelDownsample(extreme, 0.2F); });
}

void testPreprocess() {
    auto cloud = sample();
    cloud->push_back(Point(0, std::numeric_limits<float>::infinity(), 0));
    cloud->is_dense = true;
    std::ostringstream log;
    auto* previous = std::clog.rdbuf(log.rdbuf());
    PreprocessResult result;
    try {
        result = preprocess(cloud, {1.0F});
    } catch (...) {
        std::clog.rdbuf(previous);
        throw;
    }
    std::clog.rdbuf(previous);
    check(result.input_points == 4 && result.finite_points == 3 &&
          result.output_points == 2 && result.cloud->size() == 2, "预处理计数错误");
    check(log.str().find("input_points=4 finite_points=3 output_points=2") != std::string::npos,
          "日志未输出计数");
    check(log.str().find("x=[0.1, 1.2] y=[-0.2, 0.4] z=[0.3, 2.4] (m)") != std::string::npos,
          "有限点范围统计错误");
    check(log.str().find("x=[0.2, 1.2] y=[-0.2, 0.3] z=[0.4, 2.4] (m)") != std::string::npos,
          "输出点范围统计错误");
    check(cloud->size() == 4 && cloud->is_dense && std::isinf((*cloud)[3].y),
          "预处理修改输入");
    (*result.cloud)[0].x = 42;
    check(coordinatesNear((*cloud)[0].x, 0.1F), "预处理结果未独立分配");
    const auto defaultResult = preprocess(sample());
    const auto direct = voxelDownsample(sample(), 0.2F);
    check(defaultResult.output_points == direct->size(), "默认体素参数不符 v1.1");
}
}  // namespace

int main() {
    try {
        Fixtures fixtures;
        const std::vector<std::pair<std::string, std::function<void()>>> tests = {
            {"PCD 三种编码及非有限点保留", [&] { testPcd(fixtures); }},
            {"PCD 读取错误和空数据", [&] { testPcdErrors(fixtures); }},
            {"XYZ 有限性及输入不变", testCleaning},
            {"体素质心、负坐标和单点", testVoxel},
            {"非法输入、体素参数和网格越界", testInvalidInputs},
            {"预处理计数、范围和默认参数", testPreprocess}
        };
        int failures = 0;
        for (const auto& test : tests) {
            try {
                test.second();
                std::cout << "通过: " << test.first << '\n';
            } catch (const std::exception& error) {
                ++failures;
                std::cerr << "失败: " << test.first << ": " << error.what() << '\n';
            }
        }
        std::cout << "模块 A 测试组: " << tests.size() - failures << '/' << tests.size() << '\n';
        return failures == 0 ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << "测试初始化失败: " << error.what() << '\n';
        return 1;
    }
}
