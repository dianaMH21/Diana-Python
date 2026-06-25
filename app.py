import streamlit as st
import pandas as pd
import base64
import os
import re
from io import BytesIO

st.set_page_config(page_title="Dashboard Teletalk Digital", layout="wide", initial_sidebar_state="expanded")

@st.cache_data(ttl=3600)
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
    bg = _leer_img_b64(img_file)
    if not bg:
        st.sidebar.warning(f"Imagen no encontrada: {img_file}")
    st.markdown(f"""<style>
        .stApp {{ {bg} background-size:cover; background-position:center; background-attachment:fixed; }}
        .stApp::before {{ content:""; position:fixed; inset:0;
            background:linear-gradient(135deg,rgba(2,6,23,.48) 0%,rgba(10,26,68,.34) 50%,rgba(60,5,80,.30) 100%);
            pointer-events:none; z-index:0; }}
        .caratula-hero {{
            position:relative; z-index:1; text-align:center;
            padding:52px 24px 44px 24px;
            background:linear-gradient(135deg,rgba(7,24,52,.84),rgba(15,66,135,.78) 52%,rgba(79,23,135,.76));
            border-radius:30px; border:1px solid rgba(255,255,255,.16);
            box-shadow:0 40px 100px rgba(2,8,23,.36),0 12px 36px rgba(15,66,135,.22);
            backdrop-filter:blur(22px); -webkit-backdrop-filter:blur(22px);
            margin-bottom:30px; overflow:hidden;
        }}
        .caratula-hero::before {{
            content:""; position:absolute; width:500px; height:500px;
            right:-170px; top:-170px; border-radius:50%;
            background:radial-gradient(circle,rgba(124,58,237,.20),transparent 70%);
            pointer-events:none;
        }}
        .caratula-badge {{
            display:inline-flex; align-items:center; gap:8px;
            padding:8px 18px; border-radius:999px;
            background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22);
            color:rgba(255,255,255,.88); font-size:11px; font-weight:800;
            letter-spacing:.16em; text-transform:uppercase; margin-bottom:20px;
        }}
        .main-title {{
            text-align:center; color:white; font-weight:950; font-size:60px;
            letter-spacing:-.04em; line-height:.96; margin-bottom:8px;
            text-shadow:0 4px 32px rgba(37,99,235,.38);
        }}
        .title-accent {{ color:#bfdbfe; }}
        .sub-title {{
            text-align:center; font-weight:700; font-size:18px;
            color:rgba(255,255,255,.78); margin-bottom:28px; letter-spacing:.01em;
        }}
        .caratula-divider {{
            width:80px; height:3px; margin:0 auto 26px auto;
            background:linear-gradient(90deg,#2563eb,#9333ea); border-radius:99px;
        }}
        .caratula-pills {{
            display:flex; justify-content:center; gap:10px; flex-wrap:wrap;
        }}
        .caratula-pill {{
            display:inline-flex; align-items:center; gap:6px;
            padding:9px 16px; border-radius:13px;
            background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.18);
            color:rgba(255,255,255,.82); font-size:12px; font-weight:750;
        }}
        .kpi-wrapper {{ display:flex; flex-direction:column; align-items:center; margin-top:20px; }}
        .box-header-dc {{ background:linear-gradient(135deg,#0f4287,#2563eb); color:white; width:320px; padding:18px 22px; border-radius:22px; text-align:center; font-weight:900; font-size:16px; margin-bottom:18px; box-shadow:0 18px 40px rgba(15,66,135,.28); letter-spacing:.08em; text-transform:uppercase; }}
        .box-header-tt {{ background:linear-gradient(135deg,#6d0b8c,#9333ea); color:white; width:320px; padding:18px 22px; border-radius:22px; text-align:center; font-weight:900; font-size:16px; margin-bottom:18px; box-shadow:0 18px 40px rgba(109,11,140,.28); letter-spacing:.08em; text-transform:uppercase; }}
        .data-card-dc {{ background:rgba(255,255,255,.97); width:320px; padding:24px; border-radius:24px; border:2px solid #0f4287; text-align:center; margin-bottom:16px; box-shadow:0 16px 40px rgba(0,0,0,.10); }}
        .data-card-tt {{ background:rgba(255,255,255,.97); width:320px; padding:24px; border-radius:24px; border:2px solid #6d0b8c; text-align:center; margin-bottom:16px; box-shadow:0 16px 40px rgba(0,0,0,.10); }}
        .label {{ color:#4b5563; font-weight:800; font-size:13px; text-transform:uppercase; display:block; letter-spacing:.1em; margin-bottom:8px; }}
        .value {{ color:#111827; font-size:42px; font-weight:900; display:block; line-height:1.05; }}
        .section-title-dc {{ color:#004a99; font-size:38px; font-weight:900; margin-bottom:10px; }}
        .section-title-tt {{ color:#70008f; font-size:38px; font-weight:900; margin-bottom:10px; }}
        .small-subtitle-dc {{ color:#004a99; font-weight:800; font-size:18px; margin-bottom:10px; }}
        .small-subtitle-tt {{ color:#70008f; font-weight:800; font-size:18px; margin-bottom:10px; }}
        .block-filter {{ background:rgba(255,255,255,.92); padding:16px; border-radius:16px; border:1px solid #d9d9d9; margin-top:20px; margin-bottom:20px; backdrop-filter:blur(10px); }}
        .stExpander {{ border-radius:12px !important; overflow:hidden; }}
    </style>""", unsafe_allow_html=True)

DATA_DIR = "."
MESES_ES = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
            7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
MESES_MAP = {v.lower(): k for k, v in MESES_ES.items()}

CSV_MAP = {
    "dbo.CLARO_DC_FIJA":              "CLARO_DC_FIJA.csv",
    "dbo.CLARO_DC_FIJA_SEGUNDA_CAIDA": "CLARO_DC_FIJA_SEGUNDA_CAIDA.csv",
    "dbo.CLARO_TELETALK_FIJA":        "CLARO_TELETALK_FIJA.csv",
    "dbo.CLARO_DC_MOVIL":             "CLARO_DC_MOVIL.csv",
    "dbo.CLARO_TELETALK_MOVIL":       "CLARO_TELETALK_MOVIL.csv",
    "[DATA DEVELZ].dbo.FIJA_DC":      "FIJA_DC.csv",
    "[DATA DEVELZ].dbo.FIJA_TELETALK":"FIJA_TELETALK.csv",
}

TIPIS_ESTADO_MAP = {
    "ATENDIDA/CONFORME":"Conforme","CONFORME PODIO":"Conforme","ATENDIDA - REASIGNACION":"Conforme",
    "CONFORME":"Conforme","ATENDIDA/OBSERVADO":"Conforme","AUDIO LOTEADO":"Conforme",
    "CONFORME - REASIGNACION":"Conforme","AUDIO KO":"1era Caída","SOT CON OTRO DAC":"1era Caída",
    "SEC SIN CORRECCIÓN":"1era Caída","SEC SIN CORRECCION":"1era Caída","OTROS":"1era Caída",
    "EDIFICIO NO LIBERADO PC":"1era Caída","SIN COBERTURA PC":"1era Caída","FICHA DUPLICADA":"1era Caída",
    "SEC CON EXCLUSIVIDAD":"1era Caída","NO ADJUNTA SUSTENTO":"1era Caída","NO ENVIA SUSTENTO":"1era Caída",
    "VENTA CARRUSEL":"1era Caída","DIRECCIÓN CON SERVICIO DE BAJA":"1era Caída",
    "DIRECCION CON SERVICIO DE BAJA":"1era Caída","FACILIDADES TECNICAS":"2da Caída",
    "CLIENTE NO DESEA":"2da Caída","FALTA CONTACTO":"2da Caída","CLIENTE NO CALIFICA":"2da Caída",
    "PRUEBA - CANCELADA":"2da Caída","DIRECCION INCORRECTA":"2da Caída","DIRECCIÓN INCORRECTA":"2da Caída",
    "MALA OFERTA":"2da Caída","RED SATURADA":"2da Caída","FRAUDE":"2da Caída","VIAJE O MUDANZA":"2da Caída",
    "CONTRA OFERTA":"2da Caída","FALTA INFRAESTRUCTURA":"2da Caída","EDIFICIO NO LIBERADO":"2da Caída",
    "EJECUCION - AUDIO LOTEADO":"Ejecución","EJECUCION - AUDIO CONFORME":"Ejecución",
    "PENDIENTE AUDIO OK":"Ejecución","EJECUCION":"Ejecución","EJECUCION - SIN AUDIO":"Ejecución",
    "PENDIENTE SOT":"Ejecución","PENDIENTE AUDIO KO":"Ejecución","EJECUCION - AUDIO OBSERVADO":"Ejecución",
    "PENDIENTE PRE - AUDITORIA":"Ejecución","EJECUCION - REASIGNACION":"Ejecución",
    "EJECUCION - AUDITADO":"Ejecución",
}

ruta_base    = "."
img_caratula_png = os.path.join(ruta_base, "caratula.png")
img_caratula_jpg = os.path.join(ruta_base, "caratula.png.jpg")
img_caratula = img_caratula_png if os.path.exists(img_caratula_png) else img_caratula_jpg
img_dc       = os.path.join(ruta_base, "34bab75f-2b2e-455e-8935-377abf566b76.jpg")
img_tt       = os.path.join(ruta_base, "ab3ac40e-1612-430f-bb3a-817d24b709db.jpg")

# ─────────────────────────────────────────────────────────────────────────
# DVZ.csv unificado: reemplaza a FIJA_DC.csv, FIJA_TELETALK.csv,
# MOVIL_DC.csv y MOVIL_TELETALK.csv. Se identifica:
#   - FIJA vs MOVIL  -> columna "Tipo Producto" (valores "FIJA" / "MOVIL")
#   - D&C vs Teletalk -> columna "Datos Adicionales - Clip" (valores "D&C" / "TELETALK")
# Si DVZ.csv no existe, se conserva el comportamiento original (4 archivos sueltos).
# ─────────────────────────────────────────────────────────────────────────
_DVZ_SPLIT_MAP = {
    "FIJA_DC.csv":       ("FIJA",  "D&C"),
    "FIJA_TELETALK.csv": ("FIJA",  "TELETALK"),
    "MOVIL_DC.csv":      ("MOVIL", "D&C"),
    "MOVIL_TELETALK.csv":("MOVIL", "TELETALK"),
}

@st.cache_data(ttl=600)
def _leer_dvz_crudo():
    ruta = os.path.join(DATA_DIR, "DVZ.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    for enc in ["latin-1","utf-8-sig","utf-8","cp1252","iso-8859-1"]:
        for sep in [";",",","\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, on_bad_lines="skip", engine="python")
                df.columns = df.columns.str.strip()
                if len(df.columns) > 1: return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
    return pd.DataFrame()

@st.cache_data(ttl=600)
def _cargar_dvz_filtrado(nombre):
    tipo_prod, canal_clip = _DVZ_SPLIT_MAP[nombre]
    df = _leer_dvz_crudo()
    if df.empty:
        return df
    col_tipo = next((c for c in df.columns if c.strip().lower() == "tipo producto"), None)
    col_clip = next((c for c in df.columns if c.strip().lower() == "datos adicionales - clip"), None)
    if not col_tipo or not col_clip:
        return pd.DataFrame()
    mask_tipo = df[col_tipo].fillna("").astype(str).str.strip().str.upper() == tipo_prod
    mask_clip = df[col_clip].fillna("").astype(str).str.strip().str.upper() == canal_clip
    return df[mask_tipo & mask_clip].copy()

@st.cache_data(ttl=600)
def cargar_csv(nombre):
    # Interceptar los 4 archivos antiguos -> leer desde DVZ.csv si existe
    if nombre in _DVZ_SPLIT_MAP and os.path.exists(os.path.join(DATA_DIR, "DVZ.csv")):
        df_dvz = _cargar_dvz_filtrado(nombre)
        if not df_dvz.empty:
            return df_dvz
    ruta = os.path.join(DATA_DIR, nombre)
    for enc in ["latin-1","utf-8-sig","utf-8","cp1252","iso-8859-1"]:
        for sep in [";",",","\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, on_bad_lines="skip", engine="python")
                df.columns = df.columns.str.strip()
                if len(df.columns) > 1: return df
            except FileNotFoundError:
                st.warning(f"Archivo no encontrado: {ruta}")
                return pd.DataFrame()
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
    st.error(f"No se pudo leer {nombre}")
    return pd.DataFrame()

def get_tabla(nombre):
    return cargar_csv(CSV_MAP.get(nombre, nombre.split(".")[-1] + ".csv"))

def preparar_fechas_fija(df):
    for col in ["FECHA INSTALACION", "FECHA GENERACION", "FECHA DE VENTA"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df

def preparar_fechas_movil(df):
    for col in ["FECHA OPERACION", "FECHA CARGA", "FECHA DE VENTA", "FECHA VENTA", "Fecha de Venta", "Fecha Venta"]:
        if col not in df.columns: continue
        serie = df[col].astype(str).str.strip()
        es_iso = serie.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
        es_lat = serie.str.match(r"^\d{1,2}/\d{1,2}/\d{4}$", na=False)
        fechas = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        if es_iso.any(): fechas.loc[es_iso] = pd.to_datetime(serie.loc[es_iso], format="%Y-%m-%d", errors="coerce")
        if es_lat.any(): fechas.loc[es_lat] = pd.to_datetime(serie.loc[es_lat], dayfirst=True, errors="coerce")
        otros = ~(es_iso | es_lat)
        if otros.any(): fechas.loc[otros] = pd.to_datetime(serie.loc[otros], errors="coerce", dayfirst=True)
        df[col] = fechas
    return df

def encontrar_columna(df, posibles):
    return next((n for n in posibles if n in df.columns), None)

def obtener_comision_fija(df):
    col = encontrar_columna(df, ["COMISION","COMISIÓN","Comision","Comisión","comision","comisión","COMIS","MONTO"])
    return pd.to_numeric(df[col], errors="coerce").fillna(0) if col else pd.Series([0.0]*len(df))

def obtener_comision_movil(df):
    col = encontrar_columna(df, ["COMISION TOTAL","COMISIÓN TOTAL","Comision Total","COMISION","MONTO"])
    return pd.to_numeric(df[col], errors="coerce").fillna(0) if col else pd.Series([0.0]*len(df))

def formatear_moneda(v):
    try: return f"S/ {float(v):,.2f}"
    except: return "S/ 0.00"

# =========================================================
# AUDITORÍA DE DESCARGAS
# =========================================================
def registrar_descarga(seccion, archivo, filtros=""):
    try:
        from datetime import datetime
        log_file = os.path.join(DATA_DIR, "log_descargas.csv")
        nuevo = pd.DataFrame([{"fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": st.session_state.get("usuario_logueado","Sin usuario"),
            "seccion": seccion, "archivo": archivo, "filtros": filtros, "accion": "DESCARGA"}])
        final = pd.concat([pd.read_csv(log_file, encoding="utf-8-sig"), nuevo], ignore_index=True) if os.path.exists(log_file) else nuevo
        final.to_csv(log_file, index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"Error registrando descarga: {e}")

def mostrar_auditoria_descargas():
    set_bg(img_caratula)
    st.markdown('<div class="section-title-dc">Auditoria de Descargas</div>', unsafe_allow_html=True)
    st.write("---")
    if st.session_state.get("usuario_logueado","") != "Fiorella":
        st.error("Acceso restringido."); return
    log_file = os.path.join(DATA_DIR, "log_descargas.csv")
    if not os.path.exists(log_file): st.info("No hay descargas registradas."); return
    df_log = pd.read_csv(log_file, encoding="utf-8-sig")
    if df_log.empty: st.info("No hay descargas registradas."); return
    df_log["fecha_hora"] = pd.to_datetime(df_log["fecha_hora"], errors="coerce")
    df_log = df_log.sort_values("fecha_hora", ascending=False)
    ult = df_log["fecha_hora"].max().strftime("%d/%m/%Y %H:%M:%S") if df_log["fecha_hora"].notna().any() else "Sin fecha"
    c1,c2,c3 = st.columns(3)
    _kpi_card_html(c1,"Total Descargas",f"{len(df_log):,}","Historico","#0f4287","#0f4287")
    _kpi_card_html(c2,"Usuarios",f"{df_log['usuario'].nunique() if 'usuario' in df_log.columns else 0:,}","Con actividad","#0f4287","#0f4287")
    _kpi_card_html(c3,"Ultima Descarga",ult,"Mas reciente","#0f4287","#0f4287")
    st.write("---")
    f1,f2 = st.columns(2)
    with f1: filtro_usuario = st.selectbox("Usuario", (["Todos"]+sorted(df_log["usuario"].dropna().astype(str).unique().tolist())) if "usuario" in df_log.columns else ["Todos"], key="audit_usuario")
    with f2: filtro_seccion = st.selectbox("Seccion",  (["Todas"]+sorted(df_log["seccion"].dropna().astype(str).unique().tolist())) if "seccion"  in df_log.columns else ["Todas"], key="audit_seccion")
    df_show = df_log.copy()
    if filtro_usuario != "Todos" and "usuario" in df_show.columns: df_show = df_show[df_show["usuario"].astype(str)==filtro_usuario]
    if filtro_seccion != "Todas" and "seccion"  in df_show.columns: df_show = df_show[df_show["seccion"].astype(str)==filtro_seccion]
    df_show["fecha_hora"] = df_show["fecha_hora"].dt.strftime("%d/%m/%Y %H:%M:%S")
    st.dataframe(df_show, use_container_width=True, height=480)
    st.download_button("Descargar historial", data=df_log.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="auditoria_descargas.csv", mime="text/csv", key="dl_auditoria_descargas")

def parse_mes_anio(txt):
    if not txt or txt == "Todos los meses": return None, None
    p = txt.strip().lower().split()
    if len(p) == 2 and p[0] in MESES_MAP and p[1].isdigit(): return MESES_MAP[p[0]], int(p[1])
    return None, None

def filtrar_por_mes_anio(df, col, txt):
    m, y = parse_mes_anio(txt)
    if m and y and col in df.columns: return df[(df[col].dt.month == m) & (df[col].dt.year == y)].copy()
    return df.copy()

def porta_si(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False).isin(['SI','YES','Y'])

def _es_portabilidad_movil(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False) == "PORTABILIDAD"

def _es_alta_movil(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False).isin(["ALTA NUEVA","ALTA"])

@st.cache_data(ttl=3600)
def obtener_meses_fija(col):
    meses = set()
    for nombre in ["CLARO_DC_FIJA.csv","CLARO_TELETALK_FIJA.csv"]:
        df = preparar_fechas_fija(cargar_csv(nombre))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].capitalize()} {f.year}" for f in df[col].dropna())
    return (["Todos los meses"] +
            sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))))

@st.cache_data(ttl=3600)
def obtener_meses_fija_develz(col):
    meses = set()
    for nombre in ["FIJA_DC.csv", "FIJA_TELETALK.csv"]:
        df = preparar_fechas_fija(cargar_csv(nombre))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].capitalize()} {f.year}" for f in df[col].dropna())
    return (["Todos los meses"] +
            sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))))

@st.cache_data(ttl=3600)
def obtener_meses_movil(col, archivos):
    meses = set()
    for a in archivos:
        df = preparar_fechas_movil(cargar_csv(a))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].lower()} {f.year}".capitalize()
                         for f in df[df[col].notna()][col])
    return (["Todos los meses"] +
            sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))))

@st.cache_data(ttl=3600)
def obtener_metricas_fija(tabla, f_inst, f_gene):
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return 0, 0.0
        if f_inst != "Todos los meses": df = filtrar_por_mes_anio(df, "FECHA INSTALACION", f_inst)
        if f_gene != "Todos los meses": df = filtrar_por_mes_anio(df, "FECHA GENERACION", f_gene)
        return int(df["SOT"].nunique() if "SOT" in df.columns else 0), float(obtener_comision_fija(df).sum())
    except: return 0, 0.0

@st.cache_data(ttl=3600)
def obtener_reporte_liquidado(ventas_tabla, maestro_tabla, fecha_inst):
    cols = ["SOT","ASESOR","Nombre del Cliente","COMISION","COMISIONES","¿Pagado?"]
    try:
        df_v = preparar_fechas_fija(get_tabla(ventas_tabla))
        df_m = get_tabla(maestro_tabla)
        if df_v.empty: return pd.DataFrame(columns=cols)
        df_v = filtrar_por_mes_anio(df_v, "FECHA INSTALACION", fecha_inst)
        df_v["SOT"] = df_v["SOT"].astype(str).str.strip()
        if not df_m.empty and "Back Office - Sot" in df_m.columns:
            df_m["Back Office - Sot"] = df_m["Back Office - Sot"].astype(str).str.strip()
            df = df_v.merge(df_m, left_on="SOT", right_on="Back Office - Sot", how="left")
        else:
            df = df_v.copy()
        df["ASESOR"] = df.get("USUARIO", pd.Series([""] * len(df))).replace("", pd.NA).fillna("Sin Asesor")
        nom = df.get("Cliente - Nombre", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
        ape = df.get("Cliente - Apellido Paterno", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
        df["Nombre del Cliente"] = (nom + " " + ape).str.strip().replace("", "Sin Datos").fillna("Sin Datos")
        df["COMISION"] = obtener_comision_fija(df)
        df["¿Pagado?"] = df["COMISION"].apply(lambda x: "SÍ" if x > 0 else "NO")
        return df[cols]
    except Exception as e:
        st.error(f"Error reporte liquidado: {e}")
        return pd.DataFrame(columns=cols)

def _base_factor_fija(df, col_fecha):
    df["COMISION"] = obtener_comision_fija(df)
    df["_porta"] = porta_si(df.get("PORTABILIDAD", pd.Series([""] * len(df))).fillna("").astype(str))
    srv = df.get("SERVICIO", pd.Series([""] * len(df))).fillna("").astype(str).str.upper()
    tip = df.get("TIPO TRABAJO", pd.Series([""] * len(df))).fillna("").astype(str).str.upper()
    df["_ftth"] = srv.str.contains("FTTH") | tip.str.contains("FTTH")
    df["_hfc"]  = srv.str.contains("HFC")  | tip.str.contains("HFC")
    df["_anio"] = df[col_fecha].dt.year
    df["_mes"]  = df[col_fecha].dt.month
    return df

@st.cache_data(ttl=3600)
def obtener_factor_fija_resumen(tabla, col_fecha, filtro):
    cols = ["Año","Mes","Ventas","PORTABILIDAD SI","PORTABILIDAD NO","FTTH","HFC","S/."]
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        df = _base_factor_fija(df, col_fecha)
        ds = df.drop_duplicates(subset=["SOT","_anio","_mes"])
        grp = ds.groupby(["_anio","_mes"]).agg(
            Ventas=("SOT","nunique"), **{"PORTABILIDAD SI":("_porta","sum")},
            **{"PORTABILIDAD NO":("_porta", lambda x: (~x).sum())},
            FTTH=("_ftth","sum"), HFC=("_hfc","sum"),
        ).reset_index()
        com = df.groupby(["_anio","_mes"])["COMISION"].sum().reset_index()
        com.columns = ["_anio","_mes","S/."]
        grp = grp.merge(com, on=["_anio","_mes"], how="left")
        grp.columns = ["Año","MesNum","Ventas","PORTABILIDAD SI","PORTABILIDAD NO","FTTH","HFC","S/."]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        return grp.sort_values(["Año","MesNum"])[cols]
    except Exception as e:
        st.error(f"Error factor fija resumen: {e}")
        return pd.DataFrame(columns=cols)

@st.cache_data(ttl=3600)
def obtener_factor_fija_detallado(tabla, col_fecha, filtro):
    cols = ["Año","Mes","MesNum","Dia","Ventas","Porta_SI","Porta_NO","FTTH","HFC","Monto"]
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        df = _base_factor_fija(df, col_fecha)
        df["_dia"] = df[col_fecha].dt.day
        ds = df.drop_duplicates(subset=["SOT","_anio","_mes","_dia"])
        grp = ds.groupby(["_anio","_mes","_dia"]).agg(
            Ventas=("SOT","nunique"), Porta_SI=("_porta","sum"),
            Porta_NO=("_porta", lambda x: (~x).sum()), FTTH=("_ftth","sum"), HFC=("_hfc","sum"),
        ).reset_index()
        com = df.groupby(["_anio","_mes","_dia"])["COMISION"].sum().reset_index()
        com.columns = ["_anio","_mes","_dia","Monto"]
        grp = grp.merge(com, on=["_anio","_mes","_dia"], how="left")
        grp.columns = ["Año","MesNum","Dia","Ventas","Porta_SI","Porta_NO","FTTH","HFC","Monto"]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        return grp.sort_values(["Año","MesNum","Dia"], ascending=[False,False,True])[cols]
    except Exception as e:
        st.error(f"Error factor fija detallado: {e}")
        return pd.DataFrame(columns=cols)

def _base_factor_movil(df, col_fecha):
    df["_comision"] = obtener_comision_movil(df)
    tr = df.get("TRANSACCION", pd.Series([""] * len(df), index=df.index)).fillna("").astype(str)
    df["_porta"] = _es_portabilidad_movil(tr)
    df["_alta"]  = _es_alta_movil(tr)
    cf   = pd.to_numeric(df.get("CF",   pd.Series([0.0]*len(df), index=df.index)), errors="coerce").fillna(0)
    dias = pd.to_numeric(df.get("DIAS PORTADAS", pd.Series([0.0]*len(df), index=df.index)), errors="coerce").fillna(0)
    df["_cf_mayor"]   = cf > 69.90;   df["_cf_menor"]   = cf <= 69.90
    df["_dias_mayor"] = dias > 90;    df["_dias_menor"]  = dias <= 90
    df["_anio"] = df[col_fecha].dt.year.astype("Int64")
    df["_mes"]  = df[col_fecha].dt.month.astype("Int64")
    return df

@st.cache_data(ttl=3600)
def obtener_factor_movil_resumen(tabla, filtro, col_fecha):
    cols = ["Año","Mes","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","S/."]
    try:
        df = preparar_fechas_movil(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        if df.empty: return pd.DataFrame(columns=cols)
        df = _base_factor_movil(df, col_fecha)
        grp = df.groupby(["_anio","_mes"]).agg(
            Ventas=("TRANSACCION","size"), PORTABILIDAD=("_porta","sum"), ALTA=("_alta","sum"),
            **{"CF>69.90":("_cf_mayor","sum")}, **{"CF<=69.90":("_cf_menor","sum")},
            **{"Dias>90":("_dias_mayor","sum")}, **{"Dias<=90":("_dias_menor","sum")},
            **{"S/.":("_comision","sum")},
        ).reset_index()
        grp.columns = ["Año","MesNum","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","S/."]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        int_cols = ["Año","MesNum","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90"]
        for c in int_cols: grp[c] = pd.to_numeric(grp[c], errors="coerce").fillna(0).astype(int)
        return grp.sort_values(["Año","MesNum"])[cols]
    except Exception as e:
        st.error(f"Error factor móvil resumen: {e}")
        return pd.DataFrame(columns=cols)

@st.cache_data(ttl=3600)
def obtener_factor_movil_detallado(tabla, filtro, col_fecha):
    cols = ["Año","Mes","MesNum","Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","Monto"]
    try:
        df = preparar_fechas_movil(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        if df.empty: return pd.DataFrame(columns=cols)
        df = _base_factor_movil(df, col_fecha)
        df["_dia"] = df[col_fecha].dt.day.astype("Int64")
        grp = df.groupby(["_anio","_mes","_dia"]).agg(
            Ventas=("TRANSACCION","size"), PORTABILIDAD=("_porta","sum"), ALTA=("_alta","sum"),
            **{"CF>69.90":("_cf_mayor","sum")}, **{"CF<=69.90":("_cf_menor","sum")},
            **{"Dias>90":("_dias_mayor","sum")}, **{"Dias<=90":("_dias_menor","sum")},
            Monto=("_comision","sum"),
        ).reset_index()
        grp.columns = ["Año","MesNum","Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","Monto"]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        int_cols = ["Año","MesNum","Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90"]
        for c in int_cols: grp[c] = pd.to_numeric(grp[c], errors="coerce").fillna(0).astype(int)
        return grp.sort_values(["Año","MesNum","Dia"], ascending=[False,False,True])[cols]
    except Exception as e:
        st.error(f"Error factor móvil detallado: {e}")
        return pd.DataFrame(columns=cols)

def construir_ranking_asesores(df):
    if df.empty: return pd.DataFrame(columns=["Rank","ASESOR","Cantidad_Ventas","Ventas_Pagadas","Ventas_No_Pagadas","Total_Comision"])
    df = df.copy()
    cn = df["COMISIONES"].astype(str).str.upper().str.replace('Í','I',regex=False).str.strip()
    df["_cn"] = cn
    r = (df.groupby("ASESOR", dropna=False).agg(
        Total_Comision=("COMISION","sum"),
        Ventas_Pagadas=("SOT", lambda x: x[df.loc[x.index,"_cn"] == "SI"].nunique()),
        Ventas_No_Pagadas=("SOT", lambda x: x[df.loc[x.index,"_cn"] == "NO"].nunique()),
    ).reset_index().sort_values("Total_Comision", ascending=False))
    r["Rank"] = r["Total_Comision"].rank(method="dense", ascending=False).astype(int)
    r["Cantidad_Ventas"] = r["Ventas_Pagadas"] + r["Ventas_No_Pagadas"]
    r = r[["Rank","ASESOR","Cantidad_Ventas","Ventas_Pagadas","Ventas_No_Pagadas","Total_Comision"]]
    total = pd.DataFrame([{"Rank":"Total","ASESOR":"","Cantidad_Ventas":r["Cantidad_Ventas"].sum(),
        "Ventas_Pagadas":r["Ventas_Pagadas"].sum(),"Ventas_No_Pagadas":r["Ventas_No_Pagadas"].sum(),
        "Total_Comision":r["Total_Comision"].sum()}])
    return pd.concat([r, total], ignore_index=True)

def mostrar_tabla_ranking(ranking):
    if ranking.empty: st.warning("No se encontraron datos para el ranking."); return
    st.table(ranking.style.format({"Total_Comision":"S/ {:,.2f}"})
        .set_table_attributes('style="width:1000px;table-layout:fixed;background-color:white;"')
        .set_table_styles([
            {"selector":"th","props":[("text-align","center"),("font-size","14px"),("padding","8px"),("background-color","white")]},
            {"selector":"td","props":[("padding","8px"),("font-size","13px"),("white-space","nowrap"),("overflow","hidden"),("text-overflow","ellipsis"),("background-color","white")]},
        ])
        .set_properties(**{"text-align":"center"}, subset=["Rank","Cantidad_Ventas","Ventas_Pagadas","Ventas_No_Pagadas","Total_Comision"])
        .set_properties(**{"text-align":"left"}, subset=["ASESOR"]))

def _style_tabla(color):
    hc = "#0f4287" if color == "dc" else "#70008f"
    return [
        {"selector":"th","props":[("background-color","white"),("color",hc),("font-size","13px"),("text-align","center"),("border-bottom","2px solid #ddd")]},
        {"selector":"td","props":[("padding","10px 8px"),("font-size","13px"),("border-bottom","1px solid #eee"),("background-color","white")]}
    ]

def mostrar_expanders_fija(df_det, color="dc"):
    if df_det.empty: st.warning("No se encontraron datos."); return
    icono = "🔵" if color == "dc" else "🟣"
    for _, p in (df_det[["Año","Mes","MesNum"]].drop_duplicates()
                 .sort_values(["Año","MesNum"], ascending=[False,False])).iterrows():
        dm = df_det[(df_det["Año"] == p["Año"]) & (df_det["Mes"] == p["Mes"])].copy()
        with st.expander(f"{icono} {p['Mes']} {p['Año']}  |  Ventas: {int(dm['Ventas'].sum())}  |  Total: {formatear_moneda(dm['Monto'].sum())}", expanded=False):
            t = dm[["Dia","Ventas","Porta_SI","Porta_NO","FTTH","HFC","Monto"]].copy()
            t["Monto"] = t["Monto"].map(formatear_moneda)
            st.table(t)

def mostrar_expanders_movil(df_det, color="dc"):
    if df_det.empty: st.warning("No se encontraron datos."); return
    icono = "🔵" if color == "dc" else "🟣"
    for _, p in (df_det[["Año","Mes","MesNum"]].drop_duplicates()
                 .sort_values(["Año","MesNum"], ascending=[False,False])).iterrows():
        dm = df_det[(df_det["Año"] == p["Año"]) & (df_det["Mes"] == p["Mes"])].copy()
        with st.expander(f"{icono} {p['Mes']} {p['Año']}  |  Ventas: {int(dm['Ventas'].sum())}  |  Total: {formatear_moneda(dm['Monto'].sum())}", expanded=False):
            t = dm[["Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","Monto"]].copy()
            t["Monto"] = t["Monto"].map(formatear_moneda)
            st.table(t)

def mostrar_factor_fija(tabla, col_fecha, filtro, color):
    col1, col2 = st.columns([1.1, 1.6])
    with col1:
        st.markdown("### Resumen")
        df_f = obtener_factor_fija_resumen(tabla, col_fecha, filtro)
        if df_f.empty: st.warning("Sin datos.")
        else:
            total = pd.DataFrame([{"Año":"Total","Mes":"","Ventas":df_f["Ventas"].sum(),
                "PORTABILIDAD SI":df_f["PORTABILIDAD SI"].sum(),"PORTABILIDAD NO":df_f["PORTABILIDAD NO"].sum(),
                "FTTH":df_f["FTTH"].sum(),"HFC":df_f["HFC"].sum(),"S/.":df_f["S/."].sum()}])
            d = pd.concat([df_f, total], ignore_index=True)
            d["S/."] = d["S/."].map(formatear_moneda)
            st.table(d.style.set_table_styles(_style_tabla(color))
                .set_properties(subset=["Año","Mes"], **{"text-align":"left"})
                .set_properties(subset=["Ventas","PORTABILIDAD SI","PORTABILIDAD NO","FTTH","HFC","S/."], **{"text-align":"center"}))
    with col2:
        st.markdown("### Detalle desplegable")
        mostrar_expanders_fija(obtener_factor_fija_detallado(tabla, col_fecha, filtro), color=color)

def mostrar_factor_movil(tabla, col_fecha, filtro, color):
    col1, col2 = st.columns([1.2, 1.6])
    with col1:
        st.markdown("### Resumen")
        df_r = obtener_factor_movil_resumen(tabla, filtro, col_fecha)
        if df_r.empty: st.warning("Sin datos.")
        else:
            total = pd.DataFrame([{"Año":"Total","Mes":"","Ventas":df_r["Ventas"].sum(),
                "PORTABILIDAD":df_r["PORTABILIDAD"].sum(),"ALTA":df_r["ALTA"].sum(),
                "CF>69.90":df_r["CF>69.90"].sum(),"CF<=69.90":df_r["CF<=69.90"].sum(),
                "Dias>90":df_r["Dias>90"].sum(),"Dias<=90":df_r["Dias<=90"].sum(),"S/.":df_r["S/."].sum()}])
            d = pd.concat([df_r, total], ignore_index=True)
            d["S/."] = d["S/."].map(formatear_moneda)
            st.table(d.style.set_table_styles(_style_tabla(color))
                .set_properties(subset=["Año","Mes"], **{"text-align":"left"})
                .set_properties(subset=["Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","S/."], **{"text-align":"center"}))
    with col2:
        st.markdown("### Detalle desplegable")
        mostrar_expanders_movil(obtener_factor_movil_detallado(tabla, filtro, col_fecha), color=color)

def mostrar_iae_movil(tabla, col_fecha, filtro, key_asesor, color):
    df_m = preparar_fechas_movil(get_tabla(tabla))
    df_m = filtrar_por_mes_anio(df_m, col_fecha, filtro)
    if df_m.empty: st.warning("Sin datos."); return
    df_m["_comision"] = obtener_comision_movil(df_m)
    tr = df_m.get("TRANSACCION", pd.Series([""] * len(df_m))).fillna("").astype(str)
    df_m["_porta"] = _es_portabilidad_movil(tr)
    df_m["_alta"]  = _es_alta_movil(tr)
    col_a = encontrar_columna(df_m, ["USUARIO","ASESOR","VENDEDOR","DISTRIBUIDOR"])
    df_m["ASESOR"] = df_m[col_a].fillna("Sin Asesor") if col_a else "Sin Asesor"
    filtro_a = st.selectbox("Selecciona Asesor", ["Todos"] + sorted(df_m["ASESOR"].unique().tolist()), key=key_asesor)
    df_f = df_m[df_m["ASESOR"] == filtro_a].copy() if filtro_a != "Todos" else df_m.copy()
    st.markdown("### Ranking de Asesores")
    r = (df_f.groupby("ASESOR").agg(
        Total_Ventas=("_porta", lambda x: len(x)), Portabilidades=("_porta","sum"),
        Altas=("_alta","sum"), Comision_Total=("_comision","sum"),
    ).reset_index().sort_values("Comision_Total", ascending=False))
    r["Rank"] = r["Comision_Total"].rank(method="dense", ascending=False).astype(int)
    r = r[["Rank","ASESOR","Total_Ventas","Portabilidades","Altas","Comision_Total"]]
    total = pd.DataFrame([{"Rank":"Total","ASESOR":"","Total_Ventas":r["Total_Ventas"].sum(),
        "Portabilidades":r["Portabilidades"].sum(),"Altas":r["Altas"].sum(),"Comision_Total":r["Comision_Total"].sum()}])
    st.table(pd.concat([r, total], ignore_index=True).style.format({"Comision_Total":"S/ {:,.2f}"})
        .set_properties(**{"text-align":"center"}).set_properties(subset=["ASESOR"], **{"text-align":"left"}))

def _normalizar_texto(txt):
    return str(txt).upper().strip().replace("Í","I").replace("Á","A").replace("É","E").replace("Ó","O").replace("Ú","U")

def _estado_desde_tipis(tipis_txt):
    return TIPIS_ESTADO_MAP.get(_normalizar_texto(tipis_txt), "Otros")

def _normalizar_sot_series(serie):
    """
    Normaliza SOT para cruces entre DEVELZ y CLARO.
    Corrige casos como:
    - 87274852.0  -> 87274852
    - 87274852    -> 87274852
    - espacios invisibles / caracteres raros
    - valores nulos
    - SOT con guiones o separadores

    IMPORTANTE:
    Esta función se usa para mostrar la SOT limpia.
    Para comparar de forma más agresiva se usa _sot_key_series().
    """
    s = serie.fillna("").astype(str).str.strip()
    s = s.str.replace("\\u00a0", "", regex=False)
    s = s.str.replace("\ufeff", "", regex=False)
    s = s.str.replace(r"\s+", "", regex=True)
    s = s.str.replace(r"\.0+$", "", regex=True)
    s = s.str.replace(r"^'", "", regex=True)
    s = s.replace(["nan","NaN","None","NONE","null","NULL","NaT","<NA>"], "")
    return s

def _sot_key_series(serie):
    """
    Llave técnica SOLO para cruces SOT.
    Evita falsos faltantes cuando una base trae la SOT como texto, número,
    decimal, con espacios, guiones o caracteres invisibles.

    Ejemplos que quedan iguales:
    - 87274852
    - 87274852.0
    - 87 274 852
    - 87-274-852
    """
    s = _normalizar_sot_series(serie)
    s = s.str.replace(r"[^0-9]", "", regex=True)
    s = s.str.lstrip("0")
    return s.replace(["nan","NaN","None","NONE","null","NULL","NaT","<NA>"], "")

# --- Obtención de campos DEVELZ ---
def _obtener_sot_develz(df):
    col = encontrar_columna(df, ["Back Office - Sot","Back Office - SOT","SOT","sot","Sot"])
    return df[col].fillna("").astype(str).str.strip() if col else pd.Series([""] * len(df), index=df.index)

def _obtener_fecha_inst_develz(df):
    col = encontrar_columna(df, ["Back Office - Fecha Instalacion","Back Office - Fecha Instalación",
                                  "FECHA INSTALACION","Fecha Instalacion","Fecha Instalación"])
    return pd.to_datetime(df[col], errors="coerce", dayfirst=True) if col else pd.Series(pd.NaT, index=df.index)

def _obtener_fecha_venta_develz(df):
    col = encontrar_columna(df, ["FECHA DE VENTA", "Fecha de Venta", "Fecha Venta", "FECHA VENTA",
                                  "Back Office - Fecha de Venta", "Back Office - Fecha Venta",
                                  "FECHA GENERACION", "Fecha Generacion", "Fecha Generación"])
    return pd.to_datetime(df[col], errors="coerce", dayfirst=True) if col else pd.Series(pd.NaT, index=df.index)

def _obtener_supervisor_develz(df):
    col = encontrar_columna(df, ["Datos Adicionales - Supervisor","Datos adicionales - Supervisor",
                                  "SUPERVISOR","Supervisor","supervisor","USUARIO","Usuario"])
    return (df[col].fillna("Sin Supervisor").astype(str).str.strip().replace("","Sin Supervisor")
            if col else pd.Series(["Sin Supervisor"] * len(df), index=df.index))

def _obtener_asesor_creador_develz(df):
    col = encontrar_columna(df, ["CREADOR","Creador","creador","Usuario Creador","USUARIO CREADOR",
                                  "Datos Adicionales - Creador","Datos adicionales - Creador"])
    return (df[col].fillna("Sin Asesor").astype(str).str.strip().replace("","Sin Asesor")
            if col else pd.Series(["Sin Asesor"] * len(df), index=df.index))

def _obtener_nombre_cliente_develz(df):
    def _col(posibles): return encontrar_columna(df, posibles)
    def _get(posibles, defecto=""):
        c = _col(posibles); return df[c].fillna("").astype(str).str.strip() if c else pd.Series([defecto]*len(df),index=df.index)
    nom     = _get(["Cliente - Nombre","NOMBRE","Nombre","CLIENTE"])
    ape_pat = _get(["Cliente - Apellido Paterno","Apellido Paterno","APELLIDO PATERNO"])
    ape_mat = _get(["Cliente - Apellido Materno","Apellido Materno","APELLIDO MATERNO"])
    return (nom+" "+ape_pat+" "+ape_mat).str.strip().replace("","Sin Datos").fillna("Sin Datos")

def _obtener_departamento_develz(df):
    col = encontrar_columna(df, ["Datos Instalación - Departamento","Datos Instalacion - Departamento",
                                  "DEPARTAMENTO","Departamento","departamento"])
    return (df[col].fillna("Sin Datos").astype(str).str.strip().replace("","Sin Datos")
            if col else pd.Series(["Sin Datos"] * len(df), index=df.index))

def _obtener_tipis_develz(df):
    col = encontrar_columna(df, ["TIPIS","Tipis","tipis","Estados - Venta Especificacion",
                                  "Estados - Venta Especificación","Estado - Venta Especificacion",
                                  "Estado - Venta Especificación","ESTADO OPERATIVO","Estado Operativo","estado operativo"])
    return (df[col].fillna("Sin TIPIS").astype(str).str.strip().replace("","Sin TIPIS")
            if col else pd.Series(["Sin TIPIS"] * len(df), index=df.index))

def _obtener_documento_develz(df):
    col = encontrar_columna(df, ["Cliente - Documento","Cliente - Nro Documento"])
    return df[col].fillna("").astype(str).str.strip() if col else pd.Series([""] * len(df), index=df.index)

@st.cache_data(ttl=600)
def _base_claro_pago(tabla_ventas):
    df_c = preparar_fechas_fija(get_tabla(tabla_ventas))
    cols = ["SOT","COMISION_CLARO","COMISIONES_CLARO","FECHA_INSTALACION_CLARO"]
    if df_c.empty or "SOT" not in df_c.columns: return pd.DataFrame(columns=cols)
    df_c = df_c.copy()
    df_c["SOT"] = _normalizar_sot_series(df_c["SOT"])
    df_c = df_c[df_c["SOT"] != ""]
    df_c["COMISION_CLARO"] = obtener_comision_fija(df_c)
    df_c["COMISIONES_CLARO"] = (df_c["COMISIONES"].fillna("").astype(str).str.upper().str.strip().str.replace("Í","I",regex=False)
                                 if "COMISIONES" in df_c.columns else "")
    df_c["_pagada_flag"] = (df_c["COMISIONES_CLARO"] == "SI") | (df_c["COMISION_CLARO"] > 0)
    # Extraer FECHA INSTALACION de CLARO para mostrarla en el detalle
    df_c["_FECHA_INST_CLARO_DT"] = pd.to_datetime(
        df_c["FECHA INSTALACION"] if "FECHA INSTALACION" in df_c.columns else None,
        errors="coerce", dayfirst=True
    )
    resumen = df_c.groupby("SOT", as_index=False).agg(
        COMISION_CLARO=("COMISION_CLARO","sum"),
        PAGADA_FLAG=("_pagada_flag","max"),
        FECHA_INSTALACION_CLARO=("_FECHA_INST_CLARO_DT","max"))
    resumen["COMISIONES_CLARO"] = resumen["PAGADA_FLAG"].apply(lambda x: "SI" if x else "NO")
    resumen["FECHA_INSTALACION_CLARO"] = pd.to_datetime(
        resumen["FECHA_INSTALACION_CLARO"], errors="coerce"
    ).dt.strftime("%d/%m/%Y").fillna("")
    return resumen[cols]

@st.cache_data(ttl=600)
def construir_detalle_fija_develz(tabla_maestro, tabla_claro, canal, filtro_mes, filtro_fecha_venta="Todos los meses"):
    cols_salida = ["Canal","SOT","Documento","SUPERVISOR","ASESOR","Nombre del Cliente","Departamento",
                   "FECHA INSTALACION","FECHA DE VENTA","TIPIS","Estado Operativo","COMISION","Estado Pago"]
    try:
        df_m = get_tabla(tabla_maestro)
        if df_m.empty: return pd.DataFrame(columns=cols_salida)
        df_m = df_m.copy()
        df_m["Canal"] = canal
        df_m["SOT"] = _normalizar_sot_series(_obtener_sot_develz(df_m))
        df_m["Documento"] = _obtener_documento_develz(df_m)
        df_m["_FECHA_DT"] = _obtener_fecha_inst_develz(df_m)
        df_m["_FECHA_VENTA_DT"] = _obtener_fecha_venta_develz(df_m)

        if filtro_mes != "Todos los meses":
            m, y = parse_mes_anio(filtro_mes)
            if m and y:
                df_m = df_m[(df_m["_FECHA_DT"].dt.month == m) & (df_m["_FECHA_DT"].dt.year == y)].copy()

        if filtro_fecha_venta != "Todos los meses":
            m_v, y_v = parse_mes_anio(filtro_fecha_venta)
            if m_v and y_v:
                df_m = df_m[(df_m["_FECHA_VENTA_DT"].dt.month == m_v) & (df_m["_FECHA_VENTA_DT"].dt.year == y_v)].copy()

        if df_m.empty: return pd.DataFrame(columns=cols_salida)
        df_m["SUPERVISOR"] = _obtener_supervisor_develz(df_m)
        df_m["ASESOR"] = _obtener_asesor_creador_develz(df_m)
        df_m["Nombre del Cliente"] = _obtener_nombre_cliente_develz(df_m)
        df_m["Departamento"] = _obtener_departamento_develz(df_m)
        df_m["TIPIS"] = _obtener_tipis_develz(df_m)
        df_m["Estado Operativo"] = df_m["TIPIS"].apply(_estado_desde_tipis)
        df_pago = _base_claro_pago(tabla_claro)
        df = df_m.merge(df_pago, on="SOT", how="left")

        # Diagnóstico interno opcional:
        # st.session_state["debug_detalle_fija"] = True
        if st.session_state.get("debug_detalle_fija", False):
            st.write(f"DEBUG {canal} | Base DEVELZ:", len(df_m))
            st.write(f"DEBUG {canal} | SOT DEVELZ únicos:", df_m["SOT"].nunique())
            st.write(f"DEBUG {canal} | Base CLARO pagos:", len(df_pago))
            st.write(f"DEBUG {canal} | Cruces encontrados:", df["COMISION_CLARO"].notna().sum())
            st.write(f"DEBUG {canal} | Pagadas SI:", (df.get("COMISIONES_CLARO", "").fillna("").astype(str).str.upper() == "SI").sum())
            st.write(f"DEBUG {canal} | Comisión mayor a 0:", (pd.to_numeric(df.get("COMISION_CLARO", 0), errors="coerce").fillna(0) > 0).sum())
        df["COMISION"] = pd.to_numeric(df.get("COMISION_CLARO", 0), errors="coerce").fillna(0)
        df["COMISIONES_CLARO"] = df.get("COMISIONES_CLARO","").fillna("").astype(str).str.upper().str.strip().str.replace("Í","I",regex=False)
        df["Estado Pago"] = "CAÍDA"
        df.loc[(df["COMISIONES_CLARO"] == "SI") | (df["COMISION"] > 0), "Estado Pago"] = "PAGADA"
        # FECHA INSTALACION: usar la del archivo CLARO cuando hay cruce, si no la de DEVELZ
        _fecha_claro = df.get("FECHA_INSTALACION_CLARO", pd.Series("", index=df.index)).fillna("")
        _fecha_develz = df["_FECHA_DT"].dt.strftime("%d/%m/%Y").fillna("")
        df["FECHA INSTALACION"] = _fecha_claro.where(_fecha_claro != "", _fecha_develz)
        df["FECHA DE VENTA"] = df["_FECHA_VENTA_DT"].dt.strftime("%d/%m/%Y").fillna("")
        for col in cols_salida:
            if col not in df.columns: df[col] = ""
        return df[cols_salida].reset_index(drop=True)
    except Exception as e:
        st.error(f"Error construyendo detalle DEVELZ {canal}: {e}")
        return pd.DataFrame(columns=cols_salida)

@st.cache_data(ttl=600)
def construir_detalle_fija_general(filtro_mes, filtro_fecha_venta="Todos los meses"):
    df_dc = construir_detalle_fija_develz("[DATA DEVELZ].dbo.FIJA_DC", "dbo.CLARO_DC_FIJA", "D&C", filtro_mes, filtro_fecha_venta)
    df_tt = construir_detalle_fija_develz("[DATA DEVELZ].dbo.FIJA_TELETALK", "dbo.CLARO_TELETALK_FIJA", "Teletalk", filtro_mes, filtro_fecha_venta)
    return pd.concat([df_dc, df_tt], ignore_index=True)

def kpi_detalle_fija(df):
    if df.empty: return 0, 0, 0, 0.0, 0.0
    t,p,c = int(len(df)), int((df["Estado Pago"]=="PAGADA").sum()), int((df["Estado Pago"]=="CAÍDA").sum())
    com = pd.to_numeric(df["COMISION"], errors="coerce").fillna(0).sum()
    return t, p, c, com, (p/t*100) if t>0 else 0

def ranking_departamentos_df(df):
    """
    Ranking gerencial por departamento.
    Mantiene la lógica original:
    - Total = cantidad de registros DEVELZ filtrados
    - Pagadas = Estado Pago == PAGADA
    - Caidas = Estado Pago == CAÍDA
    - Comisión = suma de COMISION
    """
    cols = ["Rank", "Departamento", "Total", "Pagadas", "Caidas", "Comision", "% Participación", "% Efectividad"]

    if df.empty or "Departamento" not in df.columns: return pd.DataFrame(columns=cols)

    base = df.copy()
    base["Departamento"] = base["Departamento"].fillna("Sin Departamento").astype(str).str.strip()
    base.loc[base["Departamento"].eq(""), "Departamento"] = "Sin Departamento"
    base["COMISION"] = pd.to_numeric(base.get("COMISION", 0), errors="coerce").fillna(0)

    grp = (
        base.groupby("Departamento", dropna=False)
        .agg(
            Total=("Estado Pago", "count"),
            Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
            Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
            Comision=("COMISION", "sum"),
        )
        .reset_index()
    )

    total_ventas = int(grp["Total"].sum())
    total_pagadas = int(grp["Pagadas"].sum())
    total_caidas = int(grp["Caidas"].sum())
    total_comision = float(pd.to_numeric(grp["Comision"], errors="coerce").fillna(0).sum())

    grp["% Participación"] = (grp["Pagadas"] / total_pagadas * 100).round(2) if total_pagadas > 0 else 0.0
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).fillna(0)

    grp = grp.sort_values(["Pagadas", "Comision", "Total"], ascending=[False, False, False]).reset_index(drop=True)
    grp.insert(0, "Rank", grp.index + 1)

    total_row = pd.DataFrame([{
        "Rank": "TOTAL",
        "Departamento": "",
        "Total": total_ventas,
        "Pagadas": total_pagadas,
        "Caidas": total_caidas,
        "Comision": total_comision,
        "% Participación": 100.00 if total_pagadas > 0 else 0.00,
        "% Efectividad": round((total_pagadas / total_ventas * 100), 2) if total_ventas > 0 else 0.00,
    }])

    return pd.concat([grp[cols], total_row[cols]], ignore_index=True)

def mostrar_ranking_departamentos_premium(df):
    rank_dpto = ranking_departamentos_df(df)

    if rank_dpto.empty:
        st.warning("No se encontró columna de departamento.")
        return

    base = rank_dpto[rank_dpto["Rank"].astype(str) != "TOTAL"].copy()
    total = rank_dpto[rank_dpto["Rank"].astype(str) == "TOTAL"].copy()

    total_departamentos = int(base["Departamento"].nunique()) if not base.empty else 0
    total_ventas = int(total["Total"].iloc[0]) if not total.empty else int(base["Total"].sum())
    total_pagadas = int(total["Pagadas"].iloc[0]) if not total.empty else int(base["Pagadas"].sum())
    total_caidas = int(total["Caidas"].iloc[0]) if not total.empty else int(base["Caidas"].sum())
    total_comision = float(total["Comision"].iloc[0]) if not total.empty else float(pd.to_numeric(base["Comision"], errors="coerce").fillna(0).sum())
    efectividad = (total_pagadas / total_ventas * 100) if total_ventas > 0 else 0

    # KPI territorial: Lima vs Provincia.
    # Se calcula sobre el total de ventas de cada departamento dentro de la base filtrada.
    if not base.empty and "Departamento" in base.columns:
        dep_norm = (
            base["Departamento"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
            .str.replace("Á", "A", regex=False)
            .str.replace("É", "E", regex=False)
            .str.replace("Í", "I", regex=False)
            .str.replace("Ó", "O", regex=False)
            .str.replace("Ú", "U", regex=False)
        )
        mask_lima = dep_norm.str.contains("LIMA", na=False)
        lima_total = int(pd.to_numeric(base.loc[mask_lima, "Total"], errors="coerce").fillna(0).sum())
        provincia_total = int(pd.to_numeric(base.loc[~mask_lima, "Total"], errors="coerce").fillna(0).sum())
    else:
        lima_total = 0
        provincia_total = 0

    lima_pct = (lima_total / total_ventas * 100) if total_ventas > 0 else 0
    provincia_pct = (provincia_total / total_ventas * 100) if total_ventas > 0 else 0

    st.markdown("""
    <style>
        .dpto-premium-wrap{
            background:linear-gradient(135deg, rgba(255,255,255,.98), rgba(239,246,255,.96));
            border:1px solid rgba(15,66,135,.16);
            border-radius:26px;
            padding:24px 24px 18px 24px;
            box-shadow:0 18px 50px rgba(15,66,135,.13);
            margin-bottom:18px;
        }
        .dpto-kpi-card{
            background:white;
            border-radius:22px;
            padding:18px 14px;
            text-align:center;
            border:1px solid rgba(15,66,135,.16);
            box-shadow:0 10px 28px rgba(0,0,0,.08);
            min-height:112px;
        }
        .dpto-kpi-label{
            font-size:11px;
            font-weight:900;
            color:#64748b;
            letter-spacing:.08em;
            text-transform:uppercase;
            margin-bottom:8px;
        }
        .dpto-kpi-value{
            font-size:30px;
            font-weight:950;
            color:#0f4287;
            line-height:1.05;
        }
        .dpto-kpi-sub{
            font-size:11px;
            font-weight:700;
            color:#94a3b8;
            margin-top:6px;
        }
    </style>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Departamentos</div><div class="dpto-kpi-value">{total_departamentos:,}</div><div class="dpto-kpi-sub">zonas con gestión</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Lima</div><div class="dpto-kpi-value" style="color:#0f4287;">{lima_total:,}</div><div class="dpto-kpi-sub">{lima_pct:.2f}% del total</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Provincia</div><div class="dpto-kpi-value" style="color:#7c3aed;">{provincia_total:,}</div><div class="dpto-kpi-sub">{provincia_pct:.2f}% del total</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Efectividad</div><div class="dpto-kpi-value">{efectividad:.2f}%</div><div class="dpto-kpi-sub">pagadas / total</div></div>', unsafe_allow_html=True)

    st.write("")

    if not base.empty:
        top = base.head(10).copy()
        try:
            import altair as alt
            chart_data = top[["Departamento", "Pagadas", "Caidas"]].melt(
                "Departamento",
                var_name="Estado",
                value_name="Cantidad"
            )
            chart = (
                alt.Chart(chart_data)
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Cantidad:Q", title="Ventas"),
                    y=alt.Y("Departamento:N", sort="-x", title=""),
                    color=alt.Color(
                        "Estado:N",
                        scale=alt.Scale(domain=["Pagadas", "Caidas"], range=["#059669", "#dc2626"]),
                        legend=alt.Legend(title="Estado")
                    ),
                    tooltip=["Departamento", "Estado", "Cantidad"]
                )
                .properties(height=max(260, len(top) * 42), title="Top departamentos por ventas pagadas y caídas")
                .configure_axis(labelFontSize=12, titleFontSize=13)
                .configure_title(fontSize=18, fontWeight="bold", color="#0f4287")
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.info("No se pudo renderizar el gráfico, pero la tabla gerencial está disponible abajo.")

    tabla = rank_dpto.copy()
    tabla["Comision"] = tabla["Comision"].apply(lambda x: formatear_moneda(x) if isinstance(x, (int, float)) else x)
    tabla["% Participación"] = tabla["% Participación"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)
    tabla["% Efectividad"] = tabla["% Efectividad"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)

    st.markdown("#### Tabla gerencial por departamento")

    # IMPORTANTE:
    # No usamos Styler.background_gradient porque requiere matplotlib.
    # Estos estilos son manuales y funcionan sin instalar paquetes adicionales.
    def _color_pagadas(val):
        try:
            v = float(val)
            max_v = float(pd.to_numeric(tabla["Pagadas"], errors="coerce").fillna(0).max())
            intensidad = 0 if max_v == 0 else min(v / max_v, 1)
            alpha = 0.10 + (intensidad * 0.28)
            return f"background-color: rgba(5,150,105,{alpha}); color:#064e3b; font-weight:800; text-align:center;"
        except Exception:
            return "text-align:center;"

    def _color_caidas(val):
        try:
            v = float(val)
            max_v = float(pd.to_numeric(tabla["Caidas"], errors="coerce").fillna(0).max())
            intensidad = 0 if max_v == 0 else min(v / max_v, 1)
            alpha = 0.08 + (intensidad * 0.24)
            return f"background-color: rgba(220,38,38,{alpha}); color:#7f1d1d; font-weight:800; text-align:center;"
        except Exception:
            return "text-align:center;"

    def _resaltar_total(row):
        if str(row.get("Rank", "")).upper() == "TOTAL": return ["background-color:#0f4287; color:white; font-weight:900;" for _ in row]
        return ["" for _ in row]

    st.dataframe(
        tabla.style
        .apply(_resaltar_total, axis=1)
        .map(_color_pagadas, subset=["Pagadas"])
        .map(_color_caidas, subset=["Caidas"])
        .set_properties(**{"text-align": "center", "font-size": "13px"})
        .set_properties(subset=["Departamento"], **{"text-align": "left", "font-weight": "bold"}),
        use_container_width=True,
        height=min(650, 90 + 36 * len(tabla))
    )

    st.download_button(
        "⬇️ Descargar Ranking Departamentos",
        data=rank_dpto.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="ranking_departamentos_develz.csv",
        mime="text/csv",
        key="dl_ranking_departamentos_premium",
        on_click=registrar_descarga,
        args=("Ranking Departamentos", "ranking_departamentos_develz.csv", "Vista premium gerencial")
    )

def ranking_asesores_detalle(df):
    if df.empty or "SUPERVISOR" not in df.columns: return pd.DataFrame()
    grp = df.groupby("SUPERVISOR").agg(
        Total=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
        Comision=("COMISION", lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum()),
    ).reset_index().sort_values(["Comision","Total"], ascending=[False,False]).reset_index(drop=True)
    grp.insert(0,"Rank", grp.index + 1)
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).astype(str) + "%"
    total_row = pd.DataFrame([{"Rank":"TOTAL","SUPERVISOR":"","Total":grp["Total"].sum(),
        "Pagadas":grp["Pagadas"].sum(),"Caidas":grp["Caidas"].sum(),
        "% Efectividad":"","Comision":grp["Comision"].sum()}])
    return pd.concat([grp, total_row], ignore_index=True)

def ranking_asesores_por_supervisor_df(df, supervisor):
    cols = ["Rank","ASESOR","Total","Pagadas","Caidas","Comision","% Efectividad"]
    if df.empty: return pd.DataFrame(columns=cols)
    base = df.copy()
    if "SUPERVISOR" not in base.columns:
        base["SUPERVISOR"] = "Sin Supervisor"
    if "ASESOR" not in base.columns:
        base["ASESOR"] = "Sin Asesor"
    base["SUPERVISOR"] = base["SUPERVISOR"].fillna("Sin Supervisor").astype(str).str.strip().replace("", "Sin Supervisor")
    base["ASESOR"] = base["ASESOR"].fillna("Sin Asesor").astype(str).str.strip().replace("", "Sin Asesor")
    base["COMISION"] = pd.to_numeric(base.get("COMISION", 0), errors="coerce").fillna(0)
    base = base[base["SUPERVISOR"] == supervisor].copy()
    if base.empty: return pd.DataFrame(columns=cols)
    grp = base.groupby("ASESOR", dropna=False).agg(
        Total=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
        Comision=("COMISION","sum"),
    ).reset_index().sort_values(["Comision","Pagadas","Total"], ascending=[False,False,False]).reset_index(drop=True)
    grp.insert(0, "Rank", grp.index + 1)
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).astype(str) + "%"
    total = pd.DataFrame([{"Rank":"TOTAL","ASESOR":"","Total":int(grp["Total"].sum()),
        "Pagadas":int(grp["Pagadas"].sum()),"Caidas":int(grp["Caidas"].sum()),
        "Comision":float(grp["Comision"].sum()),"% Efectividad":""}])
    return pd.concat([grp[cols], total[cols]], ignore_index=True)

def mostrar_ranking_supervisores_con_asesores(df):
    rank_df = ranking_asesores_detalle(df)
    if rank_df.empty:
        st.warning("Sin datos para el ranking.")
        return

    rank_sin_total = rank_df[rank_df["Rank"].astype(str) != "TOTAL"].copy()
    total_row = rank_df[rank_df["Rank"].astype(str) == "TOTAL"].copy()

    st.caption("Haz clic en el ➕ de cada supervisor para ver el detalle de asesores.")

    for _, row in rank_sin_total.iterrows():
        supervisor = str(row.get("SUPERVISOR", "Sin Supervisor")).strip() or "Sin Supervisor"
        etiqueta = (
            f"➕ {row['Rank']} | {supervisor} | "
            f"Total: {int(row['Total']):,} | Pagadas: {int(row['Pagadas']):,} | "
            f"Caídas: {int(row['Caidas']):,} | Comisión: {formatear_moneda(row['Comision'])} | "
            f"Efectividad: {row['% Efectividad']}"
        )
        with st.expander(etiqueta, expanded=False):
            detalle_asesor = ranking_asesores_por_supervisor_df(df, supervisor)
            if detalle_asesor.empty:
                st.info("Este supervisor no tiene asesores asociados con los filtros actuales.")
            else:
                st.dataframe(
                    detalle_asesor.style.format({"Comision": lambda x: formatear_moneda(x) if isinstance(x, (int, float)) else x})
                    .set_properties(**{"text-align":"center"})
                    .set_properties(subset=["ASESOR"], **{"text-align":"left"}),
                    use_container_width=True,
                    height=min(420, 80 + 36 * len(detalle_asesor))
                )

    if not total_row.empty:
        st.markdown("##### Total general")
        st.table(total_row.style
            .format({"Comision": lambda x: formatear_moneda(x) if isinstance(x,(int,float)) else x})
            .set_properties(**{"text-align":"center"})
            .set_properties(subset=["SUPERVISOR"], **{"text-align":"left"}))

def ranking_asesores_fija_develz(df):
    cols = ["Rank","ASESOR","Total","Pagadas","Caidas","% Efectividad","Comision"]
    if df.empty or "ASESOR" not in df.columns: return pd.DataFrame(columns=cols)
    base = df.copy()
    base["ASESOR"] = base["ASESOR"].fillna("Sin Asesor").astype(str).str.strip().replace("","Sin Asesor")
    base["COMISION"] = pd.to_numeric(base.get("COMISION",0), errors="coerce").fillna(0)
    grp = base.groupby("ASESOR", dropna=False).agg(
        Total=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
        Comision=("COMISION","sum"),
    ).reset_index().sort_values(["Comision","Pagadas","Total"], ascending=[False,False,False]).reset_index(drop=True)
    grp.insert(0,"Rank", grp.index + 1)
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).astype(str) + "%"
    total = pd.DataFrame([{"Rank":"TOTAL","ASESOR":"","Total":int(grp["Total"].sum()),
        "Pagadas":int(grp["Pagadas"].sum()),"Caidas":int(grp["Caidas"].sum()),
        "% Efectividad":"","Comision":float(grp["Comision"].sum())}])
    return pd.concat([grp[cols], total[cols]], ignore_index=True)

def mostrar_iae_asesor_fija_develz(tabla_maestro, tabla_claro, canal, filtro_mes, key_asesor, color):
    df_det = construir_detalle_fija_develz(tabla_maestro, tabla_claro, canal, filtro_mes)
    if df_det.empty: st.warning("Sin datos."); return

    for campo, defecto in [("ASESOR","Sin Asesor"),("SUPERVISOR","Sin Supervisor"),("TIPIS","Sin TIPIS")]:
        if campo not in df_det.columns: df_det[campo] = defecto
        df_det[campo] = df_det[campo].fillna(defecto).astype(str).str.strip()
        df_det.loc[df_det[campo].eq(""), campo] = defecto

    f1, f2, f3 = st.columns(3)
    with f1: filtro_a  = st.selectbox("Asesor / Creador", ["Todos"] + sorted(df_det["ASESOR"].unique().tolist()), key=key_asesor)
    with f2: filtro_su = st.selectbox("Supervisor",       ["Todos"] + sorted(df_det["SUPERVISOR"].unique().tolist()), key=f"{key_asesor}_supervisor")
    with f3: filtro_ti = st.selectbox("Tipificación",     ["Todos"] + sorted(df_det["TIPIS"].unique().tolist()), key=f"{key_asesor}_tipificacion")

    df_f = df_det.copy()
    if filtro_a  != "Todos": df_f = df_f[df_f["ASESOR"]      == filtro_a]
    if filtro_su != "Todos": df_f = df_f[df_f["SUPERVISOR"]   == filtro_su]
    if filtro_ti != "Todos": df_f = df_f[df_f["TIPIS"]        == filtro_ti]

    total, pagadas, caidas, comision, pct = kpi_detalle_fija(df_f)
    color_borde = "#0f4287" if color == "dc" else "#70008f"

    def _card(col, label, valor, sub=""):
        with col:
            st.markdown(
                f'<div style="background:rgba(255,255,255,.95);padding:14px;border-radius:16px;'
                f'border:2px solid {color_borde};text-align:center;margin-bottom:8px;min-height:86px;">'
                f'<span style="color:#4b5563;font-weight:800;font-size:10px;text-transform:uppercase;display:block;">{label}</span>'
                f'<span style="color:{color_borde};font-size:24px;font-weight:900;display:block;line-height:1.1;">{valor}</span>'
                f'<span style="color:#6b7280;font-size:10px;">{sub}</span></div>', unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import base64
import os
from io import BytesIO

st.set_page_config(page_title="Dashboard Teletalk Digital", layout="wide", initial_sidebar_state="expanded")

def set_bg(img_file):
    bg = _leer_img_b64(img_file)
    if not bg:
        st.sidebar.warning(f"Imagen no encontrada: {img_file}")
    st.markdown(f"""<style>
        .stApp {{ {bg} background-size:cover; background-position:center; background-attachment:fixed; }}
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

DATA_DIR = "."
MESES_ES = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
            7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
MESES_MAP = {v.lower(): k for k, v in MESES_ES.items()}

CSV_MAP = {
    "dbo.CLARO_DC_FIJA":              "CLARO_DC_FIJA.csv",
    "dbo.CLARO_DC_FIJA_SEGUNDA_CAIDA": "CLARO_DC_FIJA_SEGUNDA_CAIDA.csv",
    "dbo.CLARO_TELETALK_FIJA":        "CLARO_TELETALK_FIJA.csv",
    "dbo.CLARO_DC_MOVIL":             "CLARO_DC_MOVIL.csv",
    "dbo.CLARO_TELETALK_MOVIL":       "CLARO_TELETALK_MOVIL.csv",
    "[DATA DEVELZ].dbo.FIJA_DC":      "FIJA_DC.csv",
    "[DATA DEVELZ].dbo.FIJA_TELETALK":"FIJA_TELETALK.csv",
}

TIPIS_ESTADO_MAP = {
    "ATENDIDA/CONFORME":"Conforme","CONFORME PODIO":"Conforme","ATENDIDA - REASIGNACION":"Conforme",
    "CONFORME":"Conforme","ATENDIDA/OBSERVADO":"Conforme","AUDIO LOTEADO":"Conforme",
    "CONFORME - REASIGNACION":"Conforme","AUDIO KO":"1era Caída","SOT CON OTRO DAC":"1era Caída",
    "SEC SIN CORRECCIÓN":"1era Caída","SEC SIN CORRECCION":"1era Caída","OTROS":"1era Caída",
    "EDIFICIO NO LIBERADO PC":"1era Caída","SIN COBERTURA PC":"1era Caída","FICHA DUPLICADA":"1era Caída",
    "SEC CON EXCLUSIVIDAD":"1era Caída","NO ADJUNTA SUSTENTO":"1era Caída","NO ENVIA SUSTENTO":"1era Caída",
    "VENTA CARRUSEL":"1era Caída","DIRECCIÓN CON SERVICIO DE BAJA":"1era Caída",
    "DIRECCION CON SERVICIO DE BAJA":"1era Caída","FACILIDADES TECNICAS":"2da Caída",
    "CLIENTE NO DESEA":"2da Caída","FALTA CONTACTO":"2da Caída","CLIENTE NO CALIFICA":"2da Caída",
    "PRUEBA - CANCELADA":"2da Caída","DIRECCION INCORRECTA":"2da Caída","DIRECCIÓN INCORRECTA":"2da Caída",
    "MALA OFERTA":"2da Caída","RED SATURADA":"2da Caída","FRAUDE":"2da Caída","VIAJE O MUDANZA":"2da Caída",
    "CONTRA OFERTA":"2da Caída","FALTA INFRAESTRUCTURA":"2da Caída","EDIFICIO NO LIBERADO":"2da Caída",
    "EJECUCION - AUDIO LOTEADO":"Ejecución","EJECUCION - AUDIO CONFORME":"Ejecución",
    "PENDIENTE AUDIO OK":"Ejecución","EJECUCION":"Ejecución","EJECUCION - SIN AUDIO":"Ejecución",
    "PENDIENTE SOT":"Ejecución","PENDIENTE AUDIO KO":"Ejecución","EJECUCION - AUDIO OBSERVADO":"Ejecución",
    "PENDIENTE PRE - AUDITORIA":"Ejecución","EJECUCION - REASIGNACION":"Ejecución",
    "EJECUCION - AUDITADO":"Ejecución",
}

ruta_base    = "."
img_caratula_png = os.path.join(ruta_base, "caratula.png")
img_caratula_jpg = os.path.join(ruta_base, "caratula.png.jpg")
img_caratula = img_caratula_png if os.path.exists(img_caratula_png) else img_caratula_jpg
img_dc       = os.path.join(ruta_base, "34bab75f-2b2e-455e-8935-377abf566b76.jpg")
img_tt       = os.path.join(ruta_base, "ab3ac40e-1612-430f-bb3a-817d24b709db.jpg")

# ─────────────────────────────────────────────────────────────────────────
# DVZ.csv unificado: reemplaza a FIJA_DC.csv, FIJA_TELETALK.csv,
# MOVIL_DC.csv y MOVIL_TELETALK.csv. Se identifica:
#   - FIJA vs MOVIL  -> columna "Tipo Producto" (valores "FIJA" / "MOVIL")
#   - D&C vs Teletalk -> columna "Datos Adicionales - Clip" (valores "D&C" / "TELETALK")
# Si DVZ.csv no existe, se conserva el comportamiento original (4 archivos sueltos).
# ─────────────────────────────────────────────────────────────────────────
_DVZ_SPLIT_MAP = {
    "FIJA_DC.csv":       ("FIJA",  "D&C"),
    "FIJA_TELETALK.csv": ("FIJA",  "TELETALK"),
    "MOVIL_DC.csv":      ("MOVIL", "D&C"),
    "MOVIL_TELETALK.csv":("MOVIL", "TELETALK"),
}

@st.cache_data(ttl=600)
def _leer_dvz_crudo():
    ruta = os.path.join(DATA_DIR, "DVZ.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    for enc in ["latin-1","utf-8-sig","utf-8","cp1252","iso-8859-1"]:
        for sep in [";",",","\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, on_bad_lines="skip", engine="python")
                df.columns = df.columns.str.strip()
                if len(df.columns) > 1: return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
    return pd.DataFrame()

@st.cache_data(ttl=600)
def _cargar_dvz_filtrado(nombre):
    tipo_prod, canal_clip = _DVZ_SPLIT_MAP[nombre]
    df = _leer_dvz_crudo()
    if df.empty:
        return df
    col_tipo = next((c for c in df.columns if c.strip().lower() == "tipo producto"), None)
    col_clip = next((c for c in df.columns if c.strip().lower() == "datos adicionales - clip"), None)
    if not col_tipo or not col_clip:
        return pd.DataFrame()
    mask_tipo = df[col_tipo].fillna("").astype(str).str.strip().str.upper() == tipo_prod
    mask_clip = df[col_clip].fillna("").astype(str).str.strip().str.upper() == canal_clip
    return df[mask_tipo & mask_clip].copy()

@st.cache_data(ttl=600)
def cargar_csv(nombre):
    # Interceptar los 4 archivos antiguos -> leer desde DVZ.csv si existe
    if nombre in _DVZ_SPLIT_MAP and os.path.exists(os.path.join(DATA_DIR, "DVZ.csv")):
        df_dvz = _cargar_dvz_filtrado(nombre)
        if not df_dvz.empty:
            return df_dvz
    ruta = os.path.join(DATA_DIR, nombre)
    for enc in ["latin-1","utf-8-sig","utf-8","cp1252","iso-8859-1"]:
        for sep in [";",",","\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, on_bad_lines="skip", engine="python")
                df.columns = df.columns.str.strip()
                if len(df.columns) > 1: return df
            except FileNotFoundError:
                st.warning(f"Archivo no encontrado: {ruta}")
                return pd.DataFrame()
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
    st.error(f"No se pudo leer {nombre}")
    return pd.DataFrame()

def get_tabla(nombre):
    return cargar_csv(CSV_MAP.get(nombre, nombre.split(".")[-1] + ".csv"))

# =========================================================
# DOTACIÓN — cruce para columna COLA
# =========================================================
@st.cache_data(ttl=600)
def cargar_dotacion():
    """
    Carga DOTACION.csv y retorna un dict {USUARIO_NORM: SEGMENTO}.
    La columna de usuario en DOTACION se llama USUARIO.
    El segmento (COLA) viene de la columna SEGMENTO.
    Los valores se normalizan a str.upper().strip() para el cruce.
    """
    df = cargar_csv("DOTACION.csv")
    if df.empty:
        return {}
    col_usuario = next((c for c in df.columns if c.strip().upper() == "USUARIO"), None)
    col_segmento = next((c for c in df.columns if c.strip().upper() == "SEGMENTO"), None)
    if not col_usuario or not col_segmento:
        return {}
    df = df.copy()
    # Normaliza la clave: quita sufijo ".0" (cuando pandas lee la extensión como float) y espacios.
    df["_KEY"] = df[col_usuario].fillna("").astype(str).str.upper().str.strip().str.replace(r"\.0$", "", regex=True)
    df["_SEG"] = df[col_segmento].fillna("EXTERNO").astype(str).str.strip()
    df = df[df["_KEY"] != ""]
    return dict(zip(df["_KEY"], df["_SEG"]))

def _agregar_cola_por_extension(df, col_extension):
    """
    Dado un DataFrame y la columna que contiene la extensión/usuario del asesor,
    retorna una Serie con la COLA (SEGMENTO de DOTACION).
    Los que no cruzan quedan como 'EXTERNO'.
    """
    dotacion_map = cargar_dotacion()
    if not dotacion_map or col_extension not in df.columns:
        return pd.Series(["EXTERNO"] * len(df), index=df.index)
    # Misma normalización que la clave de DOTACION para que el BUSCARV cruce bien.
    keys = df[col_extension].fillna("").astype(str).str.upper().str.strip().str.replace(r"\.0$", "", regex=True)
    return keys.map(dotacion_map).fillna("EXTERNO")

def preparar_fechas_fija(df):
    for col in ["FECHA INSTALACION", "FECHA GENERACION", "FECHA DE VENTA"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df

def preparar_fechas_movil(df):
    for col in ["FECHA OPERACION", "FECHA CARGA", "FECHA DE VENTA", "FECHA VENTA", "Fecha de Venta", "Fecha Venta"]:
        if col not in df.columns: continue
        serie = df[col].astype(str).str.strip()
        es_iso = serie.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
        es_lat = serie.str.match(r"^\d{1,2}/\d{1,2}/\d{4}$", na=False)
        fechas = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        if es_iso.any(): fechas.loc[es_iso] = pd.to_datetime(serie.loc[es_iso], format="%Y-%m-%d", errors="coerce")
        if es_lat.any(): fechas.loc[es_lat] = pd.to_datetime(serie.loc[es_lat], dayfirst=True, errors="coerce")
        otros = ~(es_iso | es_lat)
        if otros.any(): fechas.loc[otros] = pd.to_datetime(serie.loc[otros], errors="coerce", dayfirst=True)
        df[col] = fechas
    return df

def encontrar_columna(df, posibles):
    return next((n for n in posibles if n in df.columns), None)

def obtener_comision_fija(df):
    col = encontrar_columna(df, ["COMISION","COMISIÓN","Comision","Comisión","comision","comisión","COMIS","MONTO"])
    return pd.to_numeric(df[col], errors="coerce").fillna(0) if col else pd.Series([0.0]*len(df))

def obtener_comision_movil(df):
    col = encontrar_columna(df, ["COMISION TOTAL","COMISIÓN TOTAL","Comision Total","COMISION","MONTO"])
    return pd.to_numeric(df[col], errors="coerce").fillna(0) if col else pd.Series([0.0]*len(df))

def formatear_moneda(v):
    try: return f"S/ {float(v):,.2f}"
    except: return "S/ 0.00"

# =========================================================
# AUDITORÍA DE DESCARGAS
# =========================================================
def registrar_descarga(seccion, archivo, filtros=""):
    try:
        from datetime import datetime
        log_file = os.path.join(DATA_DIR, "log_descargas.csv")
        nuevo = pd.DataFrame([{"fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": st.session_state.get("usuario_logueado","Sin usuario"),
            "seccion": seccion, "archivo": archivo, "filtros": filtros, "accion": "DESCARGA"}])
        final = pd.concat([pd.read_csv(log_file, encoding="utf-8-sig"), nuevo], ignore_index=True) if os.path.exists(log_file) else nuevo
        final.to_csv(log_file, index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"Error registrando descarga: {e}")

def mostrar_auditoria_descargas():
    set_bg(img_caratula)
    st.markdown('<div class="section-title-dc">Auditoria de Descargas</div>', unsafe_allow_html=True)
    st.write("---")
    if st.session_state.get("usuario_logueado","") != "Fiorella":
        st.error("Acceso restringido."); return
    log_file = os.path.join(DATA_DIR, "log_descargas.csv")
    if not os.path.exists(log_file): st.info("No hay descargas registradas."); return
    df_log = pd.read_csv(log_file, encoding="utf-8-sig")
    if df_log.empty: st.info("No hay descargas registradas."); return
    df_log["fecha_hora"] = pd.to_datetime(df_log["fecha_hora"], errors="coerce")
    df_log = df_log.sort_values("fecha_hora", ascending=False)
    ult = df_log["fecha_hora"].max().strftime("%d/%m/%Y %H:%M:%S") if df_log["fecha_hora"].notna().any() else "Sin fecha"
    c1,c2,c3 = st.columns(3)
    _kpi_card_html(c1,"Total Descargas",f"{len(df_log):,}","Historico","#0f4287","#0f4287")
    _kpi_card_html(c2,"Usuarios",f"{df_log['usuario'].nunique() if 'usuario' in df_log.columns else 0:,}","Con actividad","#0f4287","#0f4287")
    _kpi_card_html(c3,"Ultima Descarga",ult,"Mas reciente","#0f4287","#0f4287")
    st.write("---")
    f1,f2 = st.columns(2)
    with f1: filtro_usuario = st.selectbox("Usuario", (["Todos"]+sorted(df_log["usuario"].dropna().astype(str).unique().tolist())) if "usuario" in df_log.columns else ["Todos"], key="audit_usuario")
    with f2: filtro_seccion = st.selectbox("Seccion",  (["Todas"]+sorted(df_log["seccion"].dropna().astype(str).unique().tolist())) if "seccion"  in df_log.columns else ["Todas"], key="audit_seccion")
    df_show = df_log.copy()
    if filtro_usuario != "Todos" and "usuario" in df_show.columns: df_show = df_show[df_show["usuario"].astype(str)==filtro_usuario]
    if filtro_seccion != "Todas" and "seccion"  in df_show.columns: df_show = df_show[df_show["seccion"].astype(str)==filtro_seccion]
    df_show["fecha_hora"] = df_show["fecha_hora"].dt.strftime("%d/%m/%Y %H:%M:%S")
    st.dataframe(df_show, use_container_width=True, height=480)
    st.download_button("Descargar historial", data=df_log.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="auditoria_descargas.csv", mime="text/csv", key="dl_auditoria_descargas")

def parse_mes_anio(txt):
    if not txt or txt == "Todos los meses": return None, None
    p = txt.strip().lower().split()
    if len(p) == 2 and p[0] in MESES_MAP and p[1].isdigit(): return MESES_MAP[p[0]], int(p[1])
    return None, None

def filtrar_por_mes_anio(df, col, txt):
    m, y = parse_mes_anio(txt)
    if m and y and col in df.columns: return df[(df[col].dt.month == m) & (df[col].dt.year == y)].copy()
    return df.copy()

def porta_si(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False).isin(['SI','YES','Y'])

def _es_portabilidad_movil(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False) == "PORTABILIDAD"

def _es_alta_movil(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False).isin(["ALTA NUEVA","ALTA"])

@st.cache_data(ttl=3600)
def obtener_meses_fija(col):
    meses = set()
    for nombre in ["CLARO_DC_FIJA.csv","CLARO_TELETALK_FIJA.csv"]:
        df = preparar_fechas_fija(cargar_csv(nombre))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].capitalize()} {f.year}" for f in df[col].dropna())
    return (["Todos los meses"] +
            sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))))

@st.cache_data(ttl=3600)
def obtener_meses_fija_develz(col):
    meses = set()
    for nombre in ["FIJA_DC.csv", "FIJA_TELETALK.csv"]:
        df = preparar_fechas_fija(cargar_csv(nombre))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].capitalize()} {f.year}" for f in df[col].dropna())
    return (["Todos los meses"] +
            sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))))

@st.cache_data(ttl=3600)
def obtener_meses_movil(col, archivos):
    meses = set()
    for a in archivos:
        df = preparar_fechas_movil(cargar_csv(a))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].lower()} {f.year}".capitalize()
                         for f in df[df[col].notna()][col])
    return (["Todos los meses"] +
            sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))))

@st.cache_data(ttl=3600)
def obtener_metricas_fija(tabla, f_inst, f_gene):
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return 0, 0.0
        if f_inst != "Todos los meses": df = filtrar_por_mes_anio(df, "FECHA INSTALACION", f_inst)
        if f_gene != "Todos los meses": df = filtrar_por_mes_anio(df, "FECHA GENERACION", f_gene)
        return int(df["SOT"].nunique() if "SOT" in df.columns else 0), float(obtener_comision_fija(df).sum())
    except: return 0, 0.0

@st.cache_data(ttl=3600)
def obtener_reporte_liquidado(ventas_tabla, maestro_tabla, fecha_inst):
    cols = ["SOT","ASESOR","Nombre del Cliente","COMISION","COMISIONES","¿Pagado?"]
    try:
        df_v = preparar_fechas_fija(get_tabla(ventas_tabla))
        df_m = get_tabla(maestro_tabla)
        if df_v.empty: return pd.DataFrame(columns=cols)
        df_v = filtrar_por_mes_anio(df_v, "FECHA INSTALACION", fecha_inst)
        df_v["SOT"] = df_v["SOT"].astype(str).str.strip()
        if not df_m.empty and "Back Office - Sot" in df_m.columns:
            df_m["Back Office - Sot"] = df_m["Back Office - Sot"].astype(str).str.strip()
            df = df_v.merge(df_m, left_on="SOT", right_on="Back Office - Sot", how="left")
        else:
            df = df_v.copy()
        df["ASESOR"] = df.get("USUARIO", pd.Series([""] * len(df))).replace("", pd.NA).fillna("Sin Asesor")
        nom = df.get("Cliente - Nombre", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
        ape = df.get("Cliente - Apellido Paterno", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
        df["Nombre del Cliente"] = (nom + " " + ape).str.strip().replace("", "Sin Datos").fillna("Sin Datos")
        df["COMISION"] = obtener_comision_fija(df)
        df["¿Pagado?"] = df["COMISION"].apply(lambda x: "SÍ" if x > 0 else "NO")
        return df[cols]
    except Exception as e:
        st.error(f"Error reporte liquidado: {e}")
        return pd.DataFrame(columns=cols)

def _base_factor_fija(df, col_fecha):
    df["COMISION"] = obtener_comision_fija(df)
    df["_porta"] = porta_si(df.get("PORTABILIDAD", pd.Series([""] * len(df))).fillna("").astype(str))
    srv = df.get("SERVICIO", pd.Series([""] * len(df))).fillna("").astype(str).str.upper()
    tip = df.get("TIPO TRABAJO", pd.Series([""] * len(df))).fillna("").astype(str).str.upper()
    df["_ftth"] = srv.str.contains("FTTH") | tip.str.contains("FTTH")
    df["_hfc"]  = srv.str.contains("HFC")  | tip.str.contains("HFC")
    df["_anio"] = df[col_fecha].dt.year
    df["_mes"]  = df[col_fecha].dt.month
    return df

@st.cache_data(ttl=3600)
def obtener_factor_fija_resumen(tabla, col_fecha, filtro):
    cols = ["Año","Mes","Ventas","PORTABILIDAD SI","PORTABILIDAD NO","FTTH","HFC","S/."]
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        df = _base_factor_fija(df, col_fecha)
        ds = df.drop_duplicates(subset=["SOT","_anio","_mes"])
        grp = ds.groupby(["_anio","_mes"]).agg(
            Ventas=("SOT","nunique"), **{"PORTABILIDAD SI":("_porta","sum")},
            **{"PORTABILIDAD NO":("_porta", lambda x: (~x).sum())},
            FTTH=("_ftth","sum"), HFC=("_hfc","sum"),
        ).reset_index()
        com = df.groupby(["_anio","_mes"])["COMISION"].sum().reset_index()
        com.columns = ["_anio","_mes","S/."]
        grp = grp.merge(com, on=["_anio","_mes"], how="left")
        grp.columns = ["Año","MesNum","Ventas","PORTABILIDAD SI","PORTABILIDAD NO","FTTH","HFC","S/."]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        return grp.sort_values(["Año","MesNum"])[cols]
    except Exception as e:
        st.error(f"Error factor fija resumen: {e}")
        return pd.DataFrame(columns=cols)

@st.cache_data(ttl=3600)
def obtener_factor_fija_detallado(tabla, col_fecha, filtro):
    cols = ["Año","Mes","MesNum","Dia","Ventas","Porta_SI","Porta_NO","FTTH","HFC","Monto"]
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        df = _base_factor_fija(df, col_fecha)
        df["_dia"] = df[col_fecha].dt.day
        ds = df.drop_duplicates(subset=["SOT","_anio","_mes","_dia"])
        grp = ds.groupby(["_anio","_mes","_dia"]).agg(
            Ventas=("SOT","nunique"), Porta_SI=("_porta","sum"),
            Porta_NO=("_porta", lambda x: (~x).sum()), FTTH=("_ftth","sum"), HFC=("_hfc","sum"),
        ).reset_index()
        com = df.groupby(["_anio","_mes","_dia"])["COMISION"].sum().reset_index()
        com.columns = ["_anio","_mes","_dia","Monto"]
        grp = grp.merge(com, on=["_anio","_mes","_dia"], how="left")
        grp.columns = ["Año","MesNum","Dia","Ventas","Porta_SI","Porta_NO","FTTH","HFC","Monto"]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        return grp.sort_values(["Año","MesNum","Dia"], ascending=[False,False,True])[cols]
    except Exception as e:
        st.error(f"Error factor fija detallado: {e}")
        return pd.DataFrame(columns=cols)

def _base_factor_movil(df, col_fecha):
    df["_comision"] = obtener_comision_movil(df)
    tr = df.get("TRANSACCION", pd.Series([""] * len(df), index=df.index)).fillna("").astype(str)
    df["_porta"] = _es_portabilidad_movil(tr)
    df["_alta"]  = _es_alta_movil(tr)
    cf   = pd.to_numeric(df.get("CF",   pd.Series([0.0]*len(df), index=df.index)), errors="coerce").fillna(0)
    dias = pd.to_numeric(df.get("DIAS PORTADAS", pd.Series([0.0]*len(df), index=df.index)), errors="coerce").fillna(0)
    df["_cf_mayor"]   = cf > 69.90;   df["_cf_menor"]   = cf <= 69.90
    df["_dias_mayor"] = dias > 90;    df["_dias_menor"]  = dias <= 90
    df["_anio"] = df[col_fecha].dt.year.astype("Int64")
    df["_mes"]  = df[col_fecha].dt.month.astype("Int64")
    return df

@st.cache_data(ttl=3600)
def obtener_factor_movil_resumen(tabla, filtro, col_fecha):
    cols = ["Año","Mes","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","S/."]
    try:
        df = preparar_fechas_movil(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        if df.empty: return pd.DataFrame(columns=cols)
        df = _base_factor_movil(df, col_fecha)
        grp = df.groupby(["_anio","_mes"]).agg(
            Ventas=("TRANSACCION","size"), PORTABILIDAD=("_porta","sum"), ALTA=("_alta","sum"),
            **{"CF>69.90":("_cf_mayor","sum")}, **{"CF<=69.90":("_cf_menor","sum")},
            **{"Dias>90":("_dias_mayor","sum")}, **{"Dias<=90":("_dias_menor","sum")},
            **{"S/.":("_comision","sum")},
        ).reset_index()
        grp.columns = ["Año","MesNum","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","S/."]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        int_cols = ["Año","MesNum","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90"]
        for c in int_cols: grp[c] = pd.to_numeric(grp[c], errors="coerce").fillna(0).astype(int)
        return grp.sort_values(["Año","MesNum"])[cols]
    except Exception as e:
        st.error(f"Error factor móvil resumen: {e}")
        return pd.DataFrame(columns=cols)

@st.cache_data(ttl=3600)
def obtener_factor_movil_detallado(tabla, filtro, col_fecha):
    cols = ["Año","Mes","MesNum","Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","Monto"]
    try:
        df = preparar_fechas_movil(get_tabla(tabla))
        if df.empty: return pd.DataFrame(columns=cols)
        df = filtrar_por_mes_anio(df, col_fecha, filtro)
        if df.empty: return pd.DataFrame(columns=cols)
        df = _base_factor_movil(df, col_fecha)
        df["_dia"] = df[col_fecha].dt.day.astype("Int64")
        grp = df.groupby(["_anio","_mes","_dia"]).agg(
            Ventas=("TRANSACCION","size"), PORTABILIDAD=("_porta","sum"), ALTA=("_alta","sum"),
            **{"CF>69.90":("_cf_mayor","sum")}, **{"CF<=69.90":("_cf_menor","sum")},
            **{"Dias>90":("_dias_mayor","sum")}, **{"Dias<=90":("_dias_menor","sum")},
            Monto=("_comision","sum"),
        ).reset_index()
        grp.columns = ["Año","MesNum","Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","Monto"]
        grp["Mes"] = grp["MesNum"].map(MESES_ES)
        int_cols = ["Año","MesNum","Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90"]
        for c in int_cols: grp[c] = pd.to_numeric(grp[c], errors="coerce").fillna(0).astype(int)
        return grp.sort_values(["Año","MesNum","Dia"], ascending=[False,False,True])[cols]
    except Exception as e:
        st.error(f"Error factor móvil detallado: {e}")
        return pd.DataFrame(columns=cols)

def construir_ranking_asesores(df):
    if df.empty: return pd.DataFrame(columns=["Rank","ASESOR","Cantidad_Ventas","Ventas_Pagadas","Ventas_No_Pagadas","Total_Comision"])
    df = df.copy()
    cn = df["COMISIONES"].astype(str).str.upper().str.replace('Í','I',regex=False).str.strip()
    df["_cn"] = cn
    r = (df.groupby("ASESOR", dropna=False).agg(
        Total_Comision=("COMISION","sum"),
        Ventas_Pagadas=("SOT", lambda x: x[df.loc[x.index,"_cn"] == "SI"].nunique()),
        Ventas_No_Pagadas=("SOT", lambda x: x[df.loc[x.index,"_cn"] == "NO"].nunique()),
    ).reset_index().sort_values("Total_Comision", ascending=False))
    r["Rank"] = r["Total_Comision"].rank(method="dense", ascending=False).astype(int)
    r["Cantidad_Ventas"] = r["Ventas_Pagadas"] + r["Ventas_No_Pagadas"]
    r = r[["Rank","ASESOR","Cantidad_Ventas","Ventas_Pagadas","Ventas_No_Pagadas","Total_Comision"]]
    total = pd.DataFrame([{"Rank":"Total","ASESOR":"","Cantidad_Ventas":r["Cantidad_Ventas"].sum(),
        "Ventas_Pagadas":r["Ventas_Pagadas"].sum(),"Ventas_No_Pagadas":r["Ventas_No_Pagadas"].sum(),
        "Total_Comision":r["Total_Comision"].sum()}])
    return pd.concat([r, total], ignore_index=True)

def mostrar_tabla_ranking(ranking):
    if ranking.empty: st.warning("No se encontraron datos para el ranking."); return
    st.table(ranking.style.format({"Total_Comision":"S/ {:,.2f}"})
        .set_table_attributes('style="width:1000px;table-layout:fixed;background-color:white;"')
        .set_table_styles([
            {"selector":"th","props":[("text-align","center"),("font-size","14px"),("padding","8px"),("background-color","white")]},
            {"selector":"td","props":[("padding","8px"),("font-size","13px"),("white-space","nowrap"),("overflow","hidden"),("text-overflow","ellipsis"),("background-color","white")]},
        ])
        .set_properties(**{"text-align":"center"}, subset=["Rank","Cantidad_Ventas","Ventas_Pagadas","Ventas_No_Pagadas","Total_Comision"])
        .set_properties(**{"text-align":"left"}, subset=["ASESOR"]))

def _style_tabla(color):
    hc = "#0f4287" if color == "dc" else "#70008f"
    return [
        {"selector":"th","props":[("background-color","white"),("color",hc),("font-size","13px"),("text-align","center"),("border-bottom","2px solid #ddd")]},
        {"selector":"td","props":[("padding","10px 8px"),("font-size","13px"),("border-bottom","1px solid #eee"),("background-color","white")]}
    ]

def mostrar_expanders_fija(df_det, color="dc"):
    if df_det.empty: st.warning("No se encontraron datos."); return
    icono = "🔵" if color == "dc" else "🟣"
    for _, p in (df_det[["Año","Mes","MesNum"]].drop_duplicates()
                 .sort_values(["Año","MesNum"], ascending=[False,False])).iterrows():
        dm = df_det[(df_det["Año"] == p["Año"]) & (df_det["Mes"] == p["Mes"])].copy()
        with st.expander(f"{icono} {p['Mes']} {p['Año']}  |  Ventas: {int(dm['Ventas'].sum())}  |  Total: {formatear_moneda(dm['Monto'].sum())}", expanded=False):
            t = dm[["Dia","Ventas","Porta_SI","Porta_NO","FTTH","HFC","Monto"]].copy()
            t["Monto"] = t["Monto"].map(formatear_moneda)
            st.table(t)

def mostrar_expanders_movil(df_det, color="dc"):
    if df_det.empty: st.warning("No se encontraron datos."); return
    icono = "🔵" if color == "dc" else "🟣"
    for _, p in (df_det[["Año","Mes","MesNum"]].drop_duplicates()
                 .sort_values(["Año","MesNum"], ascending=[False,False])).iterrows():
        dm = df_det[(df_det["Año"] == p["Año"]) & (df_det["Mes"] == p["Mes"])].copy()
        with st.expander(f"{icono} {p['Mes']} {p['Año']}  |  Ventas: {int(dm['Ventas'].sum())}  |  Total: {formatear_moneda(dm['Monto'].sum())}", expanded=False):
            t = dm[["Dia","Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","Monto"]].copy()
            t["Monto"] = t["Monto"].map(formatear_moneda)
            st.table(t)

def mostrar_factor_fija(tabla, col_fecha, filtro, color):
    col1, col2 = st.columns([1.1, 1.6])
    with col1:
        st.markdown("### Resumen")
        df_f = obtener_factor_fija_resumen(tabla, col_fecha, filtro)
        if df_f.empty: st.warning("Sin datos.")
        else:
            total = pd.DataFrame([{"Año":"Total","Mes":"","Ventas":df_f["Ventas"].sum(),
                "PORTABILIDAD SI":df_f["PORTABILIDAD SI"].sum(),"PORTABILIDAD NO":df_f["PORTABILIDAD NO"].sum(),
                "FTTH":df_f["FTTH"].sum(),"HFC":df_f["HFC"].sum(),"S/.":df_f["S/."].sum()}])
            d = pd.concat([df_f, total], ignore_index=True)
            d["S/."] = d["S/."].map(formatear_moneda)
            st.table(d.style.set_table_styles(_style_tabla(color))
                .set_properties(subset=["Año","Mes"], **{"text-align":"left"})
                .set_properties(subset=["Ventas","PORTABILIDAD SI","PORTABILIDAD NO","FTTH","HFC","S/."], **{"text-align":"center"}))
    with col2:
        st.markdown("### Detalle desplegable")
        mostrar_expanders_fija(obtener_factor_fija_detallado(tabla, col_fecha, filtro), color=color)

def mostrar_factor_movil(tabla, col_fecha, filtro, color):
    col1, col2 = st.columns([1.2, 1.6])
    with col1:
        st.markdown("### Resumen")
        df_r = obtener_factor_movil_resumen(tabla, filtro, col_fecha)
        if df_r.empty: st.warning("Sin datos.")
        else:
            total = pd.DataFrame([{"Año":"Total","Mes":"","Ventas":df_r["Ventas"].sum(),
                "PORTABILIDAD":df_r["PORTABILIDAD"].sum(),"ALTA":df_r["ALTA"].sum(),
                "CF>69.90":df_r["CF>69.90"].sum(),"CF<=69.90":df_r["CF<=69.90"].sum(),
                "Dias>90":df_r["Dias>90"].sum(),"Dias<=90":df_r["Dias<=90"].sum(),"S/.":df_r["S/."].sum()}])
            d = pd.concat([df_r, total], ignore_index=True)
            d["S/."] = d["S/."].map(formatear_moneda)
            st.table(d.style.set_table_styles(_style_tabla(color))
                .set_properties(subset=["Año","Mes"], **{"text-align":"left"})
                .set_properties(subset=["Ventas","PORTABILIDAD","ALTA","CF>69.90","CF<=69.90","Dias>90","Dias<=90","S/."], **{"text-align":"center"}))
    with col2:
        st.markdown("### Detalle desplegable")
        mostrar_expanders_movil(obtener_factor_movil_detallado(tabla, filtro, col_fecha), color=color)

def mostrar_iae_movil(tabla, col_fecha, filtro, key_asesor, color):
    df_m = preparar_fechas_movil(get_tabla(tabla))
    df_m = filtrar_por_mes_anio(df_m, col_fecha, filtro)
    if df_m.empty: st.warning("Sin datos."); return
    df_m["_comision"] = obtener_comision_movil(df_m)
    tr = df_m.get("TRANSACCION", pd.Series([""] * len(df_m))).fillna("").astype(str)
    df_m["_porta"] = _es_portabilidad_movil(tr)
    df_m["_alta"]  = _es_alta_movil(tr)
    col_a = encontrar_columna(df_m, ["USUARIO","ASESOR","VENDEDOR","DISTRIBUIDOR"])
    df_m["ASESOR"] = df_m[col_a].fillna("Sin Asesor") if col_a else "Sin Asesor"
    filtro_a = st.selectbox("Selecciona Asesor", ["Todos"] + sorted(df_m["ASESOR"].unique().tolist()), key=key_asesor)
    df_f = df_m[df_m["ASESOR"] == filtro_a].copy() if filtro_a != "Todos" else df_m.copy()
    st.markdown("### Ranking de Asesores")
    r = (df_f.groupby("ASESOR").agg(
        Total_Ventas=("_porta", lambda x: len(x)), Portabilidades=("_porta","sum"),
        Altas=("_alta","sum"), Comision_Total=("_comision","sum"),
    ).reset_index().sort_values("Comision_Total", ascending=False))
    r["Rank"] = r["Comision_Total"].rank(method="dense", ascending=False).astype(int)
    r = r[["Rank","ASESOR","Total_Ventas","Portabilidades","Altas","Comision_Total"]]
    total = pd.DataFrame([{"Rank":"Total","ASESOR":"","Total_Ventas":r["Total_Ventas"].sum(),
        "Portabilidades":r["Portabilidades"].sum(),"Altas":r["Altas"].sum(),"Comision_Total":r["Comision_Total"].sum()}])
    st.table(pd.concat([r, total], ignore_index=True).style.format({"Comision_Total":"S/ {:,.2f}"})
        .set_properties(**{"text-align":"center"}).set_properties(subset=["ASESOR"], **{"text-align":"left"}))

def _normalizar_texto(txt):
    return str(txt).upper().strip().replace("Í","I").replace("Á","A").replace("É","E").replace("Ó","O").replace("Ú","U")

def _estado_desde_tipis(tipis_txt):
    return TIPIS_ESTADO_MAP.get(_normalizar_texto(tipis_txt), "Otros")

def _normalizar_sot_series(serie):
    """
    Normaliza SOT para cruces entre DEVELZ y CLARO.
    Corrige casos como:
    - 87274852.0  -> 87274852
    - 87274852    -> 87274852
    - espacios invisibles / caracteres raros
    - valores nulos
    - SOT con guiones o separadores

    IMPORTANTE:
    Esta función se usa para mostrar la SOT limpia.
    Para comparar de forma más agresiva se usa _sot_key_series().
    """
    s = serie.fillna("").astype(str).str.strip()
    s = s.str.replace("\\u00a0", "", regex=False)
    s = s.str.replace("\ufeff", "", regex=False)
    s = s.str.replace(r"\s+", "", regex=True)
    s = s.str.replace(r"\.0+$", "", regex=True)
    s = s.str.replace(r"^'", "", regex=True)
    s = s.replace(["nan","NaN","None","NONE","null","NULL","NaT","<NA>"], "")
    return s

def _sot_key_series(serie):
    """
    Llave técnica SOLO para cruces SOT.
    Evita falsos faltantes cuando una base trae la SOT como texto, número,
    decimal, con espacios, guiones o caracteres invisibles.

    Ejemplos que quedan iguales:
    - 87274852
    - 87274852.0
    - 87 274 852
    - 87-274-852
    """
    s = _normalizar_sot_series(serie)
    s = s.str.replace(r"[^0-9]", "", regex=True)
    s = s.str.lstrip("0")
    return s.replace(["nan","NaN","None","NONE","null","NULL","NaT","<NA>"], "")

# --- Obtención de campos DEVELZ ---
def _obtener_sot_develz(df):
    col = encontrar_columna(df, ["Back Office - Sot","Back Office - SOT","SOT","sot","Sot"])
    return df[col].fillna("").astype(str).str.strip() if col else pd.Series([""] * len(df), index=df.index)

def _obtener_fecha_inst_develz(df):
    col = encontrar_columna(df, ["Back Office - Fecha Instalacion","Back Office - Fecha Instalación",
                                  "FECHA INSTALACION","Fecha Instalacion","Fecha Instalación"])
    return pd.to_datetime(df[col], errors="coerce", dayfirst=True) if col else pd.Series(pd.NaT, index=df.index)

def _obtener_fecha_venta_develz(df):
    col = encontrar_columna(df, ["FECHA DE VENTA", "Fecha de Venta", "Fecha Venta", "FECHA VENTA",
                                  "Back Office - Fecha de Venta", "Back Office - Fecha Venta",
                                  "FECHA GENERACION", "Fecha Generacion", "Fecha Generación"])
    return pd.to_datetime(df[col], errors="coerce", dayfirst=True) if col else pd.Series(pd.NaT, index=df.index)

def _obtener_supervisor_develz(df):
    col = encontrar_columna(df, ["Datos Adicionales - Supervisor","Datos adicionales - Supervisor",
                                  "SUPERVISOR","Supervisor","supervisor","USUARIO","Usuario"])
    return (df[col].fillna("Sin Supervisor").astype(str).str.strip().replace("","Sin Supervisor")
            if col else pd.Series(["Sin Supervisor"] * len(df), index=df.index))

def _obtener_asesor_creador_develz(df):
    col = encontrar_columna(df, ["CREADOR","Creador","creador","Usuario Creador","USUARIO CREADOR",
                                  "Datos Adicionales - Creador","Datos adicionales - Creador"])
    return (df[col].fillna("Sin Asesor").astype(str).str.strip().replace("","Sin Asesor")
            if col else pd.Series(["Sin Asesor"] * len(df), index=df.index))

def _obtener_nombre_cliente_develz(df):
    def _col(posibles): return encontrar_columna(df, posibles)
    def _get(posibles, defecto=""):
        c = _col(posibles); return df[c].fillna("").astype(str).str.strip() if c else pd.Series([defecto]*len(df),index=df.index)
    nom     = _get(["Cliente - Nombre","NOMBRE","Nombre","CLIENTE"])
    ape_pat = _get(["Cliente - Apellido Paterno","Apellido Paterno","APELLIDO PATERNO"])
    ape_mat = _get(["Cliente - Apellido Materno","Apellido Materno","APELLIDO MATERNO"])
    return (nom+" "+ape_pat+" "+ape_mat).str.strip().replace("","Sin Datos").fillna("Sin Datos")

def _obtener_departamento_develz(df):
    col = encontrar_columna(df, ["Datos Instalación - Departamento","Datos Instalacion - Departamento",
                                  "DEPARTAMENTO","Departamento","departamento"])
    return (df[col].fillna("Sin Datos").astype(str).str.strip().replace("","Sin Datos")
            if col else pd.Series(["Sin Datos"] * len(df), index=df.index))

def _obtener_tipis_develz(df):
    col = encontrar_columna(df, ["TIPIS","Tipis","tipis","Estados - Venta Especificacion",
                                  "Estados - Venta Especificación","Estado - Venta Especificacion",
                                  "Estado - Venta Especificación","ESTADO OPERATIVO","Estado Operativo","estado operativo"])
    return (df[col].fillna("Sin TIPIS").astype(str).str.strip().replace("","Sin TIPIS")
            if col else pd.Series(["Sin TIPIS"] * len(df), index=df.index))

def _obtener_documento_develz(df):
    col = encontrar_columna(df, ["Cliente - Documento","Cliente - Nro Documento"])
    return df[col].fillna("").astype(str).str.strip() if col else pd.Series([""] * len(df), index=df.index)

@st.cache_data(ttl=600)
def _base_claro_pago(tabla_ventas):
    df_c = preparar_fechas_fija(get_tabla(tabla_ventas))
    cols = ["SOT","COMISION_CLARO","COMISIONES_CLARO","FECHA_INSTALACION_CLARO"]
    if df_c.empty or "SOT" not in df_c.columns: return pd.DataFrame(columns=cols)
    df_c = df_c.copy()
    df_c["SOT"] = _normalizar_sot_series(df_c["SOT"])
    df_c = df_c[df_c["SOT"] != ""]
    df_c["COMISION_CLARO"] = obtener_comision_fija(df_c)
    df_c["COMISIONES_CLARO"] = (df_c["COMISIONES"].fillna("").astype(str).str.upper().str.strip().str.replace("Í","I",regex=False)
                                 if "COMISIONES" in df_c.columns else "")
    df_c["_pagada_flag"] = (df_c["COMISIONES_CLARO"] == "SI") | (df_c["COMISION_CLARO"] > 0)
    # Extraer FECHA INSTALACION de CLARO para mostrarla en el detalle
    df_c["_FECHA_INST_CLARO_DT"] = pd.to_datetime(
        df_c["FECHA INSTALACION"] if "FECHA INSTALACION" in df_c.columns else None,
        errors="coerce", dayfirst=True
    )
    resumen = df_c.groupby("SOT", as_index=False).agg(
        COMISION_CLARO=("COMISION_CLARO","sum"),
        PAGADA_FLAG=("_pagada_flag","max"),
        FECHA_INSTALACION_CLARO=("_FECHA_INST_CLARO_DT","max"))
    resumen["COMISIONES_CLARO"] = resumen["PAGADA_FLAG"].apply(lambda x: "SI" if x else "NO")
    resumen["FECHA_INSTALACION_CLARO"] = pd.to_datetime(
        resumen["FECHA_INSTALACION_CLARO"], errors="coerce"
    ).dt.strftime("%d/%m/%Y").fillna("")
    return resumen[cols]

@st.cache_data(ttl=600)
def construir_detalle_fija_develz(tabla_maestro, tabla_claro, canal, filtro_mes, filtro_fecha_venta="Todos los meses"):
    cols_salida = ["Canal","SOT","Documento","SUPERVISOR","ASESOR","Nombre del Cliente","Departamento",
                   "FECHA INSTALACION","FECHA DE VENTA","TIPIS","Estado Operativo","COMISION","Estado Pago","COLA"]
    try:
        df_m = get_tabla(tabla_maestro)
        if df_m.empty: return pd.DataFrame(columns=cols_salida)
        df_m = df_m.copy()
        df_m["Canal"] = canal
        df_m["SOT"] = _normalizar_sot_series(_obtener_sot_develz(df_m))
        df_m["Documento"] = _obtener_documento_develz(df_m)
        df_m["_FECHA_DT"] = _obtener_fecha_inst_develz(df_m)
        df_m["_FECHA_VENTA_DT"] = _obtener_fecha_venta_develz(df_m)

        if filtro_mes != "Todos los meses":
            m, y = parse_mes_anio(filtro_mes)
            if m and y:
                df_m = df_m[(df_m["_FECHA_DT"].dt.month == m) & (df_m["_FECHA_DT"].dt.year == y)].copy()

        if filtro_fecha_venta != "Todos los meses":
            m_v, y_v = parse_mes_anio(filtro_fecha_venta)
            if m_v and y_v:
                df_m = df_m[(df_m["_FECHA_VENTA_DT"].dt.month == m_v) & (df_m["_FECHA_VENTA_DT"].dt.year == y_v)].copy()

        if df_m.empty: return pd.DataFrame(columns=cols_salida)
        df_m["SUPERVISOR"] = _obtener_supervisor_develz(df_m)
        df_m["ASESOR"] = _obtener_asesor_creador_develz(df_m)
        df_m["Nombre del Cliente"] = _obtener_nombre_cliente_develz(df_m)
        df_m["Departamento"] = _obtener_departamento_develz(df_m)
        df_m["TIPIS"] = _obtener_tipis_develz(df_m)
        df_m["Estado Operativo"] = df_m["TIPIS"].apply(_estado_desde_tipis)
        df_pago = _base_claro_pago(tabla_claro)
        df = df_m.merge(df_pago, on="SOT", how="left")

        # Diagnóstico interno opcional:
        # st.session_state["debug_detalle_fija"] = True
        if st.session_state.get("debug_detalle_fija", False):
            st.write(f"DEBUG {canal} | Base DEVELZ:", len(df_m))
            st.write(f"DEBUG {canal} | SOT DEVELZ únicos:", df_m["SOT"].nunique())
            st.write(f"DEBUG {canal} | Base CLARO pagos:", len(df_pago))
            st.write(f"DEBUG {canal} | Cruces encontrados:", df["COMISION_CLARO"].notna().sum())
            st.write(f"DEBUG {canal} | Pagadas SI:", (df.get("COMISIONES_CLARO", "").fillna("").astype(str).str.upper() == "SI").sum())
            st.write(f"DEBUG {canal} | Comisión mayor a 0:", (pd.to_numeric(df.get("COMISION_CLARO", 0), errors="coerce").fillna(0) > 0).sum())
        df["COMISION"] = pd.to_numeric(df.get("COMISION_CLARO", 0), errors="coerce").fillna(0)
        df["COMISIONES_CLARO"] = df.get("COMISIONES_CLARO","").fillna("").astype(str).str.upper().str.strip().str.replace("Í","I",regex=False)
        df["Estado Pago"] = "CAÍDA"
        df.loc[(df["COMISIONES_CLARO"] == "SI") | (df["COMISION"] > 0), "Estado Pago"] = "PAGADA"
        # FECHA INSTALACION: usar la del archivo CLARO cuando hay cruce, si no la de DEVELZ
        _fecha_claro = df.get("FECHA_INSTALACION_CLARO", pd.Series("", index=df.index)).fillna("")
        _fecha_develz = df["_FECHA_DT"].dt.strftime("%d/%m/%Y").fillna("")
        df["FECHA INSTALACION"] = _fecha_claro.where(_fecha_claro != "", _fecha_develz)
        df["FECHA DE VENTA"] = df["_FECHA_VENTA_DT"].dt.strftime("%d/%m/%Y").fillna("")
        # ── COLA: cruce con DOTACION por extensión del usuario ─────────────
        # BUSCARV: EXTENSION DEL USUARIO (Excel datos)  ->  USUARIO (DOTACION)  ->  SEGMENTO
        col_ext = encontrar_columna(df_m, ["EXTENSION DEL USUARIO","EXTENSIÓN DEL USUARIO","Extension del usuario","EXTENSION","Extension"])
        if col_ext:
            df["COLA"] = _agregar_cola_por_extension(df_m.reindex(df.index), col_ext)
        else:
            df["COLA"] = "EXTERNO"
        for col in cols_salida:
            if col not in df.columns: df[col] = ""
        return df[cols_salida].reset_index(drop=True)
    except Exception as e:
        st.error(f"Error construyendo detalle DEVELZ {canal}: {e}")
        return pd.DataFrame(columns=cols_salida)

@st.cache_data(ttl=600)
def construir_detalle_fija_general(filtro_mes, filtro_fecha_venta="Todos los meses"):
    df_dc = construir_detalle_fija_develz("[DATA DEVELZ].dbo.FIJA_DC", "dbo.CLARO_DC_FIJA", "D&C", filtro_mes, filtro_fecha_venta)
    df_tt = construir_detalle_fija_develz("[DATA DEVELZ].dbo.FIJA_TELETALK", "dbo.CLARO_TELETALK_FIJA", "Teletalk", filtro_mes, filtro_fecha_venta)
    return pd.concat([df_dc, df_tt], ignore_index=True)

def kpi_detalle_fija(df):
    if df.empty: return 0, 0, 0, 0.0, 0.0
    t,p,c = int(len(df)), int((df["Estado Pago"]=="PAGADA").sum()), int((df["Estado Pago"]=="CAÍDA").sum())
    com = pd.to_numeric(df["COMISION"], errors="coerce").fillna(0).sum()
    return t, p, c, com, (p/t*100) if t>0 else 0

def ranking_departamentos_df(df):
    """
    Ranking gerencial por departamento.
    Mantiene la lógica original:
    - Total = cantidad de registros DEVELZ filtrados
    - Pagadas = Estado Pago == PAGADA
    - Caidas = Estado Pago == CAÍDA
    - Comisión = suma de COMISION
    """
    cols = ["Rank", "Departamento", "Total", "Pagadas", "Caidas", "Comision", "% Participación", "% Efectividad"]

    if df.empty or "Departamento" not in df.columns: return pd.DataFrame(columns=cols)

    base = df.copy()
    base["Departamento"] = base["Departamento"].fillna("Sin Departamento").astype(str).str.strip()
    base.loc[base["Departamento"].eq(""), "Departamento"] = "Sin Departamento"
    base["COMISION"] = pd.to_numeric(base.get("COMISION", 0), errors="coerce").fillna(0)

    grp = (
        base.groupby("Departamento", dropna=False)
        .agg(
            Total=("Estado Pago", "count"),
            Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
            Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
            Comision=("COMISION", "sum"),
        )
        .reset_index()
    )

    total_ventas = int(grp["Total"].sum())
    total_pagadas = int(grp["Pagadas"].sum())
    total_caidas = int(grp["Caidas"].sum())
    total_comision = float(pd.to_numeric(grp["Comision"], errors="coerce").fillna(0).sum())

    grp["% Participación"] = (grp["Pagadas"] / total_pagadas * 100).round(2) if total_pagadas > 0 else 0.0
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).fillna(0)

    grp = grp.sort_values(["Pagadas", "Comision", "Total"], ascending=[False, False, False]).reset_index(drop=True)
    grp.insert(0, "Rank", grp.index + 1)

    total_row = pd.DataFrame([{
        "Rank": "TOTAL",
        "Departamento": "",
        "Total": total_ventas,
        "Pagadas": total_pagadas,
        "Caidas": total_caidas,
        "Comision": total_comision,
        "% Participación": 100.00 if total_pagadas > 0 else 0.00,
        "% Efectividad": round((total_pagadas / total_ventas * 100), 2) if total_ventas > 0 else 0.00,
    }])

    return pd.concat([grp[cols], total_row[cols]], ignore_index=True)

def mostrar_ranking_departamentos_premium(df):
    rank_dpto = ranking_departamentos_df(df)

    if rank_dpto.empty:
        st.warning("No se encontró columna de departamento.")
        return

    base = rank_dpto[rank_dpto["Rank"].astype(str) != "TOTAL"].copy()
    total = rank_dpto[rank_dpto["Rank"].astype(str) == "TOTAL"].copy()

    total_departamentos = int(base["Departamento"].nunique()) if not base.empty else 0
    total_ventas = int(total["Total"].iloc[0]) if not total.empty else int(base["Total"].sum())
    total_pagadas = int(total["Pagadas"].iloc[0]) if not total.empty else int(base["Pagadas"].sum())
    total_caidas = int(total["Caidas"].iloc[0]) if not total.empty else int(base["Caidas"].sum())
    total_comision = float(total["Comision"].iloc[0]) if not total.empty else float(pd.to_numeric(base["Comision"], errors="coerce").fillna(0).sum())
    efectividad = (total_pagadas / total_ventas * 100) if total_ventas > 0 else 0

    # KPI territorial: Lima vs Provincia.
    # Se calcula sobre el total de ventas de cada departamento dentro de la base filtrada.
    if not base.empty and "Departamento" in base.columns:
        dep_norm = (
            base["Departamento"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
            .str.replace("Á", "A", regex=False)
            .str.replace("É", "E", regex=False)
            .str.replace("Í", "I", regex=False)
            .str.replace("Ó", "O", regex=False)
            .str.replace("Ú", "U", regex=False)
        )
        mask_lima = dep_norm.str.contains("LIMA", na=False)
        lima_total = int(pd.to_numeric(base.loc[mask_lima, "Total"], errors="coerce").fillna(0).sum())
        provincia_total = int(pd.to_numeric(base.loc[~mask_lima, "Total"], errors="coerce").fillna(0).sum())
    else:
        lima_total = 0
        provincia_total = 0

    lima_pct = (lima_total / total_ventas * 100) if total_ventas > 0 else 0
    provincia_pct = (provincia_total / total_ventas * 100) if total_ventas > 0 else 0

    st.markdown("""
    <style>
        .dpto-premium-wrap{
            background:linear-gradient(135deg, rgba(255,255,255,.98), rgba(239,246,255,.96));
            border:1px solid rgba(15,66,135,.16);
            border-radius:26px;
            padding:24px 24px 18px 24px;
            box-shadow:0 18px 50px rgba(15,66,135,.13);
            margin-bottom:18px;
        }
        .dpto-kpi-card{
            background:white;
            border-radius:22px;
            padding:18px 14px;
            text-align:center;
            border:1px solid rgba(15,66,135,.16);
            box-shadow:0 10px 28px rgba(0,0,0,.08);
            min-height:112px;
        }
        .dpto-kpi-label{
            font-size:11px;
            font-weight:900;
            color:#64748b;
            letter-spacing:.08em;
            text-transform:uppercase;
            margin-bottom:8px;
        }
        .dpto-kpi-value{
            font-size:30px;
            font-weight:950;
            color:#0f4287;
            line-height:1.05;
        }
        .dpto-kpi-sub{
            font-size:11px;
            font-weight:700;
            color:#94a3b8;
            margin-top:6px;
        }
    </style>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Departamentos</div><div class="dpto-kpi-value">{total_departamentos:,}</div><div class="dpto-kpi-sub">zonas con gestión</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Lima</div><div class="dpto-kpi-value" style="color:#0f4287;">{lima_total:,}</div><div class="dpto-kpi-sub">{lima_pct:.2f}% del total</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Provincia</div><div class="dpto-kpi-value" style="color:#7c3aed;">{provincia_total:,}</div><div class="dpto-kpi-sub">{provincia_pct:.2f}% del total</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="dpto-kpi-card"><div class="dpto-kpi-label">Efectividad</div><div class="dpto-kpi-value">{efectividad:.2f}%</div><div class="dpto-kpi-sub">pagadas / total</div></div>', unsafe_allow_html=True)

    st.write("")

    if not base.empty:
        top = base.head(10).copy()
        try:
            import altair as alt
            chart_data = top[["Departamento", "Pagadas", "Caidas"]].melt(
                "Departamento",
                var_name="Estado",
                value_name="Cantidad"
            )
            chart = (
                alt.Chart(chart_data)
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Cantidad:Q", title="Ventas"),
                    y=alt.Y("Departamento:N", sort="-x", title=""),
                    color=alt.Color(
                        "Estado:N",
                        scale=alt.Scale(domain=["Pagadas", "Caidas"], range=["#059669", "#dc2626"]),
                        legend=alt.Legend(title="Estado")
                    ),
                    tooltip=["Departamento", "Estado", "Cantidad"]
                )
                .properties(height=max(260, len(top) * 42), title="Top departamentos por ventas pagadas y caídas")
                .configure_axis(labelFontSize=12, titleFontSize=13)
                .configure_title(fontSize=18, fontWeight="bold", color="#0f4287")
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.info("No se pudo renderizar el gráfico, pero la tabla gerencial está disponible abajo.")

    tabla = rank_dpto.copy()
    tabla["Comision"] = tabla["Comision"].apply(lambda x: formatear_moneda(x) if isinstance(x, (int, float)) else x)
    tabla["% Participación"] = tabla["% Participación"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)
    tabla["% Efectividad"] = tabla["% Efectividad"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)

    st.markdown("#### Tabla gerencial por departamento")

    # IMPORTANTE:
    # No usamos Styler.background_gradient porque requiere matplotlib.
    # Estos estilos son manuales y funcionan sin instalar paquetes adicionales.
    def _color_pagadas(val):
        try:
            v = float(val)
            max_v = float(pd.to_numeric(tabla["Pagadas"], errors="coerce").fillna(0).max())
            intensidad = 0 if max_v == 0 else min(v / max_v, 1)
            alpha = 0.10 + (intensidad * 0.28)
            return f"background-color: rgba(5,150,105,{alpha}); color:#064e3b; font-weight:800; text-align:center;"
        except Exception:
            return "text-align:center;"

    def _color_caidas(val):
        try:
            v = float(val)
            max_v = float(pd.to_numeric(tabla["Caidas"], errors="coerce").fillna(0).max())
            intensidad = 0 if max_v == 0 else min(v / max_v, 1)
            alpha = 0.08 + (intensidad * 0.24)
            return f"background-color: rgba(220,38,38,{alpha}); color:#7f1d1d; font-weight:800; text-align:center;"
        except Exception:
            return "text-align:center;"

    def _resaltar_total(row):
        if str(row.get("Rank", "")).upper() == "TOTAL": return ["background-color:#0f4287; color:white; font-weight:900;" for _ in row]
        return ["" for _ in row]

    st.dataframe(
        tabla.style
        .apply(_resaltar_total, axis=1)
        .map(_color_pagadas, subset=["Pagadas"])
        .map(_color_caidas, subset=["Caidas"])
        .set_properties(**{"text-align": "center", "font-size": "13px"})
        .set_properties(subset=["Departamento"], **{"text-align": "left", "font-weight": "bold"}),
        use_container_width=True,
        height=min(650, 90 + 36 * len(tabla))
    )

    st.download_button(
        "⬇️ Descargar Ranking Departamentos",
        data=rank_dpto.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="ranking_departamentos_develz.csv",
        mime="text/csv",
        key="dl_ranking_departamentos_premium",
        on_click=registrar_descarga,
        args=("Ranking Departamentos", "ranking_departamentos_develz.csv", "Vista premium gerencial")
    )

def ranking_asesores_detalle(df):
    if df.empty or "SUPERVISOR" not in df.columns: return pd.DataFrame()
    grp = df.groupby("SUPERVISOR").agg(
        Total=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
        Comision=("COMISION", lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum()),
    ).reset_index().sort_values(["Comision","Total"], ascending=[False,False]).reset_index(drop=True)
    grp.insert(0,"Rank", grp.index + 1)
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).astype(str) + "%"
    total_row = pd.DataFrame([{"Rank":"TOTAL","SUPERVISOR":"","Total":grp["Total"].sum(),
        "Pagadas":grp["Pagadas"].sum(),"Caidas":grp["Caidas"].sum(),
        "% Efectividad":"","Comision":grp["Comision"].sum()}])
    return pd.concat([grp, total_row], ignore_index=True)

def ranking_asesores_por_supervisor_df(df, supervisor):
    cols = ["Rank","ASESOR","Total","Pagadas","Caidas","Comision","% Efectividad"]
    if df.empty: return pd.DataFrame(columns=cols)
    base = df.copy()
    if "SUPERVISOR" not in base.columns:
        base["SUPERVISOR"] = "Sin Supervisor"
    if "ASESOR" not in base.columns:
        base["ASESOR"] = "Sin Asesor"
    base["SUPERVISOR"] = base["SUPERVISOR"].fillna("Sin Supervisor").astype(str).str.strip().replace("", "Sin Supervisor")
    base["ASESOR"] = base["ASESOR"].fillna("Sin Asesor").astype(str).str.strip().replace("", "Sin Asesor")
    base["COMISION"] = pd.to_numeric(base.get("COMISION", 0), errors="coerce").fillna(0)
    base = base[base["SUPERVISOR"] == supervisor].copy()
    if base.empty: return pd.DataFrame(columns=cols)
    grp = base.groupby("ASESOR", dropna=False).agg(
        Total=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
        Comision=("COMISION","sum"),
    ).reset_index().sort_values(["Comision","Pagadas","Total"], ascending=[False,False,False]).reset_index(drop=True)
    grp.insert(0, "Rank", grp.index + 1)
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).astype(str) + "%"
    total = pd.DataFrame([{"Rank":"TOTAL","ASESOR":"","Total":int(grp["Total"].sum()),
        "Pagadas":int(grp["Pagadas"].sum()),"Caidas":int(grp["Caidas"].sum()),
        "Comision":float(grp["Comision"].sum()),"% Efectividad":""}])
    return pd.concat([grp[cols], total[cols]], ignore_index=True)

def mostrar_ranking_supervisores_con_asesores(df):
    rank_df = ranking_asesores_detalle(df)
    if rank_df.empty:
        st.warning("Sin datos para el ranking.")
        return

    rank_sin_total = rank_df[rank_df["Rank"].astype(str) != "TOTAL"].copy()
    total_row = rank_df[rank_df["Rank"].astype(str) == "TOTAL"].copy()

    st.caption("Haz clic en el ➕ de cada supervisor para ver el detalle de asesores.")

    for _, row in rank_sin_total.iterrows():
        supervisor = str(row.get("SUPERVISOR", "Sin Supervisor")).strip() or "Sin Supervisor"
        etiqueta = (
            f"➕ {row['Rank']} | {supervisor} | "
            f"Total: {int(row['Total']):,} | Pagadas: {int(row['Pagadas']):,} | "
            f"Caídas: {int(row['Caidas']):,} | Comisión: {formatear_moneda(row['Comision'])} | "
            f"Efectividad: {row['% Efectividad']}"
        )
        with st.expander(etiqueta, expanded=False):
            detalle_asesor = ranking_asesores_por_supervisor_df(df, supervisor)
            if detalle_asesor.empty:
                st.info("Este supervisor no tiene asesores asociados con los filtros actuales.")
            else:
                st.dataframe(
                    detalle_asesor.style.format({"Comision": lambda x: formatear_moneda(x) if isinstance(x, (int, float)) else x})
                    .set_properties(**{"text-align":"center"})
                    .set_properties(subset=["ASESOR"], **{"text-align":"left"}),
                    use_container_width=True,
                    height=min(420, 80 + 36 * len(detalle_asesor))
                )

    if not total_row.empty:
        st.markdown("##### Total general")
        st.table(total_row.style
            .format({"Comision": lambda x: formatear_moneda(x) if isinstance(x,(int,float)) else x})
            .set_properties(**{"text-align":"center"})
            .set_properties(subset=["SUPERVISOR"], **{"text-align":"left"}))

def ranking_asesores_fija_develz(df):
    cols = ["Rank","ASESOR","Total","Pagadas","Caidas","% Efectividad","Comision"]
    if df.empty or "ASESOR" not in df.columns: return pd.DataFrame(columns=cols)
    base = df.copy()
    base["ASESOR"] = base["ASESOR"].fillna("Sin Asesor").astype(str).str.strip().replace("","Sin Asesor")
    base["COMISION"] = pd.to_numeric(base.get("COMISION",0), errors="coerce").fillna(0)
    grp = base.groupby("ASESOR", dropna=False).agg(
        Total=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x == "CAÍDA").sum()),
        Comision=("COMISION","sum"),
    ).reset_index().sort_values(["Comision","Pagadas","Total"], ascending=[False,False,False]).reset_index(drop=True)
    grp.insert(0,"Rank", grp.index + 1)
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total"] * 100).round(2).astype(str) + "%"
    total = pd.DataFrame([{"Rank":"TOTAL","ASESOR":"","Total":int(grp["Total"].sum()),
        "Pagadas":int(grp["Pagadas"].sum()),"Caidas":int(grp["Caidas"].sum()),
        "% Efectividad":"","Comision":float(grp["Comision"].sum())}])
    return pd.concat([grp[cols], total[cols]], ignore_index=True)

def mostrar_iae_asesor_fija_develz(tabla_maestro, tabla_claro, canal, filtro_mes, key_asesor, color):
    df_det = construir_detalle_fija_develz(tabla_maestro, tabla_claro, canal, filtro_mes)
    if df_det.empty: st.warning("Sin datos."); return

    for campo, defecto in [("ASESOR","Sin Asesor"),("SUPERVISOR","Sin Supervisor"),("TIPIS","Sin TIPIS")]:
        if campo not in df_det.columns: df_det[campo] = defecto
        df_det[campo] = df_det[campo].fillna(defecto).astype(str).str.strip()
        df_det.loc[df_det[campo].eq(""), campo] = defecto

    f1, f2, f3 = st.columns(3)
    with f1: filtro_a  = st.selectbox("Asesor / Creador", ["Todos"] + sorted(df_det["ASESOR"].unique().tolist()), key=key_asesor)
    with f2: filtro_su = st.selectbox("Supervisor",       ["Todos"] + sorted(df_det["SUPERVISOR"].unique().tolist()), key=f"{key_asesor}_supervisor")
    with f3: filtro_ti = st.selectbox("Tipificación",     ["Todos"] + sorted(df_det["TIPIS"].unique().tolist()), key=f"{key_asesor}_tipificacion")

    df_f = df_det.copy()
    if filtro_a  != "Todos": df_f = df_f[df_f["ASESOR"]      == filtro_a]
    if filtro_su != "Todos": df_f = df_f[df_f["SUPERVISOR"]   == filtro_su]
    if filtro_ti != "Todos": df_f = df_f[df_f["TIPIS"]        == filtro_ti]

    total, pagadas, caidas, comision, pct = kpi_detalle_fija(df_f)
    color_borde = "#0f4287" if color == "dc" else "#70008f"

    def _card(col, label, valor, sub=""):
        with col:
            st.markdown(
                f'<div style="background:rgba(255,255,255,.95);padding:14px;border-radius:16px;'
                f'border:2px solid {color_borde};text-align:center;margin-bottom:8px;min-height:86px;">'
                f'<span style="color:#4b5563;font-weight:800;font-size:10px;text-transform:uppercase;display:block;">{label}</span>'
                f'<span style="color:{color_borde};font-size:24px;font-weight:900;display:block;line-height:1.1;">{valor}</span>'
                f'<span style="color:#6b7280;font-size:10px;">{sub}</span></div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    _card(k1,"Total Ventas",f"{total:,}","Base DEVELZ")
    _card(k2,"Pagadas",f"{pagadas:,}","Cruzan con CLARO")
    _card(k3,"Caídas",f"{caidas:,}","No pagadas / sin SOT")
    _card(k4,"% Efectividad",f"{pct:.2f}%","Pagadas / Total")
    _card(k5,"Comisión",formatear_moneda(comision),"CLARO pagado")

    st.write("---")
    st.markdown("### 🏆 Ranking de Asesores")
    ranking = ranking_asesores_fija_develz(df_f)
    if ranking.empty: st.warning("No se encontraron datos para el ranking.")
    else:
        st.dataframe(ranking.style.format({"Comision": lambda x: formatear_moneda(x) if isinstance(x,(int,float)) else x}),
                     use_container_width=True, height=460)

    csv_export = df_f.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(label="⬇️ Descargar base filtrada IAE asesor", data=csv_export,
        file_name=f"iae_asesor_fija_{canal}_{filtro_mes.replace(' ','_')}.csv", mime="text/csv",
        key=f"dl_iae_asesor_{canal}_{key_asesor}",
        on_click=registrar_descarga,
        args=(f"IAE Asesor Fija {canal}", f"iae_asesor_fija_{canal}_{filtro_mes.replace(' ','_')}.csv", f"Mes: {filtro_mes}"))

def estados_operativos_df(df):
    if df.empty: return pd.DataFrame()
    base = df.copy()
    if "Estado Operativo" not in base.columns: base["Estado Operativo"] = "Sin TIPIS"
    base["Estado Operativo"] = base["Estado Operativo"].fillna("Sin TIPIS").astype(str).str.strip()
    base.loc[base["Estado Operativo"].eq(""), "Estado Operativo"] = "Sin TIPIS"
    total = len(base)
    grp = base.groupby("Estado Operativo").agg(N_Ventas=("Estado Pago","count")).reset_index()
    grp["% del total"] = (grp["N_Ventas"] / total * 100).round(2).astype(str) + "%" if total > 0 else "0%"
    orden = {"Conforme":0,"1era Caída":1,"2da Caída":2,"Ejecución":3,"Otros":4,"Sin TIPIS":5}
    grp["_ord"] = grp["Estado Operativo"].map(orden).fillna(99)
    return grp.sort_values("_ord")[["Estado Operativo","N_Ventas","% del total"]]

def ventas_por_dia_df(df):
    cols = ["Fecha","Total Ventas","Pagadas","Caidas","Comision","% Efectividad"]
    if df.empty or "FECHA INSTALACION" not in df.columns: return pd.DataFrame(columns=cols)
    base = df.copy()
    base["_FECHA_DIA"] = pd.to_datetime(base["FECHA INSTALACION"], errors="coerce", dayfirst=True)
    hoy = pd.Timestamp.today().normalize()
    base = base[(base["_FECHA_DIA"] >= pd.Timestamp("2020-01-01")) & (base["_FECHA_DIA"] <= hoy)].copy()
    if base.empty: return pd.DataFrame(columns=cols)
    grp = base.groupby(base["_FECHA_DIA"].dt.date).agg(
        **{"Total Ventas":("Estado Pago","count"),
           "Pagadas":("Estado Pago", lambda x: (x == "PAGADA").sum()),
           "Caidas":("Estado Pago",  lambda x: (x == "CAÍDA").sum()),
           "Comision":("COMISION",   lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())}
    ).reset_index().rename(columns={"_FECHA_DIA":"Fecha"})
    grp["Fecha"] = pd.to_datetime(grp["Fecha"])
    grp["% Efectividad"] = (grp["Pagadas"] / grp["Total Ventas"] * 100).round(2).astype(str) + "%"
    return grp.sort_values("Fecha")[cols]

# --- Conciliación helpers ---
def _filtrar_df_por_meses(df, col_fecha, filtro_mes):
    """filtro_mes puede ser str 'Todos los meses', str 'Mes Año', o lista de 'Mes Año'."""
    if isinstance(filtro_mes, list):
        if not filtro_mes: return df
        def _match(dt):
            if pd.isna(dt): return False
            label = f"{_MESES_ES_CACHE[dt.month].capitalize()} {dt.year}"
            return label in filtro_mes
        return df[df[col_fecha].apply(_match)].copy()
    else:
        if filtro_mes == "Todos los meses": return df
        m, y = parse_mes_anio(filtro_mes)
        if m and y: return df[(df[col_fecha].dt.month == m) & (df[col_fecha].dt.year == y)].copy()
        return df

_MESES_ES_CACHE = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",
                   7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}

def _df_develz_para_conciliacion(tabla_maestro, canal, filtro_mes):
    df = get_tabla(tabla_maestro)
    empty = pd.DataFrame(columns=["Canal","SOT","Fecha_Develz","Supervisor","Cliente","Departamento","TIPIS"])
    if df.empty: return empty
    df = df.copy()
    df["Canal"] = canal
    df["SOT"] = _normalizar_sot_series(_obtener_sot_develz(df))
    df["_FECHA_DT"] = _obtener_fecha_inst_develz(df)
    df = _filtrar_df_por_meses(df, "_FECHA_DT", filtro_mes)
    if df.empty: return empty
    df["Fecha_Develz"] = df["_FECHA_DT"].dt.strftime("%d/%m/%Y").fillna("")
    df["Supervisor"]   = _obtener_supervisor_develz(df)
    df["Cliente"]      = _obtener_nombre_cliente_develz(df)
    df["Departamento"] = _obtener_departamento_develz(df)
    df["TIPIS"]        = _obtener_tipis_develz(df)
    df["Documento"]    = _obtener_documento_develz(df)
    return df[["Canal","SOT","Fecha_Develz","Supervisor","Cliente","Documento","Departamento","TIPIS"]].copy()

def _df_claro_para_conciliacion(tabla_claro, canal, filtro_mes):
    df = preparar_fechas_fija(get_tabla(tabla_claro))
    empty = pd.DataFrame(columns=["Canal","SOT","Fecha_Claro","Cliente","Documento","Comision_Claro","Comisiones_Claro"])
    if df.empty or "SOT" not in df.columns: return empty
    df = df.copy()
    df["Canal"] = canal
    df["SOT"] = _normalizar_sot_series(df["SOT"])
    df = df[df["SOT"] != ""]
    if "FECHA INSTALACION" in df.columns:
        df = _filtrar_df_por_meses(df, "FECHA INSTALACION", filtro_mes)
    if df.empty: return empty
    df["Comision_Claro"] = obtener_comision_fija(df)
    df["Comisiones_Claro"] = (df["COMISIONES"].fillna("").astype(str).str.upper().str.strip().str.replace("Í","I",regex=False)
                               if "COMISIONES" in df.columns else "")
    df["Fecha_Claro"] = (df["FECHA INSTALACION"].dt.strftime("%d/%m/%Y").fillna("")
                          if "FECHA INSTALACION" in df.columns else "")
    col_doc = encontrar_columna(df, ["NRO DOCUMENTO","DOCUMENTO","DNI"])
    df["Documento"] = df[col_doc].fillna("").astype(str).str.strip() if col_doc else ""
    col_cli = encontrar_columna(df, ["CLIENTE","Cliente","NOMBRE CLIENTE","Nombre Cliente","NOMBRE","Nombre","Nombre del Cliente"])
    df["Cliente"] = df[col_cli].fillna("").astype(str).str.strip() if col_cli else ""
    df_res = df.groupby(["Canal","SOT"], as_index=False).agg(
        Fecha_Claro=("Fecha_Claro","first"), Cliente=("Cliente","first"), Documento=("Documento","first"),
        Comision_Claro=("Comision_Claro","sum"),
        Comisiones_Claro=("Comisiones_Claro", lambda x: "SI" if (x.astype(str).str.upper().str.strip() == "SI").any() else "NO"))
    return df_res[["Canal","SOT","Fecha_Claro","Cliente","Documento","Comision_Claro","Comisiones_Claro"]].copy()

def obtener_claro_pagado_no_develz(filtro_mes, filtro_canal):
    pares = [("D&C","[DATA DEVELZ].dbo.FIJA_DC","dbo.CLARO_DC_FIJA"),
             ("Teletalk","[DATA DEVELZ].dbo.FIJA_TELETALK","dbo.CLARO_TELETALK_FIJA")]
    salida = []
    for canal, tabla_dev, tabla_claro in pares:
        if filtro_canal != "Todos" and canal != filtro_canal: continue

        # ✅ CORRECCIÓN SENIOR:
        # CLARO sí debe respetar el mes filtrado porque queremos revisar las ventas pagadas de ese periodo.
        # Pero DEVELZ NO debe filtrarse por mes en este cruce de "no aparece", porque una SOT puede existir
        # en DEVELZ con otra fecha de instalación/venta. Antes eso generaba falsos faltantes.
        dev_total = _df_develz_para_conciliacion(tabla_dev, canal, [])  # sin filtro: busca en todo DEVELZ
        claro     = _df_claro_para_conciliacion(tabla_claro, canal, filtro_mes)

        if claro.empty: continue

        # Llave técnica robusta para comparar SOT sin afectar cómo se muestra la SOT original limpia.
        claro["_SOT_KEY"] = _sot_key_series(claro["SOT"])
        if not dev_total.empty:
            dev_total["_SOT_KEY"] = _sot_key_series(dev_total["SOT"])
            dev_sot_keys = set(dev_total.loc[dev_total["_SOT_KEY"] != "", "_SOT_KEY"].unique())
        else:
            dev_sot_keys = set()

        claro["PAGADA_CLARO"] = (
            (claro["Comisiones_Claro"].fillna("").astype(str).str.upper().str.strip().str.replace("Í","I",regex=False) == "SI") |
            (pd.to_numeric(claro["Comision_Claro"], errors="coerce").fillna(0) > 0)
        )

        faltantes = claro[
            (claro["PAGADA_CLARO"]) &
            (claro["_SOT_KEY"] != "") &
            (~claro["_SOT_KEY"].isin(dev_sot_keys))
        ].copy()

        if not faltantes.empty:
            faltantes["Motivo"] = "Claro lo paga, pero el SOT no aparece en DEVELZ"
            salida.append(faltantes)

    if not salida: return pd.DataFrame(columns=["Canal","SOT","Fecha_Claro","Cliente","Documento","Comision_Claro","Comisiones_Claro","Motivo"])

    df_out = pd.concat(salida, ignore_index=True)
    for col in ["Cliente","Documento"]:
        if col not in df_out.columns:
            df_out[col] = ""

    if "_SOT_KEY" in df_out.columns:
        df_out = df_out.drop(columns=["_SOT_KEY"], errors="ignore")

    return df_out[["Canal","SOT","Fecha_Claro","Cliente","Documento","Comision_Claro","Comisiones_Claro","Motivo"]]

def mostrar_claro_pagado_no_develz(filtro_mes, filtro_canal):
    st.write("---")
    st.markdown("#### 🔴 Ventas pagadas por CLARO que NO aparecen en DEVELZ")
    st.caption("Este cuadro explica la diferencia entre el número pagado de CLARO y el detalle basado en DEVELZ.")
    df_faltantes = obtener_claro_pagado_no_develz(filtro_mes, filtro_canal)
    if df_faltantes.empty:
        st.success("No hay SOT pagados por CLARO faltantes en DEVELZ con los filtros seleccionados.")
        return
    total_sot      = df_faltantes["SOT"].nunique()
    total_comision = pd.to_numeric(df_faltantes["Comision_Claro"], errors="coerce").fillna(0).sum()
    _lbl = "-".join(filtro_mes) if isinstance(filtro_mes, list) and filtro_mes else ("todos" if isinstance(filtro_mes, list) else filtro_mes)
    _nombre_csv = f"claro_pagado_no_develz_{_lbl.replace(' ','_')}_{filtro_canal}.csv"

    def _mini(col, label, valor, color):
        with col:
            st.markdown(f'<div style="background:rgba(255,255,255,.96);padding:14px;border-radius:14px;'
                        f'border:2px solid {color};text-align:center;margin-bottom:8px;">'
                        f'<span style="color:#4b5563;font-weight:800;font-size:10px;text-transform:uppercase;">{label}</span>'
                        f'<span style="color:{color};font-size:26px;font-weight:900;display:block;">{valor}</span>'
                        f'</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    _mini(c1,"SOT pagados no encontrados",f"{total_sot:,}","#dc2626")
    _mini(c2,"Comision no conciliada",formatear_moneda(total_comision),"#dc2626")

    df_show = df_faltantes.copy()
    for col in ["Cliente","Documento"]:
        if col not in df_show.columns: df_show[col] = ""
    df_show["Comision_Claro"] = pd.to_numeric(df_show["Comision_Claro"], errors="coerce").fillna(0).map(formatear_moneda)
    st.dataframe(df_show, use_container_width=True, height=260)
    csv_export = df_faltantes.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("⬇️ Descargar SOT pagados por CLARO no encontrados en DEVELZ", data=csv_export,
        file_name=_nombre_csv, mime="text/csv", key="dl_claro_pagado_no_develz_detalle",
        on_click=registrar_descarga,
        args=("Claro pagado no DEVELZ", _nombre_csv, f"Mes: {_lbl} | Canal: {filtro_canal}"))

def _kpi_card_html(col, label, valor, sub, color_borde, color_val="inherit"):
    with col:
        st.markdown(
            f'<div style="background:rgba(255,255,255,.95);padding:16px;border-radius:16px;'
            f'border:2px solid {color_borde};text-align:center;margin-bottom:8px;min-height:92px;">'
            f'<span style="color:#4b5563;font-weight:800;font-size:10px;text-transform:uppercase;'
            f'letter-spacing:.1em;display:block;margin-bottom:6px;">{label}</span>'
            f'<span style="color:{color_val};font-size:24px;font-weight:900;display:block;line-height:1.05;">{valor}</span>'
            f'<span style="color:#6b7280;font-size:10px;">{sub}</span></div>', unsafe_allow_html=True)

def _grafico_barras_agrupado(chart_melt, sort_order, x_title, bar_size=18):
    import altair as alt
    # ✅ Seguridad extra: evita error narwhals.exceptions.DuplicateError por nombres duplicados
    chart_melt = chart_melt.loc[:, ~chart_melt.columns.duplicated()].copy()
    base = alt.Chart(chart_melt).encode(
        x=alt.X("Fecha:N", title=x_title, sort=sort_order,
                 axis=alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=12)),
        xOffset=alt.XOffset("Indicador:N"),
        y=alt.Y("Cantidad:Q", title="Ventas", axis=alt.Axis(labelFontSize=12, titleFontSize=12, grid=True)),
        color=alt.Color("Indicador:N",
                         scale=alt.Scale(domain=["Total Ventas","Pagadas"], range=["#123f7a","#10a06f"]),
                         legend=alt.Legend(title="Indicador", orient="top-right")),
        tooltip=[alt.Tooltip("Fecha:N", title=x_title), alt.Tooltip("Indicador:N"), alt.Tooltip("Cantidad:Q", format=",.0f")]
    )
    barras    = base.mark_bar(size=bar_size, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, opacity=0.92)
    etiquetas = base.mark_text(align="center", baseline="bottom", dy=-6, fontSize=10, fontWeight="bold", color="#111827"
                               ).encode(text=alt.Text("Cantidad:Q", format=".0f"))
    return (barras + etiquetas).properties(
        height=430, padding={"left":10,"right":25,"top":15,"bottom":10}
    ).configure_axis(labelFontSize=11, titleFontSize=12, grid=True, gridColor="#e5e7eb", domain=False
    ).configure_view(strokeWidth=0
    ).configure_legend(titleFontSize=12, labelFontSize=12, orient="top-right", symbolSize=120)

def _normalizar_sot_col(df, col="SOT"):
    if df.empty or col not in df.columns: return pd.Series([""] * len(df), index=df.index)
    return (df[col].fillna("").astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .replace(["nan", "NaN", "None", "NONE", "null", "NULL"], ""))

def _obtener_fecha_preferida_fija(df):
    for col in ["FECHA INSTALACION", "FECHA GENERACION", "FECHA DE VENTA", "FECHA OPERACION", "FECHA"]:
        if col in df.columns: return col
    return None

def _normalizar_si_no(valor):
    txt = str(valor).upper().strip()
    txt = (txt.replace("Í", "I").replace("Á", "A").replace("É", "E")
              .replace("Ó", "O").replace("Ú", "U"))
    return txt

def _obtener_columna_com_etapa(df):
    return encontrar_columna(df, ["COM ETAPA", "COM_ETAPA", "Com Etapa", "Com etapa", "COMISION ETAPA", "COMISIÓN ETAPA"])

def _obtener_supervisor_fija_dc_por_sot():
    cols = ["SOT", "SUPERVISOR"]
    try:
        df_sup = get_tabla("[DATA DEVELZ].dbo.FIJA_DC")
        if df_sup.empty: return pd.DataFrame(columns=cols)

        col_sot = encontrar_columna(df_sup, ["Back Office - Sot", "Back Office - SOT", "SOT", "sot", "Sot"])
        col_sup = encontrar_columna(df_sup, ["Datos Adicionales - Supervisor", "Datos adicionales - Supervisor", "SUPERVISOR", "Supervisor", "supervisor"])

        if not col_sot: return pd.DataFrame(columns=cols)

        df_sup = df_sup.copy()
        df_sup["SOT"] = _normalizar_sot_col(df_sup, col_sot)
        df_sup = df_sup[df_sup["SOT"] != ""].copy()

        if col_sup:
            df_sup["SUPERVISOR"] = df_sup[col_sup].fillna("Sin Supervisor").astype(str).str.strip()
            df_sup.loc[df_sup["SUPERVISOR"].eq(""), "SUPERVISOR"] = "Sin Supervisor"
        else:
            df_sup["SUPERVISOR"] = "Sin Supervisor"

        df_sup = df_sup.groupby("SOT", as_index=False).agg(SUPERVISOR=("SUPERVISOR", "first"))
        return df_sup[cols]
    except Exception:
        return pd.DataFrame(columns=cols)

@st.cache_data(ttl=3600)
def obtener_supervisores_segunda_caida_dc(filtro_mes_base="Todos los meses"):
    try:
        df_base = preparar_fechas_fija(get_tabla("dbo.CLARO_DC_FIJA"))
        if df_base.empty or "SOT" not in df_base.columns: return ["Todos"]

        df_base = df_base.copy()
        df_base["SOT"] = _normalizar_sot_col(df_base, "SOT")
        df_base = df_base[df_base["SOT"] != ""].copy()

        if filtro_mes_base != "Todos los meses" and "FECHA INSTALACION" in df_base.columns:
            df_base = filtrar_por_mes_anio(df_base, "FECHA INSTALACION", filtro_mes_base)

        df_sup = _obtener_supervisor_fija_dc_por_sot()
        df_base = df_base.merge(df_sup, on="SOT", how="left")
        df_base["SUPERVISOR"] = df_base.get("SUPERVISOR", "Sin Supervisor").fillna("Sin Supervisor").astype(str).str.strip()
        df_base.loc[df_base["SUPERVISOR"].eq(""), "SUPERVISOR"] = "Sin Supervisor"

        supervisores = sorted(df_base["SUPERVISOR"].dropna().astype(str).unique().tolist())
        return ["Todos"] + supervisores
    except Exception:
        return ["Todos"]

@st.cache_data(ttl=3600)
def construir_segunda_caida_fija_dc(filtro_mes_base="Todos los meses", filtro_supervisor="Todos"):
    """
    Cruza CLARO_DC_FIJA como base contra CLARO_DC_FIJA_SEGUNDA_CAIDA por SOT.
    Supervisor se trae desde FIJA_DC:
    - SOT base: CLARO_DC_FIJA[SOT]
    - SOT supervisor: FIJA_DC[Back Office - Sot]
    - Supervisor: FIJA_DC[Datos Adicionales - Supervisor]

    Regla:
    - Base: CLARO_DC_FIJA.
    - Pagadas en 3 meses: solo SOT que cruzan y tienen APLICA = SI.
    - Pendientes: SOT de base que no aparecen en segunda caída o aparecen con APLICA diferente de SI.
    - Comisión recuperada: columna COM ETAPA del archivo CLARO_DC_FIJA_SEGUNDA_CAIDA.
    """
    try:
        df_base = preparar_fechas_fija(get_tabla("dbo.CLARO_DC_FIJA"))
        df_pago_raw = preparar_fechas_fija(get_tabla("dbo.CLARO_DC_FIJA_SEGUNDA_CAIDA"))

        if df_base.empty or "SOT" not in df_base.columns: return pd.DataFrame(), pd.DataFrame(), ""

        df_base = df_base.copy()
        df_base["SOT"] = _normalizar_sot_col(df_base, "SOT")
        df_base = df_base[df_base["SOT"] != ""].copy()

        if filtro_mes_base != "Todos los meses" and "FECHA INSTALACION" in df_base.columns:
            df_base = filtrar_por_mes_anio(df_base, "FECHA INSTALACION", filtro_mes_base)

        # Cruce para traer supervisor desde FIJA_DC por SOT
        df_sup = _obtener_supervisor_fija_dc_por_sot()
        df_base = df_base.merge(df_sup, on="SOT", how="left")
        df_base["SUPERVISOR"] = df_base.get("SUPERVISOR", "Sin Supervisor").fillna("Sin Supervisor").astype(str).str.strip()
        df_base.loc[df_base["SUPERVISOR"].eq(""), "SUPERVISOR"] = "Sin Supervisor"

        if filtro_supervisor != "Todos":
            df_base = df_base[df_base["SUPERVISOR"] == filtro_supervisor].copy()

        if df_base.empty: return pd.DataFrame(), pd.DataFrame(), ""

        if df_pago_raw.empty or "SOT" not in df_pago_raw.columns:
            df_base["APLICA_SEGUNDA_CAIDA"] = "NO ENCONTRADO"
            df_base["Estado Segunda Caída"] = "PENDIENTE"
            df_base["COMISION_RECUPERADA"] = 0.0
            df_base["FECHA_PAGO_3_MESES"] = ""
            return df_base.reset_index(drop=True), pd.DataFrame(), ""

        df_pago = df_pago_raw.copy()
        df_pago["SOT"] = _normalizar_sot_col(df_pago, "SOT")
        df_pago = df_pago[df_pago["SOT"] != ""].copy()

        col_fecha_pago = _obtener_fecha_preferida_fija(df_pago)

        col_aplica = encontrar_columna(df_pago, ["APLICA", "Aplica", "aplica"])
        if col_aplica:
            df_pago["APLICA_SEGUNDA_CAIDA"] = df_pago[col_aplica].apply(_normalizar_si_no)
        else:
            df_pago["APLICA_SEGUNDA_CAIDA"] = "NO"

        col_com_etapa = _obtener_columna_com_etapa(df_pago)
        if col_com_etapa:
            df_pago["COMISION_RECUPERADA"] = pd.to_numeric(df_pago[col_com_etapa], errors="coerce").fillna(0)
        else:
            df_pago["COMISION_RECUPERADA"] = 0.0

        if col_fecha_pago:
            df_pago["FECHA_PAGO_3_MESES"] = df_pago[col_fecha_pago].dt.strftime("%d/%m/%Y").fillna("")
        else:
            df_pago["FECHA_PAGO_3_MESES"] = ""

        df_pago["CRUZA_SEGUNDA_CAIDA"] = "SI"
        df_pago["PAGADO_3_MESES"] = df_pago["APLICA_SEGUNDA_CAIDA"].apply(lambda x: "SI" if x == "SI" else "NO")

        resumen_pago = df_pago.groupby("SOT", as_index=False).agg(
            COMISION_RECUPERADA=("COMISION_RECUPERADA", lambda x: float(pd.to_numeric(x, errors="coerce").fillna(0).sum())),
            FECHA_PAGO_3_MESES=("FECHA_PAGO_3_MESES", "first"),
            APLICA_SEGUNDA_CAIDA=("APLICA_SEGUNDA_CAIDA", lambda x: "SI" if (x.astype(str).str.upper().str.strip() == "SI").any() else "NO"),
            CRUZA_SEGUNDA_CAIDA=("CRUZA_SEGUNDA_CAIDA", "first")
        )
        resumen_pago["PAGADO_3_MESES"] = resumen_pago["APLICA_SEGUNDA_CAIDA"].apply(lambda x: "SI" if x == "SI" else "NO")

        df = df_base.merge(resumen_pago, on="SOT", how="left")
        df["COMISION_RECUPERADA"] = pd.to_numeric(df.get("COMISION_RECUPERADA", 0), errors="coerce").fillna(0)
        df["APLICA_SEGUNDA_CAIDA"] = df.get("APLICA_SEGUNDA_CAIDA", "").fillna("NO ENCONTRADO")
        df["PAGADO_3_MESES"] = df.get("PAGADO_3_MESES", "").fillna("NO")
        df["CRUZA_SEGUNDA_CAIDA"] = df.get("CRUZA_SEGUNDA_CAIDA", "").fillna("NO")
        df["FECHA_PAGO_3_MESES"] = df.get("FECHA_PAGO_3_MESES", "").fillna("")
        df["Estado Segunda Caída"] = df["PAGADO_3_MESES"].apply(
            lambda x: "PAGADA EN 3 MESES" if str(x).upper().strip() == "SI" else "PENDIENTE"
        )

        return df.reset_index(drop=True), df_pago.reset_index(drop=True), col_fecha_pago or ""
    except Exception as e:
        st.error(f"Error en F - COM.INDIRECTA 2da ETAPA: {e}")
        return pd.DataFrame(), pd.DataFrame(), ""

def _ordenar_columnas_segunda_caida(df):
    cols_prioridad = [
        "SOT", "SUPERVISOR", "Estado Segunda Caída", "CRUZA_SEGUNDA_CAIDA", "APLICA_SEGUNDA_CAIDA",
        "COMISION_RECUPERADA", "FECHA_PAGO_3_MESES", "FECHA INSTALACION", "FECHA GENERACION",
        "FECHA DE VENTA", "USUARIO", "ASESOR", "CLIENTE", "NOMBRE", "Nombre del Cliente"
    ]
    cols_show = [c for c in cols_prioridad if c in df.columns]
    resto = [c for c in df.columns if c not in cols_show]
    return df[cols_show + resto].copy()

def mostrar_segunda_caida_fija_dc():
    set_bg(img_dc)
    st.markdown('<div class="section-title-dc">F - COM.INDIRECTA 2da ETAPA</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-subtitle-dc">Cruce por SOT · CLARO_DC_FIJA vs CLARO_DC_FIJA_SEGUNDA_CAIDA · Supervisor desde FIJA_DC</div>', unsafe_allow_html=True)
    st.write("---")

    f1, f2 = st.columns(2)
    with f1:
        filtro_mes_base = st.selectbox(
            "Fecha instalación base",
            obtener_meses_fija("FECHA INSTALACION"),
            key="seg_caida_dc_mes_base"
        )
    with f2:
        filtro_supervisor = st.selectbox(
            "Supervisor",
            obtener_supervisores_segunda_caida_dc(filtro_mes_base),
            key="seg_caida_dc_supervisor"
        )

    df, df_pago_original, col_fecha_pago = construir_segunda_caida_fija_dc(filtro_mes_base, filtro_supervisor)

    if df.empty:
        st.warning("No se encontraron datos en CLARO_DC_FIJA para el cruce con los filtros seleccionados.")
        return

    # TABLAS FINALES DE EXPORTACIÓN / DETALLE
    # IMPORTANTE:
    # Estas son las MISMAS tablas que se usan para el botón Descargar.
    # El desplegable muestra estas variables para que el conteo visual cuadre
    # con el KPI y con el CSV descargado.
    if "SOT" in df.columns:
        base_export = df.drop_duplicates(subset=["SOT"]).reset_index(drop=True).copy()
    else:
        base_export = df.reset_index(drop=True).copy()

    pagadas_export = (
        base_export[base_export["Estado Segunda Caída"] == "PAGADA EN 3 MESES"]
        .drop_duplicates(subset=["SOT"] if "SOT" in base_export.columns else None)
        .reset_index(drop=True)
        .copy()
    )

    pendientes_export = (
        base_export[base_export["Estado Segunda Caída"] == "PENDIENTE"]
        .drop_duplicates(subset=["SOT"] if "SOT" in base_export.columns else None)
        .reset_index(drop=True)
        .copy()
    )

    total_base = int(base_export["SOT"].nunique()) if "SOT" in base_export.columns else int(len(base_export))
    pagadas = int(pagadas_export["SOT"].nunique()) if "SOT" in pagadas_export.columns else int(len(pagadas_export))
    pendientes = int(pendientes_export["SOT"].nunique()) if "SOT" in pendientes_export.columns else int(len(pendientes_export))

    pct_base = 100.00 if total_base > 0 else 0.00
    pct_recuperacion = (pagadas / total_base * 100) if total_base > 0 else 0
    pct_caida = (pendientes / total_base * 100) if total_base > 0 else 0
    comision_recuperada = pd.to_numeric(pagadas_export.get("COMISION_RECUPERADA", 0), errors="coerce").fillna(0).sum()

    st.markdown("### 📌 Indicadores Com.Indirecta 2da Etapa")
    st.caption("Los indicadores se calculan con los filtros aplicados y a nivel SOT único.")

    k1, k2, k3, k4, k5 = st.columns(5)
    _kpi_card_html(k1, "Base CLARO_DC_FIJA", f"{total_base:,}", "Efectividad base 100%", "#0f4287", "#0f4287")
    _kpi_card_html(k2, "Segunda Caída", f"{pagadas:,}", f"Alcance {pct_recuperacion:.2f}%", "#16a34a", "#16a34a")
    _kpi_card_html(k3, "Pendientes", f"{pendientes:,}", f"Caída {pct_caida:.2f}%", "#dc2626", "#dc2626")
    _kpi_card_html(k4, "COM ETAPA", formatear_moneda(comision_recuperada), "Comisión recuperada", "#7c3aed", "#7c3aed")
    _kpi_card_html(k5, "% Caída", f"{pct_caida:.2f}%", "Pendientes / Base", "#ea580c", "#ea580c")

    st.write("---")
    st.markdown("### 🔎 Detalle desplegable")
    st.caption("El desplegable muestra exactamente la misma base final que se descarga en CSV.")

    filtro_txt = f"Base: {filtro_mes_base} | Supervisor: {filtro_supervisor}"
    sufijo_supervisor = str(filtro_supervisor).replace(" ", "_").replace("/", "_")

    with st.expander(f"➕ 0 | Base CLARO_DC_FIJA | Clientes/SOT base: {total_base:,} | Efectividad: {pct_base:.2f}%", expanded=False):
        if base_export.empty:
            st.info("No hay clientes/SOT en la base con los filtros seleccionados.")
        else:
            base_show = _ordenar_columnas_segunda_caida(base_export.copy())
            st.dataframe(base_show, use_container_width=True, height=430)
            nombre_archivo = f"segunda_caida_fija_dc_base_{filtro_mes_base.replace(' ','_')}_{sufijo_supervisor}.csv"
            st.download_button(
                "⬇️ Descargar base CLARO_DC_FIJA",
                data=base_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=nombre_archivo,
                mime="text/csv",
                key="dl_segunda_caida_dc_base",
                on_click=registrar_descarga,
                args=("F - COM.INDIRECTA 2da ETAPA - Base", nombre_archivo, filtro_txt)
            )

    with st.expander(f"➕ 1 | Pagadas en 3 meses | Cruzan y APLICA = SI: {pagadas:,} | Alcance: {pct_recuperacion:.2f}% | COM ETAPA: {formatear_moneda(comision_recuperada)}", expanded=False):
        if pagadas_export.empty:
            st.info("No hay ventas pagadas en 3 meses con APLICA = SI para los filtros seleccionados.")
        else:
            pagadas_show = _ordenar_columnas_segunda_caida(pagadas_export.copy())
            st.dataframe(pagadas_show, use_container_width=True, height=430)
            nombre_archivo = f"segunda_caida_fija_dc_pagadas_aplica_si_{filtro_mes_base.replace(' ','_')}_{sufijo_supervisor}.csv"
            st.download_button(
                "⬇️ Descargar pagadas en 3 meses",
                data=pagadas_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=nombre_archivo,
                mime="text/csv",
                key="dl_segunda_caida_dc_pagadas",
                on_click=registrar_descarga,
                args=("F - COM.INDIRECTA 2da ETAPA - Pagadas Aplica SI", nombre_archivo, filtro_txt)
            )

    with st.expander(f"➕ 2 | Pendientes | No aparecen o APLICA = NO: {pendientes:,} | Caída: {pct_caida:.2f}%", expanded=False):
        if pendientes_export.empty:
            st.success("No hay pendientes con los filtros seleccionados.")
        else:
            pendientes_show = _ordenar_columnas_segunda_caida(pendientes_export.copy())
            st.dataframe(pendientes_show, use_container_width=True, height=430)
            nombre_archivo = f"segunda_caida_fija_dc_pendientes_{filtro_mes_base.replace(' ','_')}_{sufijo_supervisor}.csv"
            st.download_button(
                "⬇️ Descargar pendientes",
                data=pendientes_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=nombre_archivo,
                mime="text/csv",
                key="dl_segunda_caida_dc_pendientes",
                on_click=registrar_descarga,
                args=("F - COM.INDIRECTA 2da ETAPA - Pendientes", nombre_archivo, filtro_txt)
            )

    st.write("---")
    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,.92);border:1px solid #dbeafe;border-left:6px solid #0f4287;
        padding:14px 16px;border-radius:14px;color:#0f172a;font-size:13px;">
            <b>Lectura rápida:</b> Base: <b>{total_base:,}</b> · Supervisor: <b>{filtro_supervisor}</b> ·
            Pagadas APLICA = SI: <b>{pagadas:,}</b> · Pendientes: <b>{pendientes:,}</b> ·
            Alcance: <b>{pct_recuperacion:.2f}%</b> · Caída: <b>{pct_caida:.2f}%</b> ·
            COM ETAPA: <b>{formatear_moneda(comision_recuperada)}</b>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# HELPERS: Planes Fija (Productos - producto Especificacion)
# =========================================================
@st.cache_data(ttl=3600)
def obtener_planes_fija_develz():
    planes = set()
    for archivo in ["FIJA_DC.csv", "FIJA_TELETALK.csv"]:
        df = cargar_csv(archivo)
        if df.empty: continue
        col = None
        for c in df.columns:
            norm = c.lower().replace("ó","o").replace("á","a")
            if "producto" in norm and "especificacion" in norm:
                col = c; break
        if not col:
            for c in df.columns:
                norm = c.lower().replace("ó","o").replace("á","a")
                if "especificacion" in norm or "plan" in norm:
                    col = c; break
        if col:
            planes.update(df[col].dropna().astype(str).str.strip().replace(["nan","None",""],"").unique().tolist())
    return ["Todos"] + sorted(p for p in planes if p)

def _obtener_col_producto_tv_fija(df):
    """Columna 'Productos - producto' (clasificación INTERNET+TELEFONIA+AVANZADO/SUPERIOR, etc.).
    Distinta de 'Productos - producto Especificacion' (velocidad del plan)."""
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a").strip()
        if norm == "productos - producto":
            return c
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "productos" in norm and "producto" in norm and "especificacion" not in norm:
            return c
    return None

def _obtener_col_plan_fija_develz(df):
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "producto" in norm and "especificacion" in norm:
            return c
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "productos" in norm and "producto" in norm:
            return c
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "especificacion" in norm or "plan" in norm:
            return c
    return None

# Combinaciones de "Productos - producto" que cuentan como "TV" para el KPI % TV
_PLANES_TV = [
    "INTERNET + AVANZADO",
    "INTERNET + TELEFONIA + AVANZADO",
    "INTERNET + TELEFONIA + SUPERIOR",
    "INTERNET + SUPERIOR",
]

@st.cache_data(ttl=3600)
def _mapa_sot_plan_fija_develz():
    """Mapa SOT -> Plan (Productos - producto Especificacion) desde FIJA_DC y FIJA_TELETALK."""
    plan_map = {}
    for archivo in ["FIJA_DC.csv", "FIJA_TELETALK.csv"]:
        df_src = cargar_csv(archivo)
        if df_src.empty: continue
        col_sot = next((c for c in df_src.columns if "sot" in c.lower()), None)
        col_plan = _obtener_col_plan_fija_develz(df_src)
        if not col_sot or not col_plan: continue
        df_src = df_src.copy()
        df_src["_K"] = df_src[col_sot].fillna("").astype(str).str.strip().str.replace(r"\.0+$","",regex=True)
        df_src["_P"] = df_src[col_plan].fillna("Sin Plan").astype(str).str.strip().replace("","Sin Plan")
        for _, row in df_src[["_K","_P"]].iterrows():
            if row["_K"] and row["_K"] not in ["nan","None",""]:
                plan_map[row["_K"]] = row["_P"]
    return plan_map

@st.cache_data(ttl=3600)
def _mapa_sot_producto_tv_fija():
    """Mapa SOT -> Productos - producto (INTERNET+TELEFONIA, INTERNET+AVANZADO, etc.)
    desde FIJA_DC y FIJA_TELETALK. Usado para el KPI % TV."""
    prod_map = {}
    for archivo in ["FIJA_DC.csv", "FIJA_TELETALK.csv"]:
        df_src = cargar_csv(archivo)
        if df_src.empty: continue
        col_sot = next((c for c in df_src.columns if "sot" in c.lower()), None)
        col_prod = _obtener_col_producto_tv_fija(df_src)
        if not col_sot or not col_prod: continue
        df_src = df_src.copy()
        df_src["_K"] = df_src[col_sot].fillna("").astype(str).str.strip().str.replace(r"\.0+$","",regex=True)
        df_src["_P"] = df_src[col_prod].fillna("Sin Producto").astype(str).str.strip().replace("","Sin Producto")
        for _, row in df_src[["_K","_P"]].iterrows():
            if row["_K"] and row["_K"] not in ["nan","None",""]:
                prod_map[row["_K"]] = row["_P"]
    return prod_map

def calcular_pct_tv_fija(df_filtrado):
    """
    Calcula el % de ventas PAGADAS cuyo 'Productos - producto' (cruzado vía SOT desde
    FIJA_DC/FIJA_TELETALK) corresponde a alguna de las combinaciones con TV:
    INTERNET + AVANZADO, INTERNET + TELEFONIA + AVANZADO,
    INTERNET + TELEFONIA + SUPERIOR, INTERNET + SUPERIOR.
    KPI = Ventas Pagadas con TV / Ventas Pagadas.
    Retorna (pct_tv, ventas_tv, total_pagadas).
    """
    if df_filtrado is None or df_filtrado.empty:
        return 0.0, 0, 0
    if "Estado Pago" not in df_filtrado.columns or "SOT" not in df_filtrado.columns:
        return 0.0, 0, 0

    base_pagada = df_filtrado[df_filtrado["Estado Pago"] == "PAGADA"]
    total_pagadas = len(base_pagada)
    if total_pagadas == 0:
        return 0.0, 0, 0

    prod_map = _mapa_sot_producto_tv_fija()
    sot_clean = base_pagada["SOT"].fillna("").astype(str).str.strip().str.replace(r"\.0+$","",regex=True)
    prod_serie = sot_clean.map(lambda s: prod_map.get(s, "Sin Producto"))

    def _normalizar(s):
        s = str(s).upper().strip()
        s = s.replace("Í", "I").replace("í", "I")
        s = s.replace("Á", "A").replace("Ó", "O").replace("É", "E").replace("Ú", "U")
        s = re.sub(r"\s*\+\s*", " + ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    planes_tv_norm = {_normalizar(p) for p in _PLANES_TV}
    prod_norm = prod_serie.map(_normalizar)
    es_tv = prod_norm.isin(planes_tv_norm)

    ventas_tv = int(es_tv.sum())
    pct_tv = (ventas_tv / total_pagadas * 100) if total_pagadas > 0 else 0.0
    return pct_tv, ventas_tv, total_pagadas


def resumen_planes_fija_gerencial(df_filtrado):
    cols_salida = ["Plan","Canal","Total Ventas","Pagadas","Caídas","% Efectividad","Comisión Total"]
    if df_filtrado is None or df_filtrado.empty:
        return pd.DataFrame(columns=cols_salida)
    plan_map = {}
    for archivo, canal_ref in [("FIJA_DC.csv","D&C"),("FIJA_TELETALK.csv","Teletalk")]:
        df_src = cargar_csv(archivo)
        if df_src.empty: continue
        col_sot = next((c for c in df_src.columns if "sot" in c.lower()), None)
        col_plan = _obtener_col_plan_fija_develz(df_src)
        if not col_sot or not col_plan: continue
        df_src = df_src.copy()
        df_src["_K"] = df_src[col_sot].fillna("").astype(str).str.strip().str.replace(r"\.0+$","",regex=True)
        df_src["_P"] = df_src[col_plan].fillna("Sin Plan").astype(str).str.strip().replace("","Sin Plan")
        for _, row in df_src[["_K","_P"]].iterrows():
            if row["_K"] and row["_K"] not in ["nan","None",""]:
                plan_map[row["_K"]] = row["_P"]
    df_work = df_filtrado.copy()
    if "SOT" in df_work.columns:
        sot_clean = df_work["SOT"].fillna("").astype(str).str.strip().str.replace(r"\.0+$","",regex=True)
    else:
        sot_clean = pd.Series([""] * len(df_work), index=df_work.index)
    df_work["_Plan_G"] = sot_clean.map(lambda s: plan_map.get(s,"Sin Plan"))
    grupos = df_work.groupby(["_Plan_G","Canal"]).agg(
        Total_Ventas=("Estado Pago","count"),
        Pagadas=("Estado Pago", lambda x: (x=="PAGADA").sum()),
        Caidas=("Estado Pago", lambda x: (x=="CAÍDA").sum()),
        Comision=("COMISION", lambda x: pd.to_numeric(x,errors="coerce").fillna(0).sum()),
    ).reset_index().sort_values(["Pagadas","Total_Ventas"],ascending=[False,False]).reset_index(drop=True)
    grupos["% Efectividad"] = (grupos["Pagadas"]/grupos["Total_Ventas"]*100).round(2)
    grupos = grupos.rename(columns={"_Plan_G":"Plan","Total_Ventas":"Total Ventas","Caidas":"Caídas","Comision":"Comisión Total"})
    grupos["% Efectividad"] = grupos["% Efectividad"].apply(lambda x: f"{x:.2f}%")
    total_row = pd.DataFrame([{
        "Plan":"TOTAL","Canal":"",
        "Total Ventas":int(grupos["Total Ventas"].sum()),
        "Pagadas":int(grupos["Pagadas"].sum()),
        "Caídas":int(grupos["Caídas"].sum()),
        "% Efectividad": f"{(grupos['Pagadas'].sum()/grupos['Total Ventas'].sum()*100):.2f}%" if grupos["Total Ventas"].sum()>0 else "0%",
        "Comisión Total":float(grupos["Comisión Total"].sum()),
    }])
    return pd.concat([grupos[cols_salida], total_row[cols_salida]], ignore_index=True)

def mostrar_tab_planes_fija_gerencial(df_filtrado, color_borde="#0f4287"):
    st.markdown("### 📦 Resumen Gerencial por Plan")
    st.caption("Clasificación por Plan contratado (Productos - producto Especificacion) · Datos cruzados desde FIJA_DC y FIJA_TELETALK")
    planes_disp = obtener_planes_fija_develz()
    c_f1, _ = st.columns([2,1])
    with c_f1:
        filtro_plan = st.selectbox("Filtrar por Plan", planes_disp, key="fija_gen_plan_filtro")
    resumen = resumen_planes_fija_gerencial(df_filtrado)
    if resumen.empty:
        st.warning("No se encontraron datos de planes. Verifica que FIJA_DC.csv y FIJA_TELETALK.csv contengan la columna 'Productos - producto Especificacion'.")
        return
    df_show = resumen.copy()
    if filtro_plan != "Todos":
        df_show = df_show[(df_show["Plan"]==filtro_plan)|(df_show["Plan"]=="TOTAL")]
    base_sin_total = df_show[df_show["Plan"]!="TOTAL"]
    k1,k2,k3,k4 = st.columns(4)
    def _mc(col, label, valor, color):
        with col:
            st.markdown(f'''<div style="background:rgba(255,255,255,.96);padding:14px;border-radius:16px;
            border:2px solid {color};text-align:center;margin-bottom:10px;">
            <span style="color:#4b5563;font-weight:800;font-size:10px;text-transform:uppercase;letter-spacing:.1em;display:block;margin-bottom:6px;">{label}</span>
            <span style="color:{color};font-size:26px;font-weight:950;display:block;">{valor}</span>
            </div>''', unsafe_allow_html=True)
    _mc(k1,"Planes únicos",f"{int(base_sin_total['Plan'].nunique()):,}",color_borde)
    _mc(k2,"Total Ventas",f"{int(base_sin_total['Total Ventas'].sum()):,}",color_borde)
    _mc(k3,"Pagadas",f"{int(base_sin_total['Pagadas'].sum()):,}","#059669")
    _mc(k4,"Comisión",formatear_moneda(float(pd.to_numeric(base_sin_total['Comisión Total'],errors='coerce').fillna(0).sum())),"#0891b2")
    st.write("")
    base_chart = base_sin_total.sort_values("Total Ventas",ascending=False).head(15).copy()
    if not base_chart.empty:
        try:
            import altair as alt
            chart_melt = base_chart.melt(id_vars=["Plan","Canal"],value_vars=["Total Ventas","Pagadas"],var_name="Indicador",value_name="Cantidad")
            chart = (alt.Chart(chart_melt).mark_bar(cornerRadiusEnd=6,opacity=.92)
                .encode(
                    x=alt.X("Cantidad:Q",title="Ventas"),
                    y=alt.Y("Plan:N",sort="-x",title=""),
                    color=alt.Color("Indicador:N",scale=alt.Scale(domain=["Total Ventas","Pagadas"],range=["#0f4287","#059669"]),legend=alt.Legend(title="Estado",orient="top-right")),
                    tooltip=["Plan","Canal","Indicador","Cantidad"]
                ).properties(height=max(280,len(base_chart)*38),title="Top Planes por Volumen de Ventas")
                .configure_title(fontSize=16,fontWeight="bold",color=color_borde))
            st.altair_chart(chart,use_container_width=True)
        except Exception: pass
    df_display = df_show.copy()
    df_display["Comisión Total"] = df_display["Comisión Total"].apply(lambda x: formatear_moneda(x) if isinstance(x,(int,float)) else x)
    def _cp(val):
        try:
            v=float(val); mx=float(pd.to_numeric(base_sin_total["Pagadas"],errors="coerce").fillna(0).max())
            a=0.08+min(v/mx,1)*.28 if mx>0 else 0.08
            return f"background-color:rgba(5,150,105,{a});color:#064e3b;font-weight:800;text-align:center;"
        except: return "text-align:center;"
    def _cc(val):
        try:
            v=float(val); mx=float(pd.to_numeric(base_sin_total["Caídas"],errors="coerce").fillna(0).max())
            a=0.06+min(v/mx,1)*.22 if mx>0 else 0.06
            return f"background-color:rgba(220,38,38,{a});color:#7f1d1d;font-weight:800;text-align:center;"
        except: return "text-align:center;"
    def _rt(row):
        if str(row.get("Plan","")).upper()=="TOTAL": return [f"background-color:{color_borde};color:white;font-weight:900;" for _ in row]
        return [""for _ in row]
    st.markdown("#### 📋 Tabla Gerencial por Plan")
    st.dataframe(
        df_display.style.apply(_rt,axis=1).map(_cp,subset=["Pagadas"]).map(_cc,subset=["Caídas"])
        .set_properties(**{"text-align":"center","font-size":"13px"})
        .set_properties(subset=["Plan"],**{"text-align":"left","font-weight":"bold"}),
        use_container_width=True, height=min(680,90+36*len(df_display))
    )
    st.download_button("⬇️ Descargar Resumen Planes Fija",
        data=df_show.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="resumen_planes_fija.csv",mime="text/csv",key="dl_planes_fija_gerencial")

def mostrar_detalle_fija_general():
    color_titulo = "#004a99"; color_borde = "#0f4287"
    set_bg(img_caratula)
    st.markdown(f'<div style="color:{color_titulo};font-size:34px;font-weight:900;margin-bottom:4px;">Detalle FIJA General</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{color_titulo};font-weight:800;font-size:16px;margin-bottom:16px;">D&C + TELETALK · BASE DEVELZ COMPLETA · CAÍDA REAL · PAGADA VS CAÍDA</div>', unsafe_allow_html=True)
    st.write("---")

    # ── Carga única en session_state (no recarga por cada widget) ──────────────
    if "dfg_det_cache" not in st.session_state:
        with st.spinner("Cargando base DEVELZ + cruce CLARO... (solo la primera vez)"):
            _df = construir_detalle_fija_general("Todos los meses", "Todos los meses")
            if "Documento" not in _df.columns: _df["Documento"] = ""
            if "TIPIS" in _df.columns:
                _df["TIPIS"] = _df["TIPIS"].fillna("Sin TIPIS").astype(str).str.strip()
                _df.loc[_df["TIPIS"].eq(""), "TIPIS"] = "Sin TIPIS"
            else: _df["TIPIS"] = "Sin TIPIS"
            # Precalcular columnas de mes para filtrado vectorizado (sin .apply fila a fila)
            for _c, _key in [("FECHA INSTALACION","_MES_INST"), ("FECHA DE VENTA","_MES_VENTA")]:
                if _c in _df.columns:
                    _dt = pd.to_datetime(_df[_c], dayfirst=True, errors="coerce")
                    _df[_key] = _dt.apply(lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")
                else:
                    _df[_key] = ""
            st.session_state["dfg_det_cache"] = _df

    df_det = st.session_state["dfg_det_cache"]
    # ── Invalidar cache si le faltan las columnas de mes precalculadas ──────
    if "_MES_INST" not in df_det.columns or "_MES_VENTA" not in df_det.columns:
        del st.session_state["dfg_det_cache"]; st.rerun()
    if df_det.empty:
        st.warning("No se encontraron datos. Verifica que FIJA_DC.csv, FIJA_TELETALK.csv y los archivos Claro esten en la carpeta correcta.")
        if st.button("Reintentar carga", key="dfg_retry"):
            del st.session_state["dfg_det_cache"]; st.rerun()
        return

    opts_inst  = [m for m in obtener_meses_fija("FECHA INSTALACION") if m != "Todos los meses"]
    opts_venta = [m for m in obtener_meses_fija_develz("FECHA DE VENTA") if m != "Todos los meses"]

    col_f1,col_f2,col_f3,col_f4 = st.columns([1.2,1.2,1.0,1.1])
    with col_f1: filtro_mes         = st.multiselect("Fecha de Instalacion", opts_inst,  default=[], placeholder="Todos los meses", key="det_general_mes")
    with col_f2: filtro_fecha_venta = st.multiselect("Fecha de Venta",       opts_venta, default=[], placeholder="Todos los meses", key="det_general_fecha_venta")
    with col_f3: filtro_canal       = st.selectbox("Canal",          ["Todos","D&C","Teletalk"], key="det_general_canal")
    with col_f4: filtro_estado      = st.selectbox("Estado de Pago", ["Todos","PAGADA","CAÍDA"], key="det_general_estado")

    col_f5,col_f6,col_f7,col_f8 = st.columns([1.3,1.4,1.1,0.7])
    with col_f5: filtro_supervisor   = st.multiselect("Supervisor", sorted(df_det["SUPERVISOR"].fillna("Sin Supervisor").unique().tolist()), default=[], placeholder="Todos los supervisores", key="det_general_supervisor")
    with col_f6: filtro_tipificacion = st.selectbox("Tipificacion", ["Todos"] + sorted(df_det["TIPIS"].fillna("Sin TIPIS").astype(str).unique().tolist()), key="det_general_tipificacion")
    with col_f7:
        colas_disponibles = sorted(df_det["COLA"].fillna("EXTERNO").unique().tolist()) if "COLA" in df_det.columns else []
        filtro_cola = st.selectbox("Cola", ["Todos"] + colas_disponibles, key="det_general_cola")
    with col_f8:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refrescar datos", key="dfg_refresh", help="Fuerza recarga desde los CSV"):
            del st.session_state["dfg_det_cache"]; st.rerun()

    # ── Filtrado vectorizado (rápido, sin .apply fila a fila) ───────────────────
    df_filtrado = df_det

    if filtro_mes:
        # Fuente de verdad: SOTs instalados en el mes según CLARO.
        # Filtramos DEVELZ por esos SOTs para que la tabla muestre exactamente
        # las ventas instaladas en el mes, igual que la lógica de los KPIs.
        _sots_claro_inst = set()
        for _archivo_claro in ["CLARO_DC_FIJA.csv", "CLARO_TELETALK_FIJA.csv"]:
            if filtro_canal == "D&C" and "TELETALK" in _archivo_claro: continue
            if filtro_canal == "Teletalk" and _archivo_claro == "CLARO_DC_FIJA.csv": continue
            _df_c = preparar_fechas_fija(cargar_csv(_archivo_claro))
            if _df_c.empty: continue
            if "FECHA INSTALACION" in _df_c.columns:
                _df_c["_MES_CLARO"] = _df_c["FECHA INSTALACION"].apply(
                    lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else ""
                )
                _df_c = _df_c[_df_c["_MES_CLARO"].isin(filtro_mes)].copy()
            _col_sot_claro = next((c for c in _df_c.columns if c.strip().upper() == "SOT"), None)
            if _col_sot_claro:
                _sots_claro_inst.update(
                    _normalizar_sot_series(_df_c[_col_sot_claro].fillna("").astype(str)).tolist()
                )
        _sots_claro_inst.discard("")
        if _sots_claro_inst:
            df_filtrado = df_filtrado[df_filtrado["SOT"].isin(_sots_claro_inst)]
        else:
            # Fallback: si CLARO no devuelve nada, filtrar por _MES_INST de DEVELZ
            df_filtrado = df_filtrado[df_filtrado["_MES_INST"].isin(filtro_mes)]

    if filtro_fecha_venta:  df_filtrado = df_filtrado[df_filtrado["_MES_VENTA"].isin(filtro_fecha_venta)]
    if filtro_canal   != "Todos": df_filtrado = df_filtrado[df_filtrado["Canal"]       == filtro_canal]
    if filtro_estado  != "Todos": df_filtrado = df_filtrado[df_filtrado["Estado Pago"] == filtro_estado]
    if filtro_supervisor:          df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(filtro_supervisor)]
    if filtro_tipificacion != "Todos": df_filtrado = df_filtrado[df_filtrado["TIPIS"]  == filtro_tipificacion]
    if filtro_cola != "Todos" and "COLA" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["COLA"] == filtro_cola]
    df_filtrado = df_filtrado.copy()

    total, pagadas, caidas, comision, pct = kpi_detalle_fija(df_filtrado)

    # ── Cuando hay filtro de Fecha de Instalación: Pagadas y Comisión
    #    vienen directamente de CLARO_DC_FIJA + CLARO_TELETALK_FIJA
    #    filtrando por FECHA INSTALACION del mes seleccionado y COMISIONES == SI  ─────
    if filtro_mes:
        _claro_total    = 0
        _claro_pagadas  = 0
        _claro_comision = 0.0
        for _archivo_claro in ["CLARO_DC_FIJA.csv", "CLARO_TELETALK_FIJA.csv"]:
            # Filtrar por canal si corresponde
            if filtro_canal == "D&C" and "TELETALK" in _archivo_claro: continue
            if filtro_canal == "Teletalk" and _archivo_claro == "CLARO_DC_FIJA.csv": continue
            _df_c = preparar_fechas_fija(cargar_csv(_archivo_claro))
            if _df_c.empty: continue
            # Filtrar por los meses de instalación seleccionados
            if "FECHA INSTALACION" in _df_c.columns:
                _df_c["_MES_CLARO"] = _df_c["FECHA INSTALACION"].apply(
                    lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else ""
                )
                _df_c = _df_c[_df_c["_MES_CLARO"].isin(filtro_mes)].copy()
            # Deduplicar por SOT única antes de contar
            _col_sot_claro = next((c for c in _df_c.columns if c.strip().upper() == "SOT"), None)
            if _col_sot_claro:
                _df_c = _df_c.drop_duplicates(subset=[_col_sot_claro]).copy()
            # Total Ventas = SOTs únicas del mes
            _claro_total += len(_df_c)
            # Filtrar solo las que tienen COMISIONES == SI
            _col_com = next((c for c in _df_c.columns if c.strip().upper() == "COMISIONES"), None)
            if _col_com:
                _mask_si = _df_c[_col_com].fillna("").astype(str).str.strip().str.upper() == "SI"
                _df_pagadas_claro = _df_c[_mask_si].copy()
            else:
                _df_pagadas_claro = _df_c.copy()
            _claro_pagadas += len(_df_pagadas_claro)
            # Sumar comisión de esas filas (ya sin duplicados)
            _col_monto = next((c for c in _df_pagadas_claro.columns
                               if c.strip().upper() in ["COMISION","COMISIÓN","MONTO","COM ETAPA"]), None)
            if _col_monto:
                _claro_comision += pd.to_numeric(_df_pagadas_claro[_col_monto], errors="coerce").fillna(0).sum()
        # Reemplazar KPIs con los valores CLARO cuando hay filtro de instalación
        total    = _claro_total
        pagadas  = _claro_pagadas
        comision = _claro_comision
        caidas   = total - pagadas
        pct      = (pagadas / total * 100) if total > 0 else 0.0

    ticket_promedio_fija = (comision / pagadas) if pagadas > 0 else 0.0
    pct_tv, ventas_tv, _total_tv = calcular_pct_tv_fija(df_filtrado)
    st.markdown("### Resumen General")
    k1,k2,k3,k4,k5,k6,k7 = st.columns(7)
    _kpi_card_html(k1,"Total Ventas",  f"{total:,}",          "Base CLARO (mes inst.)" if filtro_mes else "Base DEVELZ",   color_borde, color_borde)
    _kpi_card_html(k2,"Pagadas",       f"{pagadas:,}",         "Cruza con Claro" if filtro_mes else "Cruza con Claro","#059669","#059669")
    _kpi_card_html(k3,"No Pagadas" if filtro_mes else "Caídas", f"{caidas:,}", "Total - Pagadas" if filtro_mes else "Sin pago / sin SOT","#dc2626","#dc2626")
    _kpi_card_html(k4,"Comisión Total",formatear_moneda(comision),"Desde CLARO (mes inst.)" if filtro_mes else "Pagada", color_borde, color_borde)
    _kpi_card_html(k5,"% TV", f"{pct_tv:.2f}%", f"{ventas_tv:,} pagadas con TV", "#7c3aed", "#7c3aed")
    _kpi_card_html(k6,"% Efectividad", f"{pct:.2f}%",          "Pagadas / Total",color_borde,"#059669" if pct>=75 else "#d97706")
    _kpi_card_html(k7,"Promedio Prime",formatear_moneda(ticket_promedio_fija),"Comisión Total / Pagadas", "#0891b2", "#0891b2")
    st.write("---")

    tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs(["📋 Detalle Ventas","📆 Ventas por Día","🏆 Ranking Supervisor","👥 Ranking Asesores","📍 Ranking Departamentos","📊 Estados Operativos","📦 Por Planes"])

    with tab1:
        st.markdown("#### Detalle de ventas DEVELZ con estado final")
        def _colorear_estado(val):
            if val == "PAGADA": return "background-color:#dcfce7;color:#166534;font-weight:700"
            if val == "CAÍDA":  return "background-color:#fee2e2;color:#991b1b;font-weight:700"
            return ""
        cols_mostrar = ["Canal","SOT","Documento","SUPERVISOR","ASESOR","Nombre del Cliente","Departamento",
                        "FECHA INSTALACION","FECHA DE VENTA","TIPIS","Estado Operativo","COMISION","Estado Pago","COLA"]
        for col in cols_mostrar:
            if col not in df_filtrado.columns: df_filtrado[col] = ""
        df_show = df_filtrado[cols_mostrar].copy()
        df_show["COMISION"] = pd.to_numeric(df_show["COMISION"], errors="coerce").fillna(0).map(formatear_moneda)
        st.dataframe(df_show.style.map(_colorear_estado, subset=["Estado Pago"]), use_container_width=True, height=450)
        _lbl_inst  = "-".join(filtro_mes)         if filtro_mes         else "todos"
        _lbl_venta = "-".join(filtro_fecha_venta) if filtro_fecha_venta else "todos"
        _nombre_csv = f"detalle_fija_develz_{_lbl_inst.replace(' ','_')}_venta_{_lbl_venta.replace(' ','_')}_{filtro_canal}.csv"
        csv_export = df_filtrado.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("⬇️ Descargar CSV completo", data=csv_export,
            file_name=_nombre_csv, mime="text/csv", key="dl_det_general",
            on_click=registrar_descarga,
            args=("Detalle Fija General", _nombre_csv, f"Instalacion: {_lbl_inst} | Venta: {_lbl_venta} | Canal: {filtro_canal}"))
        mostrar_claro_pagado_no_develz(filtro_mes, filtro_canal)

    with tab2:
        st.markdown("#### Ventas por día — Total vs Pagadas")
        df_dia = ventas_por_dia_df(df_filtrado)
        if df_dia.empty:
            st.warning("No hay fechas válidas para mostrar ventas por día.")
        else:
            if not filtro_mes or len(filtro_mes) != 1:
                df_tmp = df_filtrado.copy()
                df_tmp["_FECHA_GRAFICO"] = pd.to_datetime(df_tmp["FECHA INSTALACION"], errors="coerce", dayfirst=True)
                hoy = pd.Timestamp.today().normalize()
                df_tmp = df_tmp[(df_tmp["_FECHA_GRAFICO"] >= pd.Timestamp("2020-01-01")) & (df_tmp["_FECHA_GRAFICO"] <= hoy)].copy()
                if df_tmp.empty:
                    st.warning("No hay fechas válidas para mostrar el gráfico por mes.")
                else:
                    df_chart = df_tmp.groupby(df_tmp["_FECHA_GRAFICO"].dt.to_period("M")).agg(
                        **{"Total Ventas":("Estado Pago","count"),
                           "Pagadas":("Estado Pago", lambda x: (x=="PAGADA").sum()),
                           "Caidas":("Estado Pago",  lambda x: (x=="CAÍDA").sum()),
                           "Comision":("COMISION",   lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())}
                    ).reset_index()
                    df_chart["Fecha_dt"]  = df_chart["_FECHA_GRAFICO"].dt.to_timestamp()
                    df_chart["Fecha"]     = df_chart["Fecha_dt"].dt.strftime("%m/%y")
                    df_chart["% Efectividad"] = (df_chart["Pagadas"]/df_chart["Total Ventas"]*100).round(2).astype(str)+"%"
                    chart_melt = df_chart.melt(id_vars=["Fecha_dt","Fecha"], value_vars=["Total Ventas","Pagadas"],
                                               var_name="Indicador", value_name="Cantidad")
                    chart_melt = chart_melt.rename(columns={"Fecha":"Fecha"})
                    st.altair_chart(_grafico_barras_agrupado(chart_melt, df_chart["Fecha"].tolist(), "Mes", bar_size=32), use_container_width=True)
                    tabla_dia = df_chart[["Fecha","Total Ventas","Pagadas","Caidas","Comision","% Efectividad"]].copy()
                    tabla_dia = tabla_dia.rename(columns={"Fecha":"Mes"})
                    tabla_dia["Comision"] = pd.to_numeric(tabla_dia["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
                    total_row = pd.DataFrame([{"Mes":"TOTAL","Total Ventas":tabla_dia["Total Ventas"].sum(),
                        "Pagadas":tabla_dia["Pagadas"].sum(),"Caidas":tabla_dia["Caidas"].sum(),
                        "Comision":formatear_moneda(pd.to_numeric(df_chart["Comision"], errors="coerce").fillna(0).sum()),
                        "% Efectividad":f"{(tabla_dia['Pagadas'].sum()/tabla_dia['Total Ventas'].sum()*100):.2f}%" if tabla_dia["Total Ventas"].sum()>0 else "0%"}])
                    st.markdown("#### Tabla mensual")
                    st.dataframe(pd.concat([tabla_dia,total_row],ignore_index=True), use_container_width=True, height=420)
            else:
                chart_base = df_dia.copy()
                chart_base["Fecha"] = pd.to_datetime(chart_base["Fecha"])
                chart_base["Fecha_txt"] = chart_base["Fecha"].dt.strftime("%d/%m")
                # ✅ CORRECCIÓN: Altair/Narwhals no acepta columnas duplicadas.
                # Antes se enviaba Fecha y Fecha_txt, luego Fecha_txt se renombraba a Fecha,
                # quedando 2 columnas llamadas Fecha. Aquí usamos solo la fecha visible del gráfico.
                chart_melt = chart_base.melt(id_vars=["Fecha_txt"], value_vars=["Total Ventas","Pagadas"],
                                             var_name="Indicador", value_name="Cantidad")
                chart_melt = chart_melt.rename(columns={"Fecha_txt":"Fecha"})
                chart_melt = chart_melt.loc[:, ~chart_melt.columns.duplicated()].copy()
                st.altair_chart(_grafico_barras_agrupado(chart_melt, chart_base["Fecha_txt"].tolist(), "Fecha"), use_container_width=True)
                tabla_dia = df_dia.copy()
                tabla_dia["Fecha"] = pd.to_datetime(tabla_dia["Fecha"]).dt.strftime("%d/%m/%Y")
                tabla_dia["Comision"] = pd.to_numeric(tabla_dia["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
                total_row = pd.DataFrame([{"Fecha":"TOTAL","Total Ventas":tabla_dia["Total Ventas"].sum(),
                    "Pagadas":tabla_dia["Pagadas"].sum(),"Caidas":tabla_dia["Caidas"].sum(),
                    "Comision":formatear_moneda(pd.to_numeric(df_dia["Comision"], errors="coerce").fillna(0).sum()),
                    "% Efectividad":f"{(tabla_dia['Pagadas'].sum()/tabla_dia['Total Ventas'].sum()*100):.2f}%" if tabla_dia["Total Ventas"].sum()>0 else "0%"}])
                st.markdown("#### Tabla diaria")
                st.dataframe(pd.concat([tabla_dia,total_row],ignore_index=True), use_container_width=True, height=420)

    with tab3:
        st.markdown("#### 🏆 Ranking Supervisor")
        mostrar_ranking_supervisores_con_asesores(df_filtrado)

    with tab4:
        st.markdown("#### 👥 Ranking Asesores")
        ranking_asesores = ranking_asesores_fija_develz(df_filtrado)
        if ranking_asesores.empty:
            st.warning("No se encontraron datos para el ranking de asesores.")
        else:
            st.dataframe(
                ranking_asesores.style.format({"Comision": lambda x: formatear_moneda(x) if isinstance(x, (int, float)) else x})
                .set_properties(**{"text-align":"center"})
                .set_properties(subset=["ASESOR"], **{"text-align":"left"}),
                use_container_width=True,
                height=460
            )

    with tab5:
        mostrar_ranking_departamentos_premium(df_filtrado)

    with tab6:
        st.markdown("#### 📊 Estados Operativos")
        estados_df = estados_operativos_df(df_filtrado)
        if estados_df.empty: st.warning("No se encontraron datos de TIPIS.")
        else:
            col_e1, col_e2 = st.columns([1, 1.5])
            with col_e1: st.table(estados_df)
            with col_e2:
                if "TIPIS" in df_filtrado.columns:
                    for estado_grupo in ["Conforme","1era Caída","2da Caída","Ejecución","Otros","Sin TIPIS"]:
                        df_grupo = df_filtrado[df_filtrado["Estado Operativo"] == estado_grupo]
                        if df_grupo.empty: continue
                        tipis_count = df_grupo["TIPIS"].fillna("Sin TIPIS").replace("","Sin TIPIS").value_counts().reset_index()
                        tipis_count.columns = ["TIPIS","Cantidad"]
                        with st.expander(f"{estado_grupo}  ({len(df_grupo)} ventas)", expanded=False):
                            st.table(tipis_count)

    with tab7:
        mostrar_tab_planes_fija_gerencial(df_filtrado, color_borde="#0f4287")

# =========================================================
# =========================================================
# =========================================================
# =========================================================
# LÓGICA FINAL:
# - La BASE es CLARO_TELETALK_MOVIL.csv.
# - En la BASE el número está en la columna TELEFONO.
# - La 2DA CAÍDA es CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv.
# - La 3RA CAÍDA es CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv.
# - El universo SIEMPRE es la BASE CLARO_TELETALK_MOVIL.csv.
# - Base Pagados se cuenta desde CLARO_TELETALK_MOVIL.csv.
# - 2da caída = clientes de la BASE cuyo DNI CLIENTE cruza con DNI RUC de CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv y COMISION > 0.
# - 3ra caída = clientes de la BASE cuyo DNI CLIENTE cruza con DNI RUC de CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv y COMISION > 0.
# - Fecha de Venta:
#   * Base Pagados y 2da Caída se filtran con la fecha de la BASE CLARO_TELETALK_MOVIL.csv.
#   * 3ra Caída se filtra con FEC ACTIV CTR del archivo CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv.
# - Se cuenta por líneas/registros, no por clientes únicos.
# - Se eliminan las tarjetas adicionales dentro del tab; queda solo tabla + gráfico.

ARCHIVOS_TELETALK_MOVIL_CAIDAS = [
    {
        "archivo": "CLARO_TELETALK_MOVIL.csv",
        "etapa": "Base Pagados",
        "orden": 1,
        "descripcion": "Base principal pagada",
        "columnas_numero": ["TELEFONO", "TELÉFONO", "Telefono", "Teléfono", "NUMERO", "NÚMERO", "MSISDN"],
    },
    {
        "archivo": "CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv",
        "etapa": "2da Caída - 3 meses",
        "orden": 2,
        "descripcion": "Números pagados a 3 meses",
        "columnas_numero": ["MSISDN", "TELEFONO", "TELÉFONO", "Telefono", "Teléfono", "NUMERO", "NÚMERO"],
    },
    {
        "archivo": "CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv",
        "etapa": "3ra Caída - 6 meses",
        "orden": 3,
        "descripcion": "Números pagados a 6 meses",
        "columnas_numero": ["MSISDN", "TELEFONO", "TELÉFONO", "Telefono", "Teléfono", "NUMERO", "NÚMERO"],
    },
]

def _limpiar_numero_movil(serie):
    s = (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
    )
    return s.replace(["", "nan", "NaN", "None", "NONE", "null", "NULL"], pd.NA)

def _limpiar_documento_movil(serie):
    s = (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
    )
    return s.replace(["", "nan", "NaN", "None", "NONE", "null", "NULL"], pd.NA)

def _obtener_documento_por_columnas(df, posibles):
    col = encontrar_columna(df, posibles)
    if col: return _limpiar_documento_movil(df[col]), col
    return pd.Series([pd.NA] * len(df), index=df.index), ""

def _obtener_numero_por_columnas(df, posibles):
    col = encontrar_columna(df, posibles)
    if col: return _limpiar_numero_movil(df[col]), col
    return pd.Series([pd.NA] * len(df), index=df.index), ""

def _obtener_fecha_teletalk_movil(df):
    col = encontrar_columna(df, [
        # ✅ Para CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv el filtro de Fecha de Venta
        # debe salir de FEC ACTIV CTR. Se coloca primero para darle prioridad.
        "FEC ACTIV CTR", "FEC. ACTIV CTR", "FECHA ACTIV CTR", "FECHA ACTIVACION CTR",
        "FECHA ACTIVACIÓN CTR", "Fec Activ Ctr", "FEC ACTIVACIÓN CTR",
        "FECHA OPERACION", "FECHA OPERACIÓN",
        "FECHA CARGA", "FECHA VENTA",
        "Fecha Operacion", "Fecha Operación",
        "Fecha Carga", "Fecha Venta"
    ])
    if col: return pd.to_datetime(df[col], errors="coerce", dayfirst=True), col
    return pd.Series(pd.NaT, index=df.index), ""

def _obtener_campo_movil_seguro(df, posibles, defecto="Sin datos"):
    col = encontrar_columna(df, posibles)
    if col: return df[col].fillna(defecto).astype(str).str.strip().replace("", defecto)
    return pd.Series([defecto] * len(df), index=df.index)

def _obtener_cliente_movil_teletalk(df):
    col_cliente = encontrar_columna(df, [
        "CLIENTE", "Cliente", "NOMBRE CLIENTE", "Nombre Cliente",
        "NOMBRE", "Nombre", "Nombre del Cliente"
    ])
    if col_cliente: return df[col_cliente].fillna("Sin Cliente").astype(str).str.strip().replace("", "Sin Cliente")

    nombre = _obtener_campo_movil_seguro(df, ["Cliente - Nombre", "NOMBRE"], "")
    apepat = _obtener_campo_movil_seguro(df, ["Cliente - Apellido Paterno", "APELLIDO PATERNO"], "")
    apemat = _obtener_campo_movil_seguro(df, ["Cliente - Apellido Materno", "APELLIDO MATERNO"], "")
    return (nombre + " " + apepat + " " + apemat).str.strip().replace("", "Sin Cliente")

def _obtener_numero_movil(df, posibles):
    col = encontrar_columna(df, posibles)
    if col: return pd.to_numeric(df[col], errors="coerce").fillna(0)
    return pd.Series([0.0] * len(df), index=df.index)

def _preparar_archivo_teletalk_movil(item):
    nombre_archivo = item["archivo"]
    etapa = item["etapa"]
    orden = item["orden"]
    descripcion = item["descripcion"]
    columnas_numero = item["columnas_numero"]

    cols_salida = [
        "Etapa", "Orden", "Archivo", "Descripción",
        "NUMERO_LINEA", "COLUMNA_NUMERO",
        "FECHA_ORIGINAL", "FECHA_BASE",
        "ASESOR", "Cliente", "Documento",
        "Departamento", "Transaccion", "Plan", "CF",
        "DIAS PORTADAS", "COMISION", "Estado Pago"
    ]

    df = cargar_csv(nombre_archivo)
    if df.empty: return pd.DataFrame(columns=cols_salida + ["_FECHA_ORIGINAL_DT", "_FECHA_BASE_DT"])

    df = df.copy()

    numero, col_numero = _obtener_numero_por_columnas(df, columnas_numero)
    fecha_dt, _ = _obtener_fecha_teletalk_movil(df)

    df["NUMERO_LINEA"] = numero
    df["COLUMNA_NUMERO"] = col_numero if col_numero else "NO ENCONTRADA"

    df["_FECHA_ORIGINAL_DT"] = fecha_dt
    df["_FECHA_BASE_DT"] = fecha_dt

    df["FECHA_ORIGINAL"] = df["_FECHA_ORIGINAL_DT"].dt.strftime("%d/%m/%Y").fillna("Sin fecha")
    df["FECHA_BASE"] = df["_FECHA_BASE_DT"].dt.strftime("%d/%m/%Y").fillna("Sin fecha")

    df["Etapa"] = etapa
    df["Orden"] = orden
    df["Archivo"] = nombre_archivo
    df["Descripción"] = descripcion

    df["Documento"] = _obtener_campo_movil_seguro(df, [
        "DNI CLIENTE", "DNI RUC", "DNI", "RUC", "DOCUMENTO", "NRO DOCUMENTO", "NRO. DOCUMENTO"
    ], "")

    df["ASESOR"] = _obtener_campo_movil_seguro(df, [
        "USUARIO", "ASESOR", "VENDEDOR", "DISTRIBUIDOR",
        "EJECUTIVO", "CREADOR", "Usuario", "Asesor"
    ], "Sin Asesor")

    df["Cliente"] = _obtener_cliente_movil_teletalk(df)

    df["Departamento"] = _obtener_campo_movil_seguro(df, [
        "DEPARTAMENTO", "Departamento", "departamento",
        "DPTO", "REGION", "REGIÓN", "Región",
        "Datos Instalación - Departamento",
        "Datos Instalacion - Departamento"
    ], "Sin Departamento")

    df["Transaccion"] = _obtener_campo_movil_seguro(df, [
        "TRANSACCION", "TRANSACCIÓN", "Transaccion", "Transacción",
        "TIPO TRANSACCION", "TIPO DE VENTA", "Tipo Transaccion"
    ], "Sin Transacción")

    df["Plan"] = _obtener_campo_movil_seguro(df, [
        "PLAN", "Plan", "PRODUCTO", "Producto", "SERVICIO", "Servicio"
    ], "Sin Plan")

    df["CF"] = _obtener_numero_movil(df, ["CF", "Cargo Fijo", "CARGO FIJO"])
    df["DIAS PORTADAS"] = _obtener_numero_movil(df, ["DIAS PORTADAS", "DÍAS PORTADAS", "Dias Portadas"])

    df["COMISION"] = obtener_comision_movil(df)
    df["Estado Pago"] = "PAGADA"

    return df[cols_salida + ["_FECHA_ORIGINAL_DT", "_FECHA_BASE_DT"]].reset_index(drop=True)

@st.cache_data(ttl=3600)
def _cargar_bases_teletalk_por_numero():
    base = _preparar_archivo_teletalk_movil(ARCHIVOS_TELETALK_MOVIL_CAIDAS[0])
    segunda = _preparar_archivo_teletalk_movil(ARCHIVOS_TELETALK_MOVIL_CAIDAS[1])
    tercera = _preparar_archivo_teletalk_movil(ARCHIVOS_TELETALK_MOVIL_CAIDAS[2])
    return base, segunda, tercera

def _filtrar_base_por_mes(base, filtro_mes):
    if base.empty: return base

    if filtro_mes != "Todos los meses":
        m, y = parse_mes_anio(filtro_mes)
        if m and y: return base[
                (base["_FECHA_BASE_DT"].dt.month == m) &
                (base["_FECHA_BASE_DT"].dt.year == y)
            ].copy()

    return base.copy()

@st.cache_data(ttl=3600)
def construir_detalle_movil_teletalk_caidas(filtro_mes="Todos los meses"):
    base, segunda, tercera = _cargar_bases_teletalk_por_numero()

    if base.empty: return pd.DataFrame()

    base_filtrada = _filtrar_base_por_mes(base, filtro_mes)

    # ✅ Para 3ra caída el filtro de Fecha de Venta NO debe usar la fecha de la base.
    # Debe usar FEC ACTIV CTR del archivo CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv.
    tercera_filtrada = _filtrar_base_por_mes(tercera, filtro_mes)

    # ✅ LÓGICA CORRECTA SOLICITADA:
    # Base Pagados: se queda igual desde CLARO_TELETALK_MOVIL.csv
    # 2da Caída: cruza DNI CLIENTE de CLARO_TELETALK_MOVIL.csv
    #             contra DNI RUC de CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv
    #             y SOLO cuenta cuando COMISION > 0
    # 3ra Caída: cruza DNI CLIENTE de CLARO_TELETALK_MOVIL.csv
    #             contra DNI RUC de CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv
    #             y SOLO cuenta cuando COMISION > 0
    df_base_raw = cargar_csv("CLARO_TELETALK_MOVIL.csv")
    df_segunda_raw = cargar_csv("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")

    doc_base_full, col_doc_base = _obtener_documento_por_columnas(df_base_raw, ["DNI CLIENTE"]) if not df_base_raw.empty else (pd.Series(dtype="object"), "")

    # ✅ NUEVA REGLA DE NEGOCIO:
    # La 2da caída SOLO cuenta cuando el cliente cruza por DNI y en el archivo
    # CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv la columna COMISION es mayor a cero.
    # Si COMISION está vacía, en cero o no es numérica, NO se cuenta en 2da caída.
    col_comision_segunda = encontrar_columna(df_segunda_raw, [
        "COMISION", "COMISIÓN", "Comision", "Comisión", "comision", "comisión",
        "COMISION TOTAL", "COMISIÓN TOTAL", "Comision Total", "MONTO"
    ]) if not df_segunda_raw.empty else None

    if not df_segunda_raw.empty and col_comision_segunda:
        comision_segunda = pd.to_numeric(df_segunda_raw[col_comision_segunda], errors="coerce").fillna(0)
        df_segunda_raw = df_segunda_raw[comision_segunda > 0].copy()
    elif not df_segunda_raw.empty:
        # Si no existe columna de comisión, no contamos nada en 2da caída para no inflar el KPI.
        df_segunda_raw = df_segunda_raw.iloc[0:0].copy()

    doc_segunda, col_doc_segunda = _obtener_documento_por_columnas(df_segunda_raw, ["DNI RUC"]) if not df_segunda_raw.empty else (pd.Series(dtype="object"), "")

    # ✅ Comisión adicional real de 2da caída:
    # Se toma desde CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv, columna COMISION.
    # Se agrupa por DNI RUC para no duplicar montos cuando el mismo cliente aparece más de una vez.
    if not df_segunda_raw.empty and col_comision_segunda and len(doc_segunda) > 0:
        df_segunda_comision = pd.DataFrame({
            "_DNI_CLIENTE_CRUCE": doc_segunda,
            "_COMISION_ADICIONAL_2DA": pd.to_numeric(df_segunda_raw[col_comision_segunda], errors="coerce").fillna(0)
        })
        df_segunda_comision = df_segunda_comision.dropna(subset=["_DNI_CLIENTE_CRUCE"])
        df_segunda_comision["_DNI_CLIENTE_CRUCE"] = df_segunda_comision["_DNI_CLIENTE_CRUCE"].astype(str)
        df_segunda_comision = (
            df_segunda_comision
            .groupby("_DNI_CLIENTE_CRUCE", as_index=False)["_COMISION_ADICIONAL_2DA"]
            .sum()
        )
    else:
        df_segunda_comision = pd.DataFrame(columns=["_DNI_CLIENTE_CRUCE", "_COMISION_ADICIONAL_2DA"])

    # Como base_filtrada viene de la misma base y conserva el índice original, usamos ese índice para traer el DNI CLIENTE exacto.
    base_filtrada = base_filtrada.copy()
    if len(doc_base_full) > 0:
        base_filtrada["_DNI_CLIENTE_CRUCE"] = doc_base_full.reindex(base_filtrada.index)
    else:
        base_filtrada["_DNI_CLIENTE_CRUCE"] = _limpiar_documento_movil(base_filtrada.get("Documento", pd.Series([""] * len(base_filtrada), index=base_filtrada.index)))
    base_filtrada["_DNI_CLIENTE_CRUCE"] = base_filtrada["_DNI_CLIENTE_CRUCE"].astype(str)

    docs_segunda = set(df_segunda_comision["_DNI_CLIENTE_CRUCE"].dropna().astype(str).tolist()) if not df_segunda_comision.empty else set()

    base_out = base_filtrada.copy()
    base_out["Etapa"] = "Base Pagados"
    base_out["Orden"] = 1
    base_out["Descripción"] = "Base principal pagada"
    base_out["Coincide Base"] = "SI"
    base_out["Criterio Cruce"] = "Base CLARO_TELETALK_MOVIL"

    segunda_out = base_filtrada[base_filtrada["_DNI_CLIENTE_CRUCE"].astype(str).isin(docs_segunda)].copy()
    if not segunda_out.empty:
        segunda_out = segunda_out.merge(df_segunda_comision, on="_DNI_CLIENTE_CRUCE", how="left")
        segunda_out["_COMISION_ADICIONAL_2DA"] = pd.to_numeric(
            segunda_out["_COMISION_ADICIONAL_2DA"], errors="coerce"
        ).fillna(0)
        # Evita duplicar el monto si el mismo DNI aparece varias veces en la base filtrada.
        segunda_out["_ORDEN_DNI_2DA"] = segunda_out.groupby("_DNI_CLIENTE_CRUCE").cumcount()
        segunda_out["COMISION"] = segunda_out.apply(
            lambda r: r["_COMISION_ADICIONAL_2DA"] if r["_ORDEN_DNI_2DA"] == 0 else 0,
            axis=1
        )
        segunda_out["COMISION ADICIONAL 2DA"] = segunda_out["COMISION"]
    else:
        segunda_out["COMISION ADICIONAL 2DA"] = 0
    segunda_out["Etapa"] = "2da Caída - 3 meses"
    segunda_out["Orden"] = 2
    segunda_out["Descripción"] = "Cliente de la base cuyo DNI CLIENTE cruza con DNI RUC de 2da caída y COMISION > 0"
    segunda_out["Archivo"] = "CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv"
    segunda_out["Coincide Base"] = "SI"
    segunda_out["Criterio Cruce"] = f"{col_doc_base or 'DNI CLIENTE'} vs {col_doc_segunda or 'DNI RUC'} | comisión tomada de CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA"

    # ✅ 3ra caída: se calcula con la misma lógica que 2da caída, pero usando
    # CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv y su filtro de mes por FEC ACTIV CTR.
    df_tercera_raw = cargar_csv("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv")

    col_comision_tercera = encontrar_columna(df_tercera_raw, [
        "COMISION", "COMISIÓN", "Comision", "Comisión", "comision", "comisión",
        "COMISION TOTAL", "COMISIÓN TOTAL", "Comision Total", "MONTO"
    ]) if not df_tercera_raw.empty else None

    if not df_tercera_raw.empty and col_comision_tercera:
        comision_tercera = pd.to_numeric(df_tercera_raw[col_comision_tercera], errors="coerce").fillna(0)
        df_tercera_raw = df_tercera_raw[comision_tercera > 0].copy()
    elif not df_tercera_raw.empty:
        df_tercera_raw = df_tercera_raw.iloc[0:0].copy()

    doc_tercera, col_doc_tercera = _obtener_documento_por_columnas(df_tercera_raw, ["DNI RUC"]) if not df_tercera_raw.empty else (pd.Series(dtype="object"), "")

    if not df_tercera_raw.empty and col_comision_tercera and len(doc_tercera) > 0:
        df_tercera_comision = pd.DataFrame({
            "_DNI_CLIENTE_CRUCE": doc_tercera,
            "_COMISION_ADICIONAL_3RA": pd.to_numeric(df_tercera_raw[col_comision_tercera], errors="coerce").fillna(0)
        })
        df_tercera_comision = df_tercera_comision.dropna(subset=["_DNI_CLIENTE_CRUCE"])
        df_tercera_comision["_DNI_CLIENTE_CRUCE"] = df_tercera_comision["_DNI_CLIENTE_CRUCE"].astype(str)
        df_tercera_comision = (
            df_tercera_comision
            .groupby("_DNI_CLIENTE_CRUCE", as_index=False)["_COMISION_ADICIONAL_3RA"]
            .sum()
        )
    else:
        df_tercera_comision = pd.DataFrame(columns=["_DNI_CLIENTE_CRUCE", "_COMISION_ADICIONAL_3RA"])

    docs_tercera = set(df_tercera_comision["_DNI_CLIENTE_CRUCE"].dropna().astype(str).tolist()) if not df_tercera_comision.empty else set()
    tercera_out = base_filtrada[base_filtrada["_DNI_CLIENTE_CRUCE"].astype(str).isin(docs_tercera)].copy()

    if not tercera_out.empty:
        tercera_out = tercera_out.merge(df_tercera_comision, on="_DNI_CLIENTE_CRUCE", how="left")
        tercera_out["_COMISION_ADICIONAL_3RA"] = pd.to_numeric(
            tercera_out["_COMISION_ADICIONAL_3RA"], errors="coerce"
        ).fillna(0)
        tercera_out["_ORDEN_DNI_3RA"] = tercera_out.groupby("_DNI_CLIENTE_CRUCE").cumcount()
        tercera_out["COMISION"] = tercera_out.apply(
            lambda r: r["_COMISION_ADICIONAL_3RA"] if r["_ORDEN_DNI_3RA"] == 0 else 0,
            axis=1
        )
        tercera_out["COMISION ADICIONAL 3RA"] = tercera_out["COMISION"]

    if not tercera_out.empty and not tercera_filtrada.empty:
        fechas_tercera = (
            tercera_filtrada[["NUMERO_LINEA", "FECHA_BASE", "_FECHA_BASE_DT", "FECHA_ORIGINAL", "_FECHA_ORIGINAL_DT"]]
            .dropna(subset=["NUMERO_LINEA"])
            .drop_duplicates(subset=["NUMERO_LINEA"], keep="first")
            .rename(columns={
                "FECHA_BASE": "FECHA_BASE_TERCERA",
                "_FECHA_BASE_DT": "_FECHA_BASE_DT_TERCERA",
                "FECHA_ORIGINAL": "FECHA_ORIGINAL_TERCERA",
                "_FECHA_ORIGINAL_DT": "_FECHA_ORIGINAL_DT_TERCERA",
            })
        )
        tercera_out = tercera_out.merge(fechas_tercera, on="NUMERO_LINEA", how="left")
        tercera_out["FECHA_BASE"] = tercera_out["FECHA_BASE_TERCERA"].fillna(tercera_out["FECHA_BASE"])
        tercera_out["FECHA_ORIGINAL"] = tercera_out["FECHA_ORIGINAL_TERCERA"].fillna(tercera_out["FECHA_ORIGINAL"])
        tercera_out["_FECHA_BASE_DT"] = tercera_out["_FECHA_BASE_DT_TERCERA"].fillna(tercera_out["_FECHA_BASE_DT"])
        tercera_out["_FECHA_ORIGINAL_DT"] = tercera_out["_FECHA_ORIGINAL_DT_TERCERA"].fillna(tercera_out["_FECHA_ORIGINAL_DT"])
        tercera_out = tercera_out.drop(columns=[
            "FECHA_BASE_TERCERA", "_FECHA_BASE_DT_TERCERA",
            "FECHA_ORIGINAL_TERCERA", "_FECHA_ORIGINAL_DT_TERCERA"
        ], errors="ignore")

    tercera_out["Etapa"] = "3ra Caída - 6 meses"
    tercera_out["Orden"] = 3
    tercera_out["Descripción"] = "Cliente de la base cuyo DNI CLIENTE cruza con DNI RUC de 3ra caída y COMISION > 0"
    tercera_out["Archivo"] = "CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv"
    tercera_out["Coincide Base"] = "SI"
    tercera_out["Criterio Cruce"] = f"{col_doc_base or 'DNI CLIENTE'} vs {col_doc_tercera or 'DNI RUC'} | comisión tomada de CLARO_TELETALK_MOVIL_TERCERA_CAIDA"

    df_all = pd.concat([base_out, segunda_out, tercera_out], ignore_index=True)

    return df_all.reset_index(drop=True)

@st.cache_data(ttl=3600)
def obtener_meses_teletalk_movil_caidas():
    base, _, tercera = _cargar_bases_teletalk_por_numero()
    meses = set()

    # Base Pagados / 2da Caída: meses desde la fecha de la base.
    if not base.empty:
        for f in base["_FECHA_BASE_DT"].dropna():
            meses.add(f"{MESES_ES[f.month].capitalize()} {f.year}")

    # 3ra Caída: meses desde FEC ACTIV CTR de CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv.
    if not tercera.empty:
        for f in tercera["_FECHA_BASE_DT"].dropna():
            meses.add(f"{MESES_ES[f.month].capitalize()} {f.year}")

    return ["Todos los meses"] + sorted(
        meses,
        key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))
    )

def _lineas_etapa(df, etapa):
    if df.empty: return 0
    return int((df["Etapa"] == etapa).sum())

def _comision_etapa(df, etapa):
    if df.empty: return 0.0
    return float(
        pd.to_numeric(
            df.loc[df["Etapa"] == etapa, "COMISION"],
            errors="coerce"
        ).fillna(0).sum()
    )

def _agregar_lineas_por_cliente_teletalk(df):
    """Agrega cuántas líneas tiene cada cliente dentro de cada etapa.

    Base Pagados: cuenta TELEFONO de CLARO_TELETALK_MOVIL.
    2da Caída: cuenta MSISDN de CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.
    3ra Caída: cuenta MSISDN/NUMERO_LINEA de la tercera caída cuando exista en el detalle.
    """
    if df.empty:
        df["Lineas Cliente"] = 0
        return df

    base = df.copy()
    for col in ["Etapa", "Documento", "NUMERO_LINEA"]:
        if col not in base.columns:
            base[col] = ""

    base["Documento"] = base["Documento"].fillna("").astype(str).str.strip()
    base["NUMERO_LINEA"] = base["NUMERO_LINEA"].fillna("").astype(str).str.strip()

    # Conteo estándar por etapa usando el número que ya trae cada fila.
    conteo_general = (
        base[(base["Documento"] != "") & (base["NUMERO_LINEA"] != "")]
        .drop_duplicates(subset=["Etapa", "Documento", "NUMERO_LINEA"])
        .groupby(["Etapa", "Documento"], as_index=False)["NUMERO_LINEA"]
        .nunique()
        .rename(columns={"NUMERO_LINEA": "Lineas Cliente"})
    )

    base = base.merge(conteo_general, on=["Etapa", "Documento"], how="left")
    base["Lineas Cliente"] = pd.to_numeric(base["Lineas Cliente"], errors="coerce").fillna(0).astype(int)

    # Regla especial para 2da caída: el conteo de líneas debe venir del MSISDN del archivo segunda caída.
    try:
        df_segunda_raw = cargar_csv("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")
        if not df_segunda_raw.empty:
            col_doc_seg = encontrar_columna(df_segunda_raw, ["DNI RUC", "DNI", "RUC", "DOCUMENTO", "NRO DOCUMENTO"])
            col_msidn_seg = encontrar_columna(df_segunda_raw, ["MSISDN", "TELEFONO", "TELÉFONO", "Telefono", "Teléfono", "NUMERO", "NÚMERO"])
            col_com_seg = encontrar_columna(df_segunda_raw, [
                "COMISION", "COMISIÓN", "Comision", "Comisión", "comision", "comisión",
                "COMISION TOTAL", "COMISIÓN TOTAL", "Comision Total", "MONTO"
            ])
            if col_doc_seg and col_msidn_seg and col_com_seg:
                temp = df_segunda_raw.copy()
                temp["Documento"] = _limpiar_documento_movil(temp[col_doc_seg]).astype(str)
                temp["MSISDN_LIMPIO"] = _limpiar_numero_movil(temp[col_msidn_seg]).astype(str)
                temp["COMISION_NUM"] = pd.to_numeric(temp[col_com_seg], errors="coerce").fillna(0)
                temp = temp[(temp["COMISION_NUM"] > 0) & (temp["Documento"] != "") & (temp["MSISDN_LIMPIO"] != "")]
                conteo_segunda = (
                    temp.drop_duplicates(subset=["Documento", "MSISDN_LIMPIO"])
                    .groupby("Documento", as_index=False)["MSISDN_LIMPIO"]
                    .nunique()
                    .rename(columns={"MSISDN_LIMPIO": "Lineas Cliente Segunda"})
                )
                if not conteo_segunda.empty:
                    base = base.merge(conteo_segunda, on="Documento", how="left")
                    mask_seg = base["Etapa"].eq("2da Caída - 3 meses")
                    base.loc[mask_seg, "Lineas Cliente"] = pd.to_numeric(
                        base.loc[mask_seg, "Lineas Cliente Segunda"], errors="coerce"
                    ).fillna(base.loc[mask_seg, "Lineas Cliente"]).astype(int)
                    base = base.drop(columns=["Lineas Cliente Segunda"], errors="ignore")
    except Exception:
        pass

    return base

def _resumen_etapas_teletalk(df):
    cols = ["Etapa", "Líneas", "Comision", "% Sobre Base"]
    if df.empty: return pd.DataFrame(columns=cols)

    base_lineas = _lineas_etapa(df, "Base Pagados")
    segunda_lineas = _lineas_etapa(df, "2da Caída - 3 meses")
    tercera_lineas = _lineas_etapa(df, "3ra Caída - 6 meses")

    def pct_sobre_base(valor):
        if base_lineas <= 0: return "0.00%"
        return f"{(valor / base_lineas * 100):.2f}%"

    resumen = pd.DataFrame([
        {
            "Etapa": "Base Pagados",
            "Líneas": base_lineas,
            "Comision": _comision_etapa(df, "Base Pagados"),
            "% Sobre Base": "100.00%" if base_lineas > 0 else "0.00%",
        },
        {
            "Etapa": "2da Caída - 3 meses",
            "Líneas": segunda_lineas,
            "Comision": _comision_etapa(df, "2da Caída - 3 meses"),
            "% Sobre Base": pct_sobre_base(segunda_lineas),
        },
        {
            "Etapa": "3ra Caída - 6 meses",
            "Líneas": tercera_lineas,
            "Comision": _comision_etapa(df, "3ra Caída - 6 meses"),
            "% Sobre Base": pct_sobre_base(tercera_lineas),
        },
    ])

    return resumen[cols]

def _excel_bytes_teletalk_etapa(df_export):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Detalle")
    output.seek(0)
    return output.getvalue()

def _detalle_clientes_por_etapa_teletalk(df, etapa):
    cols_salida = ["Cliente", "Documento", "Lineas Cliente", "COMISION"]
    if df.empty: return pd.DataFrame(columns=cols_salida)

    base = df[df["Etapa"] == etapa].copy()
    if base.empty: return pd.DataFrame(columns=cols_salida)

    base = _agregar_lineas_por_cliente_teletalk(base)

    for col in ["Cliente", "Documento", "Lineas Cliente", "COMISION"]:
        if col not in base.columns:
            base[col] = 0 if col in ["Lineas Cliente", "COMISION"] else ""

    detalle = base[["Cliente", "Documento", "Lineas Cliente", "COMISION"]].copy()
    detalle["Cliente"] = detalle["Cliente"].fillna("Sin Datos").astype(str).str.strip().replace("", "Sin Datos")
    detalle["Documento"] = detalle["Documento"].fillna("").astype(str).str.strip()
    detalle["Lineas Cliente"] = pd.to_numeric(detalle["Lineas Cliente"], errors="coerce").fillna(0).astype(int)
    detalle["COMISION"] = pd.to_numeric(detalle["COMISION"], errors="coerce").fillna(0)

    # Cliente único: suma comisión y conserva el mayor conteo de líneas calculado para ese DNI.
    detalle = (
        detalle.groupby(["Cliente", "Documento"], as_index=False)
        .agg({"Lineas Cliente": "max", "COMISION": "sum"})
        .sort_values(["Lineas Cliente", "COMISION"], ascending=[False, False])
        .reset_index(drop=True)
    )
    return detalle[cols_salida]

def mostrar_resumen_etapas_expandible_teletalk(df, resumen, filtro_mes):
    etapas = ["Base Pagados", "2da Caída - 3 meses", "3ra Caída - 6 meses"]

    for etapa in etapas:
        fila = resumen[resumen["Etapa"] == etapa]
        cantidad = int(fila["Líneas"].iloc[0]) if not fila.empty else 0
        comision = float(pd.to_numeric(fila["Comision"], errors="coerce").fillna(0).iloc[0]) if not fila.empty else 0.0
        pct = str(fila["% Sobre Base"].iloc[0]) if not fila.empty else "0.00%"

        with st.expander(f"➕ {etapa} | {cantidad:,} clientes | {formatear_moneda(comision)} | {pct}", expanded=False):
            detalle = _detalle_clientes_por_etapa_teletalk(df, etapa)

            if detalle.empty:
                st.warning("Sin clientes para esta etapa con los filtros seleccionados.")
                continue

            detalle_show = detalle.copy()
            detalle_show["COMISION"] = detalle_show["COMISION"].map(formatear_moneda)
            st.dataframe(detalle_show, use_container_width=True, height=320)

            archivo_etapa = (
                etapa.lower()
                .replace(" ", "_")
                .replace("í", "i")
                .replace("á", "a")
                .replace("é", "e")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("-", "")
            )
            archivo_mes = filtro_mes.replace(" ", "_")

            st.download_button(
                label=f"⬇️ Exportar {etapa} en Excel",
                data=_excel_bytes_teletalk_etapa(detalle),
                file_name=f"teletalk_movil_{archivo_etapa}_{archivo_mes}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_excel_tt_movil_{archivo_etapa}_{archivo_mes}",
                on_click=registrar_descarga,
                args=("Teletalk Móvil por Etapa", f"teletalk_movil_{archivo_etapa}_{archivo_mes}.xlsx", f"Etapa: {etapa} | Mes: {filtro_mes}")
            )

def _ranking_asesores_teletalk(df):
    cols = ["Rank", "ASESOR", "Líneas", "Comision", "% Participación"]
    if df.empty: return pd.DataFrame(columns=cols)

    base = df.copy()
    r = (
        base.groupby("ASESOR", as_index=False)
        .agg(
            **{
                "Líneas": ("Etapa", "count"),
                "Comision": ("COMISION", lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())
            }
        )
        .sort_values(["Líneas", "Comision"], ascending=[False, False])
        .reset_index(drop=True)
    )

    if r.empty: return pd.DataFrame(columns=cols)

    r.insert(0, "Rank", r.index + 1)
    total = int(r["Líneas"].sum())
    r["% Participación"] = (r["Líneas"] / total * 100).round(2).astype(str) + "%" if total > 0 else "0%"

    total_row = pd.DataFrame([{
        "Rank": "TOTAL",
        "ASESOR": "",
        "Líneas": total,
        "Comision": float(r["Comision"].sum()),
        "% Participación": "100.00%" if total > 0 else "0%"
    }])

    return pd.concat([r[cols], total_row[cols]], ignore_index=True)

def _kpi_movil_teletalk_card(col, titulo, valor, subtitulo, color="#6d0b8c"):
    with col:
        st.markdown(
            f"""
            <div style="
                background:rgba(255,255,255,.96);
                padding:18px;
                border-radius:18px;
                border:2px solid {color};
                text-align:center;
                min-height:104px;
                box-shadow:0 12px 28px rgba(0,0,0,.08);
                margin-bottom:10px;">
                <div style="font-size:11px;font-weight:900;color:#4b5563;text-transform:uppercase;letter-spacing:.08em;">
                    {titulo}
                </div>
                <div style="font-size:30px;font-weight:900;color:{color};line-height:1.1;margin-top:6px;">
                    {valor}
                </div>
                <div style="font-size:11px;color:#6b7280;margin-top:4px;">
                    {subtitulo}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def _grafico_resumen_etapa_gerencial(resumen):
    import altair as alt

    chart_df = resumen.copy()
    chart_df["Líneas"] = pd.to_numeric(chart_df["Líneas"], errors="coerce").fillna(0)

    base_val = int(chart_df.loc[chart_df["Etapa"] == "Base Pagados", "Líneas"].sum())
    chart_df["% Num"] = chart_df["Líneas"].apply(
        lambda v: (v / base_val * 100) if base_val > 0 else 0
    )
    chart_df.loc[chart_df["Etapa"] == "Base Pagados", "% Num"] = 100 if base_val > 0 else 0

    chart_df["Etiqueta"] = chart_df.apply(
        lambda r: f"{int(r['Líneas']):,} líneas · {r['% Num']:.2f}%",
        axis=1
    )

    chart_df["Orden"] = chart_df["Etapa"].map({
        "Base Pagados": 1,
        "2da Caída - 3 meses": 2,
        "3ra Caída - 6 meses": 3
    })

    chart_df["Color"] = chart_df["Etapa"].map({
        "Base Pagados": "Base",
        "2da Caída - 3 meses": "3 meses",
        "3ra Caída - 6 meses": "6 meses"
    })

    barras = (
        alt.Chart(chart_df)
        .mark_bar(
            cornerRadiusTopRight=12,
            cornerRadiusBottomRight=12,
            height=42
        )
        .encode(
            y=alt.Y(
                "Etapa:N",
                sort=alt.SortField("Orden", order="ascending"),
                title="",
                axis=alt.Axis(labelFontSize=13, labelFontWeight="bold")
            ),
            x=alt.X(
                "Líneas:Q",
                title="Líneas",
                axis=alt.Axis(labelFontSize=12, titleFontSize=12, grid=True)
            ),
            color=alt.Color(
                "Color:N",
                scale=alt.Scale(
                    domain=["Base", "3 meses", "6 meses"],
                    range=["#059669", "#d97706", "#dc2626"]
                ),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("Etapa:N", title="Etapa"),
                alt.Tooltip("Líneas:Q", title="Líneas", format=",.0f"),
                alt.Tooltip("% Num:Q", title="% sobre base", format=".2f"),
                alt.Tooltip("Comision:Q", title="Comisión", format=",.2f"),
            ]
        )
    )

    etiquetas = (
        alt.Chart(chart_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=8,
            fontSize=13,
            fontWeight="bold",
            color="#111827"
        )
        .encode(
            y=alt.Y("Etapa:N", sort=alt.SortField("Orden", order="ascending"), title=""),
            x=alt.X("Líneas:Q"),
            text="Etiqueta:N"
        )
    )

    grafico = (
        (barras + etiquetas)
        .properties(
            height=285,
            title="Recuperación móvil Teletalk sobre la base por número"
        )
        .configure_title(
            fontSize=18,
            fontWeight="bold",
            color="#111827",
            anchor="start"
        )
        .configure_axis(
            gridColor="#e5e7eb",
            domain=False,
            tickColor="#e5e7eb"
        )
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(grafico, use_container_width=True)

def _leer_csv_movil_con_fallback(nombres):
    for nombre in nombres:
        ruta = os.path.join(DATA_DIR, nombre)
        if os.path.exists(ruta):
            df = cargar_csv(nombre)
            if not df.empty: return df, nombre
    return pd.DataFrame(), nombres[0] if nombres else ""

def _normalizar_nombre_columna_movil(nombre):
    import re
    s = str(nombre).strip().upper()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ü", "U")]:
        s = s.replace(a, b)
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def encontrar_columna_flexible(df, posibles):
    if df is None or df.empty: return None
    mapa = {_normalizar_nombre_columna_movil(c): c for c in df.columns}
    for posible in posibles:
        key = _normalizar_nombre_columna_movil(posible)
        if key in mapa: return mapa[key]
    # Búsqueda secundaria por inclusión de palabras clave
    posibles_norm = [_normalizar_nombre_columna_movil(p) for p in posibles]
    for key, col_real in mapa.items():
        for p in posibles_norm:
            if p and (p in key or key in p): return col_real
    return None

def _parse_fecha_movil_robusta(serie):
    if serie is None: return pd.Series(pd.NaT)
    s = serie.copy()
    s_str = s.astype(str).str.strip()

    # Formato ISO "YYYY-MM-DD" (o con hora) -> NO usar dayfirst (evita que pandas
    # intercambie día/mes, p.ej. "2026-06-10" mal interpretado como 06-Oct-2026).
    es_iso = s_str.str.match(r"^\d{4}-\d{1,2}-\d{1,2}", na=False)
    fechas_iso = pd.to_datetime(s_str.where(es_iso), errors="coerce", dayfirst=False)

    # Formato "DD/MM/YYYY" u otros con separador '/' -> usar dayfirst.
    fechas_txt = pd.to_datetime(s_str.where(~es_iso), errors="coerce", dayfirst=True)

    # Fallback numérico (serial Excel) SOLO si el valor es puramente numérico
    # (evita que textos no-fecha o vacíos se conviertan en fechas seriales erróneas).
    es_num_puro = s_str.str.match(r"^\d+(\.\d+)?$", na=False)
    num = pd.to_numeric(s_str.where(es_num_puro), errors="coerce")
    fechas_num = pd.to_datetime(num, unit="D", origin="1899-12-30", errors="coerce")

    fechas = fechas_iso.fillna(fechas_txt).fillna(fechas_num)
    return fechas

def _obtener_fecha_venta_movil_general(df):
    col = encontrar_columna_flexible(df, [
        "FECHA DE VENTA", "Fecha de Venta", "FECHA VENTA", "Fecha Venta",
        "FECHA CREACION", "FECHA DE CREACION", "FECHA CREACIÓN", "FECHA DE CREACIÓN",
        "FECHA OPERACION", "FECHA OPERACIÓN", "Fecha Operacion", "Fecha Operación",
        "FECHA CARGA", "Fecha Carga"
    ])
    if col: return _parse_fecha_movil_robusta(df[col]), col
    return pd.Series(pd.NaT, index=df.index), ""

def _obtener_tipo_operacion_movil_general(df):
    col = encontrar_columna_flexible(df, [
        "Cliente - Tipo De Operacion", "Cliente - Tipo De Operación",
        "CLIENTE TIPO DE OPERACION", "CLIENTE TIPO DE OPERACIÓN",
        "CLIENTE - TIPO DE OPERACION", "CLIENTE - TIPO DE OPERACIÓN",
        "Tipo De Operacion", "Tipo De Operación", "TIPO DE OPERACION", "TIPO DE OPERACIÓN",
        "TIPO OPERACION", "TIPO OPERACIÓN",
        "Cliente - Tipo Operacion", "Cliente - Tipo Operación"
    ])
    if col: return ( df[col] .fillna("") .astype(str) .str.replace(r" ", " ", regex=False) .str.replace(r"\s+", " ", regex=True) .str.strip() .str.upper() .replace(["NAN", "NONE", "NULL", "NAT", "<NA>"], "") ), col
    return pd.Series([""] * len(df), index=df.index), ""

def _obtener_supervisor_movil_general(df):
    col = encontrar_columna_flexible(df, [
        "Datos Adicionales - Supervisor",
        "Datos adicionales - Supervisor",
        "DATOS ADICIONALES - SUPERVISOR"
    ])
    if col: return ( df[col] .fillna("Sin Supervisor") .astype(str) .str.replace(r" ", " ", regex=False) .str.replace(r"\s+", " ", regex=True) .str.strip() .replace("", "Sin Supervisor") ), col
    return pd.Series(["Sin Supervisor"] * len(df), index=df.index), "NO ENCONTRADA"

def _obtener_tipificacion_movil_general(df):
    col = encontrar_columna_flexible(df, [
        "Estados - Venta Especificacion",
        "Estados - Venta Especificación",
        "ESTADOS - VENTA ESPECIFICACION",
        "ESTADOS - VENTA ESPECIFICACIÓN"
    ])
    if col: return ( df[col] .fillna("Sin Tipificación") .astype(str) .str.replace(r" ", " ", regex=False) .str.replace(r"\s+", " ", regex=True) .str.strip() .replace("", "Sin Tipificación") ), col
    return pd.Series(["Sin Tipificación"] * len(df), index=df.index), "NO ENCONTRADA"

@st.cache_data(ttl=3600)
def obtener_tipificaciones_solo_movil_general():
    """
    Opciones del filtro Tipificación para Detalle Móvil General.
    IMPORTANTE: lee SOLO MOVIL_DC.csv y MOVIL_TELETALK.csv,
    y SOLO la columna Estados - Venta Especificacion.
    No usa FIJA, no usa CLARO y no mezcla TIPIS de otras pestañas.
    """
    opciones = set()
    for archivo in ["MOVIL_DC.csv", "MOVIL_TELETALK.csv"]:
        df = cargar_csv(archivo)
        if df.empty: continue

        # Búsqueda estricta de la columna solicitada en móviles.
        col = encontrar_columna_flexible(df, [
            "Estados - Venta Especificacion",
            "Estados - Venta Especificación",
            "ESTADOS - VENTA ESPECIFICACION",
            "ESTADOS - VENTA ESPECIFICACIÓN"
        ])
        if not col: continue

        serie = (
            df[col]
            .fillna("Sin Tipificación")
            .astype(str)
            .str.replace(r" ", " ", regex=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        serie = serie.replace(["", "0", "0.0", "NAN", "NONE", "NULL", "NAT", "<NA>"], "Sin Tipificación")
        opciones.update(serie.dropna().unique().tolist())

    return ["Todos"] + sorted(opciones)

def _normalizar_documento_movil_general(serie):
    """
    Limpia DNI/documento para cruzar MOVIL vs CLARO móvil.
    Corrige espacios, .0, guiones y caracteres invisibles.
    """
    s = serie.fillna("").astype(str).str.strip()
    s = s.str.replace("\u00a0", "", regex=False)
    s = s.str.replace("\ufeff", "", regex=False)
    s = s.str.replace(r"\.0+$", "", regex=True)
    s = s.str.replace(r"[^0-9A-Za-z]", "", regex=True)
    s = s.str.upper().replace(["NAN", "NONE", "NULL", "NAT", "<NA>"], "")
    return s

def _obtener_documento_movil_general(df):
    col = encontrar_columna_flexible(df, [
        "Cliente - Documento", "Cliente - Nro Documento", "Cliente Documento",
        "DOCUMENTO", "DNI", "DNI CLIENTE", "NRO DOCUMENTO", "NUMERO DOCUMENTO"
    ])
    if col: return _normalizar_documento_movil_general(df[col]), col
    return pd.Series([""] * len(df), index=df.index), "NO ENCONTRADA"

@st.cache_data(ttl=3600)
def construir_pagos_claro_movil_por_dni_mes(filtro_mes="Todos los meses", filtro_canal="Todos"):
    """
    Base REAL de liquidación móvil desde CLARO.

    Corrección final:
    - NO agrupa la comisión por DNI.
    - Conserva cada fila real de CLARO con su propia COMISION TOTAL.
    - Usa TRANSACCION de CLARO como Tipo Operacion.
    - Excluye TRANSACCION vacía o igual a 0 para no arrastrar el primer valor incorrecto.
    - Estado Pago: COMISION TOTAL > 0 = PAGADA; COMISION TOTAL <= 0 = NO PAGADA.
    - Fecha del filtro: FECHA OPERACION.
    """
    configuracion = [
        ("D&C", "CLARO_DC_MOVIL.csv"),
        ("Teletalk", "CLARO_TELETALK_MOVIL.csv"),
    ]
    bases = []
    for canal, archivo in configuracion:
        if filtro_canal != "Todos" and canal != filtro_canal: continue
        df = cargar_csv(archivo)
        if df.empty: continue

        df = df.copy()
        col_dni = encontrar_columna_flexible(df, [
            "DNI CLIENTE", "DNI", "Cliente - Documento", "Cliente Documento", "DOCUMENTO CLIENTE", "DOCUMENTO"
        ])
        col_fecha = encontrar_columna_flexible(df, [
            "FECHA OPERACION", "FECHA OPERACIÓN", "Fecha Operacion", "Fecha Operación"
        ])
        col_comision = encontrar_columna_flexible(df, [
            "COMISION TOTAL", "COMISIÓN TOTAL", "Comision Total", "Comisión Total", "MONTO"
        ])
        col_transaccion = encontrar_columna_flexible(df, [
            "TRANSACCION", "TRANSACCIÓN", "Transaccion", "Transacción",
            "TIPO TRANSACCION", "TIPO DE VENTA", "Tipo Transaccion"
        ])
        col_cliente = encontrar_columna_flexible(df, [
            "CLIENTE", "NOMBRE CLIENTE", "Cliente", "NOMBRE", "Nombre Cliente"
        ])
        col_plan = encontrar_columna_flexible(df, [
            "PLAN", "Plan", "PRODUCTO", "Producto", "SERVICIO", "Servicio"
        ])

        if not col_dni or not col_fecha or not col_comision: continue

        df["Canal"] = canal
        df["Archivo"] = archivo
        df["DOCUMENTO_KEY"] = _normalizar_documento_movil_general(df[col_dni])
        df["Documento"] = df["DOCUMENTO_KEY"]
        df["_FECHA_OPERACION_DT"] = _parse_fecha_movil_robusta(df[col_fecha])
        df["_ANIO"] = df["_FECHA_OPERACION_DT"].dt.year.astype("Int64")
        df["_MES"] = df["_FECHA_OPERACION_DT"].dt.month.astype("Int64")
        df["FECHA DE VENTA"] = df["_FECHA_OPERACION_DT"].dt.strftime("%d/%m/%Y").fillna("Sin fecha")
        df["COMISION_REAL"] = pd.to_numeric(df[col_comision], errors="coerce").fillna(0)

        if col_transaccion:
            df["Tipo Operacion"] = (
                df[col_transaccion]
                .fillna("")
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
                .str.upper()
                .str.replace("Í", "I", regex=False)
            )
        else:
            df["Tipo Operacion"] = "Sin Transacción"

        # No tomar ceros ni vacíos como tipo de operación.
        df["Tipo Operacion"] = df["Tipo Operacion"].replace([
            "", "0", "0.0", "NAN", "NONE", "NULL", "NAT", "<NA>"
        ], "")
        df = df[(df["DOCUMENTO_KEY"] != "") & df["_FECHA_OPERACION_DT"].notna()].copy()
        df = df[df["Tipo Operacion"] != ""].copy()

        if filtro_mes != "Todos los meses":
            m, y = parse_mes_anio(filtro_mes)
            if m and y:
                df = df[(df["_MES"] == m) & (df["_ANIO"] == y)].copy()

        if df.empty: continue

        df["Estado Pago"] = "NO PAGADA"
        df.loc[df["COMISION_REAL"] > 0, "Estado Pago"] = "PAGADA"
        df["Cliente"] = df[col_cliente].fillna("Sin Cliente").astype(str).str.strip().replace("", "Sin Cliente") if col_cliente else "Sin Cliente"
        df["Plan"] = df[col_plan].fillna("Sin Plan").astype(str).str.strip().replace("", "Sin Plan") if col_plan else "Sin Plan"
        df["Transaccion"] = df["Tipo Operacion"]
        df["Columna Fecha"] = col_fecha
        df["Columna Tipo Operacion"] = col_transaccion if col_transaccion else "TRANSACCION NO ENCONTRADA"
        df["Columna Documento"] = col_dni

        bases.append(df[[
            "Canal", "Archivo", "FECHA DE VENTA", "_FECHA_OPERACION_DT", "_ANIO", "_MES",
            "DOCUMENTO_KEY", "Documento", "Tipo Operacion", "Transaccion", "Cliente", "Plan",
            "COMISION_REAL", "Estado Pago", "Columna Fecha", "Columna Tipo Operacion", "Columna Documento"
        ]])

    cols = [
        "Canal", "Archivo", "FECHA DE VENTA", "_FECHA_OPERACION_DT", "_ANIO", "_MES",
        "DOCUMENTO_KEY", "Documento", "Tipo Operacion", "Transaccion", "Cliente", "Plan",
        "COMISION_REAL", "Estado Pago", "Columna Fecha", "Columna Tipo Operacion", "Columna Documento"
    ]
    if not bases: return pd.DataFrame(columns=cols)
    return pd.concat(bases, ignore_index=True).reset_index(drop=True)

def _sumar_comision_real_unica(df):
    if df is None or df.empty or "COMISION_REAL" not in df.columns: return 0.0
    return float(pd.to_numeric(df["COMISION_REAL"], errors="coerce").fillna(0).sum())

@st.cache_data(ttl=3600)
def construir_resumen_movil_general(filtro_mes="Todos los meses"):
    """
    Detalle Móvil General consolidado.

    Lógica final:
    1. MOVIL_DC/MOVIL_TELETALK solo validan DNI únicos comerciales.
    2. CLARO_DC_MOVIL/CLARO_TELETALK_MOVIL define las ventas reales pagadas/no pagadas.
    3. El Tipo Operacion sale de TRANSACCION de CLARO, no de Cliente - Tipo De Operacion.
    4. Cada fila de CLARO conserva su propia COMISION TOTAL.
    """
    configuracion_movil = [
        ("D&C", ["MOVIL_DC.csv"]),
        ("Teletalk", ["MOVIL_TELETALK.csv"]),
    ]

    bases_movil = []
    for canal, posibles_archivos in configuracion_movil:
        df, archivo_usado = _leer_csv_movil_con_fallback(posibles_archivos)
        if df.empty: continue

        df = df.copy()
        fecha_dt, col_fecha = _obtener_fecha_venta_movil_general(df)
        documento, col_documento = _obtener_documento_movil_general(df)
        supervisor, col_supervisor = _obtener_supervisor_movil_general(df)
        tipificacion, col_tipificacion = _obtener_tipificacion_movil_general(df)

        df["Canal"] = canal
        df["DOCUMENTO_KEY"] = documento
        df["Documento"] = documento
        df["_FECHA_VENTA_MOVIL_DT"] = fecha_dt
        col_fecha_inst = None
        for c in df.columns:
            norm = _normalizar_nombre_columna_movil(c)
            if norm in ("BACK OFFICE FECHA INSTALACION", "FECHA INSTALACION"):
                col_fecha_inst = c
                break
        df["_FECHA_INSTALACION_DT"] = _parse_fecha_movil_robusta(df[col_fecha_inst]) if col_fecha_inst else pd.Series(pd.NaT, index=df.index)
        df["Cliente"] = _obtener_cliente_movil_teletalk(df)
        df["ASESOR"] = _obtener_campo_movil_seguro(df, [
            "USUARIO", "ASESOR", "VENDEDOR", "DISTRIBUIDOR", "EJECUTIVO", "CREADOR", "Usuario", "Asesor"
        ], "Sin Asesor")
        df["SUPERVISOR"] = supervisor
        df["TIPIS"] = tipificacion
        df["Departamento"] = _obtener_campo_movil_seguro(df, [
            "Datos Instalación - Departamento",
            "Datos Instalacion - Departamento",
            "DATOS INSTALACIÓN - DEPARTAMENTO",
            "DATOS INSTALACION - DEPARTAMENTO",
            "Datos Instalación-Departamento",
            "Datos Instalacion-Departamento",
            "Departamento Instalación",
            "Departamento Instalacion",
            "DEPARTAMENTO INSTALACIÓN",
            "DEPARTAMENTO INSTALACION",
            "DEPARTAMENTO", "Departamento", "departamento", "DPTO", "REGION", "REGIÓN", "Región"
        ], "Sin Departamento")
        df["Columna Supervisor"] = col_supervisor
        df["Columna Tipificación"] = col_tipificacion
        df["Columna Documento Movil"] = col_documento
        df["Columna Fecha Movil"] = col_fecha if col_fecha else "NO ENCONTRADA"

        df = df[df["DOCUMENTO_KEY"] != ""].copy()
        if filtro_mes != "Todos los meses":
            m, y = parse_mes_anio(filtro_mes)
            if m and y and "_FECHA_VENTA_MOVIL_DT" in df.columns:
                # El filtro principal de pagos usa FECHA OPERACION de CLARO.
                # Este filtro en MOVIL solo reduce el universo comercial cuando exista fecha válida.
                df = df[(df["_FECHA_VENTA_MOVIL_DT"].dt.month == m) & (df["_FECHA_VENTA_MOVIL_DT"].dt.year == y)].copy()

        if not df.empty:
            # Un solo registro comercial por Canal + DNI para que MOVIL no infle ventas.
            df = df.sort_values("_FECHA_VENTA_MOVIL_DT", ascending=False, na_position="last")
            df = df.drop_duplicates(subset=["Canal", "DOCUMENTO_KEY"], keep="first")
            # Cruce DOTACION para COLA por extensión del usuario
            # BUSCARV: EXTENSION DEL USUARIO (Excel datos)  ->  USUARIO (DOTACION)  ->  SEGMENTO
            col_ext_movil = encontrar_columna(df, ["EXTENSION DEL USUARIO","EXTENSIÓN DEL USUARIO","Extension del usuario","EXTENSION","Extension"])
            df["COLA"] = _agregar_cola_por_extension(df, col_ext_movil) if col_ext_movil else "EXTERNO"
            bases_movil.append(df[[
                "Canal", "DOCUMENTO_KEY", "Documento", "Cliente", "SUPERVISOR", "TIPIS", "ASESOR",
                "Departamento", "COLA", "_FECHA_INSTALACION_DT", "Columna Supervisor", "Columna Tipificación", "Columna Documento Movil", "Columna Fecha Movil"
            ]])

    columnas_salida = [
        "Canal", "Archivo", "FECHA DE VENTA", "_FECHA_VENTA_DT", "_ANIO", "_MES",
        "DOCUMENTO_KEY", "Documento", "Tipo Operacion", "Cliente", "SUPERVISOR", "TIPIS",
        "ASESOR", "Departamento", "COLA", "_FECHA_INSTALACION_DT", "Transaccion", "Plan", "COMISION_REAL", "COMISION", "Estado Pago",
        "Columna Fecha", "Columna Tipo Operacion", "Columna Documento", "Columna Supervisor", "Columna Tipificación"
    ]

    if not bases_movil: return pd.DataFrame(columns=columnas_salida + ["Venta Valida"])

    movil_unicos = pd.concat(bases_movil, ignore_index=True)
    movil_unicos = movil_unicos.drop_duplicates(subset=["Canal", "DOCUMENTO_KEY"], keep="first")

    claro = construir_pagos_claro_movil_por_dni_mes(filtro_mes, "Todos")

    if not claro.empty:
        # Solo ventas reales de CLARO cuyo DNI exista en MOVIL del mismo canal.
        df_all = claro.merge(
            movil_unicos,
            on=["Canal", "DOCUMENTO_KEY"],
            how="inner",
            suffixes=("", "_MOVIL")
        )
        # Si el documento llegó de CLARO vacío por alguna razón, preservamos el de MOVIL.
        df_all["Documento"] = df_all["Documento"].fillna(df_all.get("Documento_MOVIL", ""))
    else:
        df_all = pd.DataFrame()

    # DNI de MOVIL que no tuvieron ninguna fila en CLARO para el filtro seleccionado.
    if claro.empty:
        sin_claro = movil_unicos.copy()
    else:
        llaves_claro = claro[["Canal", "DOCUMENTO_KEY"]].drop_duplicates()
        sin_claro = movil_unicos.merge(llaves_claro, on=["Canal", "DOCUMENTO_KEY"], how="left", indicator=True)
        sin_claro = sin_claro[sin_claro["_merge"] == "left_only"].drop(columns=["_merge"], errors="ignore")

    if not sin_claro.empty:
        sin_claro = sin_claro.copy()
        sin_claro["Archivo"] = "MOVIL sin cruce CLARO"
        sin_claro["FECHA DE VENTA"] = "Sin fecha CLARO"
        sin_claro["_FECHA_VENTA_DT"] = pd.NaT
        sin_claro["_ANIO"] = pd.NA
        sin_claro["_MES"] = pd.NA
        sin_claro["Tipo Operacion"] = "SIN TRANSACCION CLARO"
        sin_claro["Transaccion"] = "SIN TRANSACCION CLARO"
        sin_claro["Plan"] = "Sin Plan"
        sin_claro["COMISION_REAL"] = 0.0
        sin_claro["COMISION"] = 0.0
        sin_claro["Estado Pago"] = "NO PAGADA"
        sin_claro["Columna Fecha"] = "FECHA OPERACION CLARO"
        sin_claro["Columna Tipo Operacion"] = "TRANSACCION CLARO"
        sin_claro["Columna Documento"] = sin_claro.get("Columna Documento Movil", "Cliente - Documento")
        if "COLA" not in sin_claro.columns:
            sin_claro["COLA"] = "EXTERNO"
        extra = sin_claro[[
            "Canal", "Archivo", "FECHA DE VENTA", "_FECHA_VENTA_DT", "_ANIO", "_MES",
            "DOCUMENTO_KEY", "Documento", "Tipo Operacion", "Cliente", "SUPERVISOR", "TIPIS",
            "ASESOR", "Departamento", "COLA", "_FECHA_INSTALACION_DT", "Transaccion", "Plan", "COMISION_REAL", "COMISION", "Estado Pago",
            "Columna Fecha", "Columna Tipo Operacion", "Columna Documento", "Columna Supervisor", "Columna Tipificación"
        ]]
        df_all = pd.concat([df_all, extra], ignore_index=True) if not df_all.empty else extra.copy()

    if df_all.empty: return pd.DataFrame(columns=columnas_salida + ["Venta Valida"])

    if "_FECHA_OPERACION_DT" in df_all.columns:
        df_all["_FECHA_VENTA_DT"] = df_all["_FECHA_OPERACION_DT"]
    else:
        df_all["_FECHA_VENTA_DT"] = pd.NaT

    df_all["Tipo Operacion"] = (
        df_all["Tipo Operacion"]
        .fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.upper()
        .str.replace("Í", "I", regex=False)
    )
    df_all["Tipo Operacion"] = df_all["Tipo Operacion"].replace(["0", "0.0", "NAN", "NONE", "NULL", "NAT", "<NA>"], "")
    df_all["Venta Valida"] = df_all["Tipo Operacion"].ne("")
    df_all["COMISION_REAL"] = pd.to_numeric(df_all.get("COMISION_REAL", 0), errors="coerce").fillna(0)
    df_all["COMISION"] = df_all["COMISION_REAL"]
    df_all["Estado Pago"] = "NO PAGADA"
    df_all.loc[df_all["COMISION_REAL"] > 0, "Estado Pago"] = "PAGADA"

    for col in columnas_salida:
        if col not in df_all.columns:
            df_all[col] = ""

    return df_all[columnas_salida + ["Venta Valida"]].reset_index(drop=True)

@st.cache_data(ttl=3600)
def obtener_meses_movil_general():
    meses = set()
    for _, posibles_archivos in [
        ("D&C", ["MOVIL_DC.csv"]),
        ("Teletalk", ["MOVIL_TELETALK.csv"]),
    ]:
        df, _ = _leer_csv_movil_con_fallback(posibles_archivos)
        if df.empty: continue
        fecha_dt, _ = _obtener_fecha_venta_movil_general(df)
        for f in fecha_dt.dropna():
            meses.add(f"{MESES_ES[f.month].capitalize()} {f.year}")
    return ["Todos los meses"] + sorted(meses, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0)))

@st.cache_data(ttl=3600)
def construir_comision_claro_movil_general(filtro_mes="Todos los meses", filtro_canal="Todos"):
    """
    Comisión para el KPI de Detalle Móvil General.
    Fuente móvil de liquidación:
    - CLARO_DC_MOVIL.csv
    - CLARO_TELETALK_MOVIL.csv

    Fecha de filtro: FECHA OPERACION
    Monto: COMISION TOTAL
    No toca archivos de fija.
    """
    configuracion = [
        ("D&C", "CLARO_DC_MOVIL.csv"),
        ("Teletalk", "CLARO_TELETALK_MOVIL.csv"),
    ]
    bases = []
    for canal, archivo in configuracion:
        if filtro_canal != "Todos" and canal != filtro_canal: continue
        df = cargar_csv(archivo)
        if df.empty: continue
        df = df.copy()
        col_fecha = encontrar_columna_flexible(df, [
            "FECHA OPERACION", "FECHA OPERACIÓN", "Fecha Operacion", "Fecha Operación"
        ])
        col_comision = encontrar_columna_flexible(df, [
            "COMISION TOTAL", "COMISIÓN TOTAL", "Comision Total", "Comisión Total"
        ])
        if not col_fecha or not col_comision: continue
        df["_FECHA_OPERACION_DT"] = _parse_fecha_movil_robusta(df[col_fecha])
        df["_COMISION_TOTAL"] = pd.to_numeric(df[col_comision], errors="coerce").fillna(0)
        if filtro_mes != "Todos los meses":
            m, y = parse_mes_anio(filtro_mes)
            if m and y:
                df = df[(df["_FECHA_OPERACION_DT"].dt.month == m) & (df["_FECHA_OPERACION_DT"].dt.year == y)].copy()
        if not df.empty:
            bases.append(df[["_FECHA_OPERACION_DT", "_COMISION_TOTAL"]])
    if not bases: return 0.0
    base = pd.concat(bases, ignore_index=True)
    return float(pd.to_numeric(base["_COMISION_TOTAL"], errors="coerce").fillna(0).sum())

def resumen_general_movil_df(df, totales_kpi=None):
    # Tabla ejecutiva por canal. Se retira Operaciones Únicas y se agrega Caída.
    # totales_kpi: dict opcional {"D&C": total_ventas_kpi, "Teletalk": total_ventas_kpi}
    # Si se provee, "Total Ventas" y "No Pagadas" se alinean con la misma lógica de los KPIs
    # (Total Ventas = lectura directa de MOVIL_DC/MOVIL_TELETALK con exclusiones;
    #  No Pagadas = Total Ventas - Pagadas), para que KPI y tabla coincidan.
    cols = ["Canal", "Total Ventas", "Pagadas", "No Pagadas", "Caída", "Comision", "% Participación"]
    if df.empty and not totales_kpi: return pd.DataFrame(columns=cols)

    base = df[df["Venta Valida"]].copy() if not df.empty else pd.DataFrame(columns=df.columns if not df.empty else [])
    if base.empty and not totales_kpi: return pd.DataFrame(columns=cols)

    canales = set()
    if not base.empty:
        canales.update(base["Canal"].dropna().unique().tolist())
    if totales_kpi:
        canales.update(totales_kpi.keys())

    filas = []
    for canal in canales:
        g = base[base["Canal"] == canal] if not base.empty else base
        pagadas = int((g["Estado Pago"] == "PAGADA").sum()) if not g.empty else 0

        if totales_kpi is not None and canal in totales_kpi:
            total_ventas = int(totales_kpi[canal])
        else:
            total_ventas = int(g["Tipo Operacion"].count()) if not g.empty else 0

        no_pagadas = total_ventas - pagadas
        if no_pagadas < 0:
            no_pagadas = 0
        caida = (no_pagadas / total_ventas * 100) if total_ventas > 0 else 0
        filas.append({
            "Canal": canal,
            "Total Ventas": total_ventas,
            "Pagadas": pagadas,
            "No Pagadas": no_pagadas,
            "Caída": f"{caida:.2f}%",
            "Comision": _sumar_comision_real_unica(g),
        })
    resumen = pd.DataFrame(filas).sort_values("Total Ventas", ascending=False).reset_index(drop=True)
    total_general = int(resumen["Total Ventas"].sum()) if not resumen.empty else 0
    resumen["% Participación"] = resumen["Total Ventas"].apply(lambda x: f"{(x / total_general * 100):.2f}%" if total_general > 0 else "0.00%")

    pagadas_total = int(resumen["Pagadas"].sum()) if not resumen.empty else 0
    no_pagadas_total = int(resumen["No Pagadas"].sum()) if not resumen.empty else 0
    caida_total = (no_pagadas_total / total_general * 100) if total_general > 0 else 0
    comision_total = float(resumen["Comision"].sum()) if not resumen.empty else 0.0
    total_row = pd.DataFrame([{
        "Canal": "TOTAL",
        "Total Ventas": total_general,
        "Pagadas": pagadas_total,
        "No Pagadas": no_pagadas_total,
        "Caída": f"{caida_total:.2f}%",
        "Comision": comision_total,
        "% Participación": "100.00%" if total_general > 0 else "0.00%"
    }])
    return pd.concat([resumen[cols], total_row[cols]], ignore_index=True)

def resumen_diario_movil_df(df):
    cols = ["Fecha", "D&C", "Teletalk", "Total Ventas", "Pagadas", "No Pagadas", "Comision"]
    if df.empty: return pd.DataFrame(columns=cols)
    base = df[df["Venta Valida"] & df["_FECHA_VENTA_DT"].notna()].copy()
    if base.empty: return pd.DataFrame(columns=cols)

    grp = (
        base.groupby(["_FECHA_VENTA_DT", "Canal"], as_index=False)
        .agg(Ventas=("Tipo Operacion", "count"))
    )
    pivot = grp.pivot_table(index="_FECHA_VENTA_DT", columns="Canal", values="Ventas", aggfunc="sum", fill_value=0).reset_index()
    for c in ["D&C", "Teletalk"]:
        if c not in pivot.columns:
            pivot[c] = 0

    estados = base.groupby("_FECHA_VENTA_DT", as_index=False).agg(
        Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
        **{"No Pagadas": ("Estado Pago", lambda x: (x == "NO PAGADA").sum())}
    )
    comisiones = []
    for fecha, g in base.groupby("_FECHA_VENTA_DT"):
        comisiones.append({"_FECHA_VENTA_DT": fecha, "Comision": _sumar_comision_real_unica(g)})
    com = pd.DataFrame(comisiones)

    out = pivot.merge(estados, on="_FECHA_VENTA_DT", how="left").merge(com, on="_FECHA_VENTA_DT", how="left")
    out["Total Ventas"] = pd.to_numeric(out["D&C"], errors="coerce").fillna(0) + pd.to_numeric(out["Teletalk"], errors="coerce").fillna(0)
    out["Fecha"] = out["_FECHA_VENTA_DT"].dt.strftime("%d/%m/%Y")
    out = out.sort_values("_FECHA_VENTA_DT")
    return out[cols]

def ranking_movil_por_columna(df, columna, nombre_columna, incluir_total=True):
    # Ranking móvil. Se retira Operaciones Únicas y se agrega Caída = No Pagadas / Total Ventas.
    cols = ["Rank", nombre_columna, "Total Ventas", "Pagadas", "No Pagadas", "Caída", "Comision", "% Participación"]
    if df.empty or columna not in df.columns: return pd.DataFrame(columns=cols)
    base = df[df["Venta Valida"]].copy()
    if base.empty: return pd.DataFrame(columns=cols)
    base[columna] = base[columna].fillna(f"Sin {nombre_columna}").astype(str).str.strip().replace("", f"Sin {nombre_columna}")
    filas = []
    for valor, g in base.groupby(columna, dropna=False):
        total_ventas = int(g["Tipo Operacion"].count())
        pagadas = int((g["Estado Pago"] == "PAGADA").sum())
        no_pagadas = int((g["Estado Pago"] == "NO PAGADA").sum())
        caida = (no_pagadas / total_ventas * 100) if total_ventas > 0 else 0
        filas.append({
            nombre_columna: valor,
            "Total Ventas": total_ventas,
            "Pagadas": pagadas,
            "No Pagadas": no_pagadas,
            "Caída": f"{caida:.2f}%",
            "Comision": _sumar_comision_real_unica(g),
        })
    r = pd.DataFrame(filas).sort_values(["Total Ventas", "Comision"], ascending=[False, False]).reset_index(drop=True)
    r.insert(0, "Rank", r.index + 1)
    total = int(r["Total Ventas"].sum()) if not r.empty else 0
    r["% Participación"] = r["Total Ventas"].apply(lambda x: f"{(x / total * 100):.2f}%" if total > 0 else "0.00%")

    if not incluir_total: return r[cols]

    pagadas_total = int((base["Estado Pago"] == "PAGADA").sum())
    no_pagadas_total = int((base["Estado Pago"] == "NO PAGADA").sum())
    caida_total = (no_pagadas_total / total * 100) if total > 0 else 0
    total_row = pd.DataFrame([{
        "Rank": "TOTAL",
        nombre_columna: "",
        "Total Ventas": total,
        "Pagadas": pagadas_total,
        "No Pagadas": no_pagadas_total,
        "Caída": f"{caida_total:.2f}%",
        "Comision": _sumar_comision_real_unica(base),
        "% Participación": "100.00%" if total > 0 else "0.00%"
    }])
    return pd.concat([r[cols], total_row[cols]], ignore_index=True)

def mostrar_resumen_general_movil_premium(resumen_general):
    if resumen_general.empty:
        st.warning("No hay ventas válidas para el filtro seleccionado.")
        return

    base = resumen_general[resumen_general["Canal"].astype(str).str.upper() != "TOTAL"].copy()
    total = resumen_general[resumen_general["Canal"].astype(str).str.upper() == "TOTAL"].copy()
    if total.empty:
        total_ventas = int(pd.to_numeric(base.get("Total Ventas", 0), errors="coerce").fillna(0).sum())
        pagadas = int(pd.to_numeric(base.get("Pagadas", 0), errors="coerce").fillna(0).sum())
        no_pagadas = int(pd.to_numeric(base.get("No Pagadas", 0), errors="coerce").fillna(0).sum())
        comision = float(pd.to_numeric(base.get("Comision", 0), errors="coerce").fillna(0).sum())
    else:
        total_ventas = int(pd.to_numeric(total["Total Ventas"].iloc[0], errors="coerce"))
        pagadas = int(pd.to_numeric(total["Pagadas"].iloc[0], errors="coerce"))
        no_pagadas = int(pd.to_numeric(total["No Pagadas"].iloc[0], errors="coerce"))
        comision = float(pd.to_numeric(total["Comision"].iloc[0], errors="coerce"))

    pct_pago = (pagadas / total_ventas * 100) if total_ventas > 0 else 0
    pct_caida = (no_pagadas / total_ventas * 100) if total_ventas > 0 else 0

    st.markdown("""
    <style>
        .mov-resumen-wrap{
            background:linear-gradient(135deg, rgba(255,255,255,.98), rgba(245,243,255,.96));
            border:1px solid rgba(109,11,140,.16);
            border-radius:24px;
            padding:20px 22px;
            box-shadow:0 14px 42px rgba(109,11,140,.12);
            margin:8px 0 16px 0;
        }
        .mov-resumen-title{font-size:28px;font-weight:950;color:#70008f;margin-bottom:4px;}
        .mov-resumen-sub{font-size:13px;font-weight:700;color:#64748b;}
        .mov-mini-card{background:white;border-radius:18px;padding:15px 12px;text-align:center;border:1px solid rgba(109,11,140,.12);box-shadow:0 8px 24px rgba(0,0,0,.06);}
        .mov-mini-label{font-size:10px;font-weight:900;color:#64748b;letter-spacing:.08em;text-transform:uppercase;}
        .mov-mini-value{font-size:24px;font-weight:950;color:#70008f;margin-top:5px;}
    </style>
    <div class="mov-resumen-wrap">
        <div class="mov-resumen-title">📋 Resumen General por Canal</div>
        <div class="mov-resumen-sub">Lectura ejecutiva de ventas móviles, pago real Claro, caída y comisión por canal.</div>
    </div>
    """, unsafe_allow_html=True)

    tabla = resumen_general.copy()
    if "Comision" in tabla.columns:
        tabla["Comision"] = pd.to_numeric(tabla["Comision"], errors="coerce").fillna(0).map(formatear_moneda)

    def _resaltar_total_movil(row):
        if str(row.get("Canal", "")).upper() == "TOTAL": return ["background-color:#70008f;color:white;font-weight:900;text-align:center;" for _ in row]
        return ["text-align:center;" for _ in row]

    st.dataframe(
        tabla.style.apply(_resaltar_total_movil, axis=1).set_properties(**{"text-align":"center", "font-size":"13px"}),
        use_container_width=True,
        height=210
    )

    try:
        import altair as alt
        chart_base = base.copy()
        chart_base = chart_base[chart_base["Canal"].astype(str).str.upper() != "TOTAL"].copy()
        chart_base["Canal Mostrar"] = chart_base["Canal"].replace({"D&C": "Digital", "Teletalk": "Teletalk"})
        chart_data = chart_base.melt(
            id_vars=["Canal Mostrar"],
            value_vars=["Pagadas", "No Pagadas"],
            var_name="Estado",
            value_name="Ventas"
        )
        chart = (
            alt.Chart(chart_data)
            .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
            .encode(
                x=alt.X("Canal Mostrar:N", title="Canal", sort=["Digital", "Teletalk"]),
                y=alt.Y("Ventas:Q", title="Ventas"),
                xOffset=alt.XOffset("Estado:N", sort=["Pagadas", "No Pagadas"]),
                color=alt.Color("Estado:N", scale=alt.Scale(domain=["Pagadas", "No Pagadas"], range=["#059669", "#dc2626"]), legend=alt.Legend(title="Estado")),
                tooltip=["Canal Mostrar", "Estado", "Ventas"]
            )
            .properties(height=300, title="Ventas pagadas vs no pagadas por canal")
            .configure_title(fontSize=18, fontWeight="bold", color="#70008f")
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        pass

def mostrar_ranking_supervisor_movil_expandible(df):
    r_sup = ranking_movil_por_columna(df, "SUPERVISOR", "SUPERVISOR")
    if r_sup.empty:
        st.warning("No se encontraron supervisores.")
        return

    base = df[df["Venta Valida"]].copy() if not df.empty and "Venta Valida" in df.columns else pd.DataFrame()
    if base.empty:
        st.warning("No hay ventas válidas para mostrar.")
        return

    sup_rows = r_sup[r_sup["Rank"].astype(str).str.upper() != "TOTAL"].copy()
    total_row = r_sup[r_sup["Rank"].astype(str).str.upper() == "TOTAL"].copy()

    for _, row in sup_rows.iterrows():
        supervisor = str(row["SUPERVISOR"])
        titulo = (
            f"➕ #{row['Rank']} | {supervisor}  |  "
            f"Ventas: {int(row['Total Ventas']):,}  |  "
            f"Pagadas: {int(row['Pagadas']):,}  |  "
            f"No pagadas: {int(row['No Pagadas']):,}  |  "
            f"Comisión: {formatear_moneda(row['Comision'])}"
        )
        with st.expander(titulo, expanded=False):
            df_sup = base[base["SUPERVISOR"].fillna("Sin Supervisor").astype(str).str.strip().replace("", "Sin Supervisor") == supervisor].copy()
            r_asesor = ranking_movil_por_columna(df_sup, "ASESOR", "ASESOR", incluir_total=False)
            if r_asesor.empty:
                st.info("Este supervisor no tiene asesores para el filtro seleccionado.")
            else:
                show = r_asesor.copy()
                show["Comision"] = pd.to_numeric(show["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
                st.dataframe(show, use_container_width=True, height=min(420, 90 + 35 * len(show)))


def mostrar_ranking_departamentos_movil_gerencial(df_filtrado, filtro_mes="Todos los meses", filtro_canal="Todos"):
    """
    Ranking Departamentos Móvil — usa el mismo df_filtrado del Resumen General
    para que los totales sean idénticos. Departamento viene de la columna
    'Datos Instalación - Departamento' de MOVIL_DC/MOVIL_TELETALK, que ya fue
    resuelta en construir_resumen_movil_general y está en df_filtrado.
    """
    if df_filtrado.empty:
        st.warning("No hay datos para el filtro seleccionado.")
        return

    # Usar solo ventas válidas (mismo universo que el resumen general)
    base = df_filtrado[df_filtrado["Venta Valida"]].copy() if "Venta Valida" in df_filtrado.columns else df_filtrado.copy()
    if base.empty:
        st.warning("No hay ventas válidas para mostrar el ranking de departamentos.")
        return

    if "Departamento" not in base.columns:
        st.warning("No se encontró la columna Departamento en los datos.")
        return

    base["Departamento"] = base["Departamento"].fillna("Sin Departamento").astype(str).str.strip().replace("", "Sin Departamento")
    base["COMISION_REAL"] = pd.to_numeric(base.get("COMISION_REAL", 0), errors="coerce").fillna(0)

    filas = []
    for dpto, g in base.groupby("Departamento", dropna=False):
        total = int(len(g))
        activas = int((g["Estado Pago"] == "PAGADA").sum()) if "Estado Pago" in g.columns else 0
        no_activas = int((g["Estado Pago"] == "NO PAGADA").sum()) if "Estado Pago" in g.columns else 0
        comision = float(g["COMISION_REAL"].sum())
        conv = (activas / total * 100) if total > 0 else 0
        caida = (no_activas / total * 100) if total > 0 else 0
        filas.append({
            "Departamento": dpto,
            "Total Ventas": total,
            "Activas": activas,
            "No Activas": no_activas,
            "% Conversión": round(conv, 2),
            "% Caída": round(caida, 2),
            "Comisión": comision,
        })

    if not filas:
        st.warning("No se encontraron departamentos para el filtro seleccionado.")
        return

    rank_df = pd.DataFrame(filas).sort_values(["Activas", "Comisión", "Total Ventas"], ascending=[False, False, False]).reset_index(drop=True)
    rank_df.insert(0, "Rank", rank_df.index + 1)
    cols = ["Rank", "Departamento", "Total Ventas", "Activas", "No Activas", "% Conversión", "% Caída", "Comisión"]

    total_ventas_g = int(rank_df["Total Ventas"].sum())
    total_activas_g = int(rank_df["Activas"].sum())
    total_no_activas_g = int(rank_df["No Activas"].sum())
    total_comision_g = float(rank_df["Comisión"].sum())
    conv_global = (total_activas_g / total_ventas_g * 100) if total_ventas_g > 0 else 0
    caida_global = (total_no_activas_g / total_ventas_g * 100) if total_ventas_g > 0 else 0
    n_dptos = int(rank_df["Departamento"].nunique())

    dep_norm = rank_df["Departamento"].fillna("").astype(str).str.upper().str.strip().str.replace("Á","A",regex=False).str.replace("É","E",regex=False).str.replace("Í","I",regex=False).str.replace("Ó","O",regex=False).str.replace("Ú","U",regex=False)
    mask_lima = dep_norm.str.contains("LIMA", na=False)
    lima_ventas = int(rank_df.loc[mask_lima, "Total Ventas"].sum())
    prov_ventas = int(rank_df.loc[~mask_lima, "Total Ventas"].sum())
    lima_pct = (lima_ventas / total_ventas_g * 100) if total_ventas_g > 0 else 0
    prov_pct = (prov_ventas / total_ventas_g * 100) if total_ventas_g > 0 else 0

    st.markdown("""
    <style>
        .dpto-mov-wrap{
            background:linear-gradient(135deg, rgba(255,255,255,.98), rgba(245,243,255,.96));
            border:1px solid rgba(109,11,140,.16);
            border-radius:26px;
            padding:22px 24px 16px 24px;
            box-shadow:0 16px 48px rgba(109,11,140,.12);
            margin-bottom:16px;
        }
        .dpto-mov-kpi{background:white;border-radius:20px;padding:15px 12px;text-align:center;border:1px solid rgba(109,11,140,.12);box-shadow:0 8px 22px rgba(0,0,0,.06);}
        .dpto-mov-kpi-lbl{font-size:10px;font-weight:900;color:#64748b;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px;}
        .dpto-mov-kpi-val{font-size:26px;font-weight:950;line-height:1.05;margin-top:2px;}
        .dpto-mov-kpi-sub{font-size:10px;font-weight:700;color:#94a3b8;margin-top:5px;}
    </style>
    <div class="dpto-mov-wrap">
        <div style="font-size:28px;font-weight:950;color:#70008f;margin-bottom:4px;">📍 Ranking Departamentos — Móvil</div>
        <div style="font-size:13px;font-weight:700;color:#64748b;">Misma base del Resumen General. Fuente: columna Datos Instalación - Departamento de MOVIL_DC y MOVIL_TELETALK.</div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">Departamentos</div><div class="dpto-mov-kpi-val" style="color:#70008f;">{n_dptos:,}</div><div class="dpto-mov-kpi-sub">zonas con gestión</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">Total Ventas</div><div class="dpto-mov-kpi-val" style="color:#111827;">{total_ventas_g:,}</div><div class="dpto-mov-kpi-sub">misma base resumen</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">Activas (Pagadas)</div><div class="dpto-mov-kpi-val" style="color:#059669;">{total_activas_g:,}</div><div class="dpto-mov-kpi-sub">COMISION CLARO &gt; 0</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">% Conversión</div><div class="dpto-mov-kpi-val" style="color:#0f4287;">{conv_global:.2f}%</div><div class="dpto-mov-kpi-sub">activas / total</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">% Caída</div><div class="dpto-mov-kpi-val" style="color:#dc2626;">{caida_global:.2f}%</div><div class="dpto-mov-kpi-sub">no activas / total</div></div>', unsafe_allow_html=True)

    st.write("")

    k6, k7, k8 = st.columns(3)
    with k6:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">Lima</div><div class="dpto-mov-kpi-val" style="color:#0f4287;">{lima_ventas:,}</div><div class="dpto-mov-kpi-sub">{lima_pct:.2f}% del total</div></div>', unsafe_allow_html=True)
    with k7:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">Provincia</div><div class="dpto-mov-kpi-val" style="color:#7c3aed;">{prov_ventas:,}</div><div class="dpto-mov-kpi-sub">{prov_pct:.2f}% del total</div></div>', unsafe_allow_html=True)
    with k8:
        st.markdown(f'<div class="dpto-mov-kpi"><div class="dpto-mov-kpi-lbl">Comisión Total</div><div class="dpto-mov-kpi-val" style="color:#0891b2;font-size:20px;">{formatear_moneda(total_comision_g)}</div><div class="dpto-mov-kpi-sub">suma real CLARO</div></div>', unsafe_allow_html=True)

    st.write("")

    if not rank_df.empty:
        top10 = rank_df.head(10).copy()
        try:
            import altair as alt
            chart_data = top10[["Departamento", "Activas", "No Activas"]].melt(
                "Departamento", var_name="Estado", value_name="Cantidad"
            )
            chart = (
                alt.Chart(chart_data)
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Cantidad:Q", title="Ventas"),
                    y=alt.Y("Departamento:N", sort="-x", title=""),
                    color=alt.Color(
                        "Estado:N",
                        scale=alt.Scale(domain=["Activas", "No Activas"], range=["#059669", "#dc2626"]),
                        legend=alt.Legend(title="Estado")
                    ),
                    tooltip=["Departamento", "Estado", "Cantidad"]
                )
                .properties(height=max(260, len(top10) * 42), title="Top 10 departamentos — Activas vs No Activas")
                .configure_axis(labelFontSize=12, titleFontSize=13)
                .configure_title(fontSize=17, fontWeight="bold", color="#70008f")
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            pass

    st.markdown("#### Tabla gerencial por departamento")
    tabla = rank_df[cols].copy()
    total_row = pd.DataFrame([{
        "Rank": "TOTAL",
        "Departamento": "",
        "Total Ventas": total_ventas_g,
        "Activas": total_activas_g,
        "No Activas": total_no_activas_g,
        "% Conversión": round(conv_global, 2),
        "% Caída": round(caida_global, 2),
        "Comisión": total_comision_g,
    }])
    tabla = pd.concat([tabla, total_row], ignore_index=True)
    tabla["Comisión"] = tabla["Comisión"].apply(lambda x: formatear_moneda(x) if isinstance(x, (int, float)) else x)
    tabla["% Conversión"] = tabla["% Conversión"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)
    tabla["% Caída"] = tabla["% Caída"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)

    def _color_activas_movil(val):
        try:
            v = float(val)
            max_v = float(pd.to_numeric(tabla["Activas"], errors="coerce").fillna(0).max())
            alpha = 0.10 + (min(v / max_v, 1) * 0.28) if max_v > 0 else 0.10
            return f"background-color: rgba(5,150,105,{alpha}); color:#064e3b; font-weight:800; text-align:center;"
        except Exception:
            return "text-align:center;"

    def _color_no_activas_movil(val):
        try:
            v = float(val)
            max_v = float(pd.to_numeric(tabla["No Activas"], errors="coerce").fillna(0).max())
            alpha = 0.08 + (min(v / max_v, 1) * 0.24) if max_v > 0 else 0.08
            return f"background-color: rgba(220,38,38,{alpha}); color:#7f1d1d; font-weight:800; text-align:center;"
        except Exception:
            return "text-align:center;"

    def _resaltar_total_movil_dpto(row):
        if str(row.get("Rank", "")).upper() == "TOTAL":
            return ["background-color:#70008f; color:white; font-weight:900;" for _ in row]
        return ["" for _ in row]

    st.dataframe(
        tabla.style
        .apply(_resaltar_total_movil_dpto, axis=1)
        .map(_color_activas_movil, subset=["Activas"])
        .map(_color_no_activas_movil, subset=["No Activas"])
        .set_properties(**{"text-align": "center", "font-size": "13px"})
        .set_properties(subset=["Departamento"], **{"text-align": "left", "font-weight": "bold"}),
        use_container_width=True,
        height=min(650, 90 + 36 * len(tabla))
    )



# =========================================================
# HELPER: Precio Oferta Móvil (Productos - Precio Oferta)
# =========================================================
def _obtener_col_precio_oferta_movil(df):
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "precio" in norm and "oferta" in norm:
            return c
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "precio" in norm or "oferta" in norm:
            return c
    return None

def _obtener_col_tipo_operacion_movil_general(df):
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "tipo" in norm and ("operacion" in norm or "operación" in norm):
            return c
    for c in df.columns:
        norm = c.lower().replace("ó","o").replace("á","a")
        if "tipo" in norm or "transaccion" in norm:
            return c
    return None

@st.cache_data(ttl=3600)
def construir_precio_oferta_movil(filtro_mes="Todos los meses", filtro_canal="Todos"):
    """
    Lee MOVIL_DC.csv y MOVIL_TELETALK.csv.
    Agrupa por Plan (Productos - Precio Oferta) y Tipo de Operacion
    (PORTABILIDAD / LINEA NUEVA) para saber cuántos se vendieron de cada plan.
    El total de ventas coincide con el KPI del cuadro principal.
    """
    configuracion = [("D&C", "MOVIL_DC.csv"), ("Teletalk", "MOVIL_TELETALK.csv")]
    bases = []
    for canal, archivo in configuracion:
        if filtro_canal != "Todos" and canal != filtro_canal:
            continue
        df = cargar_csv(archivo)
        if df.empty:
            continue
        df = df.copy()

        # ---- Fecha ----
        col_fecha = next((c for c in df.columns if "fecha" in c.lower() and "venta" in c.lower()), None)
        if not col_fecha:
            col_fecha = next((c for c in df.columns if "fecha" in c.lower()), None)
        if col_fecha:
            df["_FECHA_DT"] = pd.to_datetime(df[col_fecha], errors="coerce", dayfirst=True)
            if filtro_mes != "Todos los meses":
                m, y = parse_mes_anio(filtro_mes)
                if m and y:
                    df = df[(df["_FECHA_DT"].dt.month == m) & (df["_FECHA_DT"].dt.year == y)].copy()
        if df.empty:
            continue

        # ---- Tipo de Operacion (Cliente - Tipo De Operacion) ----
        col_tipo = _obtener_col_tipo_operacion_movil_general(df)
        if col_tipo:
            tipo_raw = (df[col_tipo].fillna("").astype(str)
                        .str.upper().str.strip()
                        .str.replace("Í", "I", regex=False)
                        .str.replace("Á", "A", regex=False))
            df["_TIPO"] = tipo_raw.apply(
                lambda t: "PORTABILIDAD" if "PORTABILIDAD" in t
                else ("LINEA NUEVA" if t in ["ALTA", "ALTA NUEVA", "LINEA NUEVA"] else "OTROS")
            )
        else:
            df["_TIPO"] = "SIN DATO"

        # ---- Plan = Productos - Precio Oferta (valor de precio como etiqueta del plan) ----
        col_precio = _obtener_col_precio_oferta_movil(df)
        if col_precio:
            # El precio del plan es la etiqueta del plan
            df["_PLAN_PRECIO"] = pd.to_numeric(df[col_precio], errors="coerce")
            df["_PLAN_LABEL"] = df["_PLAN_PRECIO"].apply(
                lambda v: f"S/ {v:,.2f}" if pd.notna(v) and v > 0 else "Sin Precio"
            )
        else:
            df["_PLAN_PRECIO"] = 0.0
            df["_PLAN_LABEL"] = "Sin Precio"

        df["Canal"] = canal
        bases.append(df[["Canal", "_TIPO", "_PLAN_LABEL", "_PLAN_PRECIO"]])

    if not bases:
        return pd.DataFrame(columns=["Canal", "Tipo Operacion", "Plan", "Precio Oferta"])

    resultado = pd.concat(bases, ignore_index=True)
    resultado = resultado.rename(columns={
        "_TIPO": "Tipo Operacion",
        "_PLAN_LABEL": "Plan",
        "_PLAN_PRECIO": "Precio Oferta"
    })
    return resultado


def mostrar_resumen_precio_oferta_movil(df_precio):
    """
    Vista gerencial de Precio Oferta:
    - Agrupa planes (Productos - Precio Oferta) para saber cuántos se vendieron de cada uno.
    - Diferencia PORTABILIDAD vs LINEA NUEVA (Cliente - Tipo De Operacion).
    - El total de ventas coincide con el KPI del cuadro principal.
    """
    if df_precio is None or df_precio.empty:
        st.warning("No se encontraron datos de Precio Oferta. Verifica que MOVIL_DC.csv y MOVIL_TELETALK.csv contengan la columna 'Productos - Precio Oferta'.")
        return

    st.markdown("""
    <style>
        .precio-wrap{background:linear-gradient(135deg,rgba(255,255,255,.98),rgba(240,245,255,.96));
            border:1px solid rgba(15,66,135,.16);border-radius:24px;padding:20px 22px;
            box-shadow:0 14px 42px rgba(15,66,135,.12);margin:8px 0 18px 0;}
        .precio-title{font-size:26px;font-weight:950;color:#0f4287;margin-bottom:4px;}
        .precio-sub{font-size:13px;font-weight:700;color:#64748b;margin-bottom:8px;}
        .precio-kpi{background:white;border-radius:18px;padding:14px 10px;text-align:center;
            border:1px solid rgba(15,66,135,.12);box-shadow:0 6px 18px rgba(0,0,0,.06);}
        .precio-kpi-lbl{font-size:10px;font-weight:900;color:#64748b;letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px;}
        .precio-kpi-val{font-size:22px;font-weight:950;margin-top:4px;}
    </style>
    <div class="precio-wrap">
        <div class="precio-title">📦 Agrupación de Planes por Precio Oferta</div>
        <div class="precio-sub">Fuente: Productos - Precio Oferta de MOVIL_DC y MOVIL_TELETALK · Clasificado por Cliente - Tipo De Operacion (PORTABILIDAD / LINEA NUEVA)</div>
    </div>
    """, unsafe_allow_html=True)

    tipos_interes = ["PORTABILIDAD", "LINEA NUEVA"]
    df_valido = df_precio[df_precio["Tipo Operacion"].isin(tipos_interes)].copy()
    total_registros = len(df_precio)
    total_validos = len(df_valido)

    # KPI resumen total
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="precio-kpi"><div class="precio-kpi-lbl">Total Ventas</div><div class="precio-kpi-val" style="color:#111827;">{total_registros:,}</div></div>', unsafe_allow_html=True)
    with k2:
        porta = int((df_precio["Tipo Operacion"] == "PORTABILIDAD").sum())
        st.markdown(f'<div class="precio-kpi"><div class="precio-kpi-lbl">Portabilidad</div><div class="precio-kpi-val" style="color:#0f4287;">{porta:,}</div></div>', unsafe_allow_html=True)
    with k3:
        linea = int((df_precio["Tipo Operacion"] == "LINEA NUEVA").sum())
        st.markdown(f'<div class="precio-kpi"><div class="precio-kpi-lbl">Línea Nueva</div><div class="precio-kpi-val" style="color:#7c3aed;">{linea:,}</div></div>', unsafe_allow_html=True)
    with k4:
        n_planes = df_precio["Plan"].nunique()
        st.markdown(f'<div class="precio-kpi"><div class="precio-kpi-lbl">Planes distintos</div><div class="precio-kpi-val" style="color:#0891b2;">{n_planes:,}</div></div>', unsafe_allow_html=True)

    st.write("")

    # ---- Tabla principal: Planes agrupados por Tipo Operacion ----
    st.markdown("#### 📊 Ventas por Plan y Tipo de Operación")
    st.caption("Cada fila es un plan (precio). Las columnas muestran cuántas ventas de Portabilidad y Línea Nueva corresponden a ese plan.")

    if df_valido.empty:
        st.info("No hay registros de PORTABILIDAD o LINEA NUEVA para el filtro seleccionado.")
    else:
        pivot_planes = (
            df_valido.groupby(["Plan", "Tipo Operacion"], as_index=False)
            .agg(Ventas=("Canal", "count"))
        )
        tabla_planes = pivot_planes.pivot_table(
            index="Plan", columns="Tipo Operacion", values="Ventas", aggfunc="sum", fill_value=0
        ).reset_index()
        tabla_planes.columns.name = None
        for col in ["PORTABILIDAD", "LINEA NUEVA"]:
            if col not in tabla_planes.columns:
                tabla_planes[col] = 0
        tabla_planes["Total"] = tabla_planes[["PORTABILIDAD", "LINEA NUEVA"]].sum(axis=1)
        tabla_planes = tabla_planes.sort_values("Total", ascending=False).reset_index(drop=True)
        tabla_planes.insert(0, "Rank", tabla_planes.index + 1)

        # Fila total
        total_row_planes = pd.DataFrame([{
            "Rank": "TOTAL",
            "Plan": "",
            "PORTABILIDAD": int(tabla_planes["PORTABILIDAD"].sum()),
            "LINEA NUEVA": int(tabla_planes["LINEA NUEVA"].sum()),
            "Total": int(tabla_planes["Total"].sum()),
        }])
        tabla_planes_display = pd.concat([tabla_planes, total_row_planes], ignore_index=True)

        def _color_total_plan(row):
            if str(row.get("Rank", "")).upper() == "TOTAL":
                return ["background-color:#0f4287;color:white;font-weight:900;text-align:center;" for _ in row]
            return ["text-align:center;" for _ in row]

        st.dataframe(
            tabla_planes_display.style
            .apply(_color_total_plan, axis=1)
            .set_properties(**{"text-align": "center", "font-size": "13px"})
            .set_properties(subset=["Plan"], **{"text-align": "left", "font-weight": "bold"}),
            use_container_width=True,
            height=min(600, 90 + 36 * len(tabla_planes_display))
        )

        # Gráfico top planes
        try:
            import altair as alt
            top = tabla_planes.head(10).copy()
            chart_data = top[["Plan", "PORTABILIDAD", "LINEA NUEVA"]].melt(
                "Plan", var_name="Tipo", value_name="Ventas"
            )
            chart = (
                alt.Chart(chart_data)
                .mark_bar(cornerRadiusEnd=5, opacity=0.90)
                .encode(
                    x=alt.X("Ventas:Q", title="Ventas"),
                    y=alt.Y("Plan:N", sort="-x", title="Plan (Precio Oferta)"),
                    color=alt.Color("Tipo:N",
                        scale=alt.Scale(domain=["PORTABILIDAD", "LINEA NUEVA"], range=["#0f4287", "#7c3aed"]),
                        legend=alt.Legend(title="Tipo Operación")),
                    tooltip=["Plan", "Tipo", "Ventas"]
                )
                .properties(height=max(280, len(top) * 44), title="Top 10 Planes — Portabilidad vs Línea Nueva")
                .configure_title(fontSize=15, fontWeight="bold", color="#0f4287")
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            pass

    st.write("")

    # ---- Desglose por Canal ----
    st.markdown("#### 🏢 Desglose por Canal y Plan")
    for canal in df_precio["Canal"].unique():
        df_canal = df_precio[df_precio["Canal"] == canal]
        df_canal_valido = df_canal[df_canal["Tipo Operacion"].isin(tipos_interes)]
        with st.expander(f"📂 {canal} — {len(df_canal):,} ventas"):
            if df_canal_valido.empty:
                st.info("Sin datos de Portabilidad o Línea Nueva.")
                continue
            piv = (
                df_canal_valido.groupby(["Plan", "Tipo Operacion"], as_index=False)
                .agg(Ventas=("Canal", "count"))
                .pivot_table(index="Plan", columns="Tipo Operacion", values="Ventas", aggfunc="sum", fill_value=0)
                .reset_index()
            )
            piv.columns.name = None
            for col in ["PORTABILIDAD", "LINEA NUEVA"]:
                if col not in piv.columns:
                    piv[col] = 0
            piv["Total"] = piv[["PORTABILIDAD", "LINEA NUEVA"]].sum(axis=1)
            piv = piv.sort_values("Total", ascending=False).reset_index(drop=True)
            fila_t = pd.DataFrame([{"Plan": "TOTAL", "PORTABILIDAD": int(piv["PORTABILIDAD"].sum()),
                                     "LINEA NUEVA": int(piv["LINEA NUEVA"].sum()), "Total": int(piv["Total"].sum())}])
            st.dataframe(pd.concat([piv, fila_t], ignore_index=True), use_container_width=True, height=min(420, 80 + 36 * (len(piv) + 1)))

    # Descarga
    st.download_button(
        "⬇️ Descargar Agrupación Planes Móvil",
        data=df_precio.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="planes_movil_agrupados.csv",
        mime="text/csv",
        key="dl_precio_oferta_movil_nuevo"
    )

def mostrar_detalle_movil_general():
    color_titulo = "#70008f"
    color_borde = "#6d0b8c"

    set_bg(img_caratula)

    st.markdown(
        f'<div style="color:{color_titulo};font-size:36px;font-weight:900;margin-bottom:4px;">'
        f'Detalle MÓVIL GENERAL</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div style="color:{color_titulo};font-weight:800;font-size:16px;margin-bottom:16px;">'
        f'Resumen general por Fecha de Venta usando solo MOVIL_DC.csv y MOVIL_TELETALK.csv</div>',
        unsafe_allow_html=True
    )
    st.write("---")

    # Para Detalle Móvil General el filtro principal se alimenta SOLO de MOVIL_DC.csv y MOVIL_TELETALK.csv.
    # No se mezclan meses de caídas/CLARO ni de fija.
    meses_general = obtener_meses_movil_general()
    meses = ["Todos los meses"] + sorted(
        set(meses_general) - {"Todos los meses"},
        key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))
    )

    st.markdown("### 🔎 Filtros")
    c1, c2, c3 = st.columns(3)

    with c1:
        filtro_mes_list = st.multiselect("Fecha de Venta", meses[1:], default=[], key="movil_fecha_venta", placeholder="Todos los meses")
        filtro_mes = filtro_mes_list if filtro_mes_list else ["Todos los meses"]

    with c2:
        sel_canal = st.multiselect("Canal", ["D&C", "Teletalk"], default=[], key="movil_canal", placeholder="Todos los canales")
    filtro_canal = sel_canal[0] if len(sel_canal) == 1 else "Todos"

    with st.spinner("Cargando resumen móvil general por Cliente - Tipo De Operacion..."):
        dfs_general = []
        dfs_caidas = []
        for mes in filtro_mes:
            dfs_general.append(construir_resumen_movil_general(mes))
            dfs_caidas.append(construir_detalle_movil_teletalk_caidas(mes))
        df_general = pd.concat(dfs_general, ignore_index=True) if dfs_general else pd.DataFrame()
        df_caidas_tt = pd.concat(dfs_caidas, ignore_index=True) if dfs_caidas else pd.DataFrame()

    df_opciones = df_general.copy()
    if sel_canal and not df_opciones.empty:
        df_opciones = df_opciones[df_opciones["Canal"].isin(sel_canal)].copy()

    with c3:
        meses_instalacion = []
        if not df_opciones.empty and "_FECHA_INSTALACION_DT" in df_opciones.columns:
            fechas_inst = pd.to_datetime(df_opciones["_FECHA_INSTALACION_DT"], errors="coerce").dropna()
            meses_set = {f"{MESES_ES[f.month].capitalize()} {f.year}" for f in fechas_inst}
            meses_instalacion = sorted(meses_set, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0)))
        sel_fecha_instalacion = st.multiselect("Fecha de Instalación", meses_instalacion, default=[], key="movil_fecha_instalacion", placeholder="Todas las fechas")

    c4, c5, c6, c7 = st.columns(4)
    with c4:
        sel_pago = st.multiselect("Estado de Pago", ["PAGADA", "NO PAGADA"], default=[], key="movil_estado_pago", placeholder="Todos los estados")
    with c5:
        lista_supervisores = []
        if not df_opciones.empty and "SUPERVISOR" in df_opciones.columns:
            lista_supervisores = sorted(df_opciones["SUPERVISOR"].fillna("Sin Supervisor").astype(str).str.strip().replace("", "Sin Supervisor").unique().tolist())
        sel_supervisor = st.multiselect("Supervisor", lista_supervisores, default=[], key="movil_supervisor", placeholder="Todos los supervisores")
    with c6:
        tipificaciones_lista = [t for t in obtener_tipificaciones_solo_movil_general() if t != "Todos"]
        sel_tipificacion = st.multiselect("Tipificación", tipificaciones_lista, default=[], key="movil_tipificacion", placeholder="Todas las tipificaciones")
    with c7:
        colas_movil = ["EXTERNO"]
        if not df_opciones.empty and "COLA" in df_opciones.columns:
            colas_movil = sorted(df_opciones["COLA"].fillna("EXTERNO").astype(str).unique().tolist())
        sel_cola = st.selectbox("Cola", ["Todos"] + colas_movil, key="movil_cola")

    if df_general.empty and df_caidas_tt.empty:
        st.warning(
            "No se encontraron datos. Verifica que existan MOVIL_DC.csv y MOVIL_TELETALK.csv en la carpeta del app.py, "
            "y que tengan Fecha de Venta, Cliente - Tipo De Operacion, Estados - Venta Especificacion y Datos Adicionales - Supervisor."
        )
        return

    df_filtrado = df_general.copy()
    if sel_canal and not df_filtrado.empty:
        df_filtrado = df_filtrado[df_filtrado["Canal"].isin(sel_canal)].copy()

    if sel_pago and "Estado Pago" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Estado Pago"].isin(sel_pago)].copy()

    if sel_supervisor and "SUPERVISOR" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(sel_supervisor)].copy()

    if sel_tipificacion and "TIPIS" in df_filtrado.columns:
        tipis_norm = df_filtrado["TIPIS"].fillna("Sin Tipificación").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        df_filtrado = df_filtrado[tipis_norm.isin([str(t).strip() for t in sel_tipificacion])].copy()

    if sel_cola != "Todos" and "COLA" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["COLA"].fillna("EXTERNO") == sel_cola].copy()

    if sel_fecha_instalacion and "_FECHA_INSTALACION_DT" in df_filtrado.columns and not df_filtrado.empty:
        fechas_inst_filtrado = pd.to_datetime(df_filtrado["_FECHA_INSTALACION_DT"], errors="coerce")
        mask_inst = pd.Series([False] * len(df_filtrado), index=df_filtrado.index)
        for _mes_inst in sel_fecha_instalacion:
            _m, _y = parse_mes_anio(_mes_inst)
            if _m and _y:
                mask_inst |= ((fechas_inst_filtrado.dt.month == _m) & (fechas_inst_filtrado.dt.year == _y))
        df_filtrado = df_filtrado[mask_inst].copy()

    base_valida = df_filtrado[df_filtrado.get("Venta Valida", False)].copy() if not df_filtrado.empty else pd.DataFrame()

    # ── KPI Total Ventas: leer directo de MOVIL_DC + MOVIL_TELETALK excluyendo productos no comerciales ──
    _PRODUCTOS_EXCLUIR = [
        "CHIP PREPAGO", "PRE A PRE", "2 PLAY 800 MBPS",
        "IFI INTERNET INALAMBRICO", "TFI", "OLO INTERNET PORTATIL"
    ]
    _dfs_kpi = []
    _totales_kpi_canal = {}
    for _canal_kpi, _archivo_kpi in [("D&C", "MOVIL_DC.csv"), ("Teletalk", "MOVIL_TELETALK.csv")]:
        if sel_canal and _canal_kpi not in sel_canal:
            continue
        _df_kpi, _ = _leer_csv_movil_con_fallback([_archivo_kpi])
        if _df_kpi.empty:
            continue
        if filtro_mes != ["Todos los meses"]:
            _fecha_kpi, _ = _obtener_fecha_venta_movil_general(_df_kpi)
            _df_kpi["_FECHA_KPI_DT"] = _fecha_kpi
            _mask_mes = pd.Series([False] * len(_df_kpi), index=_df_kpi.index)
            for _mes_str in filtro_mes:
                _m, _y = parse_mes_anio(_mes_str)
                if _m and _y:
                    _mask_mes |= ((_df_kpi["_FECHA_KPI_DT"].dt.month == _m) & (_df_kpi["_FECHA_KPI_DT"].dt.year == _y))
            _df_kpi = _df_kpi[_mask_mes].copy()
        _col_prod_kpi = encontrar_columna_flexible(_df_kpi, [
            "Productos - producto Especificacion", "Productos - Producto Especificacion",
            "PRODUCTOS - PRODUCTO ESPECIFICACION", "Producto Especificacion",
            "PRODUCTO ESPECIFICACION", "Producto", "PRODUCTO", "Plan", "PLAN"
        ])
        if _col_prod_kpi:
            _prod_norm = _df_kpi[_col_prod_kpi].fillna("").astype(str).str.strip().str.upper()
            _df_kpi = _df_kpi[~_prod_norm.isin([p.upper() for p in _PRODUCTOS_EXCLUIR])].copy()
        _dfs_kpi.append(_df_kpi)
        _totales_kpi_canal[_canal_kpi] = _totales_kpi_canal.get(_canal_kpi, 0) + len(_df_kpi)
    total_ventas = int(sum(len(d) for d in _dfs_kpi))

    # Tabla "Resumen General por Canal" alineada con la lógica de los KPIs:
    # Total Ventas por canal = lectura directa MOVIL_DC/MOVIL_TELETALK con exclusiones (igual al KPI).
    resumen_general = resumen_general_movil_df(df_filtrado, totales_kpi=_totales_kpi_canal)

    pagadas_total = int((base_valida["Estado Pago"] == "PAGADA").sum()) if not base_valida.empty and "Estado Pago" in base_valida.columns else 0
    no_pagadas_total = total_ventas - pagadas_total
    pct_caida = (no_pagadas_total / total_ventas * 100) if total_ventas > 0 else 0

    # Portabilidad y Alta se cuentan SOLO sobre las pagadas para que Alta + Portabilidad = Pagadas.
    base_pagada = base_valida[base_valida["Estado Pago"] == "PAGADA"] if not base_valida.empty and "Estado Pago" in base_valida.columns else pd.DataFrame()
    if not base_pagada.empty:
        tipo_norm = base_pagada["Tipo Operacion"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.upper().str.replace("Í", "I", regex=False)
        portabilidad_total = int(tipo_norm.eq("PORTABILIDAD").sum())
        alta_total = int(tipo_norm.isin(["ALTA", "ALTA NUEVA"]).sum())
    else:
        portabilidad_total = 0
        alta_total = 0
    comision_total = _sumar_comision_real_unica(base_valida)
    ticket_promedio_movil = (comision_total / pagadas_total) if pagadas_total > 0 else 0.0

    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    _kpi_movil_teletalk_card(k1, "Total Ventas", f"{total_ventas:,}", "Ventas registradas", "#111827")
    _kpi_movil_teletalk_card(k2, "Pagadas", f"{pagadas_total:,}", "COMISION TOTAL > 0", "#059669")
    _kpi_movil_teletalk_card(k3, "No Pagadas", f"{no_pagadas_total:,}", "Total Ventas - Pagadas", "#dc2626")
    _kpi_movil_teletalk_card(k4, "% Caída", f"{pct_caida:.2f}%", "No pagadas / Total ventas", "#f97316")
    _kpi_movil_teletalk_card(k5, "Portabilidad", f"{portabilidad_total:,}", "Pagadas · Portabilidad", "#0f4287")
    _kpi_movil_teletalk_card(k6, "Alta", f"{alta_total:,}", "Pagadas · Alta", "#7c3aed")
    _kpi_movil_teletalk_card(k7, "Comisión", formatear_moneda(comision_total), "Cruce DNI + mes/año", "#0891b2")
    _kpi_movil_teletalk_card(k8, "Promedio Prime", formatear_moneda(ticket_promedio_movil), "Comisión / Pagadas", "#0891b2")

    st.write("")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 Resumen General",
        "📆 Ventas por Día",
        "🏆 Ranking Supervisor",
        "👥 Ranking Asesores",
        "📍 Ranking Departamentos",
        "📊 Caídas Teletalk",
        "📦 Planes por Precio Oferta"
    ])

    with tab1:
        mostrar_resumen_general_movil_premium(resumen_general)

        if not resumen_general.empty:
            st.download_button(
                "⬇️ Descargar Resumen General Móvil",
                data=resumen_general.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name="resumen_general_movil.csv",
                mime="text/csv",
                key="dl_resumen_general_movil",
                on_click=registrar_descarga,
                args=("Detalle Móvil General", "resumen_general_movil.csv", f"Fecha Venta: {', '.join(filtro_mes)} | Canal: {filtro_canal}")
            )

        st.markdown("#### Detalle de ventas")
        if df_filtrado.empty:
            st.warning("Sin detalle para mostrar.")
        else:
            columnas_detalle = [
                "Canal", "Archivo", "FECHA DE VENTA", "Documento", "Tipo Operacion",
                "Estado Pago", "Cliente", "SUPERVISOR", "TIPIS", "ASESOR", "COLA"
            ]
            columnas_detalle = [c for c in columnas_detalle if c in df_filtrado.columns]
            detalle = df_filtrado[columnas_detalle].copy()
            st.dataframe(detalle, use_container_width=True, height=420)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                detalle.to_excel(writer, index=False, sheet_name="Detalle Movil")
                resumen_general.to_excel(writer, index=False, sheet_name="Resumen")
            output.seek(0)
            st.download_button(
                "⬇️ Descargar Detalle Móvil General en Excel",
                data=output.getvalue(),
                file_name="detalle_movil_general.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_detalle_movil_general_excel",
                on_click=registrar_descarga,
                args=("Detalle Móvil General", "detalle_movil_general.xlsx", f"Fecha Venta: {', '.join(filtro_mes)} | Canal: {', '.join(sel_canal) if sel_canal else 'Todos'}")
            )

    with tab2:
        titulo_periodo = "Ventas por mes" if len(filtro_mes) > 1 or filtro_mes[0] == "Todos los meses" else "Ventas por día"
        st.markdown(f"#### 📆 {titulo_periodo}")

        base_periodo = df_filtrado.copy()
        if not base_periodo.empty and "Venta Valida" in base_periodo.columns and "_FECHA_VENTA_DT" in base_periodo.columns:
            base_periodo = base_periodo[base_periodo["Venta Valida"] & base_periodo["_FECHA_VENTA_DT"].notna()].copy()
        else:
            base_periodo = pd.DataFrame()

        if base_periodo.empty:
            st.warning("No hay fechas válidas para el filtro seleccionado.")
        else:
            if filtro_mes == "Todos los meses":
                base_periodo["Periodo"] = base_periodo["_FECHA_VENTA_DT"].dt.to_period("M").dt.to_timestamp()
                base_periodo["Periodo Texto"] = base_periodo["Periodo"].apply(lambda x: f"{MESES_ES[int(x.month)]} {int(x.year)}")
                orden_periodo = base_periodo.drop_duplicates("Periodo").sort_values("Periodo")["Periodo Texto"].tolist()
                eje_titulo = "Mes"
                graf_titulo = "Ventas móviles por mes"
            else:
                base_periodo["Periodo"] = base_periodo["_FECHA_VENTA_DT"].dt.normalize()
                base_periodo["Periodo Texto"] = base_periodo["Periodo"].dt.strftime("%d/%m/%Y")
                orden_periodo = base_periodo.drop_duplicates("Periodo").sort_values("Periodo")["Periodo Texto"].tolist()
                eje_titulo = "Fecha"
                graf_titulo = "Ventas móviles por día"

            df_periodo = (
                base_periodo.groupby(["Periodo", "Periodo Texto", "Canal"], as_index=False)
                .agg(Ventas=("Tipo Operacion", "count"))
            )
            chart_data = df_periodo.copy()
            try:
                import altair as alt
                chart = (
                    alt.Chart(chart_data)
                    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                    .encode(
                        x=alt.X("Periodo Texto:N", sort=orden_periodo, title=eje_titulo),
                        y=alt.Y("Ventas:Q", title="Ventas"),
                        xOffset="Canal:N",
                        color=alt.Color("Canal:N", scale=alt.Scale(domain=["D&C", "Teletalk"], range=["#0f4287", "#70008f"])),
                        tooltip=["Periodo Texto", "Canal", "Ventas"]
                    )
                    .properties(height=340, title=graf_titulo)
                    .configure_title(fontSize=18, fontWeight="bold", color="#111827")
                )
                st.altair_chart(chart, use_container_width=True)
            except Exception:
                st.info("No se pudo mostrar el gráfico, pero la tabla está disponible.")

            pivot = df_periodo.pivot_table(index=["Periodo", "Periodo Texto"], columns="Canal", values="Ventas", aggfunc="sum", fill_value=0).reset_index()
            for c in ["D&C", "Teletalk"]:
                if c not in pivot.columns:
                    pivot[c] = 0
            estados = base_periodo.groupby(["Periodo", "Periodo Texto"], as_index=False).agg(
                Pagadas=("Estado Pago", lambda x: (x == "PAGADA").sum()),
                **{"No Pagadas": ("Estado Pago", lambda x: (x == "NO PAGADA").sum())}
            )
            comisiones = []
            for (periodo, periodo_txt), g in base_periodo.groupby(["Periodo", "Periodo Texto"]):
                comisiones.append({"Periodo": periodo, "Periodo Texto": periodo_txt, "Comision": _sumar_comision_real_unica(g)})
            com = pd.DataFrame(comisiones)
            tabla_periodo = pivot.merge(estados, on=["Periodo", "Periodo Texto"], how="left").merge(com, on=["Periodo", "Periodo Texto"], how="left")
            tabla_periodo["Total Ventas"] = pd.to_numeric(tabla_periodo["D&C"], errors="coerce").fillna(0) + pd.to_numeric(tabla_periodo["Teletalk"], errors="coerce").fillna(0)
            tabla_periodo = tabla_periodo.sort_values("Periodo")[["Periodo Texto", "D&C", "Teletalk", "Total Ventas", "Pagadas", "No Pagadas", "Comision"]]
            tabla_periodo = tabla_periodo.rename(columns={"Periodo Texto": eje_titulo})
            tabla_show = tabla_periodo.copy()
            tabla_show["Comision"] = pd.to_numeric(tabla_show["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
            total_row = pd.DataFrame([{
                eje_titulo: "TOTAL",
                "D&C": int(tabla_periodo["D&C"].sum()),
                "Teletalk": int(tabla_periodo["Teletalk"].sum()),
                "Total Ventas": int(tabla_periodo["Total Ventas"].sum()),
                "Pagadas": int(tabla_periodo["Pagadas"].sum()),
                "No Pagadas": int(tabla_periodo["No Pagadas"].sum()),
                "Comision": formatear_moneda(pd.to_numeric(tabla_periodo["Comision"], errors="coerce").fillna(0).sum())
            }])
            st.dataframe(pd.concat([tabla_show, total_row], ignore_index=True), use_container_width=True, height=420)

    with tab3:
        st.markdown("#### 🏆 Ranking Supervisor")
        mostrar_ranking_supervisor_movil_expandible(df_filtrado)

    with tab4:
        st.markdown("#### 👥 Ranking Asesores")
        r_ase = ranking_movil_por_columna(df_filtrado, "ASESOR", "ASESOR")
        if r_ase.empty:
            st.warning("No se encontraron asesores.")
        else:
            show = r_ase.copy()
            show["Comision"] = show["Comision"].map(formatear_moneda)
            st.dataframe(show, use_container_width=True, height=460)

    with tab5:
        mostrar_ranking_departamentos_movil_gerencial(df_filtrado, ", ".join(filtro_mes) if len(filtro_mes) > 1 else filtro_mes[0], filtro_canal)

    with tab6:
        st.markdown("#### 📊 Caídas Teletalk")
        if df_caidas_tt.empty:
            st.info("No se encontró información de caídas Teletalk para el filtro seleccionado.")
        else:
            resumen_tt = _resumen_etapas_teletalk(df_caidas_tt)
            tabla_tt = resumen_tt.copy()
            tabla_tt["Comision"] = tabla_tt["Comision"].map(formatear_moneda)
            st.dataframe(tabla_tt, use_container_width=True, height=210)
            try:
                _grafico_resumen_etapa_gerencial(resumen_tt)
            except Exception:
                pass
            mostrar_resumen_etapas_expandible_teletalk(df_caidas_tt, resumen_tt, ", ".join(filtro_mes) if len(filtro_mes) > 1 else filtro_mes[0])

    with tab7:
        st.markdown("#### 📦 Planes más vendidos por Modalidad")
        st.caption("Fuente: Productos - Producto Especificacion · Cliente - Tipo De Operacion | MOVIL_DC.csv + MOVIL_TELETALK.csv")

        if base_valida.empty or "Plan" not in base_valida.columns:
            st.warning("No se encontraron datos de planes para el filtro seleccionado.")
        else:
            _bv = base_valida.copy()

            # Normalizar Plan
            _bv["_PLAN"] = (_bv["Plan"].fillna("Sin Plan").astype(str)
                            .str.strip()
                            .replace(["nan","None","NaN",""], "Sin Plan"))
            _bv["_PLAN"] = _bv["_PLAN"].apply(lambda x: "Sin Plan" if x.strip() == "" else x)

            # Normalizar Tipo Operacion
            _tipo_norm = (_bv["Tipo Operacion"].fillna("").astype(str)
                          .str.upper().str.strip()
                          .str.replace("Í","I",regex=False)
                          .str.replace("Á","A",regex=False))
            _bv["_TIPO"] = _tipo_norm.apply(
                lambda t: "PORTABILIDAD" if t == "PORTABILIDAD"
                else ("LINEA NUEVA" if t in ["ALTA","ALTA NUEVA","LINEA NUEVA"] else "OTROS")
            )

            # Estado de pago
            _bv["_PAGADA"] = (_bv["Estado Pago"] == "PAGADA")

            # ── Total por plan = TODOS los registros (igual que KPI) ──
            _total_plan = _bv.groupby("_PLAN").size().reset_index(name="Total")

            # PORTABILIDAD y LINEA NUEVA por plan
            _porta_plan = (_bv[_bv["_TIPO"] == "PORTABILIDAD"]
                           .groupby("_PLAN").size().reset_index(name="PORTABILIDAD"))
            _linea_plan = (_bv[_bv["_TIPO"] == "LINEA NUEVA"]
                           .groupby("_PLAN").size().reset_index(name="LINEA NUEVA"))

            # Pagado y No Pagadas por plan
            _pag_plan   = (_bv[_bv["_PAGADA"]]
                           .groupby("_PLAN").size().reset_index(name="Pagado"))
            _nopag_plan = (_bv[~_bv["_PAGADA"]]
                           .groupby("_PLAN").size().reset_index(name="No Pagadas"))

            # Merge todo sobre _total_plan
            _pivot = _total_plan.copy()
            for _df_m, _col in [(_porta_plan,"PORTABILIDAD"), (_linea_plan,"LINEA NUEVA"),
                                 (_pag_plan,"Pagado"), (_nopag_plan,"No Pagadas")]:
                _pivot = _pivot.merge(_df_m, on="_PLAN", how="left")
            _pivot = _pivot.rename(columns={"_PLAN":"Plan"})
            _pivot = _pivot[_pivot["Plan"] != "Sin Plan"].copy()
            for _c in ["PORTABILIDAD","LINEA NUEVA","Pagado","No Pagadas"]:
                if _c not in _pivot.columns:
                    _pivot[_c] = 0
                _pivot[_c] = _pivot[_c].fillna(0).astype(int)

            _pivot["% Pagada"]    = (_pivot["Pagado"]    / _pivot["Total"] * 100).round(1).astype(str) + "%"
            _pivot["% No Pagadas"] = (_pivot["No Pagadas"] / _pivot["Total"] * 100).round(1).astype(str) + "%"

            _pivot = _pivot.sort_values("Total", ascending=False).reset_index(drop=True)
            _pivot.insert(0, "Rank", _pivot.index + 1)

            _col_order = ["Rank","Plan","LINEA NUEVA","PORTABILIDAD","Total","Pagado","No Pagadas","% Pagada","% No Pagadas"]
            _pivot = _pivot[[c for c in _col_order if c in _pivot.columns]]

            _grand_total = int(_pivot["Total"].sum())
            _grand_pag   = int(_pivot["Pagado"].sum())
            _grand_nopag = int(_pivot["No Pagadas"].sum())
            _tot_row = pd.DataFrame([{
                "Rank":         "TOTAL",
                "Plan":         "",
                "LINEA NUEVA":  int(_pivot["LINEA NUEVA"].sum()),
                "PORTABILIDAD": int(_pivot["PORTABILIDAD"].sum()),
                "Total":        _grand_total,
                "Pagado":       _grand_pag,
                "No Pagadas":   _grand_nopag,
                "% Pagada":     f"{(_grand_pag / max(_grand_total,1) * 100):.1f}%",
                "% No Pagadas": f"{(_grand_nopag / max(_grand_total,1) * 100):.1f}%",
            }])
            _tabla_disp = pd.concat([_pivot, _tot_row], ignore_index=True)

            def _estilo_plan(row):
                if str(row.get("Rank","")).upper() == "TOTAL":
                    return ["background-color:#70008f;color:white;font-weight:900;text-align:center;" for _ in row]
                return ["text-align:center;" for _ in row]

            st.dataframe(
                _tabla_disp.style.apply(_estilo_plan, axis=1)
                .set_properties(**{"text-align":"center","font-size":"13px"})
                .set_properties(subset=["Plan"],**{"text-align":"left","font-weight":"bold"}),
                use_container_width=True,
                height=min(650, 90 + 36*len(_tabla_disp))
            )

            # Gráfico top 10 planes
            try:
                import altair as alt
                _top10 = _pivot.head(10).copy()
                _cd = _top10[["Plan","PORTABILIDAD","LINEA NUEVA"]].melt(
                    "Plan", var_name="Modalidad", value_name="Ventas"
                )
                _ch = (
                    alt.Chart(_cd).mark_bar(cornerRadiusEnd=5, opacity=0.90)
                    .encode(
                        x=alt.X("Ventas:Q", title="Ventas"),
                        y=alt.Y("Plan:N", sort="-x", title=""),
                        color=alt.Color("Modalidad:N",
                            scale=alt.Scale(domain=["PORTABILIDAD","LINEA NUEVA"],
                                            range=["#0f4287","#7c3aed"]),
                            legend=alt.Legend(title="Modalidad")),
                        tooltip=["Plan","Modalidad","Ventas"]
                    )
                    .properties(height=max(300, len(_top10)*46),
                                title="Top 10 planes más vendidos")
                    .configure_title(fontSize=15, fontWeight="bold", color="#70008f")
                )
                st.altair_chart(_ch, use_container_width=True)
            except Exception:
                pass

            st.download_button(
                "⬇️ Descargar tabla de planes",
                data=_pivot.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name="planes_movil.csv",
                mime="text/csv",
                key="dl_planes_movil_tab7"
            )

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

        USUARIOS = {
            "Fiorella": "F10r3LLa123*",
            "LuisT":    "Corp.LT_2026!k",
            "PaoloA":   "Corp.PA_2026!k",
            "DavidG":   "Corp.DG_2026!k",
            "SusanG":   "Corp.SG_2026!k",
        }

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
                import time; time.sleep(1.0)
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

        st.markdown('<div class="ls-foot">🔐 Acceso restringido · Uso interno autorizado</div>',
                    unsafe_allow_html=True)

    st.stop()

login_inicio()

OPCIONES_FIJA = [
    "Inicio: Reporte Comparativo",
    "Detalle Fija General",
]

# La auditoría queda oculta para todos y solo aparece al administrador Fiorella.
if st.session_state.get("usuario_logueado", "") == "Fiorella":
    OPCIONES_FIJA.append("🔒 Auditoría Descargas")

OPCIONES_MOVIL = [
    "Inicio: Reporte Comparativo MOVIL",
    "Detalle Móvil General",
]

OPCIONES_FACTOR = [
    "📊 Resumen NPN",
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
/* ── Ocultar nav por defecto ── */
div[data-testid="stSidebarNav"] {{display:none}}

/* ── Título del menú ── */
section[data-testid="stSidebar"] h1 {{
    font-size:17px !important;
    font-weight:900 !important;
    letter-spacing:0.12em !important;
    text-transform:uppercase !important;
    color:#ffffff !important;
    background:linear-gradient(135deg,#0F4287,#1a6dbf) !important;
    padding:10px 14px !important;
    border-radius:8px !important;
    margin-bottom:12px !important;
    text-align:center !important;
}}

/* ── Separadores de sección (no clickeables) ── */
{seps_css} {{
    pointer-events:none !important;
    cursor:default !important;
    margin-top:16px !important;
    margin-bottom:3px !important;
    border-radius:6px !important;
    background:linear-gradient(90deg,#0F4287 0%,#1a6dbf 100%) !important;
    padding:5px 10px !important;
}}
{seps_input_css} {{ display:none !important; }}

{seps_text_fija} {{
    font-weight:900 !important; font-size:13px !important;
    color:#ffffff !important; letter-spacing:0.1em !important;
    text-transform:uppercase !important;
}}
{seps_text_movil} {{
    font-weight:900 !important; font-size:13px !important;
    color:#ffffff !important; letter-spacing:0.1em !important;
    text-transform:uppercase !important;
}}
{seps_text_factor} {{
    font-weight:900 !important; font-size:13px !important;
    color:#ffffff !important; letter-spacing:0.1em !important;
    text-transform:uppercase !important;
}}

/* ── Items del menú ── */
section[data-testid="stSidebar"] .stRadio > div > label {{
    border-radius:6px !important;
    padding:5px 10px !important;
    transition:background 0.2s !important;
    font-size:13.5px !important;
}}
section[data-testid="stSidebar"] .stRadio > div > label:hover {{
    background:#e8f0fb !important;
}}

/* ── Sidebar fondo y borde ── */
section[data-testid="stSidebar"] {{
    background:#f4f7fd !important;
    border-right:2px solid #dde4f0 !important;
}}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("MENÚ DE REPORTES")
seleccion = st.sidebar.radio("MENU DE REPORTES", todas_opciones, key="radio_unico", label_visibility="collapsed")

if seleccion in SEPARADORES:
    seleccion = st.session_state.get("ultima_seleccion", "Inicio: Reporte Comparativo")
else:
    st.session_state["ultima_seleccion"] = seleccion

opcion        = seleccion if seleccion in OPCIONES_FIJA   else "Inicio: Reporte Comparativo"
opcion_movil  = seleccion if seleccion in OPCIONES_MOVIL  else "Inicio: Reporte Comparativo MOVIL"
opcion_factor = seleccion if seleccion in OPCIONES_FACTOR else "📊 Resumen NPN"
seccion       = ("movil"  if seleccion in OPCIONES_MOVIL
            else "factor" if seleccion in OPCIONES_FACTOR
            else "fija")

with st.sidebar.expander("🔍 Ver columnas de CSVs"):
    for nombre in ["FIJA_DC.csv","FIJA_TELETALK.csv","CLARO_DC_FIJA.csv","CLARO_DC_FIJA_SEGUNDA_CAIDA.csv","CLARO_TELETALK_FIJA.csv","CLARO_DC_MOVIL.csv","CLARO_TELETALK_MOVIL.csv"]:
        df_test = cargar_csv(nombre)
        if not df_test.empty: st.write(f"**{nombre}:**"); st.write(list(df_test.columns))
        else: st.write(f"**{nombre}:** ❌ no cargado")

if seccion == "factor":

    if opcion_factor == "📊 Resumen NPN":
        set_bg(img_caratula)

        st.markdown("""
        <style>
        .npn-hero {
            background: linear-gradient(135deg,
                rgba(15,66,135,0.85) 0%,
                rgba(109,11,140,0.75) 55%,
                rgba(15,66,135,0.85) 100%);
            border-radius: 16px; padding: 36px 32px 28px 32px;
            text-align: center; margin-bottom: 22px;
            box-shadow: 0 6px 28px rgba(15,66,135,0.22);
            border: 1px solid rgba(255,255,255,0.12);
        }
        .npn-title { font-size:34px; font-weight:900; color:#ffffff;
            letter-spacing:0.07em; margin-bottom:4px; }
        .npn-divider { width:60px; height:3px;
            background:linear-gradient(90deg,#0057b8,#70008f);
            border-radius:2px; margin:10px auto 12px auto; }
        .npn-sub { font-size:13px; color:#d0dff5; letter-spacing:0.09em;
            text-transform:uppercase; }
        .npn-badge-dc { display:inline-block; background:rgba(15,66,135,0.7);
            border:1.5px solid #4a90d9; color:#fff; font-weight:700; font-size:12px;
            border-radius:20px; padding:4px 16px; margin:4px; letter-spacing:0.04em; }
        .npn-badge-tt { display:inline-block; background:rgba(109,11,140,0.7);
            border:1.5px solid #b05fd4; color:#fff; font-weight:700; font-size:12px;
            border-radius:20px; padding:4px 16px; margin:4px; letter-spacing:0.04em; }
        .npn-filtros-label { font-size:12px; font-weight:800; color:#1e3a5f;
            letter-spacing:0.07em; text-transform:uppercase;
            margin:16px 0 6px 0; }
        </style>
        <div class="npn-hero">
            <div class="npn-title">📊 FACTOR NPN</div>
            <div class="npn-divider"></div>
            <div class="npn-sub">D&amp;C Digital Group &nbsp;·&nbsp; Teletalk Contact Center</div>
            <div style="margin-top:14px;">
                <span class="npn-badge-dc">📡 D&amp;C — Línea Azul</span>
                <span class="npn-badge-tt">📱 Teletalk — Línea Morada</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Cargar DVZ.csv crudo ──────────────────────────────────────
        _df_npn = _leer_dvz_crudo()

        if _df_npn.empty:
            st.warning("No se encontró el archivo DVZ.csv. Verifica que esté en la carpeta de datos.")
        else:
            _df_npn = _df_npn.copy()
            _df_npn.columns = _df_npn.columns.str.strip()

            # Detectar columnas exactas
            _col_tipo  = next((c for c in _df_npn.columns if c.strip().lower() == "tipo producto"), None)
            _col_clip  = next((c for c in _df_npn.columns if c.strip().lower() == "datos adicionales - clip"), None)
            _col_fvta  = next((c for c in _df_npn.columns if c.strip() in
                ["FECHA DE VENTA","Fecha de Venta","Fecha Venta","FECHA VENTA"]), None)
            _col_finst = next((c for c in _df_npn.columns if c.strip() in
                ["Back Office - Fecha Instalacion","Back Office - Fecha Instalación",
                 "FECHA INSTALACION","Fecha Instalacion"]), None)
            _col_sup   = next((c for c in _df_npn.columns if c.strip() in
                ["Datos Adicionales - Supervisor","Datos adicionales - Supervisor",
                 "SUPERVISOR","Supervisor"]), None)

            # Parsear fechas con detección ISO
            if _col_fvta:
                _s = _df_npn[_col_fvta].dropna().astype(str)
                _iso_vta = _s.str.match(r"^\d{4}-\d{2}-\d{2}").any() if not _s.empty else False
                _df_npn["_FVTA_DT"] = pd.to_datetime(_df_npn[_col_fvta], errors="coerce", dayfirst=not _iso_vta)
            else:
                _df_npn["_FVTA_DT"] = pd.NaT

            if _col_finst:
                _s2 = _df_npn[_col_finst].dropna().astype(str)
                _iso_inst = _s2.str.match(r"^\d{4}-\d{2}-\d{2}").any() if not _s2.empty else False
                _df_npn["_FINST_DT"] = pd.to_datetime(_df_npn[_col_finst], errors="coerce", dayfirst=not _iso_inst)
            else:
                _df_npn["_FINST_DT"] = pd.NaT

            # Construir opciones de filtros
            _opts_serv  = ["Todos"] + sorted(_df_npn[_col_tipo].dropna().astype(str).str.strip().unique().tolist()) if _col_tipo else ["Todos"]
            _opts_canal = ["Todos"] + sorted(_df_npn[_col_clip].dropna().astype(str).str.strip().unique().tolist()) if _col_clip else ["Todos"]
            _opts_sup   = ["Todos"] + sorted(_df_npn[_col_sup].dropna().astype(str).str.strip().unique().tolist()) if _col_sup else ["Todos"]

            def _npn_meses(dt_col):
                _ms = set()
                for _d in _df_npn[dt_col].dropna():
                    _ms.add(f"{MESES_ES[_d.month].capitalize()} {_d.year}")
                return sorted(_ms, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0)))

            _opts_fvta  = _npn_meses("_FVTA_DT")
            _opts_finst = _npn_meses("_FINST_DT")

            # ── Filtros en 5 columnas ─────────────────────────────────
            st.markdown('<div class="npn-filtros-label">🔍 Filtros</div>', unsafe_allow_html=True)
            _fc1, _fc2, _fc3, _fc4, _fc5 = st.columns([1,1,1.4,1.4,1.4])
            with _fc1:
                _f_serv  = st.selectbox("Servicio",            _opts_serv,  key="npn_serv")
            with _fc2:
                _f_canal = st.selectbox("Canal",               _opts_canal, key="npn_canal")
            with _fc3:
                _f_fvta  = st.multiselect("Fecha de Venta",    _opts_fvta,  default=[], placeholder="Todos los meses", key="npn_fvta")
            with _fc4:
                _f_finst = st.multiselect("Fecha Instalación", _opts_finst, default=[], placeholder="Todos los meses", key="npn_finst")
            with _fc5:
                _f_sup   = st.multiselect("Supervisor", [o for o in _opts_sup if o != "Todos"], default=[], placeholder="Todos los supervisores", key="npn_sup")

            # ── Aplicar filtros sobre DVZ crudo (para el contador de registros) ──
            _dff = _df_npn.copy()
            if _f_serv != "Todos" and _col_tipo:
                _dff = _dff[_dff[_col_tipo].fillna("").astype(str).str.strip().str.upper() == _f_serv.upper()]
            if _f_canal != "Todos" and _col_clip:
                _dff = _dff[_dff[_col_clip].fillna("").astype(str).str.strip().str.upper() == _f_canal.upper()]
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

            st.markdown(f"**{len(_dff):,} registros** encontrados con los filtros seleccionados.")

            # ── Cargar datos procesados con Estado Pago real ──────────
            with st.spinner("Calculando KPIs..."):

                # FIJA: ya tiene SOT, Estado Pago, COMISION, SUPERVISOR, FECHA DE VENTA, FECHA INSTALACION
                _df_fija_npn = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                _df_fija_npn["_TIPO_NPN"] = "FIJA"

                # MOVIL: ya tiene Estado Pago, COMISION, SUPERVISOR, FECHA DE VENTA
                _df_movil_npn = construir_resumen_movil_general("Todos los meses")
                _df_movil_npn["_TIPO_NPN"] = "MOVIL"
                if "_FECHA_INSTALACION_DT" in _df_movil_npn.columns and "FECHA INSTALACION" not in _df_movil_npn.columns:
                    _df_movil_npn["FECHA INSTALACION"] = _df_movil_npn["_FECHA_INSTALACION_DT"].astype(str)

                # SOT solo existe en fija; móvil no lo tiene → rellenar vacío
                # calcular_pct_tv_fija usa SOT para buscar el producto con TV
                if "SOT" not in _df_movil_npn.columns:
                    _df_movil_npn["SOT"] = ""

                # Columnas comunes incluyendo SOT (necesario para calcular_pct_tv_fija)
                _cols_comun = ["Canal", "SUPERVISOR", "FECHA DE VENTA", "FECHA INSTALACION",
                               "SOT", "COMISION", "Estado Pago", "_TIPO_NPN"]
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

                # Parsear fecha instalación
                _df_npn_proc["_FINST_PROC"] = pd.to_datetime(
                    _df_npn_proc["FECHA INSTALACION"], errors="coerce", dayfirst=True)
                _df_npn_proc["_MES_INST"] = _df_npn_proc["_FINST_PROC"].apply(
                    lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else "")

                # ── Aplicar los mismos filtros sobre df procesado ────
                _dfp = _df_npn_proc.copy()
                if _f_serv != "Todos":
                    _dfp = _dfp[_dfp["_TIPO_NPN"].str.upper() == _f_serv.upper()]
                if _f_canal != "Todos":
                    _dfp = _dfp[_dfp["Canal"].fillna("").astype(str).str.strip().str.upper() == _f_canal.upper()]
                if _f_fvta:
                    _dfp = _dfp[_dfp["_MES_VENTA"].isin(_f_fvta)]
                if _f_finst:
                    _dfp = _dfp[_dfp["_MES_INST"].isin(_f_finst)]
                if _f_sup:
                    _dfp = _dfp[_dfp["SUPERVISOR"].fillna("").astype(str).str.strip().isin(_f_sup)]

                # ── Pagadas ───────────────────────────────────────────
                _mask_pag = _dfp["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                _ventas_netas_total = int(_mask_pag.sum())
                _dfp_pag = _dfp[_mask_pag].copy()

                # ── Comisión Total ────────────────────────────────────
                _comision_total_npn = float(
                    pd.to_numeric(_dfp_pag["COMISION"], errors="coerce").fillna(0).sum())

                # ── % TV: igual que Detalle Fija General ─────────────
                # calcular_pct_tv_fija necesita columnas "Estado Pago" y "SOT"
                # _dfp_pag ya tiene ambas (SOT vacío en móvil → no suma TV, correcto)
                _pct_tv_npn, _ventas_tv_npn, _ = calcular_pct_tv_fija(_dfp_pag)

                # ── KPI NETAS 3 MESES: lógica directa desde archivos CLARO ──────
                # FIJA:  SOTs únicas en CLARO_DC_FIJA con COMISION > 0
                #        + SOTs únicas en CLARO_DC_FIJA_SEGUNDA_CAIDA con COM ETAPA > 0
                # MÓVIL: SECs únicas en CLARO_TELETALK_MOVIL con COMISION TOTAL > 0
                #        + SECs únicas en CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA con COMISION > 0

                _netas_3m_fija  = 0
                _netas_3m_movil = 0

                # ── FIJA: solo 2da Etapa con COM ETAPA > 0 ───────────
                # La base principal (CLARO_DC_FIJA) ya está en Ventas Netas.
                # Aquí solo contamos las SOTs que recuperaron comisión en 2da etapa.
                try:
                    _df_cf2 = cargar_csv("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
                    if not _df_cf2.empty and "SOT" in _df_cf2.columns:
                        _col_com_cf2 = encontrar_columna(_df_cf2,
                            ["COM ETAPA","COM_ETAPA","Com Etapa","COMISION ETAPA","COMISIÓN ETAPA"])
                        if _col_com_cf2:
                            _cf2_mask = pd.to_numeric(_df_cf2[_col_com_cf2], errors="coerce").fillna(0) > 0
                            _sots_cf2 = set(_df_cf2.loc[_cf2_mask, "SOT"].dropna().astype(str).str.strip().unique())
                            _netas_3m_fija = len(_sots_cf2)
                except Exception:
                    pass

                # ── MÓVIL: solo 2da Caída con COMISION > 0 ───────────
                # La base principal (CLARO_TELETALK_MOVIL) ya está en Ventas Netas.
                # Aquí solo contamos las SECs que recuperaron comisión en 2da caída.
                try:
                    _df_cm2 = cargar_csv("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")
                    if not _df_cm2.empty:
                        _col_sec_cm2 = encontrar_columna(_df_cm2, ["SEC","Sec","sec"])
                        _col_com_cm2 = encontrar_columna(_df_cm2,
                            ["COMISION","COMISIÓN","Comision","Comisión","MONTO"])
                        if _col_sec_cm2 and _col_com_cm2:
                            _cm2_mask = pd.to_numeric(_df_cm2[_col_com_cm2], errors="coerce").fillna(0) > 0
                            # Contar todas las filas con COMISION>0 (una SEC repetida = números distintos)
                            _netas_3m_movil = int(_cm2_mask.sum())
                except Exception:
                    pass

                # Disponibilidad por combinación Servicio + Canal:
                # FIJA + D&C       → Netas 3M y 6M disponibles (CLARO_DC_FIJA_SEGUNDA_CAIDA)
                # FIJA + Teletalk  → no disponible (sin archivos)
                # MOVIL + D&C      → no disponible (sin archivos)
                # MOVIL + Teletalk → Netas 3M disponible (CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA)
                # Todos + Todos    → suma solo lo disponible

                _serv_up  = _f_serv.upper()   # "FIJA" / "MOVIL" / "TODOS"
                _canal_up = _f_canal.upper()   # "D&C" / "TELETALK" / "TODOS"

                _disponible_fija  = (_serv_up in ("FIJA",  "TODOS")) and (_canal_up in ("D&C",      "TODOS"))
                _disponible_movil = (_serv_up in ("MOVIL", "TODOS")) and (_canal_up in ("TELETALK",  "TODOS"))

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

                # Netas 6 Meses: por ahora solo disponible para FIJA + D&C (mismo archivo 2da Etapa)
                if _disponible_fija and not _disponible_movil:
                    _val_n6m = "—"
                    _sub_n6m = "Próximamente"
                elif not _disponible_fija and not _disponible_movil:
                    _val_n6m = "—"
                    _sub_n6m = "Sin archivos para esta combinación"
                else:
                    _val_n6m = "—"
                    _sub_n6m = "Próximamente"

            # ── KPIs en una fila de 5 ────────────────────────────────
            st.markdown("### 📊 KPIs Resumen NPN")
            _nk1, _nk2, _nk3, _nk4, _nk5 = st.columns(5)

            _kpi_card_html(_nk1, "Ventas Netas",   f"{_ventas_netas_total:,}",            "PAGADAS Fija + Móvil",         "#059669", "#059669")
            _kpi_card_html(_nk2, "Netas 3 Meses",  _val_n3m,                              _sub_n3m,                       "#0891b2", "#0891b2")
            _kpi_card_html(_nk3, "Netas 6 Meses",  _val_n6m,                              _sub_n6m,                       "#0f4287", "#0f4287")
            _kpi_card_html(_nk4, "Comisión Total", formatear_moneda(_comision_total_npn), "Suma comisión pagadas",        "#7c3aed", "#7c3aed")
            _kpi_card_html(_nk5, "% TV",           f"{_pct_tv_npn:.2f}%",                f"{_ventas_tv_npn:,} pagadas con TV", "#7c3aed", "#7c3aed")

elif seccion == "fija":

    if opcion == "🔒 Auditoría Descargas":
        mostrar_auditoria_descargas()

    elif opcion == "Inicio: Reporte Comparativo":
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

        with st.spinner("Cargando resumen comparativo FIJA..."):
            # Carga única igual que Detalle Fija General
            if "dfg_det_cache" not in st.session_state:
                _df_base = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                if "FECHA DE VENTA" in _df_base.columns:
                    _dt = pd.to_datetime(_df_base["FECHA DE VENTA"], dayfirst=True, errors="coerce")
                    _df_base["_MES_VENTA"] = _dt.apply(
                        lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else ""
                    )
                else:
                    _df_base["_MES_VENTA"] = ""
                st.session_state["dfg_det_cache"] = _df_base

            df_base = st.session_state["dfg_det_cache"]

            def _resumir_por_canal_fija(df_full, canal):
                df_c = df_full[df_full["Canal"] == canal].copy() if not df_full.empty else df_full
                if df_c.empty or "_MES_VENTA" not in df_c.columns:
                    return pd.DataFrame(columns=["MES","VENTAS BRUTAS","VENTAS NETAS","% CAÍDA","% TV","PROMEDIO PRIME"])
                df_c["_com_num"] = pd.to_numeric(df_c.get("COMISION", 0), errors="coerce").fillna(0)
                rows = []
                for mes, grp in df_c[df_c["_MES_VENTA"] != ""].groupby("_MES_VENTA"):
                    brutas = len(grp)
                    netas  = int((grp["Estado Pago"] == "PAGADA").sum())
                    caidas = brutas - netas
                    pct    = (caidas / brutas * 100) if brutas > 0 else 0.0
                    com    = float(grp["_com_num"].sum())
                    ticket = (com / netas) if netas > 0 else 0.0
                    pct_tv, _, _ = calcular_pct_tv_fija(grp)
                    m_num, y_num = parse_mes_anio(mes)
                    rows.append({
                        "MES": mes,
                        "VENTAS BRUTAS": brutas,
                        "VENTAS NETAS": netas,
                        "% CAÍDA": f"{pct:.2f}%",
                        "% TV": f"{pct_tv:.2f}%",
                        "PROMEDIO PRIME": formatear_moneda(ticket),
                        "_sort": (y_num or 0, m_num or 0)
                    })
                if not rows:
                    return pd.DataFrame(columns=["MES","VENTAS BRUTAS","VENTAS NETAS","% CAÍDA","% TV","PROMEDIO PRIME"])
                return pd.DataFrame(rows).sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

            col_dc, col_tt = st.columns(2)
            with col_dc:
                st.markdown('<div class="tbl-canal-title tbl-canal-dc">📡 D&amp;C DIGITAL GROUP</div>', unsafe_allow_html=True)
                tbl_dc = _resumir_por_canal_fija(df_base, "D&C")
                if tbl_dc.empty:
                    st.info("Sin datos disponibles.")
                else:
                    st.dataframe(tbl_dc, use_container_width=True, hide_index=True)
            with col_tt:
                st.markdown('<div class="tbl-canal-title tbl-canal-tt">📡 TELETALK CONTACT CENTER</div>', unsafe_allow_html=True)
                tbl_tt = _resumir_por_canal_fija(df_base, "Teletalk")
                if tbl_tt.empty:
                    st.info("Sin datos disponibles.")
                else:
                    st.dataframe(tbl_tt, use_container_width=True, hide_index=True)

    elif opcion == "Detalle Fija General":
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
                df_mes = construir_resumen_movil_general(mes)
                if df_mes.empty:
                    if brutas > 0:
                        rows.append({"MES": mes, "VENTAS BRUTAS": brutas, "VENTAS NETAS": 0,
                                     "% CAÍDA": "100.00%", "PROMEDIO PRIME": formatear_moneda(0),
                                     "_sort": (y_num, m_num)})
                    continue
                df_canal = df_mes[df_mes["Canal"] == canal_filtro].copy()
                base_valida = df_canal[df_canal["Venta Valida"]].copy() if "Venta Valida" in df_canal.columns else df_canal.copy()
                netas = int((base_valida["Estado Pago"] == "PAGADA").sum()) if "Estado Pago" in base_valida.columns else 0
                base_pagada = base_valida[base_valida["Estado Pago"] == "PAGADA"].copy() if netas > 0 else pd.DataFrame()
                com = _sumar_comision_real_unica(base_pagada) if not base_pagada.empty else 0.0

                caidas = brutas - netas
                pct    = (caidas / brutas * 100) if brutas > 0 else 0.0
                ticket = (com / netas) if netas > 0 else 0.0
                rows.append({
                    "MES": mes,
                    "VENTAS BRUTAS": brutas,
                    "VENTAS NETAS": netas,
                    "% CAÍDA": f"{pct:.2f}%",
                    "PROMEDIO PRIME": formatear_moneda(ticket),
                    "_sort": (y_num, m_num)
                })
            if not rows:
                return pd.DataFrame(columns=["MES","VENTAS BRUTAS","VENTAS NETAS","% CAÍDA","PROMEDIO PRIME"])
            return pd.DataFrame(rows).sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

        with st.spinner("Cargando resumen comparativo MÓVIL..."):
            col_dc, col_tt = st.columns(2)
            with col_dc:
                st.markdown('<div class="tbl-canal-title tbl-canal-dc">📱 D&amp;C DIGITAL GROUP</div>', unsafe_allow_html=True)
                tbl_dc = _resumir_por_canal_movil("D&C")
                if tbl_dc.empty:
                    st.info("Sin datos disponibles.")
                else:
                    st.dataframe(tbl_dc, use_container_width=True, hide_index=True)
            with col_tt:
                st.markdown('<div class="tbl-canal-title tbl-canal-tt">📱 TELETALK CONTACT CENTER</div>', unsafe_allow_html=True)
                tbl_tt = _resumir_por_canal_movil("Teletalk")
                if tbl_tt.empty:
                    st.info("Sin datos disponibles.")
                else:
                    st.dataframe(tbl_tt, use_container_width=True, hide_index=True)