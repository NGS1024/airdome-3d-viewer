"""
╔══════════════════════════════════════════════════════════╗
║       AIR DOME 3D Simulator - PDF 분석 모듈              ║
║                    OzoMeta Architecture                  ║
╚══════════════════════════════════════════════════════════╝

PDF 도면에서 텍스트를 추출하고 치수 패턴을 검색합니다.
- PyMuPDF (fitz): PDF 텍스트 추출 + 이미지 변환
- pytesseract + Pillow: OCR (Tesseract 설치 시)
- 파일명 기반 추출: 최후 수단
"""

import os
import re
import sys
import subprocess

from config import DOME_KEYWORDS

# ── 라이브러리 자동 설치 및 임포트 ──
def _auto_install(pkg_name, import_name=None):
    """패키지 자동 설치 시도"""
    try:
        __import__(import_name or pkg_name)
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg_name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# PyMuPDF (PDF 열기 + 이미지 변환)
_auto_install("PyMuPDF", "fitz")
HAS_FITZ = False
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# pytesseract + Pillow (OCR - Tesseract가 설치되어 있을 때 사용)
_auto_install("pytesseract")
_auto_install("Pillow", "PIL")
HAS_TESSERACT = False
try:
    import pytesseract
    from PIL import Image
    import io
    # Tesseract 실행 파일 경로 자동 탐색 (Windows)
    if sys.platform == 'win32':
        tess_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        ]
        for tp in tess_paths:
            if os.path.exists(tp):
                pytesseract.pytesseract.tesseract_cmd = tp
                break
    # 테스트 호출
    pytesseract.get_tesseract_version()
    HAS_TESSERACT = True
except Exception:
    HAS_TESSERACT = False


class PDFAnalyzer:
    """PDF 도면에서 텍스트 추출 및 치수 패턴 검색"""

    @staticmethod
    def scan_folder(folder_path):
        """폴더에서 PDF 파일 목록 반환"""
        pdfs = []
        for f in sorted(os.listdir(folder_path)):
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(folder_path, f))
        return pdfs

    @staticmethod
    def extract_text(pdf_path):
        """PDF에서 텍스트 추출 (PyMuPDF 텍스트 + Tesseract OCR)"""
        all_text = ""

        if not HAS_FITZ:
            fname = os.path.basename(pdf_path)
            return f"[PyMuPDF 미설치] pip install PyMuPDF 실행 필요\n{fname}"

        try:
            doc = fitz.open(pdf_path)
            is_image_pdf = True

            for page in doc:
                # ── 방법 1: 일반 텍스트 추출 ──
                t = page.get_text("text") or ""
                if len(t.strip()) > 20:
                    is_image_pdf = False
                all_text += t + "\n"

                # ── 방법 2: dict 모드 ──
                if len(t.strip()) < 10:
                    try:
                        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                        for block in blocks.get("blocks", []):
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    txt = span.get("text", "").strip()
                                    if txt:
                                        all_text += txt + " "
                                        if len(txt) > 5:
                                            is_image_pdf = False
                        all_text += "\n"
                    except Exception:
                        pass

            # ── 방법 3: OCR (이미지 PDF일 때) ──
            if (is_image_pdf or len(all_text.strip()) < 20) and HAS_TESSERACT and HAS_FITZ:
                try:
                    ocr_text = ""
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        mat = fitz.Matrix(200/72, 200/72)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")

                        img = Image.open(io.BytesIO(img_data))
                        ocr_result = pytesseract.image_to_string(img)
                        if ocr_result:
                            ocr_text += ocr_result + "\n"

                        pix = None
                        img = None

                    if len(ocr_text.strip()) > 10:
                        all_text = ocr_text

                except Exception:
                    pass

            doc.close()

        except Exception as e:
            all_text += f"[PDF 열기 실패: {e}]"

        # ── 방법 4: 파일명에서 추출 (최후 수단) ──
        if len(all_text.strip()) < 10:
            fname = os.path.basename(pdf_path)
            all_text += f"\n[파일명에서 추출] {fname}\n"
            for m in re.finditer(r'(\d{3,6})', fname):
                all_text += f" {m.group(1)}"

        return all_text if all_text.strip() else "[텍스트 추출 실패]"

    @staticmethod
    def find_dimensions(text):
        """텍스트에서 치수 패턴 검색 (다양한 포맷 지원)"""
        results = {
            'dimensions_mm': [],
            'dimensions_m': [],
            'dimensions_ft': [],
            'dimensions_raw': [],
            'project_info': [],
            'dome_keywords': []
        }

        # mm 단위 치수 (예: 43,282mm, 15850mm, 43,282 mm)
        for m in re.finditer(r'(\d[\d,]*\.?\d*)\s*(?:mm|MM)', text):
            val = m.group(1).replace(',', '')
            try:
                results['dimensions_mm'].append(float(val))
            except ValueError:
                pass

        # m 단위 치수 (예: 43.282m, 68.58m)
        for m in re.finditer(r'(\d+\.?\d*)\s*(?:meters?|m\b|M\b)', text):
            try:
                results['dimensions_m'].append(float(m.group(1)))
            except ValueError:
                pass

        # ft/인치 단위 (미국 도면 - 예: 142'-0", 225', 52'-0")
        for m in re.finditer(r"(\d+)['\u2019]\s*-?\s*(\d*)[\"″]?", text):
            try:
                ft = float(m.group(1))
                inch = float(m.group(2)) if m.group(2) else 0
                mm_val = (ft * 12 + inch) * 25.4
                if mm_val > 1000:
                    results['dimensions_ft'].append(mm_val)
                    results['dimensions_mm'].append(mm_val)
            except ValueError:
                pass

        # 소수점 포함 숫자 → m 단위 추정 (예: 15.850, 40.000, 68.580)
        for m in re.finditer(r'(?<!\d)(\d{1,3}\.\d{3})(?!\d)', text):
            try:
                v = float(m.group(1))
                if 1.0 <= v <= 200.0:
                    mm_val = v * 1000
                    results['dimensions_m'].append(v)
                    results['dimensions_mm'].append(mm_val)
            except ValueError:
                pass

        # 단위 없는 큰 숫자 (건축 도면에서 mm 단위로 추정, 쉼표 포함)
        for m in re.finditer(r'(?<!\d)(\d{1,3}(?:,\d{3})+)(?!\d)', text):
            val = m.group(1).replace(',', '')
            try:
                v = float(val)
                if 1000 <= v <= 200000:
                    results['dimensions_raw'].append(v)
            except ValueError:
                pass

        # 단위 없는 4~6자리 숫자 (mm 추정)
        for m in re.finditer(r'(?<![,.\d])(\d{4,6})(?![,.\d])', text):
            try:
                v = float(m.group(1))
                if 1000 <= v <= 200000:
                    results['dimensions_raw'].append(v)
            except ValueError:
                pass

        # 프로젝트 정보
        for m in re.finditer(r'(?:Project|BDW|project|NCWC|Broadwell)[:\s]*([A-Za-z0-9\-\s]+)', text):
            results['project_info'].append(m.group(0).strip())

        # 돔 관련 키워드
        text_lower = text.lower()
        for kw in DOME_KEYWORDS:
            if kw.lower() in text_lower:
                results['dome_keywords'].append(kw)

        return results
