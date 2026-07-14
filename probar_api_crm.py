from __future__ import annotations

from api_client import fetch_crm_products, normalize_crm_products_to_dvz


def main():
    reports = fetch_crm_products()
    if reports is None:
        print("El modo API no esta activo. Usa DASHBOARD_DATA_SOURCE=api.")
        return

    df = normalize_crm_products_to_dvz(reports)
    print(f"Registros API: {len(reports)}")
    print(f"Filas normalizadas DVZ: {len(df)}")
    print("Columnas principales:")
    for col in [
        "Tipo Producto",
        "FECHA DE VENTA",
        "ASESOR",
        "Datos adicionales - Clip",
        "Back Office - SOT",
        "Datos adicionales - SEC",
        "SUPERVISOR",
        "FECHA INSTALACION",
        "TIPIS",
    ]:
        print(f"- {col}: {'OK' if col in df.columns else 'FALTA'}")


if __name__ == "__main__":
    main()
