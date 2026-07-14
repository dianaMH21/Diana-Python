import os
import re
import html as _html
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as _stc

from config import *
import data_loader as _data_loader
from data_loader import *
_leer_dvz_crudo = _data_loader._leer_dvz_crudo
_cargar_dvz_filtrado = _data_loader._cargar_dvz_filtrado
_agregar_cola_por_extension = _data_loader._agregar_cola_por_extension
from ui_components import *

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

def _inject_tabs_card_style():
    st.markdown("""
    <style>
    div[data-testid="stTabs"] > div[role="tablist"] {
        gap: 16px !important;
        border-bottom: 0 !important;
        flex-wrap: wrap !important;
        padding: 8px 0 14px 0 !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        min-height: 42px !important;
        height: 42px !important;
        padding: 0 18px 0 14px !important;
        border: 1px solid #cbd7e8 !important;
        border-radius: 7px !important;
        background: rgba(255,255,255,.86) !important;
        box-shadow: 0 10px 22px rgba(15,23,42,.05) !important;
        color: #374151 !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        transition: border-color .15s ease, box-shadow .15s ease, background .15s ease !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] > div {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        line-height: 1 !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] > div::before {
        content: "" !important;
        width: 14px !important;
        height: 14px !important;
        min-width: 14px !important;
        border-radius: 999px !important;
        border: 1.5px solid #cbd5e1 !important;
        background: #ffffff !important;
        box-shadow: inset 0 0 0 4px #ffffff !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        border-color: #bfd0e7 !important;
        background: #ffffff !important;
        color: #111827 !important;
        box-shadow: 0 12px 24px rgba(15,23,42,.08) !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] > div::before {
        border-color: #ff4b55 !important;
        background: #ff4b55 !important;
        box-shadow: inset 0 0 0 4px #ff4b55 !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] p {
        font-size: 14px !important;
        margin: 0 !important;
        white-space: nowrap !important;
        color: inherit !important;
    }
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

def _periodo_ultimo_mes_cerrado():
    hoy = pd.Timestamp.today().normalize()
    return hoy.to_period("M")

def _mes_label_permitido(label):
    m, y = parse_mes_anio(label)
    if not m or not y:
        return False
    return pd.Period(year=y, month=m, freq="M") <= _periodo_ultimo_mes_cerrado()

def _ordenar_meses_cerrados(meses):
    limpios = [m for m in meses if _mes_label_permitido(m)]
    return sorted(limpios, key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0)))

def _fecha_en_mes_cerrado(fecha):
    if pd.isna(fecha):
        return False
    return pd.Period(year=int(fecha.year), month=int(fecha.month), freq="M") <= _periodo_ultimo_mes_cerrado()

def porta_si(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False).isin(['SI','YES','Y'])

def _es_portabilidad_movil(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False) == "PORTABILIDAD"

def _es_alta_movil(serie):
    return serie.str.upper().str.strip().str.replace('Í','I',regex=False).isin(["ALTA NUEVA","ALTA"])

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_meses_fija(col):
    meses = set()
    for nombre in ["CLARO_DC_FIJA.csv","CLARO_TELETALK_FIJA.csv"]:
        df = preparar_fechas_fija(cargar_csv(nombre))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].capitalize()} {f.year}" for f in df[col].dropna() if _fecha_en_mes_cerrado(f))
    return ["Todos los meses"] + _ordenar_meses_cerrados(meses)

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_meses_fija_develz(col):
    meses = set()
    for nombre in ["FIJA_DC.csv", "FIJA_TELETALK.csv"]:
        df = preparar_fechas_fija(cargar_csv(nombre))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].capitalize()} {f.year}" for f in df[col].dropna() if _fecha_en_mes_cerrado(f))
    return ["Todos los meses"] + _ordenar_meses_cerrados(meses)

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_meses_movil(col, archivos):
    meses = set()
    for a in archivos:
        df = preparar_fechas_movil(cargar_csv(a))
        if col in df.columns:
            meses.update(f"{MESES_ES[f.month].lower()} {f.year}".capitalize()
                         for f in df[df[col].notna()][col] if _fecha_en_mes_cerrado(f))
    return ["Todos los meses"] + _ordenar_meses_cerrados(meses)

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_metricas_fija(tabla, f_inst, f_gene):
    try:
        df = preparar_fechas_fija(get_tabla(tabla))
        if df.empty: return 0, 0.0
        if f_inst != "Todos los meses": df = filtrar_por_mes_anio(df, "FECHA INSTALACION", f_inst)
        if f_gene != "Todos los meses": df = filtrar_por_mes_anio(df, "FECHA GENERACION", f_gene)
        return int(df["SOT"].nunique() if "SOT" in df.columns else 0), float(obtener_comision_fija(df).sum())
    except: return 0, 0.0

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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
def _parse_fecha_develz_robusta(serie):
    if serie is None:
        return pd.Series(pd.NaT)
    s_str = serie.astype(str).str.strip()

    es_iso = s_str.str.match(r"^\d{4}-\d{1,2}-\d{1,2}", na=False)
    fechas_iso = pd.to_datetime(
        s_str.where(es_iso), errors="coerce", dayfirst=False, format="mixed", utc=True
    ).dt.tz_convert(None)
    fechas_txt = pd.to_datetime(
        s_str.where(~es_iso), errors="coerce", dayfirst=True, format="mixed"
    )
    return fechas_iso.fillna(fechas_txt)

def _obtener_sot_develz(df):
    col = encontrar_columna(df, ["Back Office - Sot","Back Office - SOT","SOT","sot","Sot"])
    return df[col].fillna("").astype(str).str.strip() if col else pd.Series([""] * len(df), index=df.index)

def _obtener_fecha_inst_develz(df):
    col = encontrar_columna(df, ["Back Office - Fecha Instalacion","Back Office - Fecha Instalación",
                                  "FECHA INSTALACION","Fecha Instalacion","Fecha Instalación"])
    return _parse_fecha_develz_robusta(df[col]) if col else pd.Series(pd.NaT, index=df.index)

def _obtener_fecha_venta_develz(df):
    col = encontrar_columna(df, ["FECHA DE VENTA", "Fecha de Venta", "Fecha Venta", "FECHA VENTA",
                                  "Back Office - Fecha de Venta", "Back Office - Fecha Venta",
                                  "FECHA GENERACION", "Fecha Generacion", "Fecha Generación"])
    return _parse_fecha_develz_robusta(df[col]) if col else pd.Series(pd.NaT, index=df.index)

def _obtener_supervisor_develz(df):
    col = encontrar_columna(df, ["Datos Adicionales - Supervisor","Datos adicionales - Supervisor",
                                  "SUPERVISOR","Supervisor","supervisor","USUARIO","Usuario"])
    return (df[col].fillna("Sin Supervisor").astype(str).str.strip().replace("","Sin Supervisor")
            if col else pd.Series(["Sin Supervisor"] * len(df), index=df.index))

def _obtener_asesor_creador_develz(df):
    col = encontrar_columna(df, ["ASESOR","Asesor","asesor","USUARIO","Usuario","usuario",
                                  "VENDEDOR","Vendedor","EJECUTIVO","Ejecutivo",
                                  "CREADOR","Creador","creador","Usuario Creador","USUARIO CREADOR",
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

@st.cache_data(ttl=600, show_spinner=False)
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

@st.cache_data(ttl=600, show_spinner=False)
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
            df["COLA"] = _data_loader._agregar_cola_por_extension(df_m.reindex(df.index), col_ext)
        else:
            df["COLA"] = "EXTERNO"
        for col in cols_salida:
            if col not in df.columns: df[col] = ""
        return df[cols_salida].reset_index(drop=True)
    except Exception as e:
        st.error(f"Error construyendo detalle DEVELZ {canal}: {e}")
        return pd.DataFrame(columns=cols_salida)

@st.cache_data(ttl=3600, show_spinner=False)
def construir_detalle_fija_general(filtro_mes, filtro_fecha_venta="Todos los meses"):
    df_dc = construir_detalle_fija_develz("[DATA DEVELZ].dbo.FIJA_DC", "dbo.CLARO_DC_FIJA", "D&C", filtro_mes, filtro_fecha_venta)
    df_tt = construir_detalle_fija_develz("[DATA DEVELZ].dbo.FIJA_TELETALK", "dbo.CLARO_TELETALK_FIJA", "Teletalk", filtro_mes, filtro_fecha_venta)
    return pd.concat([df_dc, df_tt], ignore_index=True)

def kpi_detalle_fija(df):
    if df.empty: return 0, 0, 0, 0.0, 0.0
    estado = df.get("Estado Pago", pd.Series("", index=df.index)).fillna("").astype(str).str.upper().str.strip()
    estado = estado.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
    t = int(len(df))
    p = int((estado == "PAGADA").sum())
    c = max(t - p, 0)
    com = pd.to_numeric(df["COMISION"], errors="coerce").fillna(0).sum()
    return t, p, c, com, (p/t*100) if t>0 else 0

def _render_panel_canal_fija(df, height=230):
    base = pd.DataFrame(df).copy()
    if base.empty:
        java_table(pd.DataFrame(columns=["Canal", "Total Ventas", "Pagadas", "No Pagadas", "% Efectividad", "% Caida", "Comision"]),
                   height=180, title="Resumen por canal", subtitle="Sin datos para los filtros seleccionados", accent="#4c1d95")
        return

    estado = base.get("Estado Pago", pd.Series("", index=base.index)).fillna("").astype(str).str.upper().str.strip()
    estado = estado.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
    base["_ES_PAGADA_PANEL"] = estado.eq("PAGADA")
    base["_COM_PANEL"] = pd.to_numeric(base.get("COMISION", 0), errors="coerce").fillna(0)

    rows_data = []
    for canal in ["Teletalk", "D&C"]:
        grp = base[base.get("Canal", "").fillna("").astype(str).str.strip().eq(canal)].copy()
        if grp.empty:
            total = pagadas = no_pagadas = 0
            comision = 0.0
        else:
            total = int(len(grp))
            pagadas = int(grp["_ES_PAGADA_PANEL"].sum())
            no_pagadas = max(total - pagadas, 0)
            comision = float(grp["_COM_PANEL"].sum())
        rows_data.append((canal, total, pagadas, no_pagadas, comision))

    total_general = sum(r[1] for r in rows_data)
    pagadas_general = sum(r[2] for r in rows_data)
    no_pagadas_general = sum(r[3] for r in rows_data)
    comision_general = sum(r[4] for r in rows_data)
    rows_data.append(("TOTAL", total_general, pagadas_general, no_pagadas_general, comision_general))

    def _pill(value, bg, fg):
        return f'<span class="fjp-pill" style="background:{bg};color:{fg};">{value:,}</span>'

    body = []
    for canal, total, pagadas, no_pagadas, comision in rows_data:
        ef = (pagadas / total * 100) if total else 0
        ca = (no_pagadas / total * 100) if total else 0
        is_total = canal == "TOTAL"
        row_cls = " total" if is_total else ""
        canal_html = "TOTAL" if is_total else _html.escape(canal)
        bar_w = min(max(ef, 0), 100)
        bar_html = "" if is_total else f'<div class="fjp-bar"><span style="width:{bar_w:.1f}%"></span></div>'
        body.append(f"""
        <tr class="{row_cls}">
            <td class="canal">{canal_html}</td>
            <td>{_pill(total, "#eaf2ff", "#1d4ed8") if not is_total else f"{total:,}"}</td>
            <td>{_pill(pagadas, "#dcfce7", "#166534") if not is_total else f"{pagadas:,}"}{bar_html}</td>
            <td>{_pill(no_pagadas, "#fee2e2", "#991b1b") if not is_total else f"{no_pagadas:,}"}</td>
            <td>{ef:.1f}%</td>
            <td class="bad">{ca:.1f}%</td>
            <td class="money">{formatear_moneda(comision)}</td>
        </tr>
        """)

    _stc.html(f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box}} body{{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a;background:transparent}}
    .fjp-card{{border-radius:10px;overflow:hidden;border:1px solid #dbe3ef;background:rgba(255,255,255,.94);box-shadow:0 16px 36px rgba(15,23,42,.08)}}
    table{{width:100%;border-collapse:separate;border-spacing:0;font-size:12px}}
    th{{background:linear-gradient(90deg,#78009b,#16458f);color:#fff;text-transform:uppercase;letter-spacing:.08em;font-size:10px;font-weight:950;padding:14px 12px;text-align:right}}
    th:first-child,td:first-child{{text-align:left}}
    td{{padding:13px 12px;border-bottom:1px solid #e5eaf1;text-align:right;font-weight:850;font-variant-numeric:tabular-nums}}
    tr:hover td{{background:#f8fbff}}
    .canal{{font-weight:950;color:#6d0b8c}}
    .fjp-pill{{display:inline-block;border-radius:999px;padding:6px 13px;font-weight:950;min-width:64px;text-align:center}}
    .fjp-bar{{height:7px;background:#edf2f7;border-radius:999px;margin:8px 2px 0;overflow:hidden}}
    .fjp-bar span{{display:block;height:100%;border-radius:999px;background:#059669}}
    .bad{{color:#dc2626}}
    .money{{color:#6d28d9;font-weight:950}}
    tr.total td{{background:linear-gradient(90deg,#16458f,#78009b);color:#fff;border-bottom:0;font-weight:950}}
    tr.total .money,tr.total .bad{{color:#fff}}
    </style></head><body>
    <div class="fjp-card"><table>
        <thead><tr><th>Canal</th><th>Total Ventas</th><th>Pagadas</th><th>No Pagadas</th><th>% Efectividad</th><th>% Caida</th><th>Comision</th></tr></thead>
        <tbody>{''.join(body)}</tbody>
    </table></div>
    </body></html>
    """, height=height, scrolling=False)

def _inject_filters_panel_style():
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) {
        background: rgba(255,255,255,0.74);
        border: 1px solid rgba(15,66,135,0.12);
        border-radius: 14px;
        padding: 16px 18px 12px 18px;
        margin: 4px 0 14px 0;
        box-shadow: 0 14px 34px rgba(15,23,42,0.08);
        backdrop-filter: blur(8px);
    }
    .filter-panel-label {
        color: #0f4287;
        font-size: 10px;
        font-weight: 950;
        letter-spacing: .13em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) label {
        font-weight: 850 !important;
        color: #374151 !important;
        font-size: 12px !important;
        letter-spacing: .02em !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) [data-baseweb="select"] > div {
        min-height: 42px !important;
        border-radius: 10px !important;
        background: linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%) !important;
        border: 1px solid rgba(148,163,184,0.42) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.82), 0 4px 12px rgba(15,23,42,0.05) !important;
        transition: border-color .18s ease, box-shadow .18s ease;
    }
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) [data-baseweb="select"] > div:hover,
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) [data-baseweb="select"] > div:focus-within {
        border-color: #0f4287 !important;
        box-shadow: 0 0 0 3px rgba(15,66,135,0.10), 0 8px 18px rgba(15,23,42,0.08) !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) [data-baseweb="tag"] {
        background:#ff4b4b !important;
        color:#fff !important;
        border-radius:8px !important;
        font-weight:900 !important;
        box-shadow:0 4px 10px rgba(255,75,75,0.20);
    }
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) [data-baseweb="tag"] span {
        color:#fff !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.filter-panel-anchor) svg {
        color:#334155;
    }
    </style>
    """, unsafe_allow_html=True)

def _render_exec_header(titulo, subtitulo, modulo="Modulo Ejecutivo", badge_1="D&C Digital Group", badge_2="Teletalk Contact Center"):
    st.markdown(f"""
    <style>
    .exec-header-wrap {{
        display:flex; align-items:center; justify-content:space-between;
        background:linear-gradient(135deg,rgba(15,66,135,0.88) 0%,rgba(109,11,140,0.78) 100%);
        border-radius:14px; padding:20px 28px; margin:4px 0 22px 0;
        box-shadow:0 4px 20px rgba(15,66,135,0.20);
        border:1px solid rgba(255,255,255,0.10);
    }}
    .exec-header-left {{ text-align:left; }}
    .exec-header-right {{ text-align:right; }}
    .exec-kicker {{
        font-size:10px; font-weight:900; color:rgba(255,255,255,0.68);
        letter-spacing:0.12em; text-transform:uppercase; margin-bottom:4px;
    }}
    .exec-title {{
        font-size:26px; font-weight:950; color:#fff;
        letter-spacing:0.06em; line-height:1.1; text-transform:uppercase;
    }}
    .exec-sub {{
        font-size:11px; color:rgba(255,255,255,0.62);
        letter-spacing:0.1em; text-transform:uppercase; margin-top:7px;
    }}
    .exec-badge-dc, .exec-badge-tt {{
        display:inline-block; color:#fff; font-weight:800; font-size:11px;
        border-radius:16px; padding:5px 16px; margin:3px; letter-spacing:0.03em;
    }}
    .exec-badge-dc {{ background:rgba(15,66,135,0.75); border:1.5px solid #4a90d9; }}
    .exec-badge-tt {{ background:rgba(109,11,140,0.75); border:1.5px solid #b05fd4; }}
    @media(max-width:760px) {{
        .exec-header-wrap {{ flex-direction:column; align-items:flex-start; gap:12px; }}
        .exec-header-right {{ text-align:left; }}
    }}
    </style>
    <div class="exec-header-wrap">
        <div class="exec-header-left">
            <div class="exec-kicker">{_html.escape(str(modulo))}</div>
            <div class="exec-title">{_html.escape(str(titulo))}</div>
            <div class="exec-sub">{_html.escape(str(subtitulo))}</div>
        </div>
        <div class="exec-header-right">
            <span class="exec-badge-dc">{_html.escape(str(badge_1))}</span><br>
            <span class="exec-badge-tt">{_html.escape(str(badge_2))}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    java_table(tabla, height=min(650, 90 + 36 * len(tabla)), title="Ranking departamentos", subtitle="Ventas, pagadas, caidas y comision", accent="#0f4287", max_rows=300)

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
    base = df.copy()
    estado = base.get("Estado Pago", pd.Series("", index=base.index)).fillna("").astype(str).str.upper().str.strip()
    estado = estado.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
    base["_ES_PAGADA_RANK"] = estado.eq("PAGADA")
    base["COMISION"] = pd.to_numeric(base.get("COMISION", 0), errors="coerce").fillna(0)
    grp = base.groupby("SUPERVISOR").agg(
        Total=("SUPERVISOR","count"),
        Pagadas=("_ES_PAGADA_RANK", "sum"),
        Comision=("COMISION", "sum"),
    ).reset_index().sort_values(["Comision","Total"], ascending=[False,False]).reset_index(drop=True)
    grp["Pagadas"] = pd.to_numeric(grp["Pagadas"], errors="coerce").fillna(0).astype(int)
    grp["Caidas"] = (pd.to_numeric(grp["Total"], errors="coerce").fillna(0).astype(int) - grp["Pagadas"]).clip(lower=0)
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
    estado = base.get("Estado Pago", pd.Series("", index=base.index)).fillna("").astype(str).str.upper().str.strip()
    estado = estado.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
    base["_ES_PAGADA_RANK"] = estado.eq("PAGADA")
    base = base[base["SUPERVISOR"] == supervisor].copy()
    if base.empty: return pd.DataFrame(columns=cols)
    grp = base.groupby("ASESOR", dropna=False).agg(
        Total=("ASESOR","count"),
        Pagadas=("_ES_PAGADA_RANK", "sum"),
        Comision=("COMISION","sum"),
    ).reset_index().sort_values(["Comision","Pagadas","Total"], ascending=[False,False,False]).reset_index(drop=True)
    grp["Pagadas"] = pd.to_numeric(grp["Pagadas"], errors="coerce").fillna(0).astype(int)
    grp["Caidas"] = (pd.to_numeric(grp["Total"], errors="coerce").fillna(0).astype(int) - grp["Pagadas"]).clip(lower=0)
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
                detalle_asesor_show = detalle_asesor.copy()
                if "Comision" in detalle_asesor_show.columns:
                    detalle_asesor_show["Comision"] = pd.to_numeric(detalle_asesor_show["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
                java_table(detalle_asesor_show, height=min(420, 80 + 36 * len(detalle_asesor_show)), title=supervisor, subtitle="Detalle por asesor", accent="#6d0b8c", max_rows=200)

def ranking_asesores_fija_develz(df):
    cols = ["Rank","ASESOR","Total","Pagadas","Caidas","% Efectividad","Comision"]
    if df.empty or "ASESOR" not in df.columns: return pd.DataFrame(columns=cols)
    base = df.copy()
    base["ASESOR"] = base["ASESOR"].fillna("Sin Asesor").astype(str).str.strip().replace("","Sin Asesor")
    base["COMISION"] = pd.to_numeric(base.get("COMISION",0), errors="coerce").fillna(0)
    estado = base.get("Estado Pago", pd.Series("", index=base.index)).fillna("").astype(str).str.upper().str.strip()
    estado = estado.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
    base["_ES_PAGADA_RANK"] = estado.eq("PAGADA")
    grp = base.groupby("ASESOR", dropna=False).agg(
        Total=("ASESOR","count"),
        Pagadas=("_ES_PAGADA_RANK", "sum"),
        Comision=("COMISION","sum"),
    ).reset_index().sort_values(["Comision","Pagadas","Total"], ascending=[False,False,False]).reset_index(drop=True)
    grp["Pagadas"] = pd.to_numeric(grp["Pagadas"], errors="coerce").fillna(0).astype(int)
    grp["Caidas"] = (pd.to_numeric(grp["Total"], errors="coerce").fillna(0).astype(int) - grp["Pagadas"]).clip(lower=0)
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

def _kpi_css_once():
    st.markdown("""
    <style>
    .tl-kpi-card{
        --accent:#0f4287;
        position:relative;
        overflow:hidden;
        min-height:112px;
        height:112px;
        padding:14px 13px 12px;
        border-radius:14px;
        background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(248,250,252,.92));
        border:1px solid rgba(15,23,42,.10);
        border-top:4px solid var(--accent);
        box-shadow:0 12px 28px rgba(15,23,42,.08);
        text-align:left;
        margin-bottom:10px;
        transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease;
        isolation:isolate;
    }
    .tl-kpi-card:before{
        content:"";
        position:absolute;
        width:92px;height:92px;
        right:-44px;top:-44px;
        border-radius:999px;
        background:rgba(15,66,135,.08);
        z-index:-1;
    }
    .tl-kpi-card:hover{
        transform:translateY(-2px);
        box-shadow:0 18px 36px rgba(15,23,42,.13);
    }
    .tl-kpi-label{
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
    }
    .tl-kpi-dot{
        width:7px;height:7px;
        min-width:7px;
        border-radius:999px;
        background:var(--accent);
        margin-top:3px;
        box-shadow:0 0 0 4px rgba(15,66,135,.10);
    }
    .tl-kpi-value{
        display:block;
        color:var(--accent);
        font-size:clamp(21px,2.1vw,31px);
        line-height:1.02;
        font-weight:950;
        margin-top:7px;
        word-break:break-word;
        animation:tlKpiIn .34s cubic-bezier(.2,.8,.2,1) both;
    }
    .tl-kpi-value.tl-money{font-size:clamp(18px,1.65vw,26px);}
    .tl-kpi-sub{
        display:block;
        color:#64748b;
        font-size:10px;
        line-height:1.25;
        font-weight:700;
        margin-top:7px;
        white-space:normal;
    }
    @keyframes tlKpiIn{
        from{opacity:0;transform:translateY(6px) scale(.985);filter:blur(1px);}
        to{opacity:1;transform:translateY(0) scale(1);filter:blur(0);}
    }
    @media (max-width:1200px){
        .tl-kpi-card{height:104px;min-height:104px;padding:12px;}
        .tl-kpi-value{font-size:22px;}
        .tl-kpi-value.tl-money{font-size:19px;}
    }
    </style>
    """, unsafe_allow_html=True)

def _kpi_card_html(col, label, valor, sub, color_borde, color_val="inherit"):
    accent = color_val if color_val and color_val != "inherit" else color_borde
    value_class = "tl-kpi-value tl-money" if any(x in str(valor) for x in ["S/", "$"]) else "tl-kpi-value"
    html = f"""<div class=\"tl-kpi-card\" style=\"--accent:{accent};\">
        <div class=\"tl-kpi-label\"><span class=\"tl-kpi-dot\"></span><span>{label}</span></div>
        <span class=\"{value_class}\">{valor}</span>
        <span class=\"tl-kpi-sub\">{sub}</span>
    </div>"""
    with col:
        _kpi_css_once()
        st.markdown(html, unsafe_allow_html=True)

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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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
@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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
    java_table(df_display, height=min(680,90+36*len(df_display)), title="Tabla gerencial por plan", subtitle="Resumen por plan contratado", accent=color_borde, max_rows=300)
    st.download_button("⬇️ Descargar Resumen Planes Fija",
        data=df_show.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="resumen_planes_fija.csv",mime="text/csv",key="dl_planes_fija_gerencial")

def _parsear_semana_pago(serie):
    """
    Recibe una Serie con valores como 'S03.202511'.
    Devuelve un DataFrame con columnas: SEMANA_PAGO_RAW, SEMANA_NUM, ANIO_MES, SEMANA_LABEL.
    S03.202511 → Semana 3 · Nov 2025
    """
    s = serie.fillna("").astype(str).str.strip()
    # Número de semana: dígitos tras la 'S' antes del punto
    num = s.str.extract(r"^[Ss](\d+)", expand=False).fillna("")
    # Parte de fecha: dígitos tras el punto
    fecha_part = s.str.extract(r"\.(\d{6})", expand=False).fillna("")  # e.g. 202511
    anio   = fecha_part.str[:4]
    mes_n  = fecha_part.str[4:6]

    def _label(row):
        n, a, m = row["num"], row["anio"], row["mes"]
        if not n or not a or not m:
            return row["raw"] if row["raw"] else "Sin Semana"
        try:
            mes_es = MESES_ES.get(int(m), m)
            return f"Semana {int(n)} · {mes_es} {a}"
        except Exception:
            return row["raw"]

    tmp = pd.DataFrame({"raw": s, "num": num, "anio": anio, "mes": mes_n})
    labels = tmp.apply(_label, axis=1)
    num_int = pd.to_numeric(num, errors="coerce").fillna(0).astype(int)
    anio_int = pd.to_numeric(anio, errors="coerce").fillna(0).astype(int)
    mes_int  = pd.to_numeric(mes_n, errors="coerce").fillna(0).astype(int)
    sort_key = anio_int * 10000 + mes_int * 100 + num_int
    return pd.DataFrame({
        "SEMANA_PAGO_RAW": s,
        "SEMANA_NUM": num_int,
        "ANIO_MES": anio_int * 100 + mes_int,
        "SORT_KEY": sort_key,
        "SEMANA_LABEL": labels,
    })


@st.cache_data(ttl=600, show_spinner=False)
def _cargar_semana_pago_claro(canal_filter="Todos"):
    """
    Lee SEMANA PAGO de los archivos CLARO y devuelve un DataFrame
    con columnas: SOT_KEY, SEMANA_PAGO_RAW, SEMANA_NUM, SEMANA_LABEL,
    SORT_KEY, CANAL_CLARO, COMISION_CLARO, COMISIONES_CLARO.
    """
    partes = []
    archivos = {
        "CLARO_DC_FIJA.csv": "D&C",
        "CLARO_TELETALK_FIJA.csv": "Teletalk",
    }
    for archivo, canal_c in archivos.items():
        if canal_filter == "D&C" and canal_c != "D&C": continue
        if canal_filter == "Teletalk" and canal_c != "Teletalk": continue

        df_c = preparar_fechas_fija(cargar_csv(archivo))
        if df_c.empty: continue
        df_c = df_c.copy()

        # Columna SOT
        col_sot = next((c for c in df_c.columns if c.strip().upper() == "SOT"), None)
        if not col_sot: continue
        df_c["SOT_KEY"] = _sot_key_series(df_c[col_sot].fillna("").astype(str))
        df_c = df_c[df_c["SOT_KEY"] != ""].copy()

        # Columna SEMANA PAGO (variantes de nombre)
        col_sem = next((c for c in df_c.columns
                        if c.strip().upper() in ["SEMANA PAGO","SEMANA_PAGO","SEMANA DE PAGO"]), None)
        if not col_sem:
            continue  # si no existe la columna en este archivo, se omite

        df_c["_SEM_RAW"] = df_c[col_sem].fillna("").astype(str).str.strip()

        # Parsear semana
        sem_df = _parsear_semana_pago(df_c["_SEM_RAW"])
        df_c["SEMANA_PAGO_RAW"] = sem_df["SEMANA_PAGO_RAW"].values
        df_c["SEMANA_NUM"]      = sem_df["SEMANA_NUM"].values
        df_c["SEMANA_LABEL"]    = sem_df["SEMANA_LABEL"].values
        df_c["SORT_KEY"]        = sem_df["SORT_KEY"].values

        # Comisión y estado de pago desde CLARO
        df_c["COMISION_CLARO"] = obtener_comision_fija(df_c)
        col_com_estado = next((c for c in df_c.columns if c.strip().upper() == "COMISIONES"), None)
        df_c["COMISIONES_CLARO"] = (
            df_c[col_com_estado].fillna("").astype(str).str.upper().str.strip()
            .str.replace("Í","I",regex=False)
            if col_com_estado else "NO"
        )
        df_c["CANAL_CLARO"] = canal_c

        partes.append(df_c[["SOT_KEY","SEMANA_PAGO_RAW","SEMANA_NUM","SEMANA_LABEL",
                            "SORT_KEY","CANAL_CLARO","COMISION_CLARO","COMISIONES_CLARO"]])

    if not partes:
        return pd.DataFrame(columns=["SOT_KEY","SEMANA_PAGO_RAW","SEMANA_NUM","SEMANA_LABEL",
                                     "SORT_KEY","CANAL_CLARO","COMISION_CLARO","COMISIONES_CLARO"])

    df_all = pd.concat(partes, ignore_index=True)
    # Deduplicar: si la misma SOT aparece en varios archivos, tomar la que tenga COMISIONES_CLARO == SI
    df_all = df_all.sort_values(
        ["SOT_KEY", "COMISIONES_CLARO"],
        ascending=[True, False]
    ).drop_duplicates(subset=["SOT_KEY"], keep="first")
    return df_all.reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner=False)
def _fechas_inst_por_semana_pago():
    """
    Devuelve dict: SEMANA_PAGO_RAW → (fecha_min_str, fecha_max_str)
    Solo considera filas donde COMISIONES != NO en CLARO_DC_FIJA y CLARO_TELETALK_FIJA.
    """
    resultado = {}
    for _arch in ["CLARO_DC_FIJA.csv", "CLARO_TELETALK_FIJA.csv"]:
        _dfc = preparar_fechas_fija(cargar_csv(_arch))
        if _dfc.empty: continue
        col_sem_fi = next((c for c in _dfc.columns
                           if c.strip().upper() in ["SEMANA PAGO","SEMANA_PAGO","SEMANA DE PAGO"]), None)
        col_fi = "FECHA INSTALACION" if "FECHA INSTALACION" in _dfc.columns else None
        if not col_sem_fi or not col_fi: continue
        _dfc = _dfc.copy()

        # ── Excluir COMISIONES == NO (misma lógica que el resto de la sección) ──
        col_com_est = next((c for c in _dfc.columns if c.strip().upper() == "COMISIONES"), None)
        if col_com_est:
            _mask_si = (
                _dfc[col_com_est].fillna("NO").astype(str)
                .str.strip().str.upper()
                .str.replace("Í","I", regex=False) != "NO"
            )
            _dfc = _dfc[_mask_si].copy()

        _dfc["_SEM_R"] = _dfc[col_sem_fi].fillna("").astype(str).str.strip()
        _dfc["_FI_DT"] = pd.to_datetime(_dfc[col_fi], errors="coerce", dayfirst=True)
        for sem_raw, grp_fi in _dfc.groupby("_SEM_R"):
            if not sem_raw: continue
            fechas_v = grp_fi["_FI_DT"].dropna()
            if fechas_v.empty: continue
            f_min = fechas_v.min().strftime("%d/%m/%Y")
            f_max = fechas_v.max().strftime("%d/%m/%Y")
            if sem_raw not in resultado:
                resultado[sem_raw] = (f_min, f_max)
            else:
                prev_min = pd.to_datetime(resultado[sem_raw][0], dayfirst=True)
                prev_max = pd.to_datetime(resultado[sem_raw][1], dayfirst=True)
                new_min  = fechas_v.min()
                new_max  = fechas_v.max()
                resultado[sem_raw] = (
                    min(prev_min, new_min).strftime("%d/%m/%Y"),
                    max(prev_max, new_max).strftime("%d/%m/%Y"),
                )
    return resultado


def mostrar_detalle_fija_general():
    color_titulo = "#004a99"; color_borde = "#0f4287"
    set_bg(img_caratula)
    _render_exec_header(
        "DETALLE FIJA GENERAL",
        "D&C + TELETALK - BASE DEVELZ COMPLETA - PAGADA VS CAIDA",
        badge_1="D&C Digital Group",
        badge_2="Teletalk Contact Center",
    )

    _dfg_cache_version = "dfg_asesor_fix_v2"
    if st.session_state.get("_dfg_cache_version") != _dfg_cache_version:
        if "dfg_det_cache" in st.session_state:
            del st.session_state["dfg_det_cache"]
        st.session_state["_dfg_cache_version"] = _dfg_cache_version

    # ── Carga única en session_state (no recarga por cada widget) ──────────────
    if "dfg_det_cache" not in st.session_state:
        if True:
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
    if "Estado Pago" in df_det.columns:
        _estado_cache = df_det["Estado Pago"].fillna("").astype(str).str.upper().str.strip()
        _estado_cache = _estado_cache.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
        df_det = df_det.copy()
        df_det["Estado Pago"] = _estado_cache.apply(lambda x: "PAGADA" if x == "PAGADA" else "CAÍDA")
        st.session_state["dfg_det_cache"] = df_det
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

    _inject_filters_panel_style()
    with st.container():
        st.markdown('<div class="filter-panel-anchor"></div>', unsafe_allow_html=True)
        st.markdown('<div class="filter-panel-label">Filtros fija</div>', unsafe_allow_html=True)
        col_f1,col_f2,col_f3 = st.columns(3)
        with col_f1: filtro_mes         = st.multiselect("Fecha de Instalacion", opts_inst,  default=[], placeholder="Todos los meses", key="det_general_mes")
        with col_f2: filtro_fecha_venta = st.multiselect("Fecha de Venta",       opts_venta, default=[], placeholder="Todos los meses", key="det_general_fecha_venta")
        with col_f3: filtro_canal       = st.selectbox("Canal",          ["Todos","D&C","Teletalk"], key="det_general_canal")

        col_f4,col_f5,col_f6 = st.columns(3)
        with col_f4: filtro_estado      = st.selectbox("Estado de Pago", ["Todos","PAGADA","CAÍDA"], key="det_general_estado")
        with col_f5: filtro_supervisor   = st.multiselect("Supervisor", sorted(df_det["SUPERVISOR"].fillna("Sin Supervisor").unique().tolist()), default=[], placeholder="Todos los supervisores", key="det_general_supervisor")
        with col_f6: filtro_tipificacion = st.selectbox("Tipificacion", ["Todos"] + sorted(df_det["TIPIS"].fillna("Sin TIPIS").astype(str).unique().tolist()), key="det_general_tipificacion")

        col_f7,col_f8,col_f9 = st.columns(3)
        with col_f7:
            colas_disponibles = sorted(df_det["COLA"].fillna("EXTERNO").unique().tolist()) if "COLA" in df_det.columns else []
            filtro_cola = st.selectbox("Cola", ["Todos"] + colas_disponibles, key="det_general_cola")
        with col_f8:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Refrescar datos", key="dfg_refresh", help="Fuerza recarga desde los CSV"):
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
    if filtro_estado  != "Todos":
        _estado_fil = df_filtrado["Estado Pago"].fillna("").astype(str).str.upper().str.strip()
        _estado_fil = _estado_fil.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
        _filtro_estado_norm = str(filtro_estado).upper().strip().replace("Í", "I").replace("Á", "A")
        if _filtro_estado_norm == "PAGADA":
            df_filtrado = df_filtrado[_estado_fil == "PAGADA"]
        else:
            df_filtrado = df_filtrado[_estado_fil != "PAGADA"]
    if filtro_supervisor:          df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(filtro_supervisor)]
    if filtro_tipificacion != "Todos": df_filtrado = df_filtrado[df_filtrado["TIPIS"]  == filtro_tipificacion]
    if filtro_cola != "Todos" and "COLA" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["COLA"] == filtro_cola]
    df_filtrado = df_filtrado.copy()

    total, pagadas, caidas, comision, pct = kpi_detalle_fija(df_filtrado)

    # Cuando hay filtro de Fecha de Instalacion, Pagadas y Comision vienen de CLARO
    # filtrando por FECHA INSTALACION del mes seleccionado y COMISIONES == SI.
    if filtro_mes:
        _claro_total = 0
        _claro_pagadas = 0
        _claro_comision = 0.0
        for _archivo_claro in ["CLARO_DC_FIJA.csv", "CLARO_TELETALK_FIJA.csv"]:
            if filtro_canal == "D&C" and "TELETALK" in _archivo_claro:
                continue
            if filtro_canal == "Teletalk" and _archivo_claro == "CLARO_DC_FIJA.csv":
                continue
            _df_c = preparar_fechas_fija(cargar_csv(_archivo_claro))
            if _df_c.empty:
                continue
            if "FECHA INSTALACION" in _df_c.columns:
                _df_c["_MES_CLARO"] = _df_c["FECHA INSTALACION"].apply(
                    lambda d: f"{MESES_ES[d.month].capitalize()} {d.year}" if pd.notna(d) else ""
                )
                _df_c = _df_c[_df_c["_MES_CLARO"].isin(filtro_mes)].copy()
            _col_sot_claro = next((c for c in _df_c.columns if c.strip().upper() == "SOT"), None)
            if _col_sot_claro:
                _df_c = _df_c.drop_duplicates(subset=[_col_sot_claro]).copy()
            _claro_total += len(_df_c)
            _col_com = next((c for c in _df_c.columns if c.strip().upper() == "COMISIONES"), None)
            if _col_com:
                _mask_si = _df_c[_col_com].fillna("").astype(str).str.strip().str.upper() == "SI"
                _df_pagadas_claro = _df_c[_mask_si].copy()
            else:
                _df_pagadas_claro = _df_c.copy()
            _claro_pagadas += len(_df_pagadas_claro)
            _col_monto = next((c for c in _df_pagadas_claro.columns
                               if c.strip().upper() in ["COMISION", "COMISIÓN", "MONTO", "COM ETAPA"]), None)
            if _col_monto is not None:
                _claro_comision += pd.to_numeric(_df_pagadas_claro[_col_monto], errors="coerce").fillna(0).sum()

        if _claro_total > 0:
            total = _claro_total
            pagadas = _claro_pagadas
            caidas = max(total - pagadas, 0)
            pct = (pagadas / total * 100) if total > 0 else 0.0
        comision = _claro_comision

    pct_tv, ventas_tv, _total_pagadas_tv = calcular_pct_tv_fija(df_filtrado)
    ticket_promedio_fija = (float(comision) / pagadas) if pagadas > 0 else 0.0

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    _kpi_card_html(k1, "Total Ventas", f"{total:,}", "Ventas registradas", "#111827", "#111827")
    _kpi_card_html(k2, "Pagadas", f"{pagadas:,}", "Comisionadas", "#059669", "#059669")
    _kpi_card_html(k3, "Caídas", f"{caidas:,}", "Total - Pagadas", "#dc2626", "#dc2626")
    _kpi_card_html(k4, "Comisión Total", formatear_moneda(comision), "Desde CLARO (mes inst.)" if filtro_mes else "Pagada", color_borde, color_borde)
    _kpi_card_html(k5, "% TV", f"{pct_tv:.2f}%", f"{ventas_tv:,} pagadas con TV", "#7c3aed", "#7c3aed")
    _kpi_card_html(k6, "% Efectividad", f"{pct:.2f}%", "Pagadas / Total", color_borde, "#059669" if pct >= 75 else "#d97706")
    _kpi_card_html(k7, "Promedio Prime", formatear_moneda(ticket_promedio_fija), "Comisión Total / Pagadas", "#0891b2", "#0891b2")
    _render_panel_canal_fija(df_filtrado)
    st.write("---")

    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs(["📋 Detalle Ventas","📆 Ventas por Día","🏆 Ranking Supervisor","👥 Ranking Asesores","📍 Ranking Departamentos","📊 Estados Operativos","📦 Por Planes","📅 Semana de Pago"])

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
        _estado_show = df_show["Estado Pago"].fillna("").astype(str).str.upper().str.strip()
        _estado_show = _estado_show.str.replace("Í", "I", regex=False).str.replace("Á", "A", regex=False)
        df_show["_ORDEN_PAGO"] = (_estado_show != "PAGADA").astype(int)
        df_show["_ORDEN_COMISION"] = pd.to_numeric(df_show["COMISION"], errors="coerce").fillna(0)
        df_show["_ORDEN_FECHA"] = pd.to_datetime(df_show["FECHA DE VENTA"], errors="coerce", dayfirst=True)
        df_show = (
            df_show
            .sort_values(["_ORDEN_PAGO", "_ORDEN_COMISION", "_ORDEN_FECHA"], ascending=[True, False, False])
            .drop(columns=["_ORDEN_PAGO", "_ORDEN_COMISION", "_ORDEN_FECHA"])
            .reset_index(drop=True)
        )
        df_show["COMISION"] = pd.to_numeric(df_show["COMISION"], errors="coerce").fillna(0).map(formatear_moneda)
        java_table(df_show, height=450, title="Detalle ventas fija", subtitle="Base filtrada con estado final", accent="#0f4287", max_rows=250)
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
                    java_table(pd.concat([tabla_dia,total_row],ignore_index=True), height=420, title="Tabla mensual", subtitle="Total vs pagadas por mes", accent="#0f4287", max_rows=300)
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
                java_table(pd.concat([tabla_dia,total_row],ignore_index=True), height=420, title="Tabla diaria", subtitle="Total vs pagadas por dia", accent="#0f4287", max_rows=300)

    with tab3:
        st.markdown("#### 🏆 Ranking Supervisor")
        mostrar_ranking_supervisores_con_asesores(df_filtrado)

    with tab4:
        st.markdown("#### 👥 Ranking Asesores")
        ranking_asesores = ranking_asesores_fija_develz(df_filtrado)
        if ranking_asesores.empty:
            st.warning("No se encontraron datos para el ranking de asesores.")
        else:
            ranking_asesores_show = ranking_asesores.copy()
            if "Comision" in ranking_asesores_show.columns:
                ranking_asesores_show["Comision"] = pd.to_numeric(ranking_asesores_show["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
            java_table(ranking_asesores_show, height=460, title="Ranking asesores", subtitle="Productividad por asesor", accent="#6d0b8c", max_rows=300)

    with tab5:
        mostrar_ranking_departamentos_premium(df_filtrado)

    with tab6:
        st.markdown("#### 📊 Estados Operativos")
        estados_df = estados_operativos_df(df_filtrado)
        if estados_df.empty: st.warning("No se encontraron datos de TIPIS.")
        else:
            col_e1, col_e2 = st.columns([1, 1.5])
            with col_e1:
                java_table(estados_df, height=360, title="Estados operativos", subtitle="Resumen por grupo", accent="#0f4287", max_rows=200)
            with col_e2:
                if "TIPIS" in df_filtrado.columns:
                    for estado_grupo in ["Conforme","1era Caída","2da Caída","Ejecución","Otros","Sin TIPIS"]:
                        df_grupo = df_filtrado[df_filtrado["Estado Operativo"] == estado_grupo]
                        if df_grupo.empty: continue
                        tipis_count = df_grupo["TIPIS"].fillna("Sin TIPIS").replace("","Sin TIPIS").value_counts().reset_index()
                        tipis_count.columns = ["TIPIS","Cantidad"]
                        with st.expander(f"{estado_grupo}  ({len(df_grupo)} ventas)", expanded=False):
                            java_table(tipis_count, height=260, title=estado_grupo, subtitle="Tipificaciones del grupo", accent="#6d0b8c", max_rows=150)

    with tab7:
        mostrar_tab_planes_fija_gerencial(df_filtrado, color_borde="#0f4287")

    with tab8:
        # ─────────────────────────────────────────────────────────────
        # TAB 8 · SEMANA DE PAGO
        # Lee columna "SEMANA PAGO" de CLARO_DC_FIJA y CLARO_TELETALK_FIJA,
        # parsea el código (ej. S03.202511 → Semana 3 / Nov 2025),
        # cruza por SOT con la base DEVELZ (df_filtrado) y muestra
        # un dashboard gerencial completo por semana.
        # ─────────────────────────────────────────────────────────────

        st.markdown("""
        <style>
        .sem-kpi{background:rgba(255,255,255,.97);border-radius:18px;padding:18px 14px;text-align:center;
                 border:2px solid #0f4287;box-shadow:0 10px 28px rgba(0,0,0,.09);min-height:108px;}
        .sem-kpi-label{font-size:10px;font-weight:900;color:#64748b;letter-spacing:.09em;
                       text-transform:uppercase;margin-bottom:7px;display:block;}
        .sem-kpi-value{font-size:30px;font-weight:950;line-height:1.05;display:block;}
        .sem-kpi-sub{font-size:10px;font-weight:700;color:#94a3b8;margin-top:5px;display:block;}
        .sem-header{font-size:20px;font-weight:900;color:#0f4287;margin:18px 0 6px 0;}
        .sem-week-pill{display:inline-block;padding:6px 14px;border-radius:999px;
                       background:#eff6ff;border:1px solid #bfdbfe;
                       color:#1e40af;font-size:12px;font-weight:800;margin:3px;}
        .sem-row-card{background:white;border-radius:14px;padding:10px 16px;margin:5px 0;
                      border:1px solid #e5e7eb;box-shadow:0 2px 8px rgba(0,0,0,.05);}
        .sem-row-header{display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;gap:8px;}
        .sem-row-label{font-weight:900;font-size:14px;color:#0f4287;}
        .sem-row-stat{font-size:12px;color:#374151;font-weight:700;
                      background:#f1f5f9;border-radius:8px;padding:3px 10px;}
        .sem-date-badge{margin-top:8px;padding:7px 14px;border-radius:10px;
                        background:#eff6ff;border-left:4px solid #2563eb;font-size:13px;}
        .sem-total-card{background:linear-gradient(135deg,#0f4287,#2563eb);border-radius:14px;
                        padding:12px 18px;margin:8px 0;color:white;}
        .sem-total-label{font-weight:900;font-size:14px;}
        .sem-total-stat{font-size:12px;font-weight:700;background:rgba(255,255,255,.18);
                        border-radius:8px;padding:3px 10px;}
        </style>
        """, unsafe_allow_html=True)

        st.markdown("#### 📅 Dashboard Gerencial — Semana de Pago")
        st.caption("Semana de pago tomada de CLARO_DC_FIJA y CLARO_TELETALK_FIJA · cruzada con SOT de la base DEVELZ filtrada")

        # ── Helper: parsear código de semana (definido a nivel de módulo, ver arriba) ──

        # ── Cruzar semana con df_filtrado (DEVELZ ya filtrado) ─────────────
        _canal_sem = "Todos" if filtro_canal == "Todos" else filtro_canal
        df_semana_claro = _cargar_semana_pago_claro(_canal_sem)

        if df_semana_claro.empty:
            st.warning(
                "⚠️ No se encontró la columna **SEMANA PAGO** en CLARO_DC_FIJA.csv ni en CLARO_TELETALK_FIJA.csv. "
                "Verifica que los archivos tengan esa columna."
            )
        else:
            # Normalizar SOT en df_filtrado para el cruce
            # Solo tomar registros con Tipo Producto == FIJA (semana de pago aplica solo a FIJA)
            df_filtrado_sem = df_filtrado.copy()
            _col_tipo_sem = next((c for c in df_filtrado_sem.columns
                                  if c.strip().lower() in ["tipo producto","tipo_producto"]), None)
            if _col_tipo_sem:
                df_filtrado_sem = df_filtrado_sem[
                    df_filtrado_sem[_col_tipo_sem].fillna("").astype(str)
                    .str.strip().str.upper() == "FIJA"
                ]
            df_filtrado_sem["SOT_KEY"] = _sot_key_series(df_filtrado_sem["SOT"].fillna("").astype(str))

            # Merge: enriquecer DEVELZ filtrado con info de semana de CLARO
            df_cruzado = df_filtrado_sem.merge(
                df_semana_claro[["SOT_KEY","SEMANA_PAGO_RAW","SEMANA_NUM","SEMANA_LABEL","SORT_KEY","CANAL_CLARO","COMISION_CLARO","COMISIONES_CLARO"]],
                on="SOT_KEY",
                how="left"
            )
            df_cruzado["SEMANA_LABEL"] = df_cruzado["SEMANA_LABEL"].fillna("Sin Semana Asignada")
            df_cruzado["SORT_KEY"]     = df_cruzado["SORT_KEY"].fillna(999999).astype(int)
            df_cruzado["SEMANA_NUM"]   = df_cruzado["SEMANA_NUM"].fillna(0).astype(int)
            df_cruzado["COMISION_CLARO"]    = pd.to_numeric(df_cruzado.get("COMISION_CLARO",0), errors="coerce").fillna(0)
            df_cruzado["COMISIONES_CLARO"]  = df_cruzado.get("COMISIONES_CLARO", pd.Series(["NO"]*len(df_cruzado))).fillna("NO")

            # ── Filtro de semana (selector) ──────────────────────────────────
            semanas_disp = (
                df_cruzado[df_cruzado["SEMANA_LABEL"] != "Sin Semana Asignada"]
                [["SEMANA_LABEL","SORT_KEY"]]
                .drop_duplicates()
                .sort_values("SORT_KEY")["SEMANA_LABEL"]
                .tolist()
            )
            opciones_sem = ["Todas las semanas"] + semanas_disp
            c_sem1, c_sem2 = st.columns([2,2])
            with c_sem1:
                filtro_semana = st.selectbox("Filtrar por Semana de Pago", opciones_sem, key="det_gen_semana_pago")
            with c_sem2:
                opciones_canal_sem = ["Todos","D&C","Teletalk"]
                filtro_canal_sem = st.selectbox("Canal (semana)", opciones_canal_sem,
                                                index=opciones_canal_sem.index(filtro_canal) if filtro_canal in opciones_canal_sem else 0,
                                                key="det_gen_semana_canal")

            df_sem = df_cruzado.copy()
            if filtro_semana != "Todas las semanas":
                df_sem = df_sem[df_sem["SEMANA_LABEL"] == filtro_semana]
            if filtro_canal_sem != "Todos":
                df_sem = df_sem[df_sem["Canal"] == filtro_canal_sem]

            # ── Resumen por semana ───────────────────────────────────────────
            st.markdown('<div class="sem-header">📊 Resumen Gerencial por Semana</div>', unsafe_allow_html=True)

            if df_sem.empty:
                st.info("No hay datos para los filtros seleccionados.")
            else:
                # ── 1) Excluir "Sin Semana Asignada" de la tabla y gráfico ───
                # Mapa SOT_KEY → FECHA INSTALACION desde CLARO (función a nivel de módulo)
                _map_fechas_sem = _fechas_inst_por_semana_pago()

                df_sem_limpio = df_sem[df_sem["SEMANA_LABEL"] != "Sin Semana Asignada"].copy()

                # Solo filas con COMISION > 0
                _com_num = pd.to_numeric(df_sem_limpio["COMISION"], errors="coerce").fillna(0)
                df_sem_limpio = df_sem_limpio[_com_num > 0].copy()

                grp_sem = (
                    df_sem_limpio
                    .groupby(["SEMANA_LABEL","SEMANA_PAGO_RAW","SORT_KEY","Canal"], dropna=False)
                    .agg(
                        Total_Ventas=("Estado Pago","count"),
                        Pagadas=("Estado Pago", lambda x: (x=="PAGADA").sum()),
                        Caidas=("Estado Pago",  lambda x: (x!="PAGADA").sum()),
                        Comision=("COMISION",   lambda x: pd.to_numeric(x,errors="coerce").fillna(0).sum()),
                    )
                    .reset_index()
                    .sort_values(["SORT_KEY","Canal"])
                )
                grp_sem["% Efectividad"] = (grp_sem["Pagadas"]/grp_sem["Total_Ventas"]*100).round(2).fillna(0).astype(str) + "%"
                # Semana corta para el gráfico: extraer número desde SEMANA_LABEL ("Semana 3 · Nov 2025" → "Semana 3")
                def _extraer_semana_corta(label):
                    import re as _re
                    m = _re.search(r"[Ss]emana\s*(\d+)", str(label))
                    return f"Semana {m.group(1)}" if m else str(label)
                grp_sem["SEMANA_CORTA"] = grp_sem["SEMANA_LABEL"].apply(_extraer_semana_corta)

                # ── Tabla con botón + desplegable por semana ─────────────────
                # Ordenar filas normales y construir vista
                filas_normales = (
                    grp_sem[grp_sem["SEMANA_LABEL"] != "TOTAL"]
                    .sort_values("SORT_KEY")
                    .copy()
                )

                # Agrupar por semana (puede haber 2 filas si hay 2 canales)
                semanas_orden = (
                    filas_normales[["SEMANA_LABEL","SEMANA_PAGO_RAW","SORT_KEY"]]
                    .drop_duplicates(subset=["SEMANA_LABEL"])
                    .sort_values("SORT_KEY")
                )

                for _, _sr in semanas_orden.iterrows():
                    _lbl  = _sr["SEMANA_LABEL"]
                    _raw  = str(_sr["SEMANA_PAGO_RAW"]).strip()
                    _rng  = _map_fechas_sem.get(_raw, None)
                    _filas_sem = filas_normales[filas_normales["SEMANA_LABEL"] == _lbl]

                    _tv   = int(_filas_sem["Total_Ventas"].sum())
                    _pag  = int(_filas_sem["Pagadas"].sum())
                    _cai  = int(_filas_sem["Caidas"].sum())
                    _com  = float(_filas_sem["Comision"].sum())
                    _pct  = f"{(_pag/_tv*100):.1f}%" if _tv > 0 else "0%"

                    # Botón desplegable por semana usando st.expander con + en el título
                    _fecha_hint = f"  📆 {_rng[0]} → {_rng[1]}" if _rng else "  📆 Fechas no disponibles"
                    with st.expander(
                        f"➕  {_lbl}{_fecha_hint}   |   Ventas: {_tv}   Pagadas: {_pag}   Caídas: {_cai}   {formatear_moneda(_com)}   {_pct}",
                        expanded=False
                    ):
                        # Detalle por canal dentro del expander
                        for _, _fila in _filas_sem.iterrows():
                            _canal = str(_fila.get("Canal","")).strip() or "Sin Canal"
                            _tv_c  = int(_fila["Total_Ventas"])
                            _pag_c = int(_fila["Pagadas"])
                            _cai_c = int(_fila["Caidas"])
                            _com_c = float(_fila["Comision"])
                            _pct_c = f"{(_pag_c/_tv_c*100):.1f}%" if _tv_c > 0 else "0%"
                            _color_canal = "#0f4287" if "D&C" in _canal or "DC" in _canal.upper() else "#70008f"
                            st.markdown(
                                f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;'
                                f'padding:8px 14px;border-radius:10px;background:#f8fafc;'
                                f'border-left:4px solid {_color_canal};margin:4px 0;">'
                                f'<span style="font-weight:900;color:{_color_canal};font-size:13px;min-width:180px;">📣 {_canal}</span>'
                                f'<span style="background:#e0e7ff;color:#3730a3;border-radius:7px;padding:3px 10px;font-size:12px;font-weight:800;">Ventas: {_tv_c}</span>'
                                f'<span style="background:#dcfce7;color:#166534;border-radius:7px;padding:3px 10px;font-size:12px;font-weight:800;">✅ Pagadas: {_pag_c}</span>'
                                f'<span style="background:#fee2e2;color:#991b1b;border-radius:7px;padding:3px 10px;font-size:12px;font-weight:800;">❌ Caídas: {_cai_c}</span>'
                                f'<span style="background:#fef3c7;color:#92400e;border-radius:7px;padding:3px 10px;font-size:12px;font-weight:800;">💰 {formatear_moneda(_com_c)}</span>'
                                f'<span style="background:#f3e8ff;color:#6b21a8;border-radius:7px;padding:3px 10px;font-size:12px;font-weight:800;">📈 {_pct_c}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        # Rango de fechas
                        if _rng:
                            st.markdown(
                                f'<div style="margin-top:8px;padding:8px 14px;border-radius:10px;'
                                f'background:#eff6ff;border-left:4px solid #2563eb;">'
                                f'<span style="font-weight:900;color:#1e40af;font-size:13px;">📅 Rango de Fecha Instalación:&nbsp;&nbsp;</span>'
                                f'<span style="color:#1d4ed8;font-weight:700;">{_rng[0]}</span>'
                                f'<span style="color:#6b7280;"> → </span>'
                                f'<span style="color:#1d4ed8;font-weight:700;">{_rng[1]}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.caption("Sin fechas de instalación disponibles para esta semana.")

                        # ── Botón de descarga por semana ─────────────────
                        _df_desc_sem = df_sem[
                            (df_sem["SEMANA_LABEL"] == _lbl) &
                            (pd.to_numeric(df_sem["COMISION"], errors="coerce").fillna(0) > 0)
                        ].copy()
                        _cols_desc = [c for c in ["SOT","SUPERVISOR","Canal","FECHA DE VENTA",
                            "FECHA INSTALACION","COMISION","Estado Pago","SEMANA_LABEL",
                            "COMISION_CLARO","CANAL_CLARO"] if c in _df_desc_sem.columns]
                        _csv_sem = _df_desc_sem[_cols_desc].to_csv(index=False, encoding="utf-8-sig")
                        st.download_button(
                            label=f"⬇️ Descargar {_lbl}",
                            data=_csv_sem,
                            file_name=f"semana_pago_{_lbl.replace(" ","_").replace("·","-")}.csv",
                            mime="text/csv",
                            key=f"dl_sem_{_lbl}",
                            use_container_width=True
                        )

                # Fila TOTAL siempre al final (fuera de expanders)
                _tot_tv  = int(grp_sem["Total_Ventas"].sum())
                _tot_pag = int(grp_sem["Pagadas"].sum())
                _tot_cai = int(grp_sem["Caidas"].sum())
                _tot_com = float(grp_sem["Comision"].sum())
                _tot_pct = f"{(_tot_pag/_tot_tv*100):.1f}%" if _tot_tv > 0 else "0%"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;'
                    f'padding:12px 18px;border-radius:14px;'
                    f'background:linear-gradient(135deg,#0f4287,#2563eb);margin:10px 0;">'
                    f'<span style="font-weight:900;color:white;font-size:15px;min-width:80px;">🏁 TOTAL</span>'
                    f'<span style="background:rgba(255,255,255,.18);color:white;border-radius:7px;padding:4px 12px;font-size:13px;font-weight:800;">Ventas: {_tot_tv}</span>'
                    f'<span style="background:rgba(255,255,255,.18);color:#bbf7d0;border-radius:7px;padding:4px 12px;font-size:13px;font-weight:800;">✅ Pagadas: {_tot_pag}</span>'
                    f'<span style="background:rgba(255,255,255,.18);color:#fca5a5;border-radius:7px;padding:4px 12px;font-size:13px;font-weight:800;">❌ Caídas: {_tot_cai}</span>'
                    f'<span style="background:rgba(255,255,255,.18);color:#fde68a;border-radius:7px;padding:4px 12px;font-size:13px;font-weight:800;">💰 {formatear_moneda(_tot_com)}</span>'
                    f'<span style="background:rgba(255,255,255,.18);color:#e9d5ff;border-radius:7px;padding:4px 12px;font-size:13px;font-weight:800;">📈 {_tot_pct}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # ── 2) Gráfico con eje X abreviado "Semana N" ────────────────
                base_chart_sem = grp_sem[grp_sem["SEMANA_LABEL"] != "TOTAL"].sort_values("SORT_KEY").copy()
                if not base_chart_sem.empty:
                    try:
                        import altair as alt
                        chart_melt_sem = base_chart_sem.melt(
                            id_vars=["SEMANA_CORTA","Canal","SORT_KEY"],
                            value_vars=["Total_Ventas","Pagadas","Caidas"],
                            var_name="Indicador", value_name="Cantidad"
                        )
                        label_map = {"Total_Ventas":"Total Ventas","Pagadas":"Pagadas","Caidas":"Caídas"}
                        chart_melt_sem["Indicador"] = chart_melt_sem["Indicador"].map(label_map).fillna(chart_melt_sem["Indicador"])
                        # Orden del eje X: Semana 1, Semana 2, …
                        orden_cortas = (
                            base_chart_sem[["SEMANA_CORTA","SORT_KEY"]]
                            .drop_duplicates()
                            .sort_values("SORT_KEY")["SEMANA_CORTA"]
                            .tolist()
                        )
                        indicadores_orden = ["Total Ventas","Pagadas","Caídas"]

                        base_c = alt.Chart(chart_melt_sem).encode(
                            x=alt.X("SEMANA_CORTA:N", title="Semana de Pago", sort=orden_cortas,
                                    axis=alt.Axis(labelAngle=0, labelFontSize=12, titleFontSize=12)),
                            xOffset=alt.XOffset("Indicador:N", sort=indicadores_orden),
                            y=alt.Y("Cantidad:Q", title="Ventas",
                                    axis=alt.Axis(labelFontSize=11, titleFontSize=12, grid=True)),
                            color=alt.Color("Indicador:N",
                                sort=indicadores_orden,
                                scale=alt.Scale(
                                    domain=indicadores_orden,
                                    range=["#0f4287","#059669","#dc2626"]
                                ),
                                legend=alt.Legend(title="Indicador", orient="top-right",
                                                  titleFontSize=12, labelFontSize=12)),
                            tooltip=[
                                alt.Tooltip("SEMANA_CORTA:N", title="Semana"),
                                alt.Tooltip("Canal:N",  title="Canal"),
                                alt.Tooltip("Indicador:N", title="Indicador"),
                                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
                            ]
                        )

                        barras_c = base_c.mark_bar(
                            cornerRadiusTopLeft=5, cornerRadiusTopRight=5, opacity=.90
                        )
                        etiquetas_c = base_c.mark_text(
                            align="center", baseline="bottom",
                            dy=-4, fontSize=11, fontWeight="bold", color="#111827"
                        ).encode(
                            text=alt.Text("Cantidad:Q", format=".0f")
                        )

                        chart_sem = (
                            (barras_c + etiquetas_c)
                            .properties(height=420, title="Ventas por Semana de Pago · Total vs Pagadas vs Caídas",
                                        padding={"left":10,"right":20,"top":20,"bottom":10})
                            .configure_title(fontSize=15, fontWeight="bold", color="#0f4287")
                            .configure_axis(labelFontSize=11, titleFontSize=12,
                                            grid=True, gridColor="#e5e7eb", domain=False)
                            .configure_view(strokeWidth=0)
                        )
                        st.altair_chart(chart_sem, use_container_width=True)
                    except Exception as _e_sem_chart:
                        st.info(f"Gráfico no disponible: {_e_sem_chart}")

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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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
    # Usa el mismo componente KPI moderno para mantener consistencia y evitar HTML duplicado.
    _kpi_card_html(col, titulo, valor, subtitulo, color, color)

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

def _leer_csv_directo_local_movil(nombre):
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

def _cargar_movil_desde_dvz_local(nombre):
    if nombre not in ["MOVIL_DC.csv", "MOVIL_TELETALK.csv"]:
        return pd.DataFrame()
    df = _leer_csv_directo_local_movil("DVZ.csv")
    if df.empty:
        return pd.DataFrame()
    col_tipo = next((c for c in df.columns if c.strip().lower() == "tipo producto"), None)
    col_clip = next((c for c in df.columns if c.strip().lower() == "datos adicionales - clip"), None)
    if not col_tipo or not col_clip:
        return pd.DataFrame()
    clip = "D&C" if nombre == "MOVIL_DC.csv" else "TELETALK"
    mask_tipo = df[col_tipo].fillna("").astype(str).str.strip().str.upper() == "MOVIL"
    mask_clip = df[col_clip].fillna("").astype(str).str.strip().str.upper() == clip
    return df[mask_tipo & mask_clip].copy()

def _leer_csv_movil_con_fallback(nombres, usar_api=False):
    for nombre in nombres:
        ruta = os.path.join(DATA_DIR, nombre)
        if os.path.exists(ruta):
            if not usar_api:
                df_local_dvz = _cargar_movil_desde_dvz_local(nombre)
                if not df_local_dvz.empty:
                    return df_local_dvz, nombre
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
def construir_resumen_movil_general(filtro_mes="Todos los meses", usar_api=False):
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
        df, archivo_usado = _leer_csv_movil_con_fallback(posibles_archivos, usar_api=usar_api)
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
            df["COLA"] = _data_loader._agregar_cola_por_extension(df, col_ext_movil) if col_ext_movil else "EXTERNO"
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

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_meses_movil_general(usar_api=False):
    meses = set()
    for _, posibles_archivos in [
        ("D&C", ["MOVIL_DC.csv"]),
        ("Teletalk", ["MOVIL_TELETALK.csv"]),
    ]:
        df, _ = _leer_csv_movil_con_fallback(posibles_archivos, usar_api=usar_api)
        if df.empty: continue
        fecha_dt, _ = _obtener_fecha_venta_movil_general(df)
        for f in fecha_dt.dropna():
            if _fecha_en_mes_cerrado(f):
                meses.add(f"{MESES_ES[f.month].capitalize()} {f.year}")
    return ["Todos los meses"] + _ordenar_meses_cerrados(meses)

@st.cache_data(ttl=3600, show_spinner=False)
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

    base  = resumen_general[resumen_general["Canal"].astype(str).str.upper() != "TOTAL"].copy()
    total = resumen_general[resumen_general["Canal"].astype(str).str.upper() == "TOTAL"].copy()
    if total.empty:
        total_ventas = int(pd.to_numeric(base.get("Total Ventas", 0), errors="coerce").fillna(0).sum())
        pagadas      = int(pd.to_numeric(base.get("Pagadas",      0), errors="coerce").fillna(0).sum())
        no_pagadas   = int(pd.to_numeric(base.get("No Pagadas",   0), errors="coerce").fillna(0).sum())
        comision     = float(pd.to_numeric(base.get("Comision",   0), errors="coerce").fillna(0).sum())
    else:
        total_ventas = int(pd.to_numeric(total["Total Ventas"].iloc[0], errors="coerce"))
        pagadas      = int(pd.to_numeric(total["Pagadas"].iloc[0],      errors="coerce"))
        no_pagadas   = int(pd.to_numeric(total["No Pagadas"].iloc[0],   errors="coerce"))
        comision     = float(pd.to_numeric(total["Comision"].iloc[0],   errors="coerce"))

    pct_pago  = (pagadas    / total_ventas * 100) if total_ventas > 0 else 0
    pct_caida = (no_pagadas / total_ventas * 100) if total_ventas > 0 else 0

    # ── Header ──────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .rg-header {
        background:linear-gradient(135deg,rgba(109,11,140,0.88) 0%,rgba(15,66,135,0.78) 100%);
        border-radius:14px; padding:20px 28px; margin-bottom:16px;
        box-shadow:0 4px 20px rgba(109,11,140,0.18);
        border:1px solid rgba(255,255,255,0.10);
        display:flex; align-items:center; justify-content:space-between;
    }
    .rg-title  { font-size:24px; font-weight:900; color:#fff; letter-spacing:0.05em; line-height:1.1; }
    .rg-sub    { font-size:11px; color:rgba(255,255,255,0.60); letter-spacing:0.10em; text-transform:uppercase; margin-top:4px; }
    .rg-badge  { display:inline-block; border-radius:999px; padding:4px 14px; font-size:11px; font-weight:800; margin:2px; }
    /* Tabla custom */
    .rg-table  { width:100%; border-collapse:collapse; margin:14px 0; font-size:13px; }
    .rg-table thead tr { background:linear-gradient(90deg,#70008f,#0f4287); color:#fff; }
    .rg-table thead th { padding:11px 14px; text-align:center; font-weight:800; letter-spacing:.06em; font-size:11px; text-transform:uppercase; }
    .rg-table thead th:first-child { text-align:left; border-radius:10px 0 0 0; }
    .rg-table thead th:last-child  { border-radius:0 10px 0 0; }
    .rg-table tbody tr  { border-bottom:1px solid #f1f5f9; transition:background .15s; }
    .rg-table tbody tr:hover { background:#faf5ff; }
    .rg-table tbody td  { padding:10px 14px; text-align:center; color:#374151; }
    .rg-table tbody td:first-child { text-align:left; font-weight:800; color:#70008f; }
    .rg-table tfoot tr  { background:linear-gradient(90deg,#0f4287,#70008f); }
    .rg-table tfoot td  { padding:11px 14px; text-align:center; color:#fff; font-weight:900; font-size:13px; }
    .rg-table tfoot td:first-child { text-align:left; border-radius:0 0 0 10px; }
    .rg-table tfoot td:last-child  { border-radius:0 0 10px 0; }
    .rg-pill-green { background:#dcfce7; color:#166534; border-radius:999px; padding:3px 10px; font-weight:800; font-size:12px; display:inline-block; }
    .rg-pill-red   { background:#fee2e2; color:#991b1b; border-radius:999px; padding:3px 10px; font-weight:800; font-size:12px; display:inline-block; }
    .rg-pill-blue  { background:#eff6ff; color:#1e40af; border-radius:999px; padding:3px 10px; font-weight:800; font-size:12px; display:inline-block; }
    .rg-bar-wrap   { background:#f1f5f9; border-radius:999px; height:7px; margin-top:4px; overflow:hidden; min-width:80px; }
    .rg-bar-fill   { height:7px; border-radius:999px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="rg-header">
        <div>
            <div class="rg-sub">Módulo Ejecutivo · Línea Móvil</div>
            <div class="rg-title">📋 Resumen General por Canal</div>
            <div class="rg-sub" style="margin-top:5px;">Ventas · Pago real Claro · Caída · Comisión por canal</div>
        </div>
        <div style="text-align:right;">
            <span class="rg-badge" style="background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.35);color:#fff;">
                ✅ Efectividad global: {pct_pago:.1f}%
            </span><br>
            <span class="rg-badge" style="margin-top:6px;background:rgba(255,255,255,.10);border:1.5px solid rgba(255,255,255,.25);color:rgba(255,255,255,.80);">
                📊 {total_ventas:,} ventas totales
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabla HTML profesional ───────────────────────────────────────────
    max_pag = max((pd.to_numeric(base.get("Pagadas", 0), errors="coerce").fillna(0).max()), 1)

    def _fila_canal(row):
        canal    = str(row.get("Canal", ""))
        tv       = int(pd.to_numeric(row.get("Total Ventas", 0), errors="coerce") or 0)
        pag      = int(pd.to_numeric(row.get("Pagadas",      0), errors="coerce") or 0)
        nopag    = int(pd.to_numeric(row.get("No Pagadas",   0), errors="coerce") or 0)
        com_raw  = pd.to_numeric(row.get("Comision",         0), errors="coerce") or 0
        com_fmt  = formatear_moneda(float(com_raw))
        pct_e    = f"{(pag/tv*100):.1f}%" if tv > 0 else "—"
        pct_c    = f"{(nopag/tv*100):.1f}%" if tv > 0 else "—"
        bar_pct  = int(pag / max_pag * 100)
        bar_col  = "#059669" if bar_pct >= 60 else "#d97706"
        ic       = "📡" if "D&C" in canal or "DC" in canal.upper() else "📱"
        return f"""<tr>
            <td>{ic} {canal}</td>
            <td><span class="rg-pill-blue">{tv:,}</span></td>
            <td>
                <span class="rg-pill-green">{pag:,}</span>
                <div class="rg-bar-wrap"><div class="rg-bar-fill" style="width:{bar_pct}%;background:{bar_col};"></div></div>
            </td>
            <td><span class="rg-pill-red">{nopag:,}</span></td>
            <td><strong>{pct_e}</strong></td>
            <td><strong style="color:#dc2626;">{pct_c}</strong></td>
            <td><strong style="color:#7c3aed;">{com_fmt}</strong></td>
        </tr>"""

    filas_html = "".join(_fila_canal(row) for _, row in base.iterrows())

    # Fila total
    pct_e_tot = f"{pct_pago:.1f}%"
    pct_c_tot = f"{pct_caida:.1f}%"
    com_tot   = formatear_moneda(comision)
    tfoot_html = f"""<tr>
        <td>🏁 TOTAL</td>
        <td>{total_ventas:,}</td>
        <td>{pagadas:,}</td>
        <td>{no_pagadas:,}</td>
        <td>{pct_e_tot}</td>
        <td>{pct_c_tot}</td>
        <td>{com_tot}</td>
    </tr>"""

    st.markdown(f"""
    <table class="rg-table">
        <thead><tr>
            <th>Canal</th>
            <th>Total Ventas</th>
            <th>Pagadas</th>
            <th>No Pagadas</th>
            <th>% Efectividad</th>
            <th>% Caída</th>
            <th>Comisión</th>
        </tr></thead>
        <tbody>{filas_html}</tbody>
        <tfoot>{tfoot_html}</tfoot>
    </table>
    """, unsafe_allow_html=True)

    # ── Gráfico profesional con etiquetas ───────────────────────────────
    try:
        import altair as alt
        chart_base = base.copy()
        chart_base["Pagadas"]    = pd.to_numeric(chart_base.get("Pagadas",    0), errors="coerce").fillna(0).astype(int)
        chart_base["No Pagadas"] = pd.to_numeric(chart_base.get("No Pagadas", 0), errors="coerce").fillna(0).astype(int)
        chart_base["Total Ventas"] = pd.to_numeric(chart_base.get("Total Ventas", 0), errors="coerce").fillna(0).astype(int)

        chart_data = chart_base.melt(
            id_vars=["Canal"],
            value_vars=["Total Ventas", "Pagadas", "No Pagadas"],
            var_name="Estado", value_name="Ventas"
        )
        orden_estados = ["Total Ventas", "Pagadas", "No Pagadas"]
        base_c = alt.Chart(chart_data).encode(
            x=alt.X("Canal:N", title="Canal",
                    axis=alt.Axis(labelFontSize=13, titleFontSize=13, labelAngle=0)),
            xOffset=alt.XOffset("Estado:N", sort=orden_estados),
            y=alt.Y("Ventas:Q", title="Cantidad de Ventas",
                    axis=alt.Axis(labelFontSize=11, titleFontSize=12, grid=True, gridColor="#e5e7eb")),
            color=alt.Color("Estado:N",
                sort=orden_estados,
                scale=alt.Scale(
                    domain=["Total Ventas", "Pagadas", "No Pagadas"],
                    range=["#0f4287", "#059669", "#dc2626"]
                ),
                legend=alt.Legend(title="Indicador", orient="top-right",
                                  titleFontSize=12, labelFontSize=12)),
            tooltip=[
                alt.Tooltip("Canal:N",   title="Canal"),
                alt.Tooltip("Estado:N",  title="Indicador"),
                alt.Tooltip("Ventas:Q",  title="Cantidad", format=",.0f"),
            ]
        )
        barras = base_c.mark_bar(
            cornerRadiusTopLeft=6, cornerRadiusTopRight=6, opacity=0.92
        )
        etiquetas = base_c.mark_text(
            align="center", baseline="bottom",
            dy=-5, fontSize=12, fontWeight="bold", color="#111827"
        ).encode(text=alt.Text("Ventas:Q", format=".0f"))

        chart = (
            (barras + etiquetas)
            .properties(
                height=380,
                title=alt.TitleParams(
                    "Ventas por Canal · Total vs Pagadas vs Caídas",
                    fontSize=15, fontWeight="bold", color="#70008f", anchor="start"
                ),
                padding={"left":10, "right":20, "top":20, "bottom":10}
            )
            .configure_axis(domain=False, grid=True, gridColor="#f1f5f9")
            .configure_view(strokeWidth=0)
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

@st.cache_data(ttl=3600, show_spinner=False)
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
    _render_exec_header(
        "DETALLE MOVIL GENERAL",
        "REPORTE GERENCIAL POR FECHA DE VENTA Y ESTADO DE PAGO",
        badge_1="D&C Digital Group",
        badge_2="Teletalk Contact Center",
    )

    # Para Detalle Móvil General el filtro principal se alimenta SOLO de MOVIL_DC.csv y MOVIL_TELETALK.csv.
    # No se mezclan meses de caídas/CLARO ni de fija.
    meses_general = obtener_meses_movil_general()
    meses = ["Todos los meses"] + sorted(
        set(meses_general) - {"Todos los meses"},
        key=lambda s: (int(s.split()[1]), MESES_MAP.get(s.split()[0].lower(), 0))
    )

    _inject_filters_panel_style()
    with st.container():
        st.markdown('<div class="filter-panel-anchor"></div>', unsafe_allow_html=True)
        st.markdown('<div class="filter-panel-label">Filtros movil</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)

        with c1:
            filtro_mes_list = st.multiselect("Fecha de Venta", meses[1:], default=[], key="movil_fecha_venta", placeholder="Todos los meses")
            filtro_mes = filtro_mes_list if filtro_mes_list else ["Todos los meses"]

        with c2:
            sel_canal = st.multiselect("Canal", ["D&C", "Teletalk"], default=[], key="movil_canal", placeholder="Todos los canales")
        filtro_canal = sel_canal[0] if len(sel_canal) == 1 else "Todos"

        if True:
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

        c4, c5, c6 = st.columns(3)
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
        c7, c8, c9 = st.columns(3)
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

    # ── KPI Total Ventas ────────────────────────────────────────────────
    # Debe respetar TODOS los filtros visibles: fecha venta, canal, fecha instalación,
    # estado, supervisor, tipificación y cola. Por eso se calcula desde df_filtrado,
    # no desde los CSV crudos.
    base_kpi_total = base_valida.copy() if not base_valida.empty else pd.DataFrame()
    total_ventas = int(len(base_kpi_total))
    _totales_kpi_canal = {}
    if not base_kpi_total.empty and "Canal" in base_kpi_total.columns:
        _totales_kpi_canal = base_kpi_total.groupby("Canal").size().astype(int).to_dict()

    # Tabla "Resumen General por Canal" alineada con los KPIs y con todos los filtros.
    resumen_general = resumen_general_movil_df(df_filtrado, totales_kpi=_totales_kpi_canal)

    pagadas_total = int((base_valida["Estado Pago"] == "PAGADA").sum()) if not base_valida.empty and "Estado Pago" in base_valida.columns else 0
    no_pagadas_total = max(total_ventas - pagadas_total, 0)
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



def render_dashboard():
    _inject_tabs_card_style()
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
    div[data-testid="stSidebarNav"] {{display:none}}

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
    if st.session_state.get("radio_unico") in SEPARADORES:
        st.session_state["radio_unico"] = st.session_state.get("ultima_seleccion", "Inicio: Reporte Comparativo")
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

            # ── Cargar DVZ.csv crudo ──────────────────────────────────────
            def _leer_csv_npn_local(nombre):
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

            # NPN trabaja con CSV locales. El API no entra en esta logica.
            _df_npn = _leer_csv_npn_local("DVZ.csv")

            # Invalidate caches if DVZ file changed since last load
            try:
                _ruta_dvz = os.path.join(DATA_DIR, "DVZ.csv")
                if os.path.exists(_ruta_dvz):
                    _mtime = os.path.getmtime(_ruta_dvz)
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
                        _df_bf = _leer_csv_npn_local(_archivo_csv)
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
                        _df_bm = _leer_csv_npn_local(_archivo_csv)
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
                    _df_cf2_csv = _leer_csv_npn_local("CLARO_DC_FIJA_SEGUNDA_CAIDA.csv")
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
                    _df_cm2_csv = _leer_csv_npn_local("CLARO_TELETALK_MOVIL_SEGUNDA_CAIDA.csv")
                    _col_sec_cm2 = _npn_col_local(_df_cm2_csv, ["SEC", "Sec", "sec"])
                    _col_com_cm2 = _npn_col_local(_df_cm2_csv, ["COMISION", "COMISIÓN", "COMISIÃ“N", "Comision", "Comisión", "ComisiÃ³n", "MONTO"])
                    if not _df_cm2_csv.empty and _col_sec_cm2 and _col_com_cm2:
                        _df_cm2_csv = _df_cm2_csv.copy()
                        _df_cm2_csv["_SEC_NPN"] = _npn_norm_id_local(_df_cm2_csv[_col_sec_cm2])
                        _df_cm2_csv["_COM_NPN"] = pd.to_numeric(_df_cm2_csv[_col_com_cm2], errors="coerce").fillna(0)
                        _df_cm2_csv = _df_cm2_csv[(_df_cm2_csv["_SEC_NPN"].isin(_secs_base_csv)) & (_df_cm2_csv["_COM_NPN"] > 0)].copy()
                        _netas_3m_movil = int((_df_cm2_csv["_SEC_NPN"] != "").sum())
                        _comision_3m += float(_df_cm2_csv["_COM_NPN"].sum())

                    _df_cm3_csv = _leer_csv_npn_local("CLARO_TELETALK_MOVIL_TERCERA_CAIDA.csv")
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
            try:
                set_bg(img_caratula)

                st.markdown("""
                <style>
                .copex-header-wrap {
                    position:relative; z-index:1;
                    background:linear-gradient(135deg,rgba(15,66,135,0.88) 0%,rgba(109,11,140,0.78) 100%);
                    border-radius:14px; padding:20px 28px; margin-bottom:18px;
                    box-shadow:0 4px 20px rgba(15,66,135,0.20);
                    border:1px solid rgba(255,255,255,0.10);
                }
                .copex-title { font-size:26px; font-weight:900; color:#fff; letter-spacing:0.06em; line-height:1.1; }
                .copex-sub   { font-size:11px; color:rgba(255,255,255,0.60); letter-spacing:0.1em; text-transform:uppercase; margin-top:4px; }
                .copex-kpi-row { position:relative; z-index:1; display:flex; gap:12px; margin:14px 0 6px 0; flex-wrap:wrap; }
                .copex-kpi-card {
                    position:relative; z-index:1;
                    flex:1; min-width:160px; background:#fff; border-radius:12px;
                    padding:16px 18px; text-align:center;
                    box-shadow:0 3px 14px rgba(0,0,0,0.08);
                    border-top:4px solid #0f4287;
                }
                .copex-kpi-label { font-size:9px; font-weight:800; color:#6b7280; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:6px; }
                .copex-kpi-val   { font-size:28px; font-weight:900; color:#0f4287; line-height:1; }
                .copex-kpi-sub   { font-size:9px; color:#9ca3af; margin-top:5px; font-style:italic; }
                </style>
                <div class="copex-header-wrap">
                    <div class="copex-title">💼 COMISIÓN OPERATIVA</div>
                    <div class="copex-sub">Cruce Base Pagadas (Fija + Móvil) vs. COMI_OPERATIVA.csv</div>
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("Cargando comparativo de comisión operativa..."):

                    # ── Base: Ventas Pagadas Fija + Móvil (cachés ya existentes) ──
                    if "npn_fija_cache" not in st.session_state:
                        _tmp = construir_detalle_fija_general("Todos los meses", "Todos los meses")
                        _tmp["_TIPO_NPN"] = "FIJA"
                        st.session_state["npn_fija_cache"] = _tmp
                    if "npn_movil_cache" not in st.session_state:
                        _tmp2 = construir_resumen_movil_general("Todos los meses")
                        _tmp2["_TIPO_NPN"] = "MOVIL"
                        st.session_state["npn_movil_cache"] = _tmp2

                    _df_fija_co  = st.session_state["npn_fija_cache"]
                    _df_movil_co = st.session_state["npn_movil_cache"]

                    if "Estado Pago" in _df_fija_co.columns:
                        _pag_fija_mask = _df_fija_co["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                    else:
                        _pag_fija_mask = pd.Series([False] * len(_df_fija_co), index=_df_fija_co.index)
                    _base_pagadas_fija = int(_pag_fija_mask.sum())

                    if "Estado Pago" in _df_movil_co.columns:
                        _pag_movil_mask = _df_movil_co["Estado Pago"].fillna("").astype(str).str.strip().str.upper() == "PAGADA"
                    else:
                        _pag_movil_mask = pd.Series([False] * len(_df_movil_co), index=_df_movil_co.index)
                    _base_pagadas_movil = int(_pag_movil_mask.sum())

                    _base_pagadas_total = _base_pagadas_fija + _base_pagadas_movil

                    # ── COMI_OPERATIVA.csv: contar TODAS las filas (con repetidos) ──
                    # SOT > 0 (Fija) + SEC > 0 (Móvil), filtrando COMSION_OPERATIVA > 0
                    _df_co = cargar_csv("COMI_OPERATIVA.csv")

                    _co_sot_count = 0
                    _co_sec_count = 0
                    _co_comision_total = 0.0
                    _col_com_op = None
                    _mask_com_op = pd.Series(dtype=bool)

                    if not _df_co.empty:
                        _df_co.columns = _df_co.columns.str.strip()
                        _col_com_op = next((c for c in _df_co.columns if c.strip().upper() == "COMSION_OPERATIVA"), None)
                        _col_sot_co = next((c for c in _df_co.columns if c.strip().upper() == "SOT"), None)
                        _col_sec_co = next((c for c in _df_co.columns if c.strip().upper() == "SEC"), None)

                        if _col_com_op:
                            _com_op_num = pd.to_numeric(_df_co[_col_com_op], errors="coerce").fillna(0)
                            _mask_com_op = _com_op_num > 0

                            if _col_sot_co:
                                _mask_sot = _mask_com_op & _df_co[_col_sot_co].notna() & (_df_co[_col_sot_co].astype(str).str.strip() != "")
                                _co_sot_count = int(_mask_sot.sum())

                            if _col_sec_co:
                                _mask_sec = _mask_com_op & _df_co[_col_sec_co].notna() & (_df_co[_col_sec_co].astype(str).str.strip() != "")
                                _co_sec_count = int(_mask_sec.sum())

                            _co_comision_total = float(_com_op_num[_mask_com_op].sum())
                        else:
                            _mask_com_op = pd.Series([False] * len(_df_co), index=_df_co.index)

                    # Solo SEC count (ignora SOT para evitar doble conteo cuando una venta tiene ambos)
                    _co_total = _co_sec_count
                    _diferencia = _co_total - _base_pagadas_total

                if _df_co.empty:
                    st.warning("No se encontró el archivo COMI_OPERATIVA.csv. Verifica que esté en la carpeta de datos.")
                else:
                    st.markdown(f"""
                    <div class="copex-kpi-row">
                        <div class="copex-kpi-card" style="border-top-color:#059669;">
                            <div class="copex-kpi-label">Pagadas Base (Fija+Móvil)</div>
                            <div class="copex-kpi-val" style="color:#059669;">{_base_pagadas_total:,}</div>
                            <div class="copex-kpi-sub">Fija: {_base_pagadas_fija:,} · Móvil: {_base_pagadas_movil:,}</div>
                        </div>
                        <div class="copex-kpi-card" style="border-top-color:#0891b2;">
                            <div class="copex-kpi-label">Comisión Operativa (Total)</div>
                            <div class="copex-kpi-val" style="color:#0891b2;">{_co_total:,}</div>
                            <div class="copex-kpi-sub">SEC únicas (móvil) · SOT ref: {_co_sot_count:,}</div>
                        </div>
                        <div class="copex-kpi-card" style="border-top-color:{'#dc2626' if _diferencia > 0 else '#7c3aed'};">
                            <div class="copex-kpi-label">Diferencia</div>
                            <div class="copex-kpi-val" style="color:{'#dc2626' if _diferencia > 0 else '#7c3aed'};">{_diferencia:+,}</div>
                            <div class="copex-kpi-sub">Comi.Operativa − Base Pagadas</div>
                        </div>
                        <div class="copex-kpi-card" style="border-top-color:#7c3aed;">
                            <div class="copex-kpi-label">Monto Comisión Operativa</div>
                            <div class="copex-kpi-val" style="color:#7c3aed;font-size:22px;">{formatear_moneda(_co_comision_total)}</div>
                            <div class="copex-kpi-sub">Suma COMSION_OPERATIVA &gt; 0</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.caption(
                        "📌 **Lógica:** Pagadas Base = ventas con Estado Pago = PAGADA en Detalle Fija/Móvil General. "
                        "Comisión Operativa = se cuentan **todas** las filas (con repetidos) de COMI_OPERATIVA.csv donde "
                        "SOT (Fija) o SEC (Móvil) tienen valor, filtrando solo COMSION_OPERATIVA > 0."
                    )

                    # ── Gráfico línea de tiempo ──────────
                    import streamlit.components.v1 as _stc_co_chart
                    _col_fecha_co = next((c for c in _df_co.columns if c.strip().upper() in [
                        "FECHA_ACTIVACION","FECHA ACTIVACION","FECHA_INSTALACION","FECHA INSTALACION",
                        "FECHA_OPERACION","FECHA OPERACION","FECHA","FECHA_PAGO","FECHA PAGO"]), None)
                    if _col_fecha_co and _col_com_op and not _df_co.empty:
                        _df_chart = _df_co[_mask_com_op].copy()
                        _df_chart["_FECHA_DT"] = pd.to_datetime(_df_chart[_col_fecha_co], errors="coerce", dayfirst=True)
                        _df_chart = _df_chart.dropna(subset=["_FECHA_DT"])
                        _df_chart["_COM_NUM"] = pd.to_numeric(_df_chart[_col_com_op], errors="coerce").fillna(0)
                        _df_chart["_MES"] = _df_chart["_FECHA_DT"].dt.to_period("M").astype(str)
                        _grp_chart = (_df_chart.groupby("_MES").agg(Registros=("_MES","count"), Comision=("_COM_NUM","sum")).reset_index().sort_values("_MES"))
                        if not _grp_chart.empty:
                            _meses_js = str(_grp_chart["_MES"].tolist())
                            _regs_js  = str(_grp_chart["Registros"].tolist())
                            _comis_js = str(_grp_chart["Comision"].round(2).tolist())
                            _max_reg  = int(_grp_chart["Registros"].max()) or 1
                            _max_com  = float(_grp_chart["Comision"].max()) or 1
                            _chart_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    *{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:'Segoe UI',sans-serif;background:#f8fafc;padding:16px;}}
    .ct{{font-size:13px;font-weight:800;color:#0f4287;letter-spacing:.05em;margin-bottom:12px;}}
    .cw{{position:relative;width:100%;height:240px;}}canvas{{width:100%!important;height:100%!important;}}
    .leg{{display:flex;gap:20px;margin-top:10px;}}.li{{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:700;color:#374151;}}
    .ld{{width:12px;height:12px;border-radius:50%;}}
    .tb{{position:absolute;background:rgba(15,30,60,.92);color:#fff;border-radius:10px;padding:10px 14px;font-size:12px;pointer-events:none;display:none;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.3);z-index:99;min-width:160px;}}
    .tt{{font-weight:800;font-size:13px;margin-bottom:6px;color:#93c5fd;}}
    .tr{{display:flex;justify-content:space-between;gap:16px;margin:2px 0;}}
    .tl{{color:rgba(255,255,255,.7);font-weight:600;}}.tv{{font-weight:800;}}
    </style></head><body><div class="ct">&#128200; Línea de Tiempo — Comisión Operativa por Mes</div>
    <div class="cw"><canvas id="coC"></canvas>
    <div class="tb" id="tip"><div class="tt" id="tm"></div>
    <div class="tr"><span class="tl">Registros</span><span class="tv" id="tr1" style="color:#60a5fa"></span></div>
    <div class="tr"><span class="tl">Comisi\xc3\xb3n</span><span class="tv" id="tr2" style="color:#34d399"></span></div></div></div>
    <div class="leg"><div class="li"><div class="ld" style="background:#1976d2"></div>Registros (eje izq.)</div>
    <div class="li"><div class="ld" style="background:#00897b"></div>Comisi\xc3\xb3n S/ (eje der.)</div></div>
    <script>
    var M={_meses_js},R={_regs_js},C={_comis_js},mR={_max_reg},mC={_max_com};
    var cv=document.getElementById('coC'),tip=document.getElementById('tip'),ctx=cv.getContext('2d');
    var PL=56,PT=16,PB=38,PR=56,n=M.length;
    function fmt(v){{return Math.round(v).toLocaleString('es-PE');}}
    function fmtS(v){{return 'S/ '+v.toLocaleString('es-PE',{{minimumFractionDigits:2,maximumFractionDigits:2}})}}
    function W(){{return cv.offsetWidth;}}function H(){{return cv.offsetHeight;}}
    function xP(i){{return PL+(i/(n-1||1))*(W()-PL-PR);}}
    function yP(v,mx){{return PT+(H()-PT-PB)*(1-v/(mx||1));}}
    function resize(){{
      cv.width=cv.parentElement.clientWidth*devicePixelRatio;
      cv.height=cv.parentElement.clientHeight*devicePixelRatio;
      cv.style.width=cv.parentElement.clientWidth+'px';
      cv.style.height=cv.parentElement.clientHeight+'px';
      ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);draw();
    }}
    function draw(){{
      ctx.clearRect(0,0,W(),H());
      ctx.strokeStyle='rgba(0,0,0,0.07)';ctx.lineWidth=1;
      for(var g=0;g<=4;g++){{var gy=PT+(H()-PT-PB)*g/4;ctx.beginPath();ctx.moveTo(PL,gy);ctx.lineTo(W()-PR,gy);ctx.stroke();}}
      ctx.beginPath();
      for(var i=0;i<n;i++){{var x=xP(i),y=yP(R[i],mR);i?ctx.lineTo(x,y):ctx.moveTo(x,y);}}
      ctx.lineTo(xP(n-1),H()-PB);ctx.lineTo(xP(0),H()-PB);ctx.closePath();
      var g2=ctx.createLinearGradient(0,PT,0,H()-PB);
      g2.addColorStop(0,'rgba(25,118,210,.2)');g2.addColorStop(1,'rgba(25,118,210,.01)');
      ctx.fillStyle=g2;ctx.fill();
      ctx.lineJoin='round';ctx.lineCap='round';
      ctx.strokeStyle='#1976d2';ctx.lineWidth=2.5;ctx.setLineDash([]);
      ctx.beginPath();for(var i=0;i<n;i++){{var x=xP(i),y=yP(R[i],mR);i?ctx.lineTo(x,y):ctx.moveTo(x,y);}}ctx.stroke();
      ctx.strokeStyle='#00897b';ctx.lineWidth=2.5;ctx.setLineDash([6,3]);
      ctx.beginPath();for(var i=0;i<n;i++){{var x=xP(i),y=yP(C[i],mC);i?ctx.lineTo(x,y):ctx.moveTo(x,y);}}ctx.stroke();
      ctx.setLineDash([]);
      for(var i=0;i<n;i++){{
        [{{x:xP(i),y:yP(R[i],mR),s:'#1976d2'}},{{x:xP(i),y:yP(C[i],mC),s:'#00897b'}}].forEach(function(d){{
          ctx.beginPath();ctx.arc(d.x,d.y,3.5,0,Math.PI*2);ctx.fillStyle='#fff';ctx.fill();
          ctx.strokeStyle=d.s;ctx.lineWidth=2;ctx.stroke();
        }});
      }}
      ctx.fillStyle='#6b7280';ctx.font='9px Segoe UI';ctx.textAlign='center';
      var step=Math.max(1,Math.ceil(n/8));
      for(var i=0;i<n;i+=step){{ctx.fillText(M[i],xP(i),H()-PB+14);}}
      ctx.textAlign='right';ctx.fillStyle='#1976d2';ctx.font='9px Segoe UI';
      for(var g=0;g<=4;g++){{var v=mR*(4-g)/4,gy=PT+(H()-PT-PB)*g/4;ctx.fillText(fmt(v),PL-5,gy+3);}}
      ctx.textAlign='left';ctx.fillStyle='#00897b';
      for(var g=0;g<=4;g++){{var v=mC*(4-g)/4,gy=PT+(H()-PT-PB)*g/4;ctx.fillText(fmt(v),W()-PR+5,gy+3);}}
    }}
    cv.addEventListener('mousemove',function(e){{
      var r=cv.getBoundingClientRect(),mx=e.clientX-r.left;
      var idx=Math.round((mx-PL)/(W()-PL-PR)*(n-1));
      idx=Math.max(0,Math.min(idx,n-1));
      if(Math.abs(mx-xP(idx))<28){{
        document.getElementById('tm').textContent=M[idx];
        document.getElementById('tr1').textContent=fmt(R[idx]);
        document.getElementById('tr2').textContent=fmtS(C[idx]);
        var tx=xP(idx)+16,ty=e.clientY-r.top-44;
        if(tx+160>W())tx=xP(idx)-176;
        tip.style.left=tx+'px';tip.style.top=ty+'px';tip.style.display='block';
        draw();
        ctx.strokeStyle='rgba(0,0,0,.12)';ctx.lineWidth=1;ctx.setLineDash([4,4]);
        ctx.beginPath();ctx.moveTo(xP(idx),PT);ctx.lineTo(xP(idx),H()-PB);ctx.stroke();ctx.setLineDash([]);
      }}else{{tip.style.display='none';}}
    }});
    cv.addEventListener('mouseleave',function(){{tip.style.display='none';draw();}});
    window.addEventListener('resize',resize);resize();
    </script></body></html>"""
                            _stc_co_chart.html(_chart_html, height=320, scrolling=False)


                    # ── Tabla detalle ────────────────────────────────────────
                    with st.expander("📋 Ver detalle de COMI_OPERATIVA.csv (filas con COMSION_OPERATIVA > 0)", expanded=False):
                        _cols_det = [c for c in ["DISTRIBUIDOR","SOT","SEC","PLAN_TARIFARIO","FECHA_ACTIVACION",
                                                  "FECHA_INSTALACION","TIPO_OPERACION","DEPARTAMENTO",
                                                  "COMSION_OPERATIVA","TOTAL"] if c in _df_co.columns]
                        _df_det_co = _df_co[_mask_com_op][_cols_det].copy() if _col_com_op else _df_co[_cols_det].copy()
                        if "COMSION_OPERATIVA" in _df_det_co.columns:
                            _df_det_co["COMSION_OPERATIVA"] = pd.to_numeric(_df_det_co["COMSION_OPERATIVA"], errors="coerce").fillna(0).map(formatear_moneda)
                        st.dataframe(_df_det_co, use_container_width=True, height=400)

                        _csv_co = _df_det_co.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                        st.download_button(
                            "⬇️ Descargar detalle Comisión Operativa",
                            data=_csv_co,
                            file_name="comision_operativa_detalle.csv",
                            mime="text/csv",
                            key="dl_comision_operativa"
                        )
            except Exception as e:
                import traceback
                st.error(f"⚠️ Error al cargar Comisión Operativa: {e}")
                with st.expander("Ver detalle técnico del error"):
                    st.code(traceback.format_exc())

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

