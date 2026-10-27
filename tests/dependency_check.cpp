#include <Eigen/Core>
#include <pcl/filters/voxel_grid.h>
#include <pcl/pcl_config.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/registration/icp.h>
#include <pcl/visualization/pcl_visualizer.h>
#include <iostream>

// Third-party API/link/runtime smoke check; no rendering or module implementation.
int main() {
    auto cloud = pcl::make_shared<pcl::PointCloud<pcl::PointXYZ>>();
    cloud->emplace_back(0.0F, 0.0F, 0.0F);
    cloud->emplace_back(1.0F, 0.0F, 0.0F);
    cloud->emplace_back(0.0F, 2.0F, 0.0F);
    cloud->emplace_back(0.0F, 0.0F, 3.0F);
    pcl::VoxelGrid<pcl::PointXYZ> filter;
    filter.setInputCloud(cloud);
    filter.setLeafSize(0.1F, 0.1F, 0.1F);
    pcl::PointCloud<pcl::PointXYZ> filtered;
    filter.filter(filtered);

    pcl::IterativeClosestPoint<pcl::PointXYZ, pcl::PointXYZ> icp;
    icp.setInputSource(cloud);
    icp.setInputTarget(cloud);
    icp.setMaximumIterations(5);
    pcl::PointCloud<pcl::PointXYZ> aligned;
    icp.align(aligned);
    if (filtered.size() != cloud->size() || !icp.hasConverged() ||
        !icp.getFinalTransformation().isApprox(Eigen::Matrix4f::Identity(), 1e-4F)) {
        std::cerr << "PCL filter/registration runtime check failed\n";
        return 1;
    }

    // Building the scene exercises PCL/VTK linking; Render/spin is deliberately omitted.
    pcl::visualization::PCLVisualizer viewer("dependency_check", false);
    if (!viewer.addPointCloud<pcl::PointXYZ>(cloud, "smoke_cloud")) {
        std::cerr << "PCL/VTK scene construction failed\n";
        return 1;
    }
    std::cout << "PCL " << PCL_VERSION_PRETTY << "; Eigen " << EIGEN_WORLD_VERSION
              << '.' << EIGEN_MAJOR_VERSION << '.' << EIGEN_MINOR_VERSION
              << "; filter/ICP/VTK scene OK (no render)\n";
    return 0;
}
