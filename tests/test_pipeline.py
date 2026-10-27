"""Execute the real C++ CLI using PCD files; retain inputs, commands and reports."""

import argparse
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser()
parser.add_argument("--exe", type=Path, required=True)
parser.add_argument("--workdir", type=Path, required=True)
options, unittest_args = parser.parse_known_args()


def transform(angle, translation):
    c, s = math.cos(angle), math.sin(angle)
    return [[c, -s, 0, translation[0]], [s, c, 0, translation[1]],
            [0, 0, 1, translation[2]], [0, 0, 0, 1]]


def inverse(matrix):
    rotation = [[matrix[j][i] for j in range(3)] for i in range(3)]
    return [row + [-sum(row[k] * matrix[k][3] for k in range(3))]
            for row in rotation] + [[0, 0, 0, 1]]


def moved(points, matrix):
    return [tuple(sum(matrix[i][k] * p[k] for k in range(3)) + matrix[i][3]
                  for i in range(3)) for p in points]


def write_pcd(path, points):
    header = ("VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n"
              f"WIDTH {len(points)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n"
              f"POINTS {len(points)}\nDATA ascii\n")
    path.write_text(header + "".join(" ".join(f"{x:.9g}" for x in p) + "\n"
                                    for p in points), encoding="ascii")


def write_matrix(path, matrix):
    path.write_text("\n".join(" ".join(f"{x:.10g}" for x in row)
                              for row in matrix) + "\n", encoding="ascii")


class PipelineCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options.workdir.mkdir(parents=True, exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix="run-", dir=options.workdir)).resolve()
        rng = random.Random(20261027)
        cls.points = []
        for _ in range(400):
            x, y, z = [rng.uniform(-1, 1) for _ in range(3)]
            cls.points.append((2.5*x + 0.2*y*y, 1.3*y, 0.8*z + 0.1*x))
        cls.truth = transform(0.18, (0.3, -0.15, 0.08))
        cls.initial = transform(0.16, (0.28, -0.14, 0.07))
        cls.target_points = moved(cls.points, cls.truth)
        cls.source = cls.root / "source cloud.pcd"
        cls.target = cls.root / "target cloud.pcd"
        write_pcd(cls.source, cls.points * 2 + [(math.nan, 0, 0), (0, math.inf, 0)])
        write_pcd(cls.target, cls.target_points * 2)
        write_matrix(cls.root / "initial.txt", cls.initial)
        write_matrix(cls.root / "truth.txt", cls.truth)
        write_matrix(cls.root / "inverse.txt", inverse(cls.truth))
        cls.counter = 0
        print(f"Pipeline test artifacts: {cls.root}", flush=True)

    def invoke(self, arguments, expected):
        type(self).counter += 1
        prefix = self.root / f"{type(self).counter:02d}-{self._testMethodName}"
        command = [str(options.exe.resolve()), *map(str, arguments)]
        result = subprocess.run(command, capture_output=True, timeout=30)
        prefix.with_suffix(".command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
        prefix.with_suffix(".stdout.json").write_bytes(result.stdout)
        prefix.with_suffix(".stderr.log").write_bytes(result.stderr)
        prefix.with_suffix(".exit-code.txt").write_text(str(result.returncode), encoding="ascii")
        self.assertEqual(result.returncode, expected,
                         result.stderr.decode("utf-8", errors="replace"))
        return json.loads(result.stdout) if result.stdout.strip() else None

    def arguments(self, source=None, target=None):
        return ["--source", source or self.source, "--target", target or self.target,
                "--voxel-size", "0.005", "--initial", self.root / "initial.txt",
                "--max-correspondence-distance", "0.5", "--evaluation-distance", "0.03",
                "--max-rmse", "0.01"]

    def assert_rejected(self, report):
        self.assertFalse(report["accepted"])
        self.assertIsNone(report["pose"])
        self.assertIsNone(report["T_target_source"])
        self.assertIsNone(report["translation_error_m"])
        self.assertIsNotNone(report["diagnostic_T_target_source"])
        self.assertTrue(report["rejection_reason"])

    def test_clean_chain_and_pose(self):
        output = self.root / "accepted.json"
        report = self.invoke(self.arguments() + ["--truth", self.root / "truth.txt",
                                                "--output", output], 0)
        self.assertEqual(report, json.loads(output.read_text()))
        self.assertTrue(report["converged"] and report["accepted"])
        self.assertEqual(report["source_points"], {"input": 802, "finite": 800, "output": 400})
        self.assertEqual(report["target_points"], {"input": 800, "finite": 800, "output": 400})
        self.assertLess(report["translation_error_m"], 0.01)
        self.assertLess(report["rotation_error_rad"], math.radians(0.1))
        self.assertEqual(report["inlier_ratio"], 1)
        self.assertLess(report["rmse_m"], 0.001)
        estimated = report["T_target_source"]
        self.assertLess(max(abs(estimated[i][j] - self.truth[i][j])
                            for i in range(4) for j in range(4)), 0.001)
        for i in range(3):
            self.assertAlmostEqual(report["pose"]["translation_m"][i], estimated[i][3], places=7)
            for j in range(3):
                self.assertAlmostEqual(report["pose"]["rotation"][i][j], estimated[i][j], places=7)
        quaternion = report["pose"]["quaternion_wxyz"]
        self.assertAlmostEqual(sum(x*x for x in quaternion), 1, places=6)
        self.assertAlmostEqual(abs(quaternion[0]), math.cos(0.09), places=5)
        self.assertAlmostEqual(abs(quaternion[3]), math.sin(0.09), places=5)
        print("clean_chain:", {k: report[k] for k in
              ("translation_error_m", "rotation_error_rad", "fitness_m2", "rmse_m", "inlier_ratio")}, flush=True)

    def test_swapped_frames_estimate_inverse(self):
        args = ["--source", self.target, "--target", self.source, "--voxel-size", "0.005",
                "--initial", self.root / "inverse.txt", "--truth", self.root / "inverse.txt"]
        report = self.invoke(args, 0)
        self.assertLess(report["translation_error_m"], 0.01)
        self.assertLess(report["rotation_error_rad"], math.radians(0.1))
        expected = inverse(self.truth)
        self.assertLess(max(abs(report["T_target_source"][i][j] - expected[i][j])
                            for i in range(4) for j in range(4)), 0.001)

    def test_nonconvergence_no_correspondences(self):
        far = self.root / "far.pcd"
        write_pcd(far, [(x+100, y+20, z) for x, y, z in self.points])
        report = self.invoke(["--source", self.source, "--target", far,
                              "--voxel-size", "0.005", "--max-correspondence-distance", "0.001",
                              "--evaluation-distance", "0.001"], 4)
        self.assert_rejected(report)
        self.assertFalse(report["converged"])
        self.assertEqual(report["inliers"], 0)
        self.assertIsNone(report["rmse_m"])
        self.assertEqual(report["rejection_reason"], "icp_not_converged")

    def test_converged_with_zero_inliers_rejected(self):
        report = self.invoke(["--source", self.source, "--target", self.target,
                              "--voxel-size", "0.005", "--max-iterations", "1",
                              "--evaluation-distance", "1e-7"], 4)
        self.assert_rejected(report)
        self.assertTrue(report["converged"])
        self.assertEqual(report["inliers"], 0)
        self.assertEqual(report["rejection_reason"], "insufficient_inliers")

    def test_partial_overlap_low_ratio_rejected(self):
        partial = self.root / "partial.pcd"
        write_pcd(partial, self.target_points[:80])
        report = self.invoke(["--source", self.source, "--target", partial, "--voxel-size", "0.005",
                              "--initial", self.root / "truth.txt", "--max-correspondence-distance", "0.001",
                              "--evaluation-distance", "0.001"], 4)
        self.assert_rejected(report)
        self.assertTrue(report["converged"])
        self.assertGreater(report["inliers"], 3)
        self.assertLess(report["inlier_ratio"], 0.5)
        self.assertEqual(report["rejection_reason"], "low_inlier_ratio")

    def test_high_rmse_rejected(self):
        noisy = self.root / "offset-noise.pcd"
        rng = random.Random(11)
        write_pcd(noisy, [tuple(x+rng.gauss(0, 0.003) for x in p) for p in self.target_points])
        args = self.arguments(target=noisy)
        args[args.index("--max-rmse")+1] = "0.00001"
        report = self.invoke(args, 4)
        self.assert_rejected(report)
        self.assertTrue(report["converged"])
        self.assertGreater(report["inlier_ratio"], 0.9)
        self.assertEqual(report["rejection_reason"], "invalid_or_high_rmse")

    def test_controlled_noise_and_source_outliers(self):
        rng = random.Random(29)
        source, target = self.root / "outliers.pcd", self.root / "noise.pcd"
        write_pcd(source, self.points + [(20+i, 30+i, 40+i) for i in range(20)])
        write_pcd(target, [tuple(x+rng.gauss(0, 0.002) for x in p) for p in self.target_points])
        args = self.arguments(source, target)
        args[args.index("--voxel-size")+1] = "0.05"
        report = self.invoke(args + ["--truth", self.root / "truth.txt"], 0)
        self.assertTrue(report["accepted"])
        self.assertGreater(report["inlier_ratio"], 0.9)
        self.assertLess(report["inlier_ratio"], 1)
        self.assertLess(report["translation_error_m"], 0.01)
        self.assertLess(report["rotation_error_rad"], math.radians(0.1))
        self.assertLess(report["rmse_m"], 0.01)
        print("controlled_noise_outliers:", {k: report[k] for k in
              ("translation_error_m", "rotation_error_rad", "rmse_m", "inlier_ratio")}, flush=True)

    def test_invalid_inputs_and_configuration(self):
        for extra in (["--voxel-size", "0"], ["--min-inlier-ratio", "1.1"],
                      ["--min-inliers", "2"], ["--max-rmse", "nan"],
                      ["--max-iterations", "1.5"], ["--evaluation-distance", "-1"]):
            with self.subTest(extra=extra):
                self.assertIsNone(self.invoke(["--source", self.source, "--target", self.target] + extra, 2))
        self.assertIsNone(self.invoke(["--source", self.source], 2))
        invalid = self.root / "bad-matrix.txt"
        for content in ("1 2 3", "1 0 0 0\n0 1 0 0\n0 0 1 0\n1 0 0 1",
                        "1 0 0 0\n0 1 0 0\n0 0 1 0\n0 0 0 1 extra"):
            invalid.write_text(content)
            self.assertIsNone(self.invoke(["--source", self.source, "--target", self.target,
                                          "--initial", invalid], 2))
        singleton = self.root / "single.pcd"
        write_pcd(singleton, [(0, 0, 0)])
        self.assertIsNone(self.invoke(self.arguments(source=singleton), 2))
        nonfinite = self.root / "nonfinite.pcd"
        write_pcd(nonfinite, [(math.nan, 0, 0)])
        self.assertIsNone(self.invoke(self.arguments(source=nonfinite), 2))
        self.assertIsNone(self.invoke(self.arguments(source=self.root / "missing.pcd"), 3))
        malformed = self.root / "malformed.pcd"
        malformed.write_text("not a PCD\n")
        self.assertIsNone(self.invoke(self.arguments(source=malformed), 3))

    def test_report_preservation_and_unknown_truth(self):
        protected = self.root / "protected.json"
        protected.write_text("preserve existing report")
        self.assertIsNone(self.invoke(self.arguments() + ["--output", protected], 3))
        self.assertEqual(protected.read_text(), "preserve existing report")
        report = self.invoke(self.arguments(), 0)
        self.assertIsNone(report["translation_error_m"])
        self.assertIsNone(report["rotation_error_rad"])
        self.assertTrue(report["accepted"])

    def test_malformed_coordinate_never_reaches_icp(self):
        points = [(0, 0, 0), (1, 0, 0), (0, 2, 0), (0, 0, 3), (2, 0, 4), (4, 1, 2)]
        good, bad = self.root/'zero-token.pcd', self.root/'bad-token.pcd'
        write_pcd(good, points)
        for token in ('foo', '1foo', '1e999'):
            bad.write_text(good.read_text(encoding='ascii').replace('2 0 4', f'2 {token} 4'), encoding='ascii')
            for source, target in ((bad, good), (good, bad)):
                with self.subTest(token=token, source=str(source)):
                    output = self.root/f'invalid-{token}-{source.stem}.json'
                    self.assertIsNone(self.invoke(['--source', source, '--target', target,
                                                  '--voxel-size', '.1', '--output', output], 3))
                    self.assertFalse(output.exists())
        self.assertTrue(self.invoke(['--source', good, '--target', good, '--voxel-size', '.1'], 0)['accepted'])

    def test_repeated_structure_is_an_explicit_limitation(self):
        rng = random.Random(7)
        points = [tuple(rng.random() for _ in range(3)) for _ in range(150)]
        source, target = self.root/'repeat-source.pcd', self.root/'repeat-target.pcd'
        write_pcd(source, points)
        write_pcd(target, points + [(x+5, y, z) for x, y, z in points])
        initial, truth = self.root/'repeat-initial.txt', self.root/'repeat-truth.txt'
        write_matrix(initial, transform(0, (5, 0, 0)))
        write_matrix(truth, transform(0, (0, 0, 0)))
        report = self.invoke(['--source', source, '--target', target, '--voxel-size', '.005',
                              '--initial', initial, '--truth', truth], 0)
        self.assertTrue(report['accepted'])
        self.assertGreater(report['inlier_ratio'], .99)
        self.assertLess(report['rmse_m'], 1e-5)
        self.assertAlmostEqual(report['translation_error_m'], 5, places=4)
        print('repeated_structure_limitation:', {k: report[k] for k in
              ('accepted', 'rmse_m', 'inlier_ratio', 'translation_error_m')}, flush=True)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *unittest_args], verbosity=2)
