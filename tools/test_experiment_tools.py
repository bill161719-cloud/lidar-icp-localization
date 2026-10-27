"""验证生成器契约、转换字节保持及非法输入拒绝，不依赖核心模块改动。"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from kitti_bin_to_pcd import convert
from fetch_kitti_pair import fetch

parser = argparse.ArgumentParser()
parser.add_argument('--generator', type=Path, required=True)
parser.add_argument('--workdir', type=Path, required=True)
args, rest = parser.parse_known_args()
args.workdir.mkdir(parents=True, exist_ok=True)


class ExperimentToolTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=args.workdir, prefix='tools-'))

    def invoke(self, *options):
        return subprocess.run([str(args.generator), *map(str, options)], capture_output=True, timeout=30)

    def test_generator_reproducible_and_truth(self):
        for name in ['a', 'b']:
            result = self.invoke('--output', self.root/name, '--seed', '20261027')
            self.assertEqual(result.returncode, 0, result.stderr)
        for name in ['source.pcd', 'target.pcd', 'truth.txt', 'metadata.json']:
            self.assertEqual((self.root/'a'/name).read_bytes(), (self.root/'b'/name).read_bytes())
        def points(path):
            return [list(map(float, row.split())) for row in path.read_text().split('DATA ascii\n')[1].splitlines()]
        source, target = points(self.root/'a/source.pcd'), points(self.root/'a/target.pcd')
        matrix = [list(map(float, row.split())) for row in (self.root/'a/truth.txt').read_text().splitlines()]
        self.assertEqual(len(source), 2400)
        self.assertEqual(len(source), len(target))
        error = max(abs(sum(matrix[i][j]*p[j] for j in range(3))+matrix[i][3]-q[i])
                    for p, q in zip(source, target) for i in range(3))
        self.assertLess(error, 2e-8)
        meta = json.loads((self.root/'a/metadata.json').read_text())
        self.assertEqual(meta['seed'], 20261027)

    def test_generator_cli_errors_and_no_overwrite(self):
        self.assertEqual(self.invoke('--help').returncode, 0)
        for seed in ['-1', '4294967296', '1x', '+1', '']:
            self.assertNotEqual(self.invoke('--output', self.root/'bad', '--seed', seed).returncode, 0)
        for seed in ['0', '4294967295']:
            self.assertEqual(self.invoke('--output', self.root/seed, '--seed', seed).returncode, 0)
        destination = self.root/'existing'
        destination.mkdir(); (destination/'truth.txt').write_text('preserve')
        self.assertNotEqual(self.invoke('--output', destination, '--seed', '1').returncode, 0)
        self.assertEqual((destination/'truth.txt').read_text(), 'preserve')
        self.assertEqual(list(destination.iterdir()), [destination/'truth.txt'])

    def test_conversion_exact_payload(self):
        raw = struct.pack('<8f', 1.25, -2, .5, .75, -3, 0, 5, .125)
        src, dst = self.root/'a.bin', self.root/'a.pcd'
        src.write_bytes(raw)
        report = convert(src, dst)
        self.assertEqual(dst.read_bytes().split(b'DATA binary\n')[1], raw)
        self.assertEqual(report['points'], 2)
        self.assertEqual(report['input_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertFalse(report['coordinates_changed'])
        before = dst.read_bytes()
        with self.assertRaises(ValueError): convert(src, dst)
        self.assertEqual(dst.read_bytes(), before)

    def test_conversion_rejects_malformed(self):
        for n, raw in enumerate([b'', b'123', struct.pack('<4f', float('nan'), 0, 0, 0),
                                 struct.pack('<4f', 0, 0, 0, float('inf'))]):
            src, dst = self.root/f'{n}.bin', self.root/f'{n}.pcd'
            src.write_bytes(raw)
            with self.assertRaises(ValueError): convert(src, dst)
            self.assertFalse(dst.exists())

    def test_download_refuses_full_response(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *unused): pass
            def read(self, *unused): raise AssertionError('不应读取整包响应')
        with patch('urllib.request.urlopen', return_value=Response()):
            with self.assertRaises(RuntimeError): fetch(self.root/'download')


unittest.main(argv=[sys.argv[0], *rest])
