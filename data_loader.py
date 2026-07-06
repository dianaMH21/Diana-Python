import os
import re

import pandas as pd
import streamlit as st

from api_client import fetch_dataset
from config import DATA_DIR, CSV_MAP, _DVZ_SPLIT_MAP

def _leer_dvz_crudo():
    ruta = os.path.join(DATA_DIR, "DVZ.csv")
    if not os.path.exists(ruta):
        return pd.DataFrame()
    for enc in ["utf-8-sig","utf-8","cp1252","latin-1","iso-8859-1"]:
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

@st.cache_data(ttl=3600)
def cargar_csv(nombre):
    df_api = fetch_dataset(nombre)
    if df_api is not None:
        df_api.columns = df_api.columns.astype(str).str.strip()
        return df_api

    # Si DVZ.csv existe y el nombre corresponde a uno de los 4 archivos viejos,
    # leer siempre desde DVZ filtrado. No debe volver a leer FIJA_DC/FIJA_TELETALK/MOVIL_DC/MOVIL_TELETALK.
    if nombre in _DVZ_SPLIT_MAP and os.path.exists(os.path.join(DATA_DIR, "DVZ.csv")):
        df_dvz = _cargar_dvz_filtrado(nombre)
        if not df_dvz.empty:
            return df_dvz
        st.error(f"DVZ.csv se encontró, pero no devolvió filas para {nombre}. Verifica columnas Tipo Producto / Datos Adicionales - Clip en DVZ.csv.")
        return pd.DataFrame()

    ruta = os.path.join(DATA_DIR, nombre)
    for enc in ["utf-8-sig","utf-8","cp1252","latin-1","iso-8859-1"]:
        for sep in [";",",","\t"]:
            try:
                df = pd.read_csv(ruta, encoding=enc, sep=sep, on_bad_lines="skip", engine="python")
                df.columns = df.columns.str.strip()
                if len(df.columns) > 1:
                    return df
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
