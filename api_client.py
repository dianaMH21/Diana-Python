from __future__ import annotations

from functools import lru_cache
from io import StringIO
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

import pandas as pd

from config import (
    API_BASE_URL,
    API_TOKEN,
    CRM_EMAIL,
    CRM_FILTERS,
    CRM_LOGIN_URL,
    CRM_PASSWORD,
    CRM_REPORT_URL,
    CRM_TIMEOUT,
    DATA_SOURCE,
)


def api_enabled() -> bool:
    return DATA_SOURCE == "api"


def _read_response(resp) -> tuple[str, str]:
    content_type = resp.headers.get("Content-Type", "").lower()
    raw = resp.read().decode("utf-8-sig")
    return content_type, raw


def _request_json(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> dict:
    data = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=req_headers, method=method)
    with urlopen(req, timeout=CRM_TIMEOUT) as resp:
        _, raw = _read_response(resp)
    return json.loads(raw) if raw else {}


@lru_cache(maxsize=1)
def crm_login_token() -> str:
    if API_TOKEN:
        return API_TOKEN
    if not CRM_EMAIL or not CRM_PASSWORD:
        raise RuntimeError("Faltan CRM_EMAIL y/o CRM_PASSWORD para autenticar en CRM.")

    payload = {"email": CRM_EMAIL, "password": CRM_PASSWORD}
    data = _request_json(CRM_LOGIN_URL, method="POST", payload=payload)
    token = data.get("token", "")
    if not token:
        raise RuntimeError("El login CRM no devolvio token.")
    return token


def _parse_filters(filters: dict | None = None) -> dict | None:
    if filters is not None:
        return filters
    if not CRM_FILTERS:
        today = date.today()
        return {"rangeSale": {"from": "2025-01-01", "to": today.strftime("%Y-%m-%d")}}
    try:
        parsed = json.loads(CRM_FILTERS)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def fetch_crm_products(filters: dict | None = None) -> list[dict] | None:
    if not api_enabled():
        return None

    token = crm_login_token()
    query = {}
    parsed_filters = _parse_filters(filters)
    if parsed_filters:
        query["filters"] = json.dumps(parsed_filters, ensure_ascii=False)

    url = CRM_REPORT_URL
    if query:
        url = f"{url}?{urlencode(query)}"

    headers = {"Authorization": f"Bearer {token}"}
    data = _request_json(url, method="GET", headers=headers)
    reports = data.get("reports", [])
    if not isinstance(reports, list):
        return []
    return reports


def _nested(row: dict, *keys, default=""):
    cur = row
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def _full_name(*parts) -> str:
    clean = [str(p).strip() for p in parts if p is not None and str(p).strip()]
    return " ".join(clean)


def _tipo_producto(value) -> str:
    text = str(value or "").strip().upper()
    text = text.replace("MÓVIL", "MOVIL").replace("MOVILE", "MOVIL")
    if text == "MOBILE":
        text = "MOVIL"
    return text


def _normalizar_clip(value, campaign="") -> str:
    text = str(value or "").strip()
    up = text.upper()
    camp = str(campaign or "").upper()
    if up in {"D&C", "DC", "DYC"}:
        return "D&C"
    if "TELETALK" in up:
        return "TELETALK"
    if "D&C" in camp or " DC" in camp or camp.endswith("DC"):
        return "D&C"
    if "TELETALK" in camp:
        return "TELETALK"
    return text


def normalize_crm_products_to_dvz(reports: list[dict]) -> pd.DataFrame:
    rows = []
    for item in reports or []:
        data = item.get("data") if isinstance(item.get("data"), dict) else {}
        creator = item.get("creator") if isinstance(item.get("creator"), dict) else {}

        asesor = _full_name(creator.get("name"), creator.get("last_name")) or str(creator.get("name") or "").strip()
        cliente = _full_name(
            data.get("name") or data.get("first_name"),
            data.get("last_name1"),
            data.get("last_name2"),
        )
        clip = _normalizar_clip(data.get("clip"), item.get("campaign"))
        tipo_producto = _tipo_producto(item.get("product_type"))
        fecha_venta = item.get("venta_start_date") or item.get("createdAt") or ""
        fecha_inst = data.get("installationDate") or ""
        sale_sub = data.get("saleSub_state") or data.get("sale_sub_state") or ""

        rows.append({
            "ID CRM": item.get("id", ""),
            "Campaña": item.get("campaign", ""),
            "Tipo Producto": tipo_producto,
            "FECHA DE VENTA": fecha_venta,
            "Fecha de Venta": fecha_venta,
            "Fecha Venta": fecha_venta,
            "Fecha Creacion CRM": item.get("createdAt", ""),
            "USUARIO": asesor,
            "ASESOR": asesor,
            "EXTENSION DEL USUARIO": item.get("extension", ""),
            "Datos adicionales - Clip": clip,
            "Back Office - SOT": data.get("sot", ""),
            "SOT": data.get("sot", ""),
            "Datos adicionales - SEC": data.get("sec", ""),
            "SEC": data.get("sec", ""),
            "Datos adicionales - Documento": data.get("document", ""),
            "Documento": data.get("document", ""),
            "Cliente - Nombre": data.get("name") or data.get("first_name") or "",
            "Cliente - Apellido Paterno": data.get("last_name1", ""),
            "Cliente - Apellido Materno": data.get("last_name2", ""),
            "Nombre del Cliente": cliente,
            "Datos Adicionales - Supervisor": data.get("supervisor", ""),
            "SUPERVISOR": data.get("supervisor", ""),
            "Back Office - Fecha Instalacion": fecha_inst,
            "FECHA INSTALACION": fecha_inst,
            "Datos Instalacion - Departamento": data.get("departament", ""),
            "Datos Instalación - Departamento": data.get("departament", ""),
            "Estados - Llamada": data.get("main_state", ""),
            "Estados - Especificacion": data.get("sub_state", ""),
            "Estados - Venta": data.get("sale_state", ""),
            "Estados - Venta Especificacion": sale_sub,
            "Estados - Venta Especificación": sale_sub,
            "TIPIS": sale_sub,
            "Productos - Producto": data.get("product", ""),
            "Productos - Producto Especificacion": data.get("sub_product", ""),
            "Productos - Producto Especificación": data.get("sub_product", ""),
            "Cliente - Tipo De Operacion": data.get("typeOperation", ""),
            "Tipo Operacion": data.get("typeOperation", ""),
            "Productos - Precio Oferta": data.get("priceOferta", ""),
            "Precio Oferta": data.get("priceOferta", ""),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df.columns = df.columns.astype(str).str.strip()
    return df


def fetch_dvz_from_api(filters: dict | None = None) -> pd.DataFrame | None:
    if not api_enabled():
        return None
    try:
        reports = fetch_crm_products(filters=filters)
        if reports is None:
            return None
        return normalize_crm_products_to_dvz(reports)
    except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError):
        return None


def fetch_dataset(nombre: str) -> pd.DataFrame | None:
    """Compatibilidad con la capa antigua.

    No se usa para CLARO ni archivos manuales cuando el CRM reemplaza solo DVZ.
    Se mantiene por si luego existe otro endpoint generico.
    """
    if not api_enabled() or not API_BASE_URL:
        return None

    url = f"{API_BASE_URL}/datasets/{nombre}"
    headers = {"Accept": "application/json, text/csv"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=CRM_TIMEOUT) as resp:
            content_type, raw = _read_response(resp)
    except (URLError, HTTPError, TimeoutError):
        return None

    if "text/csv" in content_type or raw.lstrip().startswith(("sep=",)):
        return pd.read_csv(StringIO(raw))

    payload = json.loads(raw)
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    return pd.DataFrame(rows)
