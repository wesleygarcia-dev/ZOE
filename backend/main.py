
import json
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from database import (
    criar_tabelas,
    salvar_conversa,
    buscar_historico,
    salvar_memoria,
    buscar_memorias,
    atualizar_memoria,
    excluir_memoria
)


# ==========================================
# CONFIGURAÇÕES
# ==========================================

app = FastAPI(
    title="ZOE",
    description="Assistente pessoal local",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

MODELO = "qwen3.5:4b"

TEMPO_CARREGADO = "10m"
LIMITE_HISTORICO = 6
LIMITE_RESPOSTA = 256


# ==========================================
# MODELOS DE DADOS
# ==========================================

class ChatRequest(BaseModel):
    mensagem: str = Field(min_length=1, max_length=10000)


class MemoriaRequest(BaseModel):
    informacao: str = Field(min_length=1, max_length=2000)


# ==========================================
# INICIALIZAÇÃO
# ==========================================

@app.on_event("startup")
def iniciar_banco():
    criar_tabelas()


@app.get("/")
def inicio():
    return {
        "status": "online",
        "nome": "ZOE",
        "versao": "2.0.0",
        "modelo": MODELO,
        "mensagem": "ZOE está funcionando!"
    }


# ==========================================
# CONSTRUÇÃO DO CONTEXTO
# ==========================================

def construir_mensagens(mensagem):

    historico = buscar_historico(
        limite=LIMITE_HISTORICO
    )

    memorias = buscar_memorias()

    contexto_memorias = "\n".join(
        memoria["informacao"]
        for memoria in memorias
    )

    # Evita enviar um volume excessivo de memórias
    contexto_memorias = contexto_memorias[:4000]

    sistema = (
        "Seu nome é ZOE. Você é uma assistente pessoal "
        "de inteligência artificial executada localmente. "

        "Responda sempre em português brasileiro. "

        "Seja inteligente, objetiva, natural e direta. "

        "Entenda o contexto antes de responder. "

        "Não invente informações. "

        "Para perguntas simples, responda brevemente. "

        "Explique detalhadamente quando necessário "
        "ou quando o usuário solicitar. "

        "Não repita informações sem necessidade. "

        "Não apresente raciocínio interno. "
        "Apresente diretamente suas conclusões. "

        "\n\nMEMÓRIAS PERMANENTES:\n"

        + (
            contexto_memorias
            if contexto_memorias
            else "Nenhuma memória registrada."
        )
    )

    mensagens = [
        {
            "role": "system",
            "content": sistema
        }
    ]

    # Histórico em ordem cronológica
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

    return mensagens


# ==========================================
# COMANDOS DE MEMÓRIA
# ==========================================

def processar_comando_memoria(mensagem):

    texto = mensagem.strip()
    texto_lower = texto.casefold()

    prefixos = [
        "lembre-se de que ",
        "lembre-se que ",
        "lembre que ",
        "guarde que ",
        "anote que ",
        "salve que "
    ]

    for prefixo in prefixos:

        if texto_lower.startswith(prefixo):

            informacao = texto[len(prefixo):].strip()

            if not informacao:
                return "Qual informação devo guardar?"

            salvar_memoria(informacao)

            return (
                "Entendido! Vou guardar esta informação: "
                f"{informacao}"
            )

    consultas = [
        "o que você lembra sobre mim?",
        "o que voce lembra sobre mim?",
        "o que você sabe sobre mim?",
        "o que voce sabe sobre mim?"
    ]

    if texto_lower in consultas:

        memorias = buscar_memorias()

        if not memorias:
            return "Ainda não tenho memórias permanentes registradas."

        resultado = "Estas são as informações que tenho guardadas:\n"

        for memoria in memorias:
            resultado += (
                f"\n{memoria['id']}. "
                f"{memoria['informacao']}"
            )

        return resultado

    if (
        texto_lower.startswith("esqueça a memória ")
        or texto_lower.startswith("esqueca a memoria ")
    ):

        try:
            memoria_id = int(texto.rsplit(" ", 1)[1])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Informe um número válido de memória."
            )

        removida = excluir_memoria(memoria_id)

        if removida:
            return f"Memória {memoria_id} excluída com sucesso."

        return f"Não encontrei a memória {memoria_id}."

    return None


# ==========================================
# CONFIGURAÇÃO DO OLLAMA
# ==========================================

def configuracao_ollama(mensagens, stream=False):

    return {
        "model": MODELO,
        "messages": mensagens,
        "stream": stream,
        "think": False,
        "keep_alive": TEMPO_CARREGADO,
        "options": {
            "temperature": 0.6,
            "num_predict": LIMITE_RESPOSTA,
            "num_ctx": 4096
        }
    }


# ==========================================
# CHAT TRADICIONAL
# ==========================================

def gerar_resposta(mensagem):

    mensagem = mensagem.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="A mensagem não pode estar vazia."
        )

    comando = processar_comando_memoria(mensagem)

    if comando is not None:

        salvar_conversa(mensagem, comando)

        return comando

    mensagens = construir_mensagens(mensagem)

    try:

        resposta = requests.post(
            OLLAMA_URL,
            json=configuracao_ollama(mensagens),
            timeout=(10, 180)
        )

        resposta.raise_for_status()

        dados = resposta.json()

        texto = dados["message"]["content"].strip()

        salvar_conversa(mensagem, texto)

        return texto

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


@app.get("/chat")
def conversar(mensagem: str):

    return {
        "resposta": gerar_resposta(mensagem)
    }


@app.post("/chat")
def conversar_post(dados: ChatRequest):

    return {
        "resposta": gerar_resposta(dados.mensagem)
    }


# ==========================================
# CHAT COM STREAMING
# ==========================================

@app.post("/chat/stream")
def conversar_stream(dados: ChatRequest):

    mensagem = dados.mensagem.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="A mensagem não pode estar vazia."
        )

    comando = processar_comando_memoria(mensagem)

    if comando is not None:

        salvar_conversa(mensagem, comando)

        def resposta_comando():

            evento = {
                "type": "token",
                "content": comando
            }

            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"

            yield 'data: {"type":"done"}\n\n'

        return StreamingResponse(
            resposta_comando(),
            media_type="text/event-stream"
        )

    mensagens = construir_mensagens(mensagem)

    def gerar_eventos():

        texto_completo = ""

        try:

            with requests.post(
                OLLAMA_URL,
                json=configuracao_ollama(
                    mensagens,
                    stream=True
                ),
                stream=True,
                timeout=(10, 300)
            ) as resposta:

                resposta.raise_for_status()

                for linha in resposta.iter_lines():

                    if not linha:
                        continue

                    dados = json.loads(linha)

                    if dados.get("error"):
                        raise RuntimeError(dados["error"])

                    conteudo = (
                        dados.get("message", {}).get("content", "")
                    )

                    if conteudo:

                        texto_completo += conteudo

                        evento = {
                            "type": "token",
                            "content": conteudo
                        }

                        yield (
                            "data: "
                            + json.dumps(
                                evento,
                                ensure_ascii=False
                            )
                            + "\n\n"
                        )

                    if dados.get("done"):
                        break

            if texto_completo.strip():

                salvar_conversa(
                    mensagem,
                    texto_completo.strip()
                )

            yield 'data: {"type":"done"}\n\n'

        except Exception as erro:

            evento = {
                "type": "error",
                "message": str(erro)
            }

            yield (
                "data: "
                + json.dumps(
                    evento,
                    ensure_ascii=False
                )
                + "\n\n"
            )

    return StreamingResponse(
        gerar_eventos(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ==========================================
# HISTÓRICO
# ==========================================

@app.get("/historico")
def consultar_historico():

    return {
        "conversas": buscar_historico(limite=50)
    }


# ==========================================
# MEMÓRIAS
# ==========================================

@app.get("/memorias")
def consultar_memorias():

    return {
        "memorias": buscar_memorias()
    }


@app.put("/memorias/{memoria_id}")
def atualizar_memoria_api(
    memoria_id: int,
    dados: MemoriaRequest
):

    atualizada = atualizar_memoria(
        memoria_id,
        dados.informacao
    )

    if not atualizada:

        raise HTTPException(
            status_code=404,
            detail="Memória não encontrada."
        )

    return {
        "mensagem": "Memória atualizada com sucesso."
    }


@app.delete("/memorias/{memoria_id}")
def excluir_memoria_api(memoria_id: int):

    removida = excluir_memoria(memoria_id)

    if not removida:

        raise HTTPException(
            status_code=404,
            detail="Memória não encontrada."
        )

    return {
        "mensagem": "Memória excluída com sucesso."
    }


# ==========================================
# VERIFICAR O OLLAMA
# ==========================================

@app.get("/ollama/status")
def status_ollama():

    try:

        resposta = requests.get(
            OLLAMA_TAGS_URL,
            timeout=5
        )

        resposta.raise_for_status()

        modelos = resposta.json().get("models", [])

        disponivel = any(
            modelo.get("name", "").split(":")[0]
            == MODELO.split(":")[0]
            and modelo.get("name", "") == MODELO
            for modelo in modelos
        )

        return {
            "ollama": "online",
            "modelo": MODELO,
            "modelo_disponivel": disponivel
        }

    except requests.exceptions.RequestException as erro:

        raise HTTPException(
            status_code=503,
            detail=f"Ollama indisponível: {str(erro)}"
        )
