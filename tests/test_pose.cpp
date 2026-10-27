#include "pose_utils.h"

#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {
void check(bool condition, const std::string& message) {
    if (!condition) { throw std::runtime_error(message); }
}
template <class Function>
void rejects(Function function) {
    try { function(); } catch (const std::invalid_argument&) { return; }
    throw std::runtime_error("预期 invalid_argument");
}
}
int main() {
    try {
        const Eigen::Matrix4f identity = Eigen::Matrix4f::Identity();
        check(lidar::isValidTransform(identity), "单位阵合法");
        Eigen::Matrix4f T = identity;
        T.topLeftCorner<3, 3>() = Eigen::AngleAxisf(0.6F, Eigen::Vector3f::UnitZ()).toRotationMatrix();
        T.topRightCorner<3, 1>() = Eigen::Vector3f(1, 2, 2);
        check(lidar::isValidTransform(T), "旋转平移合法");
        const auto pose = lidar::decomposeTransform(T);
        check((pose.rotation - T.topLeftCorner<3, 3>().cast<double>()).norm() < 1e-12, "旋转分解");
        check((pose.translation_m - Eigen::Vector3d(1, 2, 2)).norm() < 1e-12, "平移分解");
        check(std::abs(pose.quaternion.w() - std::cos(0.3)) < 1e-7, "四元数 w");
        check(std::abs(pose.quaternion.x()) < 1e-12 && std::abs(pose.quaternion.y()) < 1e-12
              && std::abs(pose.quaternion.z() - std::sin(0.3)) < 1e-7, "四元数 x,y,z");
        check(std::abs(lidar::translationErrorM(T, identity) - 3) < 1e-12, "已知平移误差");
        check(std::abs(lidar::rotationErrorRad(T, identity) - 0.6) < 1e-6, "已知旋转误差 rad");
        check(lidar::rotationErrorRad(T, T) < 1e-12, "同一 float32 旋转误差应接近零");
        Eigen::Matrix4f tinyRotation = identity;
        tinyRotation.topLeftCorner<3, 3>() = Eigen::AngleAxisf(1e-6F, Eigen::Vector3f::UnitZ()).toRotationMatrix();
        check(std::abs(lidar::rotationErrorRad(tinyRotation, identity) - 1e-6) < 1e-12,
              "微小角度不能因 trace 的 float32 舍入变成零");
        const Eigen::Matrix4f inverse = T.inverse();
        const Eigen::Vector4f point(0.2F, -0.5F, 3, 1);
        check(lidar::isValidTransform(inverse) && (inverse * (T * point) - point).norm() < 1e-6F,
              "逆变换恢复坐标");
        check(lidar::rotationErrorRad(identity, identity) == 0, "零角度");
        Eigen::Matrix4f halfTurn = identity;
        halfTurn(0, 0) = -1; halfTurn(1, 1) = -1;
        check(std::abs(lidar::rotationErrorRad(halfTurn, identity) - std::acos(-1.0)) < 1e-12, "pi 角度");
        Eigen::Matrix4f nearIdentity = identity;
        nearIdentity(0, 0) += 1e-6F;
        check(lidar::rotationErrorRad(nearIdentity, identity) == 0, "acos 上界钳制");
        for (double tolerance : {0.0, -1.0, std::numeric_limits<double>::infinity(),
                                 std::numeric_limits<double>::quiet_NaN()}) {
            check(!lidar::isValidTransform(identity, tolerance), "非法 tolerance");
        }
        for (int type = 0; type < 6; ++type) {
            Eigen::Matrix4f invalid = identity;
            if (type == 0) invalid(0, 0) = -1;
            if (type == 1) invalid(0, 0) = 2;
            if (type == 2) invalid(0, 1) = 0.1F;
            if (type == 3) invalid(3, 0) = 0.1F;
            if (type == 4) invalid(0, 3) = std::numeric_limits<float>::quiet_NaN();
            if (type == 5) invalid(3, 3) = std::numeric_limits<float>::infinity();
            check(!lidar::isValidTransform(invalid), "非法 SE(3)");
            rejects([&] { lidar::decomposeTransform(invalid); });
            rejects([&] { lidar::translationErrorM(invalid, identity); });
            rejects([&] { lidar::translationErrorM(identity, invalid); });
            rejects([&] { lidar::rotationErrorRad(invalid, identity); });
            rejects([&] { lidar::rotationErrorRad(identity, invalid); });
        }
        std::cout << "B01 位姿测试通过\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "B01 失败: " << error.what() << '\n'; return 1;
    }
}
