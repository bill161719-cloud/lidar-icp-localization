# 模块与数据流

```text
PCD / 合法真实 LiDAR 数据 -> 模块 C 转换与来源记录 -> PCD
PCD source / target -> 模块 A 读取 -> 有限点清理 -> 体素下采样
预处理点云 + T_target_source 初值 -> 模块 B PCL ICP
  -> 收敛状态 + 最终变换 + fitness + 独立匹配误差
  -> Eigen 位姿分析 -> 主程序输出 -> 模块 C 图片/CSV/实验记录
```

A 负责输入点云与纯预处理；B 负责配准和位姿；C 负责生成/转换数据、实验和可视化输出。
主程序负责参数校验、调用顺序、退出码、统一输出。PCL 基本显示通过 C 的独立工具使用；
后续由主对话将 --visualize 接入 CLI，不要求 A 跨界实现窗口管理。

共享 include/cloud_types.h 由主对话维护。计划目标：cloud_processing、icp_registration、
generate_test_data 和 lidar_icp，主对话逐个接入 CMake；不存在的模块源文件不得提前加入目标。
当前仅 lidar_icp bootstrap；开启 LIDAR_ENABLE_PCL 时检查 Eigen/PCL 并构建 dependency_check。
PCL 组件：common、io、filters、registration、visualization；后续独立误差计算需要 kdtree 时由主对话追加。
Eigen 优先作为导入目标 Eigen3::Eigen。所有 C++ 库必须同位数、同编译器 ABI、同运行时。

无显示环境先运行数值测试，桌面截图单独验证。数据、图像与指标必须来自真实执行。
