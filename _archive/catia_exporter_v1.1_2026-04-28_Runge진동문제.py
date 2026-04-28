"""CATIA STEP Export Module for AIR DOME 3D Simulator by OzoMeta

This module provides STEP file export functionality for the AirDome 3D geometry,
enabling seamless integration with CATIA and other CAD systems.
"""

import math
import os
import datetime


class STEPExporter:
    """에어돔 3D 곡면을 STEP 파일로 내보내기 (지오메트리 분리 지원)

    CATIA Import 시 다음 4개 Body/Geometrical Set으로 분리됨:
      1. DomeSurface  — 돔 곡면 (B-Spline Surface, Open Shell)
      2. Foundation   — 매트 기초 (Closed Shell Solid, 6면 박스)
      3. CableNet     — 케이블넷 (Geometric Curve Set, Wire Body)
      4. GroundPlane  — 바닥 슬래브 (Flat Surface, Open Shell)
    """

    @staticmethod
    def export(filepath, width, length, height, nu=21, nv=31,
               cable_spacing=0, foundation_depth=500):
        """STEP AP214 내보내기 — 지오메트리 분리 버전

        Args:
            filepath: 저장 경로
            width: 돔 폭 (mm) — 단변
            length: 돔 길이 (mm) — 장변 (능선 방향)
            height: 돔 높이 (mm)
            nu, nv: B-Spline 제어점 수 (단변·장변 방향)
                    기본 21×31 — Barrel Vault + Hip 형상의 능선·hip 경계 정확 표현
            cable_spacing: 케이블 간격 (mm), 0이면 케이블 없음
            foundation_depth: 기초 깊이 (mm), 기본 500mm
        """
        a_val = width / 2
        b_val = length / 2

        def dome_z(x, y):
            # Barrel Vault + 1/4 회전 hip (균일 곡률 평형 형태)
            # x: 단변 방향 (반경 a_val), y: 장변 방향 (반경 b_val)
            # 단변 단면이 원호 R=(a²+H²)/(2H), 양 끝 hip은 √(1-(dy/a)²)로 비례 축소
            R = (a_val * a_val + height * height) / (2 * height)
            cy = height - R
            ridge = max(0.0, b_val - a_val)
            sx = R * R - x * x
            if sx <= 0:
                return 0.0
            z_section = cy + math.sqrt(sx)
            if z_section <= 0:
                return 0.0
            if abs(y) <= ridge:
                return z_section
            dy = abs(y) - ridge
            fr_sq = 1 - (dy / a_val) ** 2
            if fr_sq <= 0:
                return 0.0
            return z_section * math.sqrt(fr_sq)

        deg_u, deg_v = 3, 3
        u_p = [i / (nu - 1) for i in range(nu)]
        v_p = [j / (nv - 1) for j in range(nv)]

        # ── 1단계: dome_z 위 격자점 산출 (surface가 통과해야 할 data points) ──
        data_pts = []
        for i in range(nu):
            row = []
            for j in range(nv):
                x = (u_p[i] - 0.5) * width
                y = (v_p[j] - 0.5) * length
                z = dome_z(x, y)
                row.append((x, y, z))
            data_pts.append(row)

        def clamp_knots(n, d):
            nk = n + d + 1
            return [0.0 if i <= d else 1.0 if i >= nk-d-1 else (i-d)/(n-d) for i in range(nk)]

        def to_mults(knots):
            u, m = [], []
            for k in knots:
                if not u or abs(k - u[-1]) > 1e-10:
                    u.append(k); m.append(1)
                else:
                    m[-1] += 1
            return u, m

        # ── NURBS 보간 헬퍼 (surface와 cable 양쪽에서 공유) ──
        # v1.0 (2026-04-28): cable에만 있던 함수를 surface에도 쓰도록 모듈 상단으로 승격
        # 목적: surface가 dome_z를 정확히 통과 (기존 approximation→interpolation 전환)
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

        def _solve_interp(data, t, U, p):
            """주어진 data·param·knot로 NURBS 제어점을 가우스 소거로 풀이."""
            n = len(data) - 1
            if n < p:
                return [list(d) for d in data]
            sz = n + 1
            N_mat = [[_basis(U, ii, p, t[k]) for ii in range(sz)] for k in range(sz)]
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
                for ii in range(sz-1, -1, -1):
                    x[ii] = A[ii][sz]
                    for jj in range(ii+1, sz):
                        x[ii] -= A[ii][jj] * x[jj]
                    if abs(A[ii][ii]) > 1e-15:
                        x[ii] /= A[ii][ii]
                for ii in range(sz):
                    ctrl[ii][dim] = x[ii]
            return ctrl

        def _interp_bspline(data, p=3, t=None, U=None):
            """1D NURBS 보간 진입점. t/U 미지정 시 chord-length param 자동 산출."""
            n = len(data) - 1
            if n < p:
                return [list(d) for d in data], clamp_knots(len(data), min(p, n))
            if t is None:
                t = _chord_params(data)
            if U is None:
                U = _interp_knots(t, p)
            return _solve_interp(data, t, U, p), U

        # ── 2단계: Surface 양방향(텐서곱) NURBS 보간 ──
        # uniform parameter 사용 (격자가 균등 → chord와 거의 동일, knot 통일성 보장)
        # Phase 1: U 방향 (각 j 열에 대해 nu개 점 보간) → intermediate 제어점
        # Phase 2: V 방향 (각 i 행에 대해 intermediate nv개 점 보간) → final 제어점
        # 결과 surface는 격자점 (t_u[i], t_v[j])에서 정확히 data_pts[i][j] 통과
        t_u = [i / (nu - 1) for i in range(nu)]
        t_v = [j / (nv - 1) for j in range(nv)]
        U_surf = _interp_knots(t_u, deg_u)
        V_surf = _interp_knots(t_v, deg_v)

        intermediate = [[None]*nv for _ in range(nu)]
        for j in range(nv):
            col_data = [data_pts[i][j] for i in range(nu)]
            ctrl_col = _solve_interp(col_data, t_u, U_surf, deg_u)
            for i in range(nu):
                intermediate[i][j] = ctrl_col[i]

        cpts = [[None]*nv for _ in range(nu)]
        for i in range(nu):
            row_data = intermediate[i]
            ctrl_row = _solve_interp(row_data, t_v, V_surf, deg_v)
            for j in range(nv):
                cpts[i][j] = tuple(ctrl_row[j])

        ku_raw = U_surf
        kv_raw = V_surf
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
            # 대각선 케이블넷 생성 (3D 뷰어와 동일한 로직)
            # NURBS 보간 헬퍼 (_chord_params/_interp_knots/_basis/_interp_bspline)는
            # surface와 공유하기 위해 export() 상단에서 정의됨
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
