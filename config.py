"""
╔══════════════════════════════════════════════════════════╗
║       AIR DOME 3D Simulator - 설정 모듈                  ║
║                    OzoMeta Architecture                  ║
╚══════════════════════════════════════════════════════════╝

앱 전체에서 사용되는 디자인 토큰, 기본값, 상수를 관리합니다.
"""

# ── 버전 정보 ──
APP_VERSION = "R13"
APP_TITLE = "AIR DOME 3D Simulator - 에어돔 3D 시뮬레이터"
APP_SUBTITLE = "에어돔 구조 시뮬레이션 및 3D 모델링 도구  |  OzoMeta"

# ── 윈도우 설정 ──
WINDOW_WIDTH = 760
WINDOW_HEIGHT = 870

# ── 디자인 토큰 (다크 테마) ──
class Theme:
    BG      = "#1a1d26"   # 앱 전체 배경
    PANEL   = "#20253a"   # 패널/카드 배경
    CARD    = "#262d40"   # 버튼·입력 배경 (약간 밝은 층)
    BORDER  = "#2e3450"   # 구분선·테두리
    ACCENT  = "#4a9ec8"   # 메인 액센트 (스틸 블루)
    TEXT    = "#ccd4e0"   # 기본 텍스트
    MUTED   = "#5c6880"   # 보조 텍스트
    INP_BG  = "#1c2133"   # 입력 필드 배경
    INP_FG  = "#7ec8e3"   # 입력 필드 텍스트 (밝은 청록)
    HDR     = "#12151e"   # 헤더 바 배경

# ── 돔 기본 파라미터 ──
class DomeDefaults:
    PROJECT_NAME = "Air Dome Project"
    WIDTH = 0           # mm (단변 스팬)
    LENGTH = 0          # mm (장변 길이)
    HEIGHT = 0          # mm (정상부 높이)
    CABLE_SPACING = 3600  # mm (케이블 간격)
    FOUNDATION_DEPTH = 500  # mm (기초 깊이)
    DOME_TYPE = "Rectangular"
    DOME_TYPES = ["Rectangular", "Oval/Elliptical", "Circular"]

# ── B-Spline 기본 설정 (STEP 내보내기) ──
class StepDefaults:
    NU = 13             # U 방향 제어점 수
    NV = 19             # V 방향 제어점 수
    DEGREE_U = 3        # U 방향 차수
    DEGREE_V = 3        # V 방향 차수

# ── 3D 뷰어 설정 ──
class ViewerDefaults:
    MESH_RESOLUTION = 80  # 돔 메쉬 해상도

# ── STL 내보내기 설정 ──
class StlDefaults:
    RESOLUTION = 80     # 삼각형 메쉬 해상도

# ── 일조 시뮬레이션 기본 설정 ──
class SolarDefaults:
    LATITUDE = 37.5665      # 서울 기본 위도
    LONGITUDE = 126.9780    # 서울 기본 경도
    TIMEZONE_OFFSET = 9     # KST (UTC+9)
    DEFAULT_ADDRESS = "서울특별시 중구 세종대로 110"

# ── 돔 관련 키워드 (PDF 분석용) ──
DOME_KEYWORDS = [
    'dome', 'air dome', 'membrane', 'cable', 'inflation',
    'PVDF', 'air-supported', 'broadwell', 'tennis', 'center',
    'elevation', 'section', 'plan', 'detail',
    '에어돔', '막구조', '단면', '입면', '평면'
]
