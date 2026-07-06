# Configuracion central del dashboard.
# Ajusta estas variables via entorno cuando conectes el API o cambies rutas.
import os

APP_TITLE = os.getenv("DASHBOARD_APP_TITLE", "Dashboard Teletalk Digital")
APP_LAYOUT = os.getenv("DASHBOARD_APP_LAYOUT", "wide")
DATA_SOURCE = os.getenv("DASHBOARD_DATA_SOURCE", "csv").lower()  # csv | api
API_BASE_URL = os.getenv("DASHBOARD_API_BASE_URL", "").rstrip("/")
API_TOKEN = os.getenv("DASHBOARD_API_TOKEN", "")

DATA_DIR = os.getenv("DASHBOARD_DATA_DIR", ".")
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

ruta_base    = os.getenv("DASHBOARD_ASSETS_DIR", DATA_DIR)
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
