from .common import *
from .fija import *

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


@st.cache_data(ttl=1800, show_spinner=False)
def _excel_bytes_detalle_movil_general(detalle, resumen_general):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        detalle.to_excel(writer, index=False, sheet_name="Detalle Movil")
        resumen_general.to_excel(writer, index=False, sheet_name="Resumen")
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

def _normalizar_producto_movil_general(serie):
    s = serie.fillna("").astype(str).str.strip()
    s = s.str.replace("\u00a0", " ", regex=False)
    s = s.str.replace(r"\s+", " ", regex=True)
    s = s.str.upper()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ü", "U")]:
        s = s.str.replace(a, b, regex=False)
    return s

def _filtrar_productos_brutos_movil_general(df):
    col_producto = encontrar_columna_flexible(df, [
        "Productos - Producto Especificacion",
        "Productos - Producto Especificación",
        "Productos - producto Especificacion",
        "Productos - producto Especificación",
        "PRODUCTOS - PRODUCTO ESPECIFICACION",
        "PRODUCTOS - PRODUCTO ESPECIFICACIÓN",
    ])
    if not col_producto:
        return df

    excluidos = {
        "CHIP PREPAGO",
        "IFI INTERNET INALAMBRICO",
        "OLO INTERNET PORTATIL",
        "TFI",
    }
    producto_norm = _normalizar_producto_movil_general(df[col_producto])
    return df[~producto_norm.isin(excluidos)].copy()

@st.cache_data(ttl=3600, show_spinner=False)
def construir_resumen_movil_general(filtro_mes="Todos los meses", usar_api=False):
    """
    Detalle Móvil General consolidado.

    Lógica final:
    1. MOVIL_DC/MOVIL_TELETALK, desde DVZ.csv si existe, validan ventas brutas comerciales.
    2. CLARO_DC_MOVIL/CLARO_TELETALK_MOVIL define las ventas reales pagadas/no pagadas.
    3. El Tipo Operacion sale de TRANSACCION de CLARO, no de Cliente - Tipo De Operacion.
    4. Cada fila de CLARO conserva su propia COMISION TOTAL.
    5. Ventas brutas cuenta repetidos y excluye CHIP PREPAGO, IFI Internet Inalambrico,
       OLO Internet Portatil y TFI desde Productos - Producto Especificacion.
    """
    configuracion_movil = [
        ("D&C", ["MOVIL_DC.csv"]),
        ("Teletalk", ["MOVIL_TELETALK.csv"]),
    ]

    bases_movil = []
    for canal, posibles_archivos in configuracion_movil:
        df, archivo_usado = _leer_csv_movil_con_fallback(posibles_archivos, usar_api=usar_api)
        if df.empty: continue

        df = _filtrar_productos_brutos_movil_general(df.copy())
        if df.empty: continue
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
            df = df.sort_values("_FECHA_VENTA_MOVIL_DT", ascending=False, na_position="last")
            df["_ORDEN_VENTA_MOVIL"] = df.groupby(["Canal", "DOCUMENTO_KEY"]).cumcount()
            # Cruce DOTACION para COLA por extensión del usuario
            # BUSCARV: EXTENSION DEL USUARIO (Excel datos)  ->  USUARIO (DOTACION)  ->  SEGMENTO
            col_ext_movil = encontrar_columna(df, ["EXTENSION DEL USUARIO","EXTENSIÓN DEL USUARIO","Extension del usuario","EXTENSION","Extension"])
            df["COLA"] = _data_loader._agregar_cola_por_extension(df, col_ext_movil) if col_ext_movil else "EXTERNO"
            bases_movil.append(df[[
                "Canal", "DOCUMENTO_KEY", "Documento", "Cliente", "SUPERVISOR", "TIPIS", "ASESOR",
                "Departamento", "COLA", "_FECHA_VENTA_MOVIL_DT", "_FECHA_INSTALACION_DT", "_ORDEN_VENTA_MOVIL",
                "Columna Supervisor", "Columna Tipificación", "Columna Documento Movil", "Columna Fecha Movil"
            ]])

    columnas_salida = [
        "Canal", "Archivo", "FECHA DE VENTA", "_FECHA_VENTA_DT", "_ANIO", "_MES",
        "DOCUMENTO_KEY", "Documento", "Tipo Operacion", "Cliente", "SUPERVISOR", "TIPIS",
        "ASESOR", "Departamento", "COLA", "_FECHA_INSTALACION_DT", "Transaccion", "Plan", "COMISION_REAL", "COMISION", "Estado Pago",
        "Columna Fecha", "Columna Tipo Operacion", "Columna Documento", "Columna Supervisor", "Columna Tipificación"
    ]

    if not bases_movil: return pd.DataFrame(columns=columnas_salida + ["Venta Valida"])

    movil_unicos = pd.concat(bases_movil, ignore_index=True)

    claro = construir_pagos_claro_movil_por_dni_mes(filtro_mes, "Todos")
    if not claro.empty:
        claro = claro.sort_values("_FECHA_OPERACION_DT", ascending=False, na_position="last").copy()
        claro["_ORDEN_VENTA_MOVIL"] = claro.groupby(["Canal", "DOCUMENTO_KEY"]).cumcount()
    else:
        claro = pd.DataFrame(columns=[
            "Canal", "DOCUMENTO_KEY", "_ORDEN_VENTA_MOVIL", "Archivo", "FECHA DE VENTA",
            "_FECHA_OPERACION_DT", "_ANIO", "_MES", "Tipo Operacion", "Transaccion",
            "Plan", "COMISION_REAL", "Estado Pago", "Columna Fecha",
            "Columna Tipo Operacion", "Columna Documento"
        ])

    df_all = movil_unicos.merge(
        claro,
        on=["Canal", "DOCUMENTO_KEY", "_ORDEN_VENTA_MOVIL"],
        how="left",
        suffixes=("_MOVIL", "")
    )
    df_all["Archivo"] = df_all["Archivo"].fillna("MOVIL sin cruce CLARO")
    df_all["FECHA DE VENTA"] = df_all["FECHA DE VENTA"].fillna(df_all["_FECHA_VENTA_MOVIL_DT"].dt.strftime("%d/%m/%Y"))
    df_all["_ANIO"] = df_all["_ANIO"].fillna(df_all["_FECHA_VENTA_MOVIL_DT"].dt.year.astype("Int64"))
    df_all["_MES"] = df_all["_MES"].fillna(df_all["_FECHA_VENTA_MOVIL_DT"].dt.month.astype("Int64"))
    df_all["Tipo Operacion"] = df_all["Tipo Operacion"].fillna("SIN TRANSACCION CLARO")
    df_all["Transaccion"] = df_all["Transaccion"].fillna("SIN TRANSACCION CLARO")
    df_all["Plan"] = df_all["Plan"].fillna("Sin Plan")
    df_all["COMISION_REAL"] = pd.to_numeric(df_all["COMISION_REAL"], errors="coerce").fillna(0.0)
    df_all["COMISION"] = df_all["COMISION_REAL"]
    df_all["Estado Pago"] = df_all["Estado Pago"].fillna("NO PAGADA")
    df_all["Columna Fecha"] = df_all["Columna Fecha"].fillna("FECHA OPERACION CLARO")
    df_all["Columna Tipo Operacion"] = df_all["Columna Tipo Operacion"].fillna("TRANSACCION CLARO")
    df_all["Columna Documento"] = df_all["Columna Documento"].fillna(df_all.get("Columna Documento Movil", "Cliente - Documento"))

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
            for mes in filtro_mes:
                dfs_general.append(construir_resumen_movil_general(mes))
            df_general = pd.concat(dfs_general, ignore_index=True) if dfs_general else pd.DataFrame()

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

    if df_general.empty:
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

    _vistas_movil = [
        "📋 Resumen General",
        "📆 Ventas por Día",
        "🏆 Ranking Supervisor",
        "👥 Ranking Asesores",
        "📍 Ranking Departamentos",
        "📊 Caídas Teletalk",
        "📦 Planes por Precio Oferta"
    ]
    _vista_movil = st.radio(
        "Vista Detalle Móvil",
        _vistas_movil,
        horizontal=True,
        key="detalle_movil_vista_lazy",
        label_visibility="collapsed",
    )

    if _vista_movil == "📋 Resumen General":
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

            st.download_button(
                "⬇️ Descargar Detalle Móvil General en Excel",
                data=_excel_bytes_detalle_movil_general(detalle, resumen_general),
                file_name="detalle_movil_general.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_detalle_movil_general_excel",
                on_click=registrar_descarga,
                args=("Detalle Móvil General", "detalle_movil_general.xlsx", f"Fecha Venta: {', '.join(filtro_mes)} | Canal: {', '.join(sel_canal) if sel_canal else 'Todos'}")
            )

    elif _vista_movil == "📆 Ventas por Día":
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

    elif _vista_movil == "🏆 Ranking Supervisor":
        st.markdown("#### 🏆 Ranking Supervisor")
        mostrar_ranking_supervisor_movil_expandible(df_filtrado)

    elif _vista_movil == "👥 Ranking Asesores":
        st.markdown("#### 👥 Ranking Asesores")
        r_ase = ranking_movil_por_columna(df_filtrado, "ASESOR", "ASESOR")
        if r_ase.empty:
            st.warning("No se encontraron asesores.")
        else:
            show = r_ase.copy()
            show["Comision"] = show["Comision"].map(formatear_moneda)
            st.dataframe(show, use_container_width=True, height=460)

    elif _vista_movil == "📍 Ranking Departamentos":
        mostrar_ranking_departamentos_movil_gerencial(df_filtrado, ", ".join(filtro_mes) if len(filtro_mes) > 1 else filtro_mes[0], filtro_canal)

    elif _vista_movil == "📊 Caídas Teletalk":
        st.markdown("#### 📊 Caídas Teletalk")
        dfs_caidas = []
        for mes in filtro_mes:
            dfs_caidas.append(construir_detalle_movil_teletalk_caidas(mes))
        df_caidas_tt = pd.concat(dfs_caidas, ignore_index=True) if dfs_caidas else pd.DataFrame()
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

    elif _vista_movil == "📦 Planes por Precio Oferta":
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




__all__ = [name for name in globals() if not name.startswith("__")]
