# 第二轮独立技术复审与公开发布验收

日期：2026-10-27（Asia/Shanghai）。受审提交：`3bdc6c40c54da00ff1a0e0b5a8fb18c16277dd2a`。

## 正式结论

**通过本轮整改独立复审，可以按“两帧 LiDAR 点云配准与相对位姿估计的教学和工程展示项目”范围进入公开 GitHub 发布流程。**

两个原 P1 已关闭；归档验证器 P2 已修复并独立复验；重复结构 P2 作为明确披露、持续回归的算法局限保留，不是已经消除的算法缺陷。原 P3 的版本诊断/严格模式已满足当前发布条件。
本轮未发现新的 P0/P1 或必须先修复的发布阻断项。没有要求主对话继续增加算法或重构核心模块。

这项结论是技术与当前许可文件范围的发布验收，不是通用自动驾驶定位能力或所有权法律保证；不等于本轮获得创建公开远程和推送的授权。主对话仍须取得用户明确发布批准，并将本报告纳入交付、据此更新审查/发布状态。本轮没有执行这些写操作。

## 基线与原报告保护

- 实际 cwd：用户指定项目目录；分支 `main`，完整 HEAD 与指定提交一致。实际执行 `Get-Location`、`git status --short --branch`、`git rev-parse HEAD`、`git log -5 --oneline`；开始时状态仅 `## main`，工作区干净。
- 已读 AGENTS、README、第一轮报告、REMEDIATION_REPORT、REVIEW_CHECKLIST、PROGRESS、THIRD_PARTY，并复核 PROJECT_SPEC、ARCHITECTURE、INTERFACES、TASKS、DECISIONS、ENVIRONMENT 及实际代码差异。
- 第一轮报告 SHA256 为 `3e18e926978b461dcaa10fd864d81044e601d23da2c43dc00037df748822f0b0`，与上一轮交付及整改记录相同。**原报告未修改，原先“不通过”的历史结论不被回写成通过。**
- 没有修改核心源码、测试、旧归档、分支和依赖，没有提交、合并、创建远程或推送。唯一新增交付文件是本报告；实际运行产物仅写入被忽略的 build*/。

## 原问题逐项裁定

| 第一轮编号 | 第二轮裁定 | 是否阻止本次范围的公开发布 |
|---|---|---|
| P1-01 非法 ASCII PCD | 已关闭，原始词元反例与正常/非有限值流程均实际复验 | 否 |
| P1-02 源码授权与版权署名 | 当前授权文件范围已关闭，MIT/署名与第三方排除清楚 | 否 |
| P2-01 归档验证器（用户本轮称 P2-2） | 已关闭，原组合篡改及单独语义/源码篡改均被拒绝 | 否 |
| P2-02 重复结构（用户本轮称 P2-1） | 风险处置通过；算法歧义仍然存在，明确保留 | 否，限教学/工程展示用途 |
| P3-01 固定依赖版本策略 | 已处理，标准脚本严格模式及警告/失败分支已验证 | 否 |

新增问题：P0=0、P1=0、P2=0、P3=0。原 P2-02 不应被统计成“算法已修复”，也不能因反例仍 accepted 就把本次正确保留的风险披露当作整改失败。

## P1-01：输入读取整改的独立验证

代码位置：`src/cloud_processor.cpp:23` 的 `validateAscii`；`:133` 的 `loadPcd` 在 PCL header 解析后、正文解码前调用严格检查，三种编码没有被统一当文本处理。

独立重建六点原反例：`(0,0,0),(1,0,0),(0,2,0),(0,0,3),(2,foo,4),(4,1,2)`；正常对照将 foo 显式替换为0。实际使用新二进制、体素0.1 m，并指定此前不存在的报告路径。

| 实际检查 | 结果 |
|---|---|
| foo、1foo、1.2m、1e、0x1p2、1,2、1e999、1e-999、3.5e38；分别放在 source/target | **18/18 拒绝**；全部退出3、stdout为0字节、没有生成报告文件 |
| 正常六点对自身 | 退出0、accepted=true |
| nan、NaN、-NaN、inf、+INF、-inf、infinity、+Infinity 分别附加到正常点云 | **8/8 通过清理**；input=7、finite=6、output=6，配准接受，没有静默保留成零点 |
| ASCII/binary/binary_compressed、float64、元信息 | 实际 CTest 的模块 A 测试通过，覆盖三种编码的保存/读取和坐标比较 |
| 新增源/目标两侧非法输入 CLI 回归、正常/异常已有场景 | 实际 test_pipeline 11/11 内部测试通过 |

证据：`build-independent-review-v2/independent-probes/cli-probes.json`、`good.stdout.json`；完整编码和边界回归见该构建的 `Testing/Temporary/LastTest.log`。模块 A 7/7 内部测试均通过，含 `tests/test_cloud_processor.cpp:135` 的严格词元、行数和显式非有限数回归。

因此原先 foo 被静默转零、再被接受的问题已真正关闭。判断依据是新程序拒绝原反例且无报告，而不是仅凭有限点清理后的数值或主对话声明。严格支持范围已经在 INTERFACES 中写明：浮点XYZ、ASCII一行一个点、明确数字语法；不承诺接受所有非标准PCD扩展。

## P1-02：许可与第三方范围

- 根 `LICENSE` 包含完整 MIT 授权、保留通知条件与免责声明；署名准确为 **Copyright (c) 2026 Wang Chenqi**，与 README、THIRD_PARTY、纯合成成果说明及新生成器元信息一致。正文与 [OSI MIT 标准文本](https://opensource.org/license/mit) 核对，无缺失条款。
- MIT 后的 Scope 明确限定用户有权授权的项目原创部分，排除第三方依赖、上游摘录、KITTI数据和道路派生成果；不是给第三方重授 MIT。
- `tools/prepare_pcl_source.py:2`–`:3` 标记上游匹配上下文的 BSD 范围，并指向 `licenses/PCL-BSD-3-Clause.txt`。该文件与本地固定 PCL 1.15.1 原 LICENSE 逐行去尾随空白后完全相同，版权通知、三项条件和免责声明完整保留。在线交叉核对 [上游固定版本许可](https://github.com/PointCloudLibrary/pcl/blob/pcl-1.15.1/LICENSE.txt)。没有因为上游原文保留 XXX 占位通知就擅自更换作者。
- 已重新读取固定 Eigen 3.4.0 的 COPYING.README：主要 MPL2，部分第三方文件另有 BSD/LGPL；THIRD_PARTY 和根许可没有把这些内容变成项目原创 MIT。未分发 Eigen/PCL 库源码包或二进制。
- 道路图、道路报告和混合 CSV/provenance/validation 有单独署名与范围说明；Raw 作者、IJRR 2013作品、来源、修改说明和 CC BY-NC-SA 3.0 链接齐备。在线再次核对 [KITTI Copyright/Citation](https://www.cvlibs.net/datasets/kitti/)，没有将匿名可下载误解为无许可限制。
- 历史 pending 元信息保留为当时证据，目录说明补记当前原创MIT范围；没有篡改历史实验。新生成数据已采用当前许可说明。

当前文件未发现第三方材料被错误宣称为原创的新增证据，原先“无LICENSE/署名未定”的发布阻断已解除。用户授权已在工程规范和整改记录中明确，本轮不重复要求同一选择。

**权利边界**：无法仅凭源码和提交记录独立证明所有原创内容的最终法律权属、排除所有可能的学校/雇主/共同作者或AI生成内容来源争议；当前没有相反的新证据，不把这些假设重新列为未解决P1。KITTI具体商业使用、衍生作品法律归类仍按实际用途核实，不能把本报告当商业授权。未来若分发exe或打包依赖，须另做实际分发内容的许可通知检查。

## P2-02：重复结构风险处置

本轮直接用第一轮留存的原始150点三维结构、x+5 m副本、单位真值和5 m初值再次执行新CLI；另在36组完整实验中执行新增 `repeated_structure`。

两者均得到：accepted=true，内点率1，内点RMSE **7.872274178e-8 m**，平移真值误差 **5 m**。证据：`independent-probes/repeated.stdout.json`、`metrics/repeated_structure.json`。

`tests/test_pipeline.py:245` 有持续回归，`README.md:153` 明确披露错误副本和下游运动/场景约束，REMEDIATION_REPORT解释为何相对初值限制不能辨认该歧义。未发现README宣称通用鲁棒定位或已经实现退化检测。

裁定：保留这一局限**不阻止当前教学与工程展示项目发布**。accepted只表示局部数值门禁通过；不能据此证明物理位置、对应唯一性或安全驾驶可用。若将用途扩大为可靠自动驾驶定位、真实里程计或通用抗退化能力，当前证据不足，需重新验收。对称网格、直线及重复位置的反例不能泛化成“所有平面或一般三维结构都不可观测”。

## P2-01：验证器独立篡改测试

审查 `tools/validate_experiments.py:44`（pose）、`:72`（命令）、`:109`（源码）、`:151`（truth）及完整输入模式。下列测试对复制到 build*/ 的整改归档操作，**不依赖reference保护来发现错误**，不改原归档：

| 独立篡改 | 实际结果 |
|---|---|
| 新扫描案例T改为4×4全零 | 拒绝，SE(3)末行非法 |
| 合法但与T不同的diagnostic矩阵 | 拒绝，diagnostic/T不一致 |
| pose平移改为[9,9,9] | 拒绝，pose/T不一致 |
| 命令max-rmse改999 | 拒绝，命令配置与报告不一致 |
| 第一轮原“全零T+fake_executable/假truth/999”组合 | 拒绝 |
| 单独把可执行文件改fake_executable，T保持正常 | 拒绝，排除组合只因T错误而失败的掩盖 |
| 单独改为fake_truth路径 | 拒绝，命令输入缺溯源成员 |
| 初值文件改单位阵，更新路径、CSV及其哈希，使文件哈希本身有效 | 拒绝，初值文件/报告不一致 |
| truth文件改单位阵，保留其他案例共享的原truth成员，给替代文件合法哈希 | 拒绝，truth文件与报告误差不一致 |
| 从受审Git提交导出16文件源码快照，再修改其中一个文件 | 干净快照16哈希通过；修改后拒绝，源码哈希错误 |

证据：`build-independent-review-v2/independent-probes/validator-probes.json`及各隔离副本。
truth测试初版删除了其他案例共享的哈希成员，先被成员检查挡住；随后修正测试夹具，保留共享原成员，并确认实际进入truth数值比较后拒绝。没有将早期无关失败当作truth语义通过证据。

项目自身验证器10个内部测试也全部通过，包含矩阵形状/非有限元素、旋转/四元数等检查；q与-q等价处理仍保留。
源码核验显式指定 `--source-root`，本次同时核对当前源码和从 `git show HEAD:<path>` 导出的16文件快照。归档utf8-lf策略仅规范CRLF/LF，未规范化其他源码内容。默认不请求源码核验时会报告 not_requested，不冒称源码已验。

因此原P2-01针对的矩阵/命令/初值/truth/源码缺口已关闭。哈希和一致性验证仍不是数字签名，不能证明主动伪造整套报告与全部清单不可能，也没有这样的新能力声明。

## P3：依赖固定策略

`CMakeLists.txt:10` 新增严格模式，`:26`–`:31` 对未测组合给出失败或警告；`tools/verify_dependencies.ps1:40` 显式开启严格模式。本轮实际cache为Release、PCL ON、严格版本 ON，探针确认PCL1.15.1/Eigen3.4.0，未选系统Eigen5。

额外把当前CMake中的原始判断块提取为临时cmake -P脚本，仅模拟版本元信息：固定组合严格模式退出0；PCL1.15.2或Eigen3.4.1严格模式退出1；PCL1.15.2非严格模式退出0并发出警告。证据 `independent-probes/version-probes.json`。没有安装这些其他版本，也不据此声称它们的实际库兼容性已验证。

裁定：原P3已满足发布条件；CI等建议不是本轮必修项。

## 完整工程与实验回归

| 实际运行 | 结果 | 本地证据 |
|---|---|---|
| 全新build-independent-review-v2配置/Release编译 | 成功，固定既有工具链/依赖，无环境重建 | `build/independent-review-v2-build.log` |
| 完整CTest | **10/10，0失败，4.26 s** | 上述日志、该构建的LastTest.log |
| 模块A / CLI / 验证器内部测试 | **7/7、11/11、10/10**；不重复计入CTest总数 | LastTest.log |
| 已提交整改归档完整核查 | **36报告、46输入、16源码、6图、35旧参考案例通过** | `build/independent-review-v2-archive.json` |
| 新二进制完整实验 | **36组**，含正常、预期质量拒绝和退化反例 | `build/independent-review-v2-experiments.log`、`build-independent-review-v2/metrics/` |
| 新实验完整校验，与整改36案例比较 | **36报告、46输入、16源码、6图、36参考案例通过** | `build-independent-review-v2/validation.json` |

实际主命令：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-independent-review-v2 -Jobs 1
python tools/validate_experiments.py --metrics results/metrics/remediation --figures results/figures/module-c-v2 --reference results/metrics/main-review --source-root . --output build/independent-review-v2-archive.json

# 实际运行前先选定原CPython，再临时加入PCL bin/UCRT64 bin；结束后恢复PATH。
python tools/run_experiments.py --exe build-independent-review-v2/lidar_icp.exe --generator build-independent-review-v2/generate_test_data.exe --work build-independent-review-v2/experiment-data --kitti data/kitti/drive_0005_pair --output build-independent-review-v2/metrics --figures build-independent-review-v2/figures --sweep --repeated-structure
python tools/validate_experiments.py --metrics build-independent-review-v2/metrics --figures build-independent-review-v2/figures --reference results/metrics/remediation --source-root . --check-alignment --output build-independent-review-v2/validation.json
```

以上两次完整归档核查均**没有使用skip-inputs**。实际断言校验计数36/46/16/6，并未直接采用主对话数字。36参考报告除source/target路径及elapsed_ms外一致。
本轮复用第一轮已独立下载/转换的本地KITTI帧对，并实际核对输入哈希和重新执行C++配准；没有重新联网下载数据或编译PCL，也没有把旧JSON当作新运行。

| 新二进制实测 | 平移真值误差m | 旋转真值误差rad | 内点RMSE m | 内点率 | accepted |
|---|---:|---:|---:|---:|---|
| 人工0.02 m体素 | 3.04784994e-5 | 3.693598627e-6 | 0.0007980833413 | 1 | true |
| KITTI0.3 m | null/未测 | null/未测 | 0.1692475275 | 0.9386925795 | true |
| KITTI0.6 m | null/未测 | null/未测 | 0.2256860548 | 0.9016376558 | false |
| 重复结构 | 5 | 2.580956751e-8 | 7.872274178e-8 | 1 | true |

0.6 m案例仍为converged=true、accepted=false，有效pose/T为null。核心ICP/位姿实现没有在本次整改中改变。
六图本轮实际重新生成，SHA256与提交六图全部相同，沿用首轮已逐张查看的相同图像内容。校验源码、图像哈希和实际绘图输入/矩阵来源一致，没有用AI图片替代真实结果。固定原始子样本几何RMSE仍为人工0.3169857450→0.0000262796 m、道路0.2743072312→0.1734374016 m；这些也不是车辆真实定位误差。

## GitHub发布内容扫描

扫描受审提交的323个跟踪文件，共3,202,007字节；最大仍为kitti_alignment.png，1,117,186字节。扫描所有分支可达历史对象：无大于10MiB文件、原始BIN/PCD、exe/dll/zip或常见密钥文件；未配置remote。
对338个历史文本blob做常见GitHub/AWS凭据、私钥头和用户目录绝对路径模式扫描，未发现匹配。已有.gitignore继续覆盖构建、本地依赖、原始数据和常见秘密文件。该结果是本次静态模式扫描，不是所有隐私或凭据的绝对保证。
证据：`build-independent-review-v2/publication-audit.json`。本报告新增后总文件数将变化，不把受审提交的323说成最终发布提交的文件数。

## 发布与简历必须保留的边界

1. 项目是两帧点云配准/相对位姿实践，使用PCL point-to-point ICP，不是完整SLAM、FAST-LIO或自研完整ICP求解器。
2. accepted/converged均不是位姿真值正确的充分条件；重复位置5 m错误、直线约90°和对称网格约180°歧义仍存在，依赖初值及场景约束。
3. KITTI仅一个道路帧对，没有轨迹真值、真实定位精度、多帧漂移或通用道路鲁棒性证据。0.16925 m只可称该配置下的内点配准RMSE。
4. 固定种子、有界单因素扫描不等于全参数、全随机种子验证；单次align耗时不能写成实时FPS或完整系统延迟。
5. 无IMU融合、地图、回环或逐点去畸变；交互PCL Render、其他平台及完整内存检测器没有本轮实测。
6. 源码原创部分MIT与KITTI道路成果CC BY-NC-SA范围必须继续分开，不能将整个混合仓库和所有数据统称MIT。

可在实际个人贡献范围内写“固定环境全新Release、10项CTest、36组可复现实验、46输入/16源码哈希和六图溯源验证，分析重复结构低RMSE错误位姿”。不能写“修复所有退化问题”“实车厘米级定位”“通用鲁棒定位”或“所有权已获法律保证”。

**主对话下一步**：无需先做额外技术整改即可进入发布收尾；纳入本报告、更新V01/R01等状态和相关当前说明，保留第一轮原文及上述局限，取得用户明确公开发布批准后再发布。若增加新功能、二进制分发、数据或改变许可范围，应按变化补充验收，而非沿用本次结论无限扩展。
