#include <Eigen/Core>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/registration/icp.h>
#include <pcl/visualization/pcl_visualizer.h>

// No display is opened: this checks headers and basic linking only.
int main() {
    pcl::PointCloud<pcl::PointXYZ> cloud;
    pcl::IterativeClosestPoint<pcl::PointXYZ, pcl::PointXYZ> icp;
    const Eigen::Matrix4f identity = Eigen::Matrix4f::Identity();
    return cloud.empty() && identity.isIdentity() && !icp.hasConverged() ? 0 : 1;
}
