"""
3D Preview Module for AIR DOME 3D Simulator

This module provides HTML generation for the 3D viewer component,
rendering an interactive Three.js-based 3D visualization of the dome structure.

Project: AIR DOME 3D Simulator
Organization: OzoMeta
"""

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
