"""
Structural Simulation Module for AIR DOME 3D Simulator
========================================================
Part of the OzoMeta AIR DOME 3D Viewer and Simulator system.

This module contains the structural simulation engine for three-layer membrane
structures (air domes) with cable reinforcement. It generates interactive 3D
visualization HTML with real-time load analysis, pressure distribution,
safety factor calculations, and cable network simulation.

Author: OzoMeta
License: Proprietary
"""

import base64, os


def generate_simulation_html(params):
    """Three.js + 삼중막 구조 시뮬레이션 뷰어 (v3 Clean UI)"""
    # 로고 이미지를 base64로 인코딩하여 HTML에 내장
    import base64, os
    logo_b64 = ""
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as _lf:
            logo_b64 = base64.b64encode(_lf.read()).decode()
    logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else "logo.png"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>에어돔 삼중막 시뮬레이션 | © OZOMETA | UI Verification Mode</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:#111827;font-family:'Segoe UI','Apple SD Gothic Neo',sans-serif;overflow:hidden;color:#e5e7eb;}}

  /* ═══ 왼쪽 패널: 3단 구조 ═══ */
  #panel{{position:absolute;top:0;left:0;bottom:0;width:320px;z-index:20;
    background:#1f2937;border-right:1px solid #374151;display:flex;flex-direction:column;}}
  #panel-header{{padding:12px 14px;background:#111827;border-bottom:1px solid #374151;flex-shrink:0;}}
  #panel-header .logo-top{{display:flex;align-items:center;gap:10px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #2a3545;}}
  #panel-header .logo-top img{{height:36px;object-fit:contain;}}
  #panel-header .logo-top .brand{{font-size:10px;color:#9ca3af;letter-spacing:1px;font-weight:600;}}
  #panel-header h2{{font-size:16px;color:#60a5fa;display:flex;align-items:center;gap:6px;margin:0;}}
  #panel-header .info{{font-size:13px;color:#d1d5db;margin-top:6px;line-height:1.6;font-weight:500;}}

  /* 탭 네비 (하중/막구성/재료 3개만) */
  .tabs{{display:flex;border-bottom:1px solid #374151;background:#111827;flex-shrink:0;}}
  .tab{{flex:1;padding:9px 0;text-align:center;font-size:12px;font-weight:600;color:#6b7280;
    cursor:pointer;border-bottom:2px solid transparent;transition:all 0.2s;}}
  .tab:hover{{color:#9ca3af;}}
  .tab.on{{color:#60a5fa;border-bottom-color:#60a5fa;background:rgba(96,165,250,0.05);}}

  /* 탭 내용 (스크롤 가능) */
  .tab-body{{flex:1;overflow-y:auto;padding:0;min-height:0;}}
  .tab-body::-webkit-scrollbar{{width:3px;}}
  .tab-body::-webkit-scrollbar-thumb{{background:#4b5563;border-radius:2px;}}
  .tp{{display:none;padding:12px 14px;}}
  .tp.on{{display:block;}}

  /* 하단 고정 영역 (표시 + 프리셋) */
  #panel-fixed{{flex-shrink:0;border-top:1px solid #374151;background:#1a2332;overflow-y:auto;max-height:45vh;}}
  #panel-fixed::-webkit-scrollbar{{width:3px;}}
  #panel-fixed::-webkit-scrollbar-thumb{{background:#4b5563;border-radius:2px;}}
  .fixed-sec{{padding:10px 14px;border-bottom:1px solid #2a3545;}}
  .fixed-sec:last-child{{border-bottom:none;}}

  /* 슬라이더 */
  .f{{margin-bottom:10px;}}
  .f .fl{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;}}
  .f .fn{{font-size:11px;color:#9ca3af;}}
  .f .fv{{font-size:13px;color:#60a5fa;font-weight:700;}}
  .f .fv .u{{font-size:10px;color:#6b7280;font-weight:400;margin-left:2px;}}
  .f input[type=range]{{width:100%;height:4px;-webkit-appearance:none;background:#374151;
    border-radius:2px;outline:none;}}
  .f input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:16px;height:16px;
    border-radius:50%;background:#60a5fa;cursor:pointer;border:2px solid #1f2937;}}

  /* 버튼 공용 */
  .mode-row{{display:flex;gap:4px;margin:6px 0;}}
  .mbtn{{flex:1;padding:6px 4px;font-size:10px;text-align:center;border:1px solid #374151;
    background:#1f2937;color:#9ca3af;border-radius:4px;cursor:pointer;transition:all 0.15s;}}
  .mbtn:hover{{border-color:#60a5fa;color:#60a5fa;}}
  .mbtn.on{{background:rgba(96,165,250,0.15);border-color:#60a5fa;color:#60a5fa;font-weight:700;}}

  /* 압력 다이어그램 */
  .pdiag{{background:#111827;border-radius:6px;padding:8px 10px;margin-top:8px;
    font-size:11px;line-height:1.9;border:1px solid #1f2937;}}
  .pdiag .row{{display:flex;justify-content:space-between;padding:1px 0;}}
  .pdiag .row .dot{{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px;vertical-align:middle;}}
  .pdiag .val{{color:#60a5fa;font-weight:600;}}

  /* 섹션 제목 */
  .st{{font-size:11px;font-weight:700;color:#60a5fa;letter-spacing:1px;
    margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1f2937;}}

  /* ═══ 오른쪽 결과 패널 ═══ */
  #results{{position:absolute;top:0;right:0;bottom:0;width:280px;z-index:20;
    background:#1f2937;border-left:1px solid #374151;overflow-y:auto;}}
  #results::-webkit-scrollbar{{width:3px;}}
  #results::-webkit-scrollbar-thumb{{background:#4b5563;border-radius:2px;}}
  #results h3{{font-size:14px;color:#60a5fa;padding:8px 14px;margin:0;background:#111827;
    border-bottom:1px solid #374151;position:sticky;top:0;z-index:1;}}
  #res-body{{padding:4px 0;}}

  /* 레이어 카드 */
  .lcard{{margin:4px 8px;background:#111827;border-radius:6px;border:1px solid #374151;overflow:hidden;}}
  .lcard-h{{padding:6px 12px;display:flex;align-items:center;gap:7px;font-size:13px;font-weight:700;
    border-bottom:1px solid #1f2937;}}
  .lcard-h .cdot{{width:9px;height:9px;border-radius:50%;flex-shrink:0;}}
  .lcard-row{{display:flex;align-items:baseline;padding:4px 12px;}}
  .lcard-row .k{{flex:1;font-size:12px;color:#9ca3af;}}
  .lcard-row .v{{font-size:15px;font-weight:700;text-align:right;}}
  .lcard-row .v .u{{font-size:10px;color:#6b7280;font-weight:400;margin-left:2px;}}
  .lcard-bar{{display:none;}}
  .lcard-bar div{{height:100%;border-radius:2px;transition:width 0.3s;}}

  .sf-safe{{color:#34d399;}} .sf-warn{{color:#fbbf24;}} .sf-danger{{color:#f87171;}}

  /* 판정 카드 */
  .verdict{{margin:4px 8px;padding:8px 12px;background:#111827;border-radius:6px;
    border:1px solid #374151;font-size:13px;line-height:1.6;font-weight:500;}}

  /* 버튼 (시각화/레이어/뷰에서 공용) */
  .tb{{padding:5px 6px;font-size:10px;border:1px solid #374151;background:transparent;
    color:#9ca3af;border-radius:4px;cursor:pointer;transition:all 0.15s;white-space:nowrap;text-align:center;flex:1 1 auto;min-width:0;}}
  .tb:hover{{border-color:#60a5fa;color:#60a5fa;}}
  .tb.on{{background:rgba(96,165,250,0.15);border-color:#60a5fa;color:#60a5fa;font-weight:600;}}

  /* 오른쪽 하단: 치수 입력 + 로고 */
  #res-footer{{border-top:1px solid #374151;background:#1a2332;padding:8px 10px;}}
  .dim-sec{{margin-bottom:4px;}}
  .dim-sec .st{{font-size:11px;margin-bottom:4px;color:#60a5fa;font-weight:600;}}
  .dim-row{{display:flex;align-items:center;gap:5px;margin-bottom:4px;}}
  .dim-row label{{font-size:11px;color:#9ca3af;min-width:62px;}}
  .dim-row input[type=number]{{flex:1;background:#111827;border:1px solid #374151;border-radius:4px;
    color:#60a5fa;font-size:13px;font-weight:700;padding:4px 8px;outline:none;text-align:right;
    -moz-appearance:textfield;}}
  .dim-row input[type=number]::-webkit-inner-spin-button{{-webkit-appearance:none;}}
  .dim-row input[type=number]:focus{{border-color:#60a5fa;}}
  .dim-row .dim-u{{font-size:10px;color:#6b7280;min-width:26px;}}
  .dim-apply{{width:100%;padding:6px;font-size:11px;font-weight:700;background:rgba(96,165,250,0.15);
    border:1px solid #60a5fa;color:#60a5fa;border-radius:4px;cursor:pointer;transition:all 0.15s;}}
  .dim-apply:hover{{background:rgba(96,165,250,0.3);}}
  .btn-techguide{{width:100%;padding:8px;font-size:11px;font-weight:700;background:rgba(251,191,36,0.15);
    border:1px solid #fbbf24;color:#fbbf24;border-radius:4px;cursor:pointer;transition:all 0.15s;margin-top:8px;}}
  .btn-techguide:hover{{background:rgba(251,191,36,0.3);}}
  #logo-area{{display:flex;align-items:center;justify-content:center;padding:8px 0 4px;border-top:1px solid #2a3545;margin-top:6px;}}
  #logo-area img{{height:40px;object-fit:contain;}}

  /* 풍류 시각화 범례 */
  #wind-legend{{position:absolute;bottom:44px;left:320px;z-index:15;background:rgba(17,24,39,0.9);
    border-radius:6px;padding:6px 14px;display:none;align-items:center;gap:8px;font-size:11px;
    border:1px solid #374151;color:#e5e7eb;}}
  #wind-legend.on{{display:flex;}}
  #wind-legend canvas{{border-radius:2px;}}

  /* 범례 */
  #legend{{position:absolute;bottom:14px;left:320px;z-index:15;background:rgba(17,24,39,0.9);
    border-radius:6px;padding:6px 14px;display:flex;align-items:center;gap:8px;font-size:11px;
    border:1px solid #374151;}}
  #legend canvas{{border-radius:2px;}}

  /* 프리셋 팝업 */
  .preset-row{{display:flex;gap:3px;margin-top:8px;flex-wrap:wrap;}}

  /* ═══ 종합의견 버튼 ═══ */
  .btn-opinion{{width:100%;padding:10px;font-size:12px;font-weight:700;background:rgba(139,92,246,0.15);
    border:1px solid #8b5cf6;color:#8b5cf6;border-radius:6px;cursor:pointer;transition:all 0.2s;margin-top:8px;
    letter-spacing:0.5px;}}
  .btn-opinion:hover{{background:rgba(139,92,246,0.35);box-shadow:0 0 12px rgba(139,92,246,0.3);}}

  /* ═══ 종합의견 모달 ═══ */
  #opinion-overlay{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);
    z-index:1000;display:none;align-items:center;justify-content:center;backdrop-filter:blur(4px);}}
  #opinion-overlay.on{{display:flex;}}
  #opinion-modal{{background:#1f2937;border:1px solid #374151;border-radius:12px;width:720px;max-width:90vw;
    max-height:85vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,0.5);}}
  #opinion-modal-header{{padding:16px 20px;border-bottom:1px solid #374151;display:flex;align-items:center;
    justify-content:space-between;flex-shrink:0;}}
  #opinion-modal-header h3{{font-size:16px;color:#8b5cf6;margin:0;display:flex;align-items:center;gap:8px;}}
  #opinion-modal-header .close-btn{{background:none;border:1px solid #4b5563;color:#9ca3af;width:30px;height:30px;
    border-radius:6px;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;
    transition:all 0.15s;}}
  #opinion-modal-header .close-btn:hover{{border-color:#f87171;color:#f87171;}}
  #opinion-body{{padding:20px;overflow-y:auto;flex:1;min-height:0;}}
  #opinion-body::-webkit-scrollbar{{width:4px;}}
  #opinion-body::-webkit-scrollbar-thumb{{background:#4b5563;border-radius:2px;}}
  #opinion-content{{font-size:13.5px;line-height:2.0;color:#d1d5db;}}
  #opinion-content .op-section{{margin-bottom:16px;}}
  #opinion-content .op-title{{font-size:14px;font-weight:700;color:#8b5cf6;margin-bottom:6px;
    padding-bottom:4px;border-bottom:1px solid #2a3545;display:flex;align-items:center;gap:6px;}}
  #opinion-content .op-highlight{{color:#60a5fa;font-weight:600;}}
  #opinion-content .op-safe{{color:#34d399;font-weight:600;}}
  #opinion-content .op-warn{{color:#fbbf24;font-weight:600;}}
  #opinion-content .op-danger{{color:#f87171;font-weight:600;}}
  #opinion-content .op-param{{color:#a78bfa;font-weight:500;}}
  #opinion-footer{{padding:12px 20px;border-top:1px solid #374151;display:flex;justify-content:flex-end;gap:8px;flex-shrink:0;}}
  #opinion-footer button{{padding:8px 18px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;
    transition:all 0.15s;}}
  .btn-copy-opinion{{background:rgba(96,165,250,0.15);border:1px solid #60a5fa;color:#60a5fa;}}
  .btn-copy-opinion:hover{{background:rgba(96,165,250,0.3);}}
  .btn-close-opinion{{background:rgba(107,114,128,0.15);border:1px solid #4b5563;color:#9ca3af;}}
  .btn-close-opinion:hover{{border-color:#9ca3af;color:#e5e7eb;}}
</style>
</head>
<body>

<!-- ═══════ 왼쪽 패널 ═══════ -->
<div id="panel">
  <div id="panel-header">
    <div class="logo-top">
      <img src="{logo_src}" alt="OZO META">
      <span class="brand">© OZOMETA | UI Verification Mode</span>
    </div>
    <h2>🏗️ 에어돔 삼중막 시뮬레이션</h2>
    <div class="info" id="header-info">
      <span style="color:#34d399;font-weight:700;">{params.get('width',0):,.0f}</span> ×
      <span style="color:#34d399;font-weight:700;">{params.get('length',0):,.0f}</span> ×
      <span style="color:#34d399;font-weight:700;">{params.get('height',0):,.0f}</span> mm
      &nbsp;|&nbsp; {params.get('width',0)*params.get('length',0)/1e6:,.0f} m²
    </div>
  </div>

  <div class="tabs">
    <div class="tab on" onclick="openTab('t-load')">하중</div>
    <div class="tab" onclick="openTab('t-layer')">막구성</div>
    <div class="tab" onclick="openTab('t-mat')">재료</div>
    <div class="tab" onclick="openTab('t-cable')" style="color:#f59e0b;">케이블</div>
  </div>

  <div class="tab-body">
    <!-- ── 탭1: 하중 조건 ── -->
    <div class="tp on" id="t-load">
      <div class="f"><div class="fl"><span class="fn">내압 (P_int)</span><span class="fv"><span id="v-pressure">300</span><span class="u">Pa</span></span></div>
        <input type="range" id="s-pressure" min="100" max="5000" value="300" step="10"></div>
      <div class="f"><div class="fl"><span class="fn">풍속</span><span class="fv"><span id="v-wind">15</span><span class="u">m/s</span></span></div>
        <input type="range" id="s-wind" min="0" max="50" value="15" step="1"></div>
      <div class="f"><div class="fl"><span class="fn">적설하중</span><span class="fv"><span id="v-snow">0.5</span><span class="u">kN/m²</span></span></div>
        <input type="range" id="s-snow" min="0" max="3.0" value="0.5" step="0.1"></div>
      <div class="f"><div class="fl"><span class="fn">풍향</span><span class="fv"><span id="v-winddir">0</span><span class="u">°</span></span></div>
        <input type="range" id="s-winddir" min="0" max="360" value="0" step="5"></div>
    </div>

    <!-- ── 탭2: 막구성 ── -->
    <div class="tp" id="t-layer">
      <div class="st">공기층 간격</div>
      <div class="f"><div class="fl"><span class="fn">공기층① (외피↔내피상)</span><span class="fv"><span id="v-gap1">300</span><span class="u">mm</span></span></div>
        <input type="range" id="s-gap1" min="100" max="800" value="300" step="10"></div>
      <div style="font-size:9px;color:#4b5563;margin:-6px 0 8px;">시각 5배 확대 표시</div>
      <div class="f"><div class="fl"><span class="fn">공기층② (내피상↔내피하, 단열)</span><span class="fv"><span id="v-gap2">200</span><span class="u">mm</span></span></div>
        <input type="range" id="s-gap2" min="50" max="500" value="200" step="10"></div>
      <div style="font-size:9px;color:#4b5563;margin:-6px 0 8px;">시각 5배 확대 표시</div>

      <div class="st" style="margin-top:12px;">압력분배 모드 (자동계산)</div>
      <div class="mode-row">
        <div class="mbtn on" onclick="setPMode('equal')" id="pm-equal">균등분배</div>
        <div class="mbtn" onclick="setPMode('outer')" id="pm-outer">외피중심</div>
        <div class="mbtn" onclick="setPMode('inner')" id="pm-inner">내피보호</div>
        <div class="mbtn" onclick="setPMode('single')" id="pm-single">단일블로워</div>
      </div>
      <div style="font-size:9px;color:#6b7280;margin:4px 0;" id="pm-info">P_gap1=33% | P_gap2=67% of P_int</div>

      <div class="pdiag" id="p-diagram">
        <div class="row"><span><span class="dot" style="background:#6b7280"></span>외기</span><span class="val">0 Pa</span></div>
        <div class="row"><span><span class="dot" style="background:#e5e7eb"></span>외피막 — ΔP</span><span class="val" id="pd-o">100 Pa</span></div>
        <div class="row"><span><span class="dot" style="background:#60a5fa"></span>공기층①</span><span class="val" id="pd-g1">100 Pa</span></div>
        <div class="row"><span><span class="dot" style="background:#fb923c"></span>내피(상) — ΔP</span><span class="val" id="pd-iu">100 Pa</span></div>
        <div class="row"><span><span class="dot" style="background:#38bdf8"></span>공기층② (단열)</span><span class="val" id="pd-g2">200 Pa</span></div>
        <div class="row"><span><span class="dot" style="background:#ea580c"></span>내피(하) — ΔP</span><span class="val" id="pd-il">100 Pa</span></div>
        <div class="row"><span><span class="dot" style="background:#34d399"></span>실내공간</span><span class="val" id="pd-int">300 Pa</span></div>
      </div>
    </div>

    <!-- ── 탭3: 재료 ── -->
    <div class="tp" id="t-mat">
      <div class="st">외피막</div>
      <div class="f"><div class="fl"><span class="fn">두께</span><span class="fv"><span id="v-thick-o">0.8</span><span class="u">mm</span></span></div>
        <input type="range" id="s-thick-o" min="0.3" max="2.0" value="0.8" step="0.1"></div>
      <div class="f"><div class="fl"><span class="fn">인장강도</span><span class="fv"><span id="v-str-o">4000</span><span class="u">N/50mm</span></span></div>
        <input type="range" id="s-str-o" min="1000" max="10000" value="4000" step="100"></div>

      <div class="st" style="margin-top:12px;">내피막</div>
      <div class="f"><div class="fl"><span class="fn">두께</span><span class="fv"><span id="v-thick-i">0.5</span><span class="u">mm</span></span></div>
        <input type="range" id="s-thick-i" min="0.2" max="1.5" value="0.5" step="0.1"></div>
      <div class="f"><div class="fl"><span class="fn">인장강도</span><span class="fv"><span id="v-str-i">2500</span><span class="u">N/50mm</span></span></div>
        <input type="range" id="s-str-i" min="500" max="8000" value="2500" step="100"></div>

      <div class="st" style="margin-top:12px;">공통</div>
      <div class="f"><div class="fl"><span class="fn">탄성계수</span><span class="fv"><span id="v-elastic">600</span><span class="u">MPa</span></span></div>
        <input type="range" id="s-elastic" min="100" max="2000" value="600" step="50"></div>
      <div class="f"><div class="fl"><span class="fn">케이블 간격</span><span class="fv"><span id="v-cspace">{params.get('cable_spacing',3600):.0f}</span><span class="u">mm</span></span></div>
        <input type="range" id="s-cspace" min="1000" max="6000" value="{params.get('cable_spacing',3600):.0f}" step="100"></div>
    </div>

    <!-- ── 탭4: 케이블 해석 ── -->
    <div class="tp" id="t-cable">
      <div class="st">케이블 재질 선택</div>
      <div class="mode-row">
        <div class="mbtn on" onclick="setCableMat('sts304_4')" id="cm-sts304_4">STS304 ∅4</div>
        <div class="mbtn" onclick="setCableMat('sts304_6')" id="cm-sts304_6">STS304 ∅6</div>
        <div class="mbtn" onclick="setCableMat('sts316_6')" id="cm-sts316_6">STS316 ∅6</div>
      </div>
      <div class="mode-row">
        <div class="mbtn" onclick="setCableMat('sts304_8')" id="cm-sts304_8">STS304 ∅8</div>
        <div class="mbtn" onclick="setCableMat('galv_6')" id="cm-galv_6">아연도금 ∅6</div>
        <div class="mbtn" onclick="setCableMat('galv_8')" id="cm-galv_8">아연도금 ∅8</div>
      </div>
      <div class="mode-row">
        <div class="mbtn" onclick="setCableMat('custom')" id="cm-custom" style="border-color:#f59e0b;color:#f59e0b;">직접 입력</div>
      </div>

      <div class="st" style="margin-top:12px;">케이블 물성</div>
      <div class="f"><div class="fl"><span class="fn">직경</span><span class="fv"><span id="v-cdia">4.0</span><span class="u">mm</span></span></div>
        <input type="range" id="s-cdia" min="2" max="16" value="4.0" step="0.5"></div>
      <div class="f"><div class="fl"><span class="fn">파단하중</span><span class="fv"><span id="v-cbreak">9.0</span><span class="u">kN</span></span></div>
        <input type="range" id="s-cbreak" min="1" max="80" value="9.0" step="0.5"></div>
      <div class="f"><div class="fl"><span class="fn">탄성계수</span><span class="fv"><span id="v-celastic">130</span><span class="u">GPa</span></span></div>
        <input type="range" id="s-celastic" min="50" max="210" value="130" step="5"></div>
      <div class="f"><div class="fl"><span class="fn">요구 안전율</span><span class="fv"><span id="v-csf-req">3.0</span></span></div>
        <input type="range" id="s-csf-req" min="1.5" max="6.0" value="3.0" step="0.1"></div>

      <div class="st" style="margin-top:14px;">하중 조합 시나리오</div>
      <div style="font-size:9px;color:#6b7280;margin-bottom:6px;">체크된 조합 중 가장 불리한 조건을 자동 판정합니다</div>
      <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:#d1d5db;margin:4px 0;cursor:pointer;">
        <input type="checkbox" id="lc-1" checked style="accent-color:#60a5fa;">LC1: 내압 + 자중 (평상시)</label>
      <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:#d1d5db;margin:4px 0;cursor:pointer;">
        <input type="checkbox" id="lc-2" checked style="accent-color:#60a5fa;">LC2: 내압 + 풍하중 (강풍)</label>
      <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:#d1d5db;margin:4px 0;cursor:pointer;">
        <input type="checkbox" id="lc-3" checked style="accent-color:#60a5fa;">LC3: 내압 + 적설 (폭설)</label>
      <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:#d1d5db;margin:4px 0;cursor:pointer;">
        <input type="checkbox" id="lc-4" checked style="accent-color:#f87171;">LC4: 내압 + 풍 + 적설 (최악)</label>
      <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:#d1d5db;margin:4px 0;cursor:pointer;">
        <input type="checkbox" id="lc-5" checked style="accent-color:#fbbf24;">LC5: 내압 상실 (비상)</label>
    </div>

  </div>

  <!-- ═══════ 고정 영역: 표시 + 프리셋 (항상 보임) ═══════ -->
  <div id="panel-fixed">
    <div class="fixed-sec">
      <div class="st">시각화 모드</div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;">
        <div class="tb on" onclick="setViz('tension')" id="vb-tension">장력</div>
        <div class="tb" onclick="setViz('wind')" id="vb-wind">풍압</div>
        <div class="tb" onclick="setViz('snow')" id="vb-snow">적설</div>
        <div class="tb" onclick="setViz('combined')" id="vb-combined">합산</div>
        <div class="tb" onclick="setViz('deform')" id="vb-deform">변형</div>
        <div class="tb" onclick="setViz('safety')" id="vb-safety">안전율</div>
        <div class="tb" onclick="setViz('cable')" id="vb-cable">케이블</div>
        <div class="tb" onclick="setViz('normal')" id="vb-normal">기본</div>
      </div>

      <div class="st" style="margin-top:12px;">레이어 ON/OFF</div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;">
        <div class="tb on" onclick="togL('outer')" id="lb-outer">외피막</div>
        <div class="tb on" onclick="togL('innerU')" id="lb-innerU">내피(상)</div>
        <div class="tb on" onclick="togL('innerL')" id="lb-innerL">내피(하)</div>
        <div class="tb on" onclick="togL('spacers')" id="lb-spacers">스페이서</div>
        <div class="tb on" onclick="togL('cables')" id="lb-cables">케이블</div>
        <div class="tb on" onclick="togL('foundation')" id="lb-foundation">기초</div>
        <div class="tb" onclick="togL('wind_arrows')" id="lb-wind_arrows">풍향 화살표</div>
        <div class="tb" onclick="togWindFlow()" id="lb-windflow" style="border-color:#38bdf8;color:#38bdf8;">풍류 시각화</div>
      </div>

      <div class="st" style="margin-top:12px;">카메라 뷰</div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;">
        <div class="tb" onclick="camView('3d')">3D 투시</div>
        <div class="tb" onclick="camView('top')">평면 (Top)</div>
        <div class="tb" onclick="camView('east')">단변 (East)</div>
        <div class="tb" onclick="camView('south')">장변 (South)</div>
      </div>
    </div>

    <div class="fixed-sec">
      <div class="st">풍하중 프리셋</div>
      <div class="preset-row">
        <div class="mbtn" onclick="preset('calm')">🌤 무풍</div>
        <div class="mbtn" onclick="preset('normal')">🌬 약풍 15m/s</div>
      </div>
      <div class="preset-row">
        <div class="mbtn" onclick="preset('strong')">💨 강풍 30m/s</div>
        <div class="mbtn" onclick="preset('storm')">🌪 폭풍 45m/s</div>
      </div>

      <div class="st" style="margin-top:10px;">적설 프리셋</div>
      <div class="preset-row">
        <div class="mbtn" onclick="preset('snow_l')">❄ 소설 0.5kN</div>
        <div class="mbtn" onclick="preset('snow_h')">🌨 대설 2.0kN</div>
      </div>

      <div class="st" style="margin-top:10px;">복합 조건</div>
      <div class="preset-row">
        <div class="mbtn" onclick="preset('worst')" style="border-color:#f87171;color:#f87171;">⚠ 최악조건</div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════ 오른쪽 결과 패널 ═══════ -->
<div id="results">
  <h3>📊 해석 결과</h3>
  <div id="res-body">
    <!-- 외피막 -->
    <div class="lcard">
      <div class="lcard-h" style="color:#e5e7eb;"><div class="cdot" style="background:#e5e7eb;"></div>외피막</div>
      <div class="lcard-row"><span class="k">차압 ΔP</span><span class="v" id="r-dp-o">-</span></div>
      <div class="lcard-row"><span class="k">최대 장력</span><span class="v" id="r-t-o">-</span></div>
      <div class="lcard-bar"><div id="bar-t-o" style="width:0%;background:#60a5fa;"></div></div>
      <div class="lcard-row"><span class="k">안전율 (SF)</span><span class="v" id="r-sf-o" style="font-size:16px;">-</span></div>
    </div>

    <!-- 내피 상층 -->
    <div class="lcard">
      <div class="lcard-h" style="color:#fb923c;"><div class="cdot" style="background:#fb923c;"></div>내피 상층</div>
      <div class="lcard-row"><span class="k">차압 ΔP</span><span class="v" id="r-dp-iu">-</span></div>
      <div class="lcard-row"><span class="k">최대 장력</span><span class="v" id="r-t-iu">-</span></div>
      <div class="lcard-bar"><div id="bar-t-iu" style="width:0%;background:#fb923c;"></div></div>
      <div class="lcard-row"><span class="k">안전율 (SF)</span><span class="v" id="r-sf-iu">-</span></div>
    </div>

    <!-- 내피 하층 -->
    <div class="lcard">
      <div class="lcard-h" style="color:#ea580c;"><div class="cdot" style="background:#ea580c;"></div>내피 하층</div>
      <div class="lcard-row"><span class="k">차압 ΔP</span><span class="v" id="r-dp-il">-</span></div>
      <div class="lcard-row"><span class="k">최대 장력</span><span class="v" id="r-t-il">-</span></div>
      <div class="lcard-bar"><div id="bar-t-il" style="width:0%;background:#ea580c;"></div></div>
      <div class="lcard-row"><span class="k">안전율 (SF)</span><span class="v" id="r-sf-il">-</span></div>
    </div>

    <!-- 종합 -->
    <div class="lcard">
      <div class="lcard-h" style="color:#34d399;"><div class="cdot" style="background:#34d399;"></div>종합</div>
      <div class="lcard-row"><span class="k">스페이서 압축력</span><span class="v" id="r-spacer">-</span></div>
      <div class="lcard-row"><span class="k">케이블 최대장력</span><span class="v" id="r-cable">-</span></div>
      <div class="lcard-row"><span class="k">최대 풍압</span><span class="v" id="r-wind">-</span></div>
      <div class="lcard-row"><span class="k">최대 적설압력</span><span class="v" id="r-snow">-</span></div>
      <div class="lcard-row"><span class="k">최대 변형량</span><span class="v" id="r-defl">-</span></div>
      <div class="lcard-row"><span class="k">내압 요구량</span><span class="v" id="r-reqp">-</span></div>
    </div>

    <!-- 케이블 해석 결과 -->
    <div class="lcard" style="border-color:#f59e0b55;">
      <div class="lcard-h" style="color:#f59e0b;"><div class="cdot" style="background:#f59e0b;"></div>케이블 해석</div>
      <div class="lcard-row"><span class="k">케이블 사양</span><span class="v" id="r-cspec" style="font-size:11px;">-</span></div>
      <div class="lcard-row"><span class="k">최대 케이블 장력</span><span class="v" id="r-cable2">-</span></div>
      <div class="lcard-row"><span class="k">케이블 안전율</span><span class="v" id="r-csf" style="font-size:16px;">-</span></div>
      <div class="lcard-row"><span class="k">허용 장력</span><span class="v" id="r-callow">-</span></div>
      <div class="lcard-row"><span class="k">최악 하중조합</span><span class="v" id="r-clc" style="font-size:11px;">-</span></div>
      <div class="lcard-row"><span class="k">풍상측 장력</span><span class="v" id="r-cwind-max">-</span></div>
      <div class="lcard-row"><span class="k">풍하측 장력</span><span class="v" id="r-cwind-lee">-</span></div>
      <div class="lcard-row"><span class="k">정상부 장력</span><span class="v" id="r-ctop">-</span></div>
      <div class="lcard-row" style="border-top:1px solid #2a3545;margin-top:4px;padding-top:4px;"><span class="k">최대 응력</span><span class="v" id="r-cstress">-</span></div>
      <div class="lcard-row"><span class="k">파단 응력</span><span class="v" id="r-cbreak-stress">-</span></div>
      <div class="lcard-row"><span class="k">케이블 신장량</span><span class="v" id="r-celongation">-</span></div>
      <div class="lcard-row"><span class="k">변형률</span><span class="v" id="r-cstrain">-</span></div>
    </div>

    <div class="verdict" id="r-verdict">-</div>
  </div>

  <!-- 치수 입력 + 로고 -->
  <div id="res-footer">
    <div class="dim-sec">
      <div class="st">치수 조정</div>
      <div class="dim-row">
        <label>폭 (W)</label>
        <input type="number" id="d-width" value="{params.get('width',43282)}" min="5000" max="200000" step="100">
        <span class="dim-u">mm</span>
      </div>
      <div class="dim-row">
        <label>길이 (L)</label>
        <input type="number" id="d-length" value="{params.get('length',68580)}" min="5000" max="200000" step="100">
        <span class="dim-u">mm</span>
      </div>
      <div class="dim-row">
        <label>높이 (H)</label>
        <input type="number" id="d-height" value="{params.get('height',15850)}" min="3000" max="80000" step="100">
        <span class="dim-u">mm</span>
      </div>
      <div class="dim-row">
        <label>케이블 간격</label>
        <input type="number" id="d-cspace" value="{params.get('cable_spacing',3600)}" min="500" max="10000" step="100">
        <span class="dim-u">mm</span>
      </div>
      <button class="dim-apply" onclick="applyDims()">치수 적용 &amp; 재생성</button>
    </div>
    <button class="btn-techguide" onclick="openTechGuide()">📖 기술해설서 (PDF)</button>
    <button class="btn-opinion" onclick="showOpinion()">📋 종합의견</button>
  </div>
</div>

<!-- ═══════ 종합의견 모달 ═══════ -->
<div id="opinion-overlay" onclick="if(event.target===this)closeOpinion()">
  <div id="opinion-modal">
    <div id="opinion-modal-header">
      <h3>📋 구조 시뮬레이션 종합의견</h3>
      <button class="close-btn" onclick="closeOpinion()">&times;</button>
    </div>
    <div id="opinion-body">
      <div id="opinion-content"></div>
    </div>
    <div id="opinion-footer">
      <button class="btn-copy-opinion" onclick="copyOpinion()">📄 텍스트 복사</button>
      <button class="btn-close-opinion" onclick="closeOpinion()">닫기</button>
    </div>
  </div>
</div>

<!-- 풍류 범례 -->
<div id="wind-legend">
  <span style="color:#38bdf8;font-weight:700;">풍속</span>
  <span style="color:#6b7280;">저속</span>
  <canvas id="wl-gradient" width="120" height="8"></canvas>
  <span style="color:#6b7280;">고속</span>
  <span style="color:#f87171;margin-left:8px;">●</span><span style="color:#6b7280;">와류</span>
</div>

<!-- 범례 -->
<div id="legend">
  <span id="leg-t" style="color:#60a5fa;font-weight:700;min-width:50px;">장력</span>
  <span id="leg-min" style="color:#6b7280;min-width:35px;">0</span>
  <canvas id="legend-gradient" width="160" height="8"></canvas>
  <span id="leg-max" style="color:#6b7280;min-width:45px;text-align:right;">Max</span>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ================================================================
//  탭 제어
// ================================================================
window.openTab=function(id){{
  document.querySelectorAll('.tp').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  // 탭 버튼 활성화
  const idx={{'t-load':0,'t-layer':1,'t-mat':2,'t-cable':3}}[id]||0;
  document.querySelectorAll('.tab')[idx].classList.add('on');
}};

// ================================================================
//  기본 상수
// ================================================================
let W={params.get('width',43282)}, L={params.get('length',68580)}, H={params.get('height',15850)};
const S=0.001;
let a=W/2*S, b=L/2*S, Hs=H*S;
let a_mm=W/2, b_mm=L/2, H_mm=H;

function domeZ(x,y,h){{ let rx=1-(x/(W/2*S))**2, ry=1-(y/(L/2*S))**2;
  return (rx>0&&ry>0)?(h||Hs)*Math.sqrt(rx)*Math.sqrt(ry):0; }}
function domeZ_mm(x,y){{ let rx=1-(x/a_mm)**2, ry=1-(y/b_mm)**2;
  return (rx>0&&ry>0)?H_mm*Math.sqrt(rx)*Math.sqrt(ry):0; }}

// ================================================================
//  물리 엔진
// ================================================================
const Ph={{
  rho:1.225,
  mc:function(x,y,He){{
    const e=10,am=a_mm,bm=b_mm;
    const ax=Math.min(Math.max(x,-am+e*2),am-e*2);
    const ay=Math.min(Math.max(y,-bm+e*2),bm-e*2);
    function zf(px,py){{let rx=1-(px/am)**2,ry=1-(py/bm)**2;return(rx>0&&ry>0)?He*Math.sqrt(rx)*Math.sqrt(ry):0;}}
    const z0=zf(ax,ay),zxp=zf(ax+e,ay),zxm=zf(ax-e,ay);
    const zyp=zf(ax,ay+e),zym=zf(ax,ay-e);
    const zpp=zf(ax+e,ay+e),zpm=zf(ax+e,ay-e);
    const zmp=zf(ax-e,ay+e),zmm=zf(ax-e,ay-e);
    const fx=(zxp-zxm)/(2*e),fy=(zyp-zym)/(2*e);
    const fxx=(zxp-2*z0+zxm)/(e*e),fyy=(zyp-2*z0+zym)/(e*e);
    const fxy=(zpp-zpm-zmp+zmm)/(4*e*e);
    const d=Math.pow(1+fx*fx+fy*fy,1.5);
    return d>1e-12?((1+fy*fy)*fxx-2*fx*fy*fxy+(1+fx*fx)*fyy)/(2*d):0;
  }},
  T:function(x,y,dp,He){{
    const k=Math.abs(this.mc(x,y,He));
    if(k<1e-10)return Math.abs(dp)*Math.max(a_mm,b_mm)/2000;
    return(Math.abs(dp)*1e-6)/(2*k)*1000;
  }},
  wp:function(x,y,v,dir){{
    const q=0.5*this.rho*v*v,rad=dir*Math.PI/180;
    const wx=Math.cos(rad),wy=Math.sin(rad);
    const nx=x/a_mm,ny=y/b_mm,cosT=nx*wx+ny*wy;
    const z=domeZ_mm(x,y),sl=z/H_mm;
    let Cp;
    if(cosT>0)Cp=(0.8-1.8*sl*sl)*cosT;
    else Cp=(-0.4-0.5*sl)*(Math.abs(cosT)*0.7+0.3);
    Cp-=0.3*Math.abs(nx*(-wy)+ny*wx)*sl;
    return q*Cp;
  }},
  sp:function(x,y,sn){{
    const e=50;
    const zxp=domeZ_mm(Math.min(x+e,a_mm*0.99),y),zxm=domeZ_mm(Math.max(x-e,-a_mm*0.99),y);
    const zyp=domeZ_mm(x,Math.min(y+e,b_mm*0.99)),zym=domeZ_mm(x,Math.max(y-e,-b_mm*0.99));
    const g=Math.sqrt(((zxp-zxm)/(2*e))**2+((zyp-zym)/(2*e))**2);
    return sn*1000*Math.max(0,0.8*(1-Math.atan(g)*180/Math.PI/60));
  }},
  defl:function(T,E,t,span){{return(T/1000*span)/(E*t);}},
  cableT:function(T,sp){{return T*sp/1000;}},
  sf:function(T,str){{const t50=T*0.05;return t50>0?str/t50:99;}},
  reqP:function(v,sn){{return 0.5*this.rho*v*v*1.2+sn*1000*0.8+50;}}
}};

// ================================================================
//  케이블 재질 DB 및 해석 엔진
// ================================================================
const CableDB={{
  'sts304_4':{{name:'STS304 1x19 ∅4mm',dia:4.0,breakLoad:9.0,elastic:130,struct:'1x19'}},
  'sts304_6':{{name:'STS304 1x19 ∅6mm',dia:6.0,breakLoad:20.0,elastic:130,struct:'1x19'}},
  'sts316_6':{{name:'STS316 1x19 ∅6mm',dia:6.0,breakLoad:19.5,elastic:125,struct:'1x19'}},
  'sts304_8':{{name:'STS304 1x19 ∅8mm',dia:8.0,breakLoad:35.0,elastic:130,struct:'1x19'}},
  'galv_6':{{name:'아연도금 6x19 ∅6mm',dia:6.0,breakLoad:17.5,elastic:110,struct:'6x19'}},
  'galv_8':{{name:'아연도금 6x19 ∅8mm',dia:8.0,breakLoad:30.0,elastic:110,struct:'6x19'}},
  'custom':{{name:'직접 입력',dia:4.0,breakLoad:9.0,elastic:130,struct:'-'}}
}};
let curCableMat='sts304_4';

window.setCableMat=function(key){{
  curCableMat=key;
  document.querySelectorAll('.mbtn[id^="cm-"]').forEach(b=>b.classList.remove('on'));
  const b=document.getElementById('cm-'+key);if(b)b.classList.add('on');
  if(key!=='custom'){{
    const m=CableDB[key];
    document.getElementById('s-cdia').value=m.dia;
    document.getElementById('s-cbreak').value=m.breakLoad;
    document.getElementById('s-celastic').value=m.elastic;
    document.getElementById('v-cdia').textContent=m.dia.toFixed(1);
    document.getElementById('v-cbreak').textContent=m.breakLoad.toFixed(1);
    document.getElementById('v-celastic').textContent=m.elastic;
  }}
  runSim();
}};

// 케이블 해석 엔진
const CableEng={{
  // 하중 조합별 케이블 장력 계산
  // LC1: 내압+자중(평상시), LC2: 내압+풍하중, LC3: 내압+적설
  // LC4: 내압+풍+적설(최악), LC5: 내압상실(비상)
  calcLoadCombinations:function(xm,ym,zm,Ho,dpO,wSpd,wDir,sLoad,cSp){{
    if(zm<1)return null;
    const results=[];
    // LC1: 내압 + 자중 (평상시 - 풍속0, 적설0)
    const tLC1=Ph.T(xm,ym,Math.abs(dpO),Ho);
    results.push({{id:'LC1',name:'내압+자중',cableT:Ph.cableT(tLC1,cSp),memT:tLC1}});
    // LC2: 내압 + 풍하중 (풍속 그대로, 적설 0)
    const wp2=Ph.wp(xm,ym,wSpd,wDir);
    const net2=dpO+wp2;
    const tLC2=Ph.T(xm,ym,Math.abs(net2>0?net2:dpO-wp2),Ho);
    results.push({{id:'LC2',name:'내압+풍하중',cableT:Ph.cableT(tLC2,cSp),memT:tLC2}});
    // LC3: 내압 + 적설 (풍속0)
    const sp3=Ph.sp(xm,ym,sLoad);
    const net3=dpO-sp3;
    const tLC3=Ph.T(xm,ym,Math.abs(net3>0?net3:dpO+sp3),Ho);
    results.push({{id:'LC3',name:'내압+적설',cableT:Ph.cableT(tLC3,cSp),memT:tLC3}});
    // LC4: 내압 + 풍 + 적설 (최악)
    const net4=dpO+wp2-sp3;
    const tLC4=Ph.T(xm,ym,Math.abs(net4>0?net4:dpO-wp2-sp3),Ho);
    results.push({{id:'LC4',name:'내압+풍+적설',cableT:Ph.cableT(tLC4,cSp),memT:tLC4}});
    // LC5: 내압 상실 (P_int=0, 자중+풍압만)
    const net5=wp2-sp3;
    const tLC5=Ph.T(xm,ym,Math.abs(net5),Ho)*0.3;// 내압없으면 막이 이완, 유효장력 감소
    results.push({{id:'LC5',name:'내압상실(비상)',cableT:Ph.cableT(tLC5,cSp),memT:tLC5}});
    return results;
  }},
  // 케이블 안전율 계산
  safeFactor:function(cableForce_kN, breakLoad_kN){{
    return cableForce_kN>0?breakLoad_kN/cableForce_kN:99;
  }},
  // 허용 장력 계산
  allowableForce:function(breakLoad_kN, reqSF){{
    return breakLoad_kN/reqSF;
  }},
  // 케이블 단면적 (mm²)
  cableArea:function(dia_mm){{
    return Math.PI/4*dia_mm*dia_mm;
  }},
  // 케이블 응력 (MPa = N/mm²)
  cableStress:function(force_kN, dia_mm){{
    const A=this.cableArea(dia_mm);
    return A>0?(force_kN*1000)/A:0; // kN → N, / mm² = MPa
  }},
  // 케이블 파단응력 (MPa)
  breakStress:function(breakLoad_kN, dia_mm){{
    const A=this.cableArea(dia_mm);
    return A>0?(breakLoad_kN*1000)/A:0;
  }},
  // 케이블 신장량 (mm) — Hooke's Law: δ = F·L / (E·A)
  cableElongation:function(force_kN, span_mm, E_GPa, dia_mm){{
    const A=this.cableArea(dia_mm);
    const E_MPa=E_GPa*1000; // GPa → MPa
    return(A>0&&E_MPa>0)?(force_kN*1000*span_mm)/(E_MPa*A):0;
  }},
  // 케이블 변형률 (%)
  cableStrain:function(force_kN, E_GPa, dia_mm){{
    const A=this.cableArea(dia_mm);
    const E_MPa=E_GPa*1000;
    return(A>0&&E_MPa>0)?(force_kN*1000)/(E_MPa*A)*100:0;
  }},
  // 위치 판별 (풍상/풍하/정상부)
  positionType:function(xm,ym,zm,wDir){{
    const rad=wDir*Math.PI/180;
    const wx=Math.cos(rad),wy=Math.sin(rad);
    const nx=xm/a_mm,ny=ym/b_mm;
    const cosT=nx*wx+ny*wy;
    const sl=zm/H_mm;
    if(sl>0.85)return 'top';      // 정상부
    if(cosT<-0.3)return 'windward'; // 풍상측
    if(cosT>0.3)return 'leeward';  // 풍하측
    return 'side';                  // 측면
  }}
}};

// ================================================================
//  압력분배 모드
// ================================================================
let pressureMode='equal';
function calcPMode(mode){{
  switch(mode){{
    case 'equal':  return {{r1:1/3, r2:2/3}};
    case 'outer':  return {{r1:0.6, r2:0.8}};
    case 'inner':  return {{r1:0.8, r2:0.9}};
    case 'single': return {{r1:0.95,r2:0.97}};
  }}
  return {{r1:1/3,r2:2/3}};
}}
window.setPMode=function(m){{
  pressureMode=m;
  document.querySelectorAll('.mbtn[id^="pm-"]').forEach(b=>b.classList.remove('on'));
  const b=document.getElementById('pm-'+m); if(b)b.classList.add('on');
  const p=calcPMode(m);
  document.getElementById('pm-info').textContent=
    'P_gap1='+(p.r1*100).toFixed(1)+'% | P_gap2='+(p.r2*100).toFixed(1)+'% of P_int';
  runSim();
}};

// ================================================================
//  Three.js 씬
// ================================================================
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x111827);
scene.fog=new THREE.Fog(0x111827,150,350);
const camera=new THREE.PerspectiveCamera(45,(innerWidth-600)/innerHeight,0.1,500);
const renderer=new THREE.WebGLRenderer({{antialias:true}});
renderer.setSize(innerWidth,innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0x6677aa,0.6));
const dl=new THREE.DirectionalLight(0xffffff,0.9);
dl.position.set(30,50,20);dl.castShadow=true;scene.add(dl);
scene.add(new THREE.DirectionalLight(0xffeedd,0.4).translateX(-20).translateY(30).translateZ(-30));
const gnd=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshPhongMaterial({{color:0x1a2a1a}}));
gnd.rotation.x=-Math.PI/2;gnd.position.y=-0.05;gnd.receiveShadow=true;scene.add(gnd);
scene.add(new THREE.GridHelper(200,40,0x2a3a2a,0x1a2a1a).translateY(-0.02));

// ================================================================
//  삼중막 메시
// ================================================================
const RU=56,RV=56,layers={{}};
function makeDome(hScale,col,op){{
  const geo=new THREE.BufferGeometry();
  const vs=[],ns=[],uv2=[],cs=[],ids=[];
  for(let j=0;j<=RV;j++)for(let i=0;i<=RU;i++){{
    const u=i/RU,v=j/RV,x=(u-0.5)*2*a,y=(v-0.5)*2*b,z=domeZ(x,y,Hs*hScale);
    vs.push(x,z,y);
    const dx=0.01,dy=0.01;
    const nx2=(domeZ(x-dx,y,Hs*hScale)-domeZ(x+dx,y,Hs*hScale))/(2*dx);
    const ny2=(domeZ(x,y-dy,Hs*hScale)-domeZ(x,y+dy,Hs*hScale))/(2*dy);
    const nl=Math.sqrt(nx2*nx2+ny2*ny2+1);
    ns.push(nx2/nl,1/nl,ny2/nl);uv2.push(u,v);cs.push(col[0],col[1],col[2]);
  }}
  for(let j=0;j<RV;j++)for(let i=0;i<RU;i++){{
    const a0=j*(RU+1)+i,b0=a0+1,c0=a0+RU+1,d0=c0+1;
    ids.push(a0,b0,d0,a0,d0,c0);
  }}
  geo.setAttribute('position',new THREE.Float32BufferAttribute(vs,3));
  geo.setAttribute('normal',new THREE.Float32BufferAttribute(ns,3));
  geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv2,2));
  geo.setAttribute('color',new THREE.Float32BufferAttribute(cs,3));
  geo.setIndex(ids);
  const m=new THREE.Mesh(geo,new THREE.MeshPhongMaterial({{vertexColors:true,transparent:true,opacity:op,side:2,shininess:30}}));
  m.castShadow=true;return m;
}}

layers.outer=makeDome(1.0,[0.96,0.94,0.91],0.88);scene.add(layers.outer);
layers.innerU=makeDome(0.96,[1.0,0.55,0.25],0.6);scene.add(layers.innerU);
layers.innerL=makeDome(0.92,[1.0,0.4,0.15],0.5);scene.add(layers.innerL);

// 스페이서
layers.spacers=new THREE.Group();scene.add(layers.spacers);
function buildSpacers(){{
  while(layers.spacers.children.length)layers.spacers.remove(layers.spacers.children[0]);
  const mat=new THREE.LineBasicMaterial({{color:0x44cc44,linewidth:2}});
  const pO=layers.outer.geometry.getAttribute('position');
  const pIU=layers.innerU.geometry.getAttribute('position');
  const pIL=layers.innerL.geometry.getAttribute('position');
  const step=6;
  for(let j=2;j<RV-1;j+=step)for(let i=2;i<RU-1;i+=step){{
    const vi=j*(RU+1)+i;
    if(pO.getY(vi)<0.3)continue;
    const pts1=[new THREE.Vector3(pO.getX(vi),pO.getY(vi),pO.getZ(vi)),
                new THREE.Vector3(pIU.getX(vi),pIU.getY(vi),pIU.getZ(vi))];
    const pts2=[new THREE.Vector3(pIU.getX(vi),pIU.getY(vi),pIU.getZ(vi)),
                new THREE.Vector3(pIL.getX(vi),pIL.getY(vi),pIL.getZ(vi))];
    layers.spacers.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts1),mat));
    layers.spacers.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts2),mat));
  }}
}}

function updateInner(g1mm,g2mm){{
  const pO=layers.outer.geometry.getAttribute('position');
  const pIU=layers.innerU.geometry.getAttribute('position');
  const pIL=layers.innerL.geometry.getAttribute('position');
  const cnt=(RU+1)*(RV+1);
  const VE=5;
  const g1=g1mm*S*VE, g2=(g1mm+g2mm)*S*VE;
  for(let i=0;i<cnt;i++){{
    const ox=pO.getX(i),oy=pO.getY(i),oz=pO.getZ(i);
    if(oy>0.05){{
      const s1=Math.max(0.1,1-g1/Math.max(oy,0.1));
      const s2=Math.max(0.05,1-g2/Math.max(oy,0.1));
      pIU.setXYZ(i,ox*s1,oy-g1,oz*s1);
      pIL.setXYZ(i,ox*s2,oy-g2,oz*s2);
    }}else{{pIU.setXYZ(i,ox,0,oz);pIL.setXYZ(i,ox,0,oz);}}
  }}
  pIU.needsUpdate=true;pIL.needsUpdate=true;
  layers.innerU.geometry.computeVertexNormals();
  layers.innerL.geometry.computeVertexNormals();
  buildSpacers();
}}
updateInner(300,200);

// 케이블, 기초, 풍향
layers.cables=new THREE.Group();scene.add(layers.cables);
function buildCables(sp){{
  while(layers.cables.children.length)layers.cables.remove(layers.cables.children[0]);
  const cm=new THREE.LineBasicMaterial({{color:0x888888}});const spS=sp*S;
  for(let d=0;d<2;d++)for(let off=-b-a;off<=b+a;off+=spS){{
    const pts=[];
    for(let t=0;t<=60;t++){{let s2=t/60,x=-a+s2*2*a,y=d===0?(x+off):(-x+off);
      if(y>=-b&&y<=b){{let z=domeZ(x,y);if(z>0.01)pts.push(new THREE.Vector3(x,z,y));}}}}
    if(pts.length>2)layers.cables.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),cm));
  }}
}}
buildCables({params.get('cable_spacing',3600)});

layers.foundation=new THREE.Group();scene.add(layers.foundation);
const fm=new THREE.MeshPhongMaterial({{color:0x666666,transparent:true,opacity:0.7}});
[[-a-0.3,-b-0.3,2*a+0.6,0.3],[-a-0.3,b,2*a+0.6,0.3],[-a-0.3,-b,0.3,2*b],[a,-b,0.3,2*b]].forEach(r=>{{
  const m=new THREE.Mesh(new THREE.BoxGeometry(r[2],0.15,r[3]),fm);
  m.position.set(r[0]+r[2]/2,-0.075,r[1]+r[3]/2);layers.foundation.add(m);}});

layers.wind_arrows=new THREE.Group();layers.wind_arrows.visible=false;scene.add(layers.wind_arrows);
function buildWA(dir){{
  while(layers.wind_arrows.children.length)layers.wind_arrows.remove(layers.wind_arrows.children[0]);
  const rad=dir*Math.PI/180;
  for(let i=-2;i<=2;i++){{
    const o=new THREE.Vector3(-Math.cos(rad)*(a+10)+Math.sin(rad)*i*b/2.5,Hs*0.5,
      -Math.sin(rad)*(b+10)-Math.cos(rad)*i*b/2.5);
    layers.wind_arrows.add(new THREE.ArrowHelper(
      new THREE.Vector3(Math.cos(rad),0,Math.sin(rad)).normalize(),o,a*0.8,0x60a5fa,a*0.15,a*0.08));
  }}
}}
buildWA(0);

// ================================================================
//  치수 재설정 & 돔 재생성
// ================================================================
function rebuildDomeMesh(mesh,hScale,col,op){{
  const geo=mesh.geometry;
  const pa=geo.getAttribute('position'), na=geo.getAttribute('normal'),
        uva=geo.getAttribute('uv'), ca=geo.getAttribute('color');
  for(let j=0;j<=RV;j++)for(let i=0;i<=RU;i++){{
    const idx=j*(RU+1)+i;
    const u=i/RU,v=j/RV,x=(u-0.5)*2*a,y=(v-0.5)*2*b,z=domeZ(x,y,Hs*hScale);
    pa.setXYZ(idx,x,z,y);
    const dx=0.01,dy=0.01;
    const nx2=(domeZ(x-dx,y,Hs*hScale)-domeZ(x+dx,y,Hs*hScale))/(2*dx);
    const ny2=(domeZ(x,y-dy,Hs*hScale)-domeZ(x,y+dy,Hs*hScale))/(2*dy);
    const nl=Math.sqrt(nx2*nx2+ny2*ny2+1);
    na.setXYZ(idx,nx2/nl,1/nl,ny2/nl);
    uva.setXY(idx,u,v);
    ca.setXYZ(idx,col[0],col[1],col[2]);
  }}
  pa.needsUpdate=true;na.needsUpdate=true;uva.needsUpdate=true;ca.needsUpdate=true;
  geo.computeBoundingSphere();
}}

function rebuildFoundation(){{
  while(layers.foundation.children.length)layers.foundation.remove(layers.foundation.children[0]);
  const fm2=new THREE.MeshPhongMaterial({{color:0x666666,transparent:true,opacity:0.7}});
  [[-a-0.3,-b-0.3,2*a+0.6,0.3],[-a-0.3,b,2*a+0.6,0.3],[-a-0.3,-b,0.3,2*b],[a,-b,0.3,2*b]].forEach(r=>{{
    const m=new THREE.Mesh(new THREE.BoxGeometry(r[2],0.15,r[3]),fm2);
    m.position.set(r[0]+r[2]/2,-0.075,r[1]+r[3]/2);layers.foundation.add(m);}});
}}

window.applyDims=function(){{
  const nw=parseInt(document.getElementById('d-width').value)||W;
  const nl2=parseInt(document.getElementById('d-length').value)||L;
  const nh=parseInt(document.getElementById('d-height').value)||H;
  const ncs=parseInt(document.getElementById('d-cspace').value)||3600;
  // 전역 치수 업데이트
  W=nw; L=nl2; H=nh;
  a=W/2*S; b=L/2*S; Hs=H*S;
  a_mm=W/2; b_mm=L/2; H_mm=H;
  // 왼쪽 패널 케이블 간격 슬라이더 동기화
  const csSlider=document.getElementById('s-cspace');
  if(csSlider){{csSlider.value=ncs;}}
  const csVal=document.getElementById('v-cspace');
  if(csVal){{csVal.textContent=ncs;}}
  // 헤더 정보 업데이트
  const hi=document.getElementById('header-info');
  if(hi){{hi.innerHTML='<span style="color:#34d399;font-weight:700;">'+W.toLocaleString()+'</span> × <span style="color:#34d399;font-weight:700;">'+L.toLocaleString()+'</span> × <span style="color:#34d399;font-weight:700;">'+H.toLocaleString()+'</span> mm &nbsp;|&nbsp; '+(W*L/1e6).toLocaleString(undefined,{{maximumFractionDigits:0}})+' m²';}}
  // 메시 재생성
  rebuildDomeMesh(layers.outer,1.0,[0.96,0.94,0.91],0.88);
  rebuildDomeMesh(layers.innerU,0.96,[1.0,0.55,0.25],0.6);
  rebuildDomeMesh(layers.innerL,0.92,[1.0,0.4,0.15],0.5);
  // 갭 적용
  const g1=parseInt(document.getElementById('s-gap1').value)||300;
  const g2=parseInt(document.getElementById('s-gap2').value)||200;
  updateInner(g1,g2);
  // 케이블, 기초, 풍향 재생성
  buildCables(ncs);
  rebuildFoundation();
  buildWA(parseFloat(document.getElementById('s-winddir').value)||0);
  // 시뮬레이션 재실행
  runSim();
}};

// ================================================================
//  기술해설서 PDF 열기
// ================================================================
window.openTechGuide=function(){{
  // HTML 파일과 같은 폴더 기준으로 PDF 경로 결정
  const guideFileName='AirDome_시뮬레이션_기술해설서.pdf';
  // 방법 1: file:// 프로토콜 (로컬 실행 시)
  const basePath=window.location.href.substring(0,window.location.href.lastIndexOf('/')+1);
  const pdfUrl=basePath+encodeURIComponent(guideFileName);
  // 새 탭에서 PDF 열기
  const w=window.open(pdfUrl,'_blank');
  if(!w){{alert('팝업이 차단되었습니다.\\n브라우저 설정에서 팝업 차단을 해제해주세요.');}}
}};

// ================================================================
//  컬러맵
// ================================================================
let vizMode='tension';
function v2c(val,mn,mx){{let t=(mx>mn)?(val-mn)/(mx-mn):0.5;t=Math.max(0,Math.min(1,t));
  let r,g,b2;if(t<0.25){{r=0;g=t*4;b2=1;}}else if(t<0.5){{r=0;g=1;b2=1-(t-0.25)*4;}}
  else if(t<0.75){{r=(t-0.5)*4;g=1;b2=0;}}else{{r=1;g=1-(t-0.75)*4;b2=0;}}return[r,g,b2];}}
function sf2c(sf){{if(sf>=5)return[0.2,0.9,0.3];if(sf>=3){{let t=(sf-3)/2;return[0.2+0.8*(1-t),0.5+0.4*t,0.1];}}
  if(sf>=1.5){{let t=(sf-1.5)/1.5;return[1,0.3+0.2*t,0];}}return[1,0.1,0.1];}}

function applyC(geo,data,mn,mx,mode,dc){{
  const ca=geo.getAttribute('color'),pa=geo.getAttribute('position'),n=(RU+1)*(RV+1);
  for(let i=0;i<n;i++){{const h=pa.getY(i);
    if(h<0.05){{ca.setXYZ(i,0.15,0.15,0.15);continue;}}
    if(mode==='normal'){{ca.setXYZ(i,dc[0],dc[1],dc[2]);continue;}}
    if(mode==='safety'){{const[r,g,b2]=sf2c(data[i]);ca.setXYZ(i,r,g,b2);}}
    else{{const[r,g,b2]=v2c(data[i],mn,mx);ca.setXYZ(i,r,g,b2);}}
  }}ca.needsUpdate=true;}}

function updateLeg(mode,mn,mx){{
  const c=document.getElementById('legend-gradient').getContext('2d');
  for(let i=0;i<160;i++){{let r,g,b2;
    if(mode==='safety')[r,g,b2]=sf2c(1+i/160*4);else[r,g,b2]=v2c(i/160,0,1);
    c.fillStyle=`rgb(${{r*255|0}},${{g*255|0}},${{b2*255|0}})`;c.fillRect(i,0,1,8);}}
  document.getElementById('leg-min').textContent=mn;
  document.getElementById('leg-max').textContent=mx;}}

// ================================================================
//  시뮬레이션 실행
// ================================================================
function runSim(){{
  const pInt=+document.getElementById('s-pressure').value;
  const wSpd=+document.getElementById('s-wind').value;
  const sLoad=+document.getElementById('s-snow').value;
  const wDir=+document.getElementById('s-winddir').value;
  const gap1=+document.getElementById('s-gap1').value;
  const gap2=+document.getElementById('s-gap2').value;
  const thO=+document.getElementById('s-thick-o').value;
  const thI=+document.getElementById('s-thick-i').value;
  const strO=+document.getElementById('s-str-o').value;
  const strI=+document.getElementById('s-str-i').value;
  const E=+document.getElementById('s-elastic').value;
  const cSp=+document.getElementById('s-cspace').value;

  // 값 표시
  document.getElementById('v-pressure').textContent=pInt;
  document.getElementById('v-wind').textContent=wSpd;
  document.getElementById('v-snow').textContent=sLoad.toFixed(1);
  document.getElementById('v-winddir').textContent=wDir;
  document.getElementById('v-gap1').textContent=gap1;
  document.getElementById('v-gap2').textContent=gap2;
  document.getElementById('v-thick-o').textContent=thO.toFixed(1);
  document.getElementById('v-thick-i').textContent=thI.toFixed(1);
  document.getElementById('v-str-o').textContent=strO;
  document.getElementById('v-str-i').textContent=strI;
  document.getElementById('v-elastic').textContent=E;
  document.getElementById('v-cspace').textContent=cSp;

  // 압력분배
  const pm=calcPMode(pressureMode);
  const pG1=pInt*pm.r1, pG2=pInt*pm.r2;
  const dpO=pG1, dpIU=pG1-pG2, dpIL=pG2-pInt;

  // 압력 다이어그램
  document.getElementById('pd-o').textContent=Math.abs(dpO).toFixed(0)+' Pa';
  document.getElementById('pd-g1').textContent=pG1.toFixed(0)+' Pa';
  document.getElementById('pd-iu').textContent=Math.abs(dpIU).toFixed(0)+' Pa';
  document.getElementById('pd-g2').textContent=pG2.toFixed(0)+' Pa';
  document.getElementById('pd-il').textContent=Math.abs(dpIL).toFixed(0)+' Pa';
  document.getElementById('pd-int').textContent=pInt+' Pa';

  updateInner(gap1,gap2);buildCables(cSp);buildWA(wDir);

  const Ho=H_mm, Hiu=H_mm*(1-gap1*S/Hs), Hil=H_mm*(1-(gap1+gap2)*S/Hs);
  const N=(RU+1)*(RV+1);
  const dO=new Float32Array(N),dIU=new Float32Array(N),dIL=new Float32Array(N);
  const wD=new Float32Array(N),snD=new Float32Array(N);
  const cmbD=new Float32Array(N),defD=new Float32Array(N),sfD=new Float32Array(N),cbD=new Float32Array(N);
  let mxTO=0,mxTIU=0,mxTIL=0,mxW=-1e9,mnW=1e9,mxSn=0,mxCmb=0,mxDef=0,mxCb=0;
  let mSFo=99,mSFiu=99,mSFil=99;

  for(let j=0;j<=RV;j++)for(let i=0;i<=RU;i++){{
    const vi=j*(RU+1)+i,u=i/RU,v=j/RV;
    const xm=(u-0.5)*2*a_mm,ym=(v-0.5)*2*b_mm,zm=domeZ_mm(xm,ym);
    if(zm<1){{dO[vi]=0;dIU[vi]=0;dIL[vi]=0;wD[vi]=0;snD[vi]=0;cmbD[vi]=0;defD[vi]=0;sfD[vi]=99;cbD[vi]=0;continue;}}
    const wp=Ph.wp(xm,ym,wSpd,wDir),sp2=Ph.sp(xm,ym,sLoad);
    const netO=dpO+wp-sp2;
    const tO=Ph.T(xm,ym,Math.abs(netO>0?netO:dpO-wp-sp2),Ho);
    const tIU=Ph.T(xm,ym,Math.abs(dpIU),Hiu);
    const tIL=Ph.T(xm,ym,Math.abs(dpIL),Hil);
    const def=Ph.defl(tO,E,thO,Math.min(Math.sqrt(xm*xm+ym*ym)+100,W/2));
    const cb=Ph.cableT(tO,cSp);
    dO[vi]=tO;dIU[vi]=tIU;dIL[vi]=tIL;wD[vi]=wp;snD[vi]=sp2;
    cmbD[vi]=tO;defD[vi]=def;cbD[vi]=cb;
    const sfo=Ph.sf(tO,strO),sfiu=Ph.sf(tIU,strI),sfil=Ph.sf(tIL,strI);
    sfD[vi]=Math.min(sfo,sfiu,sfil);
    if(tO>mxTO)mxTO=tO;if(tIU>mxTIU)mxTIU=tIU;if(tIL>mxTIL)mxTIL=tIL;
    if(wp>mxW)mxW=wp;if(wp<mnW)mnW=wp;if(sp2>mxSn)mxSn=sp2;
    if(tO>mxCmb)mxCmb=tO;if(def>mxDef)mxDef=def;if(cb>mxCb)mxCb=cb;
    if(zm>H_mm*0.05){{if(sfo<mSFo)mSFo=sfo;if(sfiu<mSFiu)mSFiu=sfiu;if(sfil<mSFil)mSFil=sfil;}}
  }}

  // 결과 업데이트
  const u='<span class="u">';
  document.getElementById('r-dp-o').innerHTML=Math.abs(dpO).toFixed(0)+u+'Pa</span>';
  document.getElementById('r-t-o').innerHTML=(mxTO/1000).toFixed(1)+u+'kN/m</span>';
  document.getElementById('bar-t-o').style.width=Math.min(100,mxTO/300)+'%';
  const sfoE=document.getElementById('r-sf-o');sfoE.textContent=mSFo.toFixed(2);
  sfoE.className='v '+(mSFo>=3?'sf-safe':mSFo>=1.5?'sf-warn':'sf-danger');

  document.getElementById('r-dp-iu').innerHTML=Math.abs(dpIU).toFixed(0)+u+'Pa</span>';
  document.getElementById('r-t-iu').innerHTML=(mxTIU/1000).toFixed(2)+u+'kN/m</span>';
  document.getElementById('bar-t-iu').style.width=Math.min(100,mxTIU/100)+'%';
  const siuE=document.getElementById('r-sf-iu');siuE.textContent=mSFiu.toFixed(2);
  siuE.className='v '+(mSFiu>=3?'sf-safe':mSFiu>=1.5?'sf-warn':'sf-danger');

  document.getElementById('r-dp-il').innerHTML=Math.abs(dpIL).toFixed(0)+u+'Pa</span>';
  document.getElementById('r-t-il').innerHTML=(mxTIL/1000).toFixed(2)+u+'kN/m</span>';
  document.getElementById('bar-t-il').style.width=Math.min(100,mxTIL/100)+'%';
  const silE=document.getElementById('r-sf-il');silE.textContent=mSFil.toFixed(2);
  silE.className='v '+(mSFil>=3?'sf-safe':mSFil>=1.5?'sf-warn':'sf-danger');

  const spStep=Math.max(W,L)/(RU/6);
  document.getElementById('r-spacer').innerHTML=(Math.abs(dpO)*(spStep/1000)**2).toFixed(0)+u+'N</span>';
  document.getElementById('r-cable').innerHTML=(mxCb/1000).toFixed(1)+u+'kN</span>';
  document.getElementById('r-wind').innerHTML=Math.abs(mnW).toFixed(0)+u+'Pa 흡입</span>';
  document.getElementById('r-snow').innerHTML=mxSn.toFixed(0)+u+'Pa</span>';
  document.getElementById('r-defl').innerHTML=mxDef.toFixed(1)+u+'mm (H/'+(mxDef>0?(H_mm/mxDef).toFixed(0):'∞')+')</span>';
  const rqP=Ph.reqP(wSpd,sLoad);
  document.getElementById('r-reqp').innerHTML=rqP.toFixed(0)+u+'Pa</span>'+
    (pInt<rqP?' <span class="sf-danger">⚠부족</span>':' <span class="sf-safe">✓OK</span>');

  // ═══════ 케이블 해석 ═══════
  const cDia=+document.getElementById('s-cdia').value;
  const cBreak=+document.getElementById('s-cbreak').value;
  const cElastic=+document.getElementById('s-celastic').value;
  const cSfReq=+document.getElementById('s-csf-req').value;
  document.getElementById('v-cdia').textContent=cDia.toFixed(1);
  document.getElementById('v-cbreak').textContent=cBreak.toFixed(1);
  document.getElementById('v-celastic').textContent=cElastic;
  document.getElementById('v-csf-req').textContent=cSfReq.toFixed(1);

  // 활성화된 하중 조합 확인
  const lcActive=[1,2,3,4,5].filter(n=>document.getElementById('lc-'+n).checked);

  // 모든 그리드 포인트에서 하중 조합별 케이블 장력 계산
  let maxCableForce=0, worstLC='LC1', worstLCname='내압+자중';
  let maxWindward=0, maxLeeward=0, maxTop=0;
  // 각 LC별 최대값 추적
  const lcMax={{1:0,2:0,3:0,4:0,5:0}};

  for(let j=0;j<=RV;j++)for(let i=0;i<=RU;i++){{
    const vi=j*(RU+1)+i,uu=i/RU,vv=j/RV;
    const xm=(uu-0.5)*2*a_mm,ym=(vv-0.5)*2*b_mm,zm=domeZ_mm(xm,ym);
    if(zm<1)continue;
    const lcs=CableEng.calcLoadCombinations(xm,ym,zm,Ho,dpO,wSpd,wDir,sLoad,cSp);
    if(!lcs)continue;
    // 위치 판별
    const pos=CableEng.positionType(xm,ym,zm,wDir);
    for(const lc of lcs){{
      const lcNum=parseInt(lc.id.replace('LC',''));
      if(!lcActive.includes(lcNum))continue;
      const cf=lc.cableT/1000; // kN
      if(cf>lcMax[lcNum])lcMax[lcNum]=cf;
      if(cf>maxCableForce){{maxCableForce=cf;worstLC=lc.id;worstLCname=lc.name;}}
    }}
    // 위치별 최대값 (LC2 기준 - 풍하중 조합)
    if(lcActive.includes(2)){{
      const cfWind=lcs[1].cableT/1000;
      if(pos==='windward'&&cfWind>maxWindward)maxWindward=cfWind;
      if(pos==='leeward'&&cfWind>maxLeeward)maxLeeward=cfWind;
      if(pos==='top'&&cfWind>maxTop)maxTop=cfWind;
    }}
    // 정상부는 LC3(적설)에서도 확인
    if(lcActive.includes(3)&&CableEng.positionType(xm,ym,zm,wDir)==='top'){{
      const cfSnow=lcs[2].cableT/1000;
      if(cfSnow>maxTop)maxTop=cfSnow;
    }}
  }}

  const cableSF=CableEng.safeFactor(maxCableForce,cBreak);
  const cableAllow=CableEng.allowableForce(cBreak,cSfReq);
  const cMatInfo=CableDB[curCableMat];

  // 케이블 결과 UI 업데이트
  document.getElementById('r-cspec').innerHTML=cMatInfo.name;
  document.getElementById('r-cable2').innerHTML=maxCableForce.toFixed(2)+u+'kN</span>';
  const csfE=document.getElementById('r-csf');
  csfE.textContent=cableSF.toFixed(2);
  csfE.className='v '+(cableSF>=cSfReq?'sf-safe':cableSF>=1.5?'sf-warn':'sf-danger');
  document.getElementById('r-callow').innerHTML=cableAllow.toFixed(2)+u+'kN</span>'+
    (maxCableForce>cableAllow?' <span class="sf-danger">초과!</span>':'');
  document.getElementById('r-clc').innerHTML='<span style="color:'+(cableSF>=cSfReq?'#34d399':'#f87171')+';">'+worstLC+': '+worstLCname+'</span>';
  document.getElementById('r-cwind-max').innerHTML=maxWindward.toFixed(2)+u+'kN</span>';
  document.getElementById('r-cwind-lee').innerHTML=maxLeeward.toFixed(2)+u+'kN</span>';
  document.getElementById('r-ctop').innerHTML=maxTop.toFixed(2)+u+'kN</span>';

  // 케이블 응력/신장량 계산 (직경, 탄성계수 반영)
  const cStress=CableEng.cableStress(maxCableForce,cDia);
  const cBreakStress=CableEng.breakStress(cBreak,cDia);
  // 케이블 스팬: 돔 높이의 약 1.2배 (곡선 길이 근사)
  const cableSpan=Math.sqrt((W/2)**2+H_mm**2)*1.2;
  const cElong=CableEng.cableElongation(maxCableForce,cableSpan,cElastic,cDia);
  const cStrain=CableEng.cableStrain(maxCableForce,cElastic,cDia);

  document.getElementById('r-cstress').innerHTML=cStress.toFixed(1)+u+'MPa</span>'+
    (cStress>cBreakStress*0.8?' <span class="sf-warn">⚠</span>':'');
  document.getElementById('r-cbreak-stress').innerHTML=cBreakStress.toFixed(0)+u+'MPa</span>';
  document.getElementById('r-celongation').innerHTML=cElong.toFixed(1)+u+'mm</span>'+
    (cElong>cableSpan/200?' <span class="sf-warn">⚠과대</span>':'');
  document.getElementById('r-cstrain').innerHTML=cStrain.toFixed(3)+u+'%</span>';

  const minSF=Math.min(mSFo,mSFiu,mSFil);
  const vd=document.getElementById('r-verdict');let ms=[];
  if(pInt<rqP)ms.push('<span class="sf-danger">❌ 내압 부족 — 최소 '+rqP.toFixed(0)+'Pa 필요</span>');
  if(mSFo<1.5)ms.push('<span class="sf-danger">❌ 외피막 SF='+mSFo.toFixed(2)+' 부족</span>');
  if(mSFiu<1.5)ms.push('<span class="sf-danger">❌ 내피(상) SF 부족</span>');
  if(mSFil<1.5)ms.push('<span class="sf-danger">❌ 내피(하) SF 부족</span>');
  // 케이블 안전율 판정
  if(cableSF<1.5)ms.push('<span class="sf-danger">❌ 케이블 SF='+cableSF.toFixed(2)+' 파단 위험 ('+worstLC+')</span>');
  else if(cableSF<cSfReq)ms.push('<span class="sf-warn">⚠ 케이블 SF='+cableSF.toFixed(2)+' 기준미달 (요구 '+cSfReq.toFixed(1)+', '+worstLC+')</span>');
  if(maxCableForce>cableAllow)ms.push('<span class="sf-danger">❌ 케이블 장력 '+maxCableForce.toFixed(2)+'kN > 허용 '+cableAllow.toFixed(2)+'kN</span>');
  if(minSF<3&&cableSF>=cSfReq&&ms.length===0)ms.push('<span class="sf-warn">⚠ 주의 — 막 SF='+minSF.toFixed(2)+' (권장 3.0+)</span>');
  if(ms.length===0)ms.push('<span class="sf-safe">✅ 전 층+케이블 안전 — 막SF='+minSF.toFixed(2)+', 케이블SF='+cableSF.toFixed(2)+'</span>');
  vd.innerHTML=ms.join('<br>');

  // 컬러맵
  let lt='',lmn='',lmx='';
  const modes={{
    tension:[dO,0,mxTO,'장력','0',(mxTO/1000).toFixed(1)+'kN/m'],
    wind:[wD,mnW,mxW,'풍압',mnW.toFixed(0)+'Pa',mxW.toFixed(0)+'Pa'],
    snow:[snD,0,mxSn||1,'적설','0',mxSn.toFixed(0)+'Pa'],
    combined:[cmbD,0,mxCmb,'합산장력','0',(mxCmb/1000).toFixed(1)+'kN/m'],
    deform:[defD,0,mxDef||1,'변형량','0',mxDef.toFixed(1)+'mm'],
    cable:[cbD,0,mxCb||1,'케이블','0',(mxCb/1000).toFixed(1)+'kN'],
  }};
  if(vizMode in modes){{
    const m=modes[vizMode];
    applyC(layers.outer.geometry,m[0],m[1],m[2],vizMode,[0.96,0.94,0.91]);
    applyC(layers.innerU.geometry,vizMode==='tension'?dIU:m[0],vizMode==='tension'?0:m[1],vizMode==='tension'?mxTIU:m[2],vizMode,[1,0.55,0.25]);
    applyC(layers.innerL.geometry,vizMode==='tension'?dIL:m[0],vizMode==='tension'?0:m[1],vizMode==='tension'?mxTIL:m[2],vizMode,[1,0.4,0.15]);
    lt=m[3];lmn=m[4];lmx=m[5];
  }}else if(vizMode==='safety'){{
    applyC(layers.outer.geometry,sfD,0,0,'safety',[0.96,0.94,0.91]);
    applyC(layers.innerU.geometry,sfD,0,0,'safety',[1,0.55,0.25]);
    applyC(layers.innerL.geometry,sfD,0,0,'safety',[1,0.4,0.15]);
    lt='안전율';lmn='1.0(위험)';lmx='5.0+(안전)';
  }}else{{
    applyC(layers.outer.geometry,null,0,0,'normal',[0.96,0.94,0.91]);
    applyC(layers.innerU.geometry,null,0,0,'normal',[1,0.55,0.25]);
    applyC(layers.innerL.geometry,null,0,0,'normal',[1,0.4,0.15]);
    lt='기본뷰';lmn='';lmx='';
  }}
  document.getElementById('leg-t').textContent=lt;
  updateLeg(vizMode,lmn,lmx);
}}

// ================================================================
//  UI 제어
// ================================================================
window.setViz=function(m){{vizMode=m;
  document.querySelectorAll('.tb[id^="vb-"]').forEach(b=>b.classList.remove('on'));
  const b=document.getElementById('vb-'+m);if(b)b.classList.add('on');runSim();}};
window.togL=function(n){{if(layers[n]){{layers[n].visible=!layers[n].visible;
  const b=document.getElementById('lb-'+n);if(b)b.classList.toggle('on');}}}};
window.preset=function(p){{const g=id=>document.getElementById(id);
  switch(p){{
    case'calm':g('s-pressure').value=250;g('s-wind').value=0;g('s-snow').value=0;break;
    case'normal':g('s-pressure').value=300;g('s-wind').value=15;g('s-snow').value=0;break;
    case'strong':g('s-pressure').value=500;g('s-wind').value=30;g('s-snow').value=0;break;
    case'storm':g('s-pressure').value=800;g('s-wind').value=45;g('s-snow').value=0;break;
    case'snow_l':g('s-pressure').value=350;g('s-wind').value=5;g('s-snow').value=0.5;break;
    case'snow_h':g('s-pressure').value=500;g('s-wind').value=10;g('s-snow').value=2.0;break;
    case'worst':g('s-pressure').value=800;g('s-wind').value=40;g('s-snow').value=2.5;break;
  }}runSim();}};

// ================================================================
//  풍류 유체 시각화 (Particle Streamlines)
// ================================================================
const WFLOW={{
  active:false, N:5000, trails:12, dt:0.10,
  pts:null, geo:null, mesh:null, trailGeo:[], trailMesh:[],
  init:function(){{
    // 파티클 점(Points)
    this.pts=new Float32Array(this.N*3);
    this.vel=new Float32Array(this.N*3);
    this.life=new Float32Array(this.N);
    this.maxLife=new Float32Array(this.N);  // 개별 최대 수명
    this.lifeRate=new Float32Array(this.N); // 개별 수명 증가 속도
    this.cols=new Float32Array(this.N*3);
    this.sizes=new Float32Array(this.N);
    for(let i=0;i<this.N;i++){{
      this.maxLife[i]=0.9+Math.random()*0.9;   // 0.9~1.8 (개별 수명 - 후류까지 도달)
      this.lifeRate[i]=0.03+Math.random()*0.03; // 0.03~0.06 (개별 속도 - 더 오래 생존)
    }}
    this.geo=new THREE.BufferGeometry();
    this.geo.setAttribute('position',new THREE.Float32BufferAttribute(this.pts,3));
    this.geo.setAttribute('color',new THREE.Float32BufferAttribute(this.cols,3));
    this.geo.setAttribute('size',new THREE.Float32BufferAttribute(this.sizes,1));
    // 포인트 머티리얼 (모델 크기 적응형 크기 감쇠 + clamp)
    const shaderFactor=Math.max(a,b)*50.0;
    const vsh=`attribute float size;attribute vec3 color;varying vec3 vc;
      void main(){{vc=color;vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_PointSize=clamp(size*(${{shaderFactor.toFixed(1)}}/-mv.z),1.0,12.0);gl_Position=projectionMatrix*mv;}}`;
    const fsh=`varying vec3 vc;void main(){{float d=length(gl_PointCoord-0.5);
      if(d>0.5)discard;float a=smoothstep(0.5,0.2,d);
      gl_FragColor=vec4(vc,a*0.7);}}`;
    const mat=new THREE.ShaderMaterial({{vertexShader:vsh,fragmentShader:fsh,
      transparent:true,depthWrite:false,blending:THREE.AdditiveBlending}});
    this.mesh=new THREE.Points(this.geo,mat);
    this.mesh.visible=false;
    this.mesh.frustumCulled=false;
    scene.add(this.mesh);
    // 트레일 라인
    const tMat=new THREE.LineBasicMaterial({{color:0x38bdf8,transparent:true,opacity:0.18,blending:THREE.AdditiveBlending}});
    for(let t=0;t<this.trails;t++){{
      const tg=new THREE.BufferGeometry();
      const tp=new Float32Array(this.N/this.trails*3);
      tg.setAttribute('position',new THREE.Float32BufferAttribute(tp,3));
      const tm=new THREE.LineSegments(tg,tMat.clone());
      tm.visible=false;tm.frustumCulled=false;
      scene.add(tm);
      this.trailGeo.push(tg);this.trailMesh.push(tm);
    }}
    // 초기 배치 (수명을 전체에 고르게 분산 → 연속적 흐름)
    for(let i=0;i<this.N;i++){{this.respawn(i);this.life[i]=Math.random()*this.maxLife[i];}}
    // 풍류 범례 그라디언트
    const c=document.getElementById('wl-gradient');
    if(c){{const ctx=c.getContext('2d');
      for(let i=0;i<120;i++){{const t=i/120;
        let r,g,b2;
        if(t<0.33){{r=0.2;g=0.5+t*1.5;b2=1;}}
        else if(t<0.66){{r=t*1.5;g=0.9;b2=1-t;}}
        else{{r=1;g=1.2-t;b2=0.2;}}
        ctx.fillStyle=`rgb(${{r*255|0}},${{g*255|0}},${{b2*255|0}})`;
        ctx.fillRect(i,0,1,8);}}
    }}
  }},
  // 풍향에 따른 자유류 방향
  freeStream:function(){{
    const dir=parseFloat(document.getElementById('s-winddir').value)||0;
    const spd=parseFloat(document.getElementById('s-wind').value)||0;
    const rad=dir*Math.PI/180;
    const vn=Math.max(spd/45,0.05); // 정규화 속도
    // 방향 단위벡터 (풍속 무관하게 항상 일정한 크기)
    const ndx=Math.cos(rad), ndz=Math.sin(rad);
    return {{dx:Math.cos(rad)*vn, dz:Math.sin(rad)*vn, spd:spd, dir:dir, ndx:ndx, ndz:ndz, vn:vn}};
  }},
  // 돔 표면 높이 (3D 좌표계)
  domeH:function(x,z){{
    const rx=x/a, rz=z/b;
    const r2=rx*rx+rz*rz;
    return (r2<1)?Hs*Math.sqrt(Math.max(0,(1-rx*rx)))*Math.sqrt(Math.max(0,(1-rz*rz))):0;
  }},
  // 유동장 계산 (포텐셜 유동 + 와류 모사)
  flowField:function(x,y,z,fs){{
    const rx=x/a, rz=z/b;
    const r2=rx*rx+rz*rz;
    const R=Math.sqrt(r2);
    // 시각화용 최소 흐름 속도 보장 (풍속 낮아도 돔 전체 커버)
    const flowVn=Math.max(fs.vn, 0.25);
    let vx=fs.ndx*flowVn*8, vy=0, vz=fs.ndz*flowVn*8;
    // 원거리: 대기 경계층 프로파일
    if(R>=2.0){{
      const heightFactor=Math.min(1.3, 0.6+0.7*Math.pow(Math.max(y,0.1)/(Hs*2),0.2));
      vx*=heightFactor; vz*=heightFactor;
      const turb=0.2;
      vx+=Math.sin(rx*0.5+rz*0.3+performance.now()*0.0005)*turb;
      vz+=Math.cos(rz*0.5+rx*0.3+performance.now()*0.0007)*turb;
    }}
    if(R<2.0){{
      const dh=this.domeH(x,z);
      if(y<dh+0.3&&R<1.0){{
        // 돔 내부/표면 → 강하게 밀어냄
        const nx=rx/Math.max(R,0.01), nz=rz/Math.max(R,0.01);
        const push=4.0/(R+0.05);
        vx+=nx*push; vy+=3.0; vz+=nz*push;
      }} else if(R<1.4){{
        // 돔 표면 근처 → 가속 (베르누이 효과) + 표면 따라 흐름
        const accel=1.0+2.0*(1.0-Math.abs(R-1.0)/0.4);
        vx*=accel; vz*=accel;
        // 표면을 따라 위로 솟구침 (더 강하게)
        if(y<dh+2.5){{
          const slope=(dh-this.domeH(x-fs.dx*0.3,z-fs.dz*0.3))/0.3;
          vy+=slope*3.5;
        }}
        // 돔 양옆으로 갈라지는 효과
        const tangx=-rz/Math.max(R,0.01);
        const tangz=rx/Math.max(R,0.01);
        const deflect=Math.max(0,1.0-Math.abs(R-1.0)/0.4)*1.5;
        vx+=tangx*deflect*(Math.random()-0.5)*2;
        vz+=tangz*deflect*(Math.random()-0.5)*2;
      }}
      // 후류(wake) 영역 - 풍하측 와류 (정규화 좌표로 큰 와류 패턴)
      const windDot=rx*fs.ndx+rz*fs.ndz;
      if(windDot>0.2&&R>0.7&&R<2.0){{
        const wake=Math.min(1,(windDot-0.2)/0.4)*Math.max(0,1-(R-0.7)/1.3);
        // 와류 회전 (정규화 좌표 사용 → 큰 소용돌이 패턴)
        const t=performance.now()*0.001;
        vx+=Math.sin(t*2.5+rz*6)*wake*4.5;
        vz+=Math.cos(t*2.5+rx*6)*wake*4.5;
        vy+=Math.sin(t*3.5+rx*4)*wake*2.5;
        // 감속 (후류에서 소용돌이)
        vx*=(1-wake*0.5); vz*=(1-wake*0.5);
      }}
    }}
    // 중력 효과 (약하게)
    if(y>0.5)vy-=0.25;
    if(y<0.1)vy=Math.max(vy,0.1);
    return {{x:vx,y:vy,z:vz}};
  }},
  // 파티클 스폰 (풍상측에서 생성 - 돔 근처부터)
  respawn:function(i){{
    const fs=this.freeStream();
    const i3=i*3;
    const baseSpread=Math.max(a,b);
    const crossSpread=Math.sqrt(a*a+b*b); // 대각선 기준으로 항상 물체보다 넓게
    // 대부분 돔 가까이에서 시작, 일부만 약간 먼곳에서
    const rng=Math.random();
    const farDist=rng<0.6 ? baseSpread*(0.9+Math.random()*0.7) :
                  rng<0.85 ? baseSpread*(1.6+Math.random()*0.7) :
                  baseSpread*(0.2+Math.random()*0.6);
    const sideSpread=crossSpread*2.2;
    const side=(Math.random()-0.5)*sideSpread;
    // 높이: 돔 표면과 상호작용하도록 낮은 층 비중 높임
    const hLayer=Math.random();
    const h=hLayer<0.6 ? (0.2+Math.random()*Hs*0.7) :
            hLayer<0.85 ? (Hs*0.3+Math.random()*Hs*1.0) :
            (Hs*1.0+Math.random()*Hs*0.6);
    // 풍향 단위벡터 기반으로 스폰 위치 결정 (풍속과 무관하게 돔 전체 커버)
    this.pts[i3]  =-fs.ndx*farDist+(-fs.ndz)*side;
    this.pts[i3+1]=h;
    this.pts[i3+2]=-fs.ndz*farDist+(fs.ndx)*side;
    // 초기 속도도 최소 흐름 보장 (시각화용 최소 속도 + 실제 풍속 비례)
    const flowVn=Math.max(fs.vn, 0.25);
    this.vel[i3]=fs.ndx*flowVn*6;this.vel[i3+1]=0;this.vel[i3+2]=fs.ndz*flowVn*6;
    this.life[i]=-Math.random()*0.15;  // 약간의 음수 지연 → 파티클마다 다른 시점에 등장
    this.maxLife[i]=0.9+Math.random()*0.9;
    this.lifeRate[i]=0.03+Math.random()*0.03;
    this.sizes[i]=0.15+Math.random()*0.35;
  }},
  // 풍압 기반 색상 (파란=자유류/저압 → 초록=중간 → 빨강=고압/와류)
  pressureColor:function(t){{
    t=Math.min(1,Math.max(0,t));
    let r,g,b2;
    if(t<0.25){{r=0.15;g=0.4+t*2.4;b2=1.0;}}           // 파랑→시안
    else if(t<0.5){{r=(t-0.25)*4;g=0.9;b2=1.0-t*1.2;}}  // 시안→초록
    else if(t<0.75){{r=0.8+t*0.25;g=1.0-(t-0.5)*2.4;b2=0.1;}} // 초록→노랑→주황
    else{{r=1.0;g=0.4-(t-0.75)*1.6;b2=0.05;}}            // 주황→빨강
    return{{r:Math.min(1,r),g:Math.max(0,g),b:Math.max(0,b2)}};
  }},
  // 프레임 업데이트
  update:function(){{
    if(!this.active)return;
    const fs=this.freeStream();
    const pa=this.geo.getAttribute('position');
    const ca=this.geo.getAttribute('color');
    const sa=this.geo.getAttribute('size');
    const maxDist=Math.max(a,b)*4.5;
    for(let i=0;i<this.N;i++){{
      const i3=i*3;
      this.life[i]+=this.dt*this.lifeRate[i];
      if(this.life[i]<0){{
        pa.setXYZ(i,this.pts[i3],this.pts[i3+1],this.pts[i3+2]);
        ca.setXYZ(i,0,0,0);sa.array[i]=0;continue;}}
      const px=this.pts[i3],py=this.pts[i3+1],pz=this.pts[i3+2];
      // 유동장에서 속도 계산
      const v=this.flowField(px,py,pz,fs);
      // 약간의 난류 (돔 근처일수록 강하게)
      const rx2=px/a,rz2=pz/b,R2=Math.sqrt(rx2*rx2+rz2*rz2);
      const turbScale=R2<1.2?1.2:R2<2.0?0.7:0.2;
      v.x+=((Math.random()-0.5)*turbScale);
      v.y+=((Math.random()-0.5)*turbScale*0.4);
      v.z+=((Math.random()-0.5)*turbScale);
      // 위치 업데이트 (Euler 적분)
      this.pts[i3]  +=v.x*this.dt;
      this.pts[i3+1]+=v.y*this.dt;
      this.pts[i3+2]+=v.z*this.dt;
      // 지면 충돌
      if(this.pts[i3+1]<0.05)this.pts[i3+1]=0.05+Math.random()*0.3;
      // 범위 초과 시 리스폰
      const dist=Math.sqrt(this.pts[i3]**2+this.pts[i3+2]**2);
      if(dist>maxDist||this.pts[i3+1]>Hs*3||this.life[i]>this.maxLife[i]){{
        this.respawn(i);continue;
      }}
      // 풍압 기반 색상 (베르누이: 속도↓=압력↑=빨강, 속도↑=압력↓=파랑)
      const spd=Math.sqrt(v.x**2+v.y**2+v.z**2);
      const freeSpd=Math.max(fs.vn,0.25)*8;
      const rx=px/a,rz=pz/b,R=Math.sqrt(rx*rx+rz*rz);
      const windDot=R>0.3?((rx*fs.ndx+rz*fs.ndz)/R):0;
      // 압력 파라미터: 0=자유류(파랑) → 1=고압/와류(빨강)
      let pF=0;
      // (1) 속도 감소 → 압력 상승 (풍상측 정체점)
      if(spd<freeSpd)pF=Math.pow((freeSpd-spd)/freeSpd,0.6)*0.7;
      // (2) 돔 표면 근접도 (가까울수록 상호작용 강함)
      if(R<1.3){{const prox=Math.max(0,1.0-R)*0.4;pF+=prox;}}
      // (3) 풍상측 정면 충돌 (바람 방향과 마주보는 면)
      if(R<1.3&&windDot<-0.1)pF+=Math.abs(windDot)*0.3;
      // (4) 후류 와류 영역 (풍하측 재순환)
      if(windDot>0.2&&R>0.7&&R<2.5){{
        const wake=Math.min(1,(windDot-0.2)/0.4)*Math.max(0,1-(R-0.7)/1.8);
        pF=Math.max(pF,0.55+wake*0.45);
      }}
      pF=Math.min(1,Math.max(0,pF));
      const c=this.pressureColor(pF);
      // 수명에 따른 페이드 (개별 maxLife 기반)
      const lifeRatio=this.life[i]/this.maxLife[i];
      const alpha=lifeRatio<0.05?lifeRatio*20:
                  lifeRatio>0.85?(1-lifeRatio)*(1/0.15):1;
      ca.setXYZ(i,c.r*alpha,c.g*alpha,c.b*alpha);
      sa.array[i]=this.sizes[i]*(0.5+alpha*0.5);
      pa.setXYZ(i,this.pts[i3],this.pts[i3+1],this.pts[i3+2]);
    }}
    pa.needsUpdate=true;ca.needsUpdate=true;sa.needsUpdate=true;
    // 트레일 업데이트 (파티클 중 일부를 선분으로 연결)
    for(let t=0;t<this.trails;t++){{
      const tpa=this.trailGeo[t].getAttribute('position');
      const step=Math.floor(this.N/this.trails);
      const off=t*step;
      let ti=0;
      for(let i=off;i<off+step-1&&ti<tpa.count-1;i+=2){{
        const i3=i*3,j3=(i+1)*3;
        if(this.life[i]>0&&this.life[i]<this.maxLife[i]*0.9&&this.life[i+1]>0){{
          tpa.setXYZ(ti,this.pts[i3],this.pts[i3+1],this.pts[i3+2]);ti++;
          tpa.setXYZ(ti,this.pts[j3],this.pts[j3+1],this.pts[j3+2]);ti++;
        }}
      }}
      for(;ti<tpa.count;ti++)tpa.setXYZ(ti,0,-10,0);
      tpa.needsUpdate=true;
    }}
  }},
  show:function(on){{
    this.active=on;
    this.mesh.visible=on;
    this.trailMesh.forEach(m=>m.visible=on);
    const wl=document.getElementById('wind-legend');
    if(wl){{if(on)wl.classList.add('on');else wl.classList.remove('on');}}
    const b=document.getElementById('lb-windflow');
    if(b){{if(on)b.classList.add('on');else b.classList.remove('on');}}
    if(on)for(let i=0;i<this.N;i++){{this.respawn(i);this.life[i]=Math.random()*this.maxLife[i];}}
  }}
}};
WFLOW.init();
window.togWindFlow=function(){{WFLOW.show(!WFLOW.active);}};

// 카메라
let rot={{x:0.35,y:-0.5}},zoom=70,drag=false,mx=0,my=0;
const cv=renderer.domElement;
cv.addEventListener('mousedown',e=>{{if(e.clientX>285&&e.clientX<innerWidth-285){{drag=true;mx=e.clientX;my=e.clientY;}}}});
cv.addEventListener('mousemove',e=>{{if(!drag)return;rot.y-=(e.clientX-mx)*0.005;
  rot.x=Math.max(-0.1,Math.min(1.4,rot.x+(e.clientY-my)*0.005));mx=e.clientX;my=e.clientY;}});
cv.addEventListener('mouseup',()=>drag=false);
cv.addEventListener('mouseleave',()=>drag=false);
cv.addEventListener('wheel',e=>{{zoom=Math.max(15,Math.min(150,zoom+e.deltaY*0.05));}});
window.camView=function(v){{
  if(v==='top'){{rot={{x:1.4,y:0}};zoom=75;}}
  else if(v==='east'){{rot={{x:0.15,y:0}};zoom=55;}}
  else if(v==='south'){{rot={{x:0.15,y:Math.PI/2}};zoom=75;}}
  else{{rot={{x:0.35,y:-0.5}};zoom=70;}}
}};
(function anim(){{requestAnimationFrame(anim);
  WFLOW.update();
  camera.position.set(zoom*Math.cos(rot.x)*Math.sin(rot.y),zoom*Math.sin(rot.x)+10,
    zoom*Math.cos(rot.x)*Math.cos(rot.y));
  camera.lookAt(0,Hs*0.3,0);renderer.render(scene,camera);}})();
window.addEventListener('resize',()=>{{camera.aspect=innerWidth/innerHeight;
  camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}});

// 이벤트
['s-pressure','s-wind','s-snow','s-winddir','s-gap1','s-gap2',
 's-thick-o','s-thick-i','s-str-o','s-str-i','s-elastic','s-cspace',
 's-cdia','s-cbreak','s-celastic','s-csf-req'].forEach(id=>{{
  document.getElementById(id).addEventListener('input',function(){{
    if(['s-cdia','s-cbreak','s-celastic'].includes(id))curCableMat='custom';
    runSim();
  }});}});
// 하중 조합 체크박스 이벤트
['lc-1','lc-2','lc-3','lc-4','lc-5'].forEach(id=>{{
  document.getElementById(id).addEventListener('change',runSim);}});
runSim();

// ================================================================
//  종합의견 생성 시스템
// ================================================================
window.showOpinion=function(){{
  const html=generateOpinionHTML();
  document.getElementById('opinion-content').innerHTML=html;
  document.getElementById('opinion-overlay').classList.add('on');
}};
window.closeOpinion=function(){{
  document.getElementById('opinion-overlay').classList.remove('on');
}};
window.copyOpinion=function(){{
  const el=document.getElementById('opinion-content');
  const text=el.innerText||el.textContent;
  navigator.clipboard.writeText(text).then(()=>{{
    const btn=document.querySelector('.btn-copy-opinion');
    const orig=btn.textContent;btn.textContent='✓ 복사됨!';
    setTimeout(()=>btn.textContent=orig,1500);
  }}).catch(()=>alert('복사에 실패했습니다.'));
}};

function generateOpinionHTML(){{
  // ── 1. 모든 설정값 수집 ──
  const pInt=+document.getElementById('s-pressure').value;
  const wSpd=+document.getElementById('s-wind').value;
  const sLoad=+document.getElementById('s-snow').value;
  const wDir=+document.getElementById('s-winddir').value;
  const gap1=+document.getElementById('s-gap1').value;
  const gap2=+document.getElementById('s-gap2').value;
  const thO=+document.getElementById('s-thick-o').value;
  const thI=+document.getElementById('s-thick-i').value;
  const strO=+document.getElementById('s-str-o').value;
  const strI=+document.getElementById('s-str-i').value;
  const E=+document.getElementById('s-elastic').value;
  const cSp=+document.getElementById('s-cspace').value;

  // ── 2. 결과값 수집 (재계산) ──
  const pm=calcPMode(pressureMode);
  const pG1=pInt*pm.r1, pG2=pInt*pm.r2;
  const dpO=pG1, dpIU=pG1-pG2, dpIL=pG2-pInt;

  const Ho=H_mm, Hiu=H_mm*(1-gap1*0.001/(H_mm*0.001)), Hil=H_mm*(1-(gap1+gap2)*0.001/(H_mm*0.001));
  const N2=(RU+1)*(RV+1);
  let mxTO=0,mxTIU=0,mxTIL=0,mxW=-1e9,mnW=1e9,mxSn=0,mxDef=0,mxCb=0;
  let mSFo=99,mSFiu=99,mSFil=99;
  // 평균값 계산용
  let sumTO=0,sumTIU=0,sumTIL=0,cntValid=0;

  for(let j=0;j<=RV;j++)for(let i=0;i<=RU;i++){{
    const vi=j*(RU+1)+i,u=i/RU,v=j/RV;
    const xm=(u-0.5)*2*a_mm,ym=(v-0.5)*2*b_mm,zm=domeZ_mm(xm,ym);
    if(zm<1)continue;
    const wp=Ph.wp(xm,ym,wSpd,wDir),sp2=Ph.sp(xm,ym,sLoad);
    const netO=dpO+wp-sp2;
    const tO=Ph.T(xm,ym,Math.abs(netO>0?netO:dpO-wp-sp2),Ho);
    const tIU=Ph.T(xm,ym,Math.abs(dpIU),Hiu);
    const tIL=Ph.T(xm,ym,Math.abs(dpIL),Hil);
    const def=Ph.defl(tO,E,thO,Math.min(Math.sqrt(xm*xm+ym*ym)+100,W/2));
    const cb=Ph.cableT(tO,cSp);
    const sfo=Ph.sf(tO,strO),sfiu=Ph.sf(tIU,strI),sfil=Ph.sf(tIL,strI);
    if(tO>mxTO)mxTO=tO;if(tIU>mxTIU)mxTIU=tIU;if(tIL>mxTIL)mxTIL=tIL;
    if(wp>mxW)mxW=wp;if(wp<mnW)mnW=wp;if(sp2>mxSn)mxSn=sp2;
    if(def>mxDef)mxDef=def;if(cb>mxCb)mxCb=cb;
    if(zm>H_mm*0.05){{if(sfo<mSFo)mSFo=sfo;if(sfiu<mSFiu)mSFiu=sfiu;if(sfil<mSFil)mSFil=sfil;}}
    sumTO+=tO;sumTIU+=tIU;sumTIL+=tIL;cntValid++;
  }}
  const avgTO=cntValid>0?sumTO/cntValid:0;
  const avgTIU=cntValid>0?sumTIU/cntValid:0;
  const avgTIL=cntValid>0?sumTIL/cntValid:0;
  const minSF=Math.min(mSFo,mSFiu,mSFil);
  const rqP=Ph.reqP(wSpd,sLoad);
  const area_m2=W*L/1e6;
  const deflRatio=mxDef>0?(H_mm/mxDef):Infinity;

  // ── 3. 압력분배 모드 한글명 ──
  const pmNames={{'equal':'균등분배','outer':'외피중심','inner':'내피보호','single':'단일블로워'}};
  const pmName=pmNames[pressureMode]||pressureMode;

  // ── 4. 풍속 등급 판별 ──
  let windGrade='';
  if(wSpd<=5)windGrade='미풍(약풍) 수준';
  else if(wSpd<=15)windGrade='보통 풍속 수준';
  else if(wSpd<=25)windGrade='강풍 수준 (주의 필요)';
  else if(wSpd<=35)windGrade='매우 강한 풍속 (경계 필요)';
  else windGrade='폭풍급 풍속 (위험)';

  // ── 5. 안전율 판정 ──
  function sfLabel(sf){{
    if(sf>=5)return '<span class="op-safe">매우 안전 (SF≥5.0)</span>';
    if(sf>=3)return '<span class="op-safe">안전 (SF≥3.0, 권장 기준 충족)</span>';
    if(sf>=2)return '<span class="op-warn">주의 (SF 2.0~3.0, 권장 기준 미달)</span>';
    if(sf>=1.5)return '<span class="op-warn">경고 (SF 1.5~2.0, 안전 여유 부족)</span>';
    return '<span class="op-danger">위험 (SF&lt;1.5, 구조적 위험)</span>';
  }}

  // ── 6. 종합의견 HTML 생성 ──
  let h='';

  // [1] 개요
  h+='<div class="op-section">';
  h+='<div class="op-title">1. 구조물 개요</div>';
  h+='본 해석은 <span class="op-highlight">폭(W) '+W.toLocaleString()+' mm × 길이(L) '+L.toLocaleString()+' mm × 높이(H) '+H.toLocaleString()+' mm</span> 규모의 에어돔 삼중막 구조물에 대한 시뮬레이션 결과입니다. ';
  h+='바닥면적은 약 <span class="op-highlight">'+area_m2.toLocaleString(undefined,{{maximumFractionDigits:0}})+' m²</span>이며, ';
  h+='돔의 형상은 타원 포물면(Elliptical Paraboloid) 수식 z = H × √(1-(x/a)²) × √(1-(y/b)²)을 기반으로 생성되었습니다. ';
  h+='케이블 네트의 격자 간격은 <span class="op-param">'+cSp.toLocaleString()+' mm</span>로 설정되어 있습니다.';
  h+='</div>';

  // [2] 하중 조건
  h+='<div class="op-section">';
  h+='<div class="op-title">2. 적용 하중 조건</div>';
  h+='현재 설정된 내압(P_int)은 <span class="op-highlight">'+pInt+' Pa</span>이며, ';
  h+='풍속은 <span class="op-highlight">'+wSpd+' m/s</span>(풍향 '+wDir+'°)로 '+windGrade+'에 해당합니다. ';
  if(wSpd>0){{
    const qPeak=(0.5*1.225*wSpd*wSpd);
    h+='이 풍속에서의 기본 동압(q)은 약 '+qPeak.toFixed(0)+' Pa이며, 돔 형상에 따른 풍압계수(Cp)를 반영한 최대 풍압(흡입)은 <span class="op-highlight">'+Math.abs(mnW).toFixed(0)+' Pa</span>입니다. ';
  }}
  h+='적설하중은 <span class="op-highlight">'+sLoad.toFixed(1)+' kN/m²</span>로 설정되어 있으며';
  if(sLoad>0){{
    h+=', 돔 표면 경사에 따라 보정된 최대 적설압력은 <span class="op-highlight">'+mxSn.toFixed(0)+' Pa</span>입니다. ';
  }}else{{
    h+=', 적설하중이 없는 조건입니다. ';
  }}
  h+='시스템이 요구하는 최소 내압은 <span class="op-highlight">'+rqP.toFixed(0)+' Pa</span>이며, ';
  if(pInt>=rqP){{
    h+='현재 설정 내압('+pInt+' Pa)은 이를 <span class="op-safe">충족</span>합니다.';
  }}else{{
    h+='현재 설정 내압('+pInt+' Pa)은 이에 <span class="op-danger">'+((rqP-pInt).toFixed(0))+' Pa 부족</span>한 상태입니다. 내압을 최소 '+rqP.toFixed(0)+' Pa 이상으로 상향 조정하는 것이 필요합니다.';
  }}
  h+='</div>';

  // [3] 삼중막 구성
  h+='<div class="op-section">';
  h+='<div class="op-title">3. 삼중막 구성 및 재료</div>';
  h+='삼중막 구조는 외피막, 내피(상), 내피(하) 3겹으로 구성되어 있습니다. ';
  h+='공기층① (외피↔내피 상) 간격은 <span class="op-param">'+gap1+' mm</span>, ';
  h+='공기층② (내피 상↔내피 하, 단열층) 간격은 <span class="op-param">'+gap2+' mm</span>입니다. ';
  h+='압력분배 모드는 <span class="op-highlight">"'+pmName+'"</span> 방식이 적용되어, ';
  h+='공기층①에 전체 내압의 '+(pm.r1*100).toFixed(1)+'%, 공기층②에 '+(pm.r2*100).toFixed(1)+'%가 분배됩니다. ';
  h+='이에 따라 각 막의 차압(ΔP)은 외피막 <span class="op-param">'+Math.abs(dpO).toFixed(0)+' Pa</span>, ';
  h+='내피(상) <span class="op-param">'+Math.abs(dpIU).toFixed(0)+' Pa</span>, ';
  h+='내피(하) <span class="op-param">'+Math.abs(dpIL).toFixed(0)+' Pa</span>입니다.';
  h+='<br><br>';
  h+='외피막의 두께는 <span class="op-param">'+thO.toFixed(1)+' mm</span>, 인장강도는 <span class="op-param">'+strO.toLocaleString()+' N/50mm</span>이며, ';
  h+='내피막의 두께는 <span class="op-param">'+thI.toFixed(1)+' mm</span>, 인장강도는 <span class="op-param">'+strI.toLocaleString()+' N/50mm</span>입니다. ';
  h+='공통 탄성계수(E)는 <span class="op-param">'+E+' MPa</span>로 설정되어 있습니다.';
  h+='</div>';

  // [4] 해석 결과
  h+='<div class="op-section">';
  h+='<div class="op-title">4. 구조 해석 결과</div>';
  h+='<strong style="color:#e5e7eb;">외피막:</strong> 최대 장력은 <span class="op-highlight">'+(mxTO/1000).toFixed(2)+' kN/m</span>(평균 '+(avgTO/1000).toFixed(2)+' kN/m)이며, ';
  h+='안전율(SF)은 <span class="op-highlight">'+mSFo.toFixed(2)+'</span>로 '+sfLabel(mSFo)+' 상태입니다. ';
  h+='외피막은 내압과 풍하중, 적설하중을 동시에 부담하므로 가장 큰 하중이 집중됩니다.';
  h+='<br><br>';
  h+='<strong style="color:#fb923c;">내피(상):</strong> 최대 장력은 <span class="op-highlight">'+(mxTIU/1000).toFixed(2)+' kN/m</span>(평균 '+(avgTIU/1000).toFixed(2)+' kN/m)이며, ';
  h+='안전율(SF)은 <span class="op-highlight">'+mSFiu.toFixed(2)+'</span>로 '+sfLabel(mSFiu)+' 상태입니다.';
  h+='<br><br>';
  h+='<strong style="color:#ea580c;">내피(하):</strong> 최대 장력은 <span class="op-highlight">'+(mxTIL/1000).toFixed(2)+' kN/m</span>(평균 '+(avgTIL/1000).toFixed(2)+' kN/m)이며, ';
  h+='안전율(SF)은 <span class="op-highlight">'+mSFil.toFixed(2)+'</span>로 '+sfLabel(mSFil)+' 상태입니다.';
  h+='<br><br>';
  h+='최대 변형량은 <span class="op-highlight">'+mxDef.toFixed(1)+' mm</span>';
  if(deflRatio!==Infinity){{
    h+=' (H/'+deflRatio.toFixed(0)+')';
    if(deflRatio>=200)h+='로 <span class="op-safe">양호한 수준</span>입니다.';
    else if(deflRatio>=100)h+='로 <span class="op-warn">허용 가능하나 주의가 필요한 수준</span>입니다.';
    else h+='로 <span class="op-danger">과도한 변형이 우려</span>됩니다.';
  }}else{{
    h+='로 변형이 발생하지 않았습니다.';
  }}
  h+='</div>';

  // [4.5] 케이블 상세 해석 결과
  const opCDia=+document.getElementById('s-cdia').value;
  const opCBreak=+document.getElementById('s-cbreak').value;
  const opCSfReq=+document.getElementById('s-csf-req').value;
  const opCMatInfo=CableDB[curCableMat];
  // 종합의견 내 케이블 재계산
  let opMaxCF=0,opWorstLC='LC1',opWorstLCn='내압+자중';
  let opMaxWW=0,opMaxLee=0,opMaxTop=0;
  const opLcMax={{1:0,2:0,3:0,4:0,5:0}};
  const opLcActive=[1,2,3,4,5].filter(n=>document.getElementById('lc-'+n).checked);
  for(let j=0;j<=RV;j++)for(let i=0;i<=RU;i++){{
    const vi=j*(RU+1)+i,uu=i/RU,vv=j/RV;
    const xm=(uu-0.5)*2*a_mm,ym=(vv-0.5)*2*b_mm,zm=domeZ_mm(xm,ym);
    if(zm<1)continue;
    const lcs=CableEng.calcLoadCombinations(xm,ym,zm,Ho,dpO,wSpd,wDir,sLoad,cSp);
    if(!lcs)continue;
    const pos=CableEng.positionType(xm,ym,zm,wDir);
    for(const lc of lcs){{
      const lcN=parseInt(lc.id.replace('LC',''));
      if(!opLcActive.includes(lcN))continue;
      const cf=lc.cableT/1000;
      if(cf>opLcMax[lcN])opLcMax[lcN]=cf;
      if(cf>opMaxCF){{opMaxCF=cf;opWorstLC=lc.id;opWorstLCn=lc.name;}}
    }}
    if(opLcActive.includes(2)){{const cf2=lcs[1].cableT/1000;
      if(pos==='windward'&&cf2>opMaxWW)opMaxWW=cf2;
      if(pos==='leeward'&&cf2>opMaxLee)opMaxLee=cf2;
      if(pos==='top'&&cf2>opMaxTop)opMaxTop=cf2;}}
    if(opLcActive.includes(3)&&CableEng.positionType(xm,ym,zm,wDir)==='top'){{
      const cf3=lcs[2].cableT/1000;if(cf3>opMaxTop)opMaxTop=cf3;}}
  }}
  const opCSF=CableEng.safeFactor(opMaxCF,opCBreak);
  const opCAllow=CableEng.allowableForce(opCBreak,opCSfReq);

  h+='<div class="op-section">';
  h+='<div class="op-title">4-2. 케이블 네트 상세 해석</div>';
  h+='<strong style="color:#f59e0b;">케이블 사양:</strong> '+opCMatInfo.name+' (직경 '+opCDia.toFixed(1)+'mm, 파단하중 '+opCBreak.toFixed(1)+'kN, 간격 '+cSp+'mm)<br><br>';
  h+='<strong>하중 조합별 최대 케이블 장력:</strong><br>';
  if(opLcActive.includes(1))h+='&nbsp;&nbsp;LC1 (내압+자중): <span class="op-highlight">'+opLcMax[1].toFixed(2)+' kN</span><br>';
  if(opLcActive.includes(2))h+='&nbsp;&nbsp;LC2 (내압+풍하중): <span class="op-highlight">'+opLcMax[2].toFixed(2)+' kN</span><br>';
  if(opLcActive.includes(3))h+='&nbsp;&nbsp;LC3 (내압+적설): <span class="op-highlight">'+opLcMax[3].toFixed(2)+' kN</span><br>';
  if(opLcActive.includes(4))h+='&nbsp;&nbsp;LC4 (내압+풍+적설): <span class="op-highlight">'+opLcMax[4].toFixed(2)+' kN</span><br>';
  if(opLcActive.includes(5))h+='&nbsp;&nbsp;LC5 (내압상실): <span class="op-highlight">'+opLcMax[5].toFixed(2)+' kN</span><br>';
  h+='<br>가장 불리한 조합은 <span class="op-danger">'+opWorstLC+' ('+opWorstLCn+')</span>으로, 최대 케이블 장력 <span class="op-highlight">'+opMaxCF.toFixed(2)+' kN</span>이 발생합니다. ';
  h+='허용 장력(파단하중/요구SF)은 <span class="op-param">'+opCAllow.toFixed(2)+' kN</span>이며, ';
  h+='케이블 안전율은 <span class="op-highlight">'+opCSF.toFixed(2)+'</span>로 ';
  if(opCSF>=opCSfReq)h+='<span class="op-safe">요구 안전율('+opCSfReq.toFixed(1)+')을 충족</span>합니다.';
  else if(opCSF>=1.5)h+='<span class="op-warn">요구 안전율('+opCSfReq.toFixed(1)+') 미달이나 즉시 위험은 아님</span>. 케이블 직경 상향 또는 간격 축소를 검토하십시오.';
  else h+='<span class="op-danger">파단 위험 수준</span>입니다. 케이블 사양의 즉시 변경이 필요합니다.';
  h+='<br><br>';
  h+='<strong>위치별 분석 (풍하중 기준):</strong><br>';
  h+='&nbsp;&nbsp;풍상측: '+opMaxWW.toFixed(2)+' kN | 풍하측: '+opMaxLee.toFixed(2)+' kN | 정상부: '+opMaxTop.toFixed(2)+' kN';
  // 응력/신장량 정보
  const opStress=CableEng.cableStress(opMaxCF,opCDia);
  const opBreakStress=CableEng.breakStress(opCBreak,opCDia);
  const opCElastic=+document.getElementById('s-celastic').value;
  const opSpan2=Math.sqrt((W/2)**2+H_mm**2)*1.2;
  const opElong=CableEng.cableElongation(opMaxCF,opSpan2,opCElastic,opCDia);
  const opStrain=CableEng.cableStrain(opMaxCF,opCElastic,opCDia);
  h+='<br><br>';
  h+='<strong>케이블 응력/변형 분석:</strong><br>';
  h+='&nbsp;&nbsp;단면적: '+(CableEng.cableArea(opCDia)).toFixed(2)+' mm² (∅'+opCDia.toFixed(1)+'mm)<br>';
  h+='&nbsp;&nbsp;최대 응력: <span class="op-highlight">'+opStress.toFixed(1)+' MPa</span> / 파단 응력: '+opBreakStress.toFixed(0)+' MPa (응력비 '+(opStress/opBreakStress*100).toFixed(1)+'%)<br>';
  h+='&nbsp;&nbsp;신장량: <span class="op-highlight">'+opElong.toFixed(1)+' mm</span> (스팬 '+(opSpan2/1000).toFixed(1)+'m 기준, 변형률 '+opStrain.toFixed(3)+'%)';
  if(opElong>opSpan2/200)h+=' — <span class="op-warn">과대 신장 주의</span>';
  h+='</div>';

  // [5] 종합 판정
  h+='<div class="op-section">';
  h+='<div class="op-title">5. 종합 판정 및 권고사항</div>';

  // 종합 안전 등급
  const allSafe=minSF>=3&&pInt>=rqP&&opCSF>=opCSfReq;
  if(allSafe){{
    h+='현재 설정 조건에서 본 에어돔 구조물의 전체 안전율은 막재 <span class="op-safe">SF='+minSF.toFixed(2)+'</span>, 케이블 <span class="op-safe">SF='+opCSF.toFixed(2)+'</span>로, ';
    h+='일반적인 막구조 설계 권장 기준(SF≥3.0) 및 케이블 요구 안전율(SF≥'+opCSfReq.toFixed(1)+')을 모두 충족하고 있습니다. ';
    h+='내압 역시 요구량을 만족하므로, <span class="op-safe">현재 조건에서는 구조적으로 안전한 것으로 판단</span>됩니다.';
  }}else{{
    let issues=[];
    if(pInt<rqP)issues.push('내압 부족(현재 '+pInt+'Pa, 필요 '+rqP.toFixed(0)+'Pa)');
    if(mSFo<3)issues.push('외피막 안전율 부족(SF='+mSFo.toFixed(2)+')');
    if(mSFiu<3)issues.push('내피(상) 안전율 부족(SF='+mSFiu.toFixed(2)+')');
    if(mSFil<3)issues.push('내피(하) 안전율 부족(SF='+mSFil.toFixed(2)+')');
    if(opCSF<opCSfReq)issues.push('케이블 안전율 부족(SF='+opCSF.toFixed(2)+', 요구 '+opCSfReq.toFixed(1)+')');
    h+='현재 설정 조건에서 다음과 같은 <span class="op-warn">검토 사항</span>이 확인됩니다: ';
    h+=issues.join(', ')+'. ';

    if(minSF>=1.5){{
      h+='<br><br>전체 최소 안전율이 <span class="op-warn">SF='+minSF.toFixed(2)+'</span>로, ';
      h+='즉시 파괴 위험은 없으나 설계 권장 기준(SF≥3.0) 미달이므로 다음의 개선을 권고합니다:';
    }}else{{
      h+='<br><br>전체 최소 안전율이 <span class="op-danger">SF='+minSF.toFixed(2)+'</span>로, ';
      h+='<span class="op-danger">구조적 안전이 확보되지 않은 상태</span>이므로 다음의 개선이 반드시 필요합니다:';
    }}
  }}

  // 구체적 권고사항
  let recs=[];
  if(pInt<rqP)recs.push('내압을 최소 '+rqP.toFixed(0)+' Pa 이상으로 상향 (현재 '+(rqP-pInt).toFixed(0)+' Pa 부족)');
  if(mSFo<3){{
    const needed=(mxTO*0.05/3);
    if(strO<needed)recs.push('외피막 인장강도를 현재 '+strO+'에서 '+(needed).toFixed(0)+' N/50mm 이상으로 상향하거나, 막두께 증가 검토');
    else recs.push('내압 또는 막두께 조정을 통해 외피막 안전율 개선 검토');
  }}
  if(mSFiu<3||mSFil<3)recs.push('내피막 인장강도 상향 또는 압력분배 모드 변경 검토');
  if(wSpd>30)recs.push('풍속 30m/s 초과 조건에서는 비상시 내압 증압 시스템 가동 또는 임시 보강 조치를 권고');
  if(sLoad>=2.0)recs.push('대설 조건(≥2.0kN/m²)에서는 적시 제설 조치와 함께 내압 증압을 병행하는 것이 바람직');
  if(deflRatio<150&&deflRatio!==Infinity)recs.push('변형량이 H/'+deflRatio.toFixed(0)+'으로 다소 크므로, 탄성계수(E) 향상 또는 케이블 간격 축소를 검토');
  if(opCSF<opCSfReq){{
    const nextCable=Object.entries(CableDB).find(([k,v])=>v.breakLoad>opCBreak&&k!=='custom');
    if(nextCable)recs.push('케이블을 '+nextCable[1].name+'(파단하중 '+nextCable[1].breakLoad+'kN)으로 상향하거나, 케이블 간격(현재 '+cSp+'mm)을 축소하여 케이블 SF 개선');
    else recs.push('케이블 직경 상향(파단하중 증가) 또는 케이블 간격 축소를 통해 케이블 안전율 확보 필요');
  }}

  if(recs.length>0&&(minSF<3||pInt<rqP||opCSF<opCSfReq)){{
    h+='<br><br>';
    for(let i=0;i<recs.length;i++){{
      h+='<span class="op-param">'+(i+1)+'. </span>'+recs[i];
      if(i<recs.length-1)h+='<br>';
    }}
  }}

  if(allSafe&&recs.length===0){{
    // 전반적으로 안전한 경우에도 추가 참고사항 기재
    h+='<br><br>다만, 본 시뮬레이션은 정적 해석 기반의 간이 평가이므로 실제 시공 전에는 풍동 실험, 동적 해석 등 정밀 구조 검토를 추가적으로 수행하는 것이 바람직합니다.';
  }}else{{
    h+='<br><br>참고: 본 시뮬레이션은 정적 해석 기반의 간이 평가이므로, 상기 결과는 설계 방향 수립을 위한 참고 자료로 활용하시고, 최종 설계에는 정밀 구조 해석을 병행하시기 바랍니다.';
  }}

  h+='</div>';

  // [6] 타임스탬프
  const now=new Date();
  const ts=now.getFullYear()+'.'+(''+(now.getMonth()+1)).padStart(2,'0')+'.'+(''+now.getDate()).padStart(2,'0')+' '+(''+now.getHours()).padStart(2,'0')+':'+(''+now.getMinutes()).padStart(2,'0');
  h+='<div style="text-align:right;font-size:11px;color:#4b5563;margin-top:12px;border-top:1px solid #2a3545;padding-top:8px;">';
  h+='해석 일시: '+ts+' | OzoMeta AirDome Simulator';
  h+='</div>';

  return h;
}}
</script>
</body>
</html>"""

