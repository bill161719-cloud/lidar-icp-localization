"""验证离线一致性检查能发现损坏的 CSV、JSON 和图像；不需要 KITTI 原始数据。"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from validate_experiments import load_json, validate, validate_reports

parser = argparse.ArgumentParser()
parser.add_argument('--archive', type=Path, required=True)
parser.add_argument('--figures', type=Path, required=True)
parser.add_argument('--workdir', type=Path, required=True)
args, rest = parser.parse_known_args()
args.workdir.mkdir(parents=True, exist_ok=True)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='validation-', dir=args.workdir))
        self.metrics = self.root/'metrics'
        shutil.copytree(args.archive, self.metrics)

    def test_original_archive_is_consistent(self):
        result = validate(self.metrics, args.figures, check_inputs=False)
        self.assertEqual(result['reports_checked'], 10)
        self.assertEqual(result['figures_checked'], 6)

    def test_csv_metric_corruption_detected(self):
        path = self.metrics/'summary.csv'
        with path.open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        rows[0]['rmse_m'] = '123.0'
        with path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, '数值不一致'):
            validate_reports(self.metrics)

    def test_rejected_pose_corruption_detected(self):
        path = self.metrics/'synthetic_bad_initial.json'
        report = load_json(path)
        report['pose'] = {'translation_m': [0, 0, 0]}
        save(path, report)
        with self.assertRaisesRegex(ValueError, '拒绝状态仍含有效位姿'):
            validate_reports(self.metrics)

    def test_reference_compares_transformation_not_timing(self):
        path = self.metrics/'synthetic_v0.02.json'
        report = load_json(path)
        report['source'] = 'different-root/source.pcd'
        report['target'] = 'different-root/target.pcd'
        report['elapsed_ms'] += 42
        csv_path = self.metrics/'summary.csv'
        with csv_path.open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            if row['experiment'] == 'synthetic_v0.02':
                row['elapsed_ms'] = str(report['elapsed_ms'])
        with csv_path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        save(path, report)
        self.assertEqual(len(validate(self.metrics, args.figures, args.archive,
                                      check_inputs=False)['reference_cases_matched']), 10)
        report['T_target_source'][0][3] += 1
        save(path, report)
        with self.assertRaisesRegex(ValueError, '复验不一致'):
            validate(self.metrics, args.figures, args.archive, check_inputs=False)

    def test_figure_corruption_detected(self):
        figures = self.root/'figures'
        shutil.copytree(args.figures, figures)
        with (figures/'kitti_alignment.png').open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaisesRegex(ValueError, '图像哈希错误'):
            validate(self.metrics, figures, check_inputs=False)


unittest.main(argv=[sys.argv[0], *rest])
