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
当前六图通过 C 的 Matplotlib Agg 实际数据绘图；--visualize/PCL 交互窗口尚未实现或渲染验收，不要求 A 跨界实现窗口管理。

共享 include/cloud_types.h 由主对话维护。计划目标：cloud_processing、icp_registration、
pose_utils、generate_test_data 和 lidar_icp。主对话已配置可选的模块库/测试入口，
仅在所属源文件存在时创建目标；模块新增文件后重新配置即可，不得修改共享 CMake。
当前 A/B 已集成：cloud_processing、pose_utils、icp_registration 经 registration_pipeline 串联，
lidar_icp 已提供 PCD 到 JSON 位姿报告的完整命令行。未开启 PCL 时仍只有帮助/版本入口。
registration_pipeline 独立检查收敛、SE(3)、内点数/比例与 RMSE；拒绝结果只输出诊断，不输出有效 pose。
开启 LIDAR_ENABLE_PCL 时仍保留 dependency_check；完整 CTest 含 A/B 单测和 CLI 端到端 test_pipeline。
PCL 组件：common、io、filters、registration、visualization；kdtree/search 由 registration 等组件传递引入。
Eigen 优先作为导入目标 Eigen3::Eigen。所有 C++ 库必须同位数、同编译器 ABI、同运行时。

无显示环境先运行数值测试，桌面截图单独验证。数据、图像与指标必须来自真实执行。

C 现已接入 generate_test_data、Range 获取、KITTI BIN→PCD、实验驱动与一致性验证。
标准 CTest 共10项、离线且只用Python标准库；外部KITTI/绘图库和35组完整实验通过显式命令执行。
原 module-c-v2 证据不覆盖，main 独立复验存 main-review，并记录实际源码/二进制/输入和图像哈希。
