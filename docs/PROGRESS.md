# 项目进度

更新时间：2026-10-27（Asia/Shanghai），初始化后依赖配置阶段；不启动模块 A/B/C。

## 已完成

- 实际检查空目录、OS、工具链、磁盘和内存；初始无 Git 仓库和用户作者配置。
- 已将需求、模块边界、统一接口、任务依赖与技术决策写入真实文件。
- I02：目录、CMake、共享点云类型和管理文档完成检查。
- I03：项目内 CMake/CTest 3.31.6 安装完成；Release C++17 编译成功，3/3 bootstrap 测试通过。
- I04：main 基础提交作为模块共同基线；三个 feature 分支指向该提交。提交 ID 由 Git 查询，不在提交内部自引用。
- pacman 在受控权限下正常工作；新增 Eigen 5.0.1-1、Boost 1.92.0-4、FLANN 1.9.2-2、VTK 9.6.2-8 等 45 个包。
- 安装前后包清单比较：已有包版本变化为 0，GCC 仍为 16.2.0-6。
- 实测系统 Eigen 5 的配置版本检查与 PCL 1.15.1 不兼容，已独立安装官方 Eigen 3.4.0。
- 精确 pacman -Si 查询确认没有 mingw-w64-ucrt-x86_64-pcl；已下载并锁定 PCL 1.15.1 源码。
- 写入可复现脚本、源码 commit 和 54 个依赖/关键工具链包的版本及归档 SHA256；包基线检查通过。
- D01：PCL 1.15.1 所选库已使用现有 GCC 完成 Release 构建与安装，项目实际使用 Eigen 3.4.0。
- tools/build_dependencies.ps1 实际运行通过；tools/verify_dependencies.ps1 配置/构建/运行通过，CTest 4/4。
- 全新 build-pcl-clean 目录再次配置、编译和运行，CTest 4/4，排除原失败配置缓存的影响。

## 进行中

- 本轮依赖配置已完成；A/B/C 尚未启动。没有创建模块 worktree 或远程仓库。

## 阻塞

- 当前没有阻塞模块数值开发的依赖问题。正式 GUI 渲染、算法精度与真实数据实验尚未验收。
- 原始沙箱内 MSYS 进程限制仍存在；依赖包安装使用受控权限，不重装环境。

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

## 下一步

将已验证依赖配置提交 main；三个尚未使用的 feature 分支从该依赖基线开始。
用户可以创建独立模块 worktree，再另行启动 A/B/C 对话；必须使用共享依赖位置和对应 CMake。
模块 worktree 没有 .local-deps/.local-tools 时，向脚本传 -DependencyRoot 和 -CMake，或设置相应环境路径。
初始提交 ID 以 `git log --reverse --format=%H` 为准，避免提交哈希自引用。
