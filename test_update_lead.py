"""
Script para probar la actualización de custom fields en Kommo.
Ejecutar: python test_update_lead.py
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración
KOMMO_SUBDOMAIN = os.getenv("KOMMO_SUBDOMAIN") or "teknikkaic"
KOMMO_ACCESS_TOKEN = os.getenv("KOMMO_ACCESS_TOKEN") or ""
KOMMO_RESPONSE_FIELD_ID = os.getenv("KOMMO_RESPONSE_FIELD_ID") or "2013940"
KOMMO_SWITCH_FIELD_ID = os.getenv("KOMMO_SWITCH_FIELD_ID") or "2013942"

# Lead de prueba (cambia este ID por uno válido)
LEAD_ID = "27182570"


def test_update_lead():
    """Prueba actualizar un lead con custom fields."""
    
    print(f"\n{'='*60}")
    print("  PRUEBA DE ACTUALIZACIÓN DE CUSTOM FIELDS")
    print(f"{'='*60}\n")
    
    print(f"📋 Configuración:")
    print(f"   Subdominio: {KOMMO_SUBDOMAIN}")
    print(f"   Lead ID: {LEAD_ID}")
    print(f"   Response Field ID: {KOMMO_RESPONSE_FIELD_ID}")
    print(f"   Switch Field ID: {KOMMO_SWITCH_FIELD_ID}")
    print(f"   Token: {'✅ Configurado' if KOMMO_ACCESS_TOKEN else '❌ NO CONFIGURADO'}")
    print()
    
    if not KOMMO_ACCESS_TOKEN:
        print("❌ Error: KOMMO_ACCESS_TOKEN no está configurado")
        return
    
    url = f"https://{KOMMO_SUBDOMAIN}.kommo.com/api/v4/leads/{LEAD_ID}"
    
    headers = {
        "Authorization": f"Bearer {KOMMO_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Mensaje de prueba
    test_message = "🧪 PRUEBA desde script - " + str(os.urandom(4).hex())
    
    payload = {
        "custom_fields_values": [
            {
                "field_id": int(KOMMO_RESPONSE_FIELD_ID),
                "values": [{"value": test_message}]
            },
            {
                "field_id": int(KOMMO_SWITCH_FIELD_ID),
                "values": [{"value": True}]
            }
        ]
    }
    
    print(f"📤 Enviando PATCH a: {url}")
    print(f"📝 Payload: {payload}")
    print()
    
    try:
        response = requests.patch(url, headers=headers, json=payload)
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text[:500]}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Request exitoso!")
            print(f"\n📋 Lead actualizado:")
            print(f"   ID: {data.get('id')}")
            print(f"   Nombre: {data.get('name')}")
            
            # Verificar custom fields en la respuesta
            custom_fields = data.get('custom_fields_values', [])
            print(f"\n📋 Custom Fields en respuesta:")
            for cf in custom_fields:
                print(f"   Field ID {cf.get('field_id')}: {cf.get('values')}")
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"   Detalle: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")


def get_lead_info():
    """Obtiene información actual del lead para verificar."""
    
    print(f"\n{'='*60}")
    print("  INFORMACIÓN ACTUAL DEL LEAD")
    print(f"{'='*60}\n")
    
    url = f"https://{KOMMO_SUBDOMAIN}.kommo.com/api/v4/leads/{LEAD_ID}"
    
    headers = {
        "Authorization": f"Bearer {KOMMO_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Lead: {data.get('name')} (ID: {data.get('id')})")
            
            custom_fields = data.get('custom_fields_values', [])
            print(f"\n📋 Custom Fields actuales:")
            
            for cf in custom_fields:
                field_id = cf.get('field_id')
                field_name = cf.get('field_name', 'Sin nombre')
                values = cf.get('values', [])
                
                # Resaltar los campos que nos interesan
                marker = ""
                if str(field_id) == str(KOMMO_RESPONSE_FIELD_ID):
                    marker = " ← RESPONSE FIELD"
                elif str(field_id) == str(KOMMO_SWITCH_FIELD_ID):
                    marker = " ← SWITCH FIELD"
                
                print(f"   [{field_id}] {field_name}: {values}{marker}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Primero ver estado actual
    get_lead_info()
    
    # Luego intentar actualizar
    test_update_lead()
    
    # Verificar si se actualizó
    print("\n" + "="*60)
    print("  VERIFICANDO DESPUÉS DE LA ACTUALIZACIÓN")
    print("="*60)
    get_lead_info()