#include <iostream>
#include <optional>
#include <string_view>

static_assert(__cplusplus >= 201703L, "C++17 or later is required");

int main(int argc, char* argv[]) {
    const std::optional<std::string_view> argument =
        argc == 2 ? std::optional<std::string_view>{argv[1]} : std::nullopt;
    if (argc == 1 || (argument && *argument == "--help")) {
        std::cout << "LiDAR ICP localization bootstrap\n"
                     "Usage: lidar_icp [--help|--version]\n"
                     "Convention: T_target_source maps source to target (metres).\n"
                     "Registration modules are not implemented yet.\n";
        return 0;
    }
    if (argument && *argument == "--version") {
        std::cout << "lidar-icp-localization 0.1.0 (bootstrap)\n";
        return 0;
    }
    std::cerr << "Unsupported arguments. Run with --help.\n";
    return 2;
}
