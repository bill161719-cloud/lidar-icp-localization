#pragma once

#include <Eigen/Core>
#include <Eigen/Geometry>

namespace lidar {
struct PoseComponents {
    Eigen::Matrix3d rotation;
    Eigen::Vector3d translation_m;
    // 四元数语义顺序为 w,x,y,z；Eigen coeffs() 的存储顺序为 x,y,z,w。
    Eigen::Quaterniond quaternion;
};
bool isValidTransform(const Eigen::Matrix4f& T, double tolerance = 1e-4);
PoseComponents decomposeTransform(const Eigen::Matrix4f& T);
double translationErrorM(const Eigen::Matrix4f& estimated,
                         const Eigen::Matrix4f& ground_truth);
double rotationErrorRad(const Eigen::Matrix4f& estimated,
                        const Eigen::Matrix4f& ground_truth);
}  // namespace lidar
