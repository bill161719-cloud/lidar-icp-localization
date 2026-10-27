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

## 项目原创内容与明确授权

2026-10-27 用户明确授权：仅将其有权授权的原创代码、文档及纯合成测试成果采用 MIT，
署名 **Copyright (c) 2026 Wang Chenqi**。根目录 [LICENSE](../LICENSE) 已落盘；
Git 中的 Codex 提交身份不是版权所有者或独立的版权转让证明。

| 文件范围 | 归属和许可处理 |
|---|---|
| include/*.h、src/*.cpp、tests/*.cpp、tests/*.py | 本项目编写的接口、PCL/Eigen API 调用、流水线与测试，原创部分 MIT；未提交第三方库实现 |
| CMakeLists.txt、tools/*.cpp/*.py/*.ps1、工具配置 JSON/requirements | 本项目构建、生成、实验与验证代码 MIT；prepare_pcl_source.py 中的上游匹配片段例外，见下文 |
| README.md、AGENTS.md、docs/ 的原创文字 | 原创内容 MIT；第三方引用、事实资料及所链接的许可不被重新授权 |
| 纯人工 PCD/真值/元信息、synthetic_* 图和报告、sweep_*、repeated_structure 报告 | 本项目纯合成成果 MIT；历史元信息中的 pending 是原运行记录，不回写篡改 |
| KITTI 原始 BIN/PCD、kitti_* 图/报告、道路几何统计 | 不在 MIT 范围；按原适用许可和署名处理，原始数据仍不提交 |
| 混合道路信息的 summary.csv、provenance.json、validation.json、voxel_comparison.png | 保守按整文件 CC BY-NC-SA 3.0 分发；独立纯合成 JSON 不受该整文件安排影响 |
| licenses/PCL-BSD-3-Clause.txt | 上游原许可及版权通知，不是本项目原创 MIT 内容 |

已逐类检查跟踪源码、include/、src/、tests/、tools/ 和版权/SPDX/来源标记：
未发现仓库内 vendored PCL/Eigen 实现或直接复制的第三方 ICP 求解器。
**发现并保留的第三方源码片段**：tools/prepare_pcl_source.py 通过上游 CMake 原句匹配应用 VTK 发现修补，
包含 pcl_find_vtk.cmake 的 find_package/Qt 条件上下文。自有修补逻辑可为 MIT，原句不据此改为 MIT；
脚本已加范围通知，并完整保留本地 PCL 1.15.1 的原通知文字于 licenses/PCL-BSD-3-Clause.txt（仅移除一处尾随空格）。
上游来源：[PCL 1.15.1](https://github.com/PointCloudLibrary/pcl/tree/pcl-1.15.1)、
[原 LICENSE](https://github.com/PointCloudLibrary/pcl/blob/pcl-1.15.1/LICENSE.txt)。
其余已审查代码主要是标准库、PCL/Eigen API 组合及项目自编逻辑，没有把所调用的库纳入 MIT。
这是一轮人工/标记/历史检查，不能证明 AI 辅助生成内容绝无第三方权利问题；发现新的来源证据须重新核查。
本次不打包依赖或可执行文件。PCL 的 BSD 署名/通知、Eigen 及传递依赖原许可继续适用。

## KITTI 核查与派生成果

2026-10-27 已独立核查 [KITTI 官方 Copyright/Citation](https://www.cvlibs.net/datasets/kitti/)、
[AWS 公共桶登记](https://registry.opendata.aws/kitti/) 与 [许可条款](https://creativecommons.org/licenses/by-nc-sa/3.0/)。
两处均标示 CC BY-NC-SA 3.0；官方下载可达或匿名访问不表示无使用限制。
数据原作者 Andreas Geiger、Philip Lenz、Christoph Stiller、Raquel Urtasun；原始数据引用 IJRR 2013 的 KITTI Raw 论文。
序列为 2011_09_26_drive_0005_sync，Velodyne 帧 0000000000/0000000001。

- 原始 BIN、转换 PCD、完整时间戳仅在本地被忽略的 data/kitti/，不随仓库重分发。
- kitti_raw.png、kitti_alignment.png 和包含道路子图的 voxel_comparison.png 按 CC BY-NC-SA 3.0 保留署名、来源、许可链接、改动说明，不暗示原作者认可。
- results/metrics/module-c-v2、main-review 与 remediation 的道路派生结果沿用目录 ATTRIBUTION.md 的同样条件，不归入项目 MIT。
- 不能把 NC/SA 限制从道路成果中删除；商业使用这些受许可约束的成果需要相应授权。正式分发仍需独立发布审查。
- 纯人工图/数据的项目原创部分已按上述用户授权采用 MIT；不据此替用户授权第三方内容。

依赖许可来源：PCL 官网说明为 [BSD 三条款](https://pointclouds.org/about/)；
Eigen 3.4.0 的实际源码 COPYING.README 已重新读取，主要 MPL-2.0，部分文件有 BSD/LGPL 等例外，
见 [该版本上游台账](https://gitlab.com/libeigen/eigen/-/blob/3.4.0/COPYING.README)。
不将“主要 MPL-2.0”扩大为所有 Eigen 文件均无其他条件，也不把依赖头文件中的实现授权改成 MIT。
本轮在线再次核查 KITTI Copyright、PCL 官网和 [MIT 标准文本](https://opensource.org/license/mit)；
Eigen 许可依据本机固定 3.4.0 源码（官网入口本轮抓取失败，不冒称在线复核成功）。

源码署名及 MIT 选择已由用户确认，本轮不再等待该决定。剩余发布条件为独立复审、实际用途符合第三方许可、
以及用户明确批准公开发布。涉及学校/雇主/共同作者等新权利证据时再补充核实；当前没有擅自给这些主体署名。

Python 实验依赖未随仓库分发：NumPy 2.4.4 与 Matplotlib 3.10.8，版本锁见 tools/requirements-experiments.txt。
若将来打包 Python 或 C++ 二进制，需要按实际分发内容补足各包许可通知；本次只提交源码和结果。
