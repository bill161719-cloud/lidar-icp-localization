#include <Eigen/Geometry>
#include <charconv>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
void writeCloud(const fs::path& path, const std::vector<Eigen::Vector3d>& points) {
    std::ofstream out(path);
    out.exceptions(std::ios::badbit | std::ios::failbit);
    out << "VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH "
        << points.size() << "\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS "
        << points.size() << "\nDATA ascii\n" << std::setprecision(10);
    for (const auto& p : points) out << p.x() << ' ' << p.y() << ' ' << p.z() << '\n';
}
int main(int argc, char** argv) {
    try {
        fs::path output;
        std::uint32_t seed = 0;
        bool hasSeed = false;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            if (arg == "--help") {
                std::cout << "generate_test_data --output <dir> --seed <uint32>\n";
                return 0;
            }
            if (i + 1 >= argc) throw std::invalid_argument("Missing option value");
            const std::string value = argv[++i];
            if (arg == "--output" && output.empty()) output = value;
            else if (arg == "--seed" && !hasSeed) {
                const auto parsed = std::from_chars(value.data(), value.data()+value.size(), seed);
                if (parsed.ec != std::errc{} || parsed.ptr != value.data()+value.size())
                    throw std::invalid_argument("seed must be decimal uint32");
                hasSeed = true;
            } else throw std::invalid_argument("Unknown or duplicate option: " + arg);
        }
        if (output.empty() || !hasSeed) throw std::invalid_argument("Require --output and --seed");
        for (const auto* name : {"source.pcd", "target.pcd", "truth.txt", "metadata.json"})
            if (fs::exists(output/name)) throw std::invalid_argument("Refuse to overwrite output");
        fs::create_directories(output);
        std::mt19937 rng(seed);
        auto uniform = [&]() { return static_cast<double>(rng()) / 4294967296.0; };
        std::vector<Eigen::Vector3d> source, target;
        // Unequal orthogonal planes and a raised curved structure break symmetry.
        for (int i = 0; i < 2400; ++i) {
            const double u = uniform(), v = uniform();
            if (i < 1000) source.emplace_back(8*u, 5*v, 0.05*std::sin(8*u));
            else if (i < 1700) source.emplace_back(8*u, 0, 3*v);
            else if (i < 2200) source.emplace_back(0, 5*u, 2*v);
            else source.emplace_back(2+u, 2+v, 1+u*u+0.2*v);
        }
        const Eigen::Matrix3d rotation = (Eigen::AngleAxisd(0.12, Eigen::Vector3d::UnitZ()) *
            Eigen::AngleAxisd(-0.035, Eigen::Vector3d::UnitY()) *
            Eigen::AngleAxisd(0.02, Eigen::Vector3d::UnitX())).toRotationMatrix();
        const Eigen::Vector3d translation(0.3, -0.15, 0.08);
        for (const auto& p : source) target.push_back(rotation*p+translation);
        writeCloud(output/"source.pcd", source);
        writeCloud(output/"target.pcd", target);
        Eigen::Matrix4d truth = Eigen::Matrix4d::Identity();
        truth.block<3,3>(0,0)=rotation; truth.block<3,1>(0,3)=translation;
        std::ofstream matrix(output/"truth.txt");
        matrix.exceptions(std::ios::badbit | std::ios::failbit);
        matrix << std::setprecision(17) << truth << '\n';
        std::ofstream meta(output/"metadata.json");
        meta.exceptions(std::ios::badbit | std::ios::failbit);
        meta << "{\n  \"seed\": " << seed << ",\n  \"points\": 2400,\n"
             << "  \"geometry\": \"unequal planes and raised curved patch\",\n"
             << "  \"rotation_order\": \"Rz(0.12)*Ry(-0.035)*Rx(0.02)\",\n"
             << "  \"translation_m\": [0.3,-0.15,0.08],\n"
             << "  \"units\": \"metres and radians\",\n"
             << "  \"direction\": \"target=T_target_source*source\",\n"
             << "  \"generator\": \"mt19937, uint32/2^32\",\n"
             << "  \"license\": \"MIT; Copyright (c) 2026 Wang Chenqi; project-generated synthetic data\"\n}\n";
        std::cout << "Generated 2400 source/target points\n";
    } catch (const std::invalid_argument& e) {
        std::cerr << e.what() << '\n'; return 2;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n'; return 3;
    }
}
