from fastapi import FastAPI
import requests

app = FastAPI(
    title="ZOE",
    description="Assistente pessoal local",
    version="1.0.0"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "qwen2.5:1.5b"

@app.get("/")
def inicio():
    return {
        "status": "online",
        "nome": "ZOE",
        "versao": "1.1.0",
        "modelo": MODELO,
        "mensagem": "ZOE está funcionando corretamente!"
    }

@app.get("/chat")
def conversar(mensagem: str):
    resposta = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": MODELO,
            "messages": [
                {
                    "role": "user",
                    "content": mensagem
                }
            ],
            "think": False,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 150
            }
        }
    )

    dados = resposta.json()

    return {
        "resposta": dados["message"]["content"]
    }