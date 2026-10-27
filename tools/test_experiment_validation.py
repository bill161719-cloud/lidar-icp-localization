"""验证离线一致性检查能发现损坏的 CSV、JSON 和图像；不需要 KITTI 原始数据。"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from validate_experiments import load_json, validate, validate_reports, validate_source_hashes, validate_truth_file

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
        with self.assertRaisesRegex(ValueError, '不一致'):
            validate(self.metrics, args.figures, args.archive, check_inputs=False)

    def test_figure_corruption_detected(self):
        figures = self.root/'figures'
        shutil.copytree(args.figures, figures)
        with (figures/'kitti_alignment.png').open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaisesRegex(ValueError, '图像哈希错误'):
            validate(self.metrics, figures, check_inputs=False)

    def test_matrix_and_pose_corruptions_without_reference(self):
        path = self.metrics/'synthetic_v0.02.json'
        original = load_json(path)
        mutations = [
            ('T_target_source', [[0]*4 for _ in range(4)]),
            ('T_target_source', [[1, 0], [0, 1]]),
            ('T_target_source', [[float('nan')]*4 for _ in range(4)]),
            ('diagnostic_T_target_source', [[1,0,0,9],[0,1,0,0],[0,0,1,0],[0,0,0,1]]),
            ('initial_T_target_source', [[0]*4 for _ in range(4)])]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                report = json.loads(json.dumps(original)); report[key] = value; save(path, report)
                with self.assertRaises(ValueError): validate_reports(self.metrics)
        for key, value in [('translation_m', [9,9,9]), ('quaternion_wxyz', [1,0,0,0]),
                           ('rotation', [[0]*3 for _ in range(3)])]:
            with self.subTest(key=key):
                report = json.loads(json.dumps(original)); report['pose'][key] = value; save(path, report)
                with self.assertRaises(ValueError): validate_reports(self.metrics)

    def test_command_semantic_corruptions_without_reference(self):
        path = self.metrics/'synthetic_v0.02.command.json'
        original = load_json(path)
        for key, value in [('--source', 'fake.pcd'), ('--target', 'fake.pcd'),
                           ('--max-rmse', '999'), ('--truth', 'fake_truth')]:
            command = json.loads(json.dumps(original))
            command['argv'][command['argv'].index(key)+1] = value
            save(path, command)
            with self.subTest(key=key), self.assertRaises(ValueError): validate_reports(self.metrics)
        for argv in [['fake_executable', '--truth', 'fake_truth', '--max-rmse', '999'],
                     original['argv']+['--max-rmse', '1'], original['argv']+['--unknown','1'],
                     original['argv']+['--initial','fake_initial'], original['argv'][:-1]]:
            command = dict(original); command['argv'] = argv; save(path, command)
            with self.subTest(argv=argv), self.assertRaises(ValueError): validate_reports(self.metrics)

    def test_explicit_source_snapshot_hashes(self):
        import hashlib
        source = self.root/'source'; source.mkdir()
        code = source/'original.cpp'; code.write_text('original code', encoding='utf-8')
        provenance = {'source_sha256': {'original.cpp': hashlib.sha256(code.read_bytes()).hexdigest()}}
        self.assertEqual(validate_source_hashes(provenance, source), 1)
        code.write_text('changed code', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '源码哈希错误'): validate_source_hashes(provenance, source)
        with self.assertRaises(ValueError): validate_source_hashes({}, source)
        code.write_bytes(b'line1\r\nline2\r\n')
        canonical = {'source_hash_policy':'utf8-lf', 'source_sha256':{
            'original.cpp':hashlib.sha256(b'line1\nline2\n').hexdigest()}}
        self.assertEqual(validate_source_hashes(canonical, source), 1)
        code.write_bytes(b'line1\nline2\n')
        self.assertEqual(validate_source_hashes(canonical, source), 1)
        code.write_bytes(b'changed\nline2\n')
        with self.assertRaises(ValueError): validate_source_hashes(canonical, source)

    def test_wrong_initial_file_and_valid_quaternion_sign(self):
        path = self.metrics/'synthetic_v0.02.json'
        report = load_json(path)
        report['pose']['quaternion_wxyz'] = [-x for x in report['pose']['quaternion_wxyz']]
        save(path, report)
        self.assertEqual(len(validate_reports(self.metrics)), 10)
        command_path = self.metrics/'synthetic_bad_initial.command.json'
        command = load_json(command_path)
        initial = self.root/'wrong-initial.txt'
        initial.write_text('1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1', encoding='ascii')
        old = command['argv'][command['argv'].index('--initial')+1]
        command['argv'][command['argv'].index('--initial')+1] = str(initial); save(command_path, command)
        provenance = load_json(self.metrics/'provenance.json')
        provenance['input_sha256'][str(initial)] = provenance['input_sha256'].pop(old.replace('\\','/'))
        save(self.metrics/'provenance.json', provenance)
        csv_path = self.metrics/'summary.csv'
        with csv_path.open(encoding='utf-8', newline='') as f: rows = list(csv.DictReader(f))
        for row in rows:
            if row['experiment'] == 'synthetic_bad_initial': row['initial'] = str(initial)
        # Put this case first: the test supplies only its local matrix fixture,
        # and must never depend on historical truth files outside the archive.
        rows.sort(key=lambda row: row['experiment'] != 'synthetic_bad_initial')
        with csv_path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, '初值文件/报告'):
            validate_reports(self.metrics, check_inputs=True)

    def test_truth_file_semantics(self):
        truth = self.root/'truth.txt'
        truth.write_text('1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1', encoding='ascii')
        identity = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        report = {'T_target_source':identity, 'translation_error_m':0., 'rotation_error_rad':0.}
        validate_truth_file(report, truth)
        report['translation_error_m'] = 5.
        with self.assertRaisesRegex(ValueError, 'truth 文件'): validate_truth_file(report, truth)


unittest.main(argv=[sys.argv[0], *rest])
