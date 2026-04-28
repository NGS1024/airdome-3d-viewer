"""
╔══════════════════════════════════════════════════════════╗
║       AIR DOME 3D Simulator - STL 내보내기 모듈          ║
║                    OzoMeta Architecture                  ║
╚══════════════════════════════════════════════════════════╝

에어돔 3D 곡면을 바이너리 STL 파일로 내보냅니다.
- 80x80 해상도 삼각형 메쉬 (약 12,800 삼각형)
- 노멀 벡터 자동 계산
- 바이너리 STL 포맷 (50바이트 헤더 + 삼각형 데이터)
"""

import math
import struct

from config import StlDefaults


class STLExporter:
    """에어돔 3D 곡면을 바이너리 STL 파일로 내보내기"""

    @staticmethod
    def export(filepath, width, length, height, resolution=None):
        """STL 바이너리 파일 내보내기

        Args:
            filepath: 저장 경로
            width: 돔 폭 (mm)
            length: 돔 길이 (mm)
            height: 돔 높이 (mm)
            resolution: 메쉬 해상도 (기본 80)

        Returns:
            생성된 삼각형 수
        """
        res = resolution or StlDefaults.RESOLUTION
        a_val, b_val = width / 2, length / 2

        def dz(x, y):
            rx = 1 - (x / a_val) ** 2
            ry = 1 - (y / b_val) ** 2
            return height * math.sqrt(max(rx, 0)) * math.sqrt(max(ry, 0))

        us = [a_val * (-1 + 2 * i / res) for i in range(res + 1)]
        vs = [b_val * (-1 + 2 * j / res) for j in range(res + 1)]

        tris = []
        for j in range(res):
            for i in range(res):
                p = [(us[i + di], vs[j + dj], dz(us[i + di], vs[j + dj]))
                     for di, dj in [(0, 0), (1, 0), (1, 1), (0, 1)]]
                for t in [(p[0], p[1], p[2]), (p[0], p[2], p[3])]:
                    v1 = [t[1][k] - t[0][k] for k in range(3)]
                    v2 = [t[2][k] - t[0][k] for k in range(3)]
                    n = [
                        v1[1] * v2[2] - v1[2] * v2[1],
                        v1[2] * v2[0] - v1[0] * v2[2],
                        v1[0] * v2[1] - v1[1] * v2[0]
                    ]
                    nl = math.sqrt(sum(x * x for x in n))
                    if nl > 0:
                        n = [x / nl for x in n]
                    tris.append((n, t[0], t[1], t[2]))

        with open(filepath, 'wb') as f:
            hdr = b'AirDome STL Export'
            f.write(hdr + b'\0' * (80 - len(hdr)))
            f.write(struct.pack('<I', len(tris)))
            for n, v1, v2, v3 in tris:
                f.write(struct.pack('<3f', *n))
                for v in [v1, v2, v3]:
                    f.write(struct.pack('<3f', *v))
                f.write(struct.pack('<H', 0))

        return len(tris)
