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


__all__ = [name for name in globals() if not name.startswith("__")]

