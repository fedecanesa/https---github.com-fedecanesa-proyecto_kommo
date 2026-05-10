"""
Tool para mover un lead a la etapa "Discussão de contrato" en Kommo.
Se activa cuando el cliente quiere discutir formas de pago, financiamiento,
lugar de recogida u otros detalles del contrato.
Usa el endpoint PATCH /api/v4/leads/{id}
Docs: https://developers.kommo.com/reference/updating-single-lead
"""

import os
import requests

def move_lead_to_Discusion_de_Contrato(lead_id: int) -> bool:
    """
    Mueve un lead a la etapa "Discussão de contrato" (discusión de contrato).

    Args:
        lead_id: ID del lead a mover.

    Returns:
        True si se actualizó correctamente, False en caso de error.
    """
    subdomain = os.getenv("KOMMO_SUBDOMAIN")
    access_token = os.getenv("KOMMO_ACCESS_TOKEN")
    pipeline_id = int(os.getenv("KOMMO_PIPELINE_ID"))
    status_id = int(os.getenv("KOMMO_LEAD_CALIFICADO_STATUS_ID"))

    url = f"https://{subdomain}.kommo.com/api/v4/leads/{lead_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "pipeline_id": pipeline_id,
        "status_id": status_id,
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"🔀 Lead {lead_id} movido a 'Discussão de contrato' (status {STATUS_ID})")
        return True
    else:
        print(f"❌ Error moviendo lead a Discussão de contrato: {response.status_code}")
        print(f"   Detalle: {response.text}")
        return False
