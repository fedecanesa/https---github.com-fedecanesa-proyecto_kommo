# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI webhook service that acts as an AI sales assistant ("Andrea") for the Kommo CRM. It receives Kommo message webhooks, runs a LlamaIndex `FunctionAgent` (GPT-4.1) backed by a LlamaCloud RAG index over product PDFs, persists conversation history per lead in PostgreSQL/Supabase, and writes the response back into Kommo by updating a custom field and triggering a Salesbot.

## Common Commands

```bash
# Create / activate conda env (Python 3.11)
conda create --name LlamaIndex-proj-Kommo python=3.11
conda activate LlamaIndex-proj-Kommo

pip install -r requirements.txt

# Run the webhook server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Expose locally for Kommo webhooks
ngrok http 8000

# (Re)build the LlamaCloud index from PDFs in "Base de Conocimiento/"
python RAG/rag.py

# Helpers to inspect Kommo configuration (custom field IDs, pipelines)
python support_tools/get_custom_fields.py
python support_tools/get_pipelines.py

# Smoke test for the lead-update flow (uses a hardcoded lead_id inside the file)
python test_update_lead.py
```

## Required Environment Variables (`.env`)

- `OPENAI_API_KEY` — used by `llama-index-llms-openai` and embeddings.
- `LLAMA_CLOUD_API_KEY` — index `productos_de_salud_aidev14_kommo_crm` in project `Default`.
- `KOMMO_SUBDOMAIN`, `KOMMO_ACCESS_TOKEN` — long-lived integration token.
- `KOMMO_RESPONSE_FIELD_ID` — custom field where the AI reply is written.
- `KOMMO_SWITCH_FIELD_ID` — checkbox custom field; webhook is ignored when off.
- `KOMMO_SALESBOT_ID` — Salesbot launched after the field is updated, which is what actually delivers the message to the customer.
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (default 5432), `DB_NAME` (default `postgres`) — Supabase Postgres for chat history.

## Architecture

### Request Lifecycle (`app.py`)

1. Kommo POSTs `application/x-www-form-urlencoded` to `/webhook/kommo`. `parse_kommo_webhook` flattens the bracketed keys (`message[add][0][...]`) into a dict.
2. Filters reject the request before any LLM work: outgoing messages, system messages (`created_by != 0`), empty text, duplicates within a 5-minute in-memory window (`processed_messages`), and leads whose AI switch custom field is off.
3. Real work runs in a FastAPI `BackgroundTask` so the webhook returns `200 ok` immediately — Kommo retries otherwise.
4. `process_message` saves the user turn, formats the full per-lead history, runs the agent, parses tags, applies side effects, writes the cleaned reply back to Kommo, then launches the Salesbot.

### Agent and Tags (`agent.py`)

- `init_agent()` is called once at startup; the `OpenAI` LLM, LlamaCloud index, and `QueryEngineTool` (`knowledge_base`, `similarity_top_k=5`) are reused across requests. A new `FunctionAgent` is constructed per call because the system prompt is templated with the live conversation history.
- The system prompt instructs the model to append control tags at the end of the reply: `[INTERESADO]`, `[CONTRATO]`, `[MARCA:<product>]`, `[PAGO:<method>]`. `parse_and_clean_tags` is the contract between the agent and the rest of the system — it strips the tags from the user-visible response and returns booleans/values that drive Kommo side effects in `process_message`:
  - `[CONTRATO]` → `move_lead_to_Discusion_de_Contrato` (takes precedence over `[INTERESADO]`).
  - `[INTERESADO]` → `move_lead_to_Toma_de_Decision`.
  - `[MARCA:…]` / `[PAGO:…]` → update the corresponding custom field.

When adding a new tag, update both `SYSTEM_PROMPT_TEMPLATE` and `parse_and_clean_tags`, then wire the side effect in `app.py::process_message`.

### Conversation Memory (`conversation_history.py`)

- A single global `PostgresChatStore` (table `kommo_chat_history`) is initialized at startup. Per-lead memory is realized as `ChatMemoryBuffer(chat_store_key=lead_id, token_limit=3000)` — the lead ID is the partition key.
- The connection string uses `postgresql+asyncpg://` because `PostgresChatStore` requires asyncpg.
- `format_history_for_prompt` renders the buffered messages as `Cliente:` / `Andrea:` lines and is injected into the system prompt; the agent itself is not given LlamaIndex memory directly.

### Kommo Integration (`Kommo Functions/kommo.py`, `tools/`)

The output path is **two-step on purpose** and easy to break:

1. `update_lead_with_response` PATCHes the lead, writing the AI reply into the response custom field and setting the switch field to `true` in the same call.
2. `launch_salesbot` then POSTs to `/api/v2/salesbot/run` (note: v2, not v4). Both 200 and 202 mean success. The Salesbot is what actually sends the message to the customer over WhatsApp/etc — without this call, the response is stored on the lead but never delivered.

The `tools/move_lead_to_*.py` files PATCH `status_id` to advance the pipeline stage; `tools/update_data_*.py` write to product/payment custom fields. Field/stage IDs are environment-specific — use `support_tools/get_custom_fields.py` and `get_pipelines.py` to discover them when porting to a new Kommo account.

### RAG Pipeline (`RAG/rag.py`)

- Knowledge base lives as PDFs in `Base de Conocimiento/` (one per product). `SimpleDirectoryReader` loads them, `SentenceSplitter(512, 50)` and `OpenAIEmbedding(text-embedding-3-small, 1536)` are set globally on `Settings`, and the index is upserted to LlamaCloud.
- `ingest_data()` first attempts `LlamaCloudIndex(name=…)` and `index.insert(...)`; on failure it falls back to `LlamaCloudIndex.from_documents(...)`. The free plan caps you at 5 indexes — a 429 / "maximum number of indexes" message is fatal and means deleting old indexes at https://cloud.llamaindex.ai.
- The embedding model and dimensions used here MUST match what the runtime retrieval (`tools/retrieval.py`) expects; changing one without the other will silently degrade results.

## Conventions

- Logs and prompts are in Spanish; keep that voice when editing user-facing strings or the system prompt.
- `app.py` mutates `sys.path` to import `Kommo Functions/` (folder name has a space) — keep using the existing `from kommo import ...` style rather than restructuring the directory.
- Assistant identity is "Andrea". Products: VitaCalm, CogniBoost, JointFlex, Infusión de Energía Natural — keep these in sync between the system prompt and the PDFs in `Base de Conocimiento/`.
