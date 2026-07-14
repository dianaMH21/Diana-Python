import os
import streamlit as st

# Formato opcional: DASHBOARD_USERS="Fiorella:clave,LuisT:clave"
def _load_users():
    raw = os.getenv("DASHBOARD_USERS", "").strip()
    if raw:
        users = {}
        for item in raw.split(","):
            if ":" in item:
                user, password = item.split(":", 1)
                users[user.strip()] = password.strip()
        if users:
            return users

    # Compatibilidad temporal con el archivo original. Mover a variables de entorno antes de publicar.
    return {
        "Fiorella": "F10r3LLa123*",
        "LuisT": "Corp.LT_2026!k",
        "PaoloA": "Corp.PA_2026!k",
        "DavidG": "Corp.DG_2026!k",
        "SusanG": "Corp.SG_2026!k",
    }

def login_inicio():

    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False

    if st.session_state["login_ok"]: return True

    # ────────────────────────────────────────────────────────────────────────
    #  CSS — transforma las dos columnas de Streamlit en el panel split
    # ────────────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
        /* Ocultar sidebar, header y quitar padding general */
        section[data-testid="stSidebar"],
        div[data-testid="collapsedControl"]   { display:none !important; }
        header[data-testid="stHeader"]        { display:none !important; }
        .stApp                                { background:#eef0fb !important; }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* ── Centrar todo en la pantalla ── */
        div[data-testid="stHorizontalBlock"] {
            align-items: stretch !important;
            gap: 0 !important;
            min-height: 100vh;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* ── Columna IZQUIERDA — azul ── */
        div[data-testid="stHorizontalBlock"] > div:first-child {
            background:
                linear-gradient(128deg, rgba(9,37,84,.92) 0%, rgba(15,66,135,.94) 35%, rgba(109,11,140,.82) 100%),
                radial-gradient(circle at 22% 18%, rgba(103,232,249,.42) 0 18%, transparent 34%),
                radial-gradient(circle at 86% 78%, rgba(147,51,234,.40) 0 18%, transparent 36%) !important;
            padding: 54px 56px 42px 56px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            position: relative !important;
            overflow: hidden !important;
            min-height: 100vh !important;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child::before {
            content: "" !important;
            position: absolute !important;
            width: 72%; height: 44% !important;
            right: -22%; top: -10% !important;
            transform: rotate(-18deg);
            border-radius: 28px !important;
            background: linear-gradient(135deg, rgba(34,211,238,.46), rgba(255,255,255,.05)) !important;
            border: 1px solid rgba(255,255,255,.16) !important;
            pointer-events: none !important;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child::after {
            content: "" !important;
            position: absolute !important;
            width: 88%; height: 46% !important;
            left: -38%; bottom: -12% !important;
            transform: rotate(-32deg);
            border-radius: 34px !important;
            background: linear-gradient(135deg, rgba(2,6,23,.40), rgba(124,58,237,.22)) !important;
            border: 1px solid rgba(255,255,255,.10) !important;
            pointer-events: none !important;
        }

        /* ── Columna DERECHA — blanca ── */
        div[data-testid="stHorizontalBlock"] > div:last-child {
            background:
                linear-gradient(135deg, rgba(255,255,255,.98), rgba(248,250,252,.98)),
                radial-gradient(circle at 100% 0%, rgba(15,66,135,.08), transparent 26%) !important;
            padding: 60px 56px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            min-height: 100vh !important;
        }

        /* ── Textos del lado izquierdo ── */
        .ls-topline {
            position: relative; z-index: 2;
            display: inline-flex; align-items: center; gap: 10px;
            color: rgba(255,255,255,.82);
            font-size: 11px; font-weight: 900; letter-spacing: .18em;
            text-transform: uppercase;
            padding: 8px 12px;
            border: 1px solid rgba(255,255,255,.20);
            border-radius: 999px;
            background: rgba(255,255,255,.08);
            margin-bottom: 52px;
        }
        .ls-greeting {
            position: relative; z-index: 2;
            font-size: 54px; font-weight: 950;
            line-height: 1.02; letter-spacing: -.03em;
            color: white; margin-bottom: 18px;
            text-shadow: 0 16px 42px rgba(15,23,42,.22);
        }
        .ls-desc {
            position: relative; z-index: 2;
            font-size: 15px; font-weight: 650;
            line-height: 1.72; color: rgba(255,255,255,.82);
            max-width: 430px;
        }
        .ls-copy {
            position: relative; z-index: 2;
            font-size: 12px; color: rgba(255,255,255,.45);
            font-weight: 500; margin-top: 0;
        }
        .ls-kpi-grid {
            position: relative; z-index: 2;
            display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px; max-width: 520px; margin-top: 34px;
        }
        .ls-kpi {
            border: 1px solid rgba(255,255,255,.18);
            background: rgba(255,255,255,.10);
            border-radius: 12px;
            padding: 14px 14px;
            box-shadow: 0 16px 36px rgba(2,6,23,.16);
            backdrop-filter: blur(10px);
        }
        .ls-kpi b {
            display:block; color:#fff; font-size:22px; line-height:1; font-weight:950;
        }
        .ls-kpi span {
            display:block; color:rgba(255,255,255,.68); font-size:10px; font-weight:900;
            letter-spacing:.10em; text-transform:uppercase; margin-top:8px;
        }
        .ls-orbit {
            position: absolute; z-index: 1;
            width: 420px; height: 420px;
            right: -130px; bottom: 56px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,.14);
        }
        .ls-orbit::before {
            content:""; position:absolute; inset:48px;
            border-radius:50%; border:1px solid rgba(255,255,255,.10);
        }
        .ls-orbit::after {
            content:""; position:absolute; width:12px; height:12px; border-radius:999px;
            right:64px; top:92px; background:#67e8f9; box-shadow:0 0 22px rgba(103,232,249,.8);
        }

        /* ── Textos del lado derecho ── */
        .ls-form-card {
            width: min(100%, 760px);
            border: 1px solid #dbe3ef;
            border-radius: 18px;
            padding: 34px 36px 28px 36px;
            background: rgba(255,255,255,.92);
            box-shadow: 0 24px 60px rgba(15,23,42,.10);
        }
        .ls-brand   {
            font-size:13px; font-weight:950; color:#0f4287; margin-bottom:34px;
            letter-spacing:.12em; text-transform:uppercase;
        }
        .ls-title   { font-size:34px; font-weight:950; color:#0f172a; letter-spacing:-.03em; margin-bottom:8px; }
        .ls-sub     { font-size:13px; color:#64748b; font-weight:600; line-height:1.6; margin-bottom:28px; }
        .ls-foot    { text-align:center; margin-top:18px; font-size:12px; color:#94a3b8; }
        .ls-mini-row {
            display:flex; gap:10px; flex-wrap:wrap; margin-bottom:24px;
        }
        .ls-mini-badge {
            border:1px solid #dbe3ef; border-radius:999px; padding:7px 11px;
            color:#334155; font-size:11px; font-weight:850; background:#f8fafc;
        }

        /* ── Widgets Streamlit en el lado derecho ── */
        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label {
            color: #374151 !important;
            font-size: 12px !important;
            font-weight: 800 !important;
            letter-spacing: .07em;
            text-transform: uppercase;
        }
        div[data-testid="stSelectbox"] > div > div,
        div[data-testid="stTextInput"] input {
            border-radius: 12px !important;
            border: 1.5px solid #d1d5db !important;
            background: #f8fafc !important;
            min-height: 50px !important;
            font-size: 14px !important;
            color: #111827 !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #3b4fe8 !important;
            box-shadow: 0 0 0 3px rgba(59,79,232,.14) !important;
        }

        /* ── Botón negro ── */
        div[data-testid="stHorizontalBlock"] > div:last-child .stButton > button {
            background: linear-gradient(90deg,#0f4287,#6d0b8c) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            min-height: 54px !important;
            font-weight: 900 !important;
            font-size: 15px !important;
            letter-spacing: .03em !important;
            box-shadow: 0 12px 28px rgba(15,66,135,.22) !important;
            transition: all .16s ease !important;
            margin-top: 6px !important;
        }
        div[data-testid="stHorizontalBlock"] > div:last-child .stButton > button:hover {
            background: linear-gradient(90deg,#164f9b,#7c1da1) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 16px 34px rgba(109,11,140,.24) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    #  Layout: dos columnas de Streamlit = izquierda azul | derecha blanca
    # ────────────────────────────────────────────────────────────────────────
    col_izq, col_der = st.columns([1, 1])

    # ── IZQUIERDA: solo HTML estático (sin widgets) ──────────────────────
    with col_izq:
        st.markdown("""
        <div class="ls-orbit"></div>
        <div class="ls-topline">Panel corporativo · Ventas y comisiones</div>
        <div class="ls-greeting">
            Teletalk<br>Digital
        </div>
        <div class="ls-desc">
            Gestión ejecutiva de ventas, comisiones, productividad comercial,
            ranking de asesores, efectividad y seguimiento NPN.
        </div>
        <div class="ls-kpi-grid">
            <div class="ls-kpi"><b>FIJA</b><span>Reporte ejecutivo</span></div>
            <div class="ls-kpi"><b>MÓVIL</b><span>Control comercial</span></div>
            <div class="ls-kpi"><b>NPN</b><span>Retención</span></div>
        </div>
        <div style="flex:1"></div>
        <div class="ls-copy">© 2025 Teletalk Digital · Todos los derechos reservados.</div>
        """, unsafe_allow_html=True)

    # ── DERECHA: encabezado HTML + widgets reales de Streamlit ───────────
    with col_der:
        st.markdown("""
        <div class="ls-form-card">
        <div class="ls-brand">📊 Teletalk - Digital</div>
        <div class="ls-title">¡Bienvenido de vuelta!</div>
        <div class="ls-sub">Ingresa tus credenciales para acceder al panel corporativo.</div>
        <div class="ls-mini-row">
            <span class="ls-mini-badge">D&C Digital Group</span>
            <span class="ls-mini-badge">Teletalk Contact Center</span>
        </div>
        """, unsafe_allow_html=True)

        USUARIOS = _load_users()

        usuario  = st.selectbox("Usuario", [""] + list(USUARIOS.keys()),
                                key="login_usuario", placeholder="Selecciona tu usuario")
        password = st.text_input("Contraseña", type="password",
                                 key="login_password", placeholder="Ingresa tu contraseña")

        if st.button("Ingresar al dashboard", use_container_width=True):
            if usuario in USUARIOS and password == USUARIOS[usuario]:
                st.session_state["login_ok"]         = True
                st.session_state["usuario_logueado"] = usuario
                st.success(f"✅ ¡Hola, {usuario}! Bienvenido.")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

        st.markdown('<div class="ls-foot">🔐 Acceso restringido · Uso interno autorizado</div></div>',
                    unsafe_allow_html=True)

    st.stop()
