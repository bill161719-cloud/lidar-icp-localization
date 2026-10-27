# 独立技术审查与 GitHub 发布验收报告

审查日期：2026-10-27（Asia/Shanghai）。待审提交：`4bc4e1346288b150e367c04576cae8f6c86c1ce7`。

## 结论

**本轮不通过无保留的独立技术审查，暂不具备最终公开发布条件。**
已实际通过两次全新 Release 构建及两次完整 CTest 10/10，核心 ICP 变换方向、初值累积、位姿分解和误差计算在已测范围内正确；35 组实验及六图可以在当前固定环境复现。
但发现非法 ASCII PCD 坐标被静默转成零、仍可能被接受的重要输入正确性问题；源码 LICENSE/版权署名也未确定。两项 P1 须先处理。

问题数量：P0 **0**，P1 **2**，P2 **2**，P3 **1**。未发现 P0 不表示已证明全部输入、第三方库或全部道路条件安全正确。
没有修改算法、源码、测试、任务状态或已有实验归档，没有提交、合并、创建远程或推送。唯一新增交付文件是本报告；复验产物位于 Git 忽略的 build*/。

## 审查基线与执行范围

- 开始时执行 `git status --short --branch`：仅 `## main`，工作区干净；执行 `git log -5 --oneline` 并核对完整 HEAD，与用户指定提交一致。报告原先不存在，无未提交报告被覆盖。
- 已读 AGENTS、README、PROJECT_SPEC、ARCHITECTURE、INTERFACES、TASKS、PROGRESS、DECISIONS、ENVIRONMENT、WORKTREES、EXPERIMENTS、REVIEW_CHECKLIST、THIRD_PARTY。
- 阅读 CMake、A/B/流水线/CLI 源码、公开头文件、现有单元/CLI 测试、数据生成/下载/转换/绘图/验证工具及实际归档。
- 保持原有 Windows UCRT64 GCC 16.2.0、PCL 1.15.1、Eigen 3.4.0、CMake/CTest 3.31.6；没有安装依赖、更新包或更换工具链。
- 当前目录未切换分支。为检查路径可移植性，将 `git archive HEAD` 导出到被忽略目录的 `source snapshot with spaces`；这是源码快照，不是新开发分支或新对话。

## 实际构建与测试

| 检查 | 实际结果 | 本地证据（不提交） |
|---|---|---|
| 根目录全新 Release / PCL ON 构建 | 通过，脚本正常退出 | `build/independent-review-build.log` |
| 完整 CTest | **10/10**，9.33 s | 上述日志；`build-independent-review/Testing/Temporary/LastTest.log` |
| 源码和构建目录均含空格、从其他 cwd 调用脚本 | 全新配置/编译通过，CTest **10/10**，4.16 s | `build/independent-review-relocated-build.log` |
| 依赖探针 | 两次通过，PCL 1.15.1 / Eigen 3.4.0；filter/ICP/VTK scene OK，未 Render | 两份构建日志 |
| 原 main 实验归档全量核验 | 35 报告、42 输入哈希、6 图、10 参考案例通过，未使用 skip-inputs | `build/independent-review-archive.json` |
| 新二进制完整实验 | 35 个案例执行完成，包含预期退出 4 的拒绝案例 | `build/independent-review-experiments.log`；`build-independent-review/metrics/` |
| 新实验输入/报告/图像/几何校验 | 35 报告、42 输入哈希、六图通过；原 10 参考案例一致 | `build-independent-review/validation.json`；`build/independent-review-validation.log` |
| 新 35 报告与 main-review 逐项比较 | 除 source/target 路径、elapsed_ms 外全部相等 | `build-independent-review/comparison.json` |
| 额外异常输入与重复结构检查 | 发现下列 P1-01、P2-02；截断 ASCII/binary 被正确拒绝 | `build-independent-review/adversarial/` |
| 验证器额外损坏检查 | 发现下列 P2-01；非项目 CTest 项 | `build-independent-review/validator-mutation/` |

主要实际命令：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-independent-review -Jobs 1
python tools/validate_experiments.py --metrics results/metrics/main-review --figures results/figures/module-c-v2 --reference results/metrics/module-c-v2 --output build/independent-review-archive.json

# 在 build-independent-review 作为 cwd，使用 git archive 导出的源码快照；
# DependencyRoot/CMake 实际传入主目录相应路径的 Resolve-Path 结果。
& './source snapshot with spaces/tools/verify_dependencies.ps1' -DependencyRoot $deps -CMake $cmake -BuildDirectory 'build-review relocated' -Jobs 1

# 以下运行时 PATH 临时加入项目 PCL bin 和已有 UCRT64 bin，结束恢复。
python tools/run_experiments.py --exe build-independent-review/lidar_icp.exe --generator build-independent-review/generate_test_data.exe --work build-independent-review/experiment-data --kitti data/kitti/drive_0005_pair --output build-independent-review/metrics --figures build-independent-review/figures --sweep
python tools/validate_experiments.py --metrics build-independent-review/metrics --figures build-independent-review/figures --reference results/metrics/module-c-v2 --check-alignment --output build-independent-review/validation.json
```

CMake 实际生成 `-O3 -DNDEBUG -std=c++17`，编译器为 UCRT64 `c++.exe`；响应文件使用独立 Eigen 3.4.0，未选系统 Eigen 5。测试使用显式条件/非零退出，未因 Release 禁用 assert 而失效。
CMake 的路径由源码/构建目录和发现的依赖生成；未发现必须使用作者工程目录才能构建的硬编码。WORKTREES 中本机路径是协作记录，脚本提供显式覆盖参数。
含空格源码副本的成功构建说明当前共享依赖下可移动源码和改变 cwd；**没有验证另一台机器重新安装全部依赖或 Linux/MSVC 构建**。

## ICP、位姿与指标审查

- `src/icp_registration.cpp:89` 将初值直接传给 `align`，`:93` 读取最终变换，未再次乘初值。并核对所安装 PCL 的 `icp.hpp`：最终矩阵以 guess 初始化，每次左乘增量。现有测试核对 aligned 与最终矩阵作用于原始 source 一致，避免只验证最终误差而遗漏重复初值。
- `p_target = T_target_source * p_source` 与人工 `target=T_gt*source` 一致；交换输入测试验证逆变换。source=curr、target=prev 时，在静态场景与坐标前提下为 `inverse(W_prev)*W_curr`。项目没有多帧累计里程计实现，不能声称其累计漂移已验证。
- `src/pose_utils.cpp:15` 检查有限性、SO(3)、det=+1 和末行；`:26` 输出旋转/平移及归一化四元数。JSON 明确 wxyz；平移以 target 坐标表示。微小角和 π 回归通过，未发现转置/逆矩阵/四元数顺序错误。
- `src/pose_utils.cpp:35` 平移误差为相同方向矩阵的平移差范数；`:43` 使用归一化四元数最短角，单位弧度，符合 SO(3) 相对角意义。
- `src/icp_registration.cpp:47`–`:59` 的独立指标为 **aligned source 到 target 的单向最近邻**，包含距离边界，RMSE 对门限内点计算，比例分母为 source 点数，零内点为 NaN/JSON null；不是对称重叠率，也不是有真值的定位误差。
- `getFitnessScore()` 为默认范围的最近邻平方距离均值，m²；与截断内点 RMSE 不同，文档标注正确。
- `src/registration_pipeline.cpp:20` 起将 PCL converged 与质量策略分开；`src/main.cpp:149` 附近拒绝结果不输出有效 pose/T。0.6 m 道路案例真实验证了 converged=true、accepted=false。
- 额外将同一人工运行的 truth 换成单位矩阵，除耗时和两个真值误差外，全部求解输出和质量结果相等；真值未参与初值或求解。证据：`adversarial/truth-real.json`、`truth-wrong.json`。
- 空/不足三点、NaN/Inf、无对应点、非法 SE(3)、非法参数、低内点和高 RMSE 在已有测试覆盖内正确处理；读取层另有 P1-01，不能笼统判为所有非法输入均通过。

## 真实数据、图像与独立复验

实际重新执行 `fetch_kitti_pair.py --output build-independent-review/kitti-fresh`。首次沙箱网络调用因 WinError 10013 失败，未计为成功；允许网络执行后成功，传输 **4,152,294 字节**，HTTP 206/范围/ETag/CRC 检查通过。
随后分别对新 BIN 执行 `kitti_bin_to_pcd.py`。新下载的两个 BIN、timestamps 和两个新 PCD 均与现有本地输入逐字节相同。完整 35 组运行使用原本地路径；其内容已由新下载/转换结果独立交叉确认。

| 文件 | 独立确认的 SHA256 |
|---|---|
| 0000000000.bin | `956976a1b391b18a17c42719212ef5de5e91e8ab986f7b79717343b126373ad3` |
| 0000000001.bin | `31e07ff7ffd67c2347a2cec3c8504d1d5fb35a2d22b6b02e2998470a230f188f` |
| 0000000000.pcd | `5e00bbfdc61d741671da5fa88e52c24087e570be2d01a1702f5a21d90d173f8c` |
| 0000000001.pcd | `e037084ed2d86b130f9ebc0702fd28b60effad776eaf1a181e2dc58cbad01c80` |
| timestamps.txt | `33529e08de8e7604d64d4f00398b501497568312dbf9398b96655688c8bd8387` |

转换按 little-endian float32 XYZI 处理，PCD payload 保持字节，未改轴/缩放，强度保留；ICP 消费 XYZ。采用 Velodyne x前/y左/z上，没有引入相机真值或外参，没有额外逐点去畸变。
序列确为 `2011_09_26_drive_0005_sync`，source=1、target=0。仅一个道路帧对，没有参考轨迹真值、动态点剔除或多帧漂移证据。

| 独立实测场景 | 平移真值误差 m | 旋转真值误差 rad | 内点 RMSE m | 内点率 | accepted |
|---|---:|---:|---:|---:|---|
| 人工 0.02 m | 0.0000304784994 | 0.000003693598627 | 0.0007980833413 | 1 | true |
| KITTI 0.3 m | 未测/null | 未测/null | 0.1692475275 | 0.9386925795 | true |
| KITTI 0.6 m | 未测/null | 未测/null | 0.2256860548 | 0.9016376558 | false |
| 直线反例 | 约 2.98e-8 | 1.570796324 | 约 4.41e-7 | 1 | true |
| 对称平面网格反例 | 约 3.07e-8 | 3.141592651 | 约 1.93e-7 | 1 | true |

六张 PNG 已逐张查看：轴、单位、图例和前后视窗一致，属于真实点云的 Matplotlib 数据图。重新绘制的六图与提交图 SHA256 全相同。对齐矩阵只取 accepted 结果；显示裁剪/稀疏不改变 ICP 输入。
固定原始点子样本到完整 target 的最近邻 RMSE：人工 0.3169857450→0.0000262796 m，道路 0.2743072312→0.1734374016 m，支持几何对齐改善；该抽样量也不是车辆定位精度。
README/EXPERIMENTS 明确区分上述概念，未发现将 KITTI 配准 RMSE 写成真实定位精度的现有表述。人工粗体素未达真值标准的情况已披露。

## 问题清单

### P1-01：非法 ASCII PCD 数字可静默变零并输出成功位姿

- **位置**：`src/cloud_processor.cpp:69`–`:96`（尤其 PCL 读取及转换）；测试缺口位于 `tests/test_cloud_processor.cpp` 的 `testPcdErrors`、`tests/test_pipeline.py` 的非法输入场景。
- **原因**：读取层只检查 PCL 返回码、字段和转换后的有限点。当前 PCL ASCII 解析对某些非法词元不返回失败，而得到有限零值，因此后续清理/ICP 无法识别原数据已损坏。不能把“PCL 返回成功”视作数字语法已严格验证。
- **实际复现**：6 点 ASCII XYZ，坐标为 `(0,0,0),(1,0,0),(0,2,0),(0,0,3),(2,foo,4),(4,1,2)`。构造 target 为相同数据但把 foo 显式替换为 0；使用 `--voxel-size 0.1`。程序退出 **0**、accepted=true、内点率 **1**、RMSE **4.420529574e-7 m**。将 source 的 foo 改为 0 再跑，除 source 路径和耗时外，全部报告字段完全相同。对未损坏的原始六点 target 运行也会接受：内点率 5/6。
- **证据**：`build-independent-review/adversarial/bad_token.pcd`、`zero_token.pcd`、`bad_token-zero-target.stdout.json`、`zero_token-zero-target.stdout.json`；初始对照在 `results.json`。命令为 `lidar_icp --source bad_token.pcd --target zero_token.pcd --voxel-size 0.1`，实际使用这些文件的完整路径。截断 ASCII/binary 对照均退出 3，未把它们误报成缺陷。
- **影响**：把损坏/错误导出的坐标无提示改成有效几何，可能形成虚假匹配、污染误差报告，不满足非法输入明确失败的要求。质量门禁不能修复读取时丢失的语义。
- **建议修复**：由主对话协调模块 A，在支持的 ASCII 读取路径严格验证每个数字词元被完整消费，遇非法词元明确失败；保留约定支持的 NaN/Inf 清理行为。避免实现一个同样宽松的解析器；明确编码/字段支持范围，并补上 foo、数值尾缀等真实文件/CLI 回归，重新运行完整测试。
- **阻止 GitHub 发布**：**是**。这是当前已复现的重要输入正确性缺陷，本报告未修复。

### P1-02：源码 LICENSE 与版权主体尚未确定

- **位置**：仓库根目录缺少 LICENSE；`README.md:172`、`docs/THIRD_PARTY.md:14` 明确仍为候选许可。人工图、人工数据元信息同样仍标 pending。
- **原因/影响**：当前交付不具备项目要求的明确源码使用授权和版权署名；不能称“MIT 开源项目”。候选 MIT 也不能覆盖 KITTI 派生图/结果。
- **复现**：`git ls-files` 无 LICENSE；作者历史当前使用 `Codex <codex@localhost>`，该提交身份不能代替真实版权归属决定。
- **建议修复**：用户确认版权主体和源码/自有成果许可后，由主对话加入准确 LICENSE，明确源码、自有图和 KITTI 成果范围，核对 README/THIRD_PARTY/各 ATTRIBUTION 的一致性。是否需要更新生成器 future metadata 由主对话安排；保留历史实验原证据，不应静默改写归档。
- **阻止 GitHub 发布**：**是**，按项目明确的发布前要求。不是断言“任何无 LICENSE 仓库都不能公开”，也不擅自为用户选择许可。

### P2-01：归档验证器对新增案例的矩阵和命令校验不完整

- **位置**：`tools/validate_experiments.py:35`–`:78`、`:127`–`:136`；损坏测试 `tools/test_experiment_validation.py`。只有参考 10 案例做完整报告比较，25 个扫描案例没有相同参考保护。
- **原因**：接受报告仅校验 pose/T 非 null、收敛及标量门禁，未验证 SE(3)、pose/T 一致性；command 主要检查退出码和是否出现 --truth，没有把 argv 的文件和参数与报告逐项对应，也未核验 provenance 的 source_sha256。
- **实际复现**：复制 main-review 到 `build-independent-review/validator-mutation`；将 `sweep_noise_0.0.json` 的 T 改成 **4×4 全零矩阵**，同时将对应 command argv 改成 `['fake_executable','--truth','fake_truth','--max-rmse','999']`，保留退出码。用原始六图和 module-c-v2 reference 校验，**仍返回 passed / 35 报告**。最初完全删掉 --truth 会被现有检查正确拦下；这里保留该词后即可绕过语义核对。
- **影响**：不能把该工具的 passed 理解为35组位姿/命令/源码溯源的完整性证明。当前归档另经真实 CLI 复跑和35报告比较，未发现实际伪造或损坏，故不升级为 P1。
- **建议修复**：补矩阵尺寸、有限性、SE(3)、pose/diagnostic 一致性；解析 argv 并核对配置/初值/truth/输入对应；增加上述损坏回归。源码哈希核查应允许显式指定受审源码根，区分历史归档和当前版本，不能盲目用当前源码否定历史结果。
- **阻止 GitHub 发布**：**否**；建议发布前修补，以免验证器能力说明过强。

### P2-02：质量通过仍可接受重复结构的错误平移，鲁棒性证据有限

- **位置**：`src/registration_pipeline.cpp:20`–`:38`、`src/icp_registration.cpp:34`–`:61`；`tools/run_experiments.py:232`–`:255`；`README.md:147`–`:150`。
- **原因**：单向最近邻内点质量没有对应唯一性、可观测性或运动先验；几何指标无法区别重复位置。已有90°直线/180°对称网格反例披露准确，但初值扫描只覆盖 x 平移、固定种子，未覆盖一般三轴旋转/参数交互。不能把有限对称网格反例推广为“所有平面 point-to-point ICP 都不可观测”。
- **独立新增复现**：固定 Python `Random(7)` 在单位立方体生成150个三维点，source 为这组点；target 为该组点与其 x+5 m 副本的并集；指定真值单位阵，初值为 x+5 m，体素0.005 m。真实 CLI 返回 accepted=true、内点率 **1**、RMSE **7.872274178e-8 m**，但平移真值误差 **5 m**。证据 `adversarial/repeated.command.json`、`repeated*.pcd`、`repeated.stdout.json`。这是带部分视野的重复结构歧义，不能据此声称一般随机三维几何本身退化。
- **影响**：accepted 是数值门禁，不是实际运动正确或可用于安全驾驶的证明；将其用于累计轨迹仍可能错误。噪声、离群点和空间裁剪已做有界复验，一个真实道路帧对不构成通用鲁棒性证明。
- **建议修复**：近期保留局限和反例，并将重复结构案例纳入可持续回归/文档；明确下游除 accepted 外仍需场景/运动约束。将旋转初值和更多种子作为后续实验建议，不要求本轮开发新算法或篡改这些反例的 accepted。
- **阻止 GitHub 发布**：**否**，前提是按当前“两帧学习/工程实践”范围发布并保留限制；若宣称可靠自动驾驶定位或退化检测能力，则不能通过该用途验收。

### P3-01：固定依赖版本策略可在 CMake 中更明确

- **位置**：`CMakeLists.txt:23`–`:24`；`tools/verify_dependencies.ps1`。
- **原因/复现**：直接 CMake 仅要求 Eigen >=3.3、PCL >=1.12，与项目固定验证版本1.15.1/3.4.0不同。标准脚本本次确实选中正确前缀，未出现实际混库；没有用另一版本做兼容性试验。
- **建议**：考虑固定版本模式或清晰的版本漂移诊断，把“支持范围”与“已测固定组合”区分；可补同环境 CI。不得为实现这些建议擅自升级依赖。
- **阻止 GitHub 发布**：**否**。

## GitHub 发布与许可核查

当前跟踪204个文件，合计 **3,005,386字节**；最大文件为 `kitti_alignment.png`，**1,117,186字节**。检查所有分支可达对象的大小与文件名，未发现原始 BIN/PCD、exe/dll/zip、构建缓存或大于10 MiB的文件。未配置 remote。
对当前文本和历史229个文本 blob 做用户目录绝对路径、常见 GitHub/AWS 凭据及私钥头模式检查，未发现匹配。这是静态模式扫描，不是已运行专用全规则 secret scanner，也不保证不存在所有类型隐私。
.gitignore 覆盖 build*/、本地依赖/工具、KITTI/raw 数据、二进制、.env 和常见密钥文件；本次所有复验产物未进入 Git 跟踪。

本轮在线读取并核查以下官方来源：

- [KITTI Copyright / Citation](https://www.cvlibs.net/datasets/kitti/)：数据许可 CC BY-NC-SA 3.0；Raw 引用 IJRR 2013。
- [AWS KITTI 登记](https://registry.opendata.aws/kitti/)：同样许可，公共桶 avg-kitti、eu-central-1，支持匿名访问。
- [CC BY-NC-SA 3.0 条款摘要](https://creativecommons.org/licenses/by-nc-sa/3.0/)：署名、非商业、相同方式共享要求。

现有道路图及结果目录已提供作者、作品、来源、许可链接和修改说明，混合道路图/CSV/provenance 采取整文件沿用许可的保守处理；未发现宣称 KITTI 属于 MIT 或公有领域。
**求职展示或后续商业用途是否符合 NC、具体派生成果的法律归类仍需按实际用途确认，本报告不作确定法律结论。** 原始数据不提交，并不自动免除派生成果的许可条件。
本轮未分发第三方二进制；若未来打包 exe/Python 环境，需另核对实际分发依赖的完整许可通知，不能把本次源码审查当二进制发行许可验收。

## 需求边界、整改顺序与简历表述

| 项目 | 独立结论 |
|---|---|
| R01 PCD 读取 | 常规编码与清理通过；P1-01 待修，不无保留通过 |
| R02 预处理/可视化 | 预处理与六张离线数据图通过；交互 PCL 窗口未实现/未渲染验收 |
| R03–R06 ICP/位姿/误差/人工真值 | 已测范围通过，含近初值、逆方向、失败和微小角测试；不推导全场景正确 |
| R07–R08 道路/实验/溯源 | 单道路帧对和有界35组复现通过；验证器缺口见 P2-01 |
| R09 公开交付 | 构建和中文文档具备；源码许可、P1整改及最终发布批准待完成 |

主对话应先修复 P1-01 并补回归/重跑完整 ON Release/CTest，再确认 P1-02 并核对许可范围。P2-01 建议同期修补，P2-02 保留为明确算法局限与后续实验建议。整改后由主对话重新验收、维护 TASKS/PROGRESS；不能因本报告已生成就直接把 V01 标 DONE。公开远程创建/推送仍需用户明确批准。

可以如实用于实习简历的内容：

> 基于 C++17、PCL 与 Eigen 构建两帧 LiDAR 点云预处理、point-to-point ICP 配准及相对位姿分析工具，提供 SE(3) 校验、独立最近邻 RMSE/内点率、质量门禁和 JSON 报告；在固定环境下通过10项CTest，完成35组人工/道路及参数退化实验，复现KITTI相邻帧配准与六张可追溯数据图，分析低RMSE仍出现错误位姿的局限。

如需写数值，明确“人工固定种子、0.02 m体素，平移误差约3.05e-5 m、旋转误差约3.69e-6 rad”；道路只可写“该帧对0.3 m体素，内点RMSE约0.16925 m、内点率93.87%”，注明不是车辆定位真值误差。根据个人实际贡献描述使用/集成PCL ICP，不应冒称自研ICP求解器。
不能写完整SLAM/FAST-LIO复现、实车厘米级定位、通用抗退化、实时性能、跨平台全部验证、零缺陷或已经完成MIT开源发布。当前也不能写“独立技术审查全部通过”。

尚未执行：交互窗口 Render、完整内存检测器/模糊测试、多帧真实轨迹与漂移评估、其他平台构建、其他真实道路序列。报告不将这些未执行项写成通过。
