"""严格转换 KITTI little-endian float32 XYZI，保留 intensity 和原始坐标。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def convert(source, output):
    source, output = Path(source), Path(output)
    if output.exists() or output.with_suffix('.conversion.json').exists():
        raise ValueError('拒绝覆盖输出')
    raw = source.read_bytes()
    if not raw or len(raw) % 16:
        raise ValueError('输入必须为非空、16 字节整数倍的 XYZI 数据')
    count = len(raw)//16
    for point in struct.iter_unpack('<4f', raw):
        if not all(math.isfinite(v) for v in point):
            raise ValueError('XYZI 含非有限值；拒绝静默丢点')
    header = ('VERSION 0.7\nFIELDS x y z intensity\nSIZE 4 4 4 4\nTYPE F F F F\n'
              f'COUNT 1 1 1 1\nWIDTH {count}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n'
              f'POINTS {count}\nDATA binary\n').encode('ascii')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as f:
        f.write(header+raw)
    report = {'input_file': source.name, 'points': count, 'input_bytes': len(raw),
              'input_sha256': hashlib.sha256(raw).hexdigest(),
              'output_sha256': hashlib.sha256(header+raw).hexdigest(),
              'format': 'little-endian float32 XYZI; binary PCD',
              'units': 'XYZ metres; intensity unchanged',
              'frame': 'Velodyne: x forward, y left, z up',
              'coordinates_changed': False, 'motion_compensation_applied': False}
    output.with_suffix('.conversion.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(convert(args.input, args.output), indent=2))
