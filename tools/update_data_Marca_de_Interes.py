"""
Tool para actualizar el campo "Marca de Interés" en un lead de Kommo.
Usa el endpoint PATCH /api/v4/leads/{id}
Docs: https://developers.kommo.com/reference/updating-single-lead
"""

import os
import requests

MARCA_INTERES_FIELD_ID = 2030070


def update_data_Marca_de_Interes(lead_id: int, marca: str) -> bool:
    """
    Actualiza el campo "Marca de Interés" del lead.

    Args:
        lead_id: ID del lead.
        marca: Nombre de la marca/producto de interés.

    Returns:
        True si se actualizó correctamente, False en caso de error.
    """
    subdomain = os.getenv("KOMMO_SUBDOMAIN")
    access_token = os.getenv("KOMMO_ACCESS_TOKEN")

    url = f"https://{subdomain}.kommo.com/api/v4/leads/{lead_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "custom_fields_values": [
            {
                "field_id": MARCA_INTERES_FIELD_ID,
                "values": [{"value": marca}]
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"📌 Lead {lead_id}: Marca de Interés actualizada a '{marca}'")
        return True
    else:
        print(f"❌ Error actualizando Marca de Interés: {response.status_code}")
        print(f"   Detalle: {response.text}")
        return False
