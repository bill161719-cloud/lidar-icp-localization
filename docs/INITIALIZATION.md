# 初始化验证记录

日期：2026-10-27（Asia/Shanghai）；范围仅基础工程，未执行 A/B/C 算法。
工具链：Windows x64、MSYS2 UCRT64 GCC 16.2.0、CMake/CTest 3.31.6、GNU Make 4.4.1、Git 2.55.0。

以下命令在仓库根目录实际执行。CMake 安装没有更改系统 PATH；命令使用本地可执行文件。

```powershell
python -m pip install --disable-pip-version-check --no-warn-script-location --target .local-tools/python cmake==3.31.6
& .\.local-tools\python\cmake\data\bin\cmake.exe -S . -B build -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
& .\.local-tools\python\cmake\data\bin\cmake.exe --build build --parallel 2
& .\.local-tools\python\cmake\data\bin\ctest.exe --test-dir build --output-on-failure
& .\build\lidar_icp.exe --help
& .\build\lidar_icp.exe --version
& .\.local-tools\python\cmake\data\bin\cmake.exe -S . -B build-pcl -G 'MinGW Makefiles' -DLIDAR_ENABLE_PCL=ON -DCMAKE_BUILD_TYPE=Release
```

| 验证 | 实际结果 |
|---|---|
| 初始 pip 下载 | 沙箱网络拒绝，失败；受控网络重试成功安装 3.31.6 |
| 默认 CMake 配置 | 退出 0；GNU 16.2.0，生成 MinGW Makefiles |
| Release 编译 | 退出 0；成功生成 lidar_icp；无编译警告 |
| C++17 | 编译参数 -std=c++17；static_assert 与标准库特性成功编译 |
| bootstrap_help | 通过，输出方向说明 |
| bootstrap_version | 通过，输出 0.1.0 (bootstrap) |
| bootstrap_rejects_unknown | 通过，未知参数返回非零 |
| CTest 汇总 | 3/3 通过，0 失败，退出 0 |
| --help / --version 手动运行 | 退出 0，输出符合当前骨架功能 |
| PCL ON 配置 | 退出 1，找不到 Eigen3Config.cmake；符合缺失依赖时显式失败的设计 |
| PCL dependency_check | 未编译、未运行；等待 D01 |
| 点云实验/截图 | 未执行；无算法精度或运行耗时结果 |

原始本地日志：build/configure.log、build/compile.log、build/ctest.log、
build/Testing/Temporary/LastTest.log、build-pcl/configure.log；因含本机路径且为构建产物，不提交 Git。
以上结果表随源码提交保留可审查记录；完整功能阶段需要重新跑依赖检查和模块测试。

基础提交作者标为 Codex <codex@localhost>，只用单次 Git 参数，不改用户全局身份。
主分支 main；feature/cloud-processing、feature/icp-registration、feature/experiments 均从基础提交创建。
哈希由 `git log --reverse --format=%H` 和 `git branch -v` 查询；不在同一提交内写入自身哈希。

没有创建公开远程仓库、推送、完整依赖安装、工具链更换、模块实现或数据下载。
