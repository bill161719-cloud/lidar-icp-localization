"""本地演示的真实 HTTP / C++ 回归；不下载数据或修改历史实验。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location('demo_server', Path(__file__).with_name('server.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (module.ROOT / 'build-web-demo').mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='demo-tests-', dir=module.ROOT / 'build-web-demo')
        cls.demo = module.Demo(module.ROOT / 'build-release-ready/lidar_icp.exe',
                              module.ROOT / '.local-deps', Path('C:/msys64'), Path(cls.temp.name))
        cls.http = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
        cls.http.demo = cls.demo
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.http.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path, payload=None, **headers):
        data = None if payload is None else json.dumps(payload).encode()
        if payload is not None:
            headers.setdefault('X-Demo-Token', self.demo.token)
        req = Request(self.base + path, data=data, headers=headers)
        try:
            with urlopen(req, timeout=70) as response:
                return response.status, response.read(), response.headers
        except HTTPError as error:
            return error.code, error.read(), error.headers

    def payload(self, dataset='synthetic', voxel=0.02):
        return dict(dataset=dataset, voxel=voxel, iterations=100, correspondence=1,
                    evaluation=0.2 if dataset == 'synthetic' else 0.5,
                    max_rmse=0.1 if dataset == 'synthetic' else 0.2)

    def test_static_offline_assets(self):
        for path in ('/', '/app.js', '/style.css', '/voxel.png'):
            status, body, headers = self.request(path)
            self.assertEqual(status, 200)
            self.assertGreater(len(body), 100)
            self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual(self.request('/../LICENSE')[0], 404)

    def test_config_and_clouds(self):
        status, raw, _ = self.request('/api/config')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['token'], self.demo.token)
        status, raw, _ = self.request('/api/clouds?dataset=synthetic')
        cloud = json.loads(raw)
        self.assertEqual(status, 200)
        self.assertEqual(len(cloud['source']['points']), 2400)
        self.assertEqual(cloud['source']['sha256'], module.digest(self.demo.datasets['synthetic']['source']))
        self.assertEqual(self.request('/api/clouds?dataset=../../LICENSE')[0], 400)

    def test_host_origin_and_token(self):
        self.assertEqual(self.request('/api/config', Host='attacker.example')[0], 403)
        self.assertEqual(self.request('/api/config', Origin='https://attacker.example')[0], 403)
        self.assertEqual(self.request('/api/run', self.payload(), **{'X-Demo-Token': 'wrong'})[0], 403)

    def test_invalid_parameters_never_start_cpp(self):
        for name, value in [('voxel', 0), ('iterations', 3.5), ('evaluation', True),
                            ('correspondence', '1;echo x'), ('max_rmse', float('inf')),
                            ('dataset', '../../LICENSE')]:
            body = self.payload()
            body[name] = value
            self.assertEqual(self.request('/api/run', body)[0], 400, name)
        body = self.payload()
        body['command'] = 'arbitrary'
        self.assertEqual(self.request('/api/run', body)[0], 400)

    def test_live_synthetic_truth_and_run_evidence(self):
        status, raw, _ = self.request('/api/run', self.payload())
        self.assertEqual(status, 200, raw)
        result = json.loads(raw)
        r = result['report']
        self.assertEqual(result['mode'], 'live')
        self.assertTrue(r['accepted'])
        self.assertLess(r['translation_error_m'], 0.01)
        self.assertLess(r['rotation_error_rad'], 0.00174533)
        folder = Path(self.temp.name) / 'runs' / result['run_id']
        evidence = json.loads((folder / 'execution.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['exit_code'], 0)
        self.assertEqual(evidence['binary_sha256'], module.digest(self.demo.binary))
        self.assertTrue((folder / 'report.json').is_file())

    def test_kitti_accepted_and_rejected(self):
        if 'kitti' not in self.demo.datasets:
            self.skipTest('本机未准备 KITTI，离线合成测试不要求外部数据')
        for voxel, accepted in ((0.3, True), (0.6, False)):
            status, raw, _ = self.request('/api/run', self.payload('kitti', voxel))
            self.assertEqual(status, 200, raw)
            report = json.loads(raw)['report']
            archive = self.demo.replay('kitti', voxel == 0.6)['report']
            self.assertEqual(report['accepted'], accepted)
            self.assertAlmostEqual(report['rmse_m'], archive['rmse_m'], places=8)
            if not accepted:
                self.assertIsNone(report['T_target_source'])
                self.assertIsNone(report['pose'])

    def test_replay_labeled_and_hash_verified(self):
        status, raw, _ = self.request('/api/replay?dataset=synthetic')
        self.assertEqual(status, 200, raw)
        self.assertEqual(json.loads(raw)['mode'], 'replay')
        source = self.demo.datasets['synthetic']['source']
        original = source.read_bytes()
        try:
            source.write_bytes(original + b'\n')
            self.assertEqual(self.request('/api/replay?dataset=synthetic')[0], 400)
        finally:
            source.write_bytes(original)

    def test_binary_reader_and_malformed_payload(self):
        import struct
        path = Path(self.temp.name) / 'reader.pcd'
        header = b'FIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nPOINTS 1\nDATA binary\n'
        path.write_bytes(header + struct.pack('<3f', 1, 2, 3))
        self.assertEqual(module.read_points(path)['points'], [[1, 2, 3]])
        path.write_bytes(header + b'bad')
        with self.assertRaises(ValueError):
            module.read_points(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
