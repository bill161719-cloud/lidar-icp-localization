"""驱动真实 CLI、保留原始证据，并从实际点云生成静态实验图。"""
import argparse
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np



def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def read_pcd(path):
    raw = Path(path).read_bytes()
    offset = 0
    fields = []
    for line in raw.splitlines(keepends=True):
        offset += len(line)
        if line.startswith(b'FIELDS '):
            fields = line.decode().split()[1:]
        if line.startswith(b'DATA '):
            mode = line.strip().split()[1]
            break
    else:
        raise ValueError('PCD 缺失 DATA')
    body = raw[offset:]
    if mode == b'binary':
        return np.frombuffer(body, dtype='<f4').reshape(-1, len(fields))[:, :3].astype(float)
    if mode != b'ascii':
        raise ValueError('实验绘图读取器仅支持本工具生成的 ASCII/binary PCD')
    return np.atleast_2d(np.loadtxt(io.BytesIO(body)))[:, :3]



def write_pcd(path, points):
    with path.open('x', encoding='ascii') as f:
        f.write('VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n'
                f'WIDTH {len(points)}\nHEIGHT 1\nPOINTS {len(points)}\nDATA ascii\n')
        np.savetxt(f, points, fmt='%.10g')


def moved(points, matrix):
    matrix = np.asarray(matrix)
    return points @ matrix[:3, :3].T + matrix[:3, 3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot_pair(source, target, report, path, road=False):
    if not report['accepted']:
        raise RuntimeError('拒绝绘制被拒绝结果的有效对齐图')
    aligned = moved(source, report['T_target_source'])
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    limits = ((-20, 40), (-25, 25), (-4, 8)) if road else ((-1, 9), (-1, 6), (-1, 4))
    for row, (a, b, names) in enumerate([(0, 1, ('x (m)', 'y (m)')), (0, 2, ('x (m)', 'z (m)'))]):
        for col, points in enumerate([source, aligned]):
            ax = axes[row, col]
            ax.scatter(target[::3 if road else 1, a], target[::3 if road else 1, b], s=0.4 if road else 2,
                       color='#ea8a23', alpha=.55, label='target')
            ax.scatter(points[::3 if road else 1, a], points[::3 if road else 1, b], s=0.4 if road else 2,
                       color='#237ac4', alpha=.55, label='source' if col == 0 else 'aligned source')
            ax.set(xlim=limits[a], ylim=limits[b], xlabel=names[0], ylabel=names[1],
                   title='配准前' if col == 0 else '配准后（accepted=true）')
            ax.set_aspect('equal', adjustable='box')
            ax.grid(alpha=.2)
            ax.legend(markerscale=5, loc='upper right')
    fig.suptitle(('KITTI 相邻帧；仅显示局部视窗，运算使用完整点云' if road else '已知刚体变换；非对称三维结构')+
                 f"\n内点 RMSE={report['rmse_m']:.6g} m；内点率={report['inlier_ratio']:.4f}")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_raw(points, path, road=False):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(projection='3d')
    p = points[::5] if road else points
    if road:
        p = p[(p[:, 0] > -20) & (p[:, 0] < 40) & (abs(p[:, 1]) < 25) & (p[:, 2] < 8)]
    artist = ax.scatter(*p.T, c=p[:, 2], cmap='viridis', s=.8 if road else 3)
    ax.set(xlabel='x (m)', ylabel='y (m)', zlabel='z (m)',
           title='KITTI 帧 0000000001 原始点云（局部视窗，每 5 点显示 1 点）' if road else '人工 source 原始三维点云（2400 点）')
    ax.view_init(elev=25, azim=-65)
    fig.colorbar(artist, ax=ax, shrink=.6, label='z (m)')
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main(args):
    output = args.output
    if output.exists():
        raise ValueError('实验输出目录必须不存在，防止覆盖证据')
    output.mkdir(parents=True)
    figures = args.figures
    if figures.exists():
        raise ValueError('图片输出目录必须不存在')
    figures.mkdir(parents=True)
    data = args.work
    data.mkdir(parents=True, exist_ok=True)
    synthetic = data/'synthetic'
    subprocess.run([str(args.generator), '--output', str(synthetic), '--seed', '20261027'], check=True)
    source, target = read_pcd(synthetic/'source.pcd'), read_pcd(synthetic/'target.pcd')
    rng = np.random.default_rng(20261027)
    write_pcd(data/'noisy_target.pcd', target+rng.normal(0, .02, target.shape))
    write_pcd(data/'outlier_source.pcd', np.vstack([source, rng.uniform([15, 15, 10], [20, 20, 15], (240, 3))]))
    write_pcd(data/'partial_target.pcd', target[:240])
    bad = np.eye(4); bad[:3, 3] = [30, 30, 30]
    np.savetxt(data/'bad_initial.txt', bad)
    records = []
    reports = {}
    used_inputs = set()

    def run(name, s, t, voxel, truth=None, initial=None, rmse=.2, evaluation=.5, correspondence=1.0):
        used_inputs.update(Path(p) for p in (s, t, truth, initial) if p is not None)
        command = [str(args.exe), '--source', str(s), '--target', str(t), '--output', str(output/(name+'.json')),
                   '--voxel-size', str(voxel), '--max-iterations', '100',
                   '--max-correspondence-distance', str(correspondence),
                   '--evaluation-distance', str(evaluation), '--max-rmse', str(rmse)]
        if truth: command += ['--truth', str(truth)]
        if initial: command += ['--initial', str(initial)]
        result = subprocess.run(command, capture_output=True, timeout=180)
        (output/(name+'.stderr.txt')).write_bytes(result.stderr)
        save_json(output/(name+'.command.json'), {'argv': command, 'exit_code': result.returncode})
        if not result.stdout.strip():
            (output/(name+'.stdout.txt')).write_bytes(result.stdout)
            raise RuntimeError(f'{name}: CLI 未产生报告；退出码 {result.returncode}')
        report = json.loads(result.stdout)
        if report != json.loads((output/(name+'.json')).read_text(encoding='utf-8')):
            raise RuntimeError('stdout 与保存报告不一致')
        if result.returncode != (0 if report['accepted'] else 4):
            raise RuntimeError('退出码与 accepted 不一致')
        if not report['accepted'] and (report['T_target_source'] is not None or report['pose'] is not None):
            raise RuntimeError('拒绝结果包含有效位姿')
        if not truth and (report['translation_error_m'] is not None or report['rotation_error_rad'] is not None):
            raise RuntimeError('无真值场景出现真值误差')
        row = {'experiment': name, 'source_frame': s.name, 'target_frame': t.name,
               'voxel_size_m': voxel, 'max_iterations': 100, 'max_correspondence_distance_m': correspondence,
               'evaluation_distance_m': evaluation, 'max_rmse_m': rmse, 'initial': str(initial) if initial else 'identity',
               'source_input_points': report['source_points']['input'], 'source_output_points': report['source_points']['output'],
               'target_input_points': report['target_points']['input'], 'target_output_points': report['target_points']['output'],
               'exit_code': result.returncode}
        for key in ['converged', 'accepted', 'fitness_m2', 'rmse_m', 'inliers', 'inlier_ratio',
                    'elapsed_ms', 'translation_error_m', 'rotation_error_rad', 'rejection_reason']:
            row[key] = report[key]
        records.append(row); reports[name] = report
        print(name, row, flush=True)
        return report

    for voxel in [.02, .1, .3]:
        run(f'synthetic_v{voxel}', synthetic/'source.pcd', synthetic/'target.pcd', voxel,
            truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
    clean = reports['synthetic_v0.02']
    if not clean['accepted'] or clean['translation_error_m'] >= .01 or clean['rotation_error_rad'] >= math.radians(.1):
        raise RuntimeError('人工数据精度验收失败')
    run('synthetic_noise_outliers', data/'outlier_source.pcd', data/'noisy_target.pcd', .1,
        truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
    rejected = run('synthetic_bad_initial', synthetic/'source.pcd', synthetic/'target.pcd', .1,
                   truth=synthetic/'truth.txt', initial=data/'bad_initial.txt')
    if rejected['accepted']: raise RuntimeError('远离初值未被拒绝')
    run('synthetic_partial', synthetic/'source.pcd', data/'partial_target.pcd', .1,
        truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plot_raw(source, figures/'synthetic_raw.png')
    plot_pair(source, target, clean, figures/'synthetic_alignment.png')
    pair = args.kitti
    road_source, road_target = pair/'0000000001.pcd', pair/'0000000000.pcd'
    for voxel in [.1, .3, .6]:
        run(f'kitti_v{voxel}', road_source, road_target, voxel)
    run('kitti_strict_gate', road_source, road_target, .3, rmse=.01)
    road = reports['kitti_v0.3']
    plot_raw(read_pcd(road_source), figures/'kitti_raw.png', road=True)
    plot_pair(read_pcd(road_source), read_pcd(road_target), road, figures/'kitti_alignment.png', road=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    synth = [r for r in records if r['experiment'].startswith('synthetic_v')]
    road_rows = [r for r in records if r['experiment'].startswith('kitti_v')]
    for rows, ax, title in [(synth, axes[0], '人工已知变换'), (road_rows, axes[1], 'KITTI 相邻帧（无参考真值）')]:
        ax.plot([r['voxel_size_m'] for r in rows], [r['rmse_m'] for r in rows], 'o-', label='内点 RMSE (m)')
        ax.set(xlabel='体素边长 (m)', ylabel='内点 RMSE (m)', title=title)
        ax.grid(alpha=.3); ax.legend()
    fig.tight_layout(); fig.savefig(figures/'voxel_comparison.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    voxels = [r['voxel_size_m'] for r in synth]
    axes[0].plot(voxels, [r['translation_error_m'] for r in synth], 'o-')
    axes[0].set(ylabel='平移误差 (m)', xlabel='体素边长 (m)')
    axes[1].plot(voxels, [math.degrees(r['rotation_error_rad']) for r in synth], 'o-')
    axes[1].set(ylabel='旋转误差 (°)', xlabel='体素边长 (m)')
    for ax in axes: ax.grid(alpha=.3)
    fig.suptitle('人工已知变换误差；单位阵初值')
    fig.tight_layout(); fig.savefig(figures/'synthetic_errors.png', dpi=160); plt.close(fig)
    if args.sweep:
        # Bounded, deterministic experiment coverage; this does not change ICP.
        for sigma in [0.0, .01, .03, .08]:
            path = data/f'sweep_noise_{sigma}.pcd'
            samples = target + np.random.default_rng(2710).normal(0, sigma, target.shape)
            write_pcd(path, samples)
            run(f'sweep_noise_{sigma}', synthetic/'source.pcd', path, .1,
                truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
        for fraction in [0.0, .1, .5, 1.0]:
            count = round(len(source)*fraction)
            extra = np.random.default_rng(2711).uniform([15, 15, 10], [20, 20, 15], (count, 3))
            path = data/f'sweep_outliers_{fraction}.pcd'
            write_pcd(path, np.vstack([source, extra]))
            run(f'sweep_outliers_{fraction}', path, synthetic/'target.pcd', .1,
                truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
        order = np.random.default_rng(2712).permutation(len(target))
        for fraction in [1.0, .75, .5, .25, .1]:
            path = data/f'sweep_target_samples_{fraction}.pcd'
            write_pcd(path, target[order[:round(len(target)*fraction)]])
            run(f'sweep_target_samples_{fraction}', synthetic/'source.pcd', path, .1,
                truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
        for fraction in [1.0, .75, .5, .25, .1]:
            # Known source/target point pairing makes this a spatial region crop,
            # distinct from uniformly reducing target sampling density.
            path = data/f'sweep_spatial_crop_{fraction}.pcd'
            write_pcd(path, target[source[:, 0] <= 8.0*fraction])
            run(f'sweep_spatial_crop_{fraction}', synthetic/'source.pcd', path, .1,
                truth=synthetic/'truth.txt', rmse=.1, evaluation=.2)
        for tx in [0.0, .3, 1.0, 3.0, 30.0]:
            path = data/f'sweep_initial_tx_{tx}.txt'
            guess = np.eye(4); guess[0, 3] = tx
            np.savetxt(path, guess)
            run(f'sweep_initial_tx_{tx}', synthetic/'source.pcd', synthetic/'target.pcd', .1,
                truth=synthetic/'truth.txt', initial=path, rmse=.1, evaluation=.2)
        # Ambiguous geometry: wrong rotations can have perfect correspondences.
        truth = np.loadtxt(synthetic/'truth.txt')
        geometry = {
            'line': np.column_stack([np.linspace(-3, 3, 301), np.zeros((301, 2))]),
            'symmetric_plane': np.array([(x, y, 0) for x in np.linspace(-2, 2, 21)
                                        for y in np.linspace(-2, 2, 21)])}
        for name, points in geometry.items():
            src, dst, init = data/f'sweep_{name}_source.pcd', data/f'sweep_{name}_target.pcd', data/f'sweep_{name}_initial.txt'
            write_pcd(src, points); write_pcd(dst, moved(points, truth))
            ambiguity = np.eye(4)
            if name == 'line':
                ambiguity[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
            else:
                ambiguity[0, 0] = ambiguity[1, 1] = -1
            np.savetxt(init, truth @ ambiguity)
            run(f'sweep_degenerate_{name}', src, dst, .005,
                truth=synthetic/'truth.txt', initial=init, rmse=.1, evaluation=.2)
    with (output/'summary.csv').open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    inputs = [synthetic/p for p in ['source.pcd', 'target.pcd', 'truth.txt', 'metadata.json']]
    inputs += [data/p for p in ['noisy_target.pcd', 'outlier_source.pcd', 'partial_target.pcd', 'bad_initial.txt']]
    inputs += [pair/p for p in ['0000000000.bin', '0000000001.bin', '0000000000.pcd', '0000000001.pcd', 'timestamps.txt']]
    inputs = sorted(set(inputs) | used_inputs)
    source_files = [Path('CMakeLists.txt'), Path('tools/generate_test_data.cpp'), Path('tools/run_experiments.py')]
    source_files += sorted(Path('src').glob('*.cpp')) + sorted(Path('include').glob('*.h'))
    save_json(output/'provenance.json', {
        'date': datetime.now().astimezone().isoformat(),
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'working_tree_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()),
        'binary_sha256': {'lidar_icp': sha(args.exe), 'generate_test_data': sha(args.generator)},
        'source_sha256': {p.as_posix(): sha(p) for p in source_files},
        'python': platform.python_version(), 'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
        'input_sha256': {p.as_posix(): sha(p) for p in inputs},
        'figure_sha256': {p.name: sha(p) for p in sorted(figures.glob('*.png'))},
        'download': json.loads((pair/'download.json').read_text()),
        'conversion': [json.loads((pair/(str(i).zfill(10)+'.conversion.json')).read_text()) for i in [0, 1]],
        'timestamp_pair': (pair/'timestamps.txt').read_text().splitlines()[:2],
        'validation': 'stdout 与文件逐项相等；退出码/accepted 一致；拒绝位姿为 null；无真值误差为 null；人工精度通过',
        'plotting': '原始完整点云作变换；道路图每 3/5 点显示一点并裁剪视窗；不使用诊断矩阵绘制对齐',
        'timing': '单次 align 耗时，仅供观察，非性能基准'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=Path('build-pcl/lidar_icp.exe'))
    parser.add_argument('--generator', type=Path, default=Path('build-pcl/generate_test_data.exe'))
    parser.add_argument('--work', type=Path, default=Path('build-pcl/experiments-v1'))
    parser.add_argument('--kitti', type=Path, default=Path('data/kitti/drive_0005_pair'))
    parser.add_argument('--output', type=Path, default=Path('results/metrics/module-c-v1'))
    parser.add_argument('--figures', type=Path, default=Path('results/figures/module-c-v1'))
    parser.add_argument('--sweep', action='store_true', help='附加25个固定参数/空间裁剪/退化反例实验；非完整鲁棒性保证')
    main(parser.parse_args())
