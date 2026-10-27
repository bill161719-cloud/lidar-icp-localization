"""从 AWS 公共 KITTI ZIP 按范围获取两个相邻帧；禁止整包降级下载。"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.request
import zipfile
import zlib

URL = ('https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/'
       '2011_09_26_drive_0005/2011_09_26_drive_0005_sync.zip')
PREFIX = '2011_09_26/2011_09_26_drive_0005_sync/velodyne_points/'
NAMES = [PREFIX + 'data/0000000000.bin', PREFIX + 'data/0000000001.bin',
         PREFIX + 'timestamps.txt']


def fetch(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / Path(n).name for n in NAMES]
    if any(p.exists() for p in paths + [output / 'download.json']):
        raise ValueError('拒绝覆盖已有下载')
    requests = []
    etag = None

    def get_range(value):
        nonlocal etag
        headers = {'Range': 'bytes=' + value}
        if etag:
            headers['If-Match'] = etag
        with urllib.request.urlopen(urllib.request.Request(URL, headers=headers), timeout=45) as r:
            if r.status != 206:
                raise RuntimeError('服务器未返回 206；拒绝下载完整 ZIP')
            current = r.headers['ETag']
            if etag and current != etag:
                raise RuntimeError('远程 ZIP 已改变')
            etag = current
            size = int(r.headers['Content-Length'])
            content_range = r.headers['Content-Range']
            if not content_range.startswith('bytes '):
                raise RuntimeError('非法 Content-Range')
            span, total = content_range[6:].split('/')
            start, end = map(int, span.split('-'))
            if value.startswith('-'):
                expected = (max(0, int(total)-int(value[1:])), int(total)-1)
            else:
                expected = tuple(map(int, value.split('-')))
            if (start, end) != expected or size != end-start+1 or size > 8*1024*1024:
                raise RuntimeError('响应范围不符或范围过大')
            body = r.read(size+1)
            if len(body) != size:
                raise RuntimeError('范围读取长度不符')
            requests.append({'range': value, 'content_range': content_range, 'bytes': size})
            return body

    tail = get_range('-65536')
    offset = tail.rfind(b'PK\x05\x06')
    if offset < 0:
        raise RuntimeError('未找到 ZIP EOCD')
    fields = struct.unpack_from('<4s4H2IH', tail, offset)
    _, disk, cd_disk, disk_count, count, cd_size, cd_offset, comment_len = fields
    if disk or cd_disk or count != disk_count or count == 65535:
        raise RuntimeError('不支持分卷或 ZIP64')
    central = get_range(f'{cd_offset}-{cd_offset+cd_size-1}')
    # zipfile only reads this synthetic central-directory container, not entry data.
    eocd = struct.pack('<4s4H2IH', b'PK\x05\x06', 0, 0, count, count, cd_size, 0, 0)
    with zipfile.ZipFile(io.BytesIO(central+eocd)) as archive:
        infos = [archive.getinfo(n) for n in NAMES]
    records = []
    for info, path in zip(infos, paths):
        local = get_range(f'{info.header_offset}-{info.header_offset+29}')
        header = struct.unpack('<4s5H3I2H', local)
        if header[0] != b'PK\x03\x04' or header[2] & 1:
            raise RuntimeError('不支持加密或无效 ZIP 条目')
        start = info.header_offset + 30 + header[-2] + header[-1]
        packed = get_range(f'{start}-{start+info.compress_size-1}')
        if info.compress_type == zipfile.ZIP_DEFLATED:
            raw = zlib.decompress(packed, -15)
        elif info.compress_type == zipfile.ZIP_STORED:
            raw = packed
        else:
            raise RuntimeError('不支持压缩方法')
        if len(raw) != info.file_size or zlib.crc32(raw) != info.CRC:
            raise RuntimeError('CRC/文件长度不匹配')
        path.write_bytes(raw)
        records.append({'entry': info.filename, 'file': path.name, 'bytes': len(raw),
                        'crc32': f'{info.CRC:08x}', 'sha256': hashlib.sha256(raw).hexdigest()})
    manifest = {'url': URL, 'etag': etag, 'files': records, 'requests': requests,
                'downloaded_bytes': sum(r['bytes'] for r in requests),
                'license': 'CC BY-NC-SA 3.0',
                'source': 'https://registry.opendata.aws/kitti/'}
    (output/'download.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(fetch(args.output), indent=2))
