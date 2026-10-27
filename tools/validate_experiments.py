"""离线核对实验 CSV/JSON、门禁、输入/图像哈希和参考归档；不访问网络。"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


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


def validate_reports(metrics):
    metrics = Path(metrics)
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


def validate(metrics, figures, reference=None, check_inputs=True, check_alignment=False):
    metrics, figures = Path(metrics), Path(figures)
    reports = validate_reports(metrics)
    provenance = load_json(metrics/'provenance.json')
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
            'input_hashes_checked': len(provenance['input_sha256']) if check_inputs else 0,
            'reference_cases_matched': compared, 'alignment_checks': geometry, 'result': 'passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--figures', type=Path, required=True)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--skip-inputs', action='store_true',
                        help='只核对归档报告和图片，不声称检查未下载的原始输入哈希')
    parser.add_argument('--check-alignment', action='store_true',
                        help='用 NumPy 抽样原始几何，核对两幅对齐图的前后最近邻距离')
    args = parser.parse_args()
    result = validate(args.metrics, args.figures, args.reference, check_inputs=not args.skip_inputs,
                      check_alignment=args.check_alignment)
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
