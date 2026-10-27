#pragma once

#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

namespace lidar {
using Point = pcl::PointXYZ;
using Cloud = pcl::PointCloud<Point>;
using CloudPtr = Cloud::Ptr;
using CloudConstPtr = Cloud::ConstPtr;
}  // namespace lidar
