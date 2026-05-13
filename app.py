import os
import sys
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks

sys.path.append(os.path.join(os.path.dirname(__file__), "Kommo Functions"))
from kommo import parse_kommo_webhook, update_lead_with_response, launch_salesbot, get_switch_status

sys.path.append(os.path.join(os.path.dirname(__file__), "tools"))
from tools.move_lead_to_Toma_de_Decision import move_lead_to_Toma_de_Decision
from tools.move_lead_to_Discusion_de_Contrato import move_lead_to_Discusion_de_Contrato
from tools.move_lead_to_Lead_Cerrado import move_lead_to_Lead_Cerrado
from tools.update_data_Marca_de_Interes import update_data_Marca_de_Interes
from tools.update_data_Metodo_de_Pago import update_data_Metodo_de_Pago

from conversation_history import init_chat_store, save_message, format_history_for_prompt
from agent import init_agent, ask_agent, parse_and_clean_tags

load_dotenv()

# Deduplicación: evita procesar el mismo mensaje si Kommo reenvía el webhook
processed_messages: dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 300  # 5 minutos

print("💾 Inicializando historial de conversación (PostgreSQL/Supabase)...")
init_chat_store()

llm, retrieval_tool = init_agent()

app = FastAPI(title="Kommo AI Chatbot")


def is_duplicate(lead_id: str, text: str) -> bool:
    """Verifica si este mensaje ya fue procesado recientemente (deduplicación)."""
    now = time.time()

    expired = [k for k, v in processed_messages.items() if now - v > DEDUP_WINDOW_SECONDS]
    for k in expired:
        del processed_messages[k]

    key = f"{lead_id}:{text}"
    if key in processed_messages:
        return True

    processed_messages[key] = now
    return False


async def process_message(message_text: str, lead_id: str):
    """Procesa el mensaje en segundo plano: genera respuesta con el agente, actualiza lead, lanza salesbot."""
    try:
        # 1. Verificar switch de IA antes de procesar
        if not get_switch_status(lead_id):
            print(f"🔴 Switch IA DESACTIVADO para lead {lead_id}")
            return

        # 2. Guardar mensaje del usuario en el historial
        save_message(lead_id, "user", message_text)

        # 3. Obtener historial y consultar al agente
        history_str = format_history_for_prompt(lead_id)
        response_text = await ask_agent(llm, retrieval_tool, message_text, history_str)

        # 4. Parsear tags y limpiar respuesta
        tags = parse_and_clean_tags(response_text)
        clean_response = tags["clean_response"]

        print(f"🤖 Respuesta: {clean_response[:80]}...")

        # 4. Guardar respuesta del asistente en el historial
        save_message(lead_id, "assistant", clean_response)

        # 5. Ejecutar acciones según tags detectados
        if tags["is_closed"]:
            print(f"🏁 COMPRA CERRADA detectada para lead {lead_id}")
            move_lead_to_Lead_Cerrado(int(lead_id))
        elif tags["is_contract"]:
            print(f"📝 DISCUSIÓN DE CONTRATO detectada para lead {lead_id}")
            move_lead_to_Discusion_de_Contrato(int(lead_id))
        elif tags["is_interested"]:
            print(f"🎯 INTERÉS DE COMPRA detectado para lead {lead_id}")
            move_lead_to_Toma_de_Decision(int(lead_id))

        if tags["marca"]:
            update_data_Marca_de_Interes(int(lead_id), tags["marca"])

        if tags["pago"]:
            update_data_Metodo_de_Pago(int(lead_id), tags["pago"])

        # 6. Actualizar lead en Kommo y lanzar salesbot solo si el update fue exitoso
        updated = update_lead_with_response(lead_id, clean_response)
        if not updated:
            print(f"❌ No se pudo actualizar el lead {lead_id}. Se omite lanzamiento de Salesbot.")
            return

        print(f"✅ Lead {lead_id} actualizado: respuesta guardada + switch activado")

        launch_salesbot(lead_id)

    except Exception as e:
        print(f"❌ Error procesando mensaje: {str(e)}")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Kommo AI Chatbot activo"}


@app.get("/webhook/kommo")
async def kommo_webhook_info():
    return {
        "status": "ok",
        "message": "Endpoint activo. Kommo debe enviar POST form-urlencoded a esta URL."
    }


@app.post("/webhook/kommo")
async def kommo_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()

    data = parse_kommo_webhook(body)

    message_text = data.get("text", "")
    lead_id = data.get("lead_id")
    chat_id = data.get("chat_id")
    entity_type = data.get("entity_type")
    message_type = data.get("type", "")
    author_type = data.get("author_type")

    print(
        "🧾 Webhook parseado: "
        f"lead_id={lead_id}, chat_id={chat_id}, entity_type={entity_type}, "
        f"type={message_type}, author_type={author_type}, "
        f"text_len={len(message_text.strip()) if message_text else 0}"
    )

    # Solo procesar mensajes entrantes de contactos (clientes).
    # Salesbot, agentes humanos y cualquier otro remitente se ignoran.
    if message_type == "outgoing":
        print("⏭️ Webhook ignorado: outgoing message")
        return {"status": "ignored", "reason": "outgoing message"}

    # Ignorar mensajes de agentes humanos y bots. Clientes llegan como "contact" o "external".
    if author_type and str(author_type).lower() in ("user", "bot"):
        print(f"⏭️ Webhook ignorado: author_type={author_type}")
        return {"status": "ignored", "reason": f"non-contact author: {author_type}"}

    if not message_text or not lead_id:
        print("⏭️ Webhook ignorado: missing data")
        return {"status": "ignored", "reason": "missing data"}

    if len(message_text.strip()) < 1:
        print("⏭️ Webhook ignorado: empty message")
        return {"status": "ignored", "reason": "empty message"}

    if is_duplicate(lead_id, message_text):
        print(f"⏭️ Webhook duplicado ignorado (lead {lead_id})")
        return {"status": "ignored", "reason": "duplicate webhook"}

    print(f"📩 Webhook recibido de Kommo!")
    print(f"💬 Mensaje: '{message_text[:50]}...' | Lead ID: {lead_id}")

    background_tasks.add_task(process_message, message_text, lead_id)

    return {"status": "ok", "message": "processing"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
