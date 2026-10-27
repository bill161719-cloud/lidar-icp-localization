#include "pose_utils.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace lidar {
namespace {
void requireTransform(const Eigen::Matrix4f& T) {
    if (!isValidTransform(T)) {
        throw std::invalid_argument("变换必须是有限的 SE(3) 齐次矩阵");
    }
}
}  // namespace

bool isValidTransform(const Eigen::Matrix4f& T, double tolerance) {
    if (!std::isfinite(tolerance) || tolerance <= 0.0 || !T.allFinite()) {
        return false;
    }
    const Eigen::Matrix4d matrix = T.cast<double>();
    const Eigen::Matrix3d R = matrix.topLeftCorner<3, 3>();
    return (matrix.row(3) - Eigen::RowVector4d(0, 0, 0, 1)).cwiseAbs().maxCoeff() <= tolerance
        && (R.transpose() * R - Eigen::Matrix3d::Identity()).cwiseAbs().maxCoeff() <= tolerance
        && std::abs(R.determinant() - 1.0) <= tolerance;
}

PoseComponents decomposeTransform(const Eigen::Matrix4f& T) {
    requireTransform(T);
    PoseComponents pose;
    pose.rotation = T.topLeftCorner<3, 3>().cast<double>();
    pose.translation_m = T.topRightCorner<3, 1>().cast<double>();
    pose.quaternion = Eigen::Quaterniond(pose.rotation).normalized();
    return pose;
}

double translationErrorM(const Eigen::Matrix4f& estimated,
                         const Eigen::Matrix4f& ground_truth) {
    requireTransform(estimated);
    requireTransform(ground_truth);
    return (estimated.topRightCorner<3, 1>().cast<double>()
          - ground_truth.topRightCorner<3, 1>().cast<double>()).norm();
}

double rotationErrorRad(const Eigen::Matrix4f& estimated,
                        const Eigen::Matrix4f& ground_truth) {
    requireTransform(estimated);
    requireTransform(ground_truth);
    const Eigen::Matrix3d relative = ground_truth.topLeftCorner<3, 3>().cast<double>().transpose()
                                  * estimated.topLeftCorner<3, 3>().cast<double>();
    return std::acos(std::clamp((relative.trace() - 1.0) / 2.0, -1.0, 1.0));
}
}  // namespace lidar
