╔══════════════════════════════════════════════════════════╗
║       AIR DOME 3D Simulator R13 - 설치 가이드            ║
║                    OzoMeta Architecture                  ║
╚══════════════════════════════════════════════════════════╝

■ 버전 정보
  - R13: 모듈 분리 버전
  - R12에서 단일 파일(3,487줄)이었던 코드를 7개 모듈로 분리

■ 모듈 구조
  AirDome_3D_Viewer_R13/
  ├── main.py              ← 실행 진입점 (메인 GUI)
  ├── config.py            ← 설정, 테마, 기본값
  ├── pdf_analyzer.py      ← PDF 도면 분석 (OCR 포함)
  ├── viewer_3d.py         ← 3D 미리보기 (Three.js HTML)
  ├── catia_exporter.py    ← CATIA STEP 내보내기
  ├── stl_exporter.py      ← STL 파일 내보내기
  ├── simulation.py        ← 구조 시뮬레이션 (Three.js HTML)
  ├── AirDome3DViewer_실행.bat  ← 실행 배치파일
  ├── logo.png             ← 로고 이미지
  └── AirDome_시뮬레이션_기술해설서.pdf  ← 기술해설서

■ 실행 방법
  1. AirDome3DViewer_실행.bat 더블클릭
  또는
  2. 명령 프롬프트에서: python main.py

■ 필요 환경
  - Python 3.8 이상
  - tkinter (Python 기본 포함)

■ 선택 라이브러리 (자동 설치 시도됨)
  - PyMuPDF (pip install PyMuPDF) : PDF 텍스트 추출
  - Pillow (pip install Pillow) : 이미지 처리
  - pytesseract (pip install pytesseract) : OCR
    → Tesseract-OCR 프로그램이 별도로 설치되어 있어야 함

■ 기능별 모듈 설명
  1. [3D 미리보기] → viewer_3d.py
     Three.js 기반 웹 브라우저 3D 돔 뷰어

  2. [CATIA로 내보내기] → catia_exporter.py
     STEP AP214 형식으로 CATIA 호환 3D 파일 생성
     분리된 Body: DomeSurface, Foundation, CableNet, GroundPlane

  3. [STL 파일 내보내기] → stl_exporter.py
     바이너리 STL 형식 3D 메쉬 파일 생성

  4. [구조 시뮬레이션] → simulation.py
     삼중막 구조 해석, 하중 조합, 케이블 해석

■ 리비전 관리
  - 코드 수정 시 새 폴더(R14, R15...)를 생성하여 관리
  - 이전 버전은 그대로 유지
  - 각 모듈은 독립적으로 수정 가능

■ 변경 이력
  R12 → R13: 단일 파일을 7개 모듈로 분리 (기능 동일)
