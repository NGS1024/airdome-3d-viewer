"""
╔══════════════════════════════════════════════════════════╗
║       AIR DOME 3D Simulator - 에어돔 구조 시뮬레이터       ║
║                    OzoMeta Architecture                  ║
╚══════════════════════════════════════════════════════════╝

사용법:
  1. 프로그램 실행 → PDF 도면 폴더 선택
  2. PDF 목록에서 도면 확인
  3. 파라미터 입력 (폭, 길이, 높이, 돔 타입)
  4. [3D 미리보기] 클릭 → 브라우저에서 3D 돔 확인
  5. [STEP 내보내기] 클릭 → CATIA용 STP 파일 생성

필요 라이브러리:
  - tkinter (Python 기본 포함)
  - 추가 설치: pip install PyMuPDF (PDF 텍스트 추출, 선택사항)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import json
import math
import webbrowser
import struct
import tempfile
import datetime
import threading
from pathlib import Path

# ── 라이브러리 자동 설치 및 임포트 ──
import subprocess, sys, shutil

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


# ============================================================
# 3D Viewer HTML Template (Three.js)
# ============================================================
def generate_viewer_html(params):
    """Three.js 기반 3D 돔 뷰어 HTML 생성"""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>AIR DOME 3D Simulator - {{W}}x{{L}}x{{H}}mm</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#c8dce8; font-family:'Segoe UI',sans-serif; overflow:hidden; }}
  #info {{ position:absolute; top:10px; left:10px; color:#e0e0e0; z-index:10;
           background:rgba(0,0,0,0.6); padding:12px; border-radius:8px; font-size:13px; }}
  #info h2 {{ font-size:16px; margin-bottom:4px; }}
  #info .sub {{ color:#888; font-size:11px; }}
  #controls {{ position:absolute; top:10px; right:10px; z-index:10;
              background:rgba(0,0,0,0.6); padding:10px; border-radius:8px; }}
  #controls button {{ display:block; width:100%; margin:3px 0; padding:6px 12px;
    background:rgba(255,255,255,0.08); border:1px solid #555; border-radius:4px;
    color:#ccc; cursor:pointer; font-size:11px; }}
  #controls button:hover {{ background:rgba(79,195,247,0.2); border-color:#4fc3f7; color:#4fc3f7; }}
  #controls button.active {{ background:rgba(79,195,247,0.2); border-color:#4fc3f7; color:#4fc3f7; font-weight:bold; }}
  #legend {{ position:absolute; bottom:12px; left:12px; z-index:10;
    background:rgba(0,0,0,0.7); padding:12px; border-radius:8px;
    font-size:11px; color:#ccc; line-height:1.8; }}
  #legend b {{ color:#fff; }}
  .dim {{ display:inline-block; width:12px; height:3px; margin-right:6px; vertical-align:middle; }}
  #profile {{ position:absolute; bottom:12px; right:12px; z-index:10;
    background:rgba(0,0,0,0.7); padding:12px; border-radius:8px;
    font-size:11px; color:#ccc; line-height:1.8; max-width:220px; }}
  #profile .eq {{ color:#4fc3f7; margin-top:4px; }}
</style>
</head>
<body>
<div id="info">
  <h2>{params.get('project_name','Air Dome')} - 3D Preview</h2>
  <div class="sub">{params.get('width',0):,.0f} x {params.get('length',0):,.0f} x {params.get('height',0):,.0f} mm | {params.get('dome_type','Rectangular')}</div>
  <div class="sub" style="color:#4fc3f7; margin-top:2px;">Drag to rotate | Scroll to zoom</div>
</div>
<div id="controls">
  <div style="color:#888; font-size:10px; margin-bottom:4px;">VIEWS</div>
  <button onclick="setView('perspective')">3D Perspective</button>
  <button onclick="setView('top')">Top (평면)</button>
  <button onclick="setView('east')">East (단변)</button>
  <button onclick="setView('south')">South (장변)</button>
  <button onclick="setView('section')">Cross Section</button>
  <div style="color:#888; font-size:10px; margin:8px 0 4px;">LAYERS</div>
  <button id="btn_membrane" class="active" onclick="toggle('membrane')">Membrane</button>
  <button id="btn_cable" class="active" onclick="toggle('cable')">Cable Net</button>
  <button id="btn_wireframe" onclick="toggle('wireframe')">Wireframe</button>
  <button id="btn_foundation" class="active" onclick="toggle('foundation')">Foundation</button>
  <button id="btn_dims" class="active" onclick="toggle('dims')">Dimensions</button>
</div>
<div id="legend">
  <b>Key Dimensions (mm)</b><br>
  <span class="dim" style="background:#ff4444"></span>Width: <b style="color:#ff6666">{params.get('width',0):,.0f}</b><br>
  <span class="dim" style="background:#44ff44"></span>Length: <b style="color:#66ff66">{params.get('length',0):,.0f}</b><br>
  <span class="dim" style="background:#4488ff"></span>Height: <b style="color:#6699ff">{params.get('height',0):,.0f}</b>
</div>
<div id="profile">
  <b>Profile Analysis</b><br>
  Type: Semi-Ellipsoidal<br>
  Half-span (a): {params.get('width',0)/2:,.0f} mm<br>
  Half-length (b): {params.get('length',0)/2:,.0f} mm<br>
  Crown height (c): {params.get('height',0):,.0f} mm<br>
  <div class="eq">z = H × √(1-(x/a)²) × √(1-(y/b)²)</div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const W = {params.get('width',43282)};
const L = {params.get('length',68580)};
const H = {params.get('height',15850)};
const S = 0.001;
const a = W/2*S, b = L/2*S, Hs = H*S;

function domeZ(x,y) {{
  let rx=1-(x/a)**2, ry=1-(y/b)**2;
  return (rx>0&&ry>0) ? Hs*Math.sqrt(rx)*Math.sqrt(ry) : 0;
}}

// Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xc8dce8);
scene.fog = new THREE.Fog(0xc8dce8, 120, 300);
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 500);
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lights
scene.add(new THREE.AmbientLight(0x8899aa, 0.8));
const dl = new THREE.DirectionalLight(0xffffff, 1.0);
dl.position.set(30,50,20); dl.castShadow=true; scene.add(dl);
scene.add(new THREE.DirectionalLight(0xffeedd, 0.5).translateX(-20).translateY(30).translateZ(-30));

// Ground
const gnd = new THREE.Mesh(new THREE.PlaneGeometry(200,200), new THREE.MeshPhongMaterial({{color:0x5a8a50}}));
gnd.rotation.x=-Math.PI/2; gnd.position.y=-0.05; gnd.receiveShadow=true; scene.add(gnd);
const grid = new THREE.GridHelper(200,40,0x6a9a60,0x4a7a40); grid.position.y=-0.02; scene.add(grid);

// Dome mesh
const resU=80, resV=80;
const domeGeo = new THREE.BufferGeometry();
const verts=[], norms=[], uvs=[], idx=[];
for(let j=0;j<=resV;j++) for(let i=0;i<=resU;i++) {{
  let u=i/resU, v=j/resV;
  let x=(u-0.5)*2*a, y=(v-0.5)*2*b, z=domeZ(x,y);
  verts.push(x,z,y);
  let dx=0.01, dy=0.01;
  let nx=(domeZ(x-dx,y)-domeZ(x+dx,y))/(2*dx);
  let ny=(domeZ(x,y-dy)-domeZ(x,y+dy))/(2*dy);
  let nl=Math.sqrt(nx*nx+ny*ny+1);
  norms.push(nx/nl,1/nl,ny/nl); uvs.push(u,v);
}}
for(let j=0;j<resV;j++) for(let i=0;i<resU;i++) {{
  let a0=j*(resU+1)+i, b0=a0+1, c0=a0+resU+1, d0=c0+1;
  idx.push(a0,b0,d0,a0,d0,c0);
}}
domeGeo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));
domeGeo.setAttribute('normal',new THREE.Float32BufferAttribute(norms,3));
domeGeo.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
domeGeo.setIndex(idx);

const layers = {{}};
layers.membrane = new THREE.Mesh(domeGeo, new THREE.MeshPhongMaterial({{
  color:0xf5f0e8, transparent:true, opacity:0.92, side:2, shininess:60, specular:0x444444
}}));
layers.membrane.castShadow=true; scene.add(layers.membrane);

layers.wireframe = new THREE.Mesh(domeGeo, new THREE.MeshBasicMaterial({{
  color:0x666666, wireframe:true, transparent:true, opacity:0.3
}}));
layers.wireframe.visible=false; scene.add(layers.wireframe);

// Cable net
layers.cable = new THREE.Group(); scene.add(layers.cable);
const cMat = new THREE.LineBasicMaterial({{color:0x555555}});
const sp = {params.get('cable_spacing', 3600)}*S;
for(let d=0;d<2;d++) {{
  for(let off=-b-a; off<=b+a; off+=sp) {{
    const pts=[];
    for(let t=0;t<=60;t++) {{
      let s=t/60, x=-a+s*2*a, y=d===0?(x+off):(-x+off);
      if(y>=-b&&y<=b) {{ let z=domeZ(x,y); if(z>0.01) pts.push(new THREE.Vector3(x,z,y)); }}
    }}
    if(pts.length>2) layers.cable.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),cMat));
  }}
}}

// Foundation
layers.foundation = new THREE.Group(); scene.add(layers.foundation);
const fMat = new THREE.MeshPhongMaterial({{color:0x999999,transparent:true,opacity:0.7}});
const fw=0.3, fd=0.15;
[[-a-fw,-b-fw,2*a+2*fw,fw],[-a-fw,b,2*a+2*fw,fw],[-a-fw,-b,fw,2*b],[ a,-b,fw,2*b]].forEach(r=>{{
  const g=new THREE.BoxGeometry(r[2],fd,r[3]);
  const m=new THREE.Mesh(g,fMat);
  m.position.set(r[0]+r[2]/2,-fd/2,r[1]+r[3]/2); layers.foundation.add(m);
}});

// Dimension lines
layers.dims = new THREE.Group(); scene.add(layers.dims);
function dimLine(p1,p2,col) {{
  const g=new THREE.BufferGeometry().setFromPoints([p1,p2]);
  layers.dims.add(new THREE.Line(g,new THREE.LineBasicMaterial({{color:col,linewidth:2}})));
  [p1,p2].forEach(p=>{{
    const s=new THREE.Mesh(new THREE.SphereGeometry(0.15,8,8),new THREE.MeshBasicMaterial({{color:col}}));
    s.position.copy(p); layers.dims.add(s);
  }});
}}
dimLine(new THREE.Vector3(-a,0,-b-3),new THREE.Vector3(a,0,-b-3),0xff4444);
dimLine(new THREE.Vector3(-a-3,0,-b),new THREE.Vector3(-a-3,0,b),0x44ff44);
dimLine(new THREE.Vector3(a+2,0,0),new THREE.Vector3(a+2,Hs,0),0x4488ff);

// Camera control
let rot={{x:0.3,y:-0.5}}, zoom=60, drag=false, mx=0, my=0;
const cv=renderer.domElement;
cv.addEventListener('mousedown',e=>{{drag=true;mx=e.clientX;my=e.clientY;}});
cv.addEventListener('mousemove',e=>{{
  if(!drag)return;
  rot.y-=(e.clientX-mx)*0.005;
  rot.x=Math.max(-0.1,Math.min(1.4,rot.x+(e.clientY-my)*0.005));
  mx=e.clientX;my=e.clientY;
}});
cv.addEventListener('mouseup',()=>drag=false);
cv.addEventListener('mouseleave',()=>drag=false);
cv.addEventListener('wheel',e=>{{zoom=Math.max(15,Math.min(150,zoom+e.deltaY*0.05));}});

window.setView = function(v) {{
  if(v==='top') {{ rot={{x:1.4,y:0}}; zoom=65; }}
  else if(v==='east') {{ rot={{x:0.15,y:0}}; zoom=50; }}
  else if(v==='south') {{ rot={{x:0.15,y:Math.PI/2}}; zoom=70; }}
  else if(v==='section') {{ rot={{x:0.1,y:0}}; zoom=40; }}
  else {{ rot={{x:0.3,y:-0.5}}; zoom=60; }}
}};

window.toggle = function(name) {{
  if(layers[name]) {{
    layers[name].visible = !layers[name].visible;
    const btn = document.getElementById('btn_'+name);
    if(btn) btn.classList.toggle('active');
  }}
}};

function animate() {{
  requestAnimationFrame(animate);
  camera.position.set(
    zoom*Math.cos(rot.x)*Math.sin(rot.y),
    zoom*Math.sin(rot.x)+10,
    zoom*Math.cos(rot.x)*Math.cos(rot.y)
  );
  camera.lookAt(0,Hs*0.3,0);
  renderer.render(scene,camera);
}}
animate();

window.addEventListener('resize',()=>{{
  camera.aspect=innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);
}});
</script>
</body>
</html>"""


# ============================================================
# Simulation Viewer HTML Template (Three.js + Structural Analysis)
# ============================================================
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
  const idx={{'t-load':0,'t-layer':1,'t-mat':2}}[id]||0;
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

  const minSF=Math.min(mSFo,mSFiu,mSFil);
  const vd=document.getElementById('r-verdict');let ms=[];
  if(pInt<rqP)ms.push('<span class="sf-danger">❌ 내압 부족 — 최소 '+rqP.toFixed(0)+'Pa 필요</span>');
  if(mSFo<1.5)ms.push('<span class="sf-danger">❌ 외피막 SF='+mSFo.toFixed(2)+' 부족</span>');
  if(mSFiu<1.5)ms.push('<span class="sf-danger">❌ 내피(상) SF 부족</span>');
  if(mSFil<1.5)ms.push('<span class="sf-danger">❌ 내피(하) SF 부족</span>');
  if(minSF<3&&ms.length===0)ms.push('<span class="sf-warn">⚠ 주의 — SF='+minSF.toFixed(2)+' (권장 3.0+)</span>');
  if(ms.length===0)ms.push('<span class="sf-safe">✅ 전 층 안전 — SF='+minSF.toFixed(2)+'</span>');
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
  active:false, N:2800, trails:10, dt:0.10,
  pts:null, geo:null, mesh:null, trailGeo:[], trailMesh:[],
  init:function(){{
    // 파티클 점(Points)
    this.pts=new Float32Array(this.N*3);
    this.vel=new Float32Array(this.N*3);
    this.life=new Float32Array(this.N);
    this.cols=new Float32Array(this.N*3);
    this.sizes=new Float32Array(this.N);
    this.geo=new THREE.BufferGeometry();
    this.geo.setAttribute('position',new THREE.Float32BufferAttribute(this.pts,3));
    this.geo.setAttribute('color',new THREE.Float32BufferAttribute(this.cols,3));
    this.geo.setAttribute('size',new THREE.Float32BufferAttribute(this.sizes,1));
    // 포인트 머티리얼 (크기 감쇠 적용)
    const vsh=`attribute float size;attribute vec3 color;varying vec3 vc;
      void main(){{vc=color;vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_PointSize=size*(200.0/-mv.z);gl_Position=projectionMatrix*mv;}}`;
    const fsh=`varying vec3 vc;void main(){{float d=length(gl_PointCoord-0.5);
      if(d>0.5)discard;float a=smoothstep(0.5,0.2,d);
      gl_FragColor=vec4(vc,a*0.85);}}`;
    const mat=new THREE.ShaderMaterial({{vertexShader:vsh,fragmentShader:fsh,
      transparent:true,depthWrite:false,blending:THREE.AdditiveBlending}});
    this.mesh=new THREE.Points(this.geo,mat);
    this.mesh.visible=false;
    this.mesh.frustumCulled=false;
    scene.add(this.mesh);
    // 트레일 라인
    const tMat=new THREE.LineBasicMaterial({{color:0x38bdf8,transparent:true,opacity:0.22,blending:THREE.AdditiveBlending}});
    for(let t=0;t<this.trails;t++){{
      const tg=new THREE.BufferGeometry();
      const tp=new Float32Array(this.N/this.trails*3);
      tg.setAttribute('position',new THREE.Float32BufferAttribute(tp,3));
      const tm=new THREE.LineSegments(tg,tMat.clone());
      tm.visible=false;tm.frustumCulled=false;
      scene.add(tm);
      this.trailGeo.push(tg);this.trailMesh.push(tm);
    }}
    // 초기 배치
    for(let i=0;i<this.N;i++)this.respawn(i);
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
    return {{dx:Math.cos(rad)*vn, dz:Math.sin(rad)*vn, spd:spd, dir:dir}};
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
    let vx=fs.dx*8, vy=0, vz=fs.dz*8;
    // 원거리: 대기 경계층 프로파일
    if(R>=2.0){{
      const heightFactor=Math.min(1.3, 0.6+0.7*Math.pow(Math.max(y,0.1)/(Hs*2),0.2));
      vx*=heightFactor; vz*=heightFactor;
      const turb=0.2;
      vx+=Math.sin(x*0.5+z*0.3+performance.now()*0.0005)*turb;
      vz+=Math.cos(z*0.5+x*0.3+performance.now()*0.0007)*turb;
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
      // 후류(wake) 영역 - 풍하측 와류 (더 강하고 넓게)
      const windDot=rx*(fs.dx/Math.max(Math.abs(fs.dx)+Math.abs(fs.dz),0.01))
                    +rz*(fs.dz/Math.max(Math.abs(fs.dx)+Math.abs(fs.dz),0.01));
      if(windDot>0.2&&R>0.7&&R<2.0){{
        const wake=Math.min(1,(windDot-0.2)/0.4)*Math.max(0,1-(R-0.7)/1.3);
        // 와류 회전 (더 역동적)
        const t=performance.now()*0.001;
        vx+=Math.sin(t*2.5+z*4)*wake*4.5;
        vz+=Math.cos(t*2.5+x*4)*wake*4.5;
        vy+=Math.sin(t*3.5+x*2.5)*wake*2.5;
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
    // 대부분 돔 가까이에서 시작, 일부만 약간 먼곳에서
    const rng=Math.random();
    const farDist=rng<0.6 ? baseSpread*(1.2+Math.random()*0.8) :
                  rng<0.85 ? baseSpread*(2.0+Math.random()*0.8) :
                  baseSpread*(0.3+Math.random()*0.7);
    const sideSpread=baseSpread*1.8;
    const side=(Math.random()-0.5)*sideSpread;
    // 높이: 돔 표면과 상호작용하도록 낮은 층 비중 높임
    const hLayer=Math.random();
    const h=hLayer<0.6 ? (0.2+Math.random()*Hs*0.7) :
            hLayer<0.85 ? (Hs*0.3+Math.random()*Hs*1.0) :
            (Hs*1.0+Math.random()*Hs*0.6);
    this.pts[i3]  =-fs.dx*farDist+(-fs.dz)*side;
    this.pts[i3+1]=h;
    this.pts[i3+2]=-fs.dz*farDist+(fs.dx)*side;
    this.vel[i3]=fs.dx*6;this.vel[i3+1]=0;this.vel[i3+2]=fs.dz*6;
    this.life[i]=Math.random()*0.1;
    this.sizes[i]=0.15+Math.random()*0.3;
  }},
  // 속도→색상 (파란→초록→노랑→빨강)
  spdColor:function(spd,isWake){{
    if(isWake)return{{r:1,g:0.3,b:0.2}};
    const t=Math.min(1,spd/12);
    let r,g,b2;
    if(t<0.33){{r=0.2;g=0.5+t*1.5;b2=1;}}
    else if(t<0.66){{r=t*1.5;g=0.9;b2=1-t;}}
    else{{r=1;g=1.2-t;b2=0.2;}}
    return{{r:r,g:g,b:b2}};
  }},
  // 프레임 업데이트
  update:function(){{
    if(!this.active)return;
    const fs=this.freeStream();
    const pa=this.geo.getAttribute('position');
    const ca=this.geo.getAttribute('color');
    const sa=this.geo.getAttribute('size');
    const maxDist=Math.max(a,b)*3.5;
    for(let i=0;i<this.N;i++){{
      const i3=i*3;
      this.life[i]+=this.dt*0.06;
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
      if(dist>maxDist||this.pts[i3+1]>Hs*3||this.life[i]>1){{
        this.respawn(i);
        ca.setXYZ(i,0,0,0);sa.array[i]=0;continue;
      }}
      // 속도 크기로 색상
      const spd=Math.sqrt(v.x**2+v.y**2+v.z**2);
      const rx=px/a,rz=pz/b,R=Math.sqrt(rx*rx+rz*rz);
      const windDot=R>0.5?((rx*(fs.dx)+rz*(fs.dz))/(Math.sqrt(fs.dx**2+fs.dz**2+0.001)*R)):0;
      const isWake=windDot>0.3&&R>0.8&&R<2.0;
      const c=this.spdColor(spd,isWake);
      // 수명에 따른 페이드
      const alpha=this.life[i]<0.1?this.life[i]*10:
                  this.life[i]>0.8?(1-this.life[i])*5:1;
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
        if(this.life[i]>0&&this.life[i]<0.9&&this.life[i+1]>0){{
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
    if(on)for(let i=0;i<this.N;i++)this.respawn(i);
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
 's-thick-o','s-thick-i','s-str-o','s-str-i','s-elastic','s-cspace'].forEach(id=>{{
  document.getElementById(id).addEventListener('input',runSim);}});
runSim();
</script>
</body>
</html>"""



# ============================================================
# PDF Analyzer
# ============================================================
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
            # PyMuPDF로 이미지 변환 → pytesseract로 OCR
            if (is_image_pdf or len(all_text.strip()) < 20) and HAS_TESSERACT and HAS_FITZ:
                try:
                    ocr_text = ""
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        # 페이지를 200 DPI 이미지로 변환
                        mat = fitz.Matrix(200/72, 200/72)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")

                        # PIL Image로 변환 후 Tesseract OCR
                        img = Image.open(io.BytesIO(img_data))
                        ocr_result = pytesseract.image_to_string(img)
                        if ocr_result:
                            ocr_text += ocr_result + "\n"

                        pix = None
                        img = None

                    if len(ocr_text.strip()) > 10:
                        all_text = ocr_text  # OCR 결과로 교체

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
        # 건축 도면에서 단위 없이 소수점 3자리 = 미터 단위 관행
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
        # 예: 43,282  또는  15850  또는  68,580
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
        dome_words = ['dome', 'air dome', 'membrane', 'cable', 'inflation',
                      'PVDF', 'air-supported', 'broadwell', 'tennis', 'center',
                      'elevation', 'section', 'plan', 'detail',
                      '에어돔', '막구조', '단면', '입면', '평면']
        text_lower = text.lower()
        for kw in dome_words:
            if kw.lower() in text_lower:
                results['dome_keywords'].append(kw)

        return results


# ============================================================
# STEP Exporter
# ============================================================
class STEPExporter:
    """에어돔 3D 곡면을 STEP 파일로 내보내기 (지오메트리 분리 지원)

    CATIA Import 시 다음 4개 Body/Geometrical Set으로 분리됨:
      1. DomeSurface  — 돔 곡면 (B-Spline Surface, Open Shell)
      2. Foundation   — 매트 기초 (Closed Shell Solid, 6면 박스)
      3. CableNet     — 케이블넷 (Geometric Curve Set, Wire Body)
      4. GroundPlane  — 바닥 슬래브 (Flat Surface, Open Shell)
    """

    @staticmethod
    def export(filepath, width, length, height, nu=13, nv=19,
               cable_spacing=0, foundation_depth=500):
        """STEP AP214 내보내기 — 지오메트리 분리 버전

        Args:
            filepath: 저장 경로
            width: 돔 폭 (mm)
            length: 돔 길이 (mm)
            height: 돔 높이 (mm)
            nu, nv: B-Spline 제어점 수
            cable_spacing: 케이블 간격 (mm), 0이면 케이블 없음
            foundation_depth: 기초 깊이 (mm), 기본 500mm
        """
        a_val = width / 2
        b_val = length / 2

        def dome_z(x, y):
            xn, yn = x / a_val, y / b_val
            rx, ry = 1.0 - xn*xn, 1.0 - yn*yn
            return height * math.sqrt(max(rx, 0)) * math.sqrt(max(ry, 0))

        deg_u, deg_v = 3, 3
        u_p = [i / (nu - 1) for i in range(nu)]
        v_p = [j / (nv - 1) for j in range(nv)]

        cpts = []
        for i in range(nu):
            row = []
            for j in range(nv):
                x = (u_p[i] - 0.5) * width
                y = (v_p[j] - 0.5) * length
                z = dome_z(x, y)
                row.append((x, y, z))
            cpts.append(row)

        def clamp_knots(n, d):
            nk = n + d + 1
            return [0.0 if i <= d else 1.0 if i >= nk-d-1 else (i-d)/(n-d) for i in range(nk)]

        ku_raw = clamp_knots(nu, deg_u)
        kv_raw = clamp_knots(nv, deg_v)

        def to_mults(knots):
            u, m = [], []
            for k in knots:
                if not u or abs(k - u[-1]) > 1e-10:
                    u.append(k); m.append(1)
                else:
                    m[-1] += 1
            return u, m

        ku_u, ku_m = to_mults(ku_raw)
        kv_u, kv_m = to_mults(kv_raw)

        # ── STEP 엔티티 빌더 ──
        eid = [0]
        lines = []
        def add(t):
            eid[0] += 1
            lines.append(f"#{eid[0]} = {t}")
            return eid[0]

        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # ── 공통 헤더: Product / Context / Units ──
        ctx = add("APPLICATION_CONTEXT('automotive_design')")
        add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{ctx})")
        pctx = add(f"PRODUCT_CONTEXT('',#{ctx},'mechanical')")
        pdctx = add(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{ctx},'')")
        prod = add(f"PRODUCT('AirDome','Air Dome Model - Separated Bodies','',(#{pctx}))")
        pdf = add(f"PRODUCT_DEFINITION_FORMATION('','',#{prod})")
        pd = add(f"PRODUCT_DEFINITION('design','',#{pdf},#{pdctx})")
        pds = add(f"PRODUCT_DEFINITION_SHAPE('','',#{pd})")

        b0 = eid[0]
        mm_id, rad_id, sr_id, unc_id, grc_id = b0+1, b0+2, b0+3, b0+4, b0+5
        add("( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )")
        add("( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) )")
        add("( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() )")
        add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-04),#{mm_id},'distance_accuracy_value','')")
        add(f"( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{unc_id})) GLOBAL_UNIT_ASSIGNED_CONTEXT((#{mm_id},#{rad_id},#{sr_id})) REPRESENTATION_CONTEXT('3D','3D') )")

        org = add("CARTESIAN_POINT('Origin',(0.,0.,0.))")
        dz_id = add("DIRECTION('',(0.,0.,1.))")
        dx_id = add("DIRECTION('',(1.,0.,0.))")
        ax = add(f"AXIS2_PLACEMENT_3D('',#{org},#{dz_id},#{dx_id})")

        # ── 공통 헬퍼: B-Spline 커브 생성 ──
        def make_curve(name, pts_ids, degree, knots_unique, knots_mults):
            p_str = "(" + ",".join(f"#{p}" for p in pts_ids) + ")"
            m_str = "(" + ",".join(str(m) for m in knots_mults) + ")"
            k_str = "(" + ",".join("%.10f" % k for k in knots_unique) + ")"
            return add(f"B_SPLINE_CURVE_WITH_KNOTS('{name}',{degree},{p_str},.UNSPECIFIED.,.F.,.F.,{m_str},{k_str},.UNSPECIFIED.)")

        # 모든 분리된 Body를 모을 리스트
        rep_items = []

        # ════════════════════════════════════════════════════════════
        # [Body 1] 돔 서피스 (DomeSurface) — B-Spline Open Shell
        # ════════════════════════════════════════════════════════════
        cp = []
        for i in range(nu):
            row = []
            for j in range(nv):
                x, y, z = cpts[i][j]
                pid = add("CARTESIAN_POINT('',(%.4f,%.4f,%.4f))" % (x, y, z))
                row.append(pid)
            cp.append(row)

        cp_str = "(" + ",".join("(" + ",".join(f"#{cp[i][j]}" for j in range(nv)) + ")" for i in range(nu)) + ")"
        um = "(" + ",".join(str(m) for m in ku_m) + ")"
        vm = "(" + ",".join(str(m) for m in kv_m) + ")"
        uk = "(" + ",".join("%.10f" % k for k in ku_u) + ")"
        vk = "(" + ",".join("%.10f" % k for k in kv_u) + ")"

        surf = add(f"B_SPLINE_SURFACE_WITH_KNOTS('DomeSurf',{deg_u},{deg_v},{cp_str},.UNSPECIFIED.,.F.,.F.,.F.,{um},{vm},{uk},{vk},.UNSPECIFIED.)")

        crv_u0 = make_curve("Edge_u0", [cp[0][j] for j in range(nv)], deg_v, kv_u, kv_m)
        crv_u1 = make_curve("Edge_u1", [cp[nu-1][j] for j in range(nv)], deg_v, kv_u, kv_m)
        crv_v0 = make_curve("Edge_v0", [cp[i][0] for i in range(nu)], deg_u, ku_u, ku_m)
        crv_v1 = make_curve("Edge_v1", [cp[i][nv-1] for i in range(nu)], deg_u, ku_u, ku_m)

        corner_cp = [cp[0][0], cp[nu-1][0], cp[nu-1][nv-1], cp[0][nv-1]]
        vx = [add(f"VERTEX_POINT('',#{c})") for c in corner_cp]

        ec_v0 = add(f"EDGE_CURVE('',#{vx[0]},#{vx[1]},#{crv_v0},.T.)")
        ec_u1 = add(f"EDGE_CURVE('',#{vx[1]},#{vx[2]},#{crv_u1},.T.)")
        ec_v1 = add(f"EDGE_CURVE('',#{vx[3]},#{vx[2]},#{crv_v1},.T.)")
        ec_u0 = add(f"EDGE_CURVE('',#{vx[0]},#{vx[3]},#{crv_u0},.T.)")

        oe1 = add(f"ORIENTED_EDGE('',*,*,#{ec_v0},.T.)")
        oe2 = add(f"ORIENTED_EDGE('',*,*,#{ec_u1},.T.)")
        oe3 = add(f"ORIENTED_EDGE('',*,*,#{ec_v1},.F.)")
        oe4 = add(f"ORIENTED_EDGE('',*,*,#{ec_u0},.F.)")

        el = add(f"EDGE_LOOP('',({','.join(f'#{o}' for o in [oe1,oe2,oe3,oe4])}))")
        fb = add(f"FACE_OUTER_BOUND('',#{el},.T.)")
        af = add(f"ADVANCED_FACE('DomeFace',(#{fb}),#{surf},.T.)")
        dome_shell = add(f"OPEN_SHELL('DomeShell',(#{af}))")
        dome_model = add(f"SHELL_BASED_SURFACE_MODEL('DomeSurface',(#{dome_shell}))")
        rep_items.append(dome_model)

        # ════════════════════════════════════════════════════════════
        # [Body 2] 매트 기초 (Foundation) — 6면 Closed Shell Solid
        #   범위: (-a_val, -b_val, -foundation_depth) ~ (a_val, b_val, 0)
        # ════════════════════════════════════════════════════════════
        if foundation_depth > 0:
            hw, hl, fd = a_val, b_val, foundation_depth

            # 8개 꼭짓점 정의 (박스)
            #   상면 z=0:  ft0(-hw,-hl,0)  ft1(hw,-hl,0)  ft2(hw,hl,0)  ft3(-hw,hl,0)
            #   하면 z=-fd: fb0(-hw,-hl,-fd) fb1(hw,-hl,-fd) fb2(hw,hl,-fd) fb3(-hw,hl,-fd)
            fcp = {
                'ft0': add("CARTESIAN_POINT('ft0',(%.4f,%.4f,0.))" % (-hw, -hl)),
                'ft1': add("CARTESIAN_POINT('ft1',(%.4f,%.4f,0.))" % ( hw, -hl)),
                'ft2': add("CARTESIAN_POINT('ft2',(%.4f,%.4f,0.))" % ( hw,  hl)),
                'ft3': add("CARTESIAN_POINT('ft3',(%.4f,%.4f,0.))" % (-hw,  hl)),
                'fb0': add("CARTESIAN_POINT('fb0',(%.4f,%.4f,%.4f))" % (-hw, -hl, -fd)),
                'fb1': add("CARTESIAN_POINT('fb1',(%.4f,%.4f,%.4f))" % ( hw, -hl, -fd)),
                'fb2': add("CARTESIAN_POINT('fb2',(%.4f,%.4f,%.4f))" % ( hw,  hl, -fd)),
                'fb3': add("CARTESIAN_POINT('fb3',(%.4f,%.4f,%.4f))" % (-hw,  hl, -fd)),
            }
            fvx = {k: add(f"VERTEX_POINT('',#{v})") for k, v in fcp.items()}

            # 직선 엣지 헬퍼: 두 점 사이 LINE 생성
            def _make_line_edge(name, vp1_key, vp2_key):
                """두 꼭짓점 사이의 직선 엣지 생성"""
                p1, p2 = fcp[vp1_key], fcp[vp2_key]
                line_id = add(f"LINE('{name}',#{p1},#{add(f'VECTOR(,#{add(chr(35)+str(p2))},1.)')})")
                # LINE 대신 더 안정적인 방법: 2점 B-Spline degree 1
                return None  # 아래 _make_box_edge 사용

            def _make_box_edge(name, vp1_key, vp2_key):
                """두 꼭짓점 사이의 직선 Edge (Polyline 사용)"""
                poly = add(f"POLYLINE('{name}',(#{fcp[vp1_key]},#{fcp[vp2_key]}))")
                return add(f"EDGE_CURVE('',#{fvx[vp1_key]},#{fvx[vp2_key]},#{poly},.T.)")

            # 12개 엣지 생성
            # 상면 (z=0) 엣지: ft0→ft1→ft2→ft3→ft0
            fe_t01 = _make_box_edge('FndTop01', 'ft0', 'ft1')
            fe_t12 = _make_box_edge('FndTop12', 'ft1', 'ft2')
            fe_t23 = _make_box_edge('FndTop23', 'ft2', 'ft3')
            fe_t30 = _make_box_edge('FndTop30', 'ft3', 'ft0')
            # 하면 (z=-fd) 엣지: fb0→fb1→fb2→fb3→fb0
            fe_b01 = _make_box_edge('FndBot01', 'fb0', 'fb1')
            fe_b12 = _make_box_edge('FndBot12', 'fb1', 'fb2')
            fe_b23 = _make_box_edge('FndBot23', 'fb2', 'fb3')
            fe_b30 = _make_box_edge('FndBot30', 'fb3', 'fb0')
            # 수직 엣지 (4개 기둥)
            fe_v0 = _make_box_edge('FndVert0', 'fb0', 'ft0')
            fe_v1 = _make_box_edge('FndVert1', 'fb1', 'ft1')
            fe_v2 = _make_box_edge('FndVert2', 'fb2', 'ft2')
            fe_v3 = _make_box_edge('FndVert3', 'fb3', 'ft3')

            # PLANE 서피스 헬퍼
            def _make_plane(name, origin_xyz, normal_xyz, ref_xyz):
                """평면 서피스 생성"""
                po = add("CARTESIAN_POINT('',(%.4f,%.4f,%.4f))" % origin_xyz)
                pn = add("DIRECTION('',(%.4f,%.4f,%.4f))" % normal_xyz)
                pr = add("DIRECTION('',(%.4f,%.4f,%.4f))" % ref_xyz)
                pax = add(f"AXIS2_PLACEMENT_3D('',#{po},#{pn},#{pr})")
                return add(f"PLANE('{name}',#{pax})")

            # ADVANCED_FACE 헬퍼: 4개 엣지로 면 생성
            def _make_quad_face(name, edges_and_orient, plane_id):
                """사각형 면 생성 (edges_and_orient: [(edge_id, is_forward), ...])"""
                oes = []
                for e_id, fwd in edges_and_orient:
                    orient = '.T.' if fwd else '.F.'
                    oes.append(add(f"ORIENTED_EDGE('',*,*,#{e_id},{orient})"))
                el_id = add(f"EDGE_LOOP('',({','.join(f'#{o}' for o in oes)}))")
                fb_id = add(f"FACE_OUTER_BOUND('',#{el_id},.T.)")
                return add(f"ADVANCED_FACE('{name}',(#{fb_id}),#{plane_id},.T.)")

            # 6개 면 생성
            # 상면 (Top, z=0): 법선 +Z, 엣지 ft0→ft1→ft2→ft3
            plane_top = _make_plane('PlnTop', (0, 0, 0), (0, 0, 1), (1, 0, 0))
            face_top = _make_quad_face('FndTopFace',
                [(fe_t01, True), (fe_t12, True), (fe_t23, True), (fe_t30, True)],
                plane_top)

            # 하면 (Bottom, z=-fd): 법선 -Z, 엣지 fb0→fb3→fb2→fb1 (외향 법선)
            plane_bot = _make_plane('PlnBot', (0, 0, -fd), (0, 0, -1), (1, 0, 0))
            face_bot = _make_quad_face('FndBotFace',
                [(fe_b01, False), (fe_b12, False), (fe_b23, False), (fe_b30, False)],
                plane_bot)

            # 전면 (Front, y=-hl): 법선 -Y, 엣지 ft0→fb0→fb1→ft1
            plane_front = _make_plane('PlnFront', (0, -hl, 0), (0, -1, 0), (1, 0, 0))
            face_front = _make_quad_face('FndFrontFace',
                [(fe_t01, False), (fe_v1, False), (fe_b01, False), (fe_v0, True)],
                plane_front)

            # 후면 (Back, y=+hl): 법선 +Y, 엣지 ft2→fb2→fb3→ft3
            plane_back = _make_plane('PlnBack', (0, hl, 0), (0, 1, 0), (-1, 0, 0))
            face_back = _make_quad_face('FndBackFace',
                [(fe_t23, False), (fe_v3, False), (fe_b23, False), (fe_v2, True)],
                plane_back)

            # 좌면 (Left, x=-hw): 법선 -X, 엣지 ft3→fb3→fb0→ft0
            plane_left = _make_plane('PlnLeft', (-hw, 0, 0), (-1, 0, 0), (0, -1, 0))
            face_left = _make_quad_face('FndLeftFace',
                [(fe_t30, False), (fe_v0, False), (fe_b30, False), (fe_v3, True)],
                plane_left)

            # 우면 (Right, x=+hw): 법선 +X, 엣지 ft1→fb1→fb2→ft2
            plane_right = _make_plane('PlnRight', (hw, 0, 0), (1, 0, 0), (0, 1, 0))
            face_right = _make_quad_face('FndRightFace',
                [(fe_t12, False), (fe_v2, False), (fe_b12, False), (fe_v1, True)],
                plane_right)

            # CLOSED_SHELL → MANIFOLD_SOLID_BREP (CATIA가 Solid Body로 인식)
            all_faces = ",".join(f"#{f}" for f in [face_top, face_bot, face_front, face_back, face_left, face_right])
            fnd_shell = add(f"CLOSED_SHELL('FoundationShell',({all_faces}))")
            fnd_solid = add(f"MANIFOLD_SOLID_BREP('Foundation',#{fnd_shell})")
            rep_items.append(fnd_solid)

        # ════════════════════════════════════════════════════════════
        # [Body 3] 케이블넷 (CableNet) — Geometric Curve Set
        # ════════════════════════════════════════════════════════════
        cable_curve_ids = []
        if cable_spacing > 0:
            # B-Spline 보간법 헬퍼 함수들
            def _chord_params(pts):
                t = [0.0]
                for i in range(1, len(pts)):
                    d = math.sqrt(sum((pts[i][k]-pts[i-1][k])**2 for k in range(3)))
                    t.append(t[-1] + d)
                L = t[-1]
                return [v/L for v in t] if L > 1e-10 else [i/(len(pts)-1) for i in range(len(pts))]

            def _interp_knots(t, p):
                n = len(t) - 1
                U = [0.0] * (p + 1)
                for j in range(1, n - p + 1):
                    U.append(sum(t[j:j+p]) / p)
                U.extend([1.0] * (p + 1))
                return U

            def _basis(U, i, p, u):
                m = len(U) - 1
                if abs(u - U[m]) < 1e-10 and i == m - p - 1:
                    return 1.0
                if p == 0:
                    return 1.0 if U[i] <= u < U[i+1] else 0.0
                v = 0.0
                d1 = U[i+p] - U[i]
                if d1 > 1e-10:
                    v += (u - U[i]) / d1 * _basis(U, i, p-1, u)
                d2 = U[i+p+1] - U[i+1]
                if d2 > 1e-10:
                    v += (U[i+p+1] - u) / d2 * _basis(U, i+1, p-1, u)
                return v

            def _interp_bspline(data, p=3):
                n = len(data) - 1
                if n < p:
                    return list(data), clamp_knots(len(data), min(p, n))
                t = _chord_params(data)
                U = _interp_knots(t, p)
                sz = n + 1
                N_mat = [[_basis(U, i, p, t[k]) for i in range(sz)] for k in range(sz)]
                ctrl = [[0.0, 0.0, 0.0] for _ in range(sz)]
                for dim in range(3):
                    rhs = [data[k][dim] for k in range(sz)]
                    A = [N_mat[r][:] + [rhs[r]] for r in range(sz)]
                    for col in range(sz):
                        mx, mr = abs(A[col][col]), col
                        for r in range(col+1, sz):
                            if abs(A[r][col]) > mx:
                                mx, mr = abs(A[r][col]), r
                        if mr != col:
                            A[col], A[mr] = A[mr], A[col]
                        if abs(A[col][col]) < 1e-15:
                            continue
                        for r in range(col+1, sz):
                            f = A[r][col] / A[col][col]
                            for c in range(col, sz+1):
                                A[r][c] -= f * A[col][c]
                    x = [0.0] * sz
                    for i in range(sz-1, -1, -1):
                        x[i] = A[i][sz]
                        for j in range(i+1, sz):
                            x[i] -= A[i][j] * x[j]
                        if abs(A[i][i]) > 1e-15:
                            x[i] /= A[i][i]
                    for i in range(sz):
                        ctrl[i][dim] = x[i]
                return ctrl, U

            # 대각선 케이블넷 생성 (3D 뷰어와 동일한 로직)
            interp_n = 40

            for d in range(2):
                off = -(b_val + a_val)
                cable_idx = 0
                while off <= (b_val + a_val):
                    if d == 0:
                        x_start = max(-a_val, -b_val - off)
                        x_end = min(a_val, b_val - off)
                    else:
                        x_start = max(-a_val, off - b_val)
                        x_end = min(a_val, off + b_val)

                    if x_end - x_start > 10:
                        data = []
                        nn = max(interp_n, 8)
                        for t in range(nn + 1):
                            s = t / nn
                            x = x_start + s * (x_end - x_start)
                            y = (x + off) if d == 0 else (-x + off)
                            y = max(-b_val, min(b_val, y))
                            z = dome_z(x, y)
                            data.append((x, y, z))

                        if len(data) >= 4:
                            try:
                                ctrl, U_interp = _interp_bspline(data, 3)
                                pts_ids = []
                                for cpt in ctrl:
                                    pid = add("CARTESIAN_POINT('',(%.4f,%.4f,%.4f))" % (cpt[0], cpt[1], cpt[2]))
                                    pts_ids.append(pid)
                                ku_i, km_i = to_mults(U_interp)
                                direction = "A" if d == 0 else "B"
                                cid = make_curve(f"Cable_{direction}_{cable_idx}", pts_ids, 3, ku_i, km_i)
                                cable_curve_ids.append(cid)
                            except Exception:
                                pass
                    cable_idx += 1
                    off += cable_spacing

        if cable_curve_ids:
            curves_ref = ",".join(f"#{c}" for c in cable_curve_ids)
            cable_set = add(f"GEOMETRIC_CURVE_SET('CableNet',({curves_ref}))")
            rep_items.append(cable_set)

        # ════════════════════════════════════════════════════════════
        # [Body 4] 바닥 슬래브 (GroundPlane) — 평면 Open Shell
        #   돔 바닥면 전체를 덮는 z=0 평면 (약간 여유 포함)
        # ════════════════════════════════════════════════════════════
        gp_margin = 500  # 바닥 슬래브 여유 폭 (mm)
        gw, gl = a_val + gp_margin, b_val + gp_margin

        # 4개 꼭짓점 (z=0 평면)
        gp_pts = {
            'g0': add("CARTESIAN_POINT('gp0',(%.4f,%.4f,0.))" % (-gw, -gl)),
            'g1': add("CARTESIAN_POINT('gp1',(%.4f,%.4f,0.))" % ( gw, -gl)),
            'g2': add("CARTESIAN_POINT('gp2',(%.4f,%.4f,0.))" % ( gw,  gl)),
            'g3': add("CARTESIAN_POINT('gp3',(%.4f,%.4f,0.))" % (-gw,  gl)),
        }
        gp_vx = {k: add(f"VERTEX_POINT('',#{v})") for k, v in gp_pts.items()}

        # 4개 엣지 (Polyline) — 중첩 f-string 회피를 위해 분리
        def _gp_edge(name, k1, k2):
            poly = add("POLYLINE('%s',(#%d,#%d))" % (name, gp_pts[k1], gp_pts[k2]))
            return add("EDGE_CURVE('',#%d,#%d,#%d,.T.)" % (gp_vx[k1], gp_vx[k2], poly))

        gp_e01 = _gp_edge('gpe01', 'g0', 'g1')
        gp_e12 = _gp_edge('gpe12', 'g1', 'g2')
        gp_e23 = _gp_edge('gpe23', 'g2', 'g3')
        gp_e30 = _gp_edge('gpe30', 'g3', 'g0')

        gp_oe0 = add(f"ORIENTED_EDGE('',*,*,#{gp_e01},.T.)")
        gp_oe1 = add(f"ORIENTED_EDGE('',*,*,#{gp_e12},.T.)")
        gp_oe2 = add(f"ORIENTED_EDGE('',*,*,#{gp_e23},.T.)")
        gp_oe3 = add(f"ORIENTED_EDGE('',*,*,#{gp_e30},.T.)")

        gp_loop = add(f"EDGE_LOOP('',({','.join(f'#{o}' for o in [gp_oe0, gp_oe1, gp_oe2, gp_oe3])}))")
        gp_bound = add(f"FACE_OUTER_BOUND('',#{gp_loop},.T.)")

        # z=0 평면 서피스
        gp_org = add("CARTESIAN_POINT('',(0.,0.,0.))")
        gp_nz = add("DIRECTION('',(0.,0.,1.))")
        gp_rx = add("DIRECTION('',(1.,0.,0.))")
        gp_ax = add(f"AXIS2_PLACEMENT_3D('',#{gp_org},#{gp_nz},#{gp_rx})")
        gp_plane = add(f"PLANE('GroundLevel',#{gp_ax})")

        gp_face = add(f"ADVANCED_FACE('GroundFace',(#{gp_bound}),#{gp_plane},.T.)")
        gp_shell = add(f"OPEN_SHELL('GroundShell',(#{gp_face}))")
        gp_model = add(f"SHELL_BASED_SURFACE_MODEL('GroundPlane',(#{gp_shell}))")
        rep_items.append(gp_model)

        # ════════════════════════════════════════════════════════════
        # SHAPE_REPRESENTATION — 모든 Body를 하나의 Part에 포함
        # CATIA Import 시 각 Named Item이 별도 Body/Geometrical Set으로 분리됨
        # ════════════════════════════════════════════════════════════
        items_str = ",".join(f"#{item}" for item in rep_items)
        rep = add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('AirDome',({items_str},#{ax}),#{grc_id})")
        add(f"SHAPE_DEFINITION_REPRESENTATION(#{pds},#{rep})")

        # ── 파일 출력 ──
        with open(filepath, 'w') as f:
            f.write("ISO-10303-21;\nHEADER;\n")
            f.write("FILE_DESCRIPTION(('Air Dome - Separated Bodies: DomeSurface, Foundation, CableNet, GroundPlane'),'2;1');\n")
            f.write(f"FILE_NAME('{os.path.basename(filepath)}','{now}',('OzoMeta'),(''),'AirDome3DViewer','','');\n")
            f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\nENDSEC;\nDATA;\n")
            for l in lines:
                f.write(l + ";\n")
            f.write("ENDSEC;\nEND-ISO-10303-21;\n")

        return eid[0]


# ============================================================
# Main Application GUI
# ============================================================
class AirDomeViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AIR DOME 3D Simulator - 에어돔 3D 시뮬레이터")
        self.geometry("800x800")
        self.configure(bg="#2c3e50")
        self.resizable(True, True)

        self.pdf_folder = tk.StringVar(value="")
        self.pdf_files = []
        self.analysis_results = {}

        # Parameters
        self.param_project = tk.StringVar(value="Air Dome Project")
        self.param_width = tk.DoubleVar(value=0)
        self.param_length = tk.DoubleVar(value=0)
        self.param_height = tk.DoubleVar(value=0)
        self.param_dome_type = tk.StringVar(value="Rectangular")
        self.param_cable_spacing = tk.DoubleVar(value=3600)
        self.param_foundation_depth = tk.DoubleVar(value=500)
        self._build_ui()

    def _build_ui(self):
        # Title with company logo
        title_frame = tk.Frame(self, bg="#1a237e", pady=10)
        title_frame.pack(fill=tk.X)

        # 로고 + 타이틀을 가로로 배치하는 내부 프레임
        title_inner = tk.Frame(title_frame, bg="#1a237e")
        title_inner.pack()

        # 회사 로고 로딩
        try:
            from PIL import Image, ImageTk
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                # 로고 높이를 50px로 맞추고 비율 유지
                logo_h = 50
                ratio = logo_h / logo_img.height
                logo_w = int(logo_img.width * ratio)
                logo_img = logo_img.resize((logo_w, logo_h), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(title_inner, image=self._logo_photo, bg="#1a237e")
                logo_label.pack(side=tk.LEFT, padx=(0, 12))
        except Exception:
            pass

        # 타이틀 텍스트 영역 (세로 배치)
        title_text_frame = tk.Frame(title_inner, bg="#1a237e")
        title_text_frame.pack(side=tk.LEFT)

        tk.Label(title_text_frame, text="AIR DOME 3D Simulator", font=("Segoe UI", 18, "bold"),
                 fg="white", bg="#1a237e").pack(anchor="w")
        tk.Label(title_text_frame, text="에어돔 구조 시뮬레이션 및 3D 모델링 도구  |  OzoMeta",
                 font=("Segoe UI", 9), fg="#aaa", bg="#1a237e").pack(anchor="w")

        # Main content
        main = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#2c3e50", sashwidth=4)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: PDF list
        left = tk.Frame(main, bg="#34495e", width=350)
        main.add(left, width=350)

        # Folder selection
        folder_frame = tk.LabelFrame(left, text=" 📁 PDF 도면 폴더 ", font=("Segoe UI", 10, "bold"),
                                     fg="white", bg="#34495e", padx=5, pady=5)
        folder_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = tk.Frame(folder_frame, bg="#34495e")
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="폴더 선택...", command=self._select_folder,
                  bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=15, pady=5).pack(side=tk.LEFT, padx=2)
        self.folder_label = tk.Label(folder_frame, textvariable=self.pdf_folder,
                                     fg="#aaa", bg="#34495e", font=("Segoe UI", 8),
                                     wraplength=320, anchor="w")
        self.folder_label.pack(fill=tk.X, pady=(3,0))

        # PDF list
        list_frame = tk.LabelFrame(left, text=" 📄 PDF 파일 목록 ", font=("Segoe UI", 10, "bold"),
                                   fg="white", bg="#34495e", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.pdf_listbox = tk.Listbox(list_frame, bg="#2c3e50", fg="white",
                                       selectbackground="#3498db", font=("Segoe UI", 9),
                                       relief=tk.FLAT, borderwidth=0)
        self.pdf_listbox.pack(fill=tk.BOTH, expand=True)
        self.pdf_listbox.bind('<<ListboxSelect>>', self._on_pdf_select)

        # PDF action buttons
        pdf_btn_frame = tk.Frame(left, bg="#34495e")
        pdf_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 2))

        self.btn_open_pdf = tk.Button(pdf_btn_frame, text="📖 도면 열기",
                                       command=self._open_selected_pdf,
                                       bg="#16a085", fg="white", font=("Segoe UI", 9, "bold"),
                                       relief=tk.FLAT, pady=4, cursor="hand2")
        self.btn_open_pdf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_apply_dims = tk.Button(pdf_btn_frame, text="📐 치수 적용",
                                         command=self._apply_pdf_dims,
                                         bg="#e67e22", fg="white", font=("Segoe UI", 9, "bold"),
                                         relief=tk.FLAT, pady=4, cursor="hand2")
        self.btn_apply_dims.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        self._current_pdf_dims = []

        # Analysis result
        self.analysis_text = tk.Text(left, height=8, bg="#2c3e50", fg="#aaa",
                                     font=("Consolas", 8), relief=tk.FLAT, padx=5, pady=5)
        self.analysis_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Right panel: Parameters & Actions
        right = tk.Frame(main, bg="#2c3e50")
        main.add(right)

        # Parameters
        param_frame = tk.LabelFrame(right, text=" ⚙️ 돔 파라미터 ", font=("Segoe UI", 11, "bold"),
                                    fg="white", bg="#2c3e50", padx=15, pady=10)
        param_frame.pack(fill=tk.X, padx=5, pady=5)

        params = [
            ("프로젝트명:", self.param_project, "str"),
            ("폭 Width (mm):", self.param_width, "float"),
            ("길이 Length (mm):", self.param_length, "float"),
            ("높이 Height (mm):", self.param_height, "float"),
            ("케이블 간격 (mm):", self.param_cable_spacing, "float"),
            ("기초 깊이 (mm):", self.param_foundation_depth, "float"),
        ]

        for i, (label, var, vtype) in enumerate(params):
            tk.Label(param_frame, text=label, fg="#ecf0f1", bg="#2c3e50",
                     font=("Segoe UI", 10), anchor="e").grid(row=i, column=0, sticky="e", pady=3, padx=(0,8))
            entry = tk.Entry(param_frame, textvariable=var, font=("Segoe UI", 10, "bold"),
                           bg="#34495e", fg="#4fc3f7", relief=tk.FLAT, insertbackground="#4fc3f7")
            entry.grid(row=i, column=1, sticky="ew", pady=3)

        # Dome type
        tk.Label(param_frame, text="돔 타입:", fg="#ecf0f1", bg="#2c3e50",
                 font=("Segoe UI", 10), anchor="e").grid(row=len(params), column=0, sticky="e", pady=3, padx=(0,8))
        dome_type_cb = ttk.Combobox(param_frame, textvariable=self.param_dome_type,
                                     values=["Rectangular", "Oval/Elliptical", "Circular"],
                                     font=("Segoe UI", 10), state="readonly")
        dome_type_cb.grid(row=len(params), column=1, sticky="ew", pady=3)

        param_frame.columnconfigure(1, weight=1)

        # Calculated values display
        calc_frame = tk.LabelFrame(right, text=" 📐 산출값 ", font=("Segoe UI", 11, "bold"),
                                   fg="white", bg="#2c3e50", padx=15, pady=10)
        calc_frame.pack(fill=tk.X, padx=5, pady=5)

        self.calc_text = tk.Text(calc_frame, height=6, bg="#34495e", fg="#4fc3f7",
                                 font=("Consolas", 10), relief=tk.FLAT, padx=8, pady=5)
        self.calc_text.pack(fill=tk.X)
        self._update_calcs()

        # Bind parameter changes
        for var in [self.param_width, self.param_length, self.param_height]:
            var.trace_add("write", lambda *_: self._update_calcs())

        # Action buttons
        action_frame = tk.Frame(right, bg="#2c3e50", pady=10)
        action_frame.pack(fill=tk.X, padx=5)

        tk.Button(action_frame, text="🌐  3D 미리보기  (브라우저에서 열기)",
                  command=self._preview_3d,
                  bg="#27ae60", fg="white", font=("Segoe UI", 12, "bold"),
                  relief=tk.FLAT, pady=10, cursor="hand2").pack(fill=tk.X, pady=3)

        tk.Button(action_frame, text="📦  STEP 파일 내보내기  (.stp → CATIA Import)",
                  command=self._export_step,
                  bg="#2980b9", fg="white", font=("Segoe UI", 12, "bold"),
                  relief=tk.FLAT, pady=10, cursor="hand2").pack(fill=tk.X, pady=3)

        tk.Button(action_frame, text="📊  STL 파일 내보내기  (.stl → Mesh)",
                  command=self._export_stl,
                  bg="#8e44ad", fg="white", font=("Segoe UI", 11),
                  relief=tk.FLAT, pady=8, cursor="hand2").pack(fill=tk.X, pady=3)

        # 시뮬레이션 섹션 구분선
        sep_frame = tk.Frame(action_frame, bg="#4fc3f7", height=2)
        sep_frame.pack(fill=tk.X, pady=(12, 6))

        tk.Label(action_frame, text="── 구조 시뮬레이션 ──",
                 fg="#4fc3f7", bg="#2c3e50", font=("Segoe UI", 10, "bold")).pack(pady=(0, 3))

        tk.Button(action_frame, text="🔬  구조 시뮬레이션  (압력·장력·풍하중·적설·안전율)",
                  command=self._simulation_3d,
                  bg="#e74c3c", fg="white", font=("Segoe UI", 12, "bold"),
                  relief=tk.FLAT, pady=10, cursor="hand2").pack(fill=tk.X, pady=3)

        # Status bar
        self.status_var = tk.StringVar(value="폴더를 선택하여 시작하세요")
        status_bar = tk.Label(self, textvariable=self.status_var, bg="#1a237e",
                             fg="#aaa", font=("Segoe UI", 9), anchor="w", padx=10, pady=3)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _select_folder(self):
        folder = filedialog.askdirectory(title="PDF 도면이 있는 폴더를 선택하세요")
        if folder:
            self.pdf_folder.set(folder)
            self.pdf_files = PDFAnalyzer.scan_folder(folder)
            self.pdf_listbox.delete(0, tk.END)
            for f in self.pdf_files:
                self.pdf_listbox.insert(tk.END, "  📄 " + os.path.basename(f))
            ocr_note = " (OCR 분석 중...)" if HAS_FITZ else ""
            self.status_var.set(f"⏳ {len(self.pdf_files)}개 PDF 분석 중...")
            self.update_idletasks()

            # 백그라운드 스레드에서 폴더 분석 실행
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

        # 모든 치수를 mm로 통합
        all_dims_combined = list(set(all_dims_mm))

        # 단위 없는 숫자도 포함 (mm 추정)
        for d in all_dims_raw:
            if d not in all_dims_combined:
                all_dims_combined.append(d)

        # m 단위 → mm 변환 추가
        for d in all_dims_m:
            if d < 200:  # 200m 미만이면 합리적인 건물 치수
                all_dims_combined.append(d * 1000)

        # 분석 결과를 메인 스레드에서 적용
        self.after(0, lambda: self._apply_folder_analysis(
            all_dims_combined, all_keywords, all_project
        ))

    def _apply_folder_analysis(self, all_dims_combined, all_keywords, all_project):
        """폴더 분석 결과를 UI에 적용 (메인 스레드)"""
        if all_dims_combined:
            sorted_dims = sorted(set(all_dims_combined), reverse=True)

            # 에어돔 합리적 범위 필터 (5,000mm ~ 150,000mm)
            dome_dims = [d for d in sorted_dims if 5000 <= d <= 150000]

            best_length, best_width, best_height = None, None, None

            if len(dome_dims) >= 3:
                # 에어돔 구조 특성 기반 자동 판별:
                # - 길이(L)/폭(W) 비율: 보통 1.0 ~ 2.5
                # - 높이(H)/폭(W) 비율: 보통 0.2 ~ 0.5
                # - 둘레, 합산값 등은 비율로 걸러냄
                # - 빈도가 높은 치수(여러 페이지에서 반복)에 가중치
                #
                # 전략: 모든 3개 조합을 시도해서 가장 에어돔 비율에 맞는 것 선택
                # 반복 횟수 가중치 계산
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
                        lw_ratio = L / W  # 기대: 1.0 ~ 2.5
                        if not (0.8 <= lw_ratio <= 3.0):
                            continue
                        for k, H in enumerate(candidates):
                            if k <= j:
                                continue
                            hw_ratio = H / W  # 기대: 0.2 ~ 0.5
                            if not (0.15 <= hw_ratio <= 0.55):
                                continue
                            # 점수: 비율 적합성만으로 평가 (크기 보너스 제거)
                            lw_score = 1.0 - abs(lw_ratio - 1.6) / 2.0
                            hw_score = 1.0 - abs(hw_ratio - 0.37) / 0.5
                            # 반복 출현 치수에 보너스
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
                    # 폴백: 상위 3개 직접 할당
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

        # 프로젝트명 자동 설정
        if all_project:
            self.param_project.set(all_project[0])

        # 분석 결과 요약 표시
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

    def _open_selected_pdf(self):
        """선택한 PDF를 시스템 기본 뷰어로 열기"""
        sel = self.pdf_listbox.curselection()
        if not sel:
            # 선택된 PDF가 없으면 첫 번째 파일 열기
            if self.pdf_files:
                os.startfile(self.pdf_files[0]) if sys.platform == 'win32' else webbrowser.open('file://' + self.pdf_files[0])
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

        # 백그라운드 스레드에서 PDF 분석 실행 (UI 멈춤 방지)
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
        # 모든 치수 소스 통합
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

            # 개별 PDF의 치수로도 파라미터 업데이트 제안
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

    def _preview_3d(self):
        params = self._get_params()
        if params['width'] <= 0 or params['length'] <= 0 or params['height'] <= 0:
            messagebox.showwarning("파라미터 필요",
                "폭(Width), 길이(Length), 높이(Height)를\n모두 입력해야 3D 미리보기가 가능합니다.\n\n"
                "PDF 폴더를 선택하거나 직접 입력해주세요.")
            return
        html = generate_viewer_html(params)

        # Save HTML to temp or output folder
        if self.pdf_folder.get():
            out_dir = self.pdf_folder.get()
        else:
            out_dir = tempfile.gettempdir()

        html_path = os.path.join(out_dir, "AirDome_3D_Preview.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        webbrowser.open('file://' + os.path.abspath(html_path))
        self.status_var.set(f"✅ 3D 미리보기 열림: {html_path}")

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
                # 포함된 Body 목록 표시
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
                w, l, h = params['width'], params['length'], params['height']
                a_val, b_val = w/2, l/2
                res = 80

                def dz(x, y):
                    rx = 1-(x/a_val)**2; ry = 1-(y/b_val)**2
                    return h*math.sqrt(max(rx,0))*math.sqrt(max(ry,0))

                us = [a_val*(-1 + 2*i/res) for i in range(res+1)]
                vs = [b_val*(-1 + 2*j/res) for j in range(res+1)]

                tris = []
                for j in range(res):
                    for i in range(res):
                        p = [(us[i+di], vs[j+dj], dz(us[i+di], vs[j+dj])) for di, dj in [(0,0),(1,0),(1,1),(0,1)]]
                        for t in [(p[0],p[1],p[2]), (p[0],p[2],p[3])]:
                            v1 = [t[1][k]-t[0][k] for k in range(3)]
                            v2 = [t[2][k]-t[0][k] for k in range(3)]
                            n = [v1[1]*v2[2]-v1[2]*v2[1], v1[2]*v2[0]-v1[0]*v2[2], v1[0]*v2[1]-v1[1]*v2[0]]
                            nl = math.sqrt(sum(x*x for x in n))
                            if nl > 0: n = [x/nl for x in n]
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

                self.status_var.set(f"✅ STL 저장 완료: {filepath} ({len(tris):,} triangles)")
                messagebox.showinfo("성공", f"STL 파일이 저장되었습니다.\n\n{filepath}")
            except Exception as e:
                messagebox.showerror("오류", f"STL 내보내기 실패:\n{e}")

    def _simulation_3d(self):
        """구조 시뮬레이션 뷰어 실행 (브라우저)"""
        params = self._get_params()
        if params['width'] <= 0 or params['length'] <= 0 or params['height'] <= 0:
            messagebox.showwarning("파라미터 필요",
                "폭(Width), 길이(Length), 높이(Height)를\n모두 입력해야 시뮬레이션이 가능합니다.\n\n"
                "PDF 폴더를 선택하거나 직접 입력해주세요.")
            return
        html = generate_simulation_html(params)

        # Save HTML
        if self.pdf_folder.get():
            out_dir = self.pdf_folder.get()
        else:
            out_dir = tempfile.gettempdir()

        html_path = os.path.join(out_dir, "AirDome_Simulation.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # 기술해설서 PDF를 HTML과 같은 폴더에 복사 (없으면 스크립트 폴더에서 찾기)
        guide_name = "AirDome_시뮬레이션_기술해설서.pdf"
        guide_dst = os.path.join(out_dir, guide_name)
        if not os.path.exists(guide_dst):
            # 스크립트가 위치한 폴더에서 PDF 검색
            script_dir = os.path.dirname(os.path.abspath(__file__))
            guide_src = os.path.join(script_dir, guide_name)
            if os.path.exists(guide_src):
                try:
                    shutil.copy2(guide_src, guide_dst)
                except Exception:
                    pass

        webbrowser.open('file://' + os.path.abspath(html_path))
        self.status_var.set(f"🔬 구조 시뮬레이션 열림: {html_path}")


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    app = AirDomeViewer()
    app.mainloop()