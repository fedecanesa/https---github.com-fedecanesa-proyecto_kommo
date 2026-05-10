"""
Historial de Conversación con PostgreSQL (Supabase)
Usa PostgresChatStore + ChatMemoryBuffer de LlamaIndex
para persistir la memoria de conversación automáticamente.

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.storage.chat_store.postgres import PostgresChatStore

load_dotenv()

# ──────────────────────────────────────────────
# 1. CONFIGURACIÓN DE BASE DE DATOS (Memoria)
# ──────────────────────────────────────────────

def _build_database_url() -> str:
    """
    Construye la URL de conexión a PostgreSQL desde variables de entorno.
    Compatible con Supabase (que es PostgreSQL por debajo).
    """
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")

    if not all([DB_USER, DB_PASSWORD, DB_HOST]):
        raise ValueError(
            "❌ Faltan variables de base de datos en .env\n"
            "Requeridas: DB_USER, DB_PASSWORD, DB_HOST"
        )

    # PostgresChatStore usa asyncpg, requiere el prefijo postgresql+asyncpg://
    url = f"postgresql+asyncpg://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"🔌 Conectando memoria a: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    return url


# ──────────────────────────────────────────────
# 2. INICIALIZACIÓN DEL CHAT STORE
# ──────────────────────────────────────────────

chat_store: PostgresChatStore | None = None


def init_chat_store() -> PostgresChatStore:
    """
    Inicializa el PostgresChatStore para persistir el historial de chat.
    Equivalente al PostgresChatMessageHistory de LangChain.
    """
    global chat_store
    database_url = _build_database_url()
    chat_store = PostgresChatStore.from_uri(
        uri=database_url,
        table_name="kommo_chat_history",
    )
    print("✅ PostgresChatStore inicializado (Supabase)")
    return chat_store


# ──────────────────────────────────────────────
# 3. FUNCIONES DE MEMORIA POR LEAD
# ──────────────────────────────────────────────

def get_memory_for_lead(lead_id: str) -> ChatMemoryBuffer:
    """
    Crea un ChatMemoryBuffer para un lead específico.
    Cada lead_id tiene su propia memoria persistida en PostgreSQL.

    Equivalente en LangChain:
        history = PostgresChatMessageHistory("table", session_id, connection)

    En LlamaIndex:
        memory = ChatMemoryBuffer(chat_store=store, chat_store_key=lead_id)
    """
    return ChatMemoryBuffer.from_defaults(
        token_limit=3000,
        chat_store=chat_store,
        chat_store_key=str(lead_id),
    )


def save_message(lead_id: str, role: str, content: str):
    """
    Guarda un mensaje en el historial persistente.

    Args:
        lead_id: ID del lead en Kommo (se usa como chat_store_key).
        role: 'user' o 'assistant'.
        content: Texto del mensaje.
    """
    msg_role = MessageRole.USER if role == "user" else MessageRole.ASSISTANT
    message = ChatMessage(role=msg_role, content=content)
    chat_store.add_message(str(lead_id), message)


def format_history_for_prompt(lead_id: str) -> str:
    """
    Devuelve el historial formateado como string para inyectar en el prompt.
    Usa ChatMemoryBuffer para respetar el token_limit (3000 tokens).

    Ejemplo de salida:
        Cliente: Hola, quiero información sobre VitaCalm
        Andrea: ¡Hola! VitaCalm es un suplemento natural...
        Cliente: ¿Cuánto cuesta?
    """
    memory = get_memory_for_lead(lead_id)
    messages = memory.get()

    if not messages:
        return "(Primera conversación con este cliente)"

    lines = []
    for msg in messages:
        if msg.role == MessageRole.USER:
            speaker = "Cliente"
        elif msg.role == MessageRole.ASSISTANT:
            speaker = "Andrea"
        else:
            continue
        lines.append(f"{speaker}: {msg.content}")

    return "\n".join(lines)
