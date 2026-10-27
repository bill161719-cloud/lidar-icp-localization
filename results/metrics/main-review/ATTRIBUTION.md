# 结果归档说明

此目录包含真实 CLI 输出、命令、退出码、stderr、汇总 CSV 和来源/哈希清单。
道路数据归属 KITTI 作者 Andreas Geiger、Philip Lenz、Christoph Stiller、Raquel Urtasun，
Vision meets Robotics: The KITTI Dataset，IJRR，2013。
[原始来源](https://www.cvlibs.net/datasets/kitti/raw_data.php)，[公共桶登记](https://registry.opendata.aws/kitti/)，
[许可 CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/)。

不包含原始道路点云。道路相关 kitti_*、provenance.json 中 KITTI 记录及 summary.csv 的道路记录，作为道路派生实验成果按 CC BY-NC-SA 3.0 归档。
处理变更为格式转换、体素、ICP、匹配统计；没有参考轨迹真值，误差 null 不等于零。
人工相关 synthetic_* 及其 CSV 记录由项目自生成数据得到，项目最终许可由主对话决定。
main 新增 sweep_* 来自同样的项目人工数据；其自有成果许可仍待确认。
validation.json 中包含 KITTI 几何检查，随同道路派生结果采用上述 CC BY-NC-SA 3.0；不改变任何源码许可。
为便于分发，混合道路数据的 summary.csv 和 provenance.json 整个文件随同采用 CC BY-NC-SA 3.0。
这不改变实验工具源码的许可证，也不代表 KITTI 作者对结果背书。

完整命令、指标解释、图片、验证和局限见 docs/EXPERIMENTS.md。
