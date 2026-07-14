from .common import *

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
    df_show = df_show.rename(columns={
        "Fecha_Claro": "Fecha Claro",
        "Comision_Claro": "Comisión Claro",
        "Comisiones_Claro": "Comisiones Claro",
    })
    java_table(
        df_show,
        height=320,
        title="Ventas pagadas por CLARO no encontradas en DEVELZ",
        subtitle="Conciliación por SOT pagado en CLARO sin coincidencia en la base DEVELZ",
        accent="#dc2626",
        max_rows=300,
    )
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

    _vistas_fija = [
        "📋 Detalle Ventas",
        "📆 Ventas por Día",
        "🏆 Ranking Supervisor",
        "👥 Ranking Asesores",
        "📍 Ranking Departamentos",
        "📊 Estados Operativos",
        "📦 Por Planes",
        "📅 Semana de Pago",
    ]
    _vista_fija = st.radio(
        "Vista Detalle Fija",
        _vistas_fija,
        horizontal=True,
        key="detalle_fija_vista_lazy",
        label_visibility="collapsed",
    )

    if _vista_fija == "📋 Detalle Ventas":
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

    elif _vista_fija == "📆 Ventas por Día":
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

    elif _vista_fija == "🏆 Ranking Supervisor":
        st.markdown("#### 🏆 Ranking Supervisor")
        mostrar_ranking_supervisores_con_asesores(df_filtrado)

    elif _vista_fija == "👥 Ranking Asesores":
        st.markdown("#### 👥 Ranking Asesores")
        ranking_asesores = ranking_asesores_fija_develz(df_filtrado)
        if ranking_asesores.empty:
            st.warning("No se encontraron datos para el ranking de asesores.")
        else:
            ranking_asesores_show = ranking_asesores.copy()
            if "Comision" in ranking_asesores_show.columns:
                ranking_asesores_show["Comision"] = pd.to_numeric(ranking_asesores_show["Comision"], errors="coerce").fillna(0).map(formatear_moneda)
            java_table(ranking_asesores_show, height=460, title="Ranking asesores", subtitle="Productividad por asesor", accent="#6d0b8c", max_rows=300)

    elif _vista_fija == "📍 Ranking Departamentos":
        mostrar_ranking_departamentos_premium(df_filtrado)

    elif _vista_fija == "📊 Estados Operativos":
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

    elif _vista_fija == "📦 Por Planes":
        mostrar_tab_planes_fija_gerencial(df_filtrado, color_borde="#0f4287")

    elif _vista_fija == "📅 Semana de Pago":
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


__all__ = [name for name in globals() if not name.startswith("__")]

