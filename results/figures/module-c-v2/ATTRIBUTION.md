# 道路图像署名与许可

本目录的 kitti_raw.png、kitti_alignment.png 以及 voxel_comparison.png 中 KITTI 子图，基于 KITTI Raw 数据生成。

原作者：Andreas Geiger、Philip Lenz、Christoph Stiller、Raquel Urtasun。
作品：Vision meets Robotics: The KITTI Dataset，IJRR，2013。
来源：[KITTI Raw](https://www.cvlibs.net/datasets/kitti/raw_data.php)，[AWS 公共存储登记](https://registry.opendata.aws/kitti/)。
序列：2011_09_26_drive_0005_sync，Velodyne 帧 0000000000/0000000001。

变更：BIN 转 PCD、稀疏显示/视窗裁剪、点云着色、施加 ICP 估计坐标变换，以及统计对比绘图。
这些道路派生成果按 [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/) 提供：署名、非商业、相同方式共享。
为便于分发，包含道路子图的 voxel_comparison.png 整张图随同采用上述许可。不暗示原作者认可本实验。

synthetic_raw.png、synthetic_alignment.png、synthetic_errors.png 来自项目自生成数据，不使用 KITTI 点云；随项目最终许可决定，不在此替用户选择源码或自有成果许可证。
生成命令与局限见 docs/EXPERIMENTS.md；输入/图像哈希见 results/metrics/module-c-v2/provenance.json。

2026-10-27 许可确认补记（不改写历史图片/指标/元信息）：用户确认其有权授权的项目原创纯合成成果采用 MIT，Copyright (c) 2026 Wang Chenqi。此前 pending 表述为历史状态，现由根目录 LICENSE 与 docs/THIRD_PARTY.md 的范围说明更新；KITTI 道路及混合成果仍遵循上述 CC BY-NC-SA 3.0。
