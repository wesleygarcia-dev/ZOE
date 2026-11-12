
from fastapi import FastAPI, HTTPException
import requests

from database import (
    criar_tabelas,
    salvar_conversa,
    buscar_historico,
    salvar_memoria,
    buscar_memorias,
    excluir_memoria
)

app = FastAPI(
    title="ZOE",
    description="Assistente pessoal local",
    version="1.3.0"
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen2.5:1.5b"


# Inicialização do banco
@app.on_event("startup")
def iniciar_banco():
    criar_tabelas()


# Página inicial
@app.get("/")
def inicio():
    return {
        "status": "online",
        "nome": "ZOE",
        "versao": "1.3.0",
        "modelo": MODELO,
        "mensagem": "ZOE está funcionando corretamente!"
    }


# Sistema principal de conversação
@app.get("/chat")
def conversar(mensagem: str):

    mensagem = mensagem.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="A mensagem não pode estar vazia."
        )

    mensagem_lower = mensagem.lower()

    # COMANDO: salvar memória
    prefixos_memoria = [
        "lembre-se de que ",
        "lembre-se que ",
        "guarde que "
    ]

    for prefixo in prefixos_memoria:
        if mensagem_lower.startswith(prefixo):

            informacao = mensagem[len(prefixo):].strip()

            if not informacao:
                return {"resposta": "Qual informação devo guardar?"}

            salvar_memoria(informacao)

            texto = f"Entendido! Vou guardar esta informação: {informacao}"

            salvar_conversa(mensagem, texto)

            return {"resposta": texto}

    # COMANDO: consultar memórias
    if mensagem_lower in [
        "o que você lembra sobre mim?",
        "o que voce lembra sobre mim?",
        "o que você sabe sobre mim?",
        "o que voce sabe sobre mim?"
    ]:

        memorias = buscar_memorias()

        if not memorias:
            texto = "Ainda não tenho memórias permanentes registradas."

        else:
            texto = "Estas são as informações que tenho guardadas:\n"

            for memoria in memorias:
                texto += (
                    f"\n{memoria['id']}. "
                    f"{memoria['informacao']}"
                )

        salvar_conversa(mensagem, texto)

        return {"resposta": texto}

    # COMANDO: esquecer uma memória pelo ID
    if mensagem_lower.startswith("esqueça a memória ") or mensagem_lower.startswith("esqueca a memoria "):

        try:
            memoria_id = int(mensagem_lower.rsplit(" ", 1)[1])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Informe um número válido de memória."
            )

        removida = excluir_memoria(memoria_id)

        if removida:
            texto = f"Memória {memoria_id} excluída com sucesso."
        else:
            texto = f"Não encontrei a memória {memoria_id}."

        salvar_conversa(mensagem, texto)

        return {"resposta": texto}

    # Recuperar contexto
    historico = buscar_historico(limite=10)
    memorias = buscar_memorias()

    contexto_memorias = "\n".join(
        memoria["informacao"] for memoria in memorias
    )

    mensagens = [
        {
            "role": "system",
            "content": (
                "Seu nome é ZOE. Você é uma assistente pessoal "
                "de inteligência artificial. "
                "Responda sempre em português brasileiro. "
                "Seja objetiva, inteligente, educada e natural. "
                "Entenda o contexto antes de responder. "
                "Não invente informações. "
                "Utilize o histórico para manter a continuidade "
                "das conversas.\n\n"
                "MEMÓRIAS PERMANENTES DO USUÁRIO:\n"
                f"{contexto_memorias if contexto_memorias else 'Nenhuma memória registrada.'}"
            )
        }
    ]

    # Adicionar histórico em ordem cronológica
    for conversa in reversed(historico):
        mensagens.append({
            "role": "user",
            "content": conversa["mensagem"]
        })

        mensagens.append({
            "role": "assistant",
            "content": conversa["resposta"]
        })

    mensagens.append({
        "role": "user",
        "content": mensagem
    })

    try:
        resposta = requests.post(
            OLLAMA_URL,
            json={
                "model": MODELO,
                "messages": mensagens,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 200
                }
            },
            timeout=120
        )

        resposta.raise_for_status()

        dados = resposta.json()
        texto_resposta = dados["message"]["content"]

        salvar_conversa(mensagem, texto_resposta)

        return {"resposta": texto_resposta}

    except requests.exceptions.RequestException as erro:
        raise HTTPException(
            status_code=503,
            detail=f"Erro ao comunicar com o Ollama: {str(erro)}"
        )

    except (KeyError, ValueError) as erro:
        raise HTTPException(
            status_code=502,
            detail=f"Resposta inválida do modelo: {str(erro)}"
        )


# Consultar histórico
@app.get("/historico")
def consultar_historico():
    return {
        "conversas": buscar_historico(limite=50)
    }


# Consultar memórias permanentes
@app.get("/memorias")
def consultar_memorias():
    return {
        "memorias": buscar_memorias()
    }
