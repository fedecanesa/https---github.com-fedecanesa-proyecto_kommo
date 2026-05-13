import re
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from tools.retrieval import get_index, get_retrieval_tool

INTEREST_TAG = "[INTERESADO]"
CONTRACT_TAG = "[CONTRATO]"
CLOSED_TAG = "[CERRADO]"
MARCA_PATTERN = re.compile(r"\[MARCA:(.+?)\]")
PAGO_PATTERN = re.compile(r"\[PAGO:(.+?)\]")

SYSTEM_PROMPT_TEMPLATE = """Eres Andrea, Vendedora Digital de productos de mejora cognitiva y corporal.
Tu objetivo es ayudar a los clientes con información sobre los productos.

Productos disponibles: VitaCalm, CogniBoost, JointFlex, Infusión de Energía Natural.

SIEMPRE usa la herramienta knowledge_base antes de responder para obtener información precisa de los productos.

Historial de la conversación con este cliente:
{history_str}

INSTRUCCIONES:
- Responde de forma amable, concisa y profesional.
- Usa el historial para mantener continuidad en la conversación. NO te presentes ni saludes
  de nuevo si ya lo hiciste antes en el historial.
- Si no tienes información específica, indica que puedes conectar al cliente con un asesor humano.
- Si el usuario o cliente dice que va a pagar por transferencia, indica que el pago se realizará en la cuenta de la empresa, la cual es: 0000-0000-0000-0000-0000.

ETIQUETAS (agrega al FINAL de tu respuesta las que apliquen):

1. [INTERESADO] → El cliente muestra intención clara de compra: quiere comprar, pide precio
   para adquirir, dice "lo quiero", "me interesa comprarlo", etc.
   Solo cuando hay intención REAL de compra, no por preguntas informativas.

2. [CONTRATO] → El cliente ya quiere avanzar con la compra y pregunta sobre: formas de pago,
   financiamiento, métodos de envío, lugar de recogida, plazos de entrega, garantías,
   condiciones del contrato, o cualquier detalle logístico/contractual de la transacción.

3. [CERRADO] → El cliente confirma explícitamente que quiere cerrar la compra: dice "sí, lo compro",
   "quiero proceder", "confirmado", "adelante con el pedido", etc.
   Solo cuando hay confirmación REAL de compra, no por intención previa.

4. [MARCA:nombre_del_producto] → Cuando el cliente mencione o pregunte por un producto
   específico con interés de compra, agrega esta etiqueta con el nombre exacto del producto.
   Ejemplo: [MARCA:VitaCalm], [MARCA:CogniBoost], [MARCA:JointFlex]

5. [PAGO:método] → Cuando el cliente indique cómo quiere pagar o pregunte por un método
   de pago concreto, agrega esta etiqueta con el método mencionado.
   Ejemplo: [PAGO:tarjeta de crédito], [PAGO:transferencia], [PAGO:efectivo]

Si no aplica ninguna etiqueta, NO agregues ninguna. Puedes agregar varias etiquetas a la vez."""


def init_agent():
    """Inicializa el LLM, índice y retrieval tool al arrancar."""
    print("🔗 Conectando con LlamaCloud...")
    llm = OpenAI(model="gpt-4.1", temperature=0)
    index = get_index()
    retrieval_tool = get_retrieval_tool(index, llm)
    print("✅ Índice cargado exitosamente.")
    return llm, retrieval_tool


async def ask_agent(llm, retrieval_tool, message_text: str, history_str: str) -> str:
    """Ejecuta el agente con el mensaje del cliente y devuelve la respuesta."""
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(history_str=history_str)

    agent = FunctionAgent(
        tools=[retrieval_tool],
        llm=llm,
        system_prompt=system_prompt,
    )

    response = await agent.run(user_msg=message_text)
    return str(response)


def parse_and_clean_tags(response_text: str) -> dict:
    """Extrae los tags de la respuesta de IA y devuelve la respuesta limpia + datos extraídos."""
    is_closed = CLOSED_TAG in response_text
    is_contract = CONTRACT_TAG in response_text
    is_interested = INTEREST_TAG in response_text

    marca_match = MARCA_PATTERN.search(response_text)
    pago_match = PAGO_PATTERN.search(response_text)

    marca = marca_match.group(1).strip() if marca_match else None
    pago = pago_match.group(1).strip() if pago_match else None

    clean = response_text
    clean = clean.replace(CLOSED_TAG, "")
    clean = clean.replace(CONTRACT_TAG, "")
    clean = clean.replace(INTEREST_TAG, "")
    clean = MARCA_PATTERN.sub("", clean)
    clean = PAGO_PATTERN.sub("", clean)
    clean = clean.strip()

    return {
        "clean_response": clean,
        "is_closed": is_closed,
        "is_interested": is_interested,
        "is_contract": is_contract,
        "marca": marca,
        "pago": pago,
    }
