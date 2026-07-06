import os
import time

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
            background: linear-gradient(145deg, #2d38c7 0%, #3a4ee6 50%, #4730d8 100%) !important;
            padding: 60px 52px 44px 52px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            position: relative !important;
            overflow: hidden !important;
            min-height: 100vh !important;
        }
        /* Arcos decorativos en el lado azul */
        div[data-testid="stHorizontalBlock"] > div:first-child::before {
            content: "" !important;
            position: absolute !important;
            width: 560px; height: 560px !important;
            right: -180px; bottom: -220px !important;
            border-radius: 50% !important;
            border: 1.5px solid rgba(255,255,255,.18) !important;
            pointer-events: none !important;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child::after {
            content: "" !important;
            position: absolute !important;
            width: 400px; height: 400px !important;
            right: -100px; bottom: -140px !important;
            border-radius: 50% !important;
            border: 1.5px solid rgba(255,255,255,.12) !important;
            pointer-events: none !important;
        }

        /* ── Columna DERECHA — blanca ── */
        div[data-testid="stHorizontalBlock"] > div:last-child {
            background: #ffffff !important;
            padding: 60px 56px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            min-height: 100vh !important;
        }

        /* ── Textos del lado izquierdo ── */
        .ls-star {
            font-size: 56px; line-height: 1;
            margin-bottom: 44px; display: block;
            color: white;
        }
        .ls-greeting {
            font-size: 50px; font-weight: 900;
            line-height: 1.05; letter-spacing: -.04em;
            color: white; margin-bottom: 20px;
        }
        .ls-desc {
            font-size: 15px; font-weight: 500;
            line-height: 1.72; color: rgba(255,255,255,.80);
            max-width: 360px;
        }
        .ls-copy {
            font-size: 12px; color: rgba(255,255,255,.45);
            font-weight: 500; margin-top: 0;
        }
        /* Arco extra (tercero) en el lado azul */
        .ls-arc3 {
            position: absolute;
            width: 260px; height: 260px;
            right: -40px; bottom: -70px;
            border-radius: 50%;
            border: 1.5px solid rgba(255,255,255,.09);
            pointer-events: none;
        }

        /* ── Textos del lado derecho ── */
        .ls-brand   { font-size:17px; font-weight:900; color:#0f172a; margin-bottom:44px; }
        .ls-title   { font-size:32px; font-weight:900; color:#0f172a; letter-spacing:-.04em; margin-bottom:6px; }
        .ls-sub     { font-size:13px; color:#64748b; font-weight:500; line-height:1.6; margin-bottom:28px; }
        .ls-foot    { text-align:center; margin-top:18px; font-size:12px; color:#94a3b8; }

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
            border-radius: 10px !important;
            border: 1.5px solid #d1d5db !important;
            background: #fafafa !important;
            min-height: 48px !important;
            font-size: 14px !important;
            color: #111827 !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #3b4fe8 !important;
            box-shadow: 0 0 0 3px rgba(59,79,232,.14) !important;
        }

        /* ── Botón negro ── */
        div[data-testid="stHorizontalBlock"] > div:last-child .stButton > button {
            background: #111827 !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            min-height: 52px !important;
            font-weight: 900 !important;
            font-size: 15px !important;
            letter-spacing: .03em !important;
            box-shadow: 0 4px 18px rgba(17,24,39,.20) !important;
            transition: all .16s ease !important;
            margin-top: 6px !important;
        }
        div[data-testid="stHorizontalBlock"] > div:last-child .stButton > button:hover {
            background: #1e293b !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 28px rgba(17,24,39,.28) !important;
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
        <div class="ls-arc3"></div>
        <span class="ls-star">✳</span>
        <div class="ls-greeting">
            ¡Hola,<br>Bienvenido! 👋
        </div>
        <div class="ls-desc">
            Gestión de ventas, comisiones y productividad comercial.
            Ranking de Asesores - %TV - Promedio Prime.
        </div>
        <div style="flex:1"></div>
        <div class="ls-copy">© 2025 Teletalk Digital · Todos los derechos reservados.</div>
        """, unsafe_allow_html=True)

    # ── DERECHA: encabezado HTML + widgets reales de Streamlit ───────────
    with col_der:
        st.markdown("""
        <div class="ls-brand">📊 Teletalk - Digital</div>
        <div class="ls-title">¡Bienvenido de vuelta!</div>
        <div class="ls-sub">Ingresa tus credenciales para acceder al panel corporativo.</div>
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
                st.success(f"✅ ¡Hola, {usuario}! Bienvenido. Cargando tu panel...")
                st.balloons()
                time.sleep(1.0)
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

        st.markdown('<div class="ls-foot">🔐 Acceso restringido · Uso interno autorizado</div>',
                    unsafe_allow_html=True)

    st.stop()
