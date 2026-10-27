# 项目进度

## 第一轮 A/B 集成（进行中）

- main 集成前为 4cfce35，工作区干净；已核实 A=24fc233、B=3236706 的所有改动均在约定所有权内。
- A 已审查并合入工作区，使用固定依赖在 build-integration-a 全新目录完成 Release 配置/编译，CTest 5/5。
  test_cloud_processor 的 6 组检查全部通过（读取编码、无效输入、有限点、体素与统计），原始日志 build/integration-a.log。
- A01 由主对话验收为 DONE；A 合并提交为 cae8e11。
- B 已审查并合入工作区，build-integration-ab 全新 Release 构建和完整 CTest 7/7 通过，日志 build/integration-ab.log。
  B01/B02 的 API、真值/初值、逆变换、非法输入、失败及独立误差指标验收通过，标记 DONE。
- M01 仍为 IN_PROGRESS：原模块 API 通过不代表完整应用通过；主程序、质量门禁和端到端测试正在集成。
- GCC 的 mismatched-new-delete 诊断实际来自 Eigen aligned_allocator/PCL make_shared/std shared_ptr 的内联路径；
  未屏蔽警告、未改依赖；需结合对齐配置和分配/释放路径继续记录分析，不因测试通过而宣称内存安全已穷尽验证。
- 下一步补主程序数据链路和端到端质量门禁，拒绝未收敛及零/低内点率结果作为有效位姿。

下方保留初始化、依赖和 worktree 准备阶段记录；其“尚未启动模块”描述仅代表当时状态。

更新时间：2026-10-27（Asia/Shanghai），模块 Worktree 准备阶段；不实现模块算法。

## 已完成

- 实际检查空目录、OS、工具链、磁盘和内存；初始无 Git 仓库和用户作者配置。
- 已将需求、模块边界、统一接口、任务依赖与技术决策写入真实文件。
- I02：目录、CMake、共享点云类型和管理文档完成检查。
- I03：项目内 CMake/CTest 3.31.6 安装完成；Release C++17 编译成功，3/3 bootstrap 测试通过。
- I04：main 初始提交作为共同历史基线；feature 分支后续已快进至依赖及准备提交。提交 ID 由 Git 查询，不在提交内部自引用。
- pacman 在受控权限下正常工作；新增 Eigen 5.0.1-1、Boost 1.92.0-4、FLANN 1.9.2-2、VTK 9.6.2-8 等 45 个包。
- 安装前后包清单比较：已有包版本变化为 0，GCC 仍为 16.2.0-6。
- 实测系统 Eigen 5 的配置版本检查与 PCL 1.15.1 不兼容，已独立安装官方 Eigen 3.4.0。
- 精确 pacman -Si 查询确认没有 mingw-w64-ucrt-x86_64-pcl；已下载并锁定 PCL 1.15.1 源码。
- 写入可复现脚本、源码 commit 和 54 个依赖/关键工具链包的版本及归档 SHA256；包基线检查通过。
- D01：PCL 1.15.1 所选库已使用现有 GCC 完成 Release 构建与安装，项目实际使用 Eigen 3.4.0。
- tools/build_dependencies.ps1 实际运行通过；tools/verify_dependencies.ps1 配置/构建/运行通过，CTest 4/4。
- 全新 build-pcl-clean 目录再次配置、编译和运行，CTest 4/4，排除原失败配置缓存的影响。
- W01：接口 v1.1 和模块库/测试构建入口在准备提交 70b448a 中完成；已同步全部模块分支。
- W02：三个外部同级 worktree 已建立，各自配置、编译、CTest 4/4 及直接运行依赖检查全部通过。

## Worktree 准备结果

| 模块 | 实际目录 | 分支 | 实际验证提交 | 配置/编译/CTest |
|---|---|---|---|---|
| A | D:/CodexProgects/lidar-icp-module-a | feature/cloud-processing | 70b448a（继承 015a535） | 成功 / 成功 / 4/4 |
| B | D:/CodexProgects/lidar-icp-module-b | feature/icp-registration | 70b448a（继承 015a535） | 成功 / 成功 / 4/4 |
| C | D:/CodexProgects/lidar-icp-module-c | feature/experiments | 70b448a（继承 015a535） | 成功 / 成功 / 4/4 |

验证后同步的提交仅更新进度/任务/启动文档；最终 HEAD 由 git worktree list 和各树 git log 查询。
所有依赖检查输出 PCL 1.15.1、Eigen 3.4.0；各树 .local-deps 和 .local-tools 均不存在。
实际 CMakeCache 确认 CMAKE_HOME_DIRECTORY 指向自身 worktree，PCL_DIR/Eigen3_DIR 指向主目录共享依赖。
未重新下载或源码构建 PCL；使用同一 GCC，每树独占 build-pcl/。为控制内存，验证顺序执行、每轮 Jobs=1。
实际命令为各树 tools/verify_dependencies.ps1 加主目录的 -DependencyRoot 和 -CMake，详见 WORKTREES.md。
主目录日志：build/lidar-icp-module-a-verify.log、build/lidar-icp-module-b-verify.log、build/lidar-icp-module-c-verify.log。

## 进行中

- 准备阶段已完成，无模块算法开发正在执行。A01/B01/B02/C01 等仍为 TODO。
- 未创建远程仓库或推送；没有启动任何模块子对话。

## 阻塞

- 当前没有阻塞模块数值开发的依赖问题。正式 GUI 渲染、算法精度与真实数据实验尚未验收。
- 原始沙箱内 MSYS 进程限制仍存在；依赖包安装使用受控权限，不重装环境。
- 同级 worktree 在本轮主对话可写根之外，创建、编译和 Git 核查使用受控权限成功执行；
  新模块对话必须打开自己的 worktree 文件夹以获得正确工作区，不在主目录代写模块文件。

## 最近验证

- g++ --version：GCC 16.2.0；g++ -dumpmachine：x86_64-w64-mingw32。
- git --version：2.55.0.windows.5。
- CMake 3.31.6，GNU Make 4.4.1，Release，-std=c++17 -Wall -Wextra -Wpedantic：构建退出 0，无编译警告。
- CTest：bootstrap_help、bootstrap_version、bootstrap_rejects_unknown，3/3 通过，退出 0。
- 初始 PCL ON 缺 Eigen 的失败记录保留于 INITIALIZATION.md；本次系统 Eigen 5 配置失败日志为 build-pcl/eigen5-configure.log。
- PCL 源码使用 Eigen 3.4.0，必要 VTK 模块配置成功；额外 SIMD 关闭后重测内存对齐，警告已消除。
- 当前 PCL 源码仍有第三方 Windows 宏重复、整数比较、OpenMP/VTK 弃用警告，不能称为零警告。
- 最终 PCL ON 构建、dependency_check 和 CTest 均通过；已有目录及全新目录各 4/4 测试通过。
- 依赖程序输出：PCL 1.15.1; Eigen 3.4.0; filter/ICP/VTK scene OK (no render)。
- 关键日志和保留的第三方诊断详见 ENVIRONMENT.md；包括 GCC 优化警告以及 Eigen 可选修订号探测的沙箱限制，不将其隐去。
- 本轮更新 CMake 后 main CTest 4/4；A/B/C 三个新 worktree 分别 4/4，全部命令成功退出。
- 这些是 bootstrap/依赖测试，尚未生成或执行模块算法测试，不把环境准备当作算法验收。

## 下一步

用户可以正式在各自目录启动模块 A 和模块 B（B 先 B01 后 B02）；A/B 可并行，不依赖对方未完成的实现。
C 可开始 C01/C02；C03 完整实验仍需等待集成及合法数据准备。
子对话先读 AGENTS、INTERFACES、TASKS、PROGRESS 和 WORKTREES，核对当前分支与干净状态。
模块 worktree 没有 .local-deps/.local-tools 时，向脚本传 -DependencyRoot 和 -CMake，或设置相应环境路径。
初始提交 ID 以 `git log --reverse --format=%H` 为准，避免提交哈希自引用。
