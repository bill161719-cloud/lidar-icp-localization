"""仅监听本机的 LiDAR 演示服务；配准计算由现有 C++ CLI 完成。"""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import secrets
import struct
import subprocess
import threading
from urllib.parse import urlsplit, parse_qs
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / 'static'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_points(path, limit=18000):
    """只为显示读取项目生成的 ASCII/binary FLOAT32 XYZ；不替代 C++ 校验。"""
    with path.open('rb') as stream:
        header = {}
        for _ in range(40):
            line = stream.readline().decode('ascii').strip()
            if not line or line.startswith('#'):
                continue
            key, *values = line.split()
            header[key] = values
            if key == 'DATA':
                break
        fields = header['FIELDS']
        if header['TYPE'] != ['F'] * len(fields) or header['SIZE'] != ['4'] * len(fields):
            raise ValueError('演示读取器仅支持 FLOAT32；算法读取仍使用 PCL')
        if header.get('COUNT', ['1'] * len(fields)) != ['1'] * len(fields):
            raise ValueError('不支持的 PCD COUNT')
        indices = [fields.index(k) for k in ('x', 'y', 'z')]
        count = int(header['POINTS'][0])
        if not 0 < count <= 2000000:
            raise ValueError('点数超出演示范围')
        payload = stream.read()
        if header['DATA'] == ['binary']:
            if len(payload) != count * 4 * len(fields):
                raise ValueError('PCD 数据长度不符')
            rows = struct.iter_unpack('<' + 'f' * len(fields), payload)
        elif header['DATA'] == ['ascii']:
            rows = [list(map(float, line.split())) for line in payload.decode('ascii').splitlines() if line.strip()]
            if len(rows) != count or any(len(row) != len(fields) for row in rows):
                raise ValueError('PCD 行数或列数不符')
        else:
            raise ValueError('演示不支持压缩 PCD')
        stride = max(1, math.ceil(count / limit))
        points = []
        for i, row in enumerate(rows):
            xyz = [row[index] for index in indices]
            if i % stride == 0 and all(math.isfinite(v) for v in xyz):
                points.append(xyz)
        return {'points': points, 'input_points': count, 'stride': stride,
                'sha256': digest(path)}


class Demo:
    def __init__(self, binary, dependency_root, msys_root, work):
        self.binary = binary.resolve()
        self.work = work.resolve()
        self.env = os.environ.copy()
        self.env['PATH'] = os.pathsep.join([str(dependency_root / 'pcl-1.15.1/bin'),
                                          str(msys_root / 'ucrt64/bin'), self.env.get('PATH', '')])
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.cache = {}
        self.datasets = {}
        self.work.mkdir(parents=True, exist_ok=True)
        synthetic = self.work / 'synthetic'
        if not (synthetic / 'source.pcd').exists():
            generator = self.binary.with_name('generate_test_data.exe' if os.name == 'nt' else 'generate_test_data')
            if generator.exists():
                subprocess.run([str(generator), '--output', str(synthetic), '--seed', '20261027'],
                               env=self.env, check=True, capture_output=True, timeout=30)
        self.add('synthetic', '合成真值 · 非对称结构', synthetic / 'source.pcd',
                 synthetic / 'target.pcd', synthetic / 'truth.txt',
                 '2400 点 · 固定种子 20261027 · MIT', 0.02, 0.2, 0.1)
        pair = ROOT / 'data/kitti/drive_0005_pair'
        self.add('kitti', 'KITTI · 城市道路相邻帧', pair / '0000000001.pcd',
                 pair / '0000000000.pcd', None,
                 'drive_0005 · source 帧1 → target 帧0 · CC BY-NC-SA 3.0', 0.3, 0.5, 0.2)
        if not self.datasets:
            raise ValueError('没有可用点云，请先构建生成器或按 QUICKSTART 准备 KITTI')

    def add(self, key, title, source, target, truth, note, voxel, evaluation, rmse):
        if source.is_file() and target.is_file() and (truth is None or truth.is_file()):
            self.datasets[key] = dict(id=key, title=title, source=source, target=target,
                                      truth=truth, note=note, voxel=voxel,
                                      evaluation=evaluation, max_rmse=rmse)

    def dataset(self, key):
        if key not in self.datasets:
            raise ValueError('未配置的数据集')
        return self.datasets[key]

    def clouds(self, key):
        d = self.dataset(key)
        if key not in self.cache:
            self.cache[key] = {side: read_points(d[side]) for side in ('source', 'target')}
        return self.cache[key]

    def replay(self, key, coarse=False):
        d = self.dataset(key)
        name = ('kitti_v0.6' if coarse else 'kitti_v0.3') if key == 'kitti' else 'synthetic_v0.02'
        path = ROOT / 'results/metrics/remediation' / (name + '.json')
        report = json.loads(path.read_text(encoding='utf-8'))
        provenance = json.loads(path.with_name('provenance.json').read_text(encoding='utf-8'))
        for side in ('source', 'target'):
            old_path = report[side].replace('\\', '/')
            if digest(d[side]) != provenance['input_sha256'][old_path]:
                raise ValueError('当前点云与历史记录哈希不同，不能叠加回放；请使用实际配准')
        return {'mode': 'replay', 'report': report, 'archive': str(path.relative_to(ROOT)),
                'message': '已验证实验回放；耗时来自历史记录，本次未执行 ICP'}

    def run(self, request):
        allowed = {'dataset', 'voxel', 'iterations', 'correspondence', 'evaluation', 'max_rmse'}
        if set(request) != allowed:
            raise ValueError('请求字段不符合规范')
        d = self.dataset(request['dataset'])
        bounds = {'voxel': (0.005, 2), 'iterations': (1, 200), 'correspondence': (0.01, 10),
                  'evaluation': (0.01, 5), 'max_rmse': (0.001, 2)}
        for name, (low, high) in bounds.items():
            value = request[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError('参数超出安全演示范围：' + name)
        if request['iterations'] != int(request['iterations']):
            raise ValueError('迭代次数必须为整数')
        if not self.lock.acquire(blocking=False):
            raise ValueError('已有配准正在执行，请稍后重试')
        try:
            run_id = uuid.uuid4().hex
            folder = self.work / 'runs' / run_id
            folder.mkdir(parents=True)
            output = folder / 'report.json'
            command = [str(self.binary), '--source', str(d['source']), '--target', str(d['target']),
                       '--voxel-size', str(request['voxel']), '--max-iterations', str(int(request['iterations'])),
                       '--max-correspondence-distance', str(request['correspondence']),
                       '--evaluation-distance', str(request['evaluation']), '--max-rmse', str(request['max_rmse']),
                       '--output', str(output)]
            if d['truth']:
                command += ['--truth', str(d['truth'])]
            inputs = {side: digest(d[side]) for side in ('source', 'target')}
            if d['truth']:
                inputs['truth'] = digest(d['truth'])
            metadata = {'run_id': run_id, 'started_utc': datetime.now(timezone.utc).isoformat(),
                        'argv': command, 'binary_sha256': digest(self.binary), 'input_sha256': inputs}
            try:
                proc = subprocess.run(command, env=self.env, cwd=ROOT, capture_output=True,
                                      timeout=60, text=True, encoding='utf-8', errors='replace')
            except subprocess.TimeoutExpired:
                metadata['error'] = 'timeout_60s'
                (folder / 'execution.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
                raise ValueError('实际配准超过 60 秒，已终止；请恢复默认参数')
            metadata.update(exit_code=proc.returncode, stderr=proc.stderr, stdout=proc.stdout)
            (folder / 'execution.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
            if proc.returncode not in (0, 4) or not output.is_file():
                raise ValueError('C++ 程序运行失败，退出码 ' + str(proc.returncode) + '；详见本地运行日志')
            report = json.loads(output.read_text(encoding='utf-8'))
            if report['accepted'] != (proc.returncode == 0):
                raise ValueError('C++ 退出状态与质量结果不一致')
            return {'mode': 'live', 'report': report, 'run_id': run_id,
                    'message': '本次由本机 C++ / PCL 实际计算；报告及调用日志已保存'}
        finally:
            self.lock.release()


class Handler(BaseHTTPRequestHandler):
    server_version = 'LiDARDemo/1.0'

    def send(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def trusted(self):
        authority = '127.0.0.1:' + str(self.server.server_port)
        return (self.headers.get('Host') == authority
                and self.headers.get('Origin', 'http://' + authority) == 'http://' + authority
                and self.headers.get('Sec-Fetch-Site') != 'cross-site')

    def do_GET(self):
        if not self.trusted():
            return self.send(403, {'error': '仅允许本机同源访问，请用 127.0.0.1 打开'})
        url = urlsplit(self.path)
        demo = self.server.demo
        try:
            if url.path == '/api/config':
                data = [{k: v for k, v in d.items() if k not in ('source', 'target', 'truth')}
                        for d in demo.datasets.values()]
                return self.send(200, {'datasets': data, 'token': demo.token, 'binary_ready': demo.binary.is_file()})
            query = parse_qs(url.query)
            key = query.get('dataset', ['kitti'])[0]
            if url.path == '/api/clouds':
                return self.send(200, demo.clouds(key))
            if url.path == '/api/replay':
                return self.send(200, demo.replay(key, query.get('coarse') == ['1']))
            assets = {'/': (STATIC / 'index.html', 'text/html; charset=utf-8'),
                      '/app.js': (STATIC / 'app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': (STATIC / 'style.css', 'text/css; charset=utf-8'),
                      '/voxel.png': (ROOT / 'results/figures/module-c-v2/voxel_comparison.png', 'image/png')}
            if url.path in assets:
                path, content_type = assets[url.path]
                return self.send(200, path.read_bytes(), content_type)
            return self.send(404, {'error': '未找到资源'})
        except (ValueError, KeyError, OSError) as error:
            return self.send(400, {'error': str(error)})

    def do_POST(self):
        if not self.trusted() or not secrets.compare_digest(self.headers.get('X-Demo-Token', ''), self.server.demo.token):
            return self.send(403, {'error': '同源会话校验失败，请刷新页面'})
        if self.path != '/api/run':
            return self.send(404, {'error': '未找到接口'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('请求大小不符合规范')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('请求必须为 JSON 对象')
            self.send(200, self.server.demo.run(payload))
        except (ValueError, KeyError, OSError, TypeError) as error:
            self.send(400, {'error': str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--binary', type=Path, default=ROOT / 'build-release-ready/lidar_icp.exe')
    parser.add_argument('--dependency-root', type=Path, default=ROOT / '.local-deps')
    parser.add_argument('--msys-root', type=Path, default=Path('C:/msys64'))
    parser.add_argument('--work', type=Path, default=ROOT / 'build-web-demo')
    parser.add_argument('--open-browser', action='store_true')
    args = parser.parse_args()
    demo = Demo(args.binary, args.dependency_root, args.msys_root, args.work)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.demo = demo
    print(f'LiDAR 本地演示：http://127.0.0.1:{server.server_port}  （Ctrl+C 停止）', flush=True)
    if args.open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(f'http://127.0.0.1:{server.server_port}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
