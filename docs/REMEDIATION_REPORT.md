# 独立审查整改与复审交接

日期：2026-10-27。基线 4bc4e1346288b150e367c04576cae8f6c86c1ce7。
原报告为 REVIEW_REPORT.md，SHA256：
`3e18e926978b461dcaa10fd864d81044e601d23da2c43dc00037df748822f0b0`。
开始时 main 无已跟踪文件改动，仅该报告未跟踪；本轮保留其字节并一并提交，不修改独立结论。
本文件是主对话整改自检，V01 仍待独立对话复审，不称为独立审查全部通过。

## 逐项方案与处置

| 问题 | 定位/最小方案 | 自检结果 |
|---|---|---|
| P1-01 非法 PCD | cloud_processor 的 ASCII 读取边界先读 PCL header，再严格核对词元/行/点数，随后沿用 PCL 解码；二进制不做文本解析 | 修复并回归通过 |
| P1-02 授权 | 审查自有/第三方范围，取得用户明确 MIT/署名授权，再增加 LICENSE；PCL 修补上下文保留原通知 | 用户授权已落实；范围和例外见 THIRD_PARTY |
| P2-01 验证器（用户顺序 P2-2） | 校验所有案例矩阵、pose/diagnostic、argv/CSV/输入溯源；显式指定源码根核验 | 修复，含原报告组合篡改的失败对照 |
| P2-02 重复结构（用户顺序 P2-1） | 先复现，再评估能否无先验区分重复位置；保存持续回归和使用限制 | 风险已展示/记录，未声称算法消除了歧义 |
| P3-01 版本策略 | CMake 提示未测版本，提供严格固定组合开关；标准脚本启用严格模式 | 实际固定组合通过；诊断逻辑正反例通过，未升级任何依赖 |

### PCD 输入正确性

原报告 6 点 foo/0 对照已在旧二进制重现：退出0、accepted=true。
相同损坏输入在新二进制退出3、stdout空，不写有效位姿或输出 JSON。
新测试还交换 source/target，不能通过仅验证一侧绕过检查。
合法十进制、正负号、小数/科学计数法保留；显式大小写 NaN、Inf、Infinity 和符号形式保留给 removeNonFinite。
foo、数字尾缀、残缺指数、十六进制、逗号、数值溢出/不能表示的 float32 非零数、错误列/点数明确失败。
ASCII 按一行一个点、COUNT 展开读取，允许空行/整行注释，不接受行尾额外词元；
XYZ 要求单值 FLOAT32/FLOAT64，整型辅助字段按 PCL 的 8/16/32 位类型检查。
现有 ASCII/binary/binary_compressed、float64 正常转换和元数据保留测试继续通过。
这是针对读入语法的严格边界，不是替换 PCL 或新增配准算法。

### 重复位置为何仍然危险

Random(7) 生成150个单位立方体点；target=source及其 x+5m 副本；真值单位阵、初值 x+5m、体素0.005m。
新 CLI 和持续回归均得到 accepted=true、内点率1、RMSE=7.872274178e-8m、平移误差5m。
错误副本同样提供完整、极小残差的对应，局部数值门禁无法知道真实物理位置。
该案例是部分视野与重复位置歧义，不能推导所有平面或所有一般三维点云都退化。

- 相对初值修正约束无效：本例初值已经位于错误副本，最终修正接近零。
- 固定绝对位移上限没有可信运动范围/时间/传感器前提，会误拒合法任务；不硬编码5m阈值。
- 双向覆盖率可揭示 target 多一份几何，但无法可靠区分正常部分视野；不是通用真实性判据。
- 局部几何条件数也不保证发现离散重复位置。真实外部运动先验可另行设计，但本轮没有该输入与验证依据。

因此本轮不改数值门禁冒充通用鲁棒定位；下游必须结合场景/运动约束，不能只依赖 accepted。
未来改变该反例行为时应重新审查原因，不把测试中的 accepted=true 当作永久产品要求。

### 验证器与源码溯源

所有案例均验证矩阵形状/有限性、SE(3)、有效 T/diagnostic 一致、rotation/translation/quaternion 一致；
允许 q 和 -q；拒绝状态仍只保留诊断。未收敛/非法最终变换的诊断可保留非法数值，不误当有效位姿。
argv 仅允许 CLI 支持的成组选项，拒绝假程序名、重复/未知选项和缺值，
核对 source/target、output案例名、CSV initial、全部可配阈值/默认值和输入哈希成员。
完整输入核验时进一步读取初值和 truth 文件，核对初值及已测真值误差；--skip-inputs 不冒称这些原始文件已验。
`--source-root <snapshot>` 明确核查该次源码哈希；默认 source_verification=not_requested，
历史归档应提供当时快照，不能盲目与当前源码比较。哈希是完整性检查，不是数字签名或来源真实性证明。
新归档source_hash_policy=utf8-lf只规范化CRLF/LF后校验源码，另保留source_byte_sha256原始字节哈希，
避免Git换行策略造成假阳性；旧归档没有此字段时仍按原始字节核对，不改写历史哈希。

已实际重放原报告的组合篡改：新增扫描案例 T 改全零，argv 改 fake_executable/虚假truth/阈值999。
旧验证器返回 passed，新验证器明确抛错。单独矩阵、pose、命令、初值/truth/源码变更也有正反例。

## 实际验证结果与证据

| 检查 | 实测结果 | 本地日志/公开摘要 |
|---|---|---|
| 全新 build-remediation Release/PCL ON | 配置、全部 C++ 目标编译成功，固定版本模式 ON | build/remediation-release.log |
| 最终完整配置/构建/CTest | 10/10，0失败，3.95s | build/remediation-final-regression-v2.log |
| A / CLI 内部组 | A 7/7，CLI 11/11（含非法 PCD、重复结构、已知真值） | build-remediation/Testing/Temporary/LastTest.log |
| 工具 / 验证器内部组 | 5/5、10/10；均离线、无 KITTI/绘图依赖 | 同上，不重复计入 CTest 总数 |
| 整改后完整实验 | 原35案例+重复位置=36，46输入哈希、16源码哈希、6图、35参考案例通过 | build/remediation-experiments-v2.log、remediation-validation-v2.log |
| 人工0.02m | 平移3.04784994e-5m，旋转3.693598627e-6rad | remediation/synthetic_v0.02.json |
| KITTI0.3m | 接受，RMSE0.1692475275m，内点率0.9386925795 | remediation/kitti_v0.3.json |
| KITTI0.6m | 收敛但拒绝，RMSE0.2256860548m | remediation/kitti_v0.6.json |
| CMake版本诊断 | 模拟未测1.15.2时严格模式失败、非严格警告；固定组合通过 | build/remediation-version-diagnostics.json |

道路原始数据使用本地已独立下载并有哈希的两帧，本轮重新执行真实 C++ 配准；没有重新下载/重建PCL。
35个旧报告除路径/耗时外相同，六图重新生成与旧PNG逐字节相同；不是以旧报告代替新运行。
KITTI RMSE不是车辆定位真值误差；所有未知真值仍为null。
公开结果位于 `results/metrics/remediation/`，包含真实进程输出、命令、stderr、CSV、provenance、
validation、before-after、version-diagnostics、acceptance和署名。原始数据/完整构建日志留在忽略目录。

复验命令（已存在目录不要重复覆盖，复审请选新目录）：

```powershell
./tools/verify_dependencies.ps1 -BuildDirectory build-remediation -Jobs 1
# 先解析所需 Python，再临时加入 PCL bin 与 UCRT64 bin 到 PATH，结束恢复。
python tools/run_experiments.py --exe build-remediation/lidar_icp.exe --generator build-remediation/generate_test_data.exe --work build-remediation/experiment-data-v2 --kitti data/kitti/drive_0005_pair --output build-remediation/metrics-v2 --figures build-remediation/figures-v2 --sweep --repeated-structure
python tools/validate_experiments.py --metrics build-remediation/metrics-v2 --figures build-remediation/figures-v2 --reference results/metrics/main-review --check-alignment --source-root .
python tools/validate_experiments.py --metrics results/metrics/remediation --figures results/figures/module-c-v2 --reference results/metrics/main-review --skip-inputs --source-root .
```

完整 PATH 设置见 EXPERIMENTS。最后一条不声称原始数据已检查，但确实核验当前受审源码。
本轮源码哈希不包含文档；文档更新不影响已运行二进制或原实验哈希。

## 失败、保留项与复审边界

新增验证器初稿误把历史CSV的 identity 识别为路径，已修正，不修改历史CSV以迎合代码。
加入truth校验后，一项离线测试意外试读历史路径，已改为先测试自带局部初值夹具；
失败日志 remediation-validator-prebuild.log、remediation-validator-final.log 保留；后续10/10及完整CTest通过。
不是跳过失败测试、放松SE(3)或屏蔽警告。第三方分配器警告仍保留。

源码 MIT/署名决策已由用户作出，无待确认的同一许可问题；第三方范围继续受原许可约束。
没有发布远程或推送。未实现/验证 PCL 交互 Render、完整退化检测、多帧轨迹或通用鲁棒性。
独立对话可按 REVIEW_CHECKLIST 开始复审 P1-01/P1-02、P2验证器及风险披露；
不得用本文改写原独立报告，只有复审实际结论才能推进 V01。

提交前文件检查：323个候选文件，最大1,117,186字节；无原始点云、编译缓存、超10MiB文件，
用户目录绝对路径/常见凭据模式与Markdown链接检查均无发现（静态检查并非所有隐私的证明）。
另从Git暂存区导出16个源码文件到新快照，使用--source-root独立核验通过，确认Git换行转换不造成误报。
日志：build/remediation-publication-audit.json、build/remediation-index-snapshot-validation.log。
