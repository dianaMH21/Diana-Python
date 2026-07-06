# Capa preparada para reemplazar CSV por API sin tocar las paginas.
# Por defecto esta desactivada: DASHBOARD_DATA_SOURCE=csv.
from __future__ import annotations

from io import StringIO
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
import json

import pandas as pd

from config import API_BASE_URL, API_TOKEN, DATA_SOURCE


def api_enabled() -> bool:
    return DATA_SOURCE == "api" and bool(API_BASE_URL)


def fetch_dataset(nombre: str) -> pd.DataFrame | None:
    """Devuelve un DataFrame desde el API o None si debe usarse CSV.

    Contrato recomendado del API:
    - GET {API_BASE_URL}/datasets/{nombre}
    - Respuesta JSON: lista de objetos o {"data": [...]}
    - Alternativamente puede responder CSV text/csv.
    """
    if not api_enabled():
        return None

    url = f"{API_BASE_URL}/datasets/{nombre}"
    headers = {"Accept": "application/json, text/csv"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            raw = resp.read().decode("utf-8-sig")
    except (URLError, HTTPError, TimeoutError):
        return None

    if "text/csv" in content_type or raw.lstrip().startswith(("sep=",)):
        return pd.read_csv(StringIO(raw))

    payload = json.loads(raw)
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    return pd.DataFrame(rows)
