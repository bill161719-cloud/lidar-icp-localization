# 技术决策

2026-10-27（Asia/Shanghai）：

1. 保留现有 MSYS2 UCRT64 GCC 16.2.0 x86_64，不擅自安装/切换 MSVC。
2. 最小 bootstrap 不依赖 PCL/Eigen，默认 LIDAR_ENABLE_PCL=OFF；ON 必须 REQUIRED 查找依赖，禁止静默降级。
   这只验证基础工程，不代表算法可用。PCL 安装后需单独运行依赖探针。
3. CMake 采用项目内 Python wheel 3.31.6（仅提供构建工具），不修改系统 PATH 或替换编译器。
4. 模块用 PCL PointXYZ，共享类型由主对话维护；不提前生成 A/B/C 的伪实现或占位测试。
5. 统一 T_target_source、米、弧度、列向量，初始位姿语义与最终矩阵方向写入接口。
6. fitness 与独立 RMSE 分开；收敛状态不等同于精度或正确位姿。
7. 保留现有工具链的依赖路线：Eigen 3.4.x、PCL 稳定版及 Boost/FLANN/VTK 均用 UCRT64 GCC 构建，
   先评估包可用性与版本兼容性。MSYS2 当前 eigen3 页面为 5.x，不自动采用，避免未验证的 PCL 兼容性。
   尚未确认 UCRT64 PCL 现成包可用，不能声称一条 pacman 命令即可安装。
   MSVC + 匹配 PCL/vcpkg 可作为替代路线，但属于工具链决策，须用户确认后再执行。
8. 初始 Git 若未配置作者，使用单次命令 `-c user.name=Codex -c user.email=codex@localhost` 标记自动化提交，
   不伪造用户身份、不修改全局 Git 配置；公开发布前用户设置自己的作者信息。
9. 开源许可证候选 MIT；初始化不替用户认领版权或擅自确定最终许可，发布前确认。
   第三方依赖独立遵守各自许可，不将其源码或二进制纳入初始仓库。

## 2026-10-27 依赖执行决策（更新第 7 项）

- 已用 pacman 实际安装 UCRT64 Eigen 5.0.1-1，但它不接受 PCL 1.15.1 所需 Eigen3 3.3 的版本查询。
  因此系统包保留，项目实际固定官方 Eigen 3.4.0 独立安装，不修改第三方版本检查来假装兼容。
- 当前 UCRT64 同步库实际查询无 PCL 包；不把 PDAL、Python pipcl 误认成 PCL。
- 选择固定 PCL 1.15.1 源码与现有 GCC 16.2.0，复用同 ABI 的 pacman Boost/FLANN/VTK。
  vcpkg MinGW 同样需要源码编译且属于社区配置，新增第二套库管理没有当前收益；不切换 MSVC/WSL。
- PCL 的泛化 VTK 查询会带入未安装的 Qt/VR 可选后端，已用 tools/prepare_pcl_source.py 固定、可重放地限制查询范围，
  并遵守 WITH_QT=NO。这是第三方构建发现补丁，未改配准算法。
- 禁用 PCL 额外 SSE/AVX 探测，统一默认 x86_64 对齐；修改选项后清除该对齐探测缓存并重测，不能仅消音警告。
- 依赖检查升级为直接调用 PCL 滤波、恒等 ICP 及不渲染的 VTK 场景构建，实际验证 API/链接/DLL，
  这只是第三方 smoke check，不属于模块 A/B/C 的实现或算法验收。
- 保存源码 commit、pacman 版本/缓存哈希和可重复构建/验证脚本；二进制、原始源码和日志仍不进入 Git。
- 实际验收：所选 PCL 库完成构建安装，已有 build-pcl 和全新 build-pcl-clean 各 4/4 CTest 通过；
  只解除依赖阻塞，不标记 A/B/C 算法或真实渲染已完成。

## 2026-10-27 模块开发准备

- 三个 worktree 放在主目录之外的同级模块目录，复用 Git common-dir 所在主目录的依赖与 CMake，
  使用显式脚本参数，不复制/软链依赖，不写入全局 PATH。
- 主对话预先配置按源文件存在性启用的 cloud_processing、pose_utils、icp_registration、generate_test_data
  与 A/B 测试目标，解决模块不能改 CMake 却需要独立编译测试的问题；不提前创建任何算法实现。
- 接口 v1.1 明确 B 输入全部为有限点、evaluateAlignment 可接受少于 3 点；固定 C 生成器 CLI 和拒绝覆盖规则。
  函数签名和既定变换方向保持一致；A/B 可独立构造测试数据并行开发。
