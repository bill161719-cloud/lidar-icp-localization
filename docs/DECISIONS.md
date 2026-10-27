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
