"""
╔══════════════════════════════════════════════════════════╗
║       AIR DOME 3D Simulator - 메인 애플리케이션          ║
║                    OzoMeta Architecture                  ║
╚══════════════════════════════════════════════════════════╝

사용법:
  1. 프로그램 실행 → PDF 도면 폴더 선택
  2. PDF 목록에서 도면 확인
  3. 파라미터 입력 (폭, 길이, 높이, 돔 타입)
  4. [3D 미리보기] 클릭 → 브라우저에서 3D 돔 확인
  5. [CATIA로 내보내기] 클릭 → CATIA용 STP 파일 생성
  6. [STL 내보내기] 클릭 → 3D 프린팅용 STL 파일 생성
  7. [구조 시뮬레이션] 클릭 → 브라우저에서 구조 해석

모듈 구조 (R13):
  - config.py          : 설정, 테마, 기본값
  - pdf_analyzer.py    : PDF 도면 분석
  - viewer_3d.py       : 3D 미리보기 (Three.js HTML 생성)
  - catia_exporter.py  : CATIA STEP 내보내기
  - stl_exporter.py    : STL 파일 내보내기
  - simulation.py      : 구조 시뮬레이션 (Three.js HTML 생성)
  - main.py            : 메인 GUI 애플리케이션 (이 파일)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import webbrowser
import tempfile
import threading
import shutil

# ── 모듈 import ──
from config import (
    APP_TITLE, APP_SUBTITLE, APP_VERSION,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    Theme, DomeDefaults
)
from pdf_analyzer import PDFAnalyzer, HAS_FITZ
from viewer_3d import generate_viewer_html
from catia_exporter import STEPExporter
from stl_exporter import STLExporter
from simulation import generate_simulation_html
from solar_simulation import generate_solar_simulation_html


class AirDomeViewer(tk.Tk):
    """메인 GUI 애플리케이션 (Tkinter)"""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg=Theme.BG)
        self.resizable(True, True)

        self.pdf_folder = tk.StringVar(value="")
        self.pdf_files = []
        self.analysis_results = {}

        # Parameters
        self.param_project = tk.StringVar(value=DomeDefaults.PROJECT_NAME)
        self.param_width = tk.DoubleVar(value=DomeDefaults.WIDTH)
        self.param_length = tk.DoubleVar(value=DomeDefaults.LENGTH)
        self.param_height = tk.DoubleVar(value=DomeDefaults.HEIGHT)
        self.param_dome_type = tk.StringVar(value=DomeDefaults.DOME_TYPE)
        self.param_cable_spacing = tk.DoubleVar(value=DomeDefaults.CABLE_SPACING)
        self.param_foundation_depth = tk.DoubleVar(value=DomeDefaults.FOUNDATION_DEPTH)
        self._build_ui()

    def _build_ui(self):
        # ── 디자인 토큰 로컬 참조 ──
        BG = Theme.BG
        PANEL = Theme.PANEL
        CARD = Theme.CARD
        BORDER = Theme.BORDER
        ACCENT = Theme.ACCENT
        TEXT = Theme.TEXT
        MUTED = Theme.MUTED
        INP_BG = Theme.INP_BG
        INP_FG = Theme.INP_FG
        HDR = Theme.HDR

        self.configure(bg=BG)

        # ── 헤더 바 ──
        title_frame = tk.Frame(self, bg=HDR, pady=11)
        title_frame.pack(fill=tk.X)
        tk.Frame(self, bg=ACCENT, height=1).pack(fill=tk.X)

        title_inner = tk.Frame(title_frame, bg=HDR)
        title_inner.pack()

        # 로고 로딩
        try:
            from PIL import Image, ImageTk
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_h = 44
                ratio = logo_h / logo_img.height
                logo_w = int(logo_img.width * ratio)
                logo_img = logo_img.resize((logo_w, logo_h), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(logo_img)
                tk.Label(title_inner, image=self._logo_photo, bg=HDR).pack(side=tk.LEFT, padx=(0, 14))
        except Exception:
            pass

        title_text_frame = tk.Frame(title_inner, bg=HDR)
        title_text_frame.pack(side=tk.LEFT)
        tk.Label(title_text_frame, text="AIR DOME 3D Simulator",
                 font=("Segoe UI", 17, "bold"), fg="#e8edf5", bg=HDR).pack(anchor="w")
        tk.Label(title_text_frame, text=APP_SUBTITLE,
                 font=("Segoe UI", 8), fg=MUTED, bg=HDR).pack(anchor="w")

        # ── 메인 레이아웃 ──
        main = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                              bg=BORDER, sashwidth=3, sashrelief=tk.FLAT)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ── 왼쪽 패널 ──
        left = tk.Frame(main, bg=BG)
        main.add(left, width=340)

        # 폴더 선택
        folder_frame = tk.LabelFrame(left, text="  PDF 도면 폴더",
                                     font=("Segoe UI", 9, "bold"),
                                     fg=MUTED, bg=PANEL,
                                     bd=0, relief=tk.FLAT,
                                     padx=10, pady=8)
        folder_frame.pack(fill=tk.X, padx=6, pady=(6, 3))

        tk.Button(folder_frame, text="폴더 선택", command=self._select_folder,
                  bg=ACCENT, fg="#0d1117", font=("Segoe UI", 9, "bold"),
                  relief=tk.FLAT, padx=14, pady=4,
                  cursor="hand2").pack(side=tk.LEFT)
        self.folder_label = tk.Label(folder_frame, textvariable=self.pdf_folder,
                                     fg=MUTED, bg=PANEL, font=("Segoe UI", 8),
                                     wraplength=220, anchor="w")
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        # PDF 목록
        list_frame = tk.LabelFrame(left, text="  PDF 파일 목록",
                                   font=("Segoe UI", 9, "bold"),
                                   fg=MUTED, bg=PANEL,
                                   bd=0, relief=tk.FLAT,
                                   padx=6, pady=6)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)

        self.pdf_listbox = tk.Listbox(list_frame,
                                       bg=INP_BG, fg=TEXT,
                                       selectbackground=ACCENT,
                                       selectforeground="#0d1117",
                                       font=("Segoe UI", 9),
                                       relief=tk.FLAT, borderwidth=0,
                                       activestyle="none")
        self.pdf_listbox.pack(fill=tk.BOTH, expand=True)
        self.pdf_listbox.bind('<<ListboxSelect>>', self._on_pdf_select)

        # PDF 버튼
        pdf_btn_frame = tk.Frame(left, bg=BG)
        pdf_btn_frame.pack(fill=tk.X, padx=6, pady=(3, 3))

        self.btn_open_pdf = tk.Button(pdf_btn_frame, text="도면 열기",
                                       command=self._open_selected_pdf,
                                       bg=CARD, fg=TEXT,
                                       font=("Segoe UI", 9),
                                       relief=tk.FLAT, pady=5, cursor="hand2")
        self.btn_open_pdf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_apply_dims = tk.Button(pdf_btn_frame, text="치수 적용",
                                         command=self._apply_pdf_dims,
                                         bg=ACCENT, fg="#0d1117",
                                         font=("Segoe UI", 9, "bold"),
                                         relief=tk.FLAT, pady=5, cursor="hand2")
        self.btn_apply_dims.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        self._current_pdf_dims = []

        # 분석 결과 텍스트
        self.analysis_text = tk.Text(left, height=7,
                                     bg=PANEL, fg=MUTED,
                                     font=("Consolas", 8),
                                     relief=tk.FLAT, padx=10, pady=6, bd=0)
        self.analysis_text.pack(fill=tk.X, padx=6, pady=(0, 6))

        # ── 오른쪽 패널 ──
        right = tk.Frame(main, bg=BG)
        main.add(right)

        # 파라미터 섹션
        param_frame = tk.LabelFrame(right, text="  돔 파라미터",
                                    font=("Segoe UI", 9, "bold"),
                                    fg=MUTED, bg=PANEL,
                                    bd=0, relief=tk.FLAT,
                                    padx=14, pady=10)
        param_frame.pack(fill=tk.X, padx=6, pady=(6, 3))

        params = [
            ("프로젝트명", self.param_project, "str"),
            ("폭  Width (mm)", self.param_width, "float"),
            ("길이  Length (mm)", self.param_length, "float"),
            ("높이  Height (mm)", self.param_height, "float"),
            ("케이블 간격 (mm)", self.param_cable_spacing, "float"),
            ("기초 깊이 (mm)", self.param_foundation_depth, "float"),
        ]

        for i, (label, var, vtype) in enumerate(params):
            tk.Label(param_frame, text=label,
                     fg=MUTED, bg=PANEL,
                     font=("Segoe UI", 9), anchor="e"
                     ).grid(row=i, column=0, sticky="e", pady=2, padx=(0, 10))
            entry = tk.Entry(param_frame, textvariable=var,
                           font=("Segoe UI", 10, "bold"),
                           bg=INP_BG, fg=INP_FG,
                           relief=tk.FLAT, insertbackground=ACCENT)
            entry.grid(row=i, column=1, sticky="ew", pady=2, ipady=3)

        tk.Label(param_frame, text="돔 타입",
                 fg=MUTED, bg=PANEL,
                 font=("Segoe UI", 9), anchor="e"
                 ).grid(row=len(params), column=0, sticky="e", pady=2, padx=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=INP_BG,
                        background=INP_BG,
                        foreground=INP_FG,
                        selectbackground=ACCENT,
                        selectforeground="#0d1117",
                        bordercolor=Theme.BORDER,
                        arrowcolor=ACCENT)

        dome_type_cb = ttk.Combobox(param_frame, textvariable=self.param_dome_type,
                                     values=DomeDefaults.DOME_TYPES,
                                     font=("Segoe UI", 9), state="readonly",
                                     style="Dark.TCombobox")
        dome_type_cb.grid(row=len(params), column=1, sticky="ew", pady=2)
        param_frame.columnconfigure(1, weight=1)

        # 산출값 섹션
        calc_frame = tk.LabelFrame(right, text="  산출값",
                                   font=("Segoe UI", 9, "bold"),
                                   fg=MUTED, bg=PANEL,
                                   bd=0, relief=tk.FLAT,
                                   padx=14, pady=10)
        calc_frame.pack(fill=tk.X, padx=6, pady=3)

        self.calc_text = tk.Text(calc_frame, height=5,
                                 bg=INP_BG, fg=INP_FG,
                                 font=("Consolas", 9),
                                 relief=tk.FLAT, padx=10, pady=6)
        self.calc_text.pack(fill=tk.X)
        self._update_calcs()

        for var in [self.param_width, self.param_length, self.param_height]:
            var.trace_add("write", lambda *_: self._update_calcs())

        # ── 액션 버튼 ──
        action_frame = tk.Frame(right, bg=BG, pady=4)
        action_frame.pack(fill=tk.X, padx=6)

        def _btn(text, cmd, bg_c, fg_c, pad=9):
            tk.Button(action_frame, text=text, command=cmd,
                      bg=bg_c, fg=fg_c,
                      font=("Segoe UI", 11, "bold"),
                      relief=tk.FLAT, pady=pad,
                      cursor="hand2").pack(fill=tk.X, pady=2)

        _btn("🌐   3D 미리보기",       self._preview_3d,   "#1a3f2e", "#4ade80")
        _btn("📦   CATIA로 내보내기",  self._export_step,  "#1a2f4a", "#60a5fa")
        _btn("📊   STL 파일 내보내기", self._export_stl,   "#221a35", "#c084fc", pad=7)

        # 구조 시뮬레이션 구분
        tk.Frame(action_frame, bg=Theme.BORDER, height=1).pack(fill=tk.X, pady=(10, 4))
        tk.Label(action_frame, text="구조 시뮬레이션",
                 fg=MUTED, bg=BG,
                 font=("Segoe UI", 8, "bold")).pack(pady=(0, 2))

        _btn("🔬   구조 시뮬레이션",   self._simulation_3d, "#3a1515", "#f87171")

        # 일조 시뮬레이션 구분
        tk.Frame(action_frame, bg=Theme.BORDER, height=1).pack(fill=tk.X, pady=(10, 4))
        tk.Label(action_frame, text="일조 시뮬레이션",
                 fg=MUTED, bg=BG,
                 font=("Segoe UI", 8, "bold")).pack(pady=(0, 2))

        _btn("☀️   일조 시뮬레이션",   self._solar_simulation, "#3a2a10", "#f59e0b")

        # ── 상태 바 ──
        self.status_var = tk.StringVar(value="폴더를 선택하여 시작하세요")
        tk.Frame(self, bg=Theme.BORDER, height=1).pack(fill=tk.X, side=tk.BOTTOM)
        status_bar = tk.Label(self, textvariable=self.status_var,
                              bg="#0f1219", fg=MUTED,
                              font=("Segoe UI", 8), anchor="w", padx=12, pady=4)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ================================================================
    #  폴더 선택 및 PDF 분석
    # ================================================================
    def _select_folder(self):
        folder = filedialog.askdirectory(title="PDF 도면이 있는 폴더를 선택하세요")
        if folder:
            self.pdf_folder.set(folder)
            self.pdf_files = PDFAnalyzer.scan_folder(folder)
            self.pdf_listbox.delete(0, tk.END)
            for f in self.pdf_files:
                self.pdf_listbox.insert(tk.END, "  📄 " + os.path.basename(f))
            self.status_var.set(f"⏳ {len(self.pdf_files)}개 PDF 분석 중...")
            self.update_idletasks()

            thread = threading.Thread(
                target=self._auto_analyze_folder_background,
                daemon=True
            )
            thread.start()

    def _auto_analyze_folder_background(self):
        """백그라운드 스레드에서 폴더 내 모든 PDF 분석"""
        all_dims_mm = []
        all_dims_m = []
        all_keywords = []
        all_project = []
        all_dims_raw = []

        for pdf_path in self.pdf_files:
            text = PDFAnalyzer.extract_text(pdf_path)
            results = PDFAnalyzer.find_dimensions(text)
            all_dims_mm.extend(results['dimensions_mm'])
            all_dims_m.extend(results['dimensions_m'])
            all_dims_raw.extend(results.get('dimensions_raw', []))
            all_keywords.extend(results['dome_keywords'])
            all_project.extend(results['project_info'])

        all_dims_combined = list(set(all_dims_mm))
        for d in all_dims_raw:
            if d not in all_dims_combined:
                all_dims_combined.append(d)
        for d in all_dims_m:
            if d < 200:
                all_dims_combined.append(d * 1000)

        self.after(0, lambda: self._apply_folder_analysis(
            all_dims_combined, all_keywords, all_project
        ))

    def _apply_folder_analysis(self, all_dims_combined, all_keywords, all_project):
        """폴더 분석 결과를 UI에 적용 (메인 스레드)"""
        if all_dims_combined:
            sorted_dims = sorted(set(all_dims_combined), reverse=True)
            dome_dims = [d for d in sorted_dims if 5000 <= d <= 150000]

            best_length, best_width, best_height = None, None, None

            if len(dome_dims) >= 3:
                dim_counts = {}
                for d in all_dims_combined:
                    for existing in dim_counts:
                        if abs(d - existing) / max(existing, 1) < 0.03:
                            dim_counts[existing] += 1
                            break
                    else:
                        dim_counts[d] = 1

                best_score = -1
                candidates = dome_dims[:12]

                for i, L in enumerate(candidates):
                    for j, W in enumerate(candidates):
                        if j <= i:
                            continue
                        if W > L:
                            continue
                        lw_ratio = L / W
                        if not (0.8 <= lw_ratio <= 3.0):
                            continue
                        for k, H in enumerate(candidates):
                            if k <= j:
                                continue
                            hw_ratio = H / W
                            if not (0.15 <= hw_ratio <= 0.55):
                                continue
                            lw_score = 1.0 - abs(lw_ratio - 1.6) / 2.0
                            hw_score = 1.0 - abs(hw_ratio - 0.37) / 0.5
                            freq_bonus = sum(dim_counts.get(d, 1) for d in [L, W, H]) * 0.05
                            score = lw_score + hw_score + freq_bonus
                            if score > best_score:
                                best_score = score
                                best_length, best_width, best_height = L, W, H

                if best_length and best_width and best_height:
                    self.param_length.set(best_length)
                    self.param_width.set(best_width)
                    self.param_height.set(best_height)
                    self.status_var.set(
                        f"✅ {len(self.pdf_files)}개 PDF 분석 완료 — "
                        f"자동 추출: {best_width:,.0f} x {best_length:,.0f} x {best_height:,.0f} mm"
                    )
                else:
                    best_length = dome_dims[0]
                    best_width = dome_dims[1]
                    best_height = dome_dims[2]
                    if best_width > best_length:
                        best_length, best_width = best_width, best_length
                    self.param_length.set(best_length)
                    self.param_width.set(best_width)
                    self.param_height.set(best_height)
                    self.status_var.set(
                        f"📁 {len(self.pdf_files)}개 PDF 분석 — 자동 추출 (확인 필요): "
                        f"{best_width:,.0f} x {best_length:,.0f} x {best_height:,.0f} mm"
                    )
            elif len(dome_dims) >= 2:
                self.param_width.set(min(dome_dims[:2]))
                self.param_length.set(max(dome_dims[:2]))
                self.status_var.set(
                    f"📁 {len(self.pdf_files)}개 PDF 분석 — 폭/길이 자동 추출 (높이는 수동 입력 필요)"
                )
            elif len(dome_dims) == 1:
                self.param_width.set(dome_dims[0])
                self.status_var.set(
                    f"📁 {len(self.pdf_files)}개 PDF 분석 — 치수 1개 발견 (나머지 수동 입력 필요)"
                )
            else:
                self.status_var.set(
                    f"📁 {len(self.pdf_files)}개 PDF — 돔 치수 자동 추출 실패 (수동 입력 필요)"
                )
        else:
            self.status_var.set(
                f"📁 {len(self.pdf_files)}개 PDF — 텍스트 추출 불가 (수동 입력 필요)"
            )

        if all_project:
            self.param_project.set(all_project[0])

        info = f"=== 폴더 전체 분석 결과 ===\n"
        info += f"PDF 파일: {len(self.pdf_files)}개\n"
        if all_keywords:
            info += f"키워드: {', '.join(set(all_keywords))}\n"
        if all_dims_combined:
            top = sorted(set(all_dims_combined), reverse=True)[:8]
            info += f"주요 치수(mm): {', '.join(f'{d:,.0f}' for d in top)}\n"
            info += "\n치수가 맞지 않으면 직접 수정하세요."
        else:
            info += "\n⚠️ 이미지 PDF — 자동 추출 불가\n"
            info += "━━━━━━━━━━━━━━━━━━━━\n"
            info += "[도면 열기] 클릭 → 도면 확인\n"
            info += "→ 오른쪽 파라미터에 치수 직접 입력\n"
            info += "→ [3D 미리보기] 클릭"

        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, info)
        self._update_calcs()

    # ================================================================
    #  PDF 선택 및 개별 분석
    # ================================================================
    def _open_selected_pdf(self):
        """선택한 PDF를 시스템 기본 뷰어로 열기"""
        sel = self.pdf_listbox.curselection()
        if not sel:
            if self.pdf_files:
                if sys.platform == 'win32':
                    os.startfile(self.pdf_files[0])
                else:
                    webbrowser.open('file://' + self.pdf_files[0])
                self.status_var.set(f"📖 도면 열림: {os.path.basename(self.pdf_files[0])}")
            else:
                messagebox.showinfo("안내", "먼저 PDF 폴더를 선택하세요.")
            return
        pdf_path = self.pdf_files[sel[0]]
        try:
            if sys.platform == 'win32':
                os.startfile(pdf_path)
            else:
                webbrowser.open('file://' + os.path.abspath(pdf_path))
            self.status_var.set(f"📖 도면 열림: {os.path.basename(pdf_path)} — 치수를 확인 후 오른쪽에 입력하세요")
        except Exception as e:
            messagebox.showerror("오류", f"PDF 열기 실패: {e}")

    def _on_pdf_select(self, event):
        sel = self.pdf_listbox.curselection()
        if not sel:
            return
        pdf_path = self.pdf_files[sel[0]]
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, f"⏳ 분석 중: {os.path.basename(pdf_path)}...\n")
        self.update_idletasks()

        thread = threading.Thread(
            target=self._analyze_pdf_background,
            args=(pdf_path,),
            daemon=True
        )
        thread.start()

    def _analyze_pdf_background(self, pdf_path):
        """백그라운드 스레드에서 PDF 텍스트 추출 및 치수 분석"""
        try:
            text = PDFAnalyzer.extract_text(pdf_path)
            results = PDFAnalyzer.find_dimensions(text)
        except Exception as e:
            self.after(0, lambda: self._show_pdf_analysis_error(pdf_path, e))
            return
        self.after(0, lambda: self._show_pdf_analysis_result(pdf_path, results))

    def _show_pdf_analysis_error(self, pdf_path, error):
        """PDF 분석 오류를 UI에 표시"""
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, f"❌ 분석 실패: {os.path.basename(pdf_path)}\n{error}\n")

    def _show_pdf_analysis_result(self, pdf_path, results):
        """PDF 분석 결과를 UI에 표시 (메인 스레드에서 호출)"""
        all_found_dims = list(results['dimensions_mm'])
        for d in results.get('dimensions_raw', []):
            if d not in all_found_dims:
                all_found_dims.append(d)
        for d in results.get('dimensions_ft', []):
            if d not in all_found_dims:
                all_found_dims.append(d)

        info = f"📄 {os.path.basename(pdf_path)}\n"
        if results['dome_keywords']:
            info += f"🔑 키워드: {', '.join(set(results['dome_keywords']))}\n"
        if all_found_dims:
            dims = sorted(set(all_found_dims), reverse=True)[:10]
            info += f"📏 치수(mm): {', '.join(f'{d:,.0f}' for d in dims)}\n"

            dome_dims = [d for d in dims if 3000 <= d <= 200000]
            if dome_dims:
                info += f"\n💡 이 도면의 주요 치수로 업데이트하려면\n"
                info += f"   아래 [이 도면 치수 적용] 버튼을 클릭하세요.\n"
                self._current_pdf_dims = dome_dims
        elif results['dimensions_mm']:
            dims = sorted(set(results['dimensions_mm']), reverse=True)[:10]
            info += f"📏 치수(mm): {', '.join(f'{d:,.0f}' for d in dims)}\n"

        if results['dimensions_m']:
            m_dims = sorted(set(results['dimensions_m']), reverse=True)[:5]
            info += f"📏 치수(m): {', '.join(f'{d:.1f}' for d in m_dims)}\n"
        if results['project_info']:
            info += f"📋 프로젝트: {', '.join(set(results['project_info']))}\n"
        if not all_found_dims and not results['dimensions_m'] and not results['project_info'] and not results['dome_keywords']:
            info += "\n⚠️ 이미지 PDF — 자동 읽기 불가\n"
            info += "━━━━━━━━━━━━━━━━━━━━\n"
            info += "1. [도면 열기] 클릭 → 도면 확인\n"
            info += "2. 도면에서 폭/길이/높이 확인\n"
            info += "3. 오른쪽 파라미터에 직접 입력\n"
            info += "4. [3D 미리보기] 클릭!\n"

        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, info)

    def _apply_pdf_dims(self):
        """선택한 PDF의 치수를 파라미터에 적용"""
        if not self._current_pdf_dims:
            messagebox.showinfo("안내", "먼저 PDF 파일을 선택하세요.\n치수가 있는 PDF를 클릭하면 적용 가능합니다.")
            return

        dims = sorted(self._current_pdf_dims, reverse=True)
        if len(dims) >= 3:
            best_length = dims[0]
            best_width = dims[1]
            best_height = None
            for d in dims[2:]:
                ratio = d / best_width
                if 0.15 <= ratio <= 0.6:
                    best_height = d
                    break
            if best_height is None:
                best_height = dims[2]
            if best_width > best_length:
                best_length, best_width = best_width, best_length
            self.param_length.set(best_length)
            self.param_width.set(best_width)
            self.param_height.set(best_height)
            self.status_var.set(f"✅ 치수 적용: {best_width:,.0f} x {best_length:,.0f} x {best_height:,.0f} mm")
        elif len(dims) >= 2:
            self.param_width.set(min(dims[:2]))
            self.param_length.set(max(dims[:2]))
            self.status_var.set(f"✅ 폭/길이 적용 완료 (높이는 수동 입력 필요)")
        elif len(dims) == 1:
            self.param_width.set(dims[0])
            self.status_var.set(f"✅ 치수 1개 적용 (나머지 수동 입력 필요)")

        self._update_calcs()

    # ================================================================
    #  산출값 업데이트
    # ================================================================
    def _update_calcs(self):
        try:
            w = self.param_width.get()
            l = self.param_length.get()
            h = self.param_height.get()
            self.calc_text.delete("1.0", tk.END)
            if w <= 0 or l <= 0 or h <= 0:
                self.calc_text.insert(tk.END,
                    "도면에서 치수를 확인 후 입력하세요:\n\n"
                    "  폭 Width  = 단변 스팬 (mm)\n"
                    "  길이 Length = 장변 길이 (mm)\n"
                    "  높이 Height = 정상부 높이 (mm)\n\n"
                    "[도면 열기]로 PDF를 확인하세요!"
                )
                return
            self.calc_text.insert(tk.END,
                f"반스팬 (a)  = {w/2:,.0f} mm\n"
                f"반장변 (b)  = {l/2:,.0f} mm\n"
                f"폭/높이비   = {w/h:.3f}\n"
                f"장/단변비   = {l/w:.3f}\n"
                f"바닥 면적   = {w*l/1e6:,.1f} m²\n"
                f"곡면방정식  = z = {h:.0f}×√(1-(x/{w/2:.0f})²)×√(1-(y/{l/2:.0f})²)"
            )
        except (tk.TclError, ZeroDivisionError, ValueError):
            pass

    def _get_params(self):
        return {
            'project_name': self.param_project.get(),
            'width': self.param_width.get(),
            'length': self.param_length.get(),
            'height': self.param_height.get(),
            'dome_type': self.param_dome_type.get(),
            'cable_spacing': self.param_cable_spacing.get(),
            'foundation_depth': self.param_foundation_depth.get(),
        }

    # ================================================================
    #  3D 미리보기 (viewer_3d 모듈 사용)
    # ================================================================
    def _preview_3d(self):
        params = self._get_params()
        if params['width'] <= 0 or params['length'] <= 0 or params['height'] <= 0:
            messagebox.showwarning("파라미터 필요",
                "폭(Width), 길이(Length), 높이(Height)를\n모두 입력해야 3D 미리보기가 가능합니다.\n\n"
                "PDF 폴더를 선택하거나 직접 입력해주세요.")
            return
        html = generate_viewer_html(params)

        if self.pdf_folder.get():
            out_dir = self.pdf_folder.get()
        else:
            out_dir = tempfile.gettempdir()

        html_path = os.path.join(out_dir, "AirDome_3D_Preview.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        webbrowser.open('file://' + os.path.abspath(html_path))
        self.status_var.set(f"✅ 3D 미리보기 열림: {html_path}")

    # ================================================================
    #  CATIA STEP 내보내기 (catia_exporter 모듈 사용)
    # ================================================================
    def _export_step(self):
        params = self._get_params()
        if params['width'] <= 0 or params['length'] <= 0 or params['height'] <= 0:
            messagebox.showwarning("파라미터 필요",
                "폭(Width), 길이(Length), 높이(Height)를\n모두 입력해야 STEP 내보내기가 가능합니다.")
            return
        filepath = filedialog.asksaveasfilename(
            title="STEP 파일 저장",
            defaultextension=".stp",
            filetypes=[("STEP files", "*.stp *.step"), ("All files", "*.*")],
            initialfile=f"AirDome_{params['width']:.0f}x{params['length']:.0f}x{params['height']:.0f}.stp"
        )
        if filepath:
            try:
                cable_sp = params.get('cable_spacing', 0)
                fnd_depth = params.get('foundation_depth', 500)
                n = STEPExporter.export(filepath, params['width'], params['length'], params['height'],
                                        cable_spacing=cable_sp, foundation_depth=fnd_depth)
                bodies = ["DomeSurface (돔 곡면)"]
                if fnd_depth > 0:
                    bodies.append(f"Foundation (매트 기초, 깊이 {fnd_depth:.0f}mm)")
                if cable_sp > 0:
                    bodies.append(f"CableNet (케이블넷, 간격 {cable_sp:.0f}mm)")
                bodies.append("GroundPlane (바닥 슬래브)")
                body_msg = "\n".join(f"  • {b}" for b in bodies)
                self.status_var.set(f"✅ STEP 저장 완료: {filepath} ({n} entities, {len(bodies)} bodies)")
                messagebox.showinfo("성공",
                    f"STEP 파일이 저장되었습니다.\n\n"
                    f"{filepath}\n\n"
                    f"── 분리된 Body ({len(bodies)}개) ──\n{body_msg}\n\n"
                    f"CATIA에서 Import 시 각각 별도\nBody/Geometrical Set으로 인식됩니다!")
            except Exception as e:
                messagebox.showerror("오류", f"STEP 내보내기 실패:\n{e}")

    # ================================================================
    #  STL 내보내기 (stl_exporter 모듈 사용)
    # ================================================================
    def _export_stl(self):
        params = self._get_params()
        filepath = filedialog.asksaveasfilename(
            title="STL 파일 저장",
            defaultextension=".stl",
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")],
            initialfile=f"AirDome_{params['width']:.0f}x{params['length']:.0f}x{params['height']:.0f}.stl"
        )
        if filepath:
            try:
                tri_count = STLExporter.export(
                    filepath, params['width'], params['length'], params['height']
                )
                self.status_var.set(f"✅ STL 저장 완료: {filepath} ({tri_count:,} triangles)")
                messagebox.showinfo("성공", f"STL 파일이 저장되었습니다.\n\n{filepath}")
            except Exception as e:
                messagebox.showerror("오류", f"STL 내보내기 실패:\n{e}")

    # ================================================================
    #  구조 시뮬레이션 (simulation 모듈 사용)
    # ================================================================
    def _simulation_3d(self):
        """구조 시뮬레이션 뷰어 실행 (브라우저)"""
        params = self._get_params()
        if params['width'] <= 0 or params['length'] <= 0 or params['height'] <= 0:
            messagebox.showwarning("파라미터 필요",
                "폭(Width), 길이(Length), 높이(Height)를\n모두 입력해야 시뮬레이션이 가능합니다.\n\n"
                "PDF 폴더를 선택하거나 직접 입력해주세요.")
            return
        html = generate_simulation_html(params)

        if self.pdf_folder.get():
            out_dir = self.pdf_folder.get()
        else:
            out_dir = tempfile.gettempdir()

        html_path = os.path.join(out_dir, "AirDome_Simulation.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # 기술해설서 PDF를 HTML과 같은 폴더에 복사
        guide_name = "AirDome_시뮬레이션_기술해설서.pdf"
        guide_dst = os.path.join(out_dir, guide_name)
        if not os.path.exists(guide_dst):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            guide_src = os.path.join(script_dir, guide_name)
            if os.path.exists(guide_src):
                try:
                    shutil.copy2(guide_src, guide_dst)
                except Exception:
                    pass

        webbrowser.open('file://' + os.path.abspath(html_path))
        self.status_var.set(f"🔬 구조 시뮬레이션 열림: {html_path}")

    # ================================================================
    #  일조 시뮬레이션 (solar_simulation 모듈 사용)
    # ================================================================
    def _solar_simulation(self):
        """일조 시뮬레이션 뷰어 실행 (브라우저)"""
        params = self._get_params()
        if params['width'] <= 0 or params['length'] <= 0 or params['height'] <= 0:
            messagebox.showwarning("파라미터 필요",
                "폭(Width), 길이(Length), 높이(Height)를\n모두 입력해야 일조 시뮬레이션이 가능합니다.\n\n"
                "PDF 폴더를 선택하거나 직접 입력해주세요.")
            return
        html = generate_solar_simulation_html(params)

        if self.pdf_folder.get():
            out_dir = self.pdf_folder.get()
        else:
            out_dir = tempfile.gettempdir()

        html_path = os.path.join(out_dir, "AirDome_Solar_Simulation.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        webbrowser.open('file://' + os.path.abspath(html_path))
        self.status_var.set(f"☀️ 일조 시뮬레이션 열림: {html_path}")


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    app = AirDomeViewer()
    app.mainloop()
