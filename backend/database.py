
import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parent / "zoe.db"


def conectar():
    conexao = sqlite3.connect(
        CAMINHO_BANCO,
        timeout=10
    )

    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA busy_timeout = 10000")

    return conexao


# Criação das tabelas
def criar_tabelas():
    with conectar() as conexao:

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS conversas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mensagem TEXT NOT NULL,
                resposta TEXT NOT NULL,
                data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS memorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                informacao TEXT NOT NULL UNIQUE,
                data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Salvar conversa
def salvar_conversa(mensagem, resposta):
    with conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO conversas (mensagem, resposta)
            VALUES (?, ?)
            """,
            (mensagem, resposta)
        )


# Buscar histórico
def buscar_historico(limite=10):
    limite = max(1, min(int(limite), 100))

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            SELECT id, mensagem, resposta, data_hora
            FROM conversas
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,)
        )

        return [dict(registro) for registro in cursor.fetchall()]


# Salvar memória
def salvar_memoria(informacao):
    informacao = informacao.strip()

    if not informacao:
        return False

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT OR IGNORE INTO memorias (informacao)
            VALUES (?)
            """,
            (informacao,)
        )

        return cursor.rowcount > 0


# Buscar memórias
def buscar_memorias():
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            SELECT id, informacao, data_hora
            FROM memorias
            ORDER BY id DESC
            """
        )

        return [dict(registro) for registro in cursor.fetchall()]


# Atualizar memória
def atualizar_memoria(memoria_id, informacao):
    informacao = informacao.strip()

    if not informacao:
        return False

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE memorias
            SET informacao = ?
            WHERE id = ?
            """,
            (informacao, memoria_id)
        )

        return cursor.rowcount > 0


# Excluir memória
def excluir_memoria(memoria_id):
    with conectar() as conexao:
        cursor = conexao.execute(
            "DELETE FROM memorias WHERE id = ?",
            (memoria_id,)
        )

        return cursor.rowcount > 0
