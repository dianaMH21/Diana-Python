import base64
import html
import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as _stc


def inject_gerencial_theme():
    """Capa visual global para un look ejecutivo en todo el dashboard."""
    st.markdown("""
    <style>
    :root {
        --tl-navy: #0f2f5f;
        --tl-blue: #0f4287;
        --tl-cyan: #0891b2;
        --tl-violet: #6d28d9;
        --tl-green: #059669;
        --tl-red: #dc2626;
        --tl-orange: #ea580c;
        --tl-ink: #0f172a;
        --tl-muted: #64748b;
        --tl-line: #dbe3ef;
        --tl-soft: rgba(248, 250, 252, .92);
        --tl-glass: rgba(255, 255, 255, .94);
    }

    html, body, [class*="css"] {
        font-family: Inter, "Segoe UI", Arial, sans-serif;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.4rem;
        max-width: 1560px;
    }

    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    .stApp {
        margin-top: 0 !important;
    }

    h1, h2, h3 {
        color: var(--tl-ink);
        letter-spacing: 0;
    }

    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3 {
        font-weight: 900;
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stDateInput"] label {
        color: #334155;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: .01em;
        margin-bottom: 6px;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea {
        background: rgba(241, 245, 249, .96) !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        min-height: 42px;
    }

    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="input"] > div:hover {
        border-color: rgba(15, 66, 135, .28) !important;
        background: #fff !important;
    }

    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within {
        border-color: var(--tl-blue) !important;
        box-shadow: 0 0 0 3px rgba(15, 66, 135, .12) !important;
        background: #fff !important;
    }

    .stButton > button,
    .stDownloadButton > button,
    button[kind="secondary"],
    button[kind="primary"] {
        border-radius: 8px !important;
        border: 1px solid rgba(15, 66, 135, .22) !important;
        background: linear-gradient(180deg, #ffffff, #f8fafc) !important;
        color: #1f2937 !important;
        font-weight: 800 !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, .08) !important;
        transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        border-color: var(--tl-blue) !important;
        box-shadow: 0 12px 26px rgba(15, 66, 135, .14) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid var(--tl-line);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 14px;
        color: #475569;
        font-weight: 800;
    }

    .stTabs [aria-selected="true"] {
        color: #ff3b49 !important;
        border-bottom: 2px solid #ff3b49;
        background: rgba(255, 255, 255, .72);
    }

    div[role="radiogroup"] {
        gap: 6px;
    }

    div[role="radiogroup"] label {
        background: rgba(255, 255, 255, .78);
        border: 1px solid rgba(203, 213, 225, .8);
        border-radius: 8px;
        padding: 8px 12px;
        font-weight: 800;
        box-shadow: 0 8px 20px rgba(15, 23, 42, .05);
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        border: 1px solid var(--tl-line);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 16px 36px rgba(15, 23, 42, .08);
        background: var(--tl-glass);
    }

    div[data-testid="stDataFrame"] div[role="grid"],
    div[data-testid="stDataFrame"] canvas {
        border-radius: 10px;
    }

    div[data-testid="stTable"] table {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        font-size: 12px;
    }

    div[data-testid="stTable"] thead tr th {
        background: linear-gradient(90deg, var(--tl-blue), var(--tl-violet)) !important;
        color: #fff !important;
        font-size: 10px;
        font-weight: 900;
        letter-spacing: .08em;
        text-transform: uppercase;
        padding: 12px 14px;
        border: 0 !important;
    }

    div[data-testid="stTable"] tbody tr:nth-child(even) td {
        background: rgba(248, 250, 252, .9) !important;
    }

    div[data-testid="stTable"] tbody tr:hover td {
        background: #eef6ff !important;
    }

    div[data-testid="stTable"] tbody td {
        border-bottom: 1px solid #e5eaf1 !important;
        padding: 11px 14px;
        color: #111827;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, .92);
        border: 1px solid var(--tl-line);
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, .07);
    }

    details[data-testid="stExpander"] {
        border: 1px solid var(--tl-line) !important;
        border-radius: 10px !important;
        overflow: hidden;
        background: rgba(255, 255, 255, .92) !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, .07);
    }

    details[data-testid="stExpander"] summary {
        font-weight: 900;
        color: var(--tl-blue);
        background: linear-gradient(180deg, #fff, #f8fafc);
    }

    .gerencial-title {
        color: var(--tl-blue);
        font-size: clamp(28px, 3vw, 42px);
        font-weight: 950;
        letter-spacing: 0;
        line-height: 1.05;
        margin: 2px 0 6px;
    }

    .gerencial-subtitle {
        color: #334155;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: 18px;
    }

    .java-section-card {
        background: rgba(255, 255, 255, .90);
        border: 1px solid var(--tl-line);
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 16px 36px rgba(15, 23, 42, .07);
    }

    @media (max-width: 760px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .gerencial-title { font-size: 28px; }
    }
    </style>
    """, unsafe_allow_html=True)


def java_table(df, height=420, title="", subtitle="", accent="#0f4287", max_rows=300):
    """Renderiza una tabla HTML ejecutiva con scroll interno."""
    if df is None:
        df = pd.DataFrame()
    if hasattr(df, "data"):
        df = df.data
    df = pd.DataFrame(df).copy()

    total_rows = len(df)
    if max_rows and total_rows > max_rows:
        df = df.head(max_rows).copy()
        note = f"Mostrando {max_rows:,} de {total_rows:,} registros"
    else:
        note = f"{total_rows:,} registros"

    if df.empty:
        body = '<div class="jt-empty">Sin datos disponibles para los filtros seleccionados</div>'
    else:
        headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
        rows = []
        for _, row in df.iterrows():
            cells = []
            for value in row.tolist():
                if pd.isna(value):
                    text = ""
                elif isinstance(value, float):
                    text = f"{value:,.2f}"
                else:
                    text = str(value)
                cls = ""
                upper = text.upper()
                if upper in {"PAGADA", "SI", "CONFORME"}:
                    cls = " ok"
                elif "CA" in upper and ("DA" in upper or "IDA" in upper):
                    cls = " bad"
                elif upper in {"NO PAGADA", "NO", "PENDIENTE"}:
                    cls = " warn"
                cells.append(f'<td class="{cls.strip()}">{html.escape(text)}</td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")
        body = f"""
        <div class="jt-scroll" style="max-height:{int(height)}px">
            <table>
                <thead><tr>{headers}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        """

    title_html = ""
    if title or subtitle:
        title_html = f"""
        <div class="jt-head">
            <div>
                <div class="jt-title">{html.escape(str(title))}</div>
                <div class="jt-sub">{html.escape(str(subtitle or note))}</div>
            </div>
            <div class="jt-pill">{html.escape(note)}</div>
        </div>
        """

    _stc.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; color:#0f172a; background:transparent; }}
        .jt-card {{
            border:1px solid #dbe3ef;
            border-radius:10px;
            background:rgba(255,255,255,.96);
            box-shadow:0 16px 36px rgba(15,23,42,.08);
            overflow:hidden;
        }}
        .jt-head {{
            display:flex; align-items:center; justify-content:space-between; gap:14px;
            padding:14px 16px;
            background:linear-gradient(90deg,{accent},#6d28d9);
            color:white;
        }}
        .jt-title {{ font-size:14px; font-weight:950; letter-spacing:.08em; text-transform:uppercase; }}
        .jt-sub {{ margin-top:3px; font-size:10px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; opacity:.72; }}
        .jt-pill {{ flex:0 0 auto; border:1px solid rgba(255,255,255,.42); border-radius:999px; padding:6px 10px; font-size:10px; font-weight:900; background:rgba(255,255,255,.14); }}
        .jt-scroll {{ overflow:auto; }}
        table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:12px; }}
        thead th {{
            position:sticky; top:0; z-index:2;
            background:#eef2f7; color:#475569;
            text-align:left; padding:11px 12px;
            font-size:9px; font-weight:950; letter-spacing:.08em; text-transform:uppercase;
            border-bottom:1px solid #dbe3ef;
            white-space:nowrap;
        }}
        tbody td {{
            padding:10px 12px;
            border-bottom:1px solid #e5eaf1;
            font-weight:750;
            white-space:nowrap;
            font-variant-numeric:tabular-nums;
        }}
        tbody tr:nth-child(even) td {{ background:#f8fafc; }}
        tbody tr:hover td {{ background:#eef6ff; }}
        td.ok {{ color:#059669; font-weight:950; }}
        td.bad {{ color:#dc2626; font-weight:950; }}
        td.warn {{ color:#ea580c; font-weight:950; }}
        .jt-empty {{ padding:26px; color:#64748b; font-weight:850; text-align:center; }}
    </style>
    </head>
    <body><div class="jt-card">{title_html}{body}</div></body>
    </html>
    """, height=(height + (72 if title_html else 22)), scrolling=False)


def _inject_loading_overlay():
    _stc.html("""<!DOCTYPE html><html><head><style>*{margin:0;padding:0;}body{background:transparent;overflow:hidden;}</style></head>
<body><script>
(function(){
  var doc=window.parent.document;
  if(!doc.getElementById('tld-ov')){
    var s=doc.createElement('style');
    s.textContent='@keyframes tld-spin{to{transform:rotate(360deg)}}@keyframes tld-pop{from{transform:scale(.75);opacity:0}to{transform:scale(1);opacity:1}}';
    doc.head.appendChild(s);
    var ov=doc.createElement('div');
    ov.id='tld-ov';
    ov.style.cssText='display:none;position:fixed;inset:0;z-index:2147483647;background:rgba(2,6,23,.72);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);align-items:center;justify-content:center';
    ov.innerHTML='<div style="background:linear-gradient(135deg,#0f4287,#2563eb 55%,#7c3aed);border-radius:18px;padding:28px 46px;display:flex;flex-direction:column;align-items:center;gap:14px;box-shadow:0 24px 54px rgba(0,0,0,.45);animation:tld-pop .22s cubic-bezier(.34,1.56,.64,1) both"><div style="width:42px;height:42px;border:4px solid rgba(255,255,255,.22);border-top-color:#fff;border-radius:50%;animation:tld-spin .7s linear infinite"></div><div style="color:#fff;font-size:21px;font-weight:900;font-family:Segoe UI,Arial,sans-serif;text-align:center">&#9203; Cargando Data</div><div style="color:rgba(255,255,255,.72);font-size:11px;font-weight:700;font-family:Segoe UI,Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;text-align:center">Dashboard Teletalk Digital &mdash; Por favor espere</div></div>';
    doc.body.appendChild(ov);
  }
  var ov=doc.getElementById('tld-ov');
  var timer=null;
  function show(){
    if(!ov) return;
    ov.style.display='flex';
    if(timer) clearTimeout(timer);
    timer=setTimeout(hide,1800);
  }
  function hide(){
    if(!ov) return;
    ov.style.display='none';
    if(timer) clearTimeout(timer);
    timer=null;
  }

  // Solo mostrar entre paginas/secciones del menu lateral.
  // No escucha el StatusWidget de Streamlit, porque eso se activa con filtros.
  if(!doc.__tldNavOverlayBound){
    doc.__tldNavOverlayBound=true;
    doc.addEventListener('click',function(e){
      var t=e.target;
      var menuItem=t.closest('section[data-testid="stSidebar"] .stRadio label');
      var sidebarPage=t.closest('[data-testid="stSidebarNavLink"]');
      if(menuItem || sidebarPage){ show(); }
    },true);
  }
  hide();
})();
</script></body></html>""",height=0,scrolling=False)


@st.cache_data(ttl=3600, show_spinner=False)
def _leer_img_b64(img_file):
    """Lee la imagen una sola vez y la cachea para no releerla en cada cambio de pestaña."""
    if not os.path.exists(img_file):
        return ""
    with open(img_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = img_file.split(".")[-1].lower()
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
    return f'background-image: url("data:{mime};base64,{b64}");'

def set_bg(img_file):
    st.markdown(f"""<style>
        .stApp {{
            background-color:#eef4fb;
            background-image:
                linear-gradient(122deg, rgba(15,66,135,.22) 0%, rgba(37,99,235,.10) 20%, rgba(255,255,255,.80) 43%, rgba(255,255,255,.68) 58%, rgba(109,11,140,.18) 100%),
                linear-gradient(118deg, transparent 0%, transparent 54%, rgba(15,66,135,.16) 54.2%, rgba(15,66,135,.16) 60%, transparent 60.2%),
                linear-gradient(118deg, transparent 0%, transparent 66%, rgba(8,145,178,.14) 66.2%, rgba(8,145,178,.14) 70%, transparent 70.2%),
                linear-gradient(145deg, transparent 0%, transparent 72%, rgba(109,11,140,.17) 72.2%, rgba(109,11,140,.17) 80%, transparent 80.2%),
                linear-gradient(32deg, rgba(15,23,42,.04) 0 1px, transparent 1px 26px),
                linear-gradient(122deg, rgba(15,23,42,.035) 0 1px, transparent 1px 34px);
            background-size:cover, cover, cover, cover, 34px 34px, 42px 42px;
            background-position:center;
            background-attachment:fixed;
        }}
        .stApp::before {{
            content:"";
            position:fixed;
            inset:0;
            pointer-events:none;
            z-index:0;
            background:
                linear-gradient(90deg, rgba(255,255,255,.64), rgba(255,255,255,.14) 38%, rgba(255,255,255,.52)),
                linear-gradient(180deg, rgba(255,255,255,.54), rgba(255,255,255,.10)),
                linear-gradient(135deg, transparent 0%, transparent 12%, rgba(15,66,135,.08) 12.2%, rgba(15,66,135,.08) 13%, transparent 13.2%, transparent 88%, rgba(109,11,140,.10) 88.2%, rgba(109,11,140,.10) 89%, transparent 89.2%);
        }}
        .stApp::after {{
            content:"";
            position:fixed;
            inset:auto -8vw -18vh auto;
            width:58vw;
            height:62vh;
            pointer-events:none;
            z-index:0;
            background:
                linear-gradient(135deg, rgba(15,66,135,.18), rgba(109,11,140,.18));
            clip-path:polygon(18% 0, 100% 0, 82% 100%, 0 100%);
            filter:blur(.2px);
            opacity:.55;
        }}
        .stApp > header,
        .stApp [data-testid="stSidebar"],
        .stApp [data-testid="stAppViewContainer"] {{
            position:relative;
            z-index:1;
        }}
        .main-title {{ text-align:center; color:black; font-weight:900; font-size:52px; margin-bottom:6px; }}
        .sub-title {{ text-align:center; font-weight:700; font-size:20px; color:#004a99; margin-bottom:25px; }}
        .kpi-wrapper {{ display:flex; flex-direction:column; align-items:center; margin-top:20px; }}
        .box-header-dc {{ background:linear-gradient(135deg,#0f4287,#2563eb); color:white; width:320px; padding:18px 22px; border-radius:22px; text-align:center; font-weight:900; font-size:16px; margin-bottom:18px; box-shadow:0 18px 40px rgba(15,66,135,.18); letter-spacing:.08em; text-transform:uppercase; }}
        .box-header-tt {{ background:linear-gradient(135deg,#6d0b8c,#9333ea); color:white; width:320px; padding:18px 22px; border-radius:22px; text-align:center; font-weight:900; font-size:16px; margin-bottom:18px; box-shadow:0 18px 40px rgba(109,11,140,.18); letter-spacing:.08em; text-transform:uppercase; }}
        .data-card-dc {{ background-color:rgba(255,255,255,.96); width:320px; padding:24px; border-radius:24px; border:2px solid #0f4287; text-align:center; margin-bottom:16px; box-shadow:0 16px 40px rgba(0,0,0,.08); }}
        .data-card-tt {{ background-color:rgba(255,255,255,.96); width:320px; padding:24px; border-radius:24px; border:2px solid #6d0b8c; text-align:center; margin-bottom:16px; box-shadow:0 16px 40px rgba(0,0,0,.08); }}
        .label {{ color:#4b5563; font-weight:800; font-size:13px; text-transform:uppercase; display:block; letter-spacing:.1em; margin-bottom:8px; }}
        .value {{ color:#111827; font-size:42px; font-weight:900; display:block; line-height:1.05; }}
        .section-title-dc {{ color:#004a99; font-size:38px; font-weight:900; margin-bottom:10px; }}
        .section-title-tt {{ color:#70008f; font-size:38px; font-weight:900; margin-bottom:10px; }}
        .small-subtitle-dc {{ color:#004a99; font-weight:800; font-size:18px; margin-bottom:10px; }}
        .small-subtitle-tt {{ color:#70008f; font-weight:800; font-size:18px; margin-bottom:10px; }}
        .block-filter {{ background-color:rgba(255,255,255,.85); padding:16px; border-radius:16px; border:1px solid #d9d9d9; margin-top:20px; margin-bottom:20px; }}
        .stExpander {{ border-radius:12px !important; overflow:hidden; }}
    </style>""", unsafe_allow_html=True)
