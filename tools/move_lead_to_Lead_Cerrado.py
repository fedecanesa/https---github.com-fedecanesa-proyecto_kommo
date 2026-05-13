import os
import requests


def move_lead_to_Lead_Cerrado(lead_id: int) -> bool:
    subdomain = os.getenv("KOMMO_SUBDOMAIN")
    access_token = os.getenv("KOMMO_ACCESS_TOKEN")
    pipeline_id = int(os.getenv("KOMMO_PIPELINE_ID"))
    status_id = int(os.getenv("KOMMO_LEAD_CERRADO_STATUS_ID"))

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
        print(f"🔀 Lead {lead_id} movido a 'Lead Cerrado' (status {status_id})")
        return True
    else:
        print(f"❌ Error moviendo lead a Lead Cerrado: {response.status_code}")
        print(f"   Detalle: {response.text}")
        return False
