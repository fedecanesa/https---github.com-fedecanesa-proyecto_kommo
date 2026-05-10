# Para generar el entorno virtual
conda create --name LlamaIndex-proj-Kommo python=3.11

# Para activar el entorno virtual
conda activate LlamaIndex-proj-Kommo

# Con este levantamos el endpoint
uvicorn app:app --reload --host 0.0.0.0 --port 8000


# Comando para el forwarding:
ngrok http 8000


Luego copia la API key ubicada en la pestaña "Your Authtoken"
ngrok config add-authtoken TU_TOKEN_AQUI









(LlamaIndex-proj-Kommo) kevininofuente@MacBook-Pro-de-Kevin Projecto_kommo % pip show llama-cloud-services
Name: llama-cloud-services
Version: 0.6.54
Summary: Tailored SDK clients for LlamaCloud services.
Home-page: 
Author: 
Author-email: Logan Markewich <logan@runllama.ai>
License-Expression: MIT
Location: /opt/anaconda3/envs/LlamaIndex-proj-Kommo/lib/python3.11/site-packages
Requires: click, llama-cloud, llama-index-core, platformdirs, pydantic, python-dotenv, tenacity
Required-by: llama-parse