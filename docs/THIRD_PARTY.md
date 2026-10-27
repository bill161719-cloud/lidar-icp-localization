# 第三方与数据许可台账

当前未分发第三方库二进制或 KITTI 原始 BIN/PCD；已归档真实数据派生图和结果，许可范围按下文区分。

| 对象 | 预期用途 | 发布前要求 |
|---|---|---|
| PCL 1.15.1 | 读取/滤波/ICP/显示 | 已检查源 LICENSE.txt 为 BSD 三条款；本地 VTK 发现补丁不随同分发原库 |
| Eigen 3.4.0（系统另装 5.0.1-1） | 矩阵和位姿 | 已检查 COPYING.README：主要 MPL-2.0，部分第三方文件另有许可；发布二进制前检查实际使用范围及通知 |
| Boost 1.92.0 / FLANN 1.9.2 / VTK 9.6.2 | PCL 传递依赖 | pacman 包元信息分别记录 BSL-1.0 / BSD-3-Clause / BSD-3-Clause；发布二进制前补充传递依赖完整通知 |
| CMake/GCC/Git | 本地构建工具 | 不随本仓库提交二进制 |
| 人工生成点云 | 可公开小型测试样例 | 保存生成脚本、种子和项目许可归属 |
| KITTI Raw drive_0005 两帧 | 本地 BIN/PCD 与公开派生结果 | main 已重新下载/转换并核对哈希；原始数据不提交，派生图/道路结果按 CC BY-NC-SA 3.0 署名及条件分发 |

项目源码许可证候选 MIT，待用户确认版权署名和许可选择后由主对话添加 LICENSE。
当前不应宣称仓库已经开源授权完备；正式公开发布受该任务阻塞。

## KITTI 核查与派生成果

2026-10-27 已独立核查 [KITTI 官方 Copyright/Citation](https://www.cvlibs.net/datasets/kitti/)、
[AWS 公共桶登记](https://registry.opendata.aws/kitti/) 与 [许可条款](https://creativecommons.org/licenses/by-nc-sa/3.0/)。
两处均标示 CC BY-NC-SA 3.0；官方下载可达或匿名访问不表示无使用限制。
数据原作者 Andreas Geiger、Philip Lenz、Christoph Stiller、Raquel Urtasun；原始数据引用 IJRR 2013 的 KITTI Raw 论文。
序列为 2011_09_26_drive_0005_sync，Velodyne 帧 0000000000/0000000001。

- 原始 BIN、转换 PCD、完整时间戳仅在本地被忽略的 data/kitti/，不随仓库重分发。
- kitti_raw.png、kitti_alignment.png 和包含道路子图的 voxel_comparison.png 按 CC BY-NC-SA 3.0 保留署名、来源、许可链接、改动说明，不暗示原作者认可。
- results/metrics/module-c-v2 与 main-review 的道路派生结果沿用目录 ATTRIBUTION.md 的同样条件，不笼统归入源码候选 MIT。
- 不能把 NC/SA 限制从道路成果中删除；商业使用这些受许可约束的成果需要相应授权。正式分发仍需独立发布审查。
- 纯人工数据图与自有源码最终许可尚未选定，本记录不替用户认领版权或擅自决定全项目许可。

Python 实验依赖未随仓库分发：NumPy 2.4.4 与 Matplotlib 3.10.8，版本锁见 tools/requirements-experiments.txt。
若将来打包 Python 或 C++ 二进制，需要按实际分发内容补足各包许可通知；本次只提交源码和结果。
