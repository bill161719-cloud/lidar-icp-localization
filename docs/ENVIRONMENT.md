# 本地环境与依赖方案

检查日期：2026-10-27（Asia/Shanghai）。本机绝对路径只存在本地配置/日志，不写入公共构建配置。

| 项目 | 实际检查结果 |
|---|---|
| OS | Windows build 26200.9711，25H2，64 位；版本号对应 Windows 11，旧注册表 ProductName 仍写 Windows 10 Home China |
| 编译器 | MSYS2 UCRT64 GCC 16.2.0（Rev6），target x86_64-w64-mingw32 |
| C++17 | 已以 -std=c++17 编译 static_assert、std::optional、std::string_view，通过 |
| Git | 2.55.0.windows.5；未配置 user.name / user.email |
| Make | mingw32-make 已存在，包记录 4.4.1-5 |
| CMake / CTest | 初始未发现；已安装项目内 3.31.6，配置/编译/3 项 CTest 通过 |
| PCL | 在 PATH、UCRT64 头文件和本地包记录中未发现；无可报告版本 |
| Eigen | 在 UCRT64 头文件和本地包记录中未发现；无可报告版本 |
| MSVC | cl/vswhere 未发现；存在旧 Visual Studio 目录不等于可用 C++ 工具链 |
| 依赖管理 | MSYS2 pacman 已安装；Python 3.11/pip 26.0.1 可用；winget 可执行文件存在但未验证服务；vcpkg/conda 未发现 |
| 物理内存 | 16,890,716,160 字节（15.73 GiB），检查时可用约 3.84 GiB，属动态值 |
| 磁盘 | 检查时 C 盘约 79.31 GiB 可用，D 盘约 486.63 GiB 可用 |

Get-CimInstance 被环境拒绝，使用 RuntimeInformation/注册表和 GlobalMemoryStatusEx 交叉读取。
没有修改全局 PATH、未升级 GCC 或 MSYS2、未安装完整 PCL。

## 先安装最小构建工具

在项目根目录 PowerShell 执行（需要网络；本地目录已被 Git 忽略）：

```powershell
python -m pip install --disable-pip-version-check --no-warn-script-location --target .local-tools/python cmake==3.31.6
$env:Path = "$((Resolve-Path .local-tools/python/cmake/data/bin).Path);$env:Path"
cmake --version
```

此 wheel 的 CMake 是构建工具，不是用来链接的 MSVC C++ 库，可用 MinGW Makefiles 生成器调用已有 GCC。

## PCL/Eigen：保留现有 GCC 的方案

1. 在可正常运行的 MSYS2 UCRT64 终端只读查询 pacman 包状态与可用版本。
2. 确认稳定 PCL 与 Eigen/Boost/FLANN/VTK 的兼容组合。优先 Eigen 3.4.x；
   官方 MSYS2 eigen3 页面当前是 5.x，不能直接当作已验证版本。
3. 若没有匹配 GCC/UCRT64 的 PCL 预编译包，使用同一 GCC 从源码构建 PCL 及必要依赖，
   固定版本/来源/校验值，安装到项目 .local-deps/，以 CMAKE_PREFIX_PATH 指定，避免系统污染。
4. 先验证 common/io/filters/registration，再验证 visualization 及 VTK DLL；整个功能验收仍必须含可视化。
5. 记录实际安装版本后运行 README 的 PCL ON 配置、构建及 dependency_check。

完整依赖构建可能耗时且需要更多内存；初始化先停在可验证的 bootstrap，不把未执行方案写成成功。
替代方案是用户确认后安装 MSVC Build Tools，与匹配的 PCL/vcpkg x64-windows 库一起使用；
必须新建 build 目录，禁止与现有 GCC 产物混合。这条路线本次没有执行。

依据：[MSYS2 环境](https://www.msys2.org/docs/environments/)、
[MSYS2 Eigen 包](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-eigen3)、
[PCL Windows 源码构建及编译器兼容要求](https://pointclouds.org/documentation/tutorials/compiling_pcl_windows.html)。
