
import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parent / "zoe.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
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


# Salvar histórico de conversas
def salvar_conversa(mensagem, resposta):
    with conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO conversas (mensagem, resposta)
            VALUES (?, ?)
            """,
            (mensagem, resposta)
        )


# Buscar histórico de conversas
def buscar_historico(limite=10):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            SELECT mensagem, resposta, data_hora
            FROM conversas
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,)
        )

        return [dict(registro) for registro in cursor.fetchall()]


# Salvar memória permanente
def salvar_memoria(informacao):
    with conectar() as conexao:
        conexao.execute(
            """
            INSERT OR IGNORE INTO memorias (informacao)
            VALUES (?)
            """,
            (informacao,)
        )


# Buscar memórias permanentes
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


# Excluir uma memória
def excluir_memoria(memoria_id):
    with conectar() as conexao:
        cursor = conexao.execute(
            "DELETE FROM memorias WHERE id = ?",
            (memoria_id,)
        )

        return cursor.rowcount > 0
