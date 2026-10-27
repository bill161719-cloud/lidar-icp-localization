# 整改实验归档与许可

本目录为基于 4bc4e13 待提交整改工作区实际运行的 36 组报告、命令、stderr、CSV、溯源及核验。
原 module-c-v2、main-review 的实验数值、输入元信息和图片不回写；仅补记其当前许可范围。
六张复绘图与原图哈希相同，继续使用 results/figures/module-c-v2/，不重复存储。

项目原创纯合成 synthetic_*、sweep_*、repeated_structure 成果为 MIT，
Copyright (c) 2026 Wang Chenqi。不是对所用第三方软件的重新授权。

KITTI 原作者：Andreas Geiger、Philip Lenz、Christoph Stiller、Raquel Urtasun。
作品：Vision meets Robotics: The KITTI Dataset，IJRR，2013。
[KITTI 来源](https://www.cvlibs.net/datasets/kitti/raw_data.php)，
[公共桶登记](https://registry.opendata.aws/kitti/)，
[CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/)。
序列 2011_09_26_drive_0005_sync，source=Velodyne 1、target=0。
变更包括 BIN 转 PCD、体素、ICP 和匹配/几何统计；不暗示原作者认可，无车辆定位真值。
kitti_* 及混合道路信息的 summary.csv、provenance.json、validation.json 整文件按该许可保留署名、非商业及相同方式共享条件。
不提交原始 BIN/PCD。其他项目原创说明、before-after/version-diagnostics/acceptance 为 MIT。

validation.json 的 source_verification=explicit_source_root 表示核验了当次源码；
历史归档默认不核查当前源码，不能用源码版本差异否定历史结果。
详细命令、限制和审查状态见 docs/REMEDIATION_REPORT.md、docs/EXPERIMENTS.md。
