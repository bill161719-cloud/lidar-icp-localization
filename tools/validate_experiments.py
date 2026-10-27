"""离线核对实验 CSV/JSON、门禁、输入/图像哈希和参考归档；不访问网络。"""
import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path
from pathlib import PurePosixPath


def path_key(value):
    require(isinstance(value, str) and bool(value), '命令路径为空或非法')
    return str(PurePosixPath(value.replace('\\', '/')))


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def matrix(value, rows, cols, label, nullable=False):
    require(isinstance(value, list) and len(value) == rows and
            all(isinstance(row, list) and len(row) == cols for row in value), f'{label}: 矩阵尺寸非法')
    require(all(numeric(v) or (nullable and v is None) for row in value for v in row),
            f'{label}: 矩阵含非有限/非数值元素')


def same_matrix(a, b, label, tolerance=1e-8):
    require(all(abs(x-y) <= tolerance for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b)),
            f'{label}: 矩阵/位姿不一致')


def se3(value, label):
    matrix(value, 4, 4, label)
    require(all(abs(x-y) <= 1e-4 for x, y in zip(value[3], [0, 0, 0, 1])), f'{label}: SE(3) 末行非法')
    r = [row[:3] for row in value[:3]]
    require(all(abs(sum(r[k][i]*r[k][j] for k in range(3)) - (i == j)) <= 1e-4
                for i in range(3) for j in range(3)), f'{label}: 旋转不正交')
    determinant = sum(r[0][i]*(r[1][(i+1)%3]*r[2][(i+2)%3] -
                                  r[1][(i+2)%3]*r[2][(i+1)%3]) for i in range(3))
    require(abs(determinant-1) <= 1e-4, f'{label}: 旋转行列式非法')


def validate_pose(report):
    se3(report['initial_T_target_source'], 'initial')
    diagnostic = report['diagnostic_T_target_source']
    # Invalid/non-finite solver results can legitimately be retained as rejected diagnostics.
    invalid_diagnostic = not report['accepted'] and report['rejection_reason'] in (
        'invalid_final_transform', 'icp_not_converged')
    matrix(diagnostic, 4, 4, 'diagnostic', nullable=invalid_diagnostic)
    if not invalid_diagnostic:
        se3(diagnostic, 'diagnostic')
    if not report['accepted']:
        return
    transform, pose = report['T_target_source'], report['pose']
    se3(transform, 'T_target_source')
    same_matrix(transform, diagnostic, 'diagnostic/T')
    matrix(pose['rotation'], 3, 3, 'pose.rotation')
    same_matrix(pose['rotation'], [row[:3] for row in transform[:3]], 'pose.rotation/T')
    t, q = pose['translation_m'], pose['quaternion_wxyz']
    require(isinstance(t, list) and len(t) == 3 and all(numeric(x) for x in t), '平移格式非法')
    same_matrix([t], [[row[3] for row in transform[:3]]], 'pose.translation/T')
    require(isinstance(q, list) and len(q) == 4 and all(numeric(x) for x in q) and
            abs(sum(x*x for x in q)-1) <= 1e-8, '四元数必须有限且归一化')
    w, x, y, z = q
    rotation = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    same_matrix(rotation, pose['rotation'], 'quaternion/rotation', tolerance=2e-4)


def command_options(command, report, row):
    argv = command['argv']
    require(isinstance(argv, list) and bool(argv) and all(isinstance(x, str) and x for x in argv),
            '命令 argv 非法')
    require(PurePosixPath(path_key(argv[0])).name in ('lidar_icp', 'lidar_icp.exe'), '命令可执行文件非法')
    defaults = {'--voxel-size': ('voxel_size_m', .2), '--max-iterations': ('max_iterations', 60),
                '--max-correspondence-distance': ('max_correspondence_distance_m', 1.),
                '--evaluation-distance': ('evaluation_distance_m', 1.),
                '--min-inliers': ('min_inliers', 3), '--min-inlier-ratio': ('min_inlier_ratio', .5),
                '--max-rmse': ('max_rmse_m', .2)}
    allowed = set(defaults) | {'--source', '--target', '--output', '--initial', '--truth'}
    require(len(argv) % 2 == 1, '命令选项缺少值')
    options = {}
    for key, value in zip(argv[1::2], argv[2::2]):
        require(key in allowed and key not in options, '命令未知或重复选项')
        options[key] = value
    for side in ('source', 'target'):
        require('--'+side in options and path_key(options['--'+side]) == path_key(report[side]),
                f'命令 {side} 与报告不一致')
        require(PurePosixPath(path_key(report[side])).name == row[side+'_frame'], 'CSV 帧路径不一致')
    require('--output' in options and PurePosixPath(path_key(options['--output'])).name == row['experiment']+'.json',
            '命令 output 与案例不一致')
    require(('--initial' in options and path_key(options['--initial']) == path_key(row['initial']))
            if row['initial'] not in ('', 'identity') else '--initial' not in options,
            '命令 initial 与 CSV 不一致')
    if '--initial' not in options:
        same_matrix(report['initial_T_target_source'], [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], '默认初值')
    for option, (key, default) in defaults.items():
        text = options.get(option, str(default))
        if option in ('--max-iterations', '--min-inliers'):
            require(text.isascii() and text.isdigit() and int(text) > 0, '命令整数参数非法')
        compare_value(text, report['configuration'][key], '命令配置:'+key, float32=option == '--voxel-size')
    for key, value in [('transformation_epsilon', 1e-8), ('euclidean_fitness_epsilon', 1e-6)]:
        require(report['configuration'][key] == value, '命令未支持修改 epsilon')
    return options


def validate_source_hashes(provenance, source_root):
    root = Path(source_root).resolve()
    hashes = provenance.get('source_sha256', {})
    policy = provenance.get('source_hash_policy', 'bytes')
    require(policy in ('bytes', 'utf8-lf'), '未知源码哈希策略')
    require(bool(hashes), '归档没有源码哈希，不能声称已核查源码')
    for name, expected in hashes.items():
        path = (root/path_key(name)).resolve()
        require(path.is_relative_to(root), '源码哈希路径越界')
        data = path.read_bytes()
        if policy == 'utf8-lf':
            data.decode('utf-8') # Canonicalize line endings only, never source content.
            data = data.replace(b'\r\n', b'\n')
        require(hashlib.sha256(data).hexdigest() == expected, f'源码哈希错误: {name}')
    return len(hashes)


def read_transform(path):
    # Match the CLI's float32 matrix-file representation before comparison.
    values = [struct.unpack('f', struct.pack('f', float(x)))[0]
              for x in Path(path).read_text(encoding='utf-8').split()]
    require(len(values) == 16, '矩阵文件必须16个数')
    result = [values[i:i+4] for i in range(0,16,4)]
    se3(result, '矩阵文件')
    return result


def rotation_quaternion(r):
    # Standard matrix-to-quaternion conversion, normalized as in pose_utils.
    trace = sum(r[i][i] for i in range(3))
    if trace > 0:
        s = 2*math.sqrt(trace+1)
        q = [s/4, (r[2][1]-r[1][2])/s, (r[0][2]-r[2][0])/s, (r[1][0]-r[0][1])/s]
    else:
        i = max(range(3), key=lambda k: r[k][k]); j, k = (i+1)%3, (i+2)%3
        s = 2*math.sqrt(1+r[i][i]-r[j][j]-r[k][k])
        q = [0.]*4; q[0] = (r[k][j]-r[j][k])/s; q[i+1] = s/4
        q[j+1] = (r[i][j]+r[j][i])/s; q[k+1] = (r[i][k]+r[k][i])/s
    norm = math.sqrt(sum(x*x for x in q))
    return [x/norm for x in q]


def validate_truth_file(report, path):
    truth = read_transform(path)
    estimated = report['T_target_source']
    translation = math.sqrt(sum((estimated[i][3]-truth[i][3])**2 for i in range(3)))
    a, b = rotation_quaternion(truth), rotation_quaternion(estimated)
    w = sum(x*y for x,y in zip(a,b))
    v = [a[0]*b[i]-a[i]*b[0]-a[j]*b[k]+a[k]*b[j]
         for i,j,k in ((1,2,3),(2,3,1),(3,1,2))]
    angle = 2*math.atan2(math.sqrt(sum(x*x for x in v)), abs(w))
    require(math.isclose(translation, report['translation_error_m'], rel_tol=1e-6, abs_tol=1e-7) and
            math.isclose(angle, report['rotation_error_rad'], rel_tol=1e-6, abs_tol=1e-7),
            'truth 文件与报告误差不一致')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_value(text, value, label, float32=False):
    if value is None:
        require(text == '', f'{label}: null 应为 CSV 空字段')
    elif isinstance(value, bool):
        require(text.lower() == str(value).lower(), f'{label}: bool 不一致')
    elif isinstance(value, (int, float)):
        same = math.isclose(float(text), value, rel_tol=1e-7, abs_tol=1e-9) if float32 else float(text) == value
        require(math.isfinite(float(text)) and same, f'{label}: 数值不一致')
    else:
        require(text == value, f'{label}: 文本不一致')


def validate_reports(metrics, check_inputs=False):
    metrics = Path(metrics)
    provenance = load_json(metrics/'provenance.json')
    inputs = {path_key(name) for name in provenance['input_sha256']}
    with (metrics/'summary.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    require(bool(rows), '没有实验行')
    reports = {}
    for row in rows:
        name = row['experiment']
        require(name not in reports and Path(name).name == name and '/' not in name and '\\' not in name,
                '重复或非法实验名称')
        report = load_json(metrics/(name+'.json'))
        command = load_json(metrics/(name+'.command.json'))
        reports[name] = report
        require(type(report['accepted']) is bool and type(report['converged']) is bool, '状态必须是 bool')
        require(report['schema_version'] == 1 and report['transform_direction'] == 'p_target = T_target_source * p_source'
                and report['units'] == {'length':'m','angle':'rad','fitness':'m^2'}, '报告方向/单位/schema 非法')
        require(command['exit_code'] == (0 if report['accepted'] else 4), f'{name}: 退出码不一致')
        compare_value(row['exit_code'], command['exit_code'], name)
        for key in ('converged', 'accepted', 'fitness_m2', 'rmse_m', 'inliers', 'inlier_ratio',
                    'elapsed_ms', 'translation_error_m', 'rotation_error_rad', 'rejection_reason'):
            compare_value(row[key], report[key], f'{name}:{key}')
        for key in ('voxel_size_m', 'max_iterations', 'max_correspondence_distance_m',
                    'evaluation_distance_m', 'max_rmse_m'):
            compare_value(row[key], report['configuration'][key], f'{name}:{key}', float32=key == 'voxel_size_m')
        for side in ('source', 'target'):
            for stage in ('input', 'output'):
                compare_value(row[f'{side}_{stage}_points'], report[f'{side}_points'][stage], name)
        require(0 <= report['inlier_ratio'] <= 1, f'{name}: 非法内点比例')
        require(report['inliers'] <= report['source_points']['output'], f'{name}: 非法内点数')
        require(math.isclose(report['inlier_ratio'], report['inliers']/report['source_points']['output'],
                             rel_tol=1e-9, abs_tol=1e-9), f'{name}: 内点比例分母错误')
        if report['accepted']:
            c = report['configuration']
            require(report['converged'] and report['pose'] is not None and report['T_target_source'] is not None,
                    f'{name}: 接受状态无位姿')
            require(report['inliers'] >= c['min_inliers'] and report['inlier_ratio'] >= c['min_inlier_ratio']
                    and report['rmse_m'] is not None and report['rmse_m'] <= c['max_rmse_m'],
                    f'{name}: 违反质量门禁')
        else:
            require(report['pose'] is None and report['T_target_source'] is None
                    and bool(report['rejection_reason']), f'{name}: 拒绝状态仍含有效位姿')
        validate_pose(report)
        options = command_options(command, report, row)
        for key in ('--source', '--target', '--initial', '--truth'):
            if key in options:
                require(path_key(options[key]) in inputs, f'{name}: 命令输入缺失溯源哈希: {key}')
        if check_inputs and '--initial' in options:
            initial = read_transform(options['--initial'])
            same_matrix(initial, report['initial_T_target_source'], '初值文件/报告', tolerance=1e-6)
        if '--truth' in options and report['accepted']:
            require(all(numeric(report[key]) and report[key] >= 0
                        for key in ('translation_error_m','rotation_error_rad')), '已测真值误差必须有限非负')
            if check_inputs:
                validate_truth_file(report, options['--truth'])
        if report['inliers'] == 0:
            require(report['rmse_m'] is None, f'{name}: 零内点 RMSE 必须为 null')
        if '--truth' not in command['argv'] or not report['accepted']:
            require(report['translation_error_m'] is None and report['rotation_error_rad'] is None,
                    f'{name}: 未知/拒绝误差不应为伪零')
        require((metrics/(name+'.stderr.txt')).is_file(), f'{name}: 缺失原始日志')
    return reports


def normalized_report(report):
    return {k: v for k, v in report.items() if k not in ('source', 'target', 'elapsed_ms')}


def alignment_check(report):
    # Optional numerical audit of the plotted raw geometry; no new ICP solver.
    import numpy as np
    from run_experiments import read_pcd, moved
    require(report['accepted'], '只检查有效配准图')
    source, target = read_pcd(report['source']), read_pcd(report['target'])
    stride = max(1, math.ceil(len(source)/1000))
    query = source[::stride]

    def nearest(points):
        distances = []
        for begin in range(0, len(points), 32):
            chunk = points[begin:begin+32]
            best = np.full(len(chunk), np.inf)
            for target_begin in range(0, len(target), 16384):
                delta = chunk[:, None, :] - target[None, target_begin:target_begin+16384, :]
                best = np.minimum(best, np.sum(delta*delta, axis=2).min(axis=1))
            distances.extend(np.sqrt(best))
        distances = np.asarray(distances)
        return {'median_nearest_m': float(np.median(distances)),
                'rmse_nearest_m': float(np.sqrt(np.mean(distances*distances)))}

    before = nearest(query)
    after = nearest(moved(query, report['T_target_source']))
    require(after['rmse_nearest_m'] < before['rmse_nearest_m'], '原始几何抽样最近邻误差未改善')
    return {'sample_stride': stride, 'source_queries': len(query), 'full_target_points': len(target),
            'before': before, 'after': after,
            'meaning': '固定原始 source 子样本到完整原始 target 的单向距离；不是 CLI 体素内点 RMSE 或车辆定位误差'}


def validate(metrics, figures, reference=None, check_inputs=True, check_alignment=False, source_root=None):
    metrics, figures = Path(metrics), Path(figures)
    reports = validate_reports(metrics, check_inputs=check_inputs)
    provenance = load_json(metrics/'provenance.json')
    sources_checked = validate_source_hashes(provenance, source_root) if source_root is not None else 0
    for name, expected in provenance['figure_sha256'].items():
        require(digest(figures/name) == expected, f'图像哈希错误: {name}')
    require(len(provenance['figure_sha256']) == 6, '应有六张实验图')
    if check_inputs:
        for name, expected in provenance['input_sha256'].items():
            require(digest(name) == expected, f'输入哈希错误: {name}')
    compared = []
    if reference is not None:
        previous = validate_reports(reference)
        for name, expected in previous.items():
            require(name in reports and normalized_report(reports[name]) == normalized_report(expected),
                    f'复验不一致（除路径/耗时）: {name}')
            compared.append(name)
        original_provenance = load_json(Path(reference)/'provenance.json')
        require(provenance['figure_sha256'] == original_provenance['figure_sha256'],
                '复绘六图与原提交不一致')
    geometry = {}
    if check_alignment:
        for name in ('synthetic_v0.02', 'kitti_v0.3'):
            geometry[name] = alignment_check(reports[name])
    return {'reports_checked': len(reports), 'figures_checked': 6,
            'source_hashes_checked': sources_checked,
            'source_verification': 'explicit_source_root' if source_root is not None else 'not_requested',
            'input_hashes_checked': len(provenance['input_sha256']) if check_inputs else 0,
            'reference_cases_matched': compared, 'alignment_checks': geometry, 'result': 'passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--figures', type=Path, required=True)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--source-root', type=Path, help='显式核查运行时源码快照；历史归档不要默认使用当前源码')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--skip-inputs', action='store_true',
                        help='只核对归档报告和图片，不声称检查未下载的原始输入哈希')
    parser.add_argument('--check-alignment', action='store_true',
                        help='用 NumPy 抽样原始几何，核对两幅对齐图的前后最近邻距离')
    args = parser.parse_args()
    result = validate(args.metrics, args.figures, args.reference, check_inputs=not args.skip_inputs,
                      check_alignment=args.check_alignment, source_root=args.source_root)
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
