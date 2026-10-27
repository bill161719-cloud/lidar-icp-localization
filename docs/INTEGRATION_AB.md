# 模块 A/B 首轮集成验收

日期：2026-10-27（Asia/Shanghai）。本次只验收点云配准及相对位姿估计，不是完整 SLAM 或 FAST-LIO。

## 输入提交与审核

main 起点 4cfce35，工作区干净。
A 输入 24fc23311b883283eb4a8d3877423050ad5c1d55，只新增约定的三个文件；
B 输入 3236706361e11bccdde01d9043f9971ba58b2daf，只新增约定的六个文件。
两者未修改共享文件；保留原 feature 分支及原始提交，用合并提交保留历史。

A 检查：PCD 三种编码/float64、字段校验、NaN/Inf 不依赖 is_dense、复制语义、体素质心、
int32 网格范围防护、点数与范围统计。B 检查：统一 PointXYZ、有限性与 SE(3) 校验、含初值的最终
T_target_source、单向最近邻 RMSE、fitness m²、输入不变、真值/逆变换和失败诊断。
接口签名与 INTERFACES.md v1.1 一致，A 清理后的输出可以直接进入 B。

## 实际执行顺序

| 阶段 | 实际结果 | 日志 |
|---|---|---|
| A 合入后，全新 Release 构建 | CTest 5/5；A 内部 6/6 测试组 | build/integration-a.log |
| A 验收后提交 | 合并提交 cae8e11 | Git 历史 |
| B 合入后，全新 Release 构建 | CTest 7/7 | build/integration-ab.log |
| B API 验收后提交 | 合并提交 99b52c7 | Git 历史 |
| 初版流水线与 CLI | CTest 8/8，9 个 CLI 场景 | build/integration-pipeline.log |
| 新增微小角度回归，修复前 | test_pose 失败，真实暴露 trace/acos 精度问题 | build/pose-angle-regression-before-fix.log |
| 修复后完整重新配置/构建 | CTest 8/8，含全部模块测试和 9 个 CLI 场景 | build/integration-final.log |

环境：PCL 1.15.1、项目 Eigen 3.4.0、UCRT64 GCC 16.2.0、CMake/CTest 3.31.6、C++17、Release。
构建和测试通过 tools/verify_dependencies.ps1 执行，依次传入
-BuildDirectory build-integration-a / build-integration-ab，-Jobs 1；未重新构建 PCL。
最终配置、构建、CTest 和直接运行依赖检查均退出 0。
本轮使用全新目录分别验证 A 与 A+B，最终在后者增量编译集成和修复，不声称最终又全量重编第三方库。

8 个 CTest：bootstrap_help、bootstrap_version、bootstrap_rejects_unknown、dependency_check、
test_cloud_processor、test_pose、test_icp、test_pipeline。
测试不使用 Release 会禁用的 assert 作为唯一检查。

## 主对话集成实现与安全修复

- registration_pipeline 串联 PCD 读取、清理、体素、ICP 和独立质量判断。
- 默认要求 converged、合法最终 SE(3)/有限点云/指标、至少 3 内点、内点率 >=0.5、内点 RMSE <=0.2 m。
  质量阈值可显式配置；原始 PCL converged 语义不被篡改。
- 被拒绝时 CLI 返回 4；JSON 的有效 T_target_source/pose 为 null，诊断矩阵明确另列。
  零内点 RMSE 和无真值误差为 null，不用 0 伪装成功。
- stdout 为标准 JSON，stderr 为处理日志；可保存同样 JSON，拒绝覆盖已有文件。
  非法输入返回 2，IO/运行错误返回 3，避免失败流程返回成功。
- 修复 B 的旋转误差数值精度：float32 旋转矩阵的 trace/acos 会丢失 1e-6 rad 角度，
  使用等价的归一化四元数 angularDistance（atan2 形式）。先新增回归证明失败，再修复；
  原有 0/pi/非法矩阵测试、同旋转及微小角度回归、完整集成测试均通过。
  未更改公开函数签名，未依靠放宽精度门限掩盖问题。

## 真实端到端测试结果

tests/test_pipeline.py 用标准库生成测试专用 ASCII PCD/真值文件，调用真正 lidar_icp.exe，
检查退出码、标准 JSON、清理/下采样统计、位姿及误差；不是模拟 A/B 返回值。
生成数据只存 build*/test-pipeline/run-*/，不是模块 C 的正式数据工具或道路实验。

| 场景 | 实际结果 |
|---|---|
| 干净非对称三维点集，含重复点/NaN/Inf | 接受；source 802→800 有限→400 下采样点，target 800→400 |
| source/target 对调 | 接受；估计矩阵与原真值的逆变换一致 |
| 无对应点、相隔很远 | 未收敛，退出 4，有效 pose=null |
| 一个迭代且评估门限很小 | converged=true，但 0 内点；拒绝，退出 4 |
| 部分重叠 | converged=true，80/400 内点、比例 0.2；拒绝，退出 4 |
| 严格 RMSE 上限与加噪目标 | 内点率 1，但 RMSE 0.00526758 m 超限；拒绝 |
| 单个固定种子的轻噪声 + source 离群点 | 接受；400/420 内点；只是受控 smoke check |
| 非法参数/矩阵/少点/全非法点/丢失或损坏文件 | 对应退出 2/3，不输出有效位姿 |
| 已有报告保护、无真值字段 | 不覆盖已有文件；无真值误差为 null |

最终本机一次实际结果（固定种子 20261027；干净 Rz=0.18 rad，t=(0.3,-0.15,0.08) m，显式近真值初值）：

| 场景 | 平移误差 m | 旋转误差 rad | 最近邻 RMSE m | 内点率 |
|---|---|---|---|---|
| 干净人工数据 | 6.869095905e-8 | 7.585503877e-8 | 4.224037437e-7 | 1 |
| 轻噪声/离群点 smoke | 9.050752485e-5 | 1.748481604e-4 | 0.003768631653 | 0.9523809524 |

这些是人工测试结果，不是实车定位精度，不外推为噪声/离群点鲁棒性结论。
测试包含 ICP 耗时输出，但不把单次 smoke 测试当性能基准。
本次最终人工数据原始目录：build-integration-ab/test-pipeline/run-65yh8v6b。
每次测试保留输入 PCD、矩阵、命令 JSON、stdout JSON、stderr 和退出码文件，不删除结果。
汇总保存在 build/integration-summary.json；CTest 原始日志在 build-integration-ab/Testing/Temporary/LastTest.log。

## 警告分析与局限

GCC 的 mismatched-new-delete 警告来自 Eigen::aligned_allocator → PCL make_shared →
libstdc++ shared_ptr 的内联路径。已检查实际头文件：Eigen allocate/deallocate 分别调用
aligned_malloc/aligned_free，shared_ptr 的派生 _M_destroy 使用分配器 guard；
当前 PCL_USES_EIGEN_HANDMADE_ALIGNED_MALLOC=0，消费者未额外开启 AVX，也未触发 PCL 的对齐 ABI 警告。
应用没有自行对这类指针混用 free/delete。现有证据指向第三方/编译器诊断路径；
保留原始警告，不直接断言所有警告必然误报，也未用 -Wno-* 消音或修改依赖。
未执行完整内存检测器验证，不能宣称穷尽排除内存错误。

仍未完成：真实道路数据、系统噪声/离群点/初值扫描、退化或对称几何识别、真实 GUI 渲染与截图。
质量门禁是保守应用策略，不能排除全部局部最优；体素过小/范围过大会触发 A 的网格范围拒绝。
没有实现多帧里程计、地图、回环、IMU 或完整 SLAM。
模块 C 可以从最新集成 main 开始 C01/C02，随后补完整实验和图像；先同步旧 worktree。
