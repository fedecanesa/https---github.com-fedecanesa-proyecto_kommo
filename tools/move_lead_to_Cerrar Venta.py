"""
Tool para mover un lead a la etapa "Cerrar venta" en Kommo.
Se activa cuando el cliente quiere realizar el pago correspondiente.
Usa el endpoint PATCH /api/v4/leads/{id}
Docs: https://developers.kommo.com/reference/updating-single-lead
"""

import os
import requests

# Pipeline: Funil de vendas (principal). Etapa: cerrar venta (ID obtenido con get_pipelines.py)
PIPELINE_ID = 11787268
STATUS_ID = 90710216  # cerrar venta


def move_lead_to_Cerrar_Venta(lead_id: int) -> bool:
    """
    Mueve un lead a la etapa "Cerrar venta" (cuando quiere realizar el pago).

    Args:
        lead_id: ID del lead a mover.

    Returns:
        True si se actualizó correctamente, False en caso de error.
    """
    subdomain = os.getenv("KOMMO_SUBDOMAIN")
    access_token = os.getenv("KOMMO_ACCESS_TOKEN")

    url = f"https://{subdomain}.kommo.com/api/v4/leads/{lead_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "pipeline_id": PIPELINE_ID,
        "status_id": STATUS_ID,
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"🔀 Lead {lead_id} movido a 'Cerrar venta' (status {STATUS_ID})")
        return True
    else:
        print(f"❌ Error moviendo lead a Cerrar venta: {response.status_code}")
        print(f"   Detalle: {response.text}")
        return False
