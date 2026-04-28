"""
Solar Simulation Module for AIR DOME 3D Simulator
====================================================
Part of the OzoMeta AIR DOME 3D Viewer and Simulator system.

This module generates an interactive 3D solar/daylight simulation
using Three.js. It computes real solar positions based on latitude,
longitude, date, and time using the Solar Position Algorithm (SPA),
and renders solar irradiance heatmaps with shadow casting on the
air dome surface.

Features:
  - Address → Lat/Lng geocoding (Nominatim / manual)
  - Year/Month/Day/Hour time controls
  - Season quick-select (Spring/Summer/Autumn/Winter)
  - Playback with speed control
  - Solar irradiance heatmap + shadow visualization
  - CSV data export + PNG screenshot
  - White theme UI with premium sun visuals

Author: OzoMeta
License: Proprietary
"""

import base64, os


def generate_solar_simulation_html(params):
    """Three.js 기반 일조 시뮬레이션 HTML 생성 (White Theme + Premium Visuals)"""
    logo_b64 = ""
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as _lf:
            logo_b64 = base64.b64encode(_lf.read()).decode()
    logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else "logo.png"

    W = params.get('width', 50000)
    L = params.get('length', 100000)
    H = params.get('height', 30000)
    cable_sp = params.get('cable_spacing', 3600)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>에어돔 일조 시뮬레이션 | © OZOMETA</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:#f0f4f8;font-family:'Segoe UI','Apple SD Gothic Neo',sans-serif;overflow:hidden;color:#1e293b;}}

  /* ═══ 왼쪽 패널 (화이트 테마) ═══ */
  #panel{{position:absolute;top:0;left:0;bottom:0;width:320px;z-index:20;
    background:#ffffff;border-right:1px solid #e2e8f0;display:flex;flex-direction:column;
    box-shadow:2px 0 12px rgba(0,0,0,0.06);}}
  #panel-header{{padding:14px 16px;background:linear-gradient(135deg,#1e3a5f 0%,#2d5a87 100%);
    border-bottom:1px solid #e2e8f0;flex-shrink:0;}}
  #panel-header .logo-top{{display:flex;align-items:center;gap:10px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.15);}}
  #panel-header .logo-top img{{height:36px;object-fit:contain;}}
  #panel-header .logo-top .brand{{font-size:10px;color:rgba(255,255,255,0.7);letter-spacing:1px;font-weight:600;}}
  #panel-header h2{{font-size:16px;color:#fbbf24;display:flex;align-items:center;gap:6px;margin:0;text-shadow:0 1px 3px rgba(0,0,0,0.3);}}
  #panel-header .info{{font-size:13px;color:rgba(255,255,255,0.9);margin-top:6px;line-height:1.6;font-weight:500;}}

  /* 탭 */
  .tabs{{display:flex;border-bottom:1px solid #e2e8f0;background:#f8fafc;flex-shrink:0;}}
  .tab{{flex:1;padding:10px 0;text-align:center;font-size:12px;font-weight:600;color:#94a3b8;
    cursor:pointer;border-bottom:2px solid transparent;transition:all 0.2s;}}
  .tab:hover{{color:#64748b;background:#f1f5f9;}}
  .tab.on{{color:#d97706;border-bottom-color:#d97706;background:#fffbeb;}}

  .tab-body{{flex:1;overflow-y:auto;padding:0;min-height:0;}}
  .tab-body::-webkit-scrollbar{{width:4px;}}
  .tab-body::-webkit-scrollbar-thumb{{background:#cbd5e1;border-radius:2px;}}
  .tp{{display:none;padding:14px 16px;}}
  .tp.on{{display:block;}}

  /* 섹션 제목 */
  .st{{font-size:11px;font-weight:700;color:#b45309;letter-spacing:1px;text-transform:uppercase;
    margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #fde68a;}}

  /* 슬라이더 */
  .f{{margin-bottom:12px;}}
  .f .fl{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;}}
  .f .fn{{font-size:11px;color:#64748b;font-weight:500;}}
  .f .fv{{font-size:13px;color:#b45309;font-weight:700;}}
  .f .fv .u{{font-size:10px;color:#94a3b8;font-weight:400;margin-left:2px;}}
  .f input[type=range]{{width:100%;height:5px;-webkit-appearance:none;background:#e2e8f0;
    border-radius:3px;outline:none;}}
  .f input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:18px;height:18px;
    border-radius:50%;background:#d97706;cursor:pointer;border:3px solid #fff;
    box-shadow:0 1px 4px rgba(0,0,0,0.2);}}

  /* 입력 필드 */
  .input-row{{display:flex;align-items:center;gap:6px;margin-bottom:8px;}}
  .input-row label{{font-size:11px;color:#64748b;min-width:50px;font-weight:500;}}
  .input-row input[type=text],.input-row input[type=number]{{flex:1;background:#f8fafc;
    border:1px solid #e2e8f0;border-radius:6px;color:#1e293b;font-size:12px;font-weight:600;
    padding:7px 10px;outline:none;transition:border 0.2s;}}
  .input-row input:focus{{border-color:#d97706;box-shadow:0 0 0 3px rgba(217,119,6,0.1);}}
  .input-row select{{flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
    color:#1e293b;font-size:12px;font-weight:600;padding:7px 10px;outline:none;}}

  /* 버튼 공용 */
  .mode-row{{display:flex;gap:5px;margin:6px 0;}}
  .mbtn{{flex:1;padding:7px 4px;font-size:10px;text-align:center;border:1px solid #e2e8f0;
    background:#f8fafc;color:#64748b;border-radius:6px;cursor:pointer;transition:all 0.15s;font-weight:500;}}
  .mbtn:hover{{border-color:#d97706;color:#b45309;background:#fffbeb;}}
  .mbtn.on{{background:#fffbeb;border-color:#d97706;color:#b45309;font-weight:700;box-shadow:0 1px 3px rgba(217,119,6,0.15);}}

  /* 주소 검색 */
  #addr-input{{width:100%;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
    color:#1e293b;font-size:12px;padding:9px 12px;outline:none;margin-bottom:8px;}}
  #addr-input:focus{{border-color:#d97706;box-shadow:0 0 0 3px rgba(217,119,6,0.1);}}
  #addr-search-btn{{width:100%;padding:9px;font-size:12px;font-weight:700;
    background:linear-gradient(135deg,#d97706,#b45309);border:none;color:#fff;
    border-radius:6px;cursor:pointer;transition:all 0.2s;box-shadow:0 2px 6px rgba(217,119,6,0.3);}}
  #addr-search-btn:hover{{box-shadow:0 4px 12px rgba(217,119,6,0.4);transform:translateY(-1px);}}
  .coord-display{{font-size:11px;color:#94a3b8;margin-top:8px;line-height:1.6;
    background:#f8fafc;padding:8px 10px;border-radius:6px;border:1px solid #e2e8f0;}}
  .coord-display span{{color:#b45309;font-weight:700;}}

  /* 플레이어 컨트롤 */
  .player-bar{{display:flex;align-items:center;gap:8px;margin:10px 0;
    background:#f8fafc;padding:8px 10px;border-radius:8px;border:1px solid #e2e8f0;}}
  .player-btn{{width:36px;height:36px;border-radius:50%;border:2px solid #d97706;
    background:#fff;color:#d97706;font-size:14px;cursor:pointer;
    display:flex;align-items:center;justify-content:center;transition:all 0.15s;
    box-shadow:0 2px 6px rgba(0,0,0,0.08);}}
  .player-btn:hover{{background:#d97706;color:#fff;}}
  .player-btn.playing{{background:#d97706;color:#fff;box-shadow:0 0 12px rgba(217,119,6,0.4);}}
  .player-progress{{flex:1;height:5px;background:#e2e8f0;border-radius:3px;cursor:pointer;position:relative;}}
  .player-progress-fill{{height:100%;background:linear-gradient(90deg,#fbbf24,#d97706);border-radius:3px;transition:width 0.1s;}}
  .player-time{{font-size:12px;color:#b45309;font-weight:700;min-width:42px;text-align:right;}}

  /* 하단 고정 영역 */
  #panel-fixed{{flex-shrink:0;border-top:1px solid #e2e8f0;background:#fefce8;padding:10px 14px;}}

  /* 태양 정보 */
  .solar-info{{background:#fff;border-radius:8px;padding:10px 12px;margin-top:8px;
    font-size:11px;line-height:2.0;border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,0.04);}}
  .solar-info .row{{display:flex;justify-content:space-between;padding:2px 0;}}
  .solar-info .row .dot{{display:inline-block;width:8px;height:8px;border-radius:3px;margin-right:6px;vertical-align:middle;}}
  .solar-info .val{{color:#b45309;font-weight:700;}}

  /* ═══ 오른쪽 패널 ═══ */
  #results{{position:absolute;top:0;right:0;bottom:0;width:280px;z-index:20;
    background:#ffffff;border-left:1px solid #e2e8f0;display:flex;flex-direction:column;
    box-shadow:-2px 0 12px rgba(0,0,0,0.06);}}
  #results h3{{font-size:14px;padding:10px 14px;margin:0;
    background:linear-gradient(135deg,#1e3a5f,#2d5a87);color:#fbbf24;
    border-bottom:1px solid #e2e8f0;position:sticky;top:0;z-index:1;flex-shrink:0;
    text-shadow:0 1px 2px rgba(0,0,0,0.2);}}
  #res-body{{padding:6px 0;flex:1;overflow-y:auto;}}
  #res-body::-webkit-scrollbar{{width:4px;}}
  #res-body::-webkit-scrollbar-thumb{{background:#cbd5e1;border-radius:2px;}}

  /* 결과 카드 */
  .lcard{{margin:5px 8px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;overflow:hidden;
    box-shadow:0 1px 3px rgba(0,0,0,0.04);}}
  .lcard-h{{padding:8px 12px;display:flex;align-items:center;gap:7px;font-size:13px;font-weight:700;
    border-bottom:1px solid #f1f5f9;background:#f8fafc;color:#334155;}}
  .lcard-h .cdot{{width:9px;height:9px;border-radius:50%;flex-shrink:0;}}
  .lcard-row{{display:flex;align-items:baseline;padding:5px 12px;}}
  .lcard-row .k{{flex:1;font-size:12px;color:#64748b;}}
  .lcard-row .v{{font-size:14px;font-weight:700;text-align:right;color:#1e293b;}}
  .lcard-row .v .u{{font-size:10px;color:#94a3b8;font-weight:400;margin-left:2px;}}

  /* 다운로드 버튼 */
  .btn-download{{width:calc(100% - 16px);margin:5px 8px;padding:9px;font-size:11px;font-weight:700;
    border-radius:6px;cursor:pointer;transition:all 0.2s;text-align:center;}}
  .btn-dl-csv{{background:#ecfdf5;border:1px solid #6ee7b7;color:#047857;}}
  .btn-dl-csv:hover{{background:#d1fae5;box-shadow:0 2px 8px rgba(4,120,87,0.15);}}
  .btn-dl-png{{background:#eff6ff;border:1px solid #93c5fd;color:#1d4ed8;}}
  .btn-dl-png:hover{{background:#dbeafe;box-shadow:0 2px 8px rgba(29,78,216,0.15);}}

  /* 푸터 */
  #res-footer{{border-top:1px solid #e2e8f0;background:#f8fafc;padding:8px 10px;flex-shrink:0;}}
  #logo-area{{display:flex;align-items:center;justify-content:center;padding:6px 0 4px;}}
  #logo-area img{{height:36px;object-fit:contain;}}

  /* 범례 */
  #legend{{position:absolute;bottom:14px;left:320px;z-index:15;background:rgba(255,255,255,0.92);
    border-radius:8px;padding:8px 16px;display:flex;align-items:center;gap:10px;font-size:11px;
    border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.08);color:#64748b;}}
  #legend canvas{{border-radius:3px;}}

  /* 뷰 버튼 */
  .tb{{padding:6px 8px;font-size:10px;border:1px solid #e2e8f0;background:#fff;
    color:#64748b;border-radius:6px;cursor:pointer;transition:all 0.15s;white-space:nowrap;
    text-align:center;flex:1 1 auto;min-width:0;font-weight:500;}}
  .tb:hover{{border-color:#d97706;color:#b45309;}}
  .tb.on{{background:#fffbeb;border-color:#d97706;color:#b45309;font-weight:700;}}

  .view-row{{display:flex;gap:4px;margin:6px 0;flex-wrap:wrap;}}
</style>
</head>
<body>

<!-- ═══════ 왼쪽 패널 ═══════ -->
<div id="panel">
  <div id="panel-header">
    <div class="logo-top">
      <img src="{logo_src}" alt="OZO META">
      <span class="brand">© OZOMETA | Solar Simulation</span>
    </div>
    <h2>☀️ 에어돔 일조 시뮬레이션</h2>
    <div class="info">
      <span style="color:#fbbf24;font-weight:700;">{W:,.0f}</span> ×
      <span style="color:#fbbf24;font-weight:700;">{L:,.0f}</span> ×
      <span style="color:#fbbf24;font-weight:700;">{H:,.0f}</span> mm
      &nbsp;|&nbsp; {W*L/1e6:,.0f} m²
    </div>
  </div>

  <div class="tabs">
    <div class="tab on" onclick="openTab('t-location')">위치</div>
    <div class="tab" onclick="openTab('t-time')">시간</div>
    <div class="tab" onclick="openTab('t-visual')">시각화</div>
  </div>

  <div class="tab-body">
    <!-- ── 탭1: 위치 설정 ── -->
    <div class="tp on" id="t-location">
      <div class="st">주소 검색</div>
      <input type="text" id="addr-input" placeholder="주소를 입력하세요 (예: 서울특별시 강남구...)" value="서울특별시 중구 세종대로 110">
      <button id="addr-search-btn" onclick="searchAddress()">🔍 주소 검색 (Geocoding)</button>
      <div class="coord-display" id="coord-display">
        위도: <span id="disp-lat">37.5665</span>° &nbsp;|&nbsp;
        경도: <span id="disp-lng">126.9780</span>°
      </div>

      <div style="margin-top:14px;">
        <div class="st">직접 입력</div>
        <div class="input-row">
          <label>위도</label>
          <input type="number" id="inp-lat" value="37.5665" step="0.0001" onchange="updateFromManual()">
        </div>
        <div class="input-row">
          <label>경도</label>
          <input type="number" id="inp-lng" value="126.9780" step="0.0001" onchange="updateFromManual()">
        </div>
        <div class="input-row">
          <label>시간대</label>
          <select id="inp-tz" onchange="updateSolar()">
            <option value="9" selected>KST (UTC+9)</option>
            <option value="8">CST (UTC+8)</option>
            <option value="0">UTC</option>
            <option value="-5">EST (UTC-5)</option>
          </select>
        </div>
      </div>

      <div style="margin-top:14px;">
        <div class="st">주요 도시 프리셋</div>
        <div class="mode-row">
          <div class="mbtn on" onclick="setCity(37.5665,126.978,'서울',this)">서울</div>
          <div class="mbtn" onclick="setCity(35.1796,129.0756,'부산',this)">부산</div>
          <div class="mbtn" onclick="setCity(33.4996,126.5312,'제주',this)">제주</div>
        </div>
        <div class="mode-row">
          <div class="mbtn" onclick="setCity(35.6762,139.6503,'도쿄',this)">도쿄</div>
          <div class="mbtn" onclick="setCity(31.2304,121.4737,'상해',this)">상해</div>
          <div class="mbtn" onclick="setCity(25.0330,121.5654,'타이베이',this)">타이베이</div>
        </div>
      </div>
    </div>

    <!-- ── 탭2: 시간 설정 ── -->
    <div class="tp" id="t-time">
      <div class="st">날짜 / 시간</div>
      <div class="input-row">
        <label>년도</label>
        <input type="number" id="inp-year" value="2026" min="2000" max="2050" onchange="updateSolar()">
      </div>
      <div class="input-row">
        <label>월</label>
        <input type="number" id="inp-month" value="6" min="1" max="12" onchange="updateSolar()">
      </div>
      <div class="input-row">
        <label>일</label>
        <input type="number" id="inp-day" value="21" min="1" max="31" onchange="updateSolar()">
      </div>
      <div class="f">
        <div class="fl"><span class="fn">시간</span><span class="fv"><span id="v-hour">12:00</span></span></div>
        <input type="range" id="s-hour" min="0" max="23.99" value="12" step="0.25" oninput="onHourChange()">
      </div>

      <div style="margin-top:14px;">
        <div class="st">계절 바로가기</div>
        <div class="mode-row">
          <div class="mbtn" onclick="setSeason('spring',this)">🌸 봄</div>
          <div class="mbtn" onclick="setSeason('summer',this)">☀️ 여름</div>
          <div class="mbtn" onclick="setSeason('autumn',this)">🍂 가을</div>
          <div class="mbtn" onclick="setSeason('winter',this)">❄️ 겨울</div>
        </div>
        <div style="margin-top:8px;">
          <div class="st">특수일</div>
          <div class="mode-row">
            <div class="mbtn" onclick="setSpecialDay('summer_solstice',this)">하지</div>
            <div class="mbtn" onclick="setSpecialDay('winter_solstice',this)">동지</div>
            <div class="mbtn" onclick="setSpecialDay('vernal_equinox',this)">춘분</div>
            <div class="mbtn" onclick="setSpecialDay('autumnal_equinox',this)">추분</div>
          </div>
        </div>
      </div>

      <div style="margin-top:14px;">
        <div class="st">재생 컨트롤</div>
        <div class="player-bar">
          <button class="player-btn" id="btn-play" onclick="togglePlay()" title="재생/정지">▶</button>
          <div class="player-progress" id="progress-bar" onclick="seekProgress(event)">
            <div class="player-progress-fill" id="progress-fill" style="width:50%"></div>
          </div>
          <span class="player-time" id="play-time">12:00</span>
        </div>
        <div class="input-row">
          <label>재생속도</label>
          <select id="play-speed" onchange="updatePlaySpeed()">
            <option value="0.5">0.5x (느리게)</option>
            <option value="1" selected>1x (보통)</option>
            <option value="2">2x (빠르게)</option>
            <option value="4">4x (매우 빠르게)</option>
          </select>
        </div>
        <div class="input-row">
          <label>재생범위</label>
          <select id="play-mode">
            <option value="day" selected>하루 (일출~일몰)</option>
            <option value="year">1년 (월별 정오)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ── 탭3: 시각화 설정 ── -->
    <div class="tp" id="t-visual">
      <div class="st">표시 옵션</div>
      <div class="mode-row">
        <div class="mbtn on" id="btn-heatmap" onclick="toggleVis('heatmap',this)">히트맵</div>
        <div class="mbtn on" id="btn-shadow" onclick="toggleVis('shadow',this)">그림자</div>
        <div class="mbtn" id="btn-sunpath" onclick="toggleVis('sunpath',this)">태양경로</div>
      </div>
      <div class="mode-row">
        <div class="mbtn on" id="btn-dome-wire" onclick="toggleVis('domewire',this)">돔 와이어</div>
        <div class="mbtn" id="btn-ground-grid" onclick="toggleVis('groundgrid',this)">그라운드 그리드</div>
        <div class="mbtn on" id="btn-sun-glow" onclick="toggleVis('sunglow',this)">태양 글로우</div>
      </div>

      <div style="margin-top:14px;">
        <div class="st">히트맵 설정</div>
        <div class="f">
          <div class="fl"><span class="fn">히트맵 강도</span><span class="fv"><span id="v-hm-opacity">80</span><span class="u">%</span></span></div>
          <input type="range" id="s-hm-opacity" min="10" max="100" value="80" step="5" oninput="updateHeatmapOpacity()">
        </div>
      </div>

      <div style="margin-top:14px;">
        <div class="st">카메라 뷰</div>
        <div class="view-row">
          <button class="tb on" onclick="setView('perspective',this)">원근</button>
          <button class="tb" onclick="setView('top',this)">평면</button>
          <button class="tb" onclick="setView('south',this)">남측</button>
          <button class="tb" onclick="setView('east',this)">동측</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 하단 고정: 태양 정보 -->
  <div id="panel-fixed">
    <div class="st">현재 태양 정보</div>
    <div class="solar-info">
      <div class="row"><span><span class="dot" style="background:#d97706"></span>태양 고도</span><span class="val" id="si-altitude">--°</span></div>
      <div class="row"><span><span class="dot" style="background:#ea580c"></span>태양 방위</span><span class="val" id="si-azimuth">--°</span></div>
      <div class="row"><span><span class="dot" style="background:#16a34a"></span>일출 시각</span><span class="val" id="si-sunrise">--:--</span></div>
      <div class="row"><span><span class="dot" style="background:#2563eb"></span>일몰 시각</span><span class="val" id="si-sunset">--:--</span></div>
      <div class="row"><span><span class="dot" style="background:#7c3aed"></span>일조 시간</span><span class="val" id="si-daylen">-- h</span></div>
      <div class="row"><span><span class="dot" style="background:#dc2626"></span>직달 일사량</span><span class="val" id="si-dni">-- W/m²</span></div>
    </div>
  </div>
</div>

<!-- ═══════ 오른쪽 패널 ═══════ -->
<div id="results">
  <h3>📊 일조 해석 결과</h3>
  <div id="res-body">
    <div class="lcard">
      <div class="lcard-h"><span class="cdot" style="background:#d97706"></span>일일 일사량 요약</div>
      <div class="lcard-row"><span class="k">총 일사량 (GHI)</span><span class="v" id="r-ghi">--<span class="u">kWh/m²</span></span></div>
      <div class="lcard-row"><span class="k">직달 일사량 (DNI)</span><span class="v" id="r-dni">--<span class="u">kWh/m²</span></span></div>
      <div class="lcard-row"><span class="k">산란 일사량 (DHI)</span><span class="v" id="r-dhi">--<span class="u">kWh/m²</span></span></div>
      <div class="lcard-row"><span class="k">피크 일사강도</span><span class="v" id="r-peak">--<span class="u">W/m²</span></span></div>
    </div>
    <div class="lcard">
      <div class="lcard-h"><span class="cdot" style="background:#16a34a"></span>돔 표면 분석</div>
      <div class="lcard-row"><span class="k">돔 표면적</span><span class="v" id="r-area">--<span class="u">m²</span></span></div>
      <div class="lcard-row"><span class="k">일조 면적 비율</span><span class="v" id="r-sun-ratio">--<span class="u">%</span></span></div>
      <div class="lcard-row"><span class="k">음영 면적 비율</span><span class="v" id="r-shade-ratio">--<span class="u">%</span></span></div>
      <div class="lcard-row"><span class="k">평균 입사각</span><span class="v" id="r-avg-angle">--<span class="u">°</span></span></div>
    </div>
    <div class="lcard">
      <div class="lcard-h"><span class="cdot" style="background:#2563eb"></span>에너지 환산 (참고)</div>
      <div class="lcard-row"><span class="k">일일 총 수열량</span><span class="v" id="r-total-energy">--<span class="u">kWh</span></span></div>
      <div class="lcard-row"><span class="k">월간 예상</span><span class="v" id="r-monthly">--<span class="u">MWh</span></span></div>
      <div class="lcard-row"><span class="k">연간 예상</span><span class="v" id="r-yearly">--<span class="u">MWh</span></span></div>
    </div>
    <div class="lcard">
      <div class="lcard-h"><span class="cdot" style="background:#7c3aed"></span>그림자 분석</div>
      <div class="lcard-row"><span class="k">현재 그림자 길이</span><span class="v" id="r-shadow-len">--<span class="u">m</span></span></div>
      <div class="lcard-row"><span class="k">그림자 방향</span><span class="v" id="r-shadow-dir">--<span class="u">°</span></span></div>
      <div class="lcard-row"><span class="k">그림자 면적</span><span class="v" id="r-shadow-area">--<span class="u">m²</span></span></div>
    </div>
  </div>
  <button class="btn-download btn-dl-csv" onclick="downloadCSV()">📥 일사량 데이터 CSV 다운로드</button>
  <button class="btn-download btn-dl-png" onclick="downloadPNG()">📸 현재 뷰 스크린샷 (PNG)</button>
  <div id="res-footer">
    <div id="logo-area"><img src="{logo_src}" alt="OZO META"></div>
  </div>
</div>

<!-- 범례 -->
<div id="legend">
  <span style="color:#94a3b8;">일사량</span>
  <canvas id="legend-canvas" width="200" height="14"></canvas>
  <span style="color:#94a3b8;">낮음</span>
  <span style="color:#b45309;font-weight:700;" id="legend-max">1000 W/m²</span>
</div>

<!-- ═══════ Three.js ═══════ -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
"use strict";

/* ═══ 전역 상수 ═══ */
const W={W}, L={L}, H={H};
const W_m=W/1000, L_m=L/1000, H_m=H/1000;
const CABLE_SP={cable_sp};
const DEG=Math.PI/180, RAD=180/Math.PI;

/* ═══ 상태 ═══ */
let lat=37.5665, lng=126.9780, tzOff=9;
let curYear=2026, curMonth=6, curDay=21, curHour=12;
let isPlaying=false, playSpeed=1, playInterval=null;
let showHeatmap=true, showShadow=true, showSunpath=false;
let showDomeWire=true, showGroundGrid=false, showSunGlow=true;
let heatmapIntensity=0.8;

/* ═══ 태양 위치 알고리즘 (SPA 간이판) ═══ */
const SolarCalc = {{
  julianDay(y,m,d,h,tz) {{
    const dt = new Date(Date.UTC(y,m-1,d, Math.floor(h-tz), ((h-tz)%1)*60));
    return dt.getTime()/86400000 + 2440587.5;
  }},
  solarPosition(y,m,d,hour,tz) {{
    const jd = this.julianDay(y,m,d,hour,tz);
    const n = jd - 2451545.0;
    let Ls = (280.460 + 0.9856474*n) % 360; if(Ls<0) Ls+=360;
    let g = (357.528 + 0.9856003*n) % 360; if(g<0) g+=360;
    const gRad = g*DEG;
    const ecLong = Ls + 1.915*Math.sin(gRad) + 0.020*Math.sin(2*gRad);
    const ecLongRad = ecLong*DEG;
    const obliq = (23.439 - 0.0000004*n)*DEG;
    const sinDec = Math.sin(obliq)*Math.sin(ecLongRad);
    const dec = Math.asin(sinDec);
    const ra = Math.atan2(Math.cos(obliq)*Math.sin(ecLongRad), Math.cos(ecLongRad));
    let gmst = (280.46061837 + 360.98564736629*n) % 360; if(gmst<0) gmst+=360;
    const lmst = (gmst + lng) * DEG;
    const ha = lmst - ra;
    const latRad = lat*DEG;
    const sinAlt = Math.sin(latRad)*Math.sin(dec) + Math.cos(latRad)*Math.cos(dec)*Math.cos(ha);
    const altitude = Math.asin(sinAlt)*RAD;
    const cosAz = (Math.sin(dec)-Math.sin(latRad)*sinAlt)/(Math.cos(latRad)*Math.cos(Math.asin(sinAlt)));
    let azimuth = Math.acos(Math.max(-1,Math.min(1,cosAz)))*RAD;
    if(Math.sin(ha)>0) azimuth=360-azimuth;
    return {{ altitude, azimuth, declination:dec*RAD }};
  }},
  sunriseSunset(y,m,d,tz) {{
    let rise=null, set=null;
    for(let h=0;h<24;h+=0.1) {{
      const p1=this.solarPosition(y,m,d,h,tz);
      const p2=this.solarPosition(y,m,d,h+0.1,tz);
      if(p1.altitude<=0 && p2.altitude>0) rise=h+0.1*(0-p1.altitude)/(p2.altitude-p1.altitude);
      if(p1.altitude>0 && p2.altitude<=0) set=h+0.1*(0-p1.altitude)/(p2.altitude-p1.altitude);
    }}
    return {{ sunrise:rise, sunset:set }};
  }},
  directNormalIrradiance(altitude) {{
    if(altitude<=0) return 0;
    const altRad=altitude*DEG;
    const AM=1/(Math.sin(altRad)+0.50572*Math.pow(6.07995+altitude,-1.6364));
    return Math.max(0, 1361*0.7*Math.pow(0.678,AM));
  }},
  globalHorizontalIrradiance(altitude,DNI) {{
    if(altitude<=0) return 0;
    const altRad=altitude*DEG;
    return DNI*Math.sin(altRad)+0.1*1361*Math.sin(altRad);
  }}
}};

/* ═══ Three.js 초기화 ═══ */
const canvas3d = document.createElement('canvas');
canvas3d.style.cssText = 'position:absolute;top:0;left:320px;right:280px;bottom:0;';
document.body.appendChild(canvas3d);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50,1,0.1,10000);
const renderer = new THREE.WebGLRenderer({{canvas:canvas3d, antialias:true, preserveDrawingBuffer:true, alpha:true}});
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.outputEncoding = THREE.sRGBEncoding;

function onResize() {{
  const w=window.innerWidth-320-280, h=window.innerHeight;
  canvas3d.width=w; canvas3d.height=h;
  camera.aspect=w/h; camera.updateProjectionMatrix();
  renderer.setSize(w,h); renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
}}
window.addEventListener('resize', onResize);
onResize();

/* ═══ 하늘 배경 (동적 그라디언트) ═══ */
function updateSkyColor(altitude) {{
  let topColor, bottomColor;
  if(altitude>30) {{
    topColor=new THREE.Color(0x1a6fc4);
    bottomColor=new THREE.Color(0x87ceeb);
  }} else if(altitude>10) {{
    const t=(altitude-10)/20;
    topColor=new THREE.Color(0x1a4f8a).lerp(new THREE.Color(0x1a6fc4),t);
    bottomColor=new THREE.Color(0xf5c88a).lerp(new THREE.Color(0x87ceeb),t);
  }} else if(altitude>0) {{
    const t=altitude/10;
    topColor=new THREE.Color(0x1a2a4a).lerp(new THREE.Color(0x1a4f8a),t);
    bottomColor=new THREE.Color(0xf57c3a).lerp(new THREE.Color(0xf5c88a),t);
  }} else if(altitude>-10) {{
    const t=(altitude+10)/10;
    topColor=new THREE.Color(0x0a0f1a).lerp(new THREE.Color(0x1a2a4a),t);
    bottomColor=new THREE.Color(0x1a1530).lerp(new THREE.Color(0xf57c3a),t);
  }} else {{
    topColor=new THREE.Color(0x050810);
    bottomColor=new THREE.Color(0x0a0f1a);
  }}
  scene.background=bottomColor;
  scene.fog=new THREE.Fog(bottomColor, Math.max(W_m,L_m)*2, Math.max(W_m,L_m)*6);
}}

/* 카메라 */
const scaleF = Math.max(W_m, L_m)/100;
camera.position.set(scaleF*80, scaleF*60, scaleF*80);
camera.lookAt(0,0,0);

/* 카메라 컨트롤 */
let camTheta=Math.PI/4, camPhi=Math.PI/4, camDist=scaleF*120;
let isDragging=false, lastMX=0, lastMY=0;
const target=new THREE.Vector3(0, H_m*0.3, 0);

function updateCamera() {{
  camera.position.set(
    target.x+camDist*Math.sin(camPhi)*Math.cos(camTheta),
    target.y+camDist*Math.cos(camPhi),
    target.z+camDist*Math.sin(camPhi)*Math.sin(camTheta)
  );
  camera.lookAt(target);
}}
canvas3d.addEventListener('mousedown', e=>{{ isDragging=true; lastMX=e.clientX; lastMY=e.clientY; }});
canvas3d.addEventListener('mousemove', e=>{{
  if(!isDragging)return;
  camTheta-=(e.clientX-lastMX)*0.005;
  camPhi=Math.max(0.1,Math.min(Math.PI/2-0.01, camPhi-(e.clientY-lastMY)*0.005));
  lastMX=e.clientX; lastMY=e.clientY; updateCamera();
}});
canvas3d.addEventListener('mouseup', ()=>isDragging=false);
canvas3d.addEventListener('mouseleave', ()=>isDragging=false);
canvas3d.addEventListener('wheel', e=>{{
  camDist=Math.max(scaleF*20, Math.min(scaleF*300, camDist+e.deltaY*0.05*scaleF));
  updateCamera();
}});
updateCamera();

/* ═══ 조명 ═══ */
const ambientLight = new THREE.AmbientLight(0x8899bb, 0.5);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0x87ceeb, 0x556644, 0.4);
scene.add(hemiLight);

/* 태양광 (DirectionalLight + shadow) */
const sunLight = new THREE.DirectionalLight(0xfff8e7, 2.0);
sunLight.castShadow = true;
const shadowRange = Math.max(W_m, L_m)*1.5;
sunLight.shadow.camera.left=-shadowRange;
sunLight.shadow.camera.right=shadowRange;
sunLight.shadow.camera.top=shadowRange;
sunLight.shadow.camera.bottom=-shadowRange;
sunLight.shadow.camera.near=0.1;
sunLight.shadow.camera.far=shadowRange*4;
sunLight.shadow.mapSize.width=4096;
sunLight.shadow.mapSize.height=4096;
sunLight.shadow.bias=-0.0005;
sunLight.shadow.normalBias=0.02;
scene.add(sunLight);
scene.add(sunLight.target);

/* ═══ 프리미엄 태양 비주얼 ═══ */
const sunGroup = new THREE.Group();
scene.add(sunGroup);

/* 태양 코어 (밝은 구체) */
const sunCoreGeo = new THREE.SphereGeometry(scaleF*2.0, 32, 32);
const sunCoreMat = new THREE.MeshBasicMaterial({{color:0xfff8dc}});
const sunCore = new THREE.Mesh(sunCoreGeo, sunCoreMat);
sunGroup.add(sunCore);

/* 태양 글로우 (여러 레이어) */
function createGlowSprite(size, color, opacity) {{
  const canvas=document.createElement('canvas');
  canvas.width=256; canvas.height=256;
  const ctx=canvas.getContext('2d');
  const cx=128, cy=128;
  const grd=ctx.createRadialGradient(cx,cy,0, cx,cy,128);
  grd.addColorStop(0, 'rgba('+((color>>16)&0xff)+','+((color>>8)&0xff)+','+(color&0xff)+','+opacity+')');
  grd.addColorStop(0.3, 'rgba('+((color>>16)&0xff)+','+((color>>8)&0xff)+','+(color&0xff)+','+(opacity*0.5)+')');
  grd.addColorStop(1, 'rgba('+((color>>16)&0xff)+','+((color>>8)&0xff)+','+(color&0xff)+',0)');
  ctx.fillStyle=grd;
  ctx.fillRect(0,0,256,256);
  const tex=new THREE.CanvasTexture(canvas);
  const mat=new THREE.SpriteMaterial({{map:tex, transparent:true, blending:THREE.AdditiveBlending, depthWrite:false}});
  const sprite=new THREE.Sprite(mat);
  sprite.scale.set(size,size,1);
  return sprite;
}}

const glowInner=createGlowSprite(scaleF*12, 0xfff4c0, 0.9);
sunGroup.add(glowInner);
const glowMid=createGlowSprite(scaleF*25, 0xffcc44, 0.4);
sunGroup.add(glowMid);
const glowOuter=createGlowSprite(scaleF*45, 0xff8800, 0.15);
sunGroup.add(glowOuter);
const glowHaze=createGlowSprite(scaleF*70, 0xffaa33, 0.06);
sunGroup.add(glowHaze);

/* 태양 광선 (lens flare 느낌) */
const rayCount=8;
const rays=[];
for(let i=0;i<rayCount;i++) {{
  const rayCanvas=document.createElement('canvas');
  rayCanvas.width=256; rayCanvas.height=32;
  const rctx=rayCanvas.getContext('2d');
  const rGrd=rctx.createLinearGradient(0,16,256,16);
  rGrd.addColorStop(0,'rgba(255,240,180,0)');
  rGrd.addColorStop(0.3,'rgba(255,240,180,0.25)');
  rGrd.addColorStop(0.5,'rgba(255,240,180,0.35)');
  rGrd.addColorStop(0.7,'rgba(255,240,180,0.25)');
  rGrd.addColorStop(1,'rgba(255,240,180,0)');
  rctx.fillStyle=rGrd;
  rctx.fillRect(0,0,256,32);
  const rTex=new THREE.CanvasTexture(rayCanvas);
  const rMat=new THREE.SpriteMaterial({{map:rTex, transparent:true, blending:THREE.AdditiveBlending, depthWrite:false, rotation:i*(Math.PI/rayCount)}});
  const rSprite=new THREE.Sprite(rMat);
  rSprite.scale.set(scaleF*50, scaleF*3, 1);
  rays.push(rSprite);
  sunGroup.add(rSprite);
}}

/* ═══ 바닥면 ═══ */
const groundGeo = new THREE.PlaneGeometry(W_m*4, L_m*4, 1, 1);
const groundMat = new THREE.MeshStandardMaterial({{color:0x7ab068, roughness:0.85, metalness:0.0}});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x=-Math.PI/2;
ground.position.y=-0.02;
ground.receiveShadow=true;
scene.add(ground);

/* 콘크리트 바닥 (돔 하부) */
const padGeo = new THREE.PlaneGeometry(W_m*1.3, L_m*1.3);
const padMat = new THREE.MeshStandardMaterial({{color:0xc8c8c0, roughness:0.7}});
const pad = new THREE.Mesh(padGeo, padMat);
pad.rotation.x=-Math.PI/2;
pad.position.y=-0.01;
pad.receiveShadow=true;
scene.add(pad);

/* ═══ 돔 생성 (viewer_3d.py 검증 공식 + 해석적 법선) ═══ */
const domeResU=100, domeResV=100;
const a_half=W_m/2, b_half=L_m/2;

/* 돔 높이: z = H × √(1-(x/a)²) × √(1-(y/b)²) — 직사각 경계에 정렬 */
function domeZ(x, z) {{
  const rx=1-(x/a_half)*(x/a_half);
  const rz=1-(z/b_half)*(z/b_half);
  return (rx>0 && rz>0) ? H_m*Math.sqrt(rx)*Math.sqrt(rz) : 0;
}}

const domeGeo = new THREE.BufferGeometry();
const domeVerts=[], domeNorms=[], domeUvs=[], domeIndices=[], heatmapColors=[];

for(let j=0;j<=domeResV;j++) {{
  for(let i=0;i<=domeResU;i++) {{
    const u=i/domeResU, v=j/domeResV;
    const x=(u-0.5)*W_m;
    const z=(v-0.5)*L_m;
    const y=domeZ(x,z);
    domeVerts.push(x, y, z);

    /* 해석적 법선 (편미분 공식) */
    const rx=1-(x/a_half)*(x/a_half);
    const rz=1-(z/b_half)*(z/b_half);
    let nx_n=0, ny_n=1, nz_n=0;
    if(rx>0.001 && rz>0.001 && y>0.01) {{
      /* dY/dx = H * (-x/a²) / √(1-(x/a)²) × √(1-(z/b)²) */
      const dydx = H_m * (-x/(a_half*a_half)) / Math.sqrt(rx) * Math.sqrt(rz);
      /* dY/dz = H * √(1-(x/a)²) * (-z/b²) / √(1-(z/b)²) */
      const dydz = H_m * Math.sqrt(rx) * (-z/(b_half*b_half)) / Math.sqrt(rz);
      const nl = Math.sqrt(dydx*dydx + 1 + dydz*dydz);
      nx_n = -dydx/nl;
      ny_n = 1/nl;
      nz_n = -dydz/nl;
    }}
    domeNorms.push(nx_n, ny_n, nz_n);
    domeUvs.push(u,v);
    heatmapColors.push(0.95,0.95,0.92);
  }}
}}

/* 인덱스: 높이가 0인 면은 제외 (경계가 그리드 정렬이므로 깔끔) */
for(let j=0;j<domeResV;j++) {{
  for(let i=0;i<domeResU;i++) {{
    const a=j*(domeResU+1)+i, b=a+1, c=a+(domeResU+1), d=c+1;
    const y0=domeVerts[a*3+1], y1=domeVerts[b*3+1], y2=domeVerts[c*3+1], y3=domeVerts[d*3+1];
    /* 4개 꼭짓점 모두 0일 때만 제외 → 경계 면은 포함 */
    if(y0>0.001 || y1>0.001 || y2>0.001 || y3>0.001) {{
      domeIndices.push(a,b,d, a,d,c);
    }}
  }}
}}

domeGeo.setAttribute('position', new THREE.Float32BufferAttribute(domeVerts,3));
domeGeo.setAttribute('normal', new THREE.Float32BufferAttribute(domeNorms,3));
domeGeo.setAttribute('uv', new THREE.Float32BufferAttribute(domeUvs,2));
domeGeo.setAttribute('color', new THREE.Float32BufferAttribute(heatmapColors,3));
domeGeo.setIndex(domeIndices);
/* 분석적 법선을 그대로 사용 — computeVertexNormals 호출 금지 */

const domeMat = new THREE.MeshStandardMaterial({{
  vertexColors:true, transparent:true, opacity:0.92,
  roughness:0.3, metalness:0.05, side:THREE.DoubleSide,
  envMapIntensity:0.3, flatShading:false
}});
const domeMesh = new THREE.Mesh(domeGeo, domeMat);
domeMesh.castShadow=true;
domeMesh.receiveShadow=true;
scene.add(domeMesh);

/* 돔 와이어프레임 — 더 세밀한 간격 */
const wireGeo = new THREE.WireframeGeometry(domeGeo);
const wireMat = new THREE.LineBasicMaterial({{color:0x5588aa, transparent:true, opacity:0.08}});
scene.add(wireframe);

/* 그라운드 그리드 */
const gridHelper = new THREE.GridHelper(Math.max(W_m,L_m)*2, 20, 0xaabbaa, 0xccddcc);
gridHelper.visible=false;
scene.add(gridHelper);

/* 태양 경로 라인 */
let sunPathLine=null;

/* ═══ 범례 그리기 ═══ */
function drawLegend() {{
  const c=document.getElementById('legend-canvas');
  const ctx=c.getContext('2d');
  const grd=ctx.createLinearGradient(0,0,200,0);
  grd.addColorStop(0,'#e2e8f0');
  grd.addColorStop(0.2,'#93c5fd');
  grd.addColorStop(0.4,'#4ade80');
  grd.addColorStop(0.6,'#facc15');
  grd.addColorStop(0.8,'#f97316');
  grd.addColorStop(1,'#ef4444');
  ctx.fillStyle=grd;
  ctx.fillRect(0,0,200,14);
}}
drawLegend();

/* ═══ 히트맵 색상 ═══ */
function irradianceToColor(val, maxVal) {{
  const t=Math.max(0,Math.min(1, val/maxVal));
  let r,g,b;
  if(t<0.15) {{
    const s=t/0.15;
    r=0.90-s*0.10; g=0.92-s*0.10; b=0.94+s*0.05;
  }} else if(t<0.35) {{
    const s=(t-0.15)/0.2;
    r=0.80-s*0.52; g=0.82-s*0.05; b=0.99-s*0.64;
  }} else if(t<0.55) {{
    const s=(t-0.35)/0.2;
    r=0.28+s*0.70; g=0.77+s*0.03; b=0.35-s*0.20;
  }} else if(t<0.75) {{
    const s=(t-0.55)/0.2;
    r=0.98; g=0.80-s*0.28; b=0.15-s*0.05;
  }} else {{
    const s=(t-0.75)/0.25;
    r=0.98-s*0.05; g=0.52-s*0.28; b=0.10+s*0.05;
  }}
  return [r,g,b];
}}

/* ═══ 태양 위치 업데이트 ═══ */
function updateSolar() {{
  lat=parseFloat(document.getElementById('inp-lat').value)||37.5665;
  lng=parseFloat(document.getElementById('inp-lng').value)||126.978;
  tzOff=parseInt(document.getElementById('inp-tz').value)||9;
  curYear=parseInt(document.getElementById('inp-year').value)||2026;
  curMonth=parseInt(document.getElementById('inp-month').value)||6;
  curDay=parseInt(document.getElementById('inp-day').value)||21;
  curHour=parseFloat(document.getElementById('s-hour').value)||12;

  const sp=SolarCalc.solarPosition(curYear,curMonth,curDay,curHour,tzOff);
  const ss=SolarCalc.sunriseSunset(curYear,curMonth,curDay,tzOff);
  const dni=SolarCalc.directNormalIrradiance(sp.altitude);
  const ghi=SolarCalc.globalHorizontalIrradiance(sp.altitude,dni);

  /* UI */
  document.getElementById('si-altitude').textContent=sp.altitude.toFixed(1)+'°';
  document.getElementById('si-azimuth').textContent=sp.azimuth.toFixed(1)+'°';
  document.getElementById('si-dni').textContent=dni.toFixed(0)+' W/m²';
  if(ss.sunrise!==null) {{ const rH=Math.floor(ss.sunrise),rM=Math.round((ss.sunrise%1)*60); document.getElementById('si-sunrise').textContent=(''+rH).padStart(2,'0')+':'+(''+rM).padStart(2,'0'); }}
  else document.getElementById('si-sunrise').textContent='--:--';
  if(ss.sunset!==null) {{ const sH=Math.floor(ss.sunset),sM=Math.round((ss.sunset%1)*60); document.getElementById('si-sunset').textContent=(''+sH).padStart(2,'0')+':'+(''+sM).padStart(2,'0'); }}
  else document.getElementById('si-sunset').textContent='--:--';
  if(ss.sunrise!==null&&ss.sunset!==null) document.getElementById('si-daylen').textContent=(ss.sunset-ss.sunrise).toFixed(1)+' h';
  else document.getElementById('si-daylen').textContent='-- h';

  /* 하늘 */
  updateSkyColor(sp.altitude);

  /* 조명 — 부드러운 전환 (altitude -5°~5° 구간 보간) */
  const sunDist=shadowRange*2;
  const altRad=sp.altitude*DEG, azRad=sp.azimuth*DEG;

  /* 일출/일몰 전환 팩터: -5°에서 0, +5°에서 1 (부드러운 보간) */
  const twilightFactor=Math.max(0, Math.min(1, (sp.altitude+5)/10));
  /* smoothstep 적용 */
  const tf=twilightFactor*twilightFactor*(3-2*twilightFactor);

  const sx=-sunDist*Math.cos(altRad)*Math.sin(azRad);
  const sy=sunDist*Math.max(0.01, Math.sin(Math.max(0,sp.altitude)*DEG));
  const sz=-sunDist*Math.cos(altRad)*Math.cos(azRad);
  sunLight.position.set(sx,sy,sz);
  sunLight.target.position.set(0,0,0);
  sunLight.visible=tf>0.01;

  const warmth=Math.max(0,Math.min(1,sp.altitude/50));
  const sunColor=new THREE.Color().setHSL(0.12-warmth*0.03, 0.85, 0.6+warmth*0.35);
  sunLight.color=sunColor;
  sunLight.intensity=tf*(1.0+sp.altitude/90*1.5);
  ambientLight.intensity=0.12+tf*0.45;
  hemiLight.intensity=0.08+tf*0.45;

  /* 태양 비주얼 (부드러운 페이드) */
  const sunVisualDist=sunDist*0.45;
  sunGroup.position.set(
    -sunVisualDist*Math.cos(altRad)*Math.sin(azRad),
    sunVisualDist*Math.max(0, Math.sin(Math.max(0,sp.altitude)*DEG)),
    -sunVisualDist*Math.cos(altRad)*Math.cos(azRad)
  );
  sunGroup.visible=showSunGlow && tf>0.01;
  sunCoreMat.color=sunColor;
  sunCoreMat.opacity=tf;
  rays.forEach((r,i)=>{{ r.material.rotation=i*(Math.PI/rayCount)+performance.now()*0.0001; r.material.opacity=tf*(0.15+warmth*0.15); }});
  glowInner.material.opacity=tf*(0.6+warmth*0.3);
  glowMid.material.opacity=tf*(0.3+warmth*0.2);
  glowOuter.material.opacity=tf*(0.1+warmth*0.1);
  glowHaze.material.opacity=tf*0.06;

  updateHeatmap(sp, dni);
  updateResults(sp, ss, dni, ghi);
  if(showSunpath) updateSunPath();

  const hh=Math.floor(curHour), mm=Math.round((curHour%1)*60);
  const timeStr=(''+hh).padStart(2,'0')+':'+(''+mm).padStart(2,'0');
  document.getElementById('play-time').textContent=timeStr;
  document.getElementById('v-hour').textContent=timeStr;
  document.getElementById('progress-fill').style.width=(curHour/24*100)+'%';
}}

/* ═══ 히트맵 + 돔 명암 ═══ */
function updateHeatmap(sp, maxDNI) {{
  const colors=domeGeo.getAttribute('color');
  const positions=domeGeo.getAttribute('position');
  const normals=domeGeo.getAttribute('normal');
  const count=positions.count;
  const altRad=sp.altitude*DEG, azRad=sp.azimuth*DEG;
  const sunDir=new THREE.Vector3(
    -Math.cos(altRad)*Math.sin(azRad), Math.sin(altRad), -Math.cos(altRad)*Math.cos(azRad)
  ).normalize();

  /* twilight 보간: -5°~+5° 구간 부드러운 전환 */
  const htf=Math.max(0,Math.min(1,(sp.altitude+5)/10));
  const htfs=htf*htf*(3-2*htf); /* smoothstep */

  for(let i=0;i<count;i++) {{
    const nx=normals.getX(i), ny=normals.getY(i), nz=normals.getZ(i);
    const py=positions.getY(i);
    if(py<0.01){{ colors.setXYZ(i,0.88,0.90,0.88); continue; }}
    if(htfs<0.01){{ colors.setXYZ(i,0.15,0.18,0.25); continue; }}
    const cosInc=nx*sunDir.x+ny*sunDir.y+nz*sunDir.z;

    /* 야간 색상 (부드러운 블렌딩용) */
    const nightR=0.15, nightG=0.18, nightB=0.25;

    if(showHeatmap) {{
      let fr,fg,fb;
      if(cosInc<=0) {{
        const shade=0.35+py/(H_m*2)*0.15;
        fr=shade*0.75; fg=shade*0.78; fb=shade*0.90;
      }} else {{
        const irr=maxDNI*cosInc;
        const [cr,cg,cb]=irradianceToColor(irr, 1000);
        const blend=heatmapIntensity;
        const litBase=0.6+cosInc*0.4;
        fr=cr*blend+litBase*(1-blend); fg=cg*blend+litBase*(1-blend); fb=cb*blend+litBase*(1-blend);
      }}
      /* twilight 보간으로 야간↔주간 부드럽게 전환 */
      colors.setXYZ(i, nightR*(1-htfs)+fr*htfs, nightG*(1-htfs)+fg*htfs, nightB*(1-htfs)+fb*htfs);
    }} else {{
      let fr,fg,fb;
      if(cosInc<=0) {{ fr=0.45; fg=0.47; fb=0.55; }}
      else {{ const lit=0.6+cosInc*0.35; fr=lit*0.98; fg=lit*0.96; fb=lit*0.90; }}
      colors.setXYZ(i, nightR*(1-htfs)+fr*htfs, nightG*(1-htfs)+fg*htfs, nightB*(1-htfs)+fb*htfs);
    }}
  }}
  colors.needsUpdate=true;
}}

/* ═══ 결과 패널 ═══ */
function updateResults(sp, ss, dni, ghi) {{
  let dailyGHI=0,dailyDNI=0,dailyDHI=0,peakGHI=0;
  for(let h=0;h<24;h+=0.25) {{
    const p=SolarCalc.solarPosition(curYear,curMonth,curDay,h,tzOff);
    if(p.altitude<=0)continue;
    const d=SolarCalc.directNormalIrradiance(p.altitude);
    const g=SolarCalc.globalHorizontalIrradiance(p.altitude,d);
    dailyGHI+=g*0.25; dailyDNI+=d*0.25; dailyDHI+=Math.max(0,g-d*Math.sin(p.altitude*DEG))*0.25;
    if(g>peakGHI)peakGHI=g;
  }}
  document.getElementById('r-ghi').innerHTML=(dailyGHI/1000).toFixed(2)+'<span class="u">kWh/m²</span>';
  document.getElementById('r-dni').innerHTML=(dailyDNI/1000).toFixed(2)+'<span class="u">kWh/m²</span>';
  document.getElementById('r-dhi').innerHTML=(dailyDHI/1000).toFixed(2)+'<span class="u">kWh/m²</span>';
  document.getElementById('r-peak').innerHTML=peakGHI.toFixed(0)+'<span class="u">W/m²</span>';

  const approxArea=Math.PI*(W_m/2)*(L_m/2)*1.3;
  document.getElementById('r-area').innerHTML=approxArea.toFixed(0)+'<span class="u">m²</span>';

  if(sp.altitude>0) {{
    const normals=domeGeo.getAttribute('normal'), positions=domeGeo.getAttribute('position');
    let sunCount=0,totalCount=0,angleSum=0;
    const sunDir=new THREE.Vector3(-Math.cos(sp.altitude*DEG)*Math.sin(sp.azimuth*DEG),Math.sin(sp.altitude*DEG),-Math.cos(sp.altitude*DEG)*Math.cos(sp.azimuth*DEG)).normalize();
    for(let i=0;i<normals.count;i++) {{
      if(positions.getY(i)<0.01)continue;
      totalCount++;
      const dot=normals.getX(i)*sunDir.x+normals.getY(i)*sunDir.y+normals.getZ(i)*sunDir.z;
      if(dot>0){{ sunCount++; angleSum+=Math.acos(Math.min(1,dot))*RAD; }}
    }}
    const sunRatio=totalCount>0?(sunCount/totalCount*100):0;
    document.getElementById('r-sun-ratio').innerHTML=sunRatio.toFixed(1)+'<span class="u">%</span>';
    document.getElementById('r-shade-ratio').innerHTML=(100-sunRatio).toFixed(1)+'<span class="u">%</span>';
    document.getElementById('r-avg-angle').innerHTML=(sunCount>0?(angleSum/sunCount):0).toFixed(1)+'<span class="u">°</span>';
    const shadowLen=H_m/Math.tan(Math.max(0.01,sp.altitude*DEG));
    document.getElementById('r-shadow-len').innerHTML=shadowLen.toFixed(1)+'<span class="u">m</span>';
    document.getElementById('r-shadow-dir').innerHTML=((sp.azimuth+180)%360).toFixed(1)+'<span class="u">°</span>';
    document.getElementById('r-shadow-area').innerHTML=(approxArea*0.7*Math.cos(sp.altitude*DEG)).toFixed(0)+'<span class="u">m²</span>';
  }} else {{
    ['r-sun-ratio','r-shade-ratio','r-avg-angle','r-shadow-len','r-shadow-dir','r-shadow-area'].forEach(id=>{{
      const el=document.getElementById(id);
      if(id==='r-shade-ratio') el.innerHTML='100<span class="u">%</span>';
      else if(id==='r-sun-ratio') el.innerHTML='0<span class="u">%</span>';
      else el.innerHTML='--<span class="u">'+(id.includes('len')?'m':id.includes('dir')?'°':'m²')+'</span>';
    }});
  }}
  const totalEnergy=dailyGHI/1000*approxArea*0.5;
  document.getElementById('r-total-energy').innerHTML=totalEnergy.toFixed(1)+'<span class="u">kWh</span>';
  document.getElementById('r-monthly').innerHTML=(totalEnergy*30/1000).toFixed(2)+'<span class="u">MWh</span>';
  document.getElementById('r-yearly').innerHTML=(totalEnergy*365/1000).toFixed(1)+'<span class="u">MWh</span>';
}}

/* ═══ 태양 경로 ═══ */
function updateSunPath() {{
  if(sunPathLine) scene.remove(sunPathLine);
  const pts=[], pathDist=shadowRange*0.8;
  for(let h=0;h<24;h+=0.25) {{
    const p=SolarCalc.solarPosition(curYear,curMonth,curDay,h,tzOff);
    if(p.altitude<-5) continue;
    const altR=Math.max(0,p.altitude)*DEG, azR=p.azimuth*DEG;
    pts.push(new THREE.Vector3(-pathDist*Math.cos(altR)*Math.sin(azR),pathDist*Math.sin(altR),-pathDist*Math.cos(altR)*Math.cos(azR)));
  }}
  if(pts.length>1) {{
    const geo=new THREE.BufferGeometry().setFromPoints(pts);
    sunPathLine=new THREE.Line(geo, new THREE.LineDashedMaterial({{color:0xfbbf24,dashSize:scaleF*2,gapSize:scaleF*1,transparent:true,opacity:0.6}}));
    sunPathLine.computeLineDistances();
    scene.add(sunPathLine);
  }}
}}

/* ═══ UI 함수들 ═══ */
function openTab(id) {{
  document.querySelectorAll('.tp').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  event.currentTarget.classList.add('on');
}}

function onHourChange() {{ curHour=parseFloat(document.getElementById('s-hour').value); updateSolar(); }}

function searchAddress() {{
  const addr=document.getElementById('addr-input').value.trim();
  if(!addr) return;
  document.getElementById('addr-search-btn').textContent='🔄 검색 중...';
  fetch('https://nominatim.openstreetmap.org/search?format=json&q='+encodeURIComponent(addr)+'&limit=1',{{headers:{{'Accept-Language':'ko'}}}})
  .then(r=>r.json()).then(data=>{{
    if(data&&data.length>0) {{
      lat=parseFloat(data[0].lat); lng=parseFloat(data[0].lon);
      document.getElementById('inp-lat').value=lat.toFixed(4);
      document.getElementById('inp-lng').value=lng.toFixed(4);
      document.getElementById('disp-lat').textContent=lat.toFixed(4);
      document.getElementById('disp-lng').textContent=lng.toFixed(4);
      document.getElementById('addr-search-btn').textContent='✅ '+data[0].display_name.substring(0,40);
      updateSolar();
    }} else document.getElementById('addr-search-btn').textContent='❌ 결과 없음';
  }}).catch(()=>document.getElementById('addr-search-btn').textContent='❌ 네트워크 오류');
}}

function updateFromManual() {{
  lat=parseFloat(document.getElementById('inp-lat').value)||37.5665;
  lng=parseFloat(document.getElementById('inp-lng').value)||126.978;
  document.getElementById('disp-lat').textContent=lat.toFixed(4);
  document.getElementById('disp-lng').textContent=lng.toFixed(4);
  updateSolar();
}}

function setCity(la,ln,name,el) {{
  lat=la; lng=ln;
  document.getElementById('inp-lat').value=la.toFixed(4);
  document.getElementById('inp-lng').value=ln.toFixed(4);
  document.getElementById('disp-lat').textContent=la.toFixed(4);
  document.getElementById('disp-lng').textContent=ln.toFixed(4);
  document.querySelectorAll('#t-location .mbtn').forEach(b=>b.classList.remove('on'));
  el.classList.add('on');
  updateSolar();
}}

function setSeason(season,el) {{
  const seasons={{spring:{{m:3,d:21}},summer:{{m:6,d:21}},autumn:{{m:9,d:23}},winter:{{m:12,d:22}}}};
  const s=seasons[season];
  document.getElementById('inp-month').value=s.m;
  document.getElementById('inp-day').value=s.d;
  document.querySelectorAll('#t-time .mode-row:first-of-type .mbtn').forEach(b=>b.classList.remove('on'));
  el.classList.add('on');
  updateSolar();
}}

function setSpecialDay(day) {{
  const days={{summer_solstice:{{m:6,d:21}},winter_solstice:{{m:12,d:22}},vernal_equinox:{{m:3,d:20}},autumnal_equinox:{{m:9,d:23}}}};
  const d=days[day];
  document.getElementById('inp-month').value=d.m;
  document.getElementById('inp-day').value=d.d;
  updateSolar();
}}

function togglePlay() {{
  isPlaying=!isPlaying;
  const btn=document.getElementById('btn-play');
  if(isPlaying){{ btn.textContent='⏸'; btn.classList.add('playing'); startPlayback(); }}
  else{{ btn.textContent='▶'; btn.classList.remove('playing'); if(playInterval) clearInterval(playInterval); }}
}}
function startPlayback() {{
  if(playInterval) clearInterval(playInterval);
  const mode=document.getElementById('play-mode').value;
  playInterval=setInterval(()=>{{
    if(!isPlaying)return;
    if(mode==='day'){{ curHour+=0.25*playSpeed; if(curHour>=24)curHour=0; document.getElementById('s-hour').value=curHour; }}
    else{{ curMonth+=1; if(curMonth>12){{curMonth=1;curYear++;document.getElementById('inp-year').value=curYear;}} document.getElementById('inp-month').value=curMonth; curHour=12; document.getElementById('s-hour').value=12; }}
    onHourChange();
  }}, mode==='day'?100:800);
}}
function updatePlaySpeed(){{ playSpeed=parseFloat(document.getElementById('play-speed').value); if(isPlaying) startPlayback(); }}
function seekProgress(e){{ const rect=document.getElementById('progress-bar').getBoundingClientRect(); curHour=(e.clientX-rect.left)/rect.width*24; document.getElementById('s-hour').value=curHour; onHourChange(); }}

function toggleVis(type,el) {{
  el.classList.toggle('on');
  if(type==='heatmap'){{ showHeatmap=el.classList.contains('on'); updateSolar(); }}
  else if(type==='shadow'){{ showShadow=el.classList.contains('on'); renderer.shadowMap.enabled=showShadow; ground.receiveShadow=showShadow; domeMesh.castShadow=showShadow; }}
  else if(type==='sunpath'){{ showSunpath=el.classList.contains('on'); if(showSunpath) updateSunPath(); else if(sunPathLine){{scene.remove(sunPathLine);sunPathLine=null;}} }}
  else if(type==='domewire'){{ showDomeWire=el.classList.contains('on'); wireframe.visible=showDomeWire; }}
  else if(type==='groundgrid'){{ showGroundGrid=el.classList.contains('on'); gridHelper.visible=showGroundGrid; }}
  else if(type==='sunglow'){{ showSunGlow=el.classList.contains('on'); sunGroup.visible=showSunGlow; }}
}}

function updateHeatmapOpacity() {{
  const v=parseInt(document.getElementById('s-hm-opacity').value);
  document.getElementById('v-hm-opacity').textContent=v;
  heatmapIntensity=v/100; updateSolar();
}}

function setView(view,el) {{
  document.querySelectorAll('.view-row .tb').forEach(b=>b.classList.remove('on'));
  el.classList.add('on');
  if(view==='perspective'){{ camTheta=Math.PI/4; camPhi=Math.PI/4; }}
  else if(view==='top'){{ camTheta=0; camPhi=0.01; }}
  else if(view==='south'){{ camTheta=0; camPhi=Math.PI/3; }}
  else if(view==='east'){{ camTheta=Math.PI/2; camPhi=Math.PI/3; }}
  updateCamera();
}}

/* ═══ 다운로드 ═══ */
function downloadCSV() {{
  let csv='Hour,Altitude(deg),Azimuth(deg),DNI(W/m2),GHI(W/m2),DHI(W/m2)\\n';
  for(let h=0;h<24;h+=0.25) {{
    const p=SolarCalc.solarPosition(curYear,curMonth,curDay,h,tzOff);
    const d=SolarCalc.directNormalIrradiance(p.altitude);
    const g=SolarCalc.globalHorizontalIrradiance(p.altitude,d);
    const dhi=Math.max(0,g-d*Math.sin(Math.max(0,p.altitude)*DEG));
    csv+=(''+Math.floor(h)).padStart(2,'0')+':'+(''+Math.round((h%1)*60)).padStart(2,'0')+','+p.altitude.toFixed(2)+','+p.azimuth.toFixed(2)+','+d.toFixed(1)+','+g.toFixed(1)+','+dhi.toFixed(1)+'\\n';
  }}
  csv+='\\n# Location: Lat='+lat.toFixed(4)+' Lng='+lng.toFixed(4);
  csv+='\\n# Date: '+curYear+'-'+(''+curMonth).padStart(2,'0')+'-'+(''+curDay).padStart(2,'0');
  csv+='\\n# Dome: '+W+'mm x '+L+'mm x '+H+'mm';
  csv+='\\n# Generated by OzoMeta AirDome Solar Simulator';
  const blob=new Blob([csv],{{type:'text/csv;charset=utf-8;'}});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='AirDome_Solar_'+curYear+(''+curMonth).padStart(2,'0')+(''+curDay).padStart(2,'0')+'.csv'; a.click();
}}

function downloadPNG() {{
  renderer.render(scene,camera);
  const a=document.createElement('a'); a.href=renderer.domElement.toDataURL('image/png');
  a.download='AirDome_Solar_Screenshot_'+curYear+(''+curMonth).padStart(2,'0')+(''+curDay).padStart(2,'0')+'.png'; a.click();
}}

/* ═══ 렌더 루프 ═══ */
function animate() {{
  requestAnimationFrame(animate);
  if(sunGroup.visible) rays.forEach((r,i)=>{{ r.material.rotation=i*(Math.PI/rayCount)+performance.now()*0.00008; }});
  renderer.render(scene,camera);
}}
animate();
updateSolar();
</script>
</body>
</html>"""
