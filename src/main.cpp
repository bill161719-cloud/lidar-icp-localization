#include <iostream>
#include <string_view>

#ifdef LIDAR_HAS_PIPELINE
#include "registration_pipeline.h"
#include "pose_utils.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <locale>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {
struct Options {
    std::string source, target, initial, truth, output;
    lidar::PipelineConfig config;
};

double number(const std::string& text) {
    try {
        std::size_t end = 0;
        const double value = std::stod(text, &end);
        if (end == text.size() && std::isfinite(value)) return value;
    } catch (const std::logic_error&) {}
    throw std::invalid_argument("Expected a finite number: " + text);
}

int positiveInteger(const std::string& text) {
    if (text.empty() || text.find_first_not_of("0123456789") != std::string::npos)
        throw std::invalid_argument("Expected a positive integer: " + text);
    const double value = number(text);
    if (value < 1 || value > std::numeric_limits<int>::max())
        throw std::invalid_argument("Integer outside positive int range");
    return static_cast<int>(value);
}

Options parseOptions(int argc, char* argv[]) {
    Options options;
    std::set<std::string> seen;
    for (int i = 1; i < argc; ++i) {
        const std::string key = argv[i];
        if (!seen.insert(key).second) throw std::invalid_argument("Duplicate option: " + key);
        if (i + 1 >= argc) throw std::invalid_argument("Missing value for " + key);
        const std::string value = argv[++i];
        if (key == "--source") options.source = value;
        else if (key == "--target") options.target = value;
        else if (key == "--initial") options.initial = value;
        else if (key == "--truth") options.truth = value;
        else if (key == "--output") options.output = value;
        else if (key == "--voxel-size") {
            const double size = number(value);
            if (size <= 0 || size > std::numeric_limits<float>::max() ||
                static_cast<float>(size) == 0) throw std::invalid_argument("Invalid voxel size");
            options.config.preprocessing.voxel_size_m = static_cast<float>(size);
        }
        else if (key == "--max-iterations") options.config.icp.max_iterations = positiveInteger(value);
        else if (key == "--max-correspondence-distance") options.config.icp.max_correspondence_distance_m = number(value);
        else if (key == "--evaluation-distance") options.config.icp.evaluation_distance_m = number(value);
        else if (key == "--min-inliers") options.config.quality.min_inliers = static_cast<std::size_t>(positiveInteger(value));
        else if (key == "--min-inlier-ratio") options.config.quality.min_inlier_ratio = number(value);
        else if (key == "--max-rmse") options.config.quality.max_rmse_m = number(value);
        else throw std::invalid_argument("Unknown option: " + key);
    }
    if (options.source.empty() || options.target.empty())
        throw std::invalid_argument("Both --source and --target are required");
    return options;
}

Eigen::Matrix4f readTransform(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("Cannot open transform: " + path);
    input.imbue(std::locale::classic());
    Eigen::Matrix4f matrix;
    for (int row = 0; row < 4; ++row)
        for (int col = 0; col < 4; ++col)
            if (!(input >> matrix(row, col)))
                throw std::invalid_argument("Transform requires 16 row-major numbers: " + path);
    input >> std::ws;
    if (!input.eof() || !lidar::isValidTransform(matrix))
        throw std::invalid_argument("Transform requires exactly one valid SE(3): " + path);
    return matrix;
}

void jsonString(std::ostream& out, const std::string& value) {
    out << '"';
    for (unsigned char ch : value) {
        if (ch == '"' || ch == '\\') out << '\\' << static_cast<char>(ch);
        else if (ch < 0x20) out << "\\u00" << std::hex << std::setw(2) << std::setfill('0')
                               << static_cast<int>(ch) << std::dec << std::setfill(' ');
        else out << static_cast<char>(ch);
    }
    out << '"';
}
void jsonNumber(std::ostream& out, double value) {
    if (std::isfinite(value)) out << value; else out << "null";
}
template <class Matrix>
void jsonMatrix(std::ostream& out, const Matrix& matrix) {
    out << '[';
    for (Eigen::Index row = 0; row < matrix.rows(); ++row) {
        if (row) out << ',';
        out << '[';
        for (Eigen::Index col = 0; col < matrix.cols(); ++col) {
            if (col) out << ',';
            jsonNumber(out, matrix(row, col));
        }
        out << ']';
    }
    out << ']';
}
void pointCounts(std::ostream& out, const lidar::PreprocessResult& points) {
    out << "{\"input\":" << points.input_points << ",\"finite\":" << points.finite_points
        << ",\"output\":" << points.output_points << '}';
}

std::string report(const Options& options, const lidar::PipelineResult& result,
                   const Eigen::Matrix4f& initial, const Eigen::Matrix4f& truth) {
    std::ostringstream out;
    out.imbue(std::locale::classic());
    out << std::setprecision(10) << std::boolalpha;
    const auto& r = result.registration;
    const auto& c = options.config;
    out << "{\n\"schema_version\":1,\n\"source\":"; jsonString(out, options.source);
    out << ",\n\"target\":"; jsonString(out, options.target);
    out << ",\n\"transform_direction\":\"p_target = T_target_source * p_source\","
           "\n\"units\":{\"length\":\"m\",\"angle\":\"rad\",\"fitness\":\"m^2\"},"
           "\n\"configuration\":{\"voxel_size_m\":" << c.preprocessing.voxel_size_m
        << ",\"max_iterations\":" << c.icp.max_iterations
        << ",\"max_correspondence_distance_m\":" << c.icp.max_correspondence_distance_m
        << ",\"evaluation_distance_m\":" << c.icp.evaluation_distance_m
        << ",\"transformation_epsilon\":" << c.icp.transformation_epsilon
        << ",\"euclidean_fitness_epsilon\":" << c.icp.euclidean_fitness_epsilon
        << ",\"min_inliers\":" << c.quality.min_inliers
        << ",\"min_inlier_ratio\":" << c.quality.min_inlier_ratio
        << ",\"max_rmse_m\":" << c.quality.max_rmse_m << "},\n\"source_points\":";
    pointCounts(out, result.source);
    out << ",\n\"target_points\":"; pointCounts(out, result.target);
    out << ",\n\"initial_T_target_source\":"; jsonMatrix(out, initial);
    out << ",\n\"converged\":" << r.converged << ",\n\"accepted\":" << result.quality.accepted
        << ",\n\"rejection_reason\":"; jsonString(out, result.quality.reason);
    out << ",\n\"fitness_m2\":"; jsonNumber(out, r.fitness_m2);
    out << ",\n\"rmse_m\":"; jsonNumber(out, r.matches.rmse_m);
    out << ",\n\"inliers\":" << r.matches.inliers << ",\n\"inlier_ratio\":" << r.matches.inlier_ratio
        << ",\n\"elapsed_ms\":"; jsonNumber(out, r.elapsed_ms);
    out << ",\n\"diagnostic_T_target_source\":"; jsonMatrix(out, r.T_target_source);
    out << ",\n\"T_target_source\":";
    if (result.quality.accepted) jsonMatrix(out, r.T_target_source); else out << "null";
    out << ",\n\"pose\":";
    if (result.quality.accepted) {
        const auto pose = lidar::decomposeTransform(r.T_target_source);
        out << "{\"rotation\":"; jsonMatrix(out, pose.rotation);
        out << ",\"translation_m\":[" << pose.translation_m.x() << ',' << pose.translation_m.y()
            << ',' << pose.translation_m.z() << "],\"quaternion_wxyz\":[" << pose.quaternion.w()
            << ',' << pose.quaternion.x() << ',' << pose.quaternion.y() << ',' << pose.quaternion.z() << "]}";
    } else out << "null";
    const bool evaluate = result.quality.accepted && !options.truth.empty();
    out << ",\n\"translation_error_m\":";
    if (evaluate) jsonNumber(out, lidar::translationErrorM(r.T_target_source, truth)); else out << "null";
    out << ",\n\"rotation_error_rad\":";
    if (evaluate) jsonNumber(out, lidar::rotationErrorRad(r.T_target_source, truth)); else out << "null";
    out << "\n}\n";
    return out.str();
}

int run(int argc, char* argv[]) {
    const auto options = parseOptions(argc, argv);
    const Eigen::Matrix4f initial = options.initial.empty() ? Eigen::Matrix4f::Identity() : readTransform(options.initial);
    const Eigen::Matrix4f truth = options.truth.empty() ? Eigen::Matrix4f::Identity() : readTransform(options.truth);
    if (!options.output.empty() && std::filesystem::exists(options.output))
        throw std::runtime_error("Refusing to overwrite report: " + options.output);
    const auto result = lidar::runRegistration(options.source, options.target, options.config, initial);
    const auto json = report(options, result, initial, truth);
    if (!options.output.empty()) {
        std::ofstream output(options.output, std::ios::binary);
        output << json;
        output.close();
        if (!output) throw std::runtime_error("Cannot write report: " + options.output);
    }
    std::cout << json;
    return result.quality.accepted ? 0 : 4;
}
}  // namespace
#endif

static_assert(__cplusplus >= 201703L, "C++17 or later is required");
int main(int argc, char* argv[]) {
    if (argc == 1 || (argc == 2 && std::string_view(argv[1]) == "--help")) {
        std::cout << "LiDAR registration (source to target, metres)\n"
                     "Usage: lidar_icp --source <pcd> --target <pcd> [options]\n"
                     "  --initial <matrix.txt> --truth <matrix.txt> --output <report.json>\n"
                     "  --voxel-size <m> --max-iterations <int> --max-correspondence-distance <m>\n"
                     "  --evaluation-distance <m> --min-inliers <int> --min-inlier-ratio <0..1> --max-rmse <m>\n"
                     "T_target_source maps source coordinates into target coordinates.\n";
#ifndef LIDAR_HAS_PIPELINE
        std::cout << "Registration requires LIDAR_ENABLE_PCL=ON and both modules.\n";
#endif
        return 0;
    }
    if (argc == 2 && std::string_view(argv[1]) == "--version") {
        std::cout << "lidar-icp-localization 0.1.0\n";
        return 0;
    }
#ifdef LIDAR_HAS_PIPELINE
    try { return run(argc, argv); }
    catch (const std::invalid_argument& error) {
        std::cerr << "Invalid input: " << error.what() << '\n'; return 2;
    }
    catch (const std::exception& error) {
        std::cerr << "Runtime error: " << error.what() << '\n'; return 3;
    }
#else
    std::cerr << "Registration unavailable in this build. Use --help.\n";
    return argc == 2 ? 2 : 3;
#endif
}
