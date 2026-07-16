from .common import *
from .fija import *
from .movil import *
from urllib.parse import quote


@st.cache_data(ttl=3600, show_spinner=False)
def _leer_csv_npn_local_cacheado(nombre, mtime=None):
    ruta = os.path.join(DATA_DIR, nombre)
    if not os.path.exists(ruta):
        return pd.DataFrame()
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"]:
        for sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, engine="python", on_bad_lines="skip")
                df.columns = df.columns.astype(str).str.strip()
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def _leer_operativa_teletalk_cacheado(mtime=None):
    candidatos = [
        "OPERATIVA_TELETALK.csv",
        "OPERATIVA_TELETALK.xlsx",
        "OPERATIVA_TELETALK.xls",
    ]
    ruta = next((os.path.join(DATA_DIR, n) for n in candidatos if os.path.exists(os.path.join(DATA_DIR, n))), None)
    if not ruta:
        return pd.DataFrame()
    ext = os.path.splitext(ruta)[1].lower()
    if ext in {".xlsx", ".xls"}:
        try:
            df = pd.read_excel(ruta)
            df.columns = df.columns.astype(str).str.strip()
            return df
        except Exception:
            return pd.DataFrame()
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"]:
        for sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, engine="python", on_bad_lines="skip")
                df.columns = df.columns.astype(str).str.strip()
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
    return pd.DataFrame()

def render_dashboard():
    _inject_tabs_card_style()
    OPCIONES_FIJA = [
        "Inicio: Reporte Comparativo FIJA",
        "Detalle Fija General FIJA",
    ]

    OPCIONES_MOVIL = [
        "Inicio: Reporte Comparativo MOVIL",
        "Detalle Móvil General",
    ]

    OPCIONES_FACTOR = [
        "📊 Resumen NPN",
        "💼 Comisión Operativa",
    ]

    SEP_FIJA   = "📡 FIJA"
    SEP_MOVIL  = "📱 MÓVIL"
    SEP_FACTOR = "📊 FACTOR NPN"
    SEPARADORES = {SEP_FIJA, SEP_MOVIL, SEP_FACTOR}

    todas_opciones = (
        [SEP_FIJA]   + OPCIONES_FIJA   +
        [SEP_MOVIL]  + OPCIONES_MOVIL  +
        [SEP_FACTOR] + OPCIONES_FACTOR
    )

    _nav_q = None
    try:
        _nav_q = st.query_params.get("nav")
    except Exception:
        _nav_q = None
    if isinstance(_nav_q, list):
        _nav_q = _nav_q[0] if _nav_q else None
    if _nav_q in todas_opciones and _nav_q not in SEPARADORES:
        st.session_state["radio_unico"] = _nav_q
        st.session_state["ultima_seleccion"] = _nav_q
        try:
            del st.query_params["nav"]
        except Exception:
            pass

    _mini_items = [
        ("📡", "Inicio Fija", "Inicio: Reporte Comparativo FIJA"),
        ("🧾", "Detalle Fija", "Detalle Fija General FIJA"),
        ("📱", "Inicio Móvil", "Inicio: Reporte Comparativo MOVIL"),
        ("📋", "Detalle Móvil", "Detalle Móvil General"),
        ("📊", "NPN", "📊 Resumen NPN"),
        ("💼", "Comisión Operativa", "💼 Comisión Operativa"),
    ]
    _mini_nav_html = "".join(
        f'<a class="dash-mini-item" title="{_html.escape(title)}" href="?nav={quote(option)}">'
        f'<span>{icon}</span><em>{_html.escape(title)}</em></a>'
        for icon, title, option in _mini_items
    )

    # Posiciones de los separadores (1-indexed para CSS nth-child)
    idx_sep_fija   = 1
    idx_sep_movil  = len(OPCIONES_FIJA) + 2
    idx_sep_factor = len(OPCIONES_FIJA) + len(OPCIONES_MOVIL) + 3

    seps_css = ",".join([
        f'section[data-testid="stSidebar"] .stRadio > div > label:nth-child({i})'
        for i in [idx_sep_fija, idx_sep_movil, idx_sep_factor]
    ])
    seps_input_css = ",".join([
        f'section[data-testid="stSidebar"] .stRadio > div > label:nth-child({i}) input'
        for i in [idx_sep_fija, idx_sep_movil, idx_sep_factor]
    ])
    seps_text_fija   = f'section[data-testid="stSidebar"] .stRadio > div > label:nth-child({idx_sep_fija}) div[data-testid="stMarkdownContainer"] p'
    seps_text_movil  = f'section[data-testid="stSidebar"] .stRadio > div > label:nth-child({idx_sep_movil}) div[data-testid="stMarkdownContainer"] p'
    seps_text_factor = f'section[data-testid="stSidebar"] .stRadio > div > label:nth-child({idx_sep_factor}) div[data-testid="stMarkdownContainer"] p'

    st.markdown(f"""
    <style>
    div[data-testid="stSidebarNav"] {{display:none}}

    .dash-mini-rail {{
        position:fixed;
        left:12px;
        top:86px;
        z-index:4;
        width:58px;
        padding:10px 8px;
        border-radius:18px;
        border:1px solid rgba(255,255,255,.42);
        background:linear-gradient(180deg,rgba(15,66,135,.94),rgba(109,11,140,.90));
        box-shadow:0 18px 38px rgba(15,23,42,.22);
        backdrop-filter:blur(14px);
        display:flex;
        flex-direction:column;
        gap:9px;
    }}
    .dash-mini-rail::before {{
        content:"TT";
        display:grid;
        place-items:center;
        width:38px;
        height:30px;
        margin:0 auto 4px auto;
        border-radius:10px;
        color:#fff;
        font-size:11px;
        font-weight:950;
        letter-spacing:.08em;
        background:rgba(255,255,255,.14);
        border:1px solid rgba(255,255,255,.18);
    }}
    .dash-mini-item {{
        width:40px;
        height:40px;
        margin:0 auto;
        border-radius:13px;
        display:grid;
        place-items:center;
        text-decoration:none !important;
        color:#fff !important;
        border:1px solid rgba(255,255,255,.16);
        background:rgba(255,255,255,.10);
        transition:transform .14s ease, background .14s ease, border-color .14s ease;
        position:relative;
    }}
    .dash-mini-item:hover {{
        transform:translateX(3px);
        background:rgba(255,255,255,.22);
        border-color:rgba(255,255,255,.36);
    }}
    .dash-mini-item span {{
        font-size:17px;
        line-height:1;
    }}
    .dash-mini-item em {{
        position:absolute;
        left:48px;
        top:50%;
        transform:translateY(-50%);
        display:none;
        white-space:nowrap;
        padding:8px 10px;
        border-radius:10px;
        background:#0f172a;
        color:#fff;
        font-style:normal;
        font-size:11px;
        font-weight:850;
        box-shadow:0 12px 24px rgba(15,23,42,.22);
    }}
    .dash-mini-item:hover em {{
        display:block;
    }}
    @media (min-width: 761px) {{
        body:has(section[data-testid="stSidebar"][aria-expanded="true"]) .dash-mini-rail {{
            z-index:0;
            opacity:0;
            pointer-events:none;
        }}
    }}

    section[data-testid="stSidebar"] {{
        background:
            linear-gradient(145deg, rgba(15,66,135,.96) 0%, rgba(37,99,235,.76) 43%, rgba(109,11,140,.92) 100%) !important;
        border-right:1px solid rgba(255,255,255,.24) !important;
        box-shadow:18px 0 40px rgba(15,23,42,.20) !important;
    }}
    section[data-testid="stSidebar"] > div {{
        background:linear-gradient(180deg, rgba(255,255,255,.17), rgba(255,255,255,.07)) !important;
        backdrop-filter: blur(18px) !important;
        border-right:1px solid rgba(255,255,255,.18) !important;
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top:20px !important;
        padding-left:18px !important;
        padding-right:18px !important;
    }}

    .dash-menu-shell {{
        border:1px solid rgba(255,255,255,.18);
        border-radius:10px;
        padding:13px 14px 12px 14px;
        margin-bottom:16px;
        background:rgba(10,32,76,.18);
        box-shadow:0 14px 30px rgba(15,23,42,.12);
    }}
    .dash-window-dots {{
        display:none;
    }}
    .dash-window-dots span {{
        width:11px; height:11px; border-radius:999px; display:block;
    }}
    .dash-dot-red {{ background:#ff313b; }}
    .dash-dot-yellow {{ background:#ffd33d; }}
    .dash-dot-green {{ background:#43d31d; }}
    .dash-brand {{
        font-size:18px; font-weight:950; color:#fff; letter-spacing:.03em;
        text-shadow:none;
    }}
    .dash-subbrand {{
        margin-top:4px; color:rgba(255,255,255,.72); font-size:10px;
        font-weight:900; letter-spacing:.12em; text-transform:uppercase;
    }}
    .dash-user-row {{
        display:flex; align-items:center; gap:11px;
        border-top:1px solid rgba(255,255,255,.16);
        border-bottom:0;
        padding:12px 0 2px 0; margin-top:12px;
    }}
    .dash-user-avatar {{
        width:32px; height:32px; border-radius:8px;
        display:grid; place-items:center;
        color:#fff; font-weight:950;
        background:linear-gradient(135deg,#0f4287,#7c3aed);
        border:1px solid rgba(255,255,255,.28);
    }}
    .dash-user-name {{
        color:#fff; font-size:13px; font-weight:900; line-height:1.15;
    }}
    .dash-user-role {{
        color:rgba(255,255,255,.64); font-size:10px; font-weight:800;
        text-transform:uppercase; letter-spacing:.08em; margin-top:3px;
    }}

    section[data-testid="stSidebar"] .stRadio > label {{
        display:none !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div {{
        gap:6px !important;
    }}

    {seps_css} {{
        pointer-events:none !important;
        cursor:default !important;
        margin-top:18px !important;
        margin-bottom:8px !important;
        min-height:32px !important;
        padding:8px 12px !important;
        border-radius:8px !important;
        border:1px solid rgba(255,255,255,.18) !important;
        border-left:4px solid rgba(255,255,255,.72) !important;
        background:linear-gradient(90deg, rgba(15,23,42,.24), rgba(255,255,255,.06)) !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.10) !important;
        position:relative !important;
    }}
    {seps_css}:has(input:checked) {{
        background:linear-gradient(90deg, rgba(15,23,42,.24), rgba(255,255,255,.06)) !important;
        border-color:rgba(255,255,255,.18) !important;
        border-left:4px solid rgba(255,255,255,.72) !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.10) !important;
        transform:none !important;
    }}
    {seps_input_css} {{ display:none !important; }}
    {seps_css} > div:first-child,
    {seps_css} span:first-child,
    {seps_css} svg:first-child {{
        display:none !important;
    }}
    {seps_css}::before,
    {seps_css}::after,
    {seps_css} *::before,
    {seps_css} *::after {{
        display:none !important;
        content:none !important;
    }}
    {seps_text_fija}, {seps_text_movil}, {seps_text_factor} {{
        font-weight:950 !important;
        font-size:13px !important;
        color:rgba(255,255,255,.88) !important;
        letter-spacing:.12em !important;
        text-transform:uppercase !important;
    }}
    {seps_css} div[data-testid="stMarkdownContainer"] {{
        margin:0 !important;
        padding-left:0 !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:nth-child({idx_sep_fija}) {{
        border-left-color:#7db8ff !important;
        background:linear-gradient(90deg, rgba(15,66,135,.42), rgba(255,255,255,.07)) !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:nth-child({idx_sep_movil}) {{
        border-left-color:#d8a4ff !important;
        background:linear-gradient(90deg, rgba(109,11,140,.34), rgba(255,255,255,.07)) !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:nth-child({idx_sep_factor}) {{
        border-left-color:#67e8f9 !important;
        background:linear-gradient(90deg, rgba(15,66,135,.28), rgba(109,11,140,.20)) !important;
    }}

    section[data-testid="stSidebar"] .stRadio > div > label {{
        min-height:42px !important;
        border-radius:11px !important;
        padding:9px 10px !important;
        margin:2px 0 !important;
        border:1px solid transparent !important;
        background:transparent !important;
        transition:background .16s ease, border-color .16s ease, transform .16s ease !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:hover {{
        background:rgba(255,255,255,.14) !important;
        border-color:rgba(255,255,255,.18) !important;
        transform:translateX(2px) !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
        background:linear-gradient(90deg, rgba(255,255,255,.22), rgba(255,255,255,.11)) !important;
        border-color:rgba(255,255,255,.30) !important;
        box-shadow:0 10px 24px rgba(15,23,42,.16) !important;
    }}
    {seps_css}:has(input:checked) div[data-testid="stMarkdownContainer"] p {{
        color:rgba(255,255,255,.66) !important;
        font-weight:950 !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label input {{
        display:none !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label div[data-testid="stMarkdownContainer"] p {{
        color:rgba(255,255,255,.86) !important;
        font-size:13px !important;
        font-weight:850 !important;
        line-height:1.1 !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) div[data-testid="stMarkdownContainer"] p {{
        color:#ffffff !important;
        font-weight:950 !important;
    }}
    section[data-testid="stSidebar"] .stExpander {{
        border:1px solid rgba(255,255,255,.20) !important;
        border-radius:12px !important;
        background:rgba(15,23,42,.12) !important;
    }}
    section[data-testid="stSidebar"] .stExpander p,
    section[data-testid="stSidebar"] .stExpander label,
    section[data-testid="stSidebar"] .stExpander span {{
        color:rgba(255,255,255,.86) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<nav class="dash-mini-rail" aria-label="Menu compacto">{_mini_nav_html}</nav>', unsafe_allow_html=True)

    _usuario_menu = st.session_state.get("usuario_logueado", "Usuario")
    st.sidebar.markdown(f"""
    <div class="dash-menu-shell">
        <div class="dash-window-dots">
            <span class="dash-dot-red"></span><span class="dash-dot-yellow"></span><span class="dash-dot-green"></span>
        </div>
        <div class="dash-brand">Teletalk</div>
        <div class="dash-subbrand">Dashboard Ejecutivo</div>
        <div class="dash-user-row">
            <div class="dash-user-avatar">{_html.escape(str(_usuario_menu)[:1].upper() or "U")}</div>
            <div>
                <div class="dash-user-name">{_html.escape(str(_usuario_menu))}</div>
                <div class="dash-user-role">Panel comercial</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.session_state.get("radio_unico") not in todas_opciones:
        st.session_state["radio_unico"] = st.session_state.get("ultima_seleccion", "Inicio: Reporte Comparativo FIJA")
    if st.session_state.get("radio_unico") in SEPARADORES:
        st.session_state["radio_unico"] = st.session_state.get("ultima_seleccion", "Inicio: Reporte Comparativo FIJA")
    seleccion = st.sidebar.radio("MENU DE REPORTES", todas_opciones, key="radio_unico", label_visibility="collapsed")

    if seleccion in SEPARADORES:
        seleccion = st.session_state.get("ultima_seleccion", "Inicio: Reporte Comparativo FIJA")
    else:
        st.session_state["ultima_seleccion"] = seleccion

    opcion        = seleccion if seleccion in OPCIONES_FIJA   else "Inicio: Reporte Comparativo FIJA"
    opcion_movil  = seleccion if seleccion in OPCIONES_MOVIL  else "Inicio: Reporte Comparativo MOVIL"
    opcion_factor = seleccion if seleccion in OPCIONES_FACTOR else "📊 Resumen NPN"
    seccion       = ("movil"  if seleccion in OPCIONES_MOVIL
                else "factor" if seleccion in OPCIONES_FACTOR
                else "fija")

    with st.sidebar.expander("🔍 Ver columnas de CSVs"):
        if st.button("Cargar columnas", key="btn_cargar_cols"):
            st.session_state["_cols_cargadas"] = True
        if st.session_state.get("_cols_cargadas", False):
            for nombre in ["FIJA_DC.csv","FIJA_TELETALK.csv","CLARO_DC_FIJA.csv","CLARO_DC_FIJA_SEGUNDA_CAIDA.csv","CLARO_TELETALK_FIJA.csv","CLARO_DC_MOVIL.csv","CLARO_TELETALK_MOVIL.csv"]:
                df_test = cargar_csv(nombre)
                if not df_test.empty: st.write(f"**{nombre}:**"); st.write(list(df_test.columns))
                else: st.write(f"**{nombre}:** ❌ no cargado")
        else:
            st.caption("Presiona el botón para cargar las columnas disponibles.")

    if seccion == "factor":

        if opcion_factor == "📊 Resumen NPN":
            set_bg(img_caratula)

            st.markdown("""
            <style>
            /* ── Header gerencial ── */
            .npn-header-wrap {
                display:flex; align-items:center; justify-content:space-between;
                background:linear-gradient(135deg,rgba(15,66,135,0.88) 0%,rgba(109,11,140,0.78) 100%);
                border-radius:14px; padding:20px 28px; margin-bottom:18px;
                box-shadow:0 4px 20px rgba(15,66,135,0.20);
                border:1px solid rgba(255,255,255,0.10);
            }
            .npn-header-left { text-align:left; }
            .npn-header-right { text-align:right; }
            .npn-kpi-label {
                font-size:10px; font-weight:800; color:rgba(255,255,255,0.65);
                letter-spacing:0.12em; text-transform:uppercase; margin-bottom:2px;
            }
            .npn-title {
                font-size:26px; font-weight:900; color:#fff;
                letter-spacing:0.06em; line-height:1.1;
            }
            .npn-sub {
                font-size:11px; color:rgba(255,255,255,0.60);
                letter-spacing:0.1em; text-transform:uppercase; margin-top:4px;
            }
            .npn-badge-dc {
                display:inline-block; background:rgba(15,66,135,0.75);
                border:1.5px solid #4a90d9; color:#fff; font-weight:700; font-size:11px;
                border-radius:16px; padding:3px 13px; margin:2px; letter-spacing:0.03em;
            }
            .npn-badge-tt {
                display:inline-block; background:rgba(109,11,140,0.75);
                border:1.5px solid #b05fd4; color:#fff; font-weight:700; font-size:11px;
                border-radius:16px; padding:3px 13px; margin:2px; letter-spacing:0.03em;
            }
            /* ── Filtros gerenciales ── */
            .npn-filtros-wrap {
                background:rgba(255,255,255,0.92); border-radius:10px;
                padding:12px 18px 8px 18px; margin-bottom:14px;
                box-shadow:0 2px 10px rgba(15,66,135,0.08);
                border:1px solid #dde4f0;
            }
            .npn-filtros-label {
                font-size:10px; font-weight:900; color:#0f4287;
                letter-spacing:0.12em; text-transform:uppercase; margin-bottom:6px;
            }
            /* ── KPI cards gerenciales ── */
            .npn-kpi-row { display:flex; gap:12px; margin:14px 0 6px 0; flex-wrap:wrap; }
            .npn-kpi-card {
                flex:1; min-width:140px;
                background:rgba(255,255,255,0.95); border-radius:12px;
                padding:16px 18px; text-align:center;
                box-shadow:0 3px 14px rgba(0,0,0,0.08);
                border-top:4px solid #0f4287;
            }
            .npn-kpi-card-label {
                font-size:9px; font-weight:800; color:#6b7280;
                letter-spacing:0.12em; text-transform:uppercase; margin-bottom:6px;
            }
            .npn-kpi-card-val {
                font-size:28px; font-weight:900; color:#0f4287; line-height:1;
            }
            .npn-kpi-card-sub {
                font-size:9px; color:#9ca3af; margin-top:5px; font-style:italic;
            }
            .npn-registros {
                font-size:12px; color:#374151; font-weight:600;
                background:rgba(255,255,255,0.85); border-radius:8px;
                padding:6px 14px; display:inline-block; margin-bottom:10px;
                border-left:3px solid #0f4287;
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) {
                background:rgba(255,255,255,0.74);
                border:1px solid rgba(15,66,135,0.12);
                border-radius:14px;
                padding:16px 18px 12px 18px;
                margin:4px 0 14px 0;
                box-shadow:0 14px 34px rgba(15,23,42,0.08);
                backdrop-filter:blur(8px);
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) label {
                color:#334155 !important;
                font-size:12px !important;
                font-weight:800 !important;
                letter-spacing:.02em !important;
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) [data-baseweb="select"] > div {
                min-height:42px;
                border-radius:10px !important;
                background:linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%) !important;
                border:1px solid rgba(148,163,184,0.42) !important;
                box-shadow:inset 0 1px 0 rgba(255,255,255,0.82), 0 4px 12px rgba(15,23,42,0.05);
                transition:border-color .18s ease, box-shadow .18s ease;
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) [data-baseweb="select"] > div:hover {
                border-color:#0f4287 !important;
                box-shadow:0 0 0 3px rgba(15,66,135,0.10), 0 8px 18px rgba(15,23,42,0.08);
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) [data-baseweb="tag"] {
                background:#ff4b4b !important;
                color:#fff !important;
                border-radius:8px !important;
                font-weight:900 !important;
                box-shadow:0 4px 10px rgba(255,75,75,0.20);
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) [data-baseweb="tag"] span {
                color:#fff !important;
            }
            div[data-testid="stVerticalBlock"]:has(div.npn-filter-anchor) svg {
                color:#334155;
            }
            </style>

            <div class="npn-header-wrap">
                <div class="npn-header-left">
                    <div class="npn-kpi-label">Módulo Ejecutivo</div>
                    <div class="npn-title">FACTOR NPN</div>
                    <div class="npn-sub">Reporte Consolidado de Ventas</div>
                </div>
                <div class="npn-header-right">
                    <span class="npn-badge-dc">📡 D&amp;C Digital Group</span><br>
                    <span class="npn-badge-tt" style="margin-top:5px;display:inline-block;">📱 Teletalk Contact Center</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # NPN trabaja con CSV locales. El API no entra en esta logica.
            _ruta_dvz = os.path.join(DATA_DIR, "DVZ.csv")
            _mtime = os.path.getmtime(_ruta_dvz) if os.path.exists(_ruta_dvz) else None
            _df_npn = _leer_csv_npn_local_cacheado("DVZ.csv", _mtime)

            # Invalidate caches if DVZ file changed since last load
            try:
                if _mtime is not None:
                    if st.session_state.get("_dvz_mtime") != _mtime:
                        for _k in ["npn_fija_cache", "npn_movil_cache", "dfg_det_cache"]:
                            if _k in st.session_state:
                                del st.session_state[_k]
                    st.session_state["_dvz_mtime"] = _mtime
            except Exception:
                pass

            if _df_npn.empty:
                st.warning("No se encontró el archivo DVZ.csv. Verifica que esté en la carpeta de datos.")
            else:
                _df_npn = _df_npn.copy()
                _df_npn.columns = _df_npn.columns.str.strip()

                # Detectar columnas exactas
                _col_tipo  = next((c for c in _df_npn.columns if c.strip().lower() == "tipo producto"), None)
                _col_clip  = next((c for c in _df_npn.columns if c.strip().lower() == "datos adicionales - clip"), None)
                _col_sup   = encontrar_columna(_df_npn, ["Datos Adicionales - Supervisor", "Datos adicionales - Supervisor", "SUPERVISOR", "Supervisor", "supervisor"])
                _col_finst = encontrar_columna(_df_npn, ["Back Office - Fecha Instalacion", "Back Office - Fecha Instalación", "FECHA INSTALACION", "Fecha Instalacion", "Fecha Instalación"])
                _col_fvta_r   = next((c for c in _df_npn.columns if c.strip().upper() in
                            ["FECHA DE VENTA","Fecha de Venta","Fecha Venta","FECHA VENTA"]), None)
                _col_sot_r    = next((c for c in _df_npn.columns if c.strip().lower() == "back office - sot"), None)
                _col_tipis = encontrar_columna(_df_npn, [
                    "Estados - Venta Especificacion", "Estados - Venta Especificación",
                    "TIPIS", "Tipificacion", "Tipificación", "Estado Venta", "ESTADO VENTA"
                ])
                _col_ext_npn = encontrar_columna(_df_npn, [
                    "EXTENSION DEL USUARIO", "EXTENSIÓN DEL USUARIO", "Extension del usuario",
                    "EXTENSION", "Extension", "USUARIO", "Usuario"
                ])
                _col_asesor_npn = encontrar_columna(_df_npn, [
                    "USUARIO", "Usuario", "ASESOR", "Asesor", "VENDEDOR", "Vendedor",
                    "EJECUTIVO", "Ejecutivo", "CREADOR", "Creador"
                ])
                _col_sec_npn = next((c for c in _df_npn.columns if c.strip().lower() == "datos adicionales - sec"), None)

                _col_tipo_r = _col_tipo
                _df_npn["_FVTA_DT"] = pd.to_datetime(_df_npn[_col_fvta_r], errors="coerce", dayfirst=True) if _col_fvta_r else pd.Series(pd.NaT, index=_df_npn.index)
                _df_npn["_FINST_DT"] = pd.to_datetime(_df_npn[_col_finst], errors="coerce", dayfirst=True) if _col_finst else pd.Series(pd.NaT, index=_df_npn.index)

                def _meses_desde_fecha(serie):
                    _fechas = _parse_fecha_movil_robusta(serie)
                    _fechas = pd.to_datetime(_fechas, errors="coerce", dayfirst=True)
                    _fechas = _fechas.dropna()
                    if _fechas.empty:
                        return []
                    _periodos = _fechas.dt.to_period("M")
                    _periodos = _periodos[_periodos <= _periodo_ultimo_mes_cerrado()]
                    _periodos = _periodos.drop_duplicates().sort_values()
                    return [f"{MESES_ES[p.month].capitalize()} {p.year}" for p in _periodos]

                _opts_serv = ["Todos"]
                if _col_tipo:
                    _opts_serv += sorted(_df_npn[_col_tipo].fillna("").astype(str).str.strip().replace("", "").loc[lambda s: s != ""].unique().tolist())
                _opts_canal_raw = []
                if _col_clip:
                    _opts_canal_raw = sorted(_df_npn[_col_clip].fillna("").astype(str).str.strip().loc[lambda s: s != ""].unique().tolist())
                _opts_canal_display = []
                for _c in _opts_canal_raw:
                    _cu = str(_c).strip().upper()
                    if _cu == "TELETALK":
                        _opts_canal_display.append("Teletalk")
                    elif _cu == "D&C":
                        _opts_canal_display.append("D&C")
                    else:
                        _opts_canal_display.append(str(_c).strip())
                _opts_canal_display = sorted(set(_opts_canal_display), key=lambda x: {"D&C": 0, "Teletalk": 1}.get(x, 9)) or ["D&C", "Teletalk"]
                _opts_fvta = _meses_desde_fecha(_df_npn.get("_FVTA_DT", _df_npn.get("FECHA DE VENTA", pd.Series([], dtype="object"))))
                _opts_finst = _meses_desde_fecha(_df_npn.get("_FINST_DT", _df_npn.get("FECHA INSTALACION", pd.Series([], dtype="object"))))
                _opts_sup = []
                if _col_sup:
                    _opts_sup = sorted(_df_npn[_col_sup].fillna("").astype(str).str.strip().loc[lambda s: s != ""].unique().tolist())
                _opts_tipis = []
                if _col_tipis:
                    _opts_tipis = sorted(_df_npn[_col_tipis].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación").unique().tolist())
                try:
                    _opts_tipis = sorted(set(_opts_tipis + [t for t in obtener_tipificaciones_solo_movil_general() if t != "Todos"]))
                except Exception:
                    pass
                _opts_cola = ["EXTERNO"]
                try:
                    _dot = cargar_dotacion()
                    if _dot:
                        _opts_cola = sorted(set(["EXTERNO"] + [str(v).strip() for v in _dot.values() if str(v).strip()]))
                except Exception:
                    pass

                _f_fvta = []  # NPN ya no filtra por Fecha de Venta.
                with st.container():
                    st.markdown('<div class="npn-filter-anchor"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="npn-filtros-label">Filtros NPN</div>', unsafe_allow_html=True)
                    _fc1, _fc2, _fc3 = st.columns(3)
                    with _fc1:
                        _f_serv  = st.selectbox("Servicio", _opts_serv, key="npn_serv")
                    with _fc2:
                        _f_canal_sel = st.multiselect("Canal", _opts_canal_display, default=[], key="npn_canal_multi", placeholder="Todos los canales")
                    with _fc3:
                        _f_finst = st.multiselect("Fecha de Instalación", _opts_finst, default=[], placeholder="Todas las fechas", key="npn_finst")
                    _f_estado_pago = []  # NPN no usa filtro visible de Estado de Pago.
                    _fc4, _fc5, _fc6 = st.columns(3)
                    with _fc4:
                        _f_sup = st.multiselect("Supervisor", _opts_sup, default=[], placeholder="Todos los supervisores", key="npn_sup")
                    with _fc5:
                        _f_tipis = st.multiselect("Tipificación", _opts_tipis, default=[], key="npn_tipificacion", placeholder="Todas las tipificaciones")
                    with _fc6:
                        _f_cola = st.selectbox("Cola", ["Todos"] + _opts_cola, key="npn_cola")
                _f_canal = _f_canal_sel[0] if len(_f_canal_sel) == 1 else "Todos"

                # ── Aplicar filtros sobre DVZ crudo (para el contador de registros) ──
                _dff = _df_npn.copy()
                if _f_serv != "Todos" and _col_tipo:
                    _dff = _dff[_dff[_col_tipo].fillna("").astype(str).str.strip().str.upper() == _f_serv.upper()]
                if _f_canal_sel and _col_clip:
                    _dff = _dff[_dff[_col_clip].fillna("").astype(str).str.strip().str.upper().isin([str(c).upper() for c in _f_canal_sel])]
                if _f_fvta:
                    _dff["_MV"] = _dff["_FVTA_DT"].apply(
                        lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                    _dff = _dff[_dff["_MV"].isin(_f_fvta)]
                if _f_finst:
                    _dff["_MI"] = _dff["_FINST_DT"].apply(
                        lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                    _dff = _dff[_dff["_MI"].isin(_f_finst)]
                if _f_sup and _col_sup:
                    _dff = _dff[_dff[_col_sup].fillna("").astype(str).str.strip().isin(_f_sup)]
                if _f_tipis and _col_tipis:
                    _tip_raw = _dff[_col_tipis].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                    _dff = _dff[_tip_raw.isin([str(t).strip() for t in _f_tipis])]
                if _f_cola != "Todos" and _col_ext_npn:
                    _cola_raw = _data_loader._agregar_cola_por_extension(_dff, _col_ext_npn)
                    _dff = _dff[_cola_raw.fillna("EXTERNO").astype(str).str.strip() == _f_cola]

                st.markdown(f'<div class="npn-registros">📋 {len(_dff):,} registros con los filtros seleccionados</div>', unsafe_allow_html=True)
                # ── Cargar datos procesados con Estado Pago real (cacheados) ─
                # Versionar cache: fuerza reconstrucción cuando agregamos columnas/filtros nuevos.
                _npn_schema_version = "npn_filters_v6_mes_cerrado"
                if st.session_state.get("_npn_schema_version") != _npn_schema_version:
                    for _k in ["npn_fija_cache", "npn_movil_cache"]:
                        if _k in st.session_state:
                            del st.session_state[_k]
                    st.session_state["_npn_schema_version"] = _npn_schema_version

                # Botón para reconstruir cachés desde DVZ (útil para validar cambios inmediatamente)
                if st.button("🔁 Reconstruir caches DVZ y recargar", key="btn_reconstruir_dvz"):
                    for _k in ["npn_fija_cache", "npn_movil_cache", "dfg_det_cache", "_dvz_mtime"]:
                        if _k in st.session_state:
                            del st.session_state[_k]
                    st.experimental_rerun()

                # ── Cargar datos procesados con Estado Pago real (cacheados) ─
                # Se guarda en session_state para no recalcular al cambiar filtros
                if "npn_fija_cache" not in st.session_state:
                    if True:
                        # Construir cache FIJA a partir del DVZ crudo (fuente canónica) y
                        # enriquecer con Estado Pago / COMISION desde el detalle construido
                        try:
                            # Subconjunto FIJA del DVZ
                            if _col_tipo:
                                _dvz_fija = _df_npn[_df_npn[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "FIJA"].copy()
                            else:
                                _dvz_fija = _df_npn.copy()

                            # Detectar columna SOT en DVZ
                            _col_sot_dvz = next((c for c in _dvz_fija.columns if c.strip().lower() == "back office - sot"), None)

                            # Base mínima desde DVZ con las columnas que usa NPN
                            _tmp_fija = pd.DataFrame(index=_dvz_fija.index)
                            if _col_sot_dvz:
                                _tmp_fija["SOT"] = _dvz_fija[_col_sot_dvz].astype(str).str.strip().str.replace(r"\.0$","", regex=True)
                            else:
                                _tmp_fija["SOT"] = ""
                            _tmp_fija["Canal"] = _dvz_fija[_col_clip].astype(str).str.strip() if _col_clip else ""
                            _tmp_fija["SUPERVISOR"] = _dvz_fija[_col_sup].astype(str).str.strip() if _col_sup else ""
                            _tmp_fija["ASESOR"] = _dvz_fija[_col_asesor_npn].fillna("Sin Asesor").astype(str).str.strip().replace("", "Sin Asesor") if _col_asesor_npn else "Sin Asesor"
                            _tmp_fija["TIPIS"] = _dvz_fija[_col_tipis].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación") if _col_tipis else "Sin Tipificación"
                            _tmp_fija["COLA"] = _data_loader._agregar_cola_por_extension(_dvz_fija, _col_ext_npn) if _col_ext_npn else "EXTERNO"
                            _tmp_fija["FECHA DE VENTA"] = _dvz_fija["_FVTA_DT"].dt.strftime("%d/%m/%Y").fillna("")
                            _tmp_fija["FECHA INSTALACION"] = _dvz_fija["_FINST_DT"].dt.strftime("%d/%m/%Y").fillna("")
                            # Placeholder columns to be filled from detalle (si existe)
                            _tmp_fija["COMISION"] = ""
                            _tmp_fija["Estado Pago"] = ""

                            # Construir detalle tradicional (usa archivos CLARO/DEVELZ) para obtener Estado Pago/COMISION
                            _detalle = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                            # Normalizar SOT en detalle para merge
                            if "SOT" in _detalle.columns:
                                _detalle["SOT"] = _detalle["SOT"].astype(str).str.strip().str.replace(r"\.0$","", regex=True)

                            # Merge left: conservar todos los SOT del DVZ y traer Estado Pago/COMISION cuando haya coincidencia
                            if "SOT" in _detalle.columns:
                                _merged = _tmp_fija.merge(
                                    _detalle[[c for c in ["SOT", "COMISION", "Estado Pago", "TIPIS", "COLA", "ASESOR", "SUPERVISOR"] if c in _detalle.columns]].drop_duplicates(subset=["SOT"]),
                                    on="SOT", how="left", suffixes=("","_det")
                                )
                                # Preferir valores del detalle cuando existan
                                if "COMISION_det" in _merged.columns:
                                    _merged["COMISION"] = _merged["COMISION_det"].fillna(_merged["COMISION"]) 
                                    _merged = _merged.drop(columns=["COMISION_det"])
                                if "Estado Pago_det" in _merged.columns:
                                    _merged["Estado Pago"] = _merged["Estado Pago_det"].fillna(_merged["Estado Pago"]) 
                                    _merged = _merged.drop(columns=["Estado Pago_det"])
                                if "TIPIS_det" in _merged.columns:
                                    _merged["TIPIS"] = _merged["TIPIS_det"].fillna(_merged["TIPIS"])
                                    _merged = _merged.drop(columns=["TIPIS_det"])
                                if "COLA_det" in _merged.columns:
                                    _merged["COLA"] = _merged["COLA_det"].fillna(_merged["COLA"])
                                    _merged = _merged.drop(columns=["COLA_det"])
                                if "ASESOR_det" in _merged.columns:
                                    _merged["ASESOR"] = _merged["ASESOR_det"].fillna(_merged["ASESOR"])
                                    _merged = _merged.drop(columns=["ASESOR_det"])
                                if "SUPERVISOR_det" in _merged.columns:
                                    _merged["SUPERVISOR"] = _merged["SUPERVISOR_det"].fillna(_merged["SUPERVISOR"])
                                    _merged = _merged.drop(columns=["SUPERVISOR_det"])
                            else:
                                _merged = _tmp_fija

                            _merged = _merged.reset_index(drop=True)
                            _merged["_TIPO_NPN"] = "FIJA"
                            st.session_state["npn_fija_cache"] = _merged
                        except Exception:
                            # Fallback al comportamiento previo si algo falla
                            _tmp = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                            _tmp["_TIPO_NPN"] = "FIJA"
                            st.session_state["npn_fija_cache"] = _tmp
                if "npn_movil_cache" not in st.session_state:
                    if True:
                        try:
                            # Subconjunto MOVIL del DVZ
                            if _col_tipo:
                                _dvz_movil = _df_npn[_df_npn[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"].copy()
                            else:
                                _dvz_movil = _df_npn.copy()

                            # Si el API/DVZ no trae MOVIL en producto, NPN debe seguir cuadrando
                            # con Detalle Movil General. En ese caso usamos directamente el detalle
                            # movil como cache NPN para no perder ventas netas.
                            if _dvz_movil.empty:
                                _detalle_mov_full = construir_resumen_movil_general("Todos los meses").copy()
                                if "COMISION" not in _detalle_mov_full.columns and "COMISION_REAL" in _detalle_mov_full.columns:
                                    _detalle_mov_full["COMISION"] = _detalle_mov_full["COMISION_REAL"]
                                if "FECHA INSTALACION" not in _detalle_mov_full.columns:
                                    if "_FECHA_INSTALACION_DT" in _detalle_mov_full.columns:
                                        _detalle_mov_full["FECHA INSTALACION"] = pd.to_datetime(_detalle_mov_full["_FECHA_INSTALACION_DT"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
                                    else:
                                        _detalle_mov_full["FECHA INSTALACION"] = ""
                                if "SOT" not in _detalle_mov_full.columns:
                                    _detalle_mov_full["SOT"] = ""
                                if "SEC" not in _detalle_mov_full.columns:
                                    _detalle_mov_full["SEC"] = ""
                                _detalle_mov_full["_TIPO_NPN"] = "MOVIL"
                                st.session_state["npn_movil_cache"] = _detalle_mov_full
                                raise StopIteration

                            # Normalizar documento en DVZ usando helper
                            _doc_series = _obtener_documento_develz(_dvz_movil)

                            _tmp_movil = pd.DataFrame(index=_dvz_movil.index)
                            _tmp_movil["DOCUMENTO_KEY"] = _doc_series.fillna("").astype(str).str.strip()
                            _tmp_movil["SEC"] = _dvz_movil[_col_sec_npn].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True) if _col_sec_npn else ""
                            _tmp_movil["Canal"] = _dvz_movil[_col_clip].astype(str).str.strip() if _col_clip else ""
                            _tmp_movil["SUPERVISOR"] = _dvz_movil[_col_sup].astype(str).str.strip() if _col_sup else ""
                            _tmp_movil["ASESOR"] = _dvz_movil[_col_asesor_npn].fillna("Sin Asesor").astype(str).str.strip().replace("", "Sin Asesor") if _col_asesor_npn else "Sin Asesor"
                            _tmp_movil["TIPIS"] = _dvz_movil[_col_tipis].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación") if _col_tipis else "Sin Tipificación"
                            _tmp_movil["COLA"] = _data_loader._agregar_cola_por_extension(_dvz_movil, _col_ext_npn) if _col_ext_npn else "EXTERNO"
                            _tmp_movil["FECHA DE VENTA"] = _dvz_movil["_FVTA_DT"].dt.strftime("%d/%m/%Y").fillna("")
                            _tmp_movil["FECHA INSTALACION"] = _dvz_movil["_FINST_DT"].dt.strftime("%d/%m/%Y").fillna("")
                            _tmp_movil["COMISION"] = ""
                            _tmp_movil["Estado Pago"] = ""

                            # Obtener detalle MOVIL (con COMISION / Estado Pago) y merge por DOCUMENTO_KEY
                            _detalle_mov = construir_resumen_movil_general("Todos los meses")
                            if "DOCUMENTO_KEY" in _detalle_mov.columns:
                                _detalle_mov["DOCUMENTO_KEY"] = _detalle_mov["DOCUMENTO_KEY"].astype(str).str.strip()
                                _merged_m = _tmp_movil.merge(
                                    _detalle_mov[[c for c in ["DOCUMENTO_KEY", "COMISION", "Estado Pago", "TIPIS", "COLA", "ASESOR", "SUPERVISOR", "_FECHA_INSTALACION_DT"] if c in _detalle_mov.columns]].drop_duplicates(subset=["DOCUMENTO_KEY"]),
                                    on="DOCUMENTO_KEY", how="left", suffixes=("","_det")
                                )
                                if "COMISION_det" in _merged_m.columns:
                                    _merged_m["COMISION"] = _merged_m["COMISION_det"].fillna(_merged_m["COMISION"]) 
                                    _merged_m = _merged_m.drop(columns=["COMISION_det"])
                                if "Estado Pago_det" in _merged_m.columns:
                                    _merged_m["Estado Pago"] = _merged_m["Estado Pago_det"].fillna(_merged_m["Estado Pago"]) 
                                    _merged_m = _merged_m.drop(columns=["Estado Pago_det"])
                                if "TIPIS_det" in _merged_m.columns:
                                    _merged_m["TIPIS"] = _merged_m["TIPIS_det"].fillna(_merged_m["TIPIS"])
                                    _merged_m = _merged_m.drop(columns=["TIPIS_det"])
                                if "COLA_det" in _merged_m.columns:
                                    _merged_m["COLA"] = _merged_m["COLA_det"].fillna(_merged_m["COLA"])
                                    _merged_m = _merged_m.drop(columns=["COLA_det"])
                                if "ASESOR_det" in _merged_m.columns:
                                    _merged_m["ASESOR"] = _merged_m["ASESOR_det"].fillna(_merged_m["ASESOR"])
                                    _merged_m = _merged_m.drop(columns=["ASESOR_det"])
                                if "SUPERVISOR_det" in _merged_m.columns:
                                    _merged_m["SUPERVISOR"] = _merged_m["SUPERVISOR_det"].fillna(_merged_m["SUPERVISOR"])
                                    _merged_m = _merged_m.drop(columns=["SUPERVISOR_det"])
                                if "_FECHA_INSTALACION_DT" in _merged_m.columns:
                                    _merged_m["FECHA INSTALACION"] = pd.to_datetime(_merged_m["_FECHA_INSTALACION_DT"], errors="coerce").dt.strftime("%d/%m/%Y").fillna(_merged_m["FECHA INSTALACION"])
                            else:
                                _merged_m = _tmp_movil

                            _merged_m = _merged_m.reset_index(drop=True)
                            _merged_m["_TIPO_NPN"] = "MOVIL"
                            _detalle_mov_full_cmp = construir_resumen_movil_general("Todos los meses").copy()
                            _pag_merged = int((_merged_m.get("Estado Pago", pd.Series([], dtype="object")).fillna("").astype(str).str.upper() == "PAGADA").sum())
                            _pag_detail = int((_detalle_mov_full_cmp.get("Estado Pago", pd.Series([], dtype="object")).fillna("").astype(str).str.upper() == "PAGADA").sum())
                            if _pag_detail > _pag_merged:
                                if "COMISION" not in _detalle_mov_full_cmp.columns and "COMISION_REAL" in _detalle_mov_full_cmp.columns:
                                    _detalle_mov_full_cmp["COMISION"] = _detalle_mov_full_cmp["COMISION_REAL"]
                                if "FECHA INSTALACION" not in _detalle_mov_full_cmp.columns:
                                    if "_FECHA_INSTALACION_DT" in _detalle_mov_full_cmp.columns:
                                        _detalle_mov_full_cmp["FECHA INSTALACION"] = pd.to_datetime(_detalle_mov_full_cmp["_FECHA_INSTALACION_DT"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
                                    else:
                                        _detalle_mov_full_cmp["FECHA INSTALACION"] = ""
                                if "SOT" not in _detalle_mov_full_cmp.columns:
                                    _detalle_mov_full_cmp["SOT"] = ""
                                if "SEC" not in _detalle_mov_full_cmp.columns:
                                    _detalle_mov_full_cmp["SEC"] = ""
                                _detalle_mov_full_cmp["_TIPO_NPN"] = "MOVIL"
                                _merged_m = _detalle_mov_full_cmp
                            st.session_state["npn_movil_cache"] = _merged_m
                        except StopIteration:
                            pass
                        except Exception:
                            _tmp2 = construir_resumen_movil_general("Todos los meses")
                            _tmp2["_TIPO_NPN"] = "MOVIL"
                            st.session_state["npn_movil_cache"] = _tmp2

                if True:
                    _df_fija_npn  = st.session_state["npn_fija_cache"].copy()
                    _df_movil_npn = st.session_state["npn_movil_cache"].copy()

                    # SOT solo existe en fija; móvil no lo tiene → rellenar vacío
                    if "SOT" not in _df_movil_npn.columns:
                        _df_movil_npn["SOT"] = ""

                    # Columnas comunes
                    _cols_comun = ["Canal", "SUPERVISOR", "ASESOR", "TIPIS", "COLA", "FECHA DE VENTA", "FECHA INSTALACION",
                                   "SOT", "SEC", "COMISION", "Estado Pago", "DOCUMENTO_KEY", "_TIPO_NPN"]
                    for _c in _cols_comun:
                        if _c not in _df_fija_npn.columns:  _df_fija_npn[_c]  = ""
                        if _c not in _df_movil_npn.columns: _df_movil_npn[_c] = ""

                    _df_npn_proc = pd.concat(
                        [_df_fija_npn[_cols_comun], _df_movil_npn[_cols_comun]],
                        ignore_index=True
                    )

                    # Parsear fecha de venta
                    _df_npn_proc["_FVTA_PROC"] = pd.to_datetime(
                        _df_npn_proc["FECHA DE VENTA"], errors="coerce", dayfirst=True)
                    _df_npn_proc["_MES_VENTA"] = _df_npn_proc["_FVTA_PROC"].apply(
                        lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")

                    # ── Fecha Instalación: usar Back Office - Fecha Instalacion del DVZ crudo ──
                    # El filtro _f_finst usa opciones generadas desde _df_npn["_FINST_DT"]
                    # (que viene de "Back Office - Fecha Instalacion"), así que _MES_INST
                    # en proc debe venir de la misma fuente para que el filtro matchee.
                    # Construimos un mapa SOT/SEC → mes instalación desde el DVZ crudo.
                    _col_sot_dvz_inst = next((c for c in _df_npn.columns if c.strip().lower() == "back office - sot"), None)
                    _col_sec_dvz_inst = next((c for c in _df_npn.columns if c.strip().lower() == "datos adicionales - sec"), None)
                    _col_tipo_dvz     = _col_tipo  # ya detectado arriba

                    # Mapa SOT → _MES_INST (FIJA)
                    _mapa_sot_inst = {}
                    if _col_sot_dvz_inst and _col_finst:
                        _dvz_fija_inst = _df_npn[
                            _df_npn[_col_tipo_dvz].fillna("").astype(str).str.strip().str.upper() == "FIJA"
                        ].copy() if _col_tipo_dvz else _df_npn.copy()
                        _dvz_fija_inst["_SOT_K"] = _dvz_fija_inst[_col_sot_dvz_inst].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
                        _dvz_fija_inst["_INST_MES"] = _dvz_fija_inst["_FINST_DT"].apply(
                            lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                        _mapa_sot_inst = dict(zip(_dvz_fija_inst["_SOT_K"], _dvz_fija_inst["_INST_MES"]))

                    # Mapa SEC → _MES_INST (MÓVIL)
                    _mapa_sec_inst = {}
                    if _col_sec_dvz_inst and _col_finst:
                        _dvz_movil_inst = _df_npn[
                            _df_npn[_col_tipo_dvz].fillna("").astype(str).str.strip().str.upper() == "MOVIL"
                        ].copy() if _col_tipo_dvz else _df_npn.copy()
                        _dvz_movil_inst["_SEC_K"] = _dvz_movil_inst[_col_sec_dvz_inst].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
                        _dvz_movil_inst["_INST_MES"] = _dvz_movil_inst["_FINST_DT"].apply(
                            lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                        _mapa_sec_inst = dict(zip(_dvz_movil_inst["_SEC_K"], _dvz_movil_inst["_INST_MES"]))

                    # Asignar _MES_INST en proc usando los mapas del DVZ
                    def _get_mes_inst_proc(row):
                        if row["_TIPO_NPN"] == "FIJA":
                            sot = str(row.get("SOT","")).strip().replace(".0","") if row.get("SOT","") else ""
                            return _mapa_sot_inst.get(sot, "")
                        else:
                            # Para móvil no tenemos columna SEC en proc directamente
                            # Fallback: usar FECHA INSTALACION de proc
                            try:
                                d = pd.to_datetime(row["FECHA INSTALACION"], errors="coerce", dayfirst=True)
                                return f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else ""
                            except:
                                return ""

                    _df_npn_proc["_MES_INST"] = _df_npn_proc.apply(_get_mes_inst_proc, axis=1)

                    # ── Aplicar los mismos filtros sobre df procesado ────
                    _dfp = _df_npn_proc.copy()
                    if _f_serv != "Todos":
                        _dfp = _dfp[_dfp["_TIPO_NPN"].str.upper() == _f_serv.upper()]
                    if _f_canal_sel:
                        _dfp = _dfp[_dfp["Canal"].fillna("").astype(str).str.strip().str.upper().isin([str(c).upper() for c in _f_canal_sel])]
                    if _f_fvta:
                        _dfp = _dfp[_dfp["_MES_VENTA"].isin(_f_fvta)]
                    if _f_finst:
                        _dfp = _dfp[_dfp["_MES_INST"].isin(_f_finst)]
                    if _f_sup:
                        _dfp = _dfp[_dfp["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)]
                    if _f_estado_pago and "Estado Pago" in _dfp.columns:
                        _dfp = _dfp[_dfp["Estado Pago"].fillna("NO PAGADA").astype(str).str.strip().str.upper().isin([str(e).upper() for e in _f_estado_pago])]
                    if _f_tipis and "TIPIS" in _dfp.columns:
                        _tip_proc = _dfp["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                        _dfp = _dfp[_tip_proc.isin([str(t).strip() for t in _f_tipis])]
                    if _f_cola != "Todos" and "COLA" in _dfp.columns:
                        _dfp = _dfp[_dfp["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola]

                    # ── Pagadas ───────────────────────────────────────────
                    # Modo historico NPN: en Todos mantiene base FIJA; en MOVIL usa MOVIL.
                    _dfp_kpi = _dfp.copy()
                    if _f_serv == "Todos":
                        _dfp_kpi = _dfp_kpi[_dfp_kpi["_TIPO_NPN"].fillna("").astype(str).str.upper() == "FIJA"].copy()

                    _mask_pag = _dfp_kpi["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                    _ventas_netas_total = int(_mask_pag.sum())
                    _dfp_pag = _dfp_kpi[_mask_pag].copy()

                    # ── Comisión Total ────────────────────────────────────
                    _comision_total_npn = float(
                        pd.to_numeric(_dfp_pag["COMISION"], errors="coerce").fillna(0).sum())

                    # ── % TV: igual que Detalle Fija General ─────────────
                    # calcular_pct_tv_fija necesita columnas "Estado Pago" y "SOT"
                    # _dfp_pag ya tiene ambas (SOT vacío en móvil → no suma TV, correcto)
                    _pct_tv_npn, _ventas_tv_npn, _ = calcular_pct_tv_fija(_dfp_pag)

                    # ── KPI NETAS 3 MESES ────────────────────────────────────────────
                    # FIJA : cruce por SOT  → "Back Office - Sot" (DVZ) vs "SOT" (CLARO_DC_FIJA_SEGUNDA_CAIDA)
                    # MÓVIL: cruce por SEC  → "Datos Adicionales - Sec" (DVZ) vs "SEC" (CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA)
                    # Los filtros de Fecha de Venta / Fecha Instalación se aplican sobre el DVZ.
                    # IMPORTANTE: DVZ guarda SOT/SEC como float (ej. "88597464.0") → se normaliza a entero string.
                    _comision_3m = 0.0   # comisión acumulada de 2da etapa/caída
                    _comision_6m = 0.0   # comisión acumulada de 3ra caída

                    def _norm_id(serie):
                        """Normaliza IDs numéricos: '88597464.0' → '88597464', quita blancos y nulos."""
                        s = serie.dropna().astype(str).str.strip()
                        s = s.str.replace(r"\.0$", "", regex=True)  # quitar .0 final de floats
                        return s[s.str.len() > 0]

                    _netas_3m_fija  = 0
                    _netas_3m_movil = 0

                    # Detectar columnas SOT y SEC en el DVZ (case-insensitive)
                    _col_sot_dvz = next(
                        (c for c in _df_npn.columns if c.strip().lower() == "back office - sot"), None)
                    _col_sec_dvz = next(
                        (c for c in _df_npn.columns if c.strip().lower() == "datos adicionales - sec"), None)

                    # Aplicar filtros activos sobre el DVZ (usa _df_npn que ya tiene _FVTA_DT y _FINST_DT)
                    _dvz_f = _df_npn.copy()
                    if _col_tipo and _f_serv != "Todos":
                        _dvz_f = _dvz_f[_dvz_f[_col_tipo].fillna("").astype(str).str.strip().str.upper() == _f_serv.upper()]
                    if _col_clip and _f_canal_sel:
                        _dvz_f = _dvz_f[_dvz_f[_col_clip].fillna("").astype(str).str.strip().str.upper().isin([str(c).upper() for c in _f_canal_sel])]
                    if _f_fvta:
                        _dvz_f["_MV2"] = _dvz_f["_FVTA_DT"].apply(
                            lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                        _dvz_f = _dvz_f[_dvz_f["_MV2"].isin(_f_fvta)]
                    if _f_finst:
                        _dvz_f["_MI2"] = _dvz_f["_FINST_DT"].apply(
                            lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                        _dvz_f = _dvz_f[_dvz_f["_MI2"].isin(_f_finst)]
                    if _f_sup and _col_sup:
                        _dvz_f = _dvz_f[_dvz_f[_col_sup].fillna("").astype(str).str.strip().isin(_f_sup)]
                    if _f_tipis and _col_tipis:
                        _tip_dvz = _dvz_f[_col_tipis].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                        _dvz_f = _dvz_f[_tip_dvz.isin([str(t).strip() for t in _f_tipis])]
                    if _f_cola != "Todos" and _col_ext_npn:
                        _cola_dvz = _data_loader._agregar_cola_por_extension(_dvz_f, _col_ext_npn)
                        _dvz_f = _dvz_f[_cola_dvz.fillna("EXTERNO").astype(str).str.strip() == _f_cola]
                    if _f_estado_pago:
                        # Hacer que Estado de Pago también afecte los cruces 3M/6M.
                        # FIJA cruza por SOT; MÓVIL cruza por documento cuando la columna existe en DVZ.
                        _estado_base = _dfp.copy()
                        _sots_estado = set()
                        if "SOT" in _estado_base.columns:
                            _sots_estado = set(_estado_base[_estado_base["_TIPO_NPN"].fillna("").astype(str).str.upper() == "FIJA"]["SOT"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True))
                            _sots_estado.discard("")
                        _docs_estado = set()
                        if "DOCUMENTO_KEY" in _estado_base.columns:
                            _docs_estado = set(_estado_base[_estado_base["_TIPO_NPN"].fillna("").astype(str).str.upper() == "MOVIL"]["DOCUMENTO_KEY"].fillna("").astype(str).str.strip())
                            _docs_estado.discard("")
                        _mask_estado_dvz = pd.Series([False] * len(_dvz_f), index=_dvz_f.index)
                        if _col_sot_dvz and _sots_estado:
                            _sot_dvz_estado = _dvz_f[_col_sot_dvz].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                            _mask_estado_dvz |= _sot_dvz_estado.isin(_sots_estado)
                        if _docs_estado:
                            try:
                                _doc_dvz_estado = _obtener_documento_develz(_dvz_f).fillna("").astype(str).str.strip()
                                _mask_estado_dvz |= _doc_dvz_estado.isin(_docs_estado)
                            except Exception:
                                pass
                        _dvz_f = _dvz_f[_mask_estado_dvz].copy()

                    # ── FIJA: SOTs del DVZ → cruce con CLARO_DC_FIJA_SEGUNDA_CAIDA ──────
                    try:
                        _df_cf2 = cargar_csv("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
                        _col_sot_cf2 = encontrar_columna(_df_cf2, ["SOT","Sot","sot"]) if not _df_cf2.empty else None
                        _col_com_cf2 = encontrar_columna(_df_cf2,
                            ["COM ETAPA","COM_ETAPA","Com Etapa","COMISION ETAPA","COMISIÓN ETAPA",
                             "COMISION","COMISIÓN","Comision"]) if not _df_cf2.empty else None
                        if not _df_cf2.empty and _col_sot_cf2 and _col_com_cf2:
                            _cf2_com_mask = pd.to_numeric(_df_cf2[_col_com_cf2], errors="coerce").fillna(0) > 0
                            if _col_sot_dvz:
                                # Subconjunto FIJA del DVZ filtrado
                                _dvz_fija = _dvz_f[_dvz_f[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "FIJA"].copy() if _col_tipo else _dvz_f.copy()
                                _sots_dvz = set(_norm_id(_dvz_fija[_col_sot_dvz]))
                                _cf2_sot_norm = _norm_id(_df_cf2[_col_sot_cf2]).reset_index(drop=True)
                                # Reconstruir máscara alineada al df original
                                _cf2_sot_all = _df_cf2[_col_sot_cf2].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
                                _cf2_en_dvz  = _cf2_sot_all.isin(_sots_dvz)
                                _netas_3m_fija = int(_cf2_sot_all[_cf2_en_dvz & _cf2_com_mask].nunique())
                                _comision_3m += float(pd.to_numeric(_df_cf2.loc[_cf2_en_dvz & _cf2_com_mask, _col_com_cf2], errors="coerce").fillna(0).sum())
                            else:
                                # Sin columna SOT en DVZ → comportamiento original
                                _netas_3m_fija = int(_df_cf2.loc[_cf2_com_mask, _col_sot_cf2].dropna().astype(str).str.strip().str.replace(r"\.0$","",regex=True).nunique())
                                _comision_3m += float(pd.to_numeric(_df_cf2.loc[_cf2_com_mask, _col_com_cf2], errors="coerce").fillna(0).sum())
                    except Exception:
                        pass

                    # ── MÓVIL: SECs del DVZ → cruce con CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA ──
                    try:
                        _df_cm2 = cargar_csv("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")
                        _col_sec_cm2 = encontrar_columna(_df_cm2, ["SEC","Sec","sec"]) if not _df_cm2.empty else None
                        _col_com_cm2 = encontrar_columna(_df_cm2,
                            ["COMISION","COMISIÓN","Comision","Comisión","MONTO"]) if not _df_cm2.empty else None
                        if not _df_cm2.empty and _col_sec_cm2 and _col_com_cm2:
                            _cm2_com_mask = pd.to_numeric(_df_cm2[_col_com_cm2], errors="coerce").fillna(0) > 0
                            if _col_sec_dvz:
                                # Subconjunto MOVIL del DVZ filtrado
                                _dvz_movil = _dvz_f[_dvz_f[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"].copy() if _col_tipo else _dvz_f.copy()
                                _secs_dvz = set(_norm_id(_dvz_movil[_col_sec_dvz]))
                                _cm2_sec_all = _df_cm2[_col_sec_cm2].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
                                _cm2_en_dvz  = _cm2_sec_all.isin(_secs_dvz)
                                _netas_3m_movil = int((_cm2_sec_all[_cm2_en_dvz & _cm2_com_mask] != "").sum())
                                _comision_3m += float(pd.to_numeric(_df_cm2.loc[_cm2_en_dvz & _cm2_com_mask, _col_com_cm2], errors="coerce").fillna(0).sum())
                            else:
                                # Sin columna SEC en DVZ → comportamiento original
                                _netas_3m_movil = int((_df_cm2.loc[_cm2_com_mask, _col_sec_cm2].astype(str).str.strip().str.replace(r".0$","",regex=True) != "").sum())
                                _comision_3m += float(pd.to_numeric(_df_cm2.loc[_cm2_com_mask, _col_com_cm2], errors="coerce").fillna(0).sum())
                    except Exception:
                        pass

                    # ── KPI NETAS 6 MESES ────────────────────────────────────────────
                    # Misma lógica que Netas 3 Meses, pero usando la 3ra Caída y SOLO para MÓVIL:
                    # MÓVIL: cruce por SEC → "Datos Adicionales - Sec" (DVZ) vs "SEC" (CLARO_TELETALK_MOVIL_TERCERA_CAIDA)
                    # No aplica para FIJA (no se procesa 6 meses de Fija, solo Móvil).
                    _netas_6m_movil = 0
                    try:
                        _df_cm3 = cargar_csv("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv")
                        _col_sec_cm3 = encontrar_columna(_df_cm3, ["SEC","Sec","sec"]) if not _df_cm3.empty else None
                        _col_com_cm3 = encontrar_columna(_df_cm3,
                            ["COMISION","COMISIÓN","Comision","Comisión","MONTO"]) if not _df_cm3.empty else None
                        if not _df_cm3.empty and _col_sec_cm3 and _col_com_cm3:
                            _cm3_com_mask = pd.to_numeric(_df_cm3[_col_com_cm3], errors="coerce").fillna(0) > 0
                            if _col_sec_dvz:
                                # Subconjunto MOVIL del DVZ filtrado (mismo subconjunto que Netas 3 Meses)
                                _dvz_movil_6m = _dvz_f[_dvz_f[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"].copy() if _col_tipo else _dvz_f.copy()
                                _secs_dvz_6m = set(_norm_id(_dvz_movil_6m[_col_sec_dvz]))
                                _cm3_sec_all = _df_cm3[_col_sec_cm3].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
                                _cm3_en_dvz  = _cm3_sec_all.isin(_secs_dvz_6m)
                                _netas_6m_movil = int((_cm3_sec_all[_cm3_en_dvz & _cm3_com_mask] != "").sum())
                                _comision_6m += float(pd.to_numeric(_df_cm3.loc[_cm3_en_dvz & _cm3_com_mask, _col_com_cm3], errors="coerce").fillna(0).sum())
                            else:
                                # Sin columna SEC en DVZ → comportamiento original
                                _netas_6m_movil = int((_df_cm3.loc[_cm3_com_mask, _col_sec_cm3].astype(str).str.strip().str.replace(r"\.0$","",regex=True) != "").sum())
                                _comision_6m += float(pd.to_numeric(_df_cm3.loc[_cm3_com_mask, _col_com_cm3], errors="coerce").fillna(0).sum())
                    except Exception:
                        pass

                    # Disponibilidad por combinación Servicio + Canal:
                    # FIJA + D&C       → Netas 3M y 6M disponibles (CLARO_DC_FIJA_SEGUNDA_CAIDA)
                    # FIJA + Teletalk  → no disponible (sin archivos)
                    # MOVIL + D&C      → no disponible (sin archivos)
                    # MOVIL + Teletalk → Netas 3M disponible (CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA)
                    # Todos + Todos    → suma solo lo disponible

                    _serv_up  = _f_serv.upper()   # "FIJA" / "MOVIL" / "TODOS"
                    _canales_up = {str(c).upper() for c in _f_canal_sel} if _f_canal_sel else {"TODOS"}

                    _disponible_fija  = (_serv_up in ("FIJA",  "TODOS")) and ("TODOS" in _canales_up or "D&C" in _canales_up)
                    _disponible_movil = (_serv_up in ("MOVIL", "TODOS")) and ("TODOS" in _canales_up or "TELETALK" in _canales_up or "TELETALK" in {c.replace("TELETALK", "TELETALK") for c in _canales_up})

                    if _disponible_fija and _disponible_movil:
                        _val_n3m = f"{_netas_3m_fija + _netas_3m_movil:,}"
                        _sub_n3m = "2da Etapa Fija D&C + 2da Caída Móvil Teletalk"
                    elif _disponible_fija:
                        _val_n3m = f"{_netas_3m_fija:,}"
                        _sub_n3m = "SOT únicas con COM ETAPA > 0 (2da Etapa)"
                    elif _disponible_movil:
                        _val_n3m = f"{_netas_3m_movil:,}"
                        _sub_n3m = "SEC únicas con COMISION > 0 (2da Caída)"
                    else:
                        _val_n3m = "—"
                        _sub_n3m = "Sin archivos para esta combinación"

                    # Netas 6 Meses: SOLO disponible para MÓVIL + Teletalk (3ra Caída).
                    # No se procesa Fija a 6 meses (por eso no se evalúa _disponible_fija aquí).
                    if _disponible_movil:
                        _val_n6m = f"{_netas_6m_movil:,}"
                        _sub_n6m = "SEC únicas con COMISION > 0 (3ra Caída)"
                    else:
                        _val_n6m = "—"
                        _sub_n6m = "Sin archivos para esta combinación"

                # NPN CSV puro:
                # Ventas Netas = pagadas base FIJA + MOVIL desde CSV CLARO.
                # Netas 3M = pagadas base encontradas en segunda caida.
                # Netas 6M = pagadas base encontradas en tercera caida.
                def _npn_norm_id_local(serie):
                    return (
                        serie.fillna("")
                        .astype(str)
                        .str.strip()
                        .str.replace(r"\.0$", "", regex=True)
                    )

                def _npn_col_local(df, opciones):
                    return encontrar_columna(df, opciones) if df is not None and not df.empty else None

                def _npn_mes_label_local(serie):
                    fechas = pd.to_datetime(serie, errors="coerce", dayfirst=True)
                    return fechas.apply(lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")

                _serv_npn = str(_f_serv).strip().upper()
                _canales_npn = {str(c).strip().upper() for c in _f_canal_sel} if _f_canal_sel else {"D&C", "TELETALK"}
                _usar_fija_csv = _serv_npn in ("TODOS", "FIJA")
                _usar_movil_csv = _serv_npn in ("TODOS", "MOVIL")

                _filtros_dvz_keys = bool(_f_sup or _f_tipis or _f_cola != "Todos" or _f_finst)
                _dvz_keys = _dff.copy() if "_dff" in locals() else pd.DataFrame()
                _sots_dvz_ok = set()
                _secs_dvz_ok = set()
                if not _dvz_keys.empty:
                    if _col_tipo and _col_sot_r:
                        _dvz_k_fija = _dvz_keys[_dvz_keys[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "FIJA"].copy()
                        _sots_dvz_ok = set(_npn_norm_id_local(_dvz_k_fija[_col_sot_r]))
                        _sots_dvz_ok.discard("")
                    if _col_tipo and _col_sec_npn:
                        _dvz_k_movil = _dvz_keys[_dvz_keys[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"].copy()
                        _secs_dvz_ok = set(_npn_norm_id_local(_dvz_k_movil[_col_sec_npn]))
                        _secs_dvz_ok.discard("")

                _base_fija_csv = []
                if _usar_fija_csv:
                    for _canal_csv, _archivo_csv in [("D&C", "CLARO_DC_FIJA.csv"), ("TELETALK", "CLARO_TELETALK_FIJA.csv")]:
                        if _canal_csv not in _canales_npn:
                            continue
                        _df_bf = _leer_csv_npn_local_cacheado(_archivo_csv)
                        if _df_bf.empty:
                            continue
                        _col_sot_bf = _npn_col_local(_df_bf, ["SOT", "Sot", "sot"])
                        _col_comi_bf = _npn_col_local(_df_bf, ["COMISIONES", "Comisiones"])
                        _col_com_bf = _npn_col_local(_df_bf, ["COMISION", "COMISIÓN", "Comision"])
                        _col_finst_bf = _npn_col_local(_df_bf, ["FECHA INSTALACION", "FECHA INSTALACIÓN", "Fecha Instalacion", "Fecha Instalación"])
                        if not _col_sot_bf:
                            continue
                        _df_bf = _df_bf.copy()
                        _df_bf["_SOT_NPN"] = _npn_norm_id_local(_df_bf[_col_sot_bf])
                        _df_bf = _df_bf[_df_bf["_SOT_NPN"] != ""].copy()
                        if _col_comi_bf:
                            _df_bf = _df_bf[_df_bf[_col_comi_bf].fillna("").astype(str).str.strip().str.upper() == "SI"].copy()
                        if _col_finst_bf and _f_finst:
                            _df_bf["_MES_INST_NPN"] = _npn_mes_label_local(_df_bf[_col_finst_bf])
                            _df_bf = _df_bf[_df_bf["_MES_INST_NPN"].isin(_f_finst)].copy()
                        if _filtros_dvz_keys:
                            _df_bf = _df_bf[_df_bf["_SOT_NPN"].isin(_sots_dvz_ok)].copy()
                        _df_bf = _df_bf.drop_duplicates("_SOT_NPN").copy()
                        _df_bf["_COM_NPN"] = pd.to_numeric(_df_bf[_col_com_bf], errors="coerce").fillna(0) if _col_com_bf else 0.0
                        _base_fija_csv.append(_df_bf[["_SOT_NPN", "_COM_NPN"]])

                _base_movil_csv = []
                if _usar_movil_csv:
                    for _canal_csv, _archivo_csv in [("D&C", "CLARO_DC_MOVIL.csv"), ("TELETALK", "CLARO_TELETALK_MOVIL.csv")]:
                        if _canal_csv not in _canales_npn:
                            continue
                        _df_bm = _leer_csv_npn_local_cacheado(_archivo_csv)
                        if _df_bm.empty:
                            continue
                        _col_sec_bm = _npn_col_local(_df_bm, ["SEC", "Sec", "sec"])
                        _col_com_bm = _npn_col_local(_df_bm, ["COMISION TOTAL", "COMISIÓN TOTAL", "COMISIÃ“N TOTAL", "Comision Total", "Comisión Total", "ComisiÃ³n Total"])
                        _col_trans_bm = _npn_col_local(_df_bm, ["TRANSACCION", "TRANSACCIÓN", "TRANSACCIÃ“N", "Transaccion", "Transacción", "TransacciÃ³n"])
                        if not (_col_sec_bm and _col_com_bm):
                            continue
                        _df_bm = _df_bm.copy()
                        _df_bm["_SEC_NPN"] = _npn_norm_id_local(_df_bm[_col_sec_bm])
                        _df_bm["_COM_NPN"] = pd.to_numeric(_df_bm[_col_com_bm], errors="coerce").fillna(0)
                        _df_bm["_TRANS_NPN"] = (
                            _df_bm[_col_trans_bm].fillna("").astype(str).str.strip().str.upper()
                            if _col_trans_bm else ""
                        )
                        _df_bm["_TRANS_NPN"] = _df_bm["_TRANS_NPN"].replace(["", "0", "0.0", "NAN", "NONE", "NULL", "NAT", "<NA>"], "")
                        _df_bm = _df_bm[(_df_bm["_SEC_NPN"] != "") & (_df_bm["_COM_NPN"] > 0) & (_df_bm["_TRANS_NPN"] != "")].copy()
                        if _filtros_dvz_keys:
                            _df_bm = _df_bm[_df_bm["_SEC_NPN"].isin(_secs_dvz_ok)].copy()
                        _base_movil_csv.append(_df_bm[["_SEC_NPN", "_COM_NPN"]])

                _base_fija_csv = pd.concat(_base_fija_csv, ignore_index=True) if _base_fija_csv else pd.DataFrame(columns=["_SOT_NPN", "_COM_NPN"])
                _base_movil_csv = pd.concat(_base_movil_csv, ignore_index=True) if _base_movil_csv else pd.DataFrame(columns=["_SEC_NPN", "_COM_NPN"])

                _ventas_netas_total = int(len(_base_fija_csv) + len(_base_movil_csv))
                _comision_base_csv = float(
                    pd.to_numeric(_base_fija_csv.get("_COM_NPN", 0), errors="coerce").fillna(0).sum()
                    + pd.to_numeric(_base_movil_csv.get("_COM_NPN", 0), errors="coerce").fillna(0).sum()
                )

                _sots_base_csv = set(_base_fija_csv["_SOT_NPN"].astype(str)) if not _base_fija_csv.empty else set()
                _secs_base_csv = set(_base_movil_csv["_SEC_NPN"].astype(str)) if not _base_movil_csv.empty else set()
                _sots_base_csv.discard("")
                _secs_base_csv.discard("")

                _netas_3m_fija = 0
                _netas_3m_movil = 0
                _netas_6m_movil = 0
                _comision_3m = 0.0
                _comision_6m = 0.0

                if _usar_fija_csv and _sots_base_csv:
                    _df_cf2_csv = _leer_csv_npn_local_cacheado("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
                    _col_sot_cf2 = _npn_col_local(_df_cf2_csv, ["SOT", "Sot", "sot"])
                    _col_com_cf2 = _npn_col_local(_df_cf2_csv, ["COM ETAPA", "COM_ETAPA", "Com Etapa", "COMISION ETAPA", "COMISIÓN ETAPA", "COMISIÃ“N ETAPA", "COMISION", "COMISIÓN", "COMISIÃ“N", "Comision"])
                    if not _df_cf2_csv.empty and _col_sot_cf2 and _col_com_cf2:
                        _df_cf2_csv = _df_cf2_csv.copy()
                        _df_cf2_csv["_SOT_NPN"] = _npn_norm_id_local(_df_cf2_csv[_col_sot_cf2])
                        _df_cf2_csv["_COM_NPN"] = pd.to_numeric(_df_cf2_csv[_col_com_cf2], errors="coerce").fillna(0)
                        _df_cf2_csv = _df_cf2_csv[(_df_cf2_csv["_SOT_NPN"].isin(_sots_base_csv)) & (_df_cf2_csv["_COM_NPN"] > 0)].copy()
                        _netas_3m_fija = int(_df_cf2_csv["_SOT_NPN"].nunique())
                        _comision_3m += float(_df_cf2_csv["_COM_NPN"].sum())

                if _usar_movil_csv and _secs_base_csv:
                    _df_cm2_csv = _leer_csv_npn_local_cacheado("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")
                    _col_sec_cm2 = _npn_col_local(_df_cm2_csv, ["SEC", "Sec", "sec"])
                    _col_com_cm2 = _npn_col_local(_df_cm2_csv, ["COMISION", "COMISIÓN", "COMISIÃ“N", "Comision", "Comisión", "ComisiÃ³n", "MONTO"])
                    if not _df_cm2_csv.empty and _col_sec_cm2 and _col_com_cm2:
                        _df_cm2_csv = _df_cm2_csv.copy()
                        _df_cm2_csv["_SEC_NPN"] = _npn_norm_id_local(_df_cm2_csv[_col_sec_cm2])
                        _df_cm2_csv["_COM_NPN"] = pd.to_numeric(_df_cm2_csv[_col_com_cm2], errors="coerce").fillna(0)
                        _df_cm2_csv = _df_cm2_csv[(_df_cm2_csv["_SEC_NPN"].isin(_secs_base_csv)) & (_df_cm2_csv["_COM_NPN"] > 0)].copy()
                        _netas_3m_movil = int((_df_cm2_csv["_SEC_NPN"] != "").sum())
                        _comision_3m += float(_df_cm2_csv["_COM_NPN"].sum())

                    _df_cm3_csv = _leer_csv_npn_local_cacheado("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv")
                    _col_sec_cm3 = _npn_col_local(_df_cm3_csv, ["SEC", "Sec", "sec"])
                    _col_com_cm3 = _npn_col_local(_df_cm3_csv, ["COMISION", "COMISIÓN", "COMISIÃ“N", "Comision", "Comisión", "ComisiÃ³n", "MONTO"])
                    if not _df_cm3_csv.empty and _col_sec_cm3 and _col_com_cm3:
                        _df_cm3_csv = _df_cm3_csv.copy()
                        _df_cm3_csv["_SEC_NPN"] = _npn_norm_id_local(_df_cm3_csv[_col_sec_cm3])
                        _df_cm3_csv["_COM_NPN"] = pd.to_numeric(_df_cm3_csv[_col_com_cm3], errors="coerce").fillna(0)
                        _df_cm3_csv = _df_cm3_csv[(_df_cm3_csv["_SEC_NPN"].isin(_secs_base_csv)) & (_df_cm3_csv["_COM_NPN"] > 0)].copy()
                        _netas_6m_movil = int((_df_cm3_csv["_SEC_NPN"] != "").sum())
                        _comision_6m += float(_df_cm3_csv["_COM_NPN"].sum())

                _disponible_fija = _usar_fija_csv and ("D&C" in _canales_npn or "TODOS" in _canales_npn)
                _disponible_movil = _usar_movil_csv and ("TELETALK" in _canales_npn or "TODOS" in _canales_npn)
                _val_n3m = f"{(_netas_3m_fija + _netas_3m_movil):,}" if (_disponible_fija or _disponible_movil) else "—"
                _sub_n3m = "Pagadas encontradas en 2da Caida CSV"
                _val_n6m = f"{_netas_6m_movil:,}" if _disponible_movil else "—"
                _sub_n6m = "Pagadas encontradas en 3ra Caida CSV"
                _comision_total_npn = _comision_base_csv + _comision_3m + _comision_6m

                # ── KPIs gerenciales (JavaScript animado) ────────────────
                _color_n3m = "#0891b2" if _val_n3m != "—" else "#9ca3af"
                _color_n6m = "#0f4287" if _val_n6m != "—" else "#9ca3af"
                # Preparar valores numéricos para animación JS
                _js_netas   = _ventas_netas_total
                _js_com     = round(_comision_total_npn, 2)
                _js_tv_pct  = round(_pct_tv_npn, 2)
                _js_tv_cnt  = _ventas_tv_npn
                _js_n3m_raw = (_netas_3m_fija + _netas_3m_movil) if (_disponible_fija or _disponible_movil) else -1
                _js_n6m_raw = _netas_6m_movil if _disponible_movil else -1
                _js_com3m   = round(_comision_3m, 2)
                _js_com6m   = round(_comision_6m, 2)

                _stc.html(f"""
                <style>
                * {{ box-sizing:border-box; }}
                body {{ margin:0; background:transparent; font-family:Segoe UI, Arial, sans-serif; overflow:hidden; }}
                .npn-kpi-grid {{
                    display:grid;
                    grid-template-columns: repeat(5, minmax(0,1fr));
                    gap:14px;
                    margin:0;
                    padding:2px 2px 10px;
                }}
                .npn-card {{
                    --accent:#0f4287;
                    position:relative;
                    overflow:hidden;
                    min-height:118px;
                    height:118px;
                    padding:14px 13px 12px;
                    border-radius:14px;
                    background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(248,250,252,.92));
                    border:1px solid rgba(15,23,42,.10);
                    border-top:4px solid var(--accent);
                    box-shadow:0 12px 28px rgba(15,23,42,.08);
                    text-align:left;
                    transition:transform .16s ease, box-shadow .16s ease;
                    isolation:isolate;
                    animation:npnFadeUp .38s cubic-bezier(.2,.8,.2,1) both;
                }}
                .npn-card:before {{
                    content:"";
                    position:absolute;
                    width:88px;
                    height:88px;
                    right:-42px;
                    top:-42px;
                    border-radius:999px;
                    background:rgba(15,66,135,.08);
                    z-index:-1;
                }}
                .npn-card:hover {{
                    transform:translateY(-2px);
                    box-shadow:0 18px 36px rgba(15,23,42,.13);
                }}
                .npn-card-label {{
                    min-height:24px;
                    color:#475569;
                    font-size:10px;
                    line-height:1.2;
                    font-weight:900;
                    text-transform:uppercase;
                    letter-spacing:.08em;
                    display:flex;
                    align-items:flex-start;
                    gap:6px;
                    margin-bottom:7px;
                }}
                .npn-dot {{
                    width:7px;
                    height:7px;
                    min-width:7px;
                    border-radius:999px;
                    background:var(--accent);
                    margin-top:3px;
                    box-shadow:0 0 0 4px rgba(15,66,135,.10);
                }}
                .npn-card-val {{
                    display:block;
                    color:var(--accent);
                    font-size:clamp(21px,2vw,30px);
                    line-height:1.02;
                    font-weight:950;
                    margin-top:3px;
                    word-break:break-word;
                    font-variant-numeric:tabular-nums;
                }}
                .npn-card-val.npn-money {{ font-size:clamp(18px,1.5vw,24px); }}
                .npn-card-sub {{
                    display:block;
                    color:#64748b;
                    font-size:10px;
                    line-height:1.25;
                    font-weight:700;
                    margin-top:7px;
                    font-style:normal;
                }}
                @keyframes npnFadeUp {{
                    from {{ opacity:0; transform:translateY(8px) scale(.985); filter:blur(1px); }}
                    to   {{ opacity:1; transform:translateY(0) scale(1); filter:blur(0); }}
                }}
                .npn-card:nth-child(1){{ animation-delay:.03s; }}
                .npn-card:nth-child(2){{ animation-delay:.08s; }}
                .npn-card:nth-child(3){{ animation-delay:.13s; }}
                .npn-card:nth-child(4){{ animation-delay:.18s; }}
                .npn-card:nth-child(5){{ animation-delay:.23s; }}
                </style>

                <div class="npn-kpi-grid">
                    <div class="npn-card" style="--accent:#059669;">
                        <span class="npn-card-label"><span class="npn-dot"></span><span>Ventas Netas</span></span>
                        <span class="npn-card-val" id="npnNetas">{_js_netas:,}</span>
                        <span class="npn-card-sub">PAGADAS · Fija + Móvil</span>
                    </div>
                    <div class="npn-card" style="--accent:{_color_n3m};">
                        <span class="npn-card-label"><span class="npn-dot"></span><span>Netas 3 Meses</span></span>
                        <span class="npn-card-val" id="npnN3m">{_val_n3m}</span>
                        <span class="npn-card-sub">{_sub_n3m}</span>
                    </div>
                    <div class="npn-card" style="--accent:{_color_n6m};">
                        <span class="npn-card-label"><span class="npn-dot"></span><span>Netas 6 Meses</span></span>
                        <span class="npn-card-val" id="npnN6m">{_val_n6m}</span>
                        <span class="npn-card-sub">{_sub_n6m}</span>
                    </div>
                    <div class="npn-card" style="--accent:#7c3aed;">
                        <span class="npn-card-label"><span class="npn-dot"></span><span>Comisión Total</span></span>
                        <span class="npn-card-val npn-money" id="npnCom">{formatear_moneda(_comision_total_npn)}</span>
                        <span class="npn-card-sub">Base + 3M + 6M</span>
                    </div>
                    <div class="npn-card" style="--accent:#0891b2;">
                        <span class="npn-card-label"><span class="npn-dot"></span><span>% TV</span></span>
                        <span class="npn-card-val" id="npnTv">{_js_tv_pct:.2f}%</span>
                        <span class="npn-card-sub" id="npnTvSub">{_js_tv_cnt:,} pagadas con TV</span>
                    </div>
                </div>

                <script>
                (function() {{
                    function run() {{
                        function animCount(id, from, to, dur, fmt) {{
                            var el = document.getElementById(id);
                            if (!el) {{ return; }}
                            var start = null;
                            function step(ts) {{
                                if (!start) start = ts;
                                var p = Math.min((ts - start) / dur, 1);
                                var ease = 1 - Math.pow(1 - p, 3);
                                el.textContent = fmt(from + (to - from) * ease);
                                if (p < 1) requestAnimationFrame(step);
                            }}
                            requestAnimationFrame(step);
                        }}
                        function fmtNum(v) {{ return Math.round(v).toLocaleString("es-PE"); }}
                        function fmtMon(v) {{ return "S/ " + v.toLocaleString("es-PE", {{minimumFractionDigits:2, maximumFractionDigits:2}}); }}
                        function fmtPct(v) {{ return v.toFixed(2) + "%"; }}

                        animCount("npnNetas", 0, {_js_netas},   900,  fmtNum);
                        animCount("npnCom",   0, {_js_com},     1100, fmtMon);
                        animCount("npnTv",    0, {_js_tv_pct},  900,  fmtPct);
                        if ({_js_n3m_raw} >= 0) animCount("npnN3m", 0, {_js_n3m_raw}, 900, fmtNum);
                        if ({_js_n6m_raw} >= 0) animCount("npnN6m", 0, {_js_n6m_raw}, 900, fmtNum);

                        var subEl = document.getElementById("npnTvSub");
                        if (subEl) subEl.textContent = fmtNum({_js_tv_cnt}) + " pagadas con TV";
                    }}
                    // Esperar a que Streamlit termine de montar el DOM
                    setTimeout(run, 120);
                }})();
                </script>
                """, height=142, scrolling=False)

                # ── Tablas Gerenciales de Retención por Mes de Instalación ──────────
                # Diseño tipo "panel enterprise": cabecera en degradado + badges tipo pill
                # con barra de progreso embebida para cada porcentaje.
                st.markdown("""
                <style>
                .ret-section-title {
                    display:flex; align-items:center; gap:9px;
                    font-size:14.5px; font-weight:900; letter-spacing:.07em; text-transform:uppercase;
                    padding:14px 18px; margin-top:24px; margin-bottom:0;
                    border-radius:16px 16px 0 0; color:#fff;
                }
                .ret-title-fija  { background:linear-gradient(120deg,#0b3568 0%,#0f4287 45%,#2563eb 100%); box-shadow:0 10px 24px rgba(15,66,135,.28); }
                .ret-title-movil { background:linear-gradient(120deg,#4a0763 0%,#6d0b8c 45%,#9333ea 100%); box-shadow:0 10px 24px rgba(109,11,140,.28); }
                .ret-title-badge {
                    margin-left:auto; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.28);
                    padding:3px 10px; border-radius:999px; font-size:10px; letter-spacing:.06em;
                }
                .ret-table-wrap {
                    background:rgba(255,255,255,0.98); border-radius:0 0 16px 16px;
                    overflow:hidden; margin-bottom:16px; border:1px solid rgba(15,23,42,.05);
                    box-shadow:0 14px 34px rgba(15,23,42,.10);
                }
                .ret-table { width:100%; border-collapse:collapse; font-size:12.5px; }
                .ret-table thead th {
                    padding:11px 14px; text-align:left; font-weight:800;
                    font-size:10.5px; letter-spacing:.08em; text-transform:uppercase;
                    color:#5b6472; background:#f7f9fc;
                    border-bottom:2px solid rgba(15,23,42,.07);
                    position:sticky; top:0;
                }
                .ret-table tbody tr { border-bottom:1px solid rgba(15,23,42,.045); transition:background .15s ease; }
                .ret-table tbody tr:nth-child(even) { background:rgba(37,99,235,.02); }
                .ret-table tbody tr:hover { background:rgba(37,99,235,.07); }
                .ret-table tbody tr:last-child { border-bottom:none; }
                .ret-table td { padding:10px 14px; color:#111827; font-weight:700; font-variant-numeric:tabular-nums; vertical-align:middle; }
                .ret-mes-cell { font-weight:800; color:#1f2937; white-space:nowrap; }
                .ret-col-divider { border-left:1px dashed rgba(15,23,42,.10); }

                .ret-badge {
                    display:inline-flex; align-items:center; gap:5px;
                    padding:4px 10px; border-radius:999px; font-weight:900; font-size:11.5px; line-height:1;
                }
                .ret-badge-ok   { background:rgba(5,150,105,.12); color:#059669; }
                .ret-badge-med  { background:rgba(217,119,6,.13); color:#d97706; }
                .ret-badge-proc { background:rgba(107,114,128,.10); color:#6b7280; font-style:italic; font-weight:700; }
                .ret-pct-wrap { display:flex; flex-direction:column; align-items:flex-end; gap:4px; }
                .ret-bar-track { width:58px; height:5px; border-radius:999px; background:rgba(15,23,42,.08); overflow:hidden; }
                .ret-bar-fill { height:100%; border-radius:999px; }
                .ret-bar-ok  { background:linear-gradient(90deg,#059669,#10b981); }
                .ret-bar-med { background:linear-gradient(90deg,#d97706,#f59e0b); }
                </style>
                """, unsafe_allow_html=True)

                # Función para clasificar % y estilo → badge + mini barra de progreso
                def _ret_pct_html(instalados, llegan):
                    if llegan is None:
                        return '<div class="ret-pct-wrap"><span class="ret-badge ret-badge-proc">⏳ En proceso</span></div>'
                    if instalados == 0:
                        return '<div class="ret-pct-wrap"><span class="ret-badge ret-badge-proc">—</span></div>'
                    pct = llegan / instalados * 100
                    cls  = "ok" if pct >= 80 else "med"
                    icon = "✅" if pct >= 80 else "⚠️"
                    barpct = min(pct, 100)
                    return f"""<div class="ret-pct-wrap">
                        <span class="ret-badge ret-badge-{cls}">{icon} {pct:.0f}%</span>
                        <div class="ret-bar-track"><div class="ret-bar-fill ret-bar-{cls}" style="width:{barpct:.0f}%;"></div></div>
                    </div>"""

                MESES_ORDER = {v:k for k,v in {
                    1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
                    7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'
                }.items()}

                def _sort_mes(s):
                    parts = s.split()
                    if len(parts) == 2:
                        try: return (int(parts[1]), MESES_ORDER.get(parts[0], 99))
                        except: pass
                    return (9999, 99)

                _npn_subvista = st.radio(
                    "Vista Resumen NPN",
                    ["📈 Retención por Mes", "🏆 Ranking Supervisor", "👥 Ranking Asesores"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="npn_subvista_resumen"
                )

                if _npn_subvista == "📈 Retención por Mes":
                    col_ret_fija, col_ret_movil = st.columns(2)

                    # ── Tabla FIJA ──────────────────────────────────────────────
                    with col_ret_fija:
                        st.markdown('<div class="ret-section-title ret-title-fija">📡 Retención FIJA · por Mes Instalación<span class="ret-title-badge">2da Etapa · 3M</span></div>', unsafe_allow_html=True)
                        try:
                            # Pagadas FIJA: misma fuente que Detalle Fija General.
                            # Se cuentan SOT únicas PAGADAS desde CLARO_*_FIJA por FECHA INSTALACION.
                            # COMISIONES == SI para que cuadre con el KPI Pagadas.
                            if _f_serv == "MOVIL":
                                st.info("Filtro Servicio = MOVIL. La tabla FIJA no aplica para esta selección.")
                            else:
                                _canales_fija_ret = _f_canal_sel if _f_canal_sel else ["D&C", "Teletalk"]
                                _archivos_fija_ret = []
                                if "D&C" in _canales_fija_ret:
                                    _archivos_fija_ret.append(("D&C", "CLARO_DC_FIJA.csv"))
                                if "Teletalk" in _canales_fija_ret:
                                    _archivos_fija_ret.append(("Teletalk", "CLARO_TELETALK_FIJA.csv"))

                                # Si hay filtros de detalle, se restringen las SOT usando Detalle Fija General.
                                _usar_detalle_sots = bool(_f_sup or _f_estado_pago or _f_tipis or _f_cola != "Todos")
                                _sots_detalle_ok = None
                                if _usar_detalle_sots:
                                    _det_ret = construir_detalle_fija_general("Todos los meses", "Todos los meses").copy()
                                    if "SOT" in _det_ret.columns:
                                        _det_ret["_SOT_RET"] = _normalizar_sot_series(_det_ret["SOT"].fillna("").astype(str))
                                    else:
                                        _det_ret["_SOT_RET"] = ""
                                    if _f_canal_sel and "Canal" in _det_ret.columns:
                                        _det_ret = _det_ret[_det_ret["Canal"].fillna("").astype(str).str.strip().isin(_f_canal_sel)]
                                    if _f_sup and "SUPERVISOR" in _det_ret.columns:
                                        _det_ret = _det_ret[_det_ret["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)]
                                    if _f_estado_pago and "Estado Pago" in _det_ret.columns:
                                        _det_ret = _det_ret[_det_ret["Estado Pago"].fillna("NO PAGADA").astype(str).str.strip().str.upper().isin([str(e).upper() for e in _f_estado_pago])]
                                    if _f_tipis and "TIPIS" in _det_ret.columns:
                                        _tip_det = _det_ret["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                                        _det_ret = _det_ret[_tip_det.isin([str(t).strip() for t in _f_tipis])]
                                    if _f_cola != "Todos" and "COLA" in _det_ret.columns:
                                        _det_ret = _det_ret[_det_ret["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola]
                                    _sots_detalle_ok = set(_det_ret["_SOT_RET"].dropna().astype(str))
                                    _sots_detalle_ok.discard("")

                                _mes_sots = {}
                                for _canal_ret, _archivo_ret in _archivos_fija_ret:
                                    _df_claro_ret = preparar_fechas_fija(cargar_csv(_archivo_ret))
                                    if _df_claro_ret.empty or "FECHA INSTALACION" not in _df_claro_ret.columns:
                                        continue
                                    _col_sot_ret = next((c for c in _df_claro_ret.columns if c.strip().upper() == "SOT"), None)
                                    if not _col_sot_ret:
                                        continue
                                    _df_claro_ret = _df_claro_ret.copy()
                                    _df_claro_ret["_SOT_RET"] = _normalizar_sot_series(_df_claro_ret[_col_sot_ret].fillna("").astype(str))
                                    _df_claro_ret = _df_claro_ret[_df_claro_ret["_SOT_RET"] != ""].copy()
                                    # Igual que Detalle Fija General: primero SOT única, luego COMISIONES == SI.
                                    _df_claro_ret = _df_claro_ret.drop_duplicates(subset=[_col_sot_ret]).copy()
                                    _col_comisiones_ret = next((c for c in _df_claro_ret.columns if c.strip().upper() == "COMISIONES"), None)
                                    if _col_comisiones_ret:
                                        _df_claro_ret = _df_claro_ret[
                                            _df_claro_ret[_col_comisiones_ret].fillna("").astype(str).str.strip().str.upper() == "SI"
                                        ].copy()
                                    _df_claro_ret["_MES_INST_RET"] = _df_claro_ret["FECHA INSTALACION"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                    _df_claro_ret = _df_claro_ret[_df_claro_ret["_MES_INST_RET"] != ""].copy()
                                    if _f_finst:
                                        _df_claro_ret = _df_claro_ret[_df_claro_ret["_MES_INST_RET"].isin(_f_finst)]
                                    if _sots_detalle_ok is not None:
                                        _df_claro_ret = _df_claro_ret[_df_claro_ret["_SOT_RET"].isin(_sots_detalle_ok)]
                                    for _mes_label, _grp_mes in _df_claro_ret.groupby("_MES_INST_RET"):
                                        _mes_sots.setdefault(_mes_label, set()).update(_grp_mes["_SOT_RET"].unique())

                                _meses_omitidos_fija = {"Junio 2025", "Agosto 2025", "Septiembre 2025", "Octubre 2025"}
                                _grp_fija = pd.DataFrame([
                                    {"_MES": _mes, "Pagadas": len(_sots)}
                                    for _mes, _sots in _mes_sots.items()
                                    if _mes not in _meses_omitidos_fija
                                ])
                                _grp_fija = _grp_fija.sort_values("_MES", key=lambda x: x.map(_sort_mes)) if not _grp_fija.empty else pd.DataFrame(columns=["_MES", "Pagadas"])

                                # Llegan a 3M: SOT únicas, manteniendo la regla original de FIJA.
                                _df_cf2_r = cargar_csv("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
                                _col_sot_cf2_r = encontrar_columna(_df_cf2_r, ["SOT", "Sot", "sot"]) if not _df_cf2_r.empty else None
                                _col_com_cf2_r = encontrar_columna(_df_cf2_r, [
                                    "COM ETAPA", "COM_ETAPA", "Com Etapa", "COMISION ETAPA", "COMISIÓN ETAPA",
                                    "COMISION", "COMISIÓN", "Comision"
                                ]) if not _df_cf2_r.empty else None
                                _cf2_sot_n = pd.Series(dtype="object")
                                _cf2_com_n = pd.Series(dtype="bool")
                                if not _df_cf2_r.empty and _col_sot_cf2_r and _col_com_cf2_r:
                                    _cf2_sot_n = _df_cf2_r[_col_sot_cf2_r].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                                    _cf2_com_n = pd.to_numeric(_df_cf2_r[_col_com_cf2_r], errors="coerce").fillna(0) > 0

                                _rows_fija = []
                                for _, _row in _grp_fija.iterrows():
                                    _mes_label = _row["_MES"]
                                    _pagadas_fija = int(_row["Pagadas"])
                                    _sots_mes = _mes_sots.get(_mes_label, set())
                                    _llegan = None
                                    if len(_cf2_sot_n) > 0:
                                        _llegan = int(_cf2_sot_n[_cf2_sot_n.isin(_sots_mes) & _cf2_com_n].nunique())
                                    _rows_fija.append((_mes_label, _pagadas_fija, _llegan))

                                if _rows_fija:
                                    _filas_html = ""
                                    for _mes_l, _pag, _ll in _rows_fija:
                                        _ll_txt = f"{_ll:,}" if _ll is not None else '<span style="color:#9ca3af;font-style:italic;">en proceso</span>'
                                        _pct_html = _ret_pct_html(_pag, _ll)
                                        _filas_html += f"""<tr>
                                            <td class="ret-mes-cell">{_mes_l}</td>
                                            <td style="text-align:right;">{_pag:,}</td>
                                            <td style="text-align:right;" class="ret-col-divider">{_ll_txt}</td>
                                            <td style="text-align:right;">{_pct_html}</td>
                                        </tr>"""
                                    st.markdown(f"""
                                    <div class="ret-table-wrap">
                                    <table class="ret-table">
                                        <thead>
                                            <tr>
                                                <th>Mes Instalación</th>
                                                <th style="text-align:right;">Pagadas</th>
                                                <th style="text-align:right;">Llegan a 3M</th>
                                                <th style="text-align:right;">% 3M</th>
                                            </tr>
                                        </thead>
                                        <tbody>{_filas_html}</tbody>
                                    </table>
                                    </div>""", unsafe_allow_html=True)
                                else:
                                    st.info("Sin datos de instalación FIJA disponibles.")
                        except Exception as _e_fija:
                            st.warning(f"No se pudo construir tabla FIJA: {_e_fija}")

                    # ── Tabla MÓVIL ─────────────────────────────────────────────
                    with col_ret_movil:
                        st.markdown('<div class="ret-section-title ret-title-movil">📱 Retención MÓVIL · por Mes Instalación<span class="ret-title-badge">2da y 3ra Caída · 3M / 6M</span></div>', unsafe_allow_html=True)
                        try:
                            _col_sec_r = next((c for c in _df_npn.columns if c.strip().lower() == "datos adicionales - sec"), None)

                            # ── Pagadas: MISMA fuente que Detalle Móvil General ──────────────
                            # Se usa construir_resumen_movil_general() y se agrupa por _FECHA_INSTALACION_DT.
                            # Esto hace que, por ejemplo, Teletalk Enero 2026 cuadre con 690 pagadas.
                            if _f_serv == "FIJA":
                                _instalados_por_mes = {}
                            else:
                                _df_movil_ret = construir_resumen_movil_general("Todos los meses")
                                if not _df_movil_ret.empty:
                                    _df_movil_ret = _df_movil_ret.copy()
                                    if "Venta Valida" in _df_movil_ret.columns:
                                        _df_movil_ret = _df_movil_ret[_df_movil_ret["Venta Valida"]].copy()
                                    if _f_canal_sel and "Canal" in _df_movil_ret.columns:
                                        _df_movil_ret = _df_movil_ret[_df_movil_ret["Canal"].fillna("").astype(str).str.strip().isin(_f_canal_sel)].copy()
                                    if _f_sup and "SUPERVISOR" in _df_movil_ret.columns:
                                        _df_movil_ret = _df_movil_ret[_df_movil_ret["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)].copy()
                                    if _f_estado_pago and "Estado Pago" in _df_movil_ret.columns:
                                        _df_movil_ret = _df_movil_ret[_df_movil_ret["Estado Pago"].fillna("NO PAGADA").astype(str).str.strip().str.upper().isin([str(e).upper() for e in _f_estado_pago])].copy()
                                    if _f_tipis and "TIPIS" in _df_movil_ret.columns:
                                        _tip_mret = _df_movil_ret["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                                        _df_movil_ret = _df_movil_ret[_tip_mret.isin([str(t).strip() for t in _f_tipis])].copy()
                                    if _f_cola != "Todos" and "COLA" in _df_movil_ret.columns:
                                        _df_movil_ret = _df_movil_ret[_df_movil_ret["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola].copy()

                                    _df_movil_ret["_FINST_R"] = pd.to_datetime(_df_movil_ret.get("_FECHA_INSTALACION_DT", pd.NaT), errors="coerce")
                                    _df_movil_ret["_MES_INST_M"] = _df_movil_ret["_FINST_R"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                    _df_movil_ret = _df_movil_ret[_df_movil_ret["_MES_INST_M"] != ""].copy()
                                    if _f_finst:
                                        _df_movil_ret = _df_movil_ret[_df_movil_ret["_MES_INST_M"].isin(_f_finst)].copy()
                                    _df_movil_pag = _df_movil_ret[
                                        _df_movil_ret["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                                    ].copy() if "Estado Pago" in _df_movil_ret.columns else pd.DataFrame()
                                    _instalados_por_mes = _df_movil_pag.groupby("_MES_INST_M").size().to_dict() if not _df_movil_pag.empty else {}
                                else:
                                    _instalados_por_mes = {}

                            # ── SEC universo para cruzar caídas (desde DVZ, igual que los KPI) ──
                            _sec_universo = set()
                            if _col_sec_r:
                                _uni_cross = _dvz_movil_uni.copy() if "_dvz_movil_uni" in dir() else _df_npn[
                                    _df_npn[_col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"
                                ].copy() if _col_tipo else _df_npn.copy()
                                if _f_finst:
                                    _col_finst_m = next((c for c in _df_npn.columns if c.strip().lower() in
                                        ["back office - fecha instalacion","back office - fecha instalación"]), None)
                                    if _col_finst_m:
                                        _uni_cross["_FINST_U"] = pd.to_datetime(_uni_cross[_col_finst_m], errors="coerce", dayfirst=True)
                                        _uni_cross["_MES_U"] = _uni_cross["_FINST_U"].apply(
                                            lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                        _uni_cross = _uni_cross[_uni_cross["_MES_U"].isin(_f_finst)]
                                _sec_universo = set(
                                    _uni_cross[_col_sec_r].dropna().astype(str).str.strip()
                                    .str.replace(r"\.0$","",regex=True))
                                _sec_universo.discard("")

                            # ── Llegan a 3M / 6M: FEC ACTIV CTR del archivo de caída ──────────
                            def _agrupar_caida_por_activacion(nombre_csv):
                                _df_c = cargar_csv(nombre_csv)
                                if _df_c.empty:
                                    return {}, 0
                                _col_sec_c = encontrar_columna(_df_c, ["SEC","Sec","sec"])
                                _col_com_c = encontrar_columna(_df_c, ["COMISION","COMISIÓN","Comision","Comisión","MONTO"])
                                _col_fec_c = encontrar_columna(_df_c, [
                                    "FEC ACTIV CTR","FEC. ACTIV CTR","FECHA ACTIV CTR","FECHA ACTIVACION CTR",
                                    "FECHA ACTIVACIÓN CTR","Fec Activ Ctr","FEC ACTIVACIÓN CTR"])
                                if not (_col_sec_c and _col_com_c):
                                    return {}, 0
                                _com_mask = pd.to_numeric(_df_c[_col_com_c], errors="coerce").fillna(0) > 0
                                _sec_c = _df_c[_col_sec_c].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
                                _match = _sec_c.isin(_sec_universo) & _com_mask
                                _dfm = _df_c[_match].copy()
                                _dfm["_SEC_C"] = _sec_c[_match]
                                if _col_fec_c:
                                    _dfm["_FEC_C"] = pd.to_datetime(_dfm[_col_fec_c], errors="coerce", dayfirst=True)
                                    _dfm["_MES_C"] = _dfm["_FEC_C"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                else:
                                    _dfm["_MES_C"] = ""
                                # Móvil: contar SEC con duplicados. No deduplicar por _SEC_C.
                                _sin_fecha = int((_dfm["_MES_C"] == "").sum())
                                _grp = _dfm[(_dfm["_MES_C"] != "") & (_dfm["_SEC_C"].astype(str).str.len() > 0)].groupby("_MES_C").size().to_dict()
                                return _grp, _sin_fecha

                            _llegan3_por_mes, _sinfecha3 = _agrupar_caida_por_activacion("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")
                            _llegan6_por_mes, _sinfecha6 = _agrupar_caida_por_activacion("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv")

                            _todos_meses = sorted(
                                set(_instalados_por_mes) | set(_llegan3_por_mes) | set(_llegan6_por_mes),
                                key=_sort_mes)

                            if _todos_meses:
                                _rows_movil = []
                                for _mes_label in _todos_meses:
                                    _instalados = int(_instalados_por_mes.get(_mes_label, 0))
                                    _llegan  = _llegan3_por_mes.get(_mes_label)
                                    _llegan6 = _llegan6_por_mes.get(_mes_label)
                                    _rows_movil.append((_mes_label, _instalados, _llegan, _llegan6))

                                # Caída(s) cuyo FEC ACTIV CTR no se pudo parsear/está vacío
                                if _sinfecha3 or _sinfecha6:
                                    _rows_movil.append((
                                        "Sin fecha activación (CTR)", 0,
                                        _sinfecha3 if _sinfecha3 else None,
                                        _sinfecha6 if _sinfecha6 else None
                                    ))

                                _filas_html_m = ""
                                for _mes_l, _inst, _ll, _ll6 in _rows_movil:
                                    _inst_txt = f"{_inst:,}" if _inst else '<span style="color:#9ca3af;">—</span>'
                                    _ll_txt  = f"{_ll:,}"  if _ll  is not None else '<span style="color:#9ca3af;font-style:italic;">en proceso</span>'
                                    _ll6_txt = f"{_ll6:,}" if _ll6 is not None else '<span style="color:#9ca3af;font-style:italic;">en proceso</span>'
                                    _pct_html  = _ret_pct_html(_inst, _ll)
                                    _pct6_html = _ret_pct_html(_inst, _ll6)
                                    _filas_html_m += f"""<tr>
                                        <td class="ret-mes-cell">{_mes_l}</td>
                                        <td style="text-align:right;">{_inst_txt}</td>
                                        <td style="text-align:right;" class="ret-col-divider">{_ll_txt}</td>
                                        <td style="text-align:right;">{_pct_html}</td>
                                        <td style="text-align:right;" class="ret-col-divider">{_ll6_txt}</td>
                                        <td style="text-align:right;">{_pct6_html}</td>
                                    </tr>"""
                                st.markdown(f"""
                                <div class="ret-table-wrap">
                                <table class="ret-table">
                                    <thead>
                                        <tr>
                                            <th>Mes Instalación</th>
                                            <th style="text-align:right;">Pagadas</th>
                                            <th style="text-align:right;">Llegan a 3M</th>
                                            <th style="text-align:right;">% 3M</th>
                                            <th style="text-align:right;">Llegan a 6M</th>
                                            <th style="text-align:right;">% 6M</th>
                                        </tr>
                                    </thead>
                                    <tbody>{_filas_html_m}</tbody>
                                </table>
                                </div>""", unsafe_allow_html=True)
                                st.caption("📌 FIJA Pagadas = SOT únicas con COMISIONES = SI por Fecha Instalación desde CLARO. MÓVIL Pagadas = misma base de Detalle Móvil General por Fecha Instalación. Las SEC de 3M/6M se cuentan con duplicados.")
                            else:
                                st.info("Sin datos de instalación MÓVIL disponibles.")
                        except Exception as _e_movil:
                            st.warning(f"No se pudo construir tabla MÓVIL: {_e_movil}")

                if _npn_subvista == "🏆 Ranking Supervisor":
                    try:
                        _sup_base = _dfp.copy()
                        for _c in ["ASESOR", "SUPERVISOR", "_TIPO_NPN", "SOT", "SEC"]:
                            if _c not in _sup_base.columns:
                                _sup_base[_c] = ""
                        _sup_base["ASESOR"] = (_sup_base["ASESOR"].fillna("Sin Asesor").astype(str)
                                               .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Asesor").str.upper())
                        _sup_base["SUPERVISOR"] = (_sup_base["SUPERVISOR"].fillna("Sin Supervisor").astype(str)
                                                  .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Supervisor").str.upper())
                        _sup_base["_TIPO_NPN"] = _sup_base["_TIPO_NPN"].fillna("").astype(str).str.strip().str.upper()

                        _sup_fija_pag = pd.DataFrame(columns=["ASESOR", "SUPERVISOR", "COMISION", "SOT"])
                        if _f_serv != "MOVIL":
                            _sup_fija_det = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                            if not _sup_fija_det.empty:
                                _sup_fija_det = _sup_fija_det.copy()
                                if _f_canal_sel and "Canal" in _sup_fija_det.columns:
                                    _sup_fija_det = _sup_fija_det[
                                        _sup_fija_det["Canal"].fillna("").astype(str).str.strip().str.upper()
                                        .isin([str(c).upper() for c in _f_canal_sel])
                                    ].copy()
                                if _f_finst and "FECHA INSTALACION" in _sup_fija_det.columns:
                                    _sup_fija_det["_FINST_SUP"] = pd.to_datetime(_sup_fija_det["FECHA INSTALACION"], errors="coerce", dayfirst=True)
                                    _sup_fija_det["_MES_INST_SUP"] = _sup_fija_det["_FINST_SUP"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                    _sup_fija_det = _sup_fija_det[_sup_fija_det["_MES_INST_SUP"].isin(_f_finst)].copy()
                                if _f_sup and "SUPERVISOR" in _sup_fija_det.columns:
                                    _sup_fija_det = _sup_fija_det[_sup_fija_det["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)].copy()
                                if _f_tipis and "TIPIS" in _sup_fija_det.columns:
                                    _tip_sup_fija = _sup_fija_det["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                                    _sup_fija_det = _sup_fija_det[_tip_sup_fija.isin([str(t).strip() for t in _f_tipis])].copy()
                                if _f_cola != "Todos" and "COLA" in _sup_fija_det.columns:
                                    _sup_fija_det = _sup_fija_det[_sup_fija_det["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola].copy()
                                if "Estado Pago" in _sup_fija_det.columns:
                                    _sup_fija_det = _sup_fija_det[_sup_fija_det["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"].copy()
                                else:
                                    _sup_fija_det = pd.DataFrame()
                                if not _sup_fija_det.empty:
                                    for _c in ["ASESOR", "SUPERVISOR", "COMISION", "SOT"]:
                                        if _c not in _sup_fija_det.columns:
                                            _sup_fija_det[_c] = "" if _c != "COMISION" else 0
                                    _sup_fija_det["ASESOR"] = (_sup_fija_det["ASESOR"].fillna("Sin Asesor").astype(str)
                                                               .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Asesor").str.upper())
                                    _sup_fija_det["SUPERVISOR"] = (_sup_fija_det["SUPERVISOR"].fillna("Sin Supervisor").astype(str)
                                                                  .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Supervisor").str.upper())
                                    _sup_fija_det["COMISION"] = pd.to_numeric(_sup_fija_det["COMISION"], errors="coerce").fillna(0)
                                    _sup_fija_det["SOT"] = _sup_fija_det["SOT"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                                    _sup_fija_pag = _sup_fija_det[["ASESOR", "SUPERVISOR", "COMISION", "SOT"]].copy()

                        _sup_movil_pag = pd.DataFrame(columns=["ASESOR", "SUPERVISOR", "COMISION"])
                        if _f_serv != "FIJA":
                            _sup_movil_det = construir_resumen_movil_general("Todos los meses")
                            if not _sup_movil_det.empty:
                                _sup_movil_det = _sup_movil_det.copy()
                                if "Venta Valida" in _sup_movil_det.columns:
                                    _sup_movil_det = _sup_movil_det[_sup_movil_det["Venta Valida"]].copy()
                                if _f_canal_sel and "Canal" in _sup_movil_det.columns:
                                    _sup_movil_det = _sup_movil_det[
                                        _sup_movil_det["Canal"].fillna("").astype(str).str.strip().str.upper()
                                        .isin([str(c).upper() for c in _f_canal_sel])
                                    ].copy()
                                if _f_finst:
                                    _sup_movil_det["_FINST_SUP"] = pd.to_datetime(_sup_movil_det.get("_FECHA_INSTALACION_DT", pd.NaT), errors="coerce")
                                    _sup_movil_det["_MES_INST_SUP"] = _sup_movil_det["_FINST_SUP"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                    _sup_movil_det = _sup_movil_det[_sup_movil_det["_MES_INST_SUP"].isin(_f_finst)].copy()
                                if _f_sup and "SUPERVISOR" in _sup_movil_det.columns:
                                    _sup_movil_det = _sup_movil_det[_sup_movil_det["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)].copy()
                                if _f_tipis and "TIPIS" in _sup_movil_det.columns:
                                    _tip_sup_mov = _sup_movil_det["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                                    _sup_movil_det = _sup_movil_det[_tip_sup_mov.isin([str(t).strip() for t in _f_tipis])].copy()
                                if _f_cola != "Todos" and "COLA" in _sup_movil_det.columns:
                                    _sup_movil_det = _sup_movil_det[_sup_movil_det["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola].copy()
                                if "Estado Pago" in _sup_movil_det.columns:
                                    _sup_movil_det = _sup_movil_det[_sup_movil_det["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"].copy()
                                else:
                                    _sup_movil_det = pd.DataFrame()
                                if not _sup_movil_det.empty:
                                    for _c in ["ASESOR", "SUPERVISOR", "COMISION"]:
                                        if _c not in _sup_movil_det.columns:
                                            _sup_movil_det[_c] = "" if _c != "COMISION" else 0
                                    _sup_movil_det["ASESOR"] = (_sup_movil_det["ASESOR"].fillna("Sin Asesor").astype(str)
                                                               .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Asesor").str.upper())
                                    _sup_movil_det["SUPERVISOR"] = (_sup_movil_det["SUPERVISOR"].fillna("Sin Supervisor").astype(str)
                                                                  .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Supervisor").str.upper())
                                    _sup_movil_det["COMISION"] = pd.to_numeric(_sup_movil_det["COMISION"], errors="coerce").fillna(0)
                                    _sup_movil_pag = _sup_movil_det[["ASESOR", "SUPERVISOR", "COMISION"]].copy()

                        _sup_base_rows = []
                        if not _sup_fija_pag.empty:
                            _tmp_sf = _sup_fija_pag[["SUPERVISOR", "ASESOR", "COMISION"]].copy()
                            _tmp_sf["Pagadas"] = 1
                            _tmp_sf["Netas 3 Meses"] = 0
                            _tmp_sf["Netas 6 Meses"] = 0
                            _sup_base_rows.append(_tmp_sf)
                        if not _sup_movil_pag.empty:
                            _tmp_sm = _sup_movil_pag[["SUPERVISOR", "ASESOR", "COMISION"]].copy()
                            _tmp_sm["Pagadas"] = 1
                            _tmp_sm["Netas 3 Meses"] = 0
                            _tmp_sm["Netas 6 Meses"] = 0
                            _sup_base_rows.append(_tmp_sm)

                        _sup_extra_rows = []
                        _sot_sup_map = _sup_fija_pag.copy()
                        if not _sot_sup_map.empty:
                            _sot_sup_map["_SOT_SUP"] = _normalizar_sot_series(_sot_sup_map["SOT"].fillna("").astype(str))
                            _sot_sup_map = _sot_sup_map[_sot_sup_map["_SOT_SUP"] != ""].drop_duplicates("_SOT_SUP")
                        _df_cf2_sup = cargar_csv("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
                        if not _df_cf2_sup.empty and not _sot_sup_map.empty:
                            _col_sot_cf2_sup = encontrar_columna(_df_cf2_sup, ["SOT", "Sot", "sot"])
                            _col_com_cf2_sup = encontrar_columna(_df_cf2_sup, ["COM ETAPA", "COM_ETAPA", "Com Etapa", "COMISION ETAPA", "COMISIÓN ETAPA", "COMISION", "COMISIÓN", "Comision"])
                            if _col_sot_cf2_sup and _col_com_cf2_sup:
                                _cf2_sup = _df_cf2_sup.copy()
                                _cf2_sup["_SOT_SUP"] = _normalizar_sot_series(_cf2_sup[_col_sot_cf2_sup].fillna("").astype(str))
                                _cf2_sup["COMISION"] = pd.to_numeric(_cf2_sup[_col_com_cf2_sup], errors="coerce").fillna(0)
                                _cf2_sup = _cf2_sup[(_cf2_sup["_SOT_SUP"] != "") & (_cf2_sup["COMISION"] > 0)].drop_duplicates("_SOT_SUP")
                                _cf2_sup = _cf2_sup.merge(_sot_sup_map[["_SOT_SUP", "ASESOR", "SUPERVISOR"]], on="_SOT_SUP", how="inner")
                                if not _cf2_sup.empty:
                                    _cf2_sup["Pagadas"] = 0
                                    _cf2_sup["Netas 3 Meses"] = 1
                                    _cf2_sup["Netas 6 Meses"] = 0
                                    _sup_extra_rows.append(_cf2_sup[["SUPERVISOR", "ASESOR", "COMISION", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"]])

                        _sec_sup_map = _sup_base[_sup_base["_TIPO_NPN"] == "MOVIL"].copy()
                        if not _sec_sup_map.empty:
                            _sec_sup_map["_SEC_SUP"] = _sec_sup_map["SEC"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                            _sec_sup_map = _sec_sup_map[_sec_sup_map["_SEC_SUP"] != ""].drop_duplicates("_SEC_SUP")

                        def _sup_caida_movil(_archivo, _net_col):
                            if _sec_sup_map.empty:
                                return pd.DataFrame(columns=["SUPERVISOR", "ASESOR", "COMISION", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"])
                            _df_c = cargar_csv(_archivo)
                            if _df_c.empty:
                                return pd.DataFrame(columns=["SUPERVISOR", "ASESOR", "COMISION", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"])
                            _col_sec_c = encontrar_columna(_df_c, ["SEC", "Sec", "sec"])
                            _col_com_c = encontrar_columna(_df_c, ["COMISION", "COMISIÓN", "Comision", "Comisión", "MONTO"])
                            if not (_col_sec_c and _col_com_c):
                                return pd.DataFrame(columns=["SUPERVISOR", "ASESOR", "COMISION", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"])
                            _df_c = _df_c.copy()
                            _df_c["_SEC_SUP"] = _df_c[_col_sec_c].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                            _df_c["COMISION"] = pd.to_numeric(_df_c[_col_com_c], errors="coerce").fillna(0)
                            _df_c = _df_c[(_df_c["_SEC_SUP"] != "") & (_df_c["COMISION"] > 0)].copy()
                            _df_c = _df_c.merge(_sec_sup_map[["_SEC_SUP", "ASESOR", "SUPERVISOR"]], on="_SEC_SUP", how="inner")
                            if _df_c.empty:
                                return pd.DataFrame(columns=["SUPERVISOR", "ASESOR", "COMISION", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"])
                            _df_c["Pagadas"] = 0
                            _df_c["Netas 3 Meses"] = 1 if _net_col == "Netas 3 Meses" else 0
                            _df_c["Netas 6 Meses"] = 1 if _net_col == "Netas 6 Meses" else 0
                            return _df_c[["SUPERVISOR", "ASESOR", "COMISION", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"]]

                        _sup_extra_rows.append(_sup_caida_movil("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv", "Netas 3 Meses"))
                        _sup_extra_rows.append(_sup_caida_movil("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv", "Netas 6 Meses"))

                        _sup_all_rows = _sup_base_rows + [x for x in _sup_extra_rows if x is not None and not x.empty]
                        if not _sup_all_rows:
                            st.info("Sin supervisores para los filtros seleccionados.")
                        else:
                            _sup_all = pd.concat(_sup_all_rows, ignore_index=True)
                            _sup_all["SUPERVISOR"] = _sup_all["SUPERVISOR"].fillna("SIN SUPERVISOR").astype(str).str.strip().replace("", "SIN SUPERVISOR").str.upper()
                            _sup_all["ASESOR"] = _sup_all["ASESOR"].fillna("SIN ASESOR").astype(str).str.strip().replace("", "SIN ASESOR").str.upper()
                            for _c in ["Pagadas", "Netas 3 Meses", "Netas 6 Meses", "COMISION"]:
                                _sup_all[_c] = pd.to_numeric(_sup_all[_c], errors="coerce").fillna(0)

                            _sup_tbl = (_sup_all.groupby("SUPERVISOR", as_index=False)
                                        .agg(Pagadas=("Pagadas", "sum"),
                                             **{"Netas 3 Meses": ("Netas 3 Meses", "sum"), "Netas 6 Meses": ("Netas 6 Meses", "sum")},
                                             Comision=("COMISION", "sum")))
                            _sup_tbl = _sup_tbl.sort_values(["Comision", "Pagadas", "Netas 3 Meses", "Netas 6 Meses"], ascending=[False, False, False, False]).reset_index(drop=True)

                            _ase_tbl = (_sup_all.groupby(["SUPERVISOR", "ASESOR"], as_index=False)
                                        .agg(Pagadas=("Pagadas", "sum"),
                                             **{"Netas 3 Meses": ("Netas 3 Meses", "sum"), "Netas 6 Meses": ("Netas 6 Meses", "sum")},
                                             Comision=("COMISION", "sum")))
                            _ase_tbl = _ase_tbl.sort_values(["SUPERVISOR", "Comision", "Pagadas"], ascending=[True, False, False])

                            _sup_rows_html = ""
                            for _i, _r in _sup_tbl.iterrows():
                                _sid = f"sup_{_i}"
                                _sup_name = str(_r["SUPERVISOR"])
                                _sup_rows_html += f"""<tr class=\"sup-row\">
                                    <td><button class=\"toggle\" onclick=\"toggleRows('{_sid}', this)\">+</button></td>
                                    <td class=\"rank-name\">{_html.escape(_sup_name)}</td>
                                    <td class=\"num\">{int(_r['Pagadas']):,}</td>
                                    <td class=\"num\">{int(_r['Netas 3 Meses']):,}</td>
                                    <td class=\"num\">{int(_r['Netas 6 Meses']):,}</td>
                                    <td class=\"num money\">S/ {_r['Comision']:,.2f}</td>
                                </tr>"""
                                _asesores_sup = _ase_tbl[_ase_tbl["SUPERVISOR"] == _sup_name]
                                for _, _a in _asesores_sup.iterrows():
                                    _sup_rows_html += f"""<tr class=\"child-row {_sid}\" style=\"display:none;\">
                                        <td></td>
                                        <td class=\"child-name\">{_html.escape(str(_a['ASESOR']))}</td>
                                        <td class=\"num\">{int(_a['Pagadas']):,}</td>
                                        <td class=\"num\">{int(_a['Netas 3 Meses']):,}</td>
                                        <td class=\"num\">{int(_a['Netas 6 Meses']):,}</td>
                                        <td class=\"num money child-money\">S/ {_a['Comision']:,.2f}</td>
                                    </tr>"""

                            _sup_html = f"""
                            <html><head><meta charset=\"utf-8\">
                            <style>
                                body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; color:#0f172a; }}
                                .rank-shell {{ border:1px solid #dbe3ef; border-radius:12px; overflow:hidden; background:#fff; box-shadow:0 12px 28px rgba(15,23,42,.08); }}
                                .rank-top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 16px; background:linear-gradient(90deg,#0f4287,#6d0b8c); color:#fff; }}
                                .rank-title {{ font-weight:900; letter-spacing:.06em; text-transform:uppercase; font-size:13px; }}
                                .rank-search {{ width:280px; max-width:48%; border:1px solid rgba(255,255,255,.35); border-radius:9px; padding:9px 11px; outline:0; color:#fff; background:rgba(255,255,255,.14); font-weight:700; }}
                                .rank-search::placeholder {{ color:rgba(255,255,255,.74); }}
                                .rank-scroll {{ max-height:500px; overflow:auto; }}
                                table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:12px; }}
                                thead th {{ position:sticky; top:0; z-index:2; background:#f1f5f9; color:#475569; text-align:left; padding:12px; text-transform:uppercase; font-size:10px; letter-spacing:.09em; border-bottom:1px solid #dbe3ef; }}
                                tbody td {{ padding:12px; border-bottom:1px solid #e5eaf1; font-weight:800; }}
                                tbody tr:hover {{ background:#f8fbff; }}
                                .toggle {{ width:26px; height:26px; border:0; border-radius:7px; color:#fff; background:#0f4287; font-weight:900; cursor:pointer; }}
                                .rank-name {{ font-weight:900; color:#111827; }}
                                .child-row {{ background:#f8fafc; }}
                                .child-name {{ padding-left:28px; color:#334155; font-weight:900; }}
                                .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
                                .money {{ color:#059669; font-weight:900; }}
                                .child-money {{ color:#047857; }}
                            </style></head>
                            <body>
                                <div class=\"rank-shell\">
                                    <div class=\"rank-top\">
                                        <div class=\"rank-title\">🏆 Ranking Supervisor</div>
                                        <input class=\"rank-search\" id=\"supSearch\" placeholder=\"Buscar supervisor o asesor\" oninput=\"filterSup()\">
                                    </div>
                                    <div class=\"rank-scroll\">
                                        <table id=\"supTable\">
                                            <thead><tr>
                                                <th></th><th>Supervisor</th>
                                                <th style=\"text-align:right;\">Pagadas</th>
                                                <th style=\"text-align:right;\">Netas 3 Meses</th>
                                                <th style=\"text-align:right;\">Netas 6 Meses</th>
                                                <th style=\"text-align:right;\">Comisión</th>
                                            </tr></thead>
                                            <tbody>{_sup_rows_html}</tbody>
                                        </table>
                                    </div>
                                </div>
                                <script>
                                    function toggleRows(cls, btn) {{
                                        const rows = document.querySelectorAll('.' + cls);
                                        const open = btn.textContent === '-';
                                        rows.forEach(r => r.style.display = open ? 'none' : 'table-row');
                                        btn.textContent = open ? '+' : '-';
                                    }}
                                    function filterSup() {{
                                        const q = document.getElementById('supSearch').value.toLowerCase();
                                        document.querySelectorAll('#supTable tbody tr').forEach(tr => {{
                                            tr.style.display = tr.innerText.toLowerCase().includes(q) ? '' : 'none';
                                        }});
                                    }}
                                </script>
                            </body></html>
                            """
                            _stc.html(_sup_html, height=610, scrolling=False)
                            st.download_button(
                                "⬇️ Descargar ranking supervisor",
                                data=_sup_tbl.to_csv(index=False).encode("utf-8-sig"),
                                file_name="ranking_supervisor_npn.csv",
                                mime="text/csv"
                            )
                    except Exception as _e_sup_rank:
                        st.warning(f"No se pudo construir Ranking Supervisor: {_e_sup_rank}")

                if _npn_subvista == "👥 Ranking Asesores":
                    try:
                        _rank_base = _dfp.copy()
                        for _c in ["ASESOR", "SUPERVISOR", "_TIPO_NPN", "Estado Pago", "COMISION", "SOT", "SEC"]:
                            if _c not in _rank_base.columns:
                                _rank_base[_c] = ""

                        _rank_base["ASESOR"] = (_rank_base["ASESOR"].fillna("Sin Asesor").astype(str)
                                                .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Asesor").str.upper())
                        _rank_base["SUPERVISOR"] = (_rank_base["SUPERVISOR"].fillna("Sin Supervisor").astype(str)
                                                   .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Supervisor").str.upper())
                        _rank_base["_TIPO_NPN"] = _rank_base["_TIPO_NPN"].fillna("").astype(str).str.strip().str.upper()
                        _rank_base["_ESTADO_RANK"] = _rank_base["Estado Pago"].fillna("NO PAGADA").astype(str).str.strip().str.upper()
                        _rank_base["_COMISION_RANK"] = pd.to_numeric(_rank_base["COMISION"], errors="coerce").fillna(0)
                        _rank_pag = _rank_base[_rank_base["_ESTADO_RANK"] == "PAGADA"].copy()

                        # Fija pagada se toma desde la misma fuente de Detalle Fija General,
                        # para que Ventas Fijas del ranking cuadre con sus Pagadas.
                        _rank_fija_pag = pd.DataFrame(columns=["ASESOR", "SUPERVISOR", "COMISION", "SOT"])
                        if _f_serv != "MOVIL":
                            _rank_fija_det = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                            if not _rank_fija_det.empty:
                                _rank_fija_det = _rank_fija_det.copy()
                                if _f_canal_sel and "Canal" in _rank_fija_det.columns:
                                    _rank_fija_det = _rank_fija_det[
                                        _rank_fija_det["Canal"].fillna("").astype(str).str.strip().str.upper()
                                        .isin([str(c).upper() for c in _f_canal_sel])
                                    ].copy()
                                if _f_finst and "FECHA INSTALACION" in _rank_fija_det.columns:
                                    _rank_fija_det["_FINST_RANK"] = pd.to_datetime(_rank_fija_det["FECHA INSTALACION"], errors="coerce", dayfirst=True)
                                    _rank_fija_det["_MES_INST_RANK"] = _rank_fija_det["_FINST_RANK"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                    _rank_fija_det = _rank_fija_det[_rank_fija_det["_MES_INST_RANK"].isin(_f_finst)].copy()
                                if _f_sup and "SUPERVISOR" in _rank_fija_det.columns:
                                    _rank_fija_det = _rank_fija_det[_rank_fija_det["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)].copy()
                                if _f_tipis and "TIPIS" in _rank_fija_det.columns:
                                    _tip_rank_fija = _rank_fija_det["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                                    _rank_fija_det = _rank_fija_det[_tip_rank_fija.isin([str(t).strip() for t in _f_tipis])].copy()
                                if _f_cola != "Todos" and "COLA" in _rank_fija_det.columns:
                                    _rank_fija_det = _rank_fija_det[_rank_fija_det["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola].copy()
                                if "Estado Pago" in _rank_fija_det.columns:
                                    _rank_fija_det = _rank_fija_det[
                                        _rank_fija_det["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                                    ].copy()
                                else:
                                    _rank_fija_det = pd.DataFrame()
                                if not _rank_fija_det.empty:
                                    for _c in ["ASESOR", "SUPERVISOR", "COMISION", "SOT"]:
                                        if _c not in _rank_fija_det.columns:
                                            _rank_fija_det[_c] = "" if _c != "COMISION" else 0
                                    _rank_fija_det["ASESOR"] = (_rank_fija_det["ASESOR"].fillna("Sin Asesor").astype(str)
                                                              .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Asesor").str.upper())
                                    _rank_fija_det["SUPERVISOR"] = (_rank_fija_det["SUPERVISOR"].fillna("Sin Supervisor").astype(str)
                                                                 .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Supervisor").str.upper())
                                    _rank_fija_det["COMISION"] = pd.to_numeric(_rank_fija_det["COMISION"], errors="coerce").fillna(0)
                                    _rank_fija_det["SOT"] = _rank_fija_det["SOT"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                                    _rank_fija_pag = _rank_fija_det[["ASESOR", "SUPERVISOR", "COMISION", "SOT"]].copy()

                        # Móvil pagado se toma desde la misma fuente de Detalle Móvil General,
                        # así el ranking cuadra con sus Pagadas por Fecha Instalación.
                        _rank_movil_pag = pd.DataFrame(columns=["ASESOR", "SUPERVISOR", "COMISION"])
                        if _f_serv != "FIJA":
                            _rank_movil_det = construir_resumen_movil_general("Todos los meses")
                            if not _rank_movil_det.empty:
                                _rank_movil_det = _rank_movil_det.copy()
                                if "Venta Valida" in _rank_movil_det.columns:
                                    _rank_movil_det = _rank_movil_det[_rank_movil_det["Venta Valida"]].copy()
                                if _f_canal_sel and "Canal" in _rank_movil_det.columns:
                                    _rank_movil_det = _rank_movil_det[
                                        _rank_movil_det["Canal"].fillna("").astype(str).str.strip().str.upper()
                                        .isin([str(c).upper() for c in _f_canal_sel])
                                    ].copy()
                                if _f_finst:
                                    _rank_movil_det["_FINST_RANK"] = pd.to_datetime(_rank_movil_det.get("_FECHA_INSTALACION_DT", pd.NaT), errors="coerce")
                                    _rank_movil_det["_MES_INST_RANK"] = _rank_movil_det["_FINST_RANK"].apply(
                                        lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                                    _rank_movil_det = _rank_movil_det[_rank_movil_det["_MES_INST_RANK"].isin(_f_finst)].copy()
                                if _f_sup and "SUPERVISOR" in _rank_movil_det.columns:
                                    _rank_movil_det = _rank_movil_det[_rank_movil_det["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)].copy()
                                if _f_tipis and "TIPIS" in _rank_movil_det.columns:
                                    _tip_rank_mov = _rank_movil_det["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Tipificación")
                                    _rank_movil_det = _rank_movil_det[_tip_rank_mov.isin([str(t).strip() for t in _f_tipis])].copy()
                                if _f_cola != "Todos" and "COLA" in _rank_movil_det.columns:
                                    _rank_movil_det = _rank_movil_det[_rank_movil_det["COLA"].fillna("EXTERNO").astype(str).str.strip() == _f_cola].copy()
                                if "Estado Pago" in _rank_movil_det.columns:
                                    _rank_movil_det = _rank_movil_det[
                                        _rank_movil_det["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                                    ].copy()
                                else:
                                    _rank_movil_det = pd.DataFrame()
                                if not _rank_movil_det.empty:
                                    for _c in ["ASESOR", "SUPERVISOR", "COMISION"]:
                                        if _c not in _rank_movil_det.columns:
                                            _rank_movil_det[_c] = "" if _c != "COMISION" else 0
                                    _rank_movil_det["ASESOR"] = (_rank_movil_det["ASESOR"].fillna("Sin Asesor").astype(str)
                                                               .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Asesor").str.upper())
                                    _rank_movil_det["SUPERVISOR"] = (_rank_movil_det["SUPERVISOR"].fillna("Sin Supervisor").astype(str)
                                                                  .str.replace(r"\s+", " ", regex=True).str.strip().replace("", "Sin Supervisor").str.upper())
                                    _rank_movil_det["COMISION"] = pd.to_numeric(_rank_movil_det["COMISION"], errors="coerce").fillna(0)
                                    _rank_movil_pag = _rank_movil_det[["ASESOR", "SUPERVISOR", "COMISION"]].copy()

                        _rank_people_parts = [_rank_base[["ASESOR", "SUPERVISOR"]]]
                        if not _rank_fija_pag.empty:
                            _rank_people_parts.append(_rank_fija_pag[["ASESOR", "SUPERVISOR"]])
                        if not _rank_movil_pag.empty:
                            _rank_people_parts.append(_rank_movil_pag[["ASESOR", "SUPERVISOR"]])
                        _rank_people = pd.concat(_rank_people_parts, ignore_index=True)
                        _rank_people["ASESOR"] = _rank_people["ASESOR"].fillna("Sin Asesor").astype(str).str.strip().replace("", "Sin Asesor").str.upper()
                        _rank_people["SUPERVISOR"] = _rank_people["SUPERVISOR"].fillna("Sin Supervisor").astype(str).str.strip().replace("", "Sin Supervisor").str.upper()
                        if _rank_people.empty:
                            _rank_tbl = pd.DataFrame(columns=["ASESOR", "SUPERVISOR"])
                        else:
                            _rank_sup = (_rank_people.groupby(["ASESOR", "SUPERVISOR"]).size()
                                         .reset_index(name="_SUP_COUNT")
                                         .sort_values(["ASESOR", "_SUP_COUNT"], ascending=[True, False]))
                            _rank_tbl = _rank_sup.drop_duplicates("ASESOR")[["ASESOR", "SUPERVISOR"]].reset_index(drop=True)

                        def _rank_merge_count(_tipo, _colname):
                            nonlocal_rank = _rank_pag[_rank_pag["_TIPO_NPN"] == _tipo]
                            if nonlocal_rank.empty:
                                _tmp_count = pd.DataFrame(columns=["ASESOR", _colname])
                            else:
                                _tmp_count = nonlocal_rank.groupby("ASESOR").size().reset_index(name=_colname)
                            return _tmp_count

                        for _colname in ["Ventas Fijas", "Ventas Moviles", "Netas 3 Meses", "Netas 6 Meses", "Comision Total"]:
                            _rank_tbl[_colname] = 0

                        for _tmp_count, _target in [
                            ((_rank_fija_pag.groupby("ASESOR").size().reset_index(name="Ventas Fijas")
                              if not _rank_fija_pag.empty else pd.DataFrame(columns=["ASESOR", "Ventas Fijas"])), "Ventas Fijas"),
                            ((_rank_movil_pag.groupby("ASESOR").size().reset_index(name="Ventas Moviles")
                              if not _rank_movil_pag.empty else pd.DataFrame(columns=["ASESOR", "Ventas Moviles"])), "Ventas Moviles")
                        ]:
                            if not _tmp_count.empty:
                                _rank_tbl = _rank_tbl.drop(columns=[_target], errors="ignore").merge(
                                    _tmp_count, on="ASESOR", how="left")
                                _rank_tbl[_target] = pd.to_numeric(_rank_tbl[_target], errors="coerce").fillna(0).astype(int)

                        _base_com_parts = []
                        if not _rank_fija_pag.empty:
                            _base_com_parts.append(
                                _rank_fija_pag.groupby("ASESOR")["COMISION"].sum().reset_index(name="_COM_BASE")
                            )
                        if not _rank_movil_pag.empty:
                            _base_com_parts.append(
                                _rank_movil_pag.groupby("ASESOR")["COMISION"].sum().reset_index(name="_COM_BASE")
                            )
                        _base_com = (
                            pd.concat(_base_com_parts, ignore_index=True).groupby("ASESOR", as_index=False)["_COM_BASE"].sum()
                            if _base_com_parts else pd.DataFrame(columns=["ASESOR", "_COM_BASE"])
                        )
                        if not _base_com.empty:
                            _rank_tbl = _rank_tbl.merge(_base_com, on="ASESOR", how="left")
                            _rank_tbl["Comision Total"] = pd.to_numeric(_rank_tbl["_COM_BASE"], errors="coerce").fillna(0)
                            _rank_tbl = _rank_tbl.drop(columns=["_COM_BASE"], errors="ignore")

                        _extra_rows = []

                        # FIJA 3M: SOT unica, siguiendo la misma regla de NPN fija.
                        _sot_map = _rank_fija_pag.copy()
                        if not _sot_map.empty:
                            _sot_map["_SOT_RANK"] = _normalizar_sot_series(_sot_map["SOT"].fillna("").astype(str))
                            _sot_map = _sot_map[_sot_map["_SOT_RANK"] != ""].drop_duplicates("_SOT_RANK")
                        _df_cf2_rank = cargar_csv("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
                        if not _df_cf2_rank.empty and not _sot_map.empty:
                            _col_sot_cf2_rank = encontrar_columna(_df_cf2_rank, ["SOT", "Sot", "sot"])
                            _col_com_cf2_rank = encontrar_columna(_df_cf2_rank, [
                                "COM ETAPA", "COM_ETAPA", "Com Etapa", "COMISION ETAPA", "COMISIÓN ETAPA",
                                "COMISION", "COMISIÓN", "Comision"
                            ])
                            if _col_sot_cf2_rank and _col_com_cf2_rank:
                                _cf2_rank = _df_cf2_rank.copy()
                                _cf2_rank["_SOT_RANK"] = _normalizar_sot_series(_cf2_rank[_col_sot_cf2_rank].fillna("").astype(str))
                                _cf2_rank["_COM_CAIDA"] = pd.to_numeric(_cf2_rank[_col_com_cf2_rank], errors="coerce").fillna(0)
                                _cf2_rank = _cf2_rank[(_cf2_rank["_SOT_RANK"] != "") & (_cf2_rank["_COM_CAIDA"] > 0)].drop_duplicates("_SOT_RANK")
                                _cf2_rank = _cf2_rank.merge(_sot_map[["_SOT_RANK", "ASESOR"]], on="_SOT_RANK", how="inner")
                                if not _cf2_rank.empty:
                                    _extra_rows.append(_cf2_rank.assign(_NETAS_3=1, _NETAS_6=0)[["ASESOR", "_NETAS_3", "_NETAS_6", "_COM_CAIDA"]])

                        # MOVIL 3M/6M: SEC con duplicados, como se pidio para movil.
                        _sec_map = _rank_base[_rank_base["_TIPO_NPN"] == "MOVIL"].copy()
                        if not _sec_map.empty:
                            _sec_map["_SEC_RANK"] = _sec_map["SEC"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                            _sec_map = _sec_map[_sec_map["_SEC_RANK"] != ""].drop_duplicates("_SEC_RANK")

                        def _rank_caida_movil(_archivo, _netas_col):
                            if _sec_map.empty:
                                return pd.DataFrame(columns=["ASESOR", "_NETAS_3", "_NETAS_6", "_COM_CAIDA"])
                            _df_c = cargar_csv(_archivo)
                            if _df_c.empty:
                                return pd.DataFrame(columns=["ASESOR", "_NETAS_3", "_NETAS_6", "_COM_CAIDA"])
                            _col_sec_c = encontrar_columna(_df_c, ["SEC", "Sec", "sec"])
                            _col_com_c = encontrar_columna(_df_c, ["COMISION", "COMISIÓN", "Comision", "Comisión", "MONTO"])
                            if not (_col_sec_c and _col_com_c):
                                return pd.DataFrame(columns=["ASESOR", "_NETAS_3", "_NETAS_6", "_COM_CAIDA"])
                            _df_c = _df_c.copy()
                            _df_c["_SEC_RANK"] = _df_c[_col_sec_c].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                            _df_c["_COM_CAIDA"] = pd.to_numeric(_df_c[_col_com_c], errors="coerce").fillna(0)
                            _df_c = _df_c[(_df_c["_SEC_RANK"] != "") & (_df_c["_COM_CAIDA"] > 0)].copy()
                            _df_c = _df_c.merge(_sec_map[["_SEC_RANK", "ASESOR"]], on="_SEC_RANK", how="inner")
                            if _df_c.empty:
                                return pd.DataFrame(columns=["ASESOR", "_NETAS_3", "_NETAS_6", "_COM_CAIDA"])
                            _df_c["_NETAS_3"] = 1 if _netas_col == "_NETAS_3" else 0
                            _df_c["_NETAS_6"] = 1 if _netas_col == "_NETAS_6" else 0
                            return _df_c[["ASESOR", "_NETAS_3", "_NETAS_6", "_COM_CAIDA"]]

                        _extra_rows.append(_rank_caida_movil("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv", "_NETAS_3"))
                        _extra_rows.append(_rank_caida_movil("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv", "_NETAS_6"))

                        _extra_df = pd.concat([x for x in _extra_rows if x is not None and not x.empty], ignore_index=True) if _extra_rows else pd.DataFrame()
                        if not _extra_df.empty:
                            _extra_grp = (_extra_df.groupby("ASESOR")
                                          .agg(_NETAS_3=("_NETAS_3", "sum"), _NETAS_6=("_NETAS_6", "sum"), _COM_EXTRA=("_COM_CAIDA", "sum"))
                                          .reset_index())
                            _rank_tbl = _rank_tbl.merge(_extra_grp, on="ASESOR", how="left")
                            _rank_tbl["Netas 3 Meses"] = pd.to_numeric(_rank_tbl.get("Netas 3 Meses", 0), errors="coerce").fillna(0) + pd.to_numeric(_rank_tbl["_NETAS_3"], errors="coerce").fillna(0)
                            _rank_tbl["Netas 6 Meses"] = pd.to_numeric(_rank_tbl.get("Netas 6 Meses", 0), errors="coerce").fillna(0) + pd.to_numeric(_rank_tbl["_NETAS_6"], errors="coerce").fillna(0)
                            _rank_tbl["Comision Total"] = pd.to_numeric(_rank_tbl.get("Comision Total", 0), errors="coerce").fillna(0) + pd.to_numeric(_rank_tbl["_COM_EXTRA"], errors="coerce").fillna(0)
                            _rank_tbl = _rank_tbl.drop(columns=["_NETAS_3", "_NETAS_6", "_COM_EXTRA"], errors="ignore")

                        if not _rank_tbl.empty:
                            for _c in ["Ventas Fijas", "Ventas Moviles", "Netas 3 Meses", "Netas 6 Meses"]:
                                _rank_tbl[_c] = pd.to_numeric(_rank_tbl[_c], errors="coerce").fillna(0).astype(int)
                            _rank_tbl["Comision Total"] = pd.to_numeric(_rank_tbl["Comision Total"], errors="coerce").fillna(0)
                            _rank_tbl = _rank_tbl[
                                (_rank_tbl["Ventas Fijas"] > 0) |
                                (_rank_tbl["Ventas Moviles"] > 0) |
                                (_rank_tbl["Netas 3 Meses"] > 0) |
                                (_rank_tbl["Netas 6 Meses"] > 0) |
                                (_rank_tbl["Comision Total"] > 0)
                            ].copy()
                            _rank_tbl = _rank_tbl.sort_values(
                                ["Comision Total", "Ventas Fijas", "Ventas Moviles", "Netas 3 Meses", "Netas 6 Meses"],
                                ascending=[False, False, False, False, False]
                            ).reset_index(drop=True)

                        if _rank_tbl.empty:
                            st.info("Sin asesores para los filtros seleccionados.")
                        else:
                            _rank_rows_html = ""
                            for _i, _r in _rank_tbl.iterrows():
                                _rank_rows_html += f"""<tr>
                                    <td class=\"rank-pos\">{_i + 1}</td>
                                    <td class=\"rank-name\">{_html.escape(str(_r['ASESOR']))}</td>
                                    <td>{_html.escape(str(_r['SUPERVISOR']))}</td>
                                    <td class=\"num\">{int(_r['Ventas Fijas']):,}</td>
                                    <td class=\"num\">{int(_r['Ventas Moviles']):,}</td>
                                    <td class=\"num\">{int(_r['Netas 3 Meses']):,}</td>
                                    <td class=\"num\">{int(_r['Netas 6 Meses']):,}</td>
                                    <td class=\"num money\">S/ {_r['Comision Total']:,.2f}</td>
                                </tr>"""

                            _rank_html = f"""
                            <html><head><meta charset=\"utf-8\">
                            <style>
                                body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; color:#0f172a; }}
                                .rank-shell {{ border:1px solid #dbe3ef; border-radius:12px; overflow:hidden; background:#fff; box-shadow:0 12px 28px rgba(15,23,42,.08); }}
                                .rank-top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 16px; background:linear-gradient(90deg,#0f4287,#6d0b8c); color:#fff; }}
                                .rank-title {{ font-weight:900; letter-spacing:.06em; text-transform:uppercase; font-size:13px; }}
                                .rank-search {{ width:260px; max-width:48%; border:1px solid rgba(255,255,255,.35); border-radius:9px; padding:9px 11px; outline:0; color:#fff; background:rgba(255,255,255,.14); font-weight:700; }}
                                .rank-search::placeholder {{ color:rgba(255,255,255,.74); }}
                                .rank-scroll {{ max-height:480px; overflow:auto; }}
                                table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:12px; }}
                                thead th {{ position:sticky; top:0; z-index:2; background:#f1f5f9; color:#475569; text-align:left; padding:12px 12px; text-transform:uppercase; font-size:10px; letter-spacing:.09em; border-bottom:1px solid #dbe3ef; }}
                                tbody td {{ padding:12px; border-bottom:1px solid #e5eaf1; font-weight:700; }}
                                tbody tr:hover {{ background:#f8fbff; }}
                                .rank-pos {{ width:42px; color:#0f4287; font-weight:900; }}
                                .rank-name {{ font-weight:900; color:#111827; }}
                                .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
                                .money {{ color:#059669; font-weight:900; }}
                                @media (max-width:760px) {{ .rank-top {{ align-items:flex-start; flex-direction:column; }} .rank-search {{ max-width:none; width:100%; }} table {{ font-size:11px; }} thead th, tbody td {{ padding:10px 8px; }} }}
                            </style></head>
                            <body>
                                <div class=\"rank-shell\">
                                    <div class=\"rank-top\">
                                        <div class=\"rank-title\">👥 Ranking Asesores</div>
                                        <input class=\"rank-search\" id=\"rankSearch\" placeholder=\"Buscar asesor o supervisor\" oninput=\"filterRank()\">
                                    </div>
                                    <div class=\"rank-scroll\">
                                        <table id=\"rankTable\">
                                            <thead><tr>
                                                <th>#</th><th>Nombre del asesor</th><th>Supervisor</th>
                                                <th style=\"text-align:right;\">Ventas fijas</th>
                                                <th style=\"text-align:right;\">Ventas moviles</th>
                                                <th style=\"text-align:right;\">Netas 3 Meses</th>
                                                <th style=\"text-align:right;\">Netas 6 Meses</th>
                                                <th style=\"text-align:right;\">Comisión Total</th>
                                            </tr></thead>
                                            <tbody>{_rank_rows_html}</tbody>
                                        </table>
                                    </div>
                                </div>
                                <script>
                                    function filterRank() {{
                                        const q = document.getElementById('rankSearch').value.toLowerCase();
                                        document.querySelectorAll('#rankTable tbody tr').forEach(tr => {{
                                            tr.style.display = tr.innerText.toLowerCase().includes(q) ? '' : 'none';
                                        }});
                                    }}
                                </script>
                            </body></html>
                            """
                            _stc.html(_rank_html, height=590, scrolling=False)
                            st.download_button(
                                "⬇️ Descargar ranking asesores",
                                data=_rank_tbl.rename(columns={
                                    "ASESOR": "Nombre del asesor",
                                    "SUPERVISOR": "Supervisor"
                                }).to_csv(index=False).encode("utf-8-sig"),
                                file_name="ranking_asesores_npn.csv",
                                mime="text/csv"
                            )
                    except Exception as _e_rank:
                        st.warning(f"No se pudo construir Ranking Asesores: {_e_rank}")

        elif opcion_factor == "💼 Comisión Operativa":
            set_bg(img_caratula)
            st.markdown("""
            <style>
            .op-header-wrap {display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,rgba(15,66,135,.90),rgba(109,11,140,.82));border-radius:14px;padding:20px 28px;margin-bottom:18px;box-shadow:0 4px 20px rgba(15,66,135,.20);border:1px solid rgba(255,255,255,.12);}
            .op-kicker {font-size:10px;font-weight:900;color:rgba(255,255,255,.68);letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px;}
            .op-title {font-size:26px;font-weight:950;color:#fff;letter-spacing:.06em;line-height:1.1;}
            .op-sub {font-size:11px;color:rgba(255,255,255,.66);letter-spacing:.1em;text-transform:uppercase;margin-top:5px;}
            .op-badge {display:inline-block;color:#fff;font-weight:900;font-size:11px;border-radius:999px;padding:5px 13px;margin:3px;border:1.5px solid rgba(255,255,255,.32);background:rgba(255,255,255,.12);}
            div[data-testid="stVerticalBlock"]:has(div.op-filter-anchor) {background:rgba(255,255,255,.78);border:1px solid rgba(15,66,135,.12);border-radius:14px;padding:16px 18px 12px 18px;margin:4px 0 14px 0;box-shadow:0 14px 34px rgba(15,23,42,.08);backdrop-filter:blur(8px);}
            .op-kpi-row {display:flex;gap:12px;margin:14px 0 16px 0;flex-wrap:wrap;}
            .op-kpi-card {flex:1;min-width:160px;background:rgba(255,255,255,.96);border-radius:12px;padding:16px 18px;text-align:left;box-shadow:0 3px 14px rgba(0,0,0,.08);border-top:4px solid #0f4287;}
            .op-kpi-label {font-size:9px;font-weight:900;color:#64748b;letter-spacing:.12em;text-transform:uppercase;margin-bottom:7px;}
            .op-kpi-val {font-size:27px;font-weight:950;color:#0f4287;line-height:1.05;}
            .op-kpi-sub {font-size:10px;color:#64748b;margin-top:6px;font-weight:800;}
            </style>
            <div class="op-header-wrap">
                <div><div class="op-kicker">Módulo Ejecutivo</div><div class="op-title">COMISIÓN OPERATIVA</div><div class="op-sub">Pagos mensuales desde OPERATIVA_TELETALK</div></div>
                <div style="text-align:right;"><span class="op-badge">D&amp;C Digital Group</span><br><span class="op-badge">Teletalk SAC</span></div>
            </div>
            """, unsafe_allow_html=True)

            _ruta_op = next((os.path.join(DATA_DIR, n) for n in ["OPERATIVA_TELETALK.csv", "OPERATIVA_TELETALK.xlsx", "OPERATIVA_TELETALK.xls"] if os.path.exists(os.path.join(DATA_DIR, n))), None)
            _mtime_op = os.path.getmtime(_ruta_op) if _ruta_op else None
            _df_op = _leer_operativa_teletalk_cacheado(_mtime_op)

            def _op_col(df, opciones):
                return encontrar_columna(df, opciones) if df is not None and not df.empty else None

            def _op_clean_id(serie):
                return serie.fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

            def _op_parse_fecha(serie):
                s = _op_clean_id(serie)
                s8 = s.where(s.str.match(r"^\d{8}$"), "")
                dt = pd.to_datetime(s8, format="%Y%m%d", errors="coerce")
                fallback = pd.to_datetime(serie, errors="coerce", dayfirst=True)
                return dt.fillna(fallback)

            def _op_num(serie):
                raw = serie.fillna("").astype(str).str.replace("S/", "", regex=False).str.replace(" ", "", regex=False)
                parsed = pd.to_numeric(raw, errors="coerce")
                alt = pd.to_numeric(raw.str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
                return parsed.fillna(alt).fillna(0)

            if _df_op.empty:
                st.warning("No se encontró OPERATIVA_TELETALK.csv/xlsx o no se pudo leer. Verifica que esté en la carpeta de datos.")
            else:
                _df_op = _df_op.copy()
                _df_op.columns = _df_op.columns.astype(str).str.strip()
                _col_dist = _op_col(_df_op, ["DISTRIBUIDOR", "Distribuidor"])
                _col_linea = _op_col(_df_op, ["NRO_LINEA", "NRO LINEA", "Nro Linea"])
                _col_sot = _op_col(_df_op, ["SOT", "Sot"])
                _col_fact = _op_col(_df_op, ["FECHA_ACTIVACION", "FECHA ACTIVACION", "Fecha Activacion"])
                _col_finst = _op_col(_df_op, ["FECHA_INSTALACION", "FECHA INSTALACION", "Fecha Instalacion"])
                _col_total = _op_col(_df_op, ["TOTAL", "Total"])

                if not (_col_dist and _col_total):
                    st.error("OPERATIVA_TELETALK no tiene las columnas mínimas requeridas: DISTRIBUIDOR y TOTAL.")
                else:
                    _dist_norm = _df_op[_col_dist].fillna("").astype(str).str.upper()
                    _df_op["Canal"] = "OTROS"
                    _df_op.loc[_dist_norm.str.contains("DYC|D&C|DIGITAL", regex=True, na=False), "Canal"] = "D&C"
                    _df_op.loc[_dist_norm.str.contains("TELETALK", regex=False, na=False), "Canal"] = "Teletalk"
                    _sot_ok = _op_clean_id(_df_op[_col_sot]) != "" if _col_sot else pd.Series(False, index=_df_op.index)
                    _linea_ok = _op_clean_id(_df_op[_col_linea]) != "" if _col_linea else pd.Series(False, index=_df_op.index)
                    _df_op["Servicio"] = "FIJA"
                    _df_op.loc[(~_sot_ok) & _linea_ok, "Servicio"] = "MOVIL"
                    _dt_act = _op_parse_fecha(_df_op[_col_fact]) if _col_fact else pd.Series(pd.NaT, index=_df_op.index)
                    _dt_inst = _op_parse_fecha(_df_op[_col_finst]) if _col_finst else pd.Series(pd.NaT, index=_df_op.index)
                    _df_op["_FECHA_BASE"] = _dt_inst.where(_df_op["Servicio"].eq("FIJA"), _dt_act).fillna(_dt_act).fillna(_dt_inst)
                    _df_op["Fecha usada"] = "Instalación"
                    _df_op.loc[_df_op["Servicio"].eq("MOVIL"), "Fecha usada"] = "Activación"
                    _df_op.loc[_df_op["_FECHA_BASE"].eq(_dt_act) & _dt_inst.isna(), "Fecha usada"] = "Activación"
                    _df_op.loc[_df_op["_FECHA_BASE"].eq(_dt_inst) & _dt_act.isna(), "Fecha usada"] = "Instalación"
                    _df_op = _df_op[_df_op["_FECHA_BASE"].notna()].copy()
                    _df_op["Mes"] = _df_op["_FECHA_BASE"].apply(lambda d: f"{MESES_ES[d.month]} {d.year}" if pd.notna(d) else "")
                    _df_op["_SORT"] = _df_op["_FECHA_BASE"].dt.year * 100 + _df_op["_FECHA_BASE"].dt.month
                    _df_op["Total pagado"] = _op_num(_df_op[_col_total])
                    _meses_op = _df_op[["Mes", "_SORT"]].drop_duplicates().sort_values("_SORT")["Mes"].tolist()
                    st.markdown('<div class="op-filter-anchor"></div>', unsafe_allow_html=True)
                    _c1, _c2, _c3 = st.columns(3)
                    with _c1:
                        _f_serv_op = st.selectbox("Servicio", ["Todos", "FIJA", "MOVIL"], key="op_servicio")
                    with _c2:
                        _f_canal_op = st.multiselect("Canal", ["D&C", "Teletalk"], default=[], placeholder="Todos los canales", key="op_canal")
                    with _c3:
                        _f_mes_op = st.multiselect("Mes", _meses_op, default=[], placeholder="Todos los meses", key="op_mes")
                    _df_fil = _df_op.copy()
                    if _f_serv_op != "Todos": _df_fil = _df_fil[_df_fil["Servicio"] == _f_serv_op]
                    if _f_canal_op: _df_fil = _df_fil[_df_fil["Canal"].isin(_f_canal_op)]
                    if _f_mes_op: _df_fil = _df_fil[_df_fil["Mes"].isin(_f_mes_op)]
                    _total_op = float(_df_fil["Total pagado"].sum()) if not _df_fil.empty else 0.0
                    _reg_op = int(len(_df_fil))
                    _fija_op = float(_df_fil.loc[_df_fil["Servicio"].eq("FIJA"), "Total pagado"].sum()) if not _df_fil.empty else 0.0
                    _movil_op = float(_df_fil.loc[_df_fil["Servicio"].eq("MOVIL"), "Total pagado"].sum()) if not _df_fil.empty else 0.0
                    _prom_op = (_total_op / _reg_op) if _reg_op else 0.0
                    st.markdown(f"""
                    <div class="op-kpi-row">
                        <div class="op-kpi-card" style="border-top-color:#0f4287;"><div class="op-kpi-label">Total pagado</div><div class="op-kpi-val">S/ {_total_op:,.2f}</div><div class="op-kpi-sub">Suma columna TOTAL</div></div>
                        <div class="op-kpi-card" style="border-top-color:#059669;"><div class="op-kpi-label">Registros</div><div class="op-kpi-val">{_reg_op:,}</div><div class="op-kpi-sub">Filas consideradas</div></div>
                        <div class="op-kpi-card" style="border-top-color:#7c3aed;"><div class="op-kpi-label">Fija</div><div class="op-kpi-val">S/ {_fija_op:,.2f}</div><div class="op-kpi-sub">SOT lleno o NRO_LINEA vacío</div></div>
                        <div class="op-kpi-card" style="border-top-color:#0891b2;"><div class="op-kpi-label">Móvil</div><div class="op-kpi-val">S/ {_movil_op:,.2f}</div><div class="op-kpi-sub">SOT vacío y NRO_LINEA lleno</div></div>
                        <div class="op-kpi-card" style="border-top-color:#ea580c;"><div class="op-kpi-label">Promedio</div><div class="op-kpi-val">S/ {_prom_op:,.2f}</div><div class="op-kpi-sub">Total / registros</div></div>
                    </div>""", unsafe_allow_html=True)
                    _tabla_op = (_df_fil.groupby(["_SORT", "Mes", "Canal", "Servicio", "Fecha usada"], dropna=False).agg(Registros=("Total pagado", "size"), **{"Total pagado": ("Total pagado", "sum")}).reset_index().sort_values(["_SORT", "Canal", "Servicio"]).drop(columns=["_SORT"]))
                    if not _tabla_op.empty:
                        _tabla_op["Total pagado"] = _tabla_op["Total pagado"].map(lambda x: f"S/ {float(x):,.2f}")
                    java_table(_tabla_op, height=430, title="Comisión Operativa", subtitle="Resumen por mes, canal y servicio desde OPERATIVA_TELETALK", accent="#0f4287", max_rows=500)

    elif seccion == "fija":

        if opcion == "Inicio: Reporte Comparativo FIJA":
            set_bg(img_caratula)
            st.markdown('''<div class="caratula-hero">
                <div class="caratula-badge">📡 LÍNEA FIJA &nbsp;·&nbsp; REPORTE EJECUTIVO</div>
                <div class="main-title">REPORTE <span class="title-accent">COMPARATIVO</span></div>
                <div class="caratula-divider"></div>
                <div class="sub-title">D&amp;C DIGITAL GROUP &nbsp;&nbsp;·&nbsp;&nbsp; TELETALK CONTACT CENTER</div>
            </div>''', unsafe_allow_html=True)

            st.markdown("""
            <style>
            .tbl-canal-title {font-size:17px;font-weight:900;letter-spacing:.08em;padding:10px 0 6px 2px;margin-top:18px;}
            .tbl-canal-dc    {color:#0057b8;}
            .tbl-canal-tt    {color:#70008f;}
            </style>""", unsafe_allow_html=True)

            def _col_like(df, opciones):
                norm = {str(c).strip().lower(): c for c in df.columns}
                for op in opciones:
                    hit = norm.get(str(op).strip().lower())
                    if hit is not None:
                        return hit
                for c in df.columns:
                    cl = str(c).strip().lower()
                    if any(str(op).strip().lower() in cl for op in opciones):
                        return c
                return None

            def _norm_cmp_txt(s):
                return (str(s).upper().strip()
                        .replace("?", "A").replace("?", "E").replace("?", "I")
                        .replace("?", "O").replace("?", "U")
                        .replace("??", "A").replace("??", "E").replace("??", "I")
                        .replace("??", "O").replace("??", "U"))

            _df_cmp_dvz = _leer_dvz_crudo().copy()
            _cmp_comision_cache = {}

            def _norm_cmp_id(serie):
                return serie.fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

            def _mapa_comision_claro_fija(canal):
                canal_key = "TELETALK" if str(canal).upper().startswith("TELE") else "D&C"
                if canal_key in _cmp_comision_cache:
                    return _cmp_comision_cache[canal_key]
                archivo = "CLARO_TELETALK_FIJA.csv" if canal_key == "TELETALK" else "CLARO_DC_FIJA.csv"
                claro = cargar_csv(archivo)
                if claro.empty:
                    _cmp_comision_cache[canal_key] = {}
                    return _cmp_comision_cache[canal_key]
                col_sot_claro = encontrar_columna(claro, ["SOT", "Sot", "sot"])
                if not col_sot_claro:
                    _cmp_comision_cache[canal_key] = {}
                    return _cmp_comision_cache[canal_key]
                tmp = claro.copy()
                tmp["_SOT_CMP"] = _norm_cmp_id(tmp[col_sot_claro])
                tmp["_COM_CMP_CLARO"] = obtener_comision_fija(tmp)
                tmp = tmp[tmp["_SOT_CMP"] != ""]
                _cmp_comision_cache[canal_key] = tmp.groupby("_SOT_CMP")["_COM_CMP_CLARO"].sum().to_dict()
                return _cmp_comision_cache[canal_key]

            def _resumir_por_canal_fija(canal):
                df = _df_cmp_dvz.copy()
                if df.empty:
                    return pd.DataFrame(columns=["MES", "VENTAS BRUTAS", "VENTAS NETAS", "% CAIDA", "% TV", "PROMEDIO PRIME", "COMISION"])

                col_tipo = _col_like(df, ["Tipo Producto", "product_type"])
                col_canal = _col_like(df, ["Datos adicionales - Clip", "Datos Adicionales - Clip", "clip"])
                col_fecha = _col_like(df, ["FECHA DE VENTA", "Fecha de Venta", "Fecha Venta", "venta_start_date"])
                col_estado = _col_like(df, ["Estados - Venta", "Estados - Estado Venta", "Estado Venta", "sale_state"])
                col_tipis = _col_like(df, ["Estados - Venta Especificacion", "Estados - Venta Especificaci?n", "Venta Especificacion", "saleSub_state", "TIPIS"])
                col_producto = _col_like(df, ["Productos - producto", "Productos - Producto", "product"])
                col_com = _col_like(df, ["COMISION", "COMISI?N", "Comision", "MONTO"])
                col_sot = _col_like(df, ["Back Office - SOT", "Back Office - Sot", "SOT", "sot"])

                if col_tipo:
                    df = df[df[col_tipo].fillna("").astype(str).map(_norm_cmp_txt).eq("FIJA")].copy()
                if col_canal:
                    canal_key = "TELETALK" if str(canal).upper().startswith("TELE") else "D&C"
                    df = df[df[col_canal].fillna("").astype(str).map(_norm_cmp_txt).eq(canal_key)].copy()
                if df.empty or not col_fecha:
                    return pd.DataFrame(columns=["MES", "VENTAS BRUTAS", "VENTAS NETAS", "% CAIDA", "% TV", "PROMEDIO PRIME", "COMISION"])

                df["_FECHA_CMP"] = _parse_fecha_movil_robusta(df[col_fecha])
                df = df[df["_FECHA_CMP"].notna()].copy()
                df["_MES_CMP"] = df["_FECHA_CMP"].apply(lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}")
                df = df[df["_MES_CMP"].map(_mes_label_permitido)].copy()
                if df.empty:
                    return pd.DataFrame(columns=["MES", "VENTAS BRUTAS", "VENTAS NETAS", "% CAIDA", "% TV", "PROMEDIO PRIME", "COMISION"])

                if col_sot:
                    mapa_com = _mapa_comision_claro_fija(canal)
                    df["_COM_CMP"] = _norm_cmp_id(df[col_sot]).map(mapa_com).fillna(0)
                else:
                    df["_COM_CMP"] = pd.to_numeric(df[col_com], errors="coerce").fillna(0) if col_com else 0.0
                df["_NETA_CMP"] = pd.to_numeric(df["_COM_CMP"], errors="coerce").fillna(0) > 0
                if col_producto:
                    prod_norm = df[col_producto].fillna("").astype(str).map(_norm_cmp_txt)
                    planes_tv = {_norm_cmp_txt(p) for p in globals().get("_PLANES_TV", [])}
                    df["_TV_CMP"] = prod_norm.isin(planes_tv)
                else:
                    df["_TV_CMP"] = False

                rows = []
                for mes, grp in df.groupby("_MES_CMP"):
                    brutas = int(len(grp))
                    netas = int(grp["_NETA_CMP"].sum())
                    caidas = max(brutas - netas, 0)
                    com = float(pd.to_numeric(grp["_COM_CMP"], errors="coerce").fillna(0).sum())
                    tv_pag = int((grp["_NETA_CMP"] & grp["_TV_CMP"]).sum())
                    pct_tv = (tv_pag / netas * 100) if netas else 0.0
                    ticket = (com / netas) if netas else 0.0
                    m_num, y_num = parse_mes_anio(mes)
                    rows.append({
                        "MES": mes,
                        "VENTAS BRUTAS": brutas,
                        "VENTAS NETAS": netas,
                        "% CAIDA": (caidas / brutas * 100) if brutas else 0.0,
                        "% TV": pct_tv,
                        "PROMEDIO PRIME": ticket,
                        "COMISION": com,
                        "_sort": (y_num or 0, m_num or 0),
                    })
                return pd.DataFrame(rows).sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

            def _tabla_comparativa_fija_html(tbl, titulo, subtitulo, color, accent):
                if tbl.empty:
                    return f'<div class="cmp-card" style="--cmp:{color};--accent:{accent};"><div class="cmp-head"><div><div class="cmp-title">{titulo}</div><div class="cmp-sub">{subtitulo}</div></div><div class="cmp-pill">FIJA</div></div><div class="cmp-empty">Sin datos disponibles</div></div>'
                total_brutas = int(pd.to_numeric(tbl["VENTAS BRUTAS"], errors="coerce").fillna(0).sum())
                total_netas = int(pd.to_numeric(tbl["VENTAS NETAS"], errors="coerce").fillna(0).sum())
                total_com = float(pd.to_numeric(tbl["COMISION"], errors="coerce").fillna(0).sum())
                pct_caida = ((total_brutas - total_netas) / total_brutas * 100) if total_brutas else 0
                rows = ""
                for _, r in tbl.iterrows():
                    rows += f"""<tr>
                        <td class="mes">{_html.escape(str(r['MES']))}</td>
                        <td>{int(r['VENTAS BRUTAS']):,}</td>
                        <td class="ok">{int(r['VENTAS NETAS']):,}</td>
                        <td class="warn">{float(r['% CAIDA']):.2f}%</td>
                        <td>{float(r['% TV']):.2f}%</td>
                        <td class="money">S/ {float(r['PROMEDIO PRIME']):,.2f}</td>
                    </tr>"""
                return f"""
                <div class="cmp-card" style="--cmp:{color};--accent:{accent};">
                    <div class="cmp-head">
                        <div><div class="cmp-title">{titulo}</div><div class="cmp-sub">{subtitulo}</div></div>
                        <div class="cmp-pill">FIJA</div>
                    </div>
                    <div class="cmp-kpis">
                        <div><b>{total_brutas:,}</b><span>Brutas</span></div>
                        <div><b>{total_netas:,}</b><span>Netas</span></div>
                        <div><b>{pct_caida:.2f}%</b><span>Caida</span></div>
                        <div><b>S/ {total_com:,.0f}</b><span>Comision</span></div>
                    </div>
                    <div class="cmp-scroll"><table>
                        <thead><tr><th>Mes</th><th>Brutas</th><th>Netas</th><th>% Caida</th><th>% TV</th><th>Prom. Prime</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table></div>
                </div>"""

            tbl_dc = _resumir_por_canal_fija("D&C")
            tbl_tt = _resumir_por_canal_fija("Teletalk")
            _cmp_html = f"""
            <html><head><meta charset="utf-8"><style>
            body{{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a;}}
            .cmp-wrap{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
            .cmp-card{{background:rgba(255,255,255,.96);border:1px solid #dbe3ef;border-radius:14px;overflow:hidden;box-shadow:0 16px 36px rgba(15,23,42,.08);}}
            .cmp-head{{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;background:linear-gradient(90deg,var(--cmp),var(--accent));color:#fff;}}
            .cmp-title{{font-size:15px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;}}
            .cmp-sub{{font-size:10px;font-weight:800;opacity:.74;letter-spacing:.08em;text-transform:uppercase;margin-top:3px;}}
            .cmp-pill{{font-size:10px;font-weight:900;border:1px solid rgba(255,255,255,.45);border-radius:999px;padding:6px 10px;background:rgba(255,255,255,.14);}}
            .cmp-kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#dbe3ef;}}
            .cmp-kpis div{{background:#f8fafc;padding:12px;text-align:center;}}
            .cmp-kpis b{{display:block;font-size:20px;font-weight:900;color:var(--cmp);line-height:1;}}
            .cmp-kpis span{{display:block;font-size:9px;font-weight:900;color:#64748b;letter-spacing:.08em;text-transform:uppercase;margin-top:6px;}}
            .cmp-scroll{{max-height:430px;overflow:auto;}}
            table{{width:100%;border-collapse:separate;border-spacing:0;font-size:12px;}}
            th{{position:sticky;top:0;background:#eef2f7;color:#475569;text-align:right;padding:11px 10px;text-transform:uppercase;font-size:9px;letter-spacing:.08em;border-bottom:1px solid #dbe3ef;}}
            th:first-child,td:first-child{{text-align:left;}}
            td{{padding:11px 10px;border-bottom:1px solid #e5eaf1;text-align:right;font-weight:800;font-variant-numeric:tabular-nums;}}
            tr:hover td{{background:#f8fbff;}}
            .mes{{font-weight:900;color:#111827;}}
            .ok{{color:#059669;}}
            .warn{{color:#ea580c;}}
            .money{{color:#0f4287;}}
            .cmp-empty{{padding:28px;color:#64748b;font-weight:800;}}
            @media(max-width:900px){{.cmp-wrap{{grid-template-columns:1fr;}}.cmp-kpis{{grid-template-columns:repeat(2,1fr);}}}}
            </style></head><body><div class="cmp-wrap">
            {_tabla_comparativa_fija_html(tbl_dc, 'D&C DIGITAL GROUP', 'Comparativo mensual de ventas', '#0f4287', '#2563eb')}
            {_tabla_comparativa_fija_html(tbl_tt, 'TELETALK CONTACT CENTER', 'Comparativo mensual de ventas', '#6d0b8c', '#9333ea')}
            </div></body></html>
            """
            _stc.html(_cmp_html, height=620, scrolling=False)

        elif opcion == "Detalle Fija General FIJA":
            mostrar_detalle_fija_general()

        elif opcion == "F - COM.INDIRECTA 2da ETAPA":
            mostrar_segunda_caida_fija_dc()

        elif opcion == "D&C Factor Instalación":
            set_bg(img_dc)
            st.markdown('<div class="section-title-dc">D&C Factor Instalación</div>', unsafe_allow_html=True)
            st.markdown('<div class="small-subtitle-dc">AVANCE DE FACTOR ANUAL POR FECHA DE INSTALACIÓN</div>', unsafe_allow_html=True)
            st.write("---")
            filtro = st.selectbox("Fecha de Instalación", obtener_meses_fija("FECHA INSTALACION"), key="dc_fi_inst")
            mostrar_factor_fija("dbo.CLARO_DC_FIJA", "FECHA INSTALACION", filtro, "dc")

        elif opcion == "D&C Factor F. Venta":
            set_bg(img_dc)
            st.markdown('<div class="section-title-dc">D&C Factor F. Venta</div>', unsafe_allow_html=True)
            st.markdown('<div class="small-subtitle-dc">AVANCE DE FACTOR ANUAL POR FECHA DE VENTA</div>', unsafe_allow_html=True)
            st.write("---")
            filtro = st.selectbox("Fecha de Venta", obtener_meses_fija("FECHA GENERACION"), key="dc_fv_gene")
            mostrar_factor_fija("dbo.CLARO_DC_FIJA", "FECHA GENERACION", filtro, "dc")

        elif opcion == "Teletalk Factor Instalación":
            set_bg(img_tt)
            st.markdown('<div class="section-title-tt">Teletalk Factor Instalación</div>', unsafe_allow_html=True)
            st.markdown('<div class="small-subtitle-tt">AVANCE DE FACTOR ANUAL POR FECHA DE INSTALACIÓN</div>', unsafe_allow_html=True)
            st.write("---")
            filtro = st.selectbox("Fecha de Instalación", obtener_meses_fija("FECHA INSTALACION"), key="tt_fi_inst")
            mostrar_factor_fija("dbo.CLARO_TELETALK_FIJA","FECHA INSTALACION",filtro,"tt")

        elif opcion == "Teletalk Factor F. Venta":
            set_bg(img_tt)
            st.markdown('<div class="section-title-tt">Teletalk Factor F. Venta</div>', unsafe_allow_html=True)
            st.markdown('<div class="small-subtitle-tt">AVANCE DE FACTOR ANUAL POR FECHA DE VENTA</div>', unsafe_allow_html=True)
            st.write("---")
            filtro = st.selectbox("Fecha de Venta", obtener_meses_fija("FECHA GENERACION"), key="tt_fv_gene")
            mostrar_factor_fija("dbo.CLARO_TELETALK_FIJA","FECHA GENERACION",filtro,"tt")

    else:

        if opcion_movil == "Detalle Móvil General":
            mostrar_detalle_movil_general()


        elif opcion_movil == "Inicio: Reporte Comparativo MOVIL":
            set_bg(img_caratula)
            st.markdown('''<div class="caratula-hero">
                <div class="caratula-badge">📱 LÍNEA MÓVIL &nbsp;·&nbsp; REPORTE EJECUTIVO</div>
                <div class="main-title">REPORTE <span class="title-accent">COMPARATIVO MÓVIL</span></div>
                <div class="caratula-divider"></div>
                <div class="sub-title">D&amp;C DIGITAL GROUP &nbsp;&nbsp;·&nbsp;&nbsp; TELETALK CONTACT CENTER</div>
            </div>''', unsafe_allow_html=True)

            st.markdown("""
            <style>
            .tbl-canal-title {font-size:17px;font-weight:900;letter-spacing:.08em;padding:10px 0 6px 2px;margin-top:18px;}
            .tbl-canal-dc    {color:#0057b8;}
            .tbl-canal-tt    {color:#70008f;}
            </style>""", unsafe_allow_html=True)

            _PRODUCTOS_EXCLUIR_MOV = [
                "CHIP PREPAGO", "PRE A PRE", "2 PLAY 800 MBPS",
                "IFI INTERNET INALAMBRICO", "TFI", "OLO INTERNET PORTATIL"
            ]

            _csv_local_movil_cache = {}

            def _leer_csv_local_directo_movil(nombre):
                if nombre in _csv_local_movil_cache:
                    return _csv_local_movil_cache[nombre].copy()
                ruta = os.path.join(DATA_DIR, nombre)
                if not os.path.exists(ruta):
                    return pd.DataFrame()
                for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"]:
                    for sep in [";", ",", "\t"]:
                        try:
                            df = pd.read_csv(ruta, encoding=enc, sep=sep, engine="python", on_bad_lines="skip")
                            df.columns = df.columns.astype(str).str.strip()
                            if len(df.columns) > 1:
                                _csv_local_movil_cache[nombre] = df.copy()
                                return df
                        except Exception:
                            continue
                return pd.DataFrame()

            def _leer_dvz_local_movil(canal_filtro):
                df = _leer_csv_local_directo_movil("DVZ.csv")
                if df.empty:
                    return pd.DataFrame()
                col_tipo = next((c for c in df.columns if c.strip().lower() == "tipo producto"), None)
                col_clip = next((c for c in df.columns if c.strip().lower() == "datos adicionales - clip"), None)
                if not col_tipo or not col_clip:
                    return pd.DataFrame()
                clip = "D&C" if canal_filtro == "D&C" else "TELETALK"
                mask_tipo = df[col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"
                mask_clip = df[col_clip].fillna("").astype(str).str.strip().str.upper() == clip
                return df[mask_tipo & mask_clip].copy()

            def _pagos_claro_movil_local(canal_filtro, mes):
                archivo = "CLARO_DC_MOVIL.csv" if canal_filtro == "D&C" else "CLARO_TELETALK_MOVIL.csv"
                df = _leer_csv_local_directo_movil(archivo)
                if df.empty:
                    return pd.DataFrame()

                col_dni = encontrar_columna_flexible(df, [
                    "DNI CLIENTE", "DNI", "Cliente - Documento", "Cliente Documento", "DOCUMENTO CLIENTE", "DOCUMENTO"
                ])
                col_fecha = encontrar_columna_flexible(df, [
                    "FECHA OPERACION", "FECHA OPERACIÓN", "FECHA OPERACIÃ“N", "Fecha Operacion", "Fecha Operación", "Fecha OperaciÃ³n"
                ])
                col_comision = encontrar_columna_flexible(df, [
                    "COMISION TOTAL", "COMISIÓN TOTAL", "COMISIÃ“N TOTAL", "Comision Total", "Comisión Total", "ComisiÃ³n Total", "MONTO"
                ])
                col_transaccion = encontrar_columna_flexible(df, [
                    "TRANSACCION", "TRANSACCIÓN", "TRANSACCIÃ“N", "Transaccion", "Transacción", "TransacciÃ³n",
                    "TIPO TRANSACCION", "TIPO DE VENTA", "Tipo Transaccion"
                ])
                if not col_dni or not col_fecha or not col_comision:
                    return pd.DataFrame()

                df = df.copy()
                df["Canal"] = canal_filtro
                df["DOCUMENTO_KEY"] = _normalizar_documento_movil_general(df[col_dni])
                df["_FECHA_OPERACION_DT"] = _parse_fecha_movil_robusta(df[col_fecha])
                df["COMISION_REAL"] = pd.to_numeric(df[col_comision], errors="coerce").fillna(0)
                if col_transaccion:
                    df["Tipo Operacion"] = (
                        df[col_transaccion]
                        .fillna("")
                        .astype(str)
                        .str.replace(r"\s+", " ", regex=True)
                        .str.strip()
                        .str.upper()
                    )
                else:
                    df["Tipo Operacion"] = ""

                df["Tipo Operacion"] = df["Tipo Operacion"].replace([
                    "", "0", "0.0", "NAN", "NONE", "NULL", "NAT", "<NA>"
                ], "")
                df = df[(df["DOCUMENTO_KEY"] != "") & df["_FECHA_OPERACION_DT"].notna() & (df["Tipo Operacion"] != "")].copy()
                m, y = parse_mes_anio(mes)
                if m and y:
                    df = df[(df["_FECHA_OPERACION_DT"].dt.month == m) & (df["_FECHA_OPERACION_DT"].dt.year == y)].copy()
                return df[["Canal", "DOCUMENTO_KEY", "Tipo Operacion", "COMISION_REAL"]].copy()

            def _netas_movil_pre_api(canal_filtro, mes):
                df_mov = _leer_dvz_local_movil(canal_filtro)
                if df_mov.empty:
                    archivo_movil = "MOVIL_DC.csv" if canal_filtro == "D&C" else "MOVIL_TELETALK.csv"
                    df_mov = _leer_csv_local_directo_movil(archivo_movil)
                if df_mov.empty:
                    return 0, 0.0
                fecha_mov, _ = _obtener_fecha_venta_movil_general(df_mov)
                doc_mov, _ = _obtener_documento_movil_general(df_mov)
                df_mov = df_mov.copy()
                df_mov["Canal"] = canal_filtro
                df_mov["DOCUMENTO_KEY"] = doc_mov
                df_mov["_FECHA_MOV"] = fecha_mov
                df_mov = df_mov[df_mov["DOCUMENTO_KEY"] != ""].copy()
                m, y = parse_mes_anio(mes)
                if m and y:
                    df_mov = df_mov[(df_mov["_FECHA_MOV"].dt.month == m) & (df_mov["_FECHA_MOV"].dt.year == y)].copy()
                if df_mov.empty:
                    return 0, 0.0
                df_mov = df_mov.sort_values("_FECHA_MOV", ascending=False, na_position="last")
                df_mov = df_mov.drop_duplicates(subset=["Canal", "DOCUMENTO_KEY"], keep="first")

                claro = _pagos_claro_movil_local(canal_filtro, mes)
                if claro.empty:
                    return 0, 0.0
                cruzado = claro.merge(df_mov[["Canal", "DOCUMENTO_KEY"]], on=["Canal", "DOCUMENTO_KEY"], how="inner")
                if cruzado.empty:
                    return 0, 0.0
                tipo = cruzado.get("Tipo Operacion", pd.Series([""] * len(cruzado), index=cruzado.index)).fillna("").astype(str).str.strip().str.upper()
                cruzado = cruzado[tipo.ne("") & ~tipo.isin(["0", "0.0", "NAN", "NONE", "NULL", "NAT", "<NA>"])].copy()
                if cruzado.empty:
                    return 0, 0.0
                com = pd.to_numeric(cruzado.get("COMISION_REAL", cruzado.get("COMISION", 0)), errors="coerce").fillna(0)
                pagadas = com > 0
                return int(pagadas.sum()), float(com[pagadas].sum())

            def _resumir_por_canal_movil(canal_filtro):
                """
                Replica EXACTAMENTE la lógica de mostrar_detalle_movil_general por cada mes:
                - VENTAS BRUTAS  = lectura directa MOVIL_DC/TELETALK filtrado por _FECHA_VENTA_MOVIL_DT
                                   del mes + exclusión de productos (igual al KPI Total Ventas)
                - VENTAS NETAS   = base_valida[Estado Pago == PAGADA] del canal
                - % CAÍDA        = (Brutas - Netas) / Brutas * 100
                - PROMEDIO PRIME = _sumar_comision_real_unica(base_pagada) / Netas
                """
                archivo_kpi = "MOVIL_DC.csv" if canal_filtro == "D&C" else "MOVIL_TELETALK.csv"
                meses_lista = [m for m in obtener_meses_movil_general() if m != "Todos los meses"]
                rows = []
                for mes in meses_lista:
                    m_num, y_num = parse_mes_anio(mes)
                    if not m_num or not y_num:
                        continue

                    # ── VENTAS BRUTAS: misma lógica que KPI "Total Ventas" ──────────────
                    _df_kpi, _ = _leer_csv_movil_con_fallback([archivo_kpi])
                    brutas = 0
                    if not _df_kpi.empty:
                        _fecha_kpi, _ = _obtener_fecha_venta_movil_general(_df_kpi)
                        _df_kpi = _df_kpi.copy()
                        _df_kpi["_FECHA_KPI_DT"] = _fecha_kpi
                        _df_kpi = _df_kpi[
                            (_df_kpi["_FECHA_KPI_DT"].dt.month == m_num) &
                            (_df_kpi["_FECHA_KPI_DT"].dt.year  == y_num)
                        ].copy()
                        _col_prod = encontrar_columna_flexible(_df_kpi, [
                            "Productos - producto Especificacion", "Productos - Producto Especificacion",
                            "PRODUCTOS - PRODUCTO ESPECIFICACION", "Producto Especificacion",
                            "PRODUCTO ESPECIFICACION", "Producto", "PRODUCTO", "Plan", "PLAN"
                        ])
                        if _col_prod:
                            _prod_norm = _df_kpi[_col_prod].fillna("").astype(str).str.strip().str.upper()
                            _df_kpi = _df_kpi[~_prod_norm.isin([p.upper() for p in _PRODUCTOS_EXCLUIR_MOV])].copy()
                        brutas = len(_df_kpi)

                    # ── VENTAS NETAS / COMISION: construir_resumen_movil_general(mes) ──
                    netas, com = _netas_movil_pre_api(canal_filtro, mes)

                    caidas = brutas - netas
                    pct    = (caidas / brutas * 100) if brutas > 0 else 0.0
                    ticket = (com / netas) if netas > 0 else 0.0
                    rows.append({
                        "MES": mes,
                        "VENTAS BRUTAS": brutas,
                        "VENTAS NETAS": netas,
                        "% CAIDA": pct,
                        "PROMEDIO PRIME": ticket,
                        "COMISION": com,
                        "_sort": (y_num, m_num),
                    })
                if not rows:
                    return pd.DataFrame(columns=["MES","VENTAS BRUTAS","VENTAS NETAS","% CAIDA","PROMEDIO PRIME","COMISION"])
                return pd.DataFrame(rows).sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

            def _tabla_comparativa_movil_html(tbl, titulo, subtitulo, color, accent):
                if tbl.empty:
                    return f'<div class="cmp-card" style="--cmp:{color};--accent:{accent};"><div class="cmp-head"><div><div class="cmp-title">{titulo}</div><div class="cmp-sub">{subtitulo}</div></div><div class="cmp-pill">MOVIL</div></div><div class="cmp-empty">Sin datos disponibles</div></div>'
                total_brutas = int(pd.to_numeric(tbl["VENTAS BRUTAS"], errors="coerce").fillna(0).sum())
                total_netas = int(pd.to_numeric(tbl["VENTAS NETAS"], errors="coerce").fillna(0).sum())
                total_com = float(pd.to_numeric(tbl["COMISION"], errors="coerce").fillna(0).sum())
                pct_caida = ((total_brutas - total_netas) / total_brutas * 100) if total_brutas else 0
                rows = ""
                for _, r in tbl.iterrows():
                    rows += f"""<tr>
                        <td class=\"mes\">{_html.escape(str(r['MES']))}</td>
                        <td>{int(r['VENTAS BRUTAS']):,}</td>
                        <td class=\"ok\">{int(r['VENTAS NETAS']):,}</td>
                        <td class=\"warn\">{float(r['% CAIDA']):.2f}%</td>
                        <td class=\"money\">S/ {float(r['PROMEDIO PRIME']):,.2f}</td>
                    </tr>"""
                return f"""
                <div class=\"cmp-card\" style=\"--cmp:{color};--accent:{accent};\">
                    <div class=\"cmp-head\">
                        <div><div class=\"cmp-title\">{titulo}</div><div class=\"cmp-sub\">{subtitulo}</div></div>
                        <div class=\"cmp-pill\">MOVIL</div>
                    </div>
                    <div class=\"cmp-kpis\">
                        <div><b>{total_brutas:,}</b><span>Brutas</span></div>
                        <div><b>{total_netas:,}</b><span>Netas</span></div>
                        <div><b>{pct_caida:.2f}%</b><span>Caida</span></div>
                        <div><b>S/ {total_com:,.0f}</b><span>Comision</span></div>
                    </div>
                    <div class=\"cmp-scroll\"><table>
                        <thead><tr><th>Mes</th><th>Brutas</th><th>Netas</th><th>% Caida</th><th>Prom. Prime</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table></div>
                </div>"""

            tbl_dc = _resumir_por_canal_movil("D&C")
            tbl_tt = _resumir_por_canal_movil("Teletalk")
            _cmp_html = f"""
            <html><head><meta charset=\"utf-8\"><style>
            body{{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a;}}
            .cmp-wrap{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
            .cmp-card{{background:rgba(255,255,255,.96);border:1px solid #dbe3ef;border-radius:14px;overflow:hidden;box-shadow:0 16px 36px rgba(15,23,42,.08);}}
            .cmp-head{{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;background:linear-gradient(90deg,var(--cmp),var(--accent));color:#fff;}}
            .cmp-title{{font-size:15px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;}}
            .cmp-sub{{font-size:10px;font-weight:800;opacity:.74;letter-spacing:.08em;text-transform:uppercase;margin-top:3px;}}
            .cmp-pill{{font-size:10px;font-weight:900;border:1px solid rgba(255,255,255,.45);border-radius:999px;padding:6px 10px;background:rgba(255,255,255,.14);}}
            .cmp-kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#dbe3ef;}}
            .cmp-kpis div{{background:#f8fafc;padding:12px;text-align:center;}}
            .cmp-kpis b{{display:block;font-size:20px;font-weight:900;color:var(--cmp);line-height:1;}}
            .cmp-kpis span{{display:block;font-size:9px;font-weight:900;color:#64748b;letter-spacing:.08em;text-transform:uppercase;margin-top:6px;}}
            .cmp-scroll{{max-height:430px;overflow:auto;}}
            table{{width:100%;border-collapse:separate;border-spacing:0;font-size:12px;}}
            th{{position:sticky;top:0;background:#eef2f7;color:#475569;text-align:right;padding:11px 10px;text-transform:uppercase;font-size:9px;letter-spacing:.08em;border-bottom:1px solid #dbe3ef;}}
            th:first-child,td:first-child{{text-align:left;}}
            td{{padding:11px 10px;border-bottom:1px solid #e5eaf1;text-align:right;font-weight:800;font-variant-numeric:tabular-nums;}}
            tr:hover td{{background:#f8fbff;}}
            .mes{{font-weight:900;color:#111827;}}
            .ok{{color:#059669;}}
            .warn{{color:#ea580c;}}
            .money{{color:#0f4287;}}
            .cmp-empty{{padding:28px;color:#64748b;font-weight:800;}}
            @media(max-width:900px){{.cmp-wrap{{grid-template-columns:1fr;}}.cmp-kpis{{grid-template-columns:repeat(2,1fr);}}}}
            </style></head><body><div class=\"cmp-wrap\">
            {_tabla_comparativa_movil_html(tbl_dc, 'D&C DIGITAL GROUP', 'Comparativo mensual de ventas', '#0f4287', '#2563eb')}
            {_tabla_comparativa_movil_html(tbl_tt, 'TELETALK CONTACT CENTER', 'Comparativo mensual de ventas', '#6d0b8c', '#9333ea')}
            </div></body></html>
            """
            _stc.html(_cmp_html, height=620, scrolling=False)


__all__ = [name for name in globals() if not name.startswith("__")]









