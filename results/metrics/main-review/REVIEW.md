# main 独立复验归档

输入模块提交 f85214f9788b5b7f2bb3687694230db99ddad434；main 基础为 9fc3057。
本目录是真正独立下载、转换、全新 Release 构建后执行的 35 组 CLI 结果：原 10 组加 main 补充的 25 组有界参数/退化实验。
原模块归档 results/metrics/module-c-v2 与六张图片保持不变，避免用 main 的不同耗时覆盖原始证据。

summary.csv 与全部同名 JSON、command.json、stderr.txt 来自 main 实际进程输出。
provenance.json 记录当时待合并工作区的真实 HEAD、dirty 状态、源码/二进制/42 个输入的哈希；
这里的 base_commit 不是“所有代码已属于该提交”的声明，dirty=true 与源码哈希明确保留了合并中状态。
不要求 PE 二进制或单次耗时跨构建逐字节一致。

validation.json 为独立核验结果：35 个报告、42 个输入哈希、6 张复绘 PNG 哈希全部通过；
原 10 个报告除 source/target 路径、elapsed_ms 外完全一致。六张图与 module-c-v2 逐字节一致，故不重复存图。
还保留固定原始 source 子样本对完整原始 target 的前后最近邻距离：
KITTI 抽样 RMSE 0.274307→0.173437 m，人工 0.316986→0.0000262796 m。
该辅助指标不是 CLI 体素内点 RMSE，更不是车辆定位误差。

原始输入、全量构建日志、main 复绘图片仍在被忽略的 data/kitti/、build/、build-final-c/；不在 Git 中分发道路原始点云。
可无数据核对公开归档（不会声称已检查原始输入）：

    python tools/validate_experiments.py --metrics results/metrics/main-review --figures results/figures/module-c-v2 --reference results/metrics/module-c-v2 --skip-inputs

完整重跑见 docs/EXPERIMENTS.md。道路派生成果许可见本目录 ATTRIBUTION.md，不能将其笼统标为源码候选 MIT。
