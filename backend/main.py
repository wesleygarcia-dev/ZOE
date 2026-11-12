from fastapi import FastAPI
import requests

app = FastAPI(
    title="ZOE",
    description="Assistente pessoal local",
    version="1.0.0"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "qwen3.5:4b"

@app.get("/")
def inicio():
    return {
        "status": "online",
        "mensagem": "ZOE está funcionando!"
    }

@app.get("/chat")
def conversar(mensagem: str):
    resposta = requests.post(
        OLLAMA_URL,
        json={
            "model": MODELO,
            "prompt": mensagem,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 150
            }
        }
    )

    return {
        "resposta": resposta.json()["response"]
    }