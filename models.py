import sqlite3


def criar_banco():

    conexao = sqlite3.connect("banco/amelia90.db")
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS convidados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        nome TEXT,
        telefone TEXT,
        limite INTEGER DEFAULT 1,
        respondeu INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS confirmacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        convidado_id INTEGER,
        observacoes TEXT,
        data_confirmacao DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        confirmacao_id INTEGER,
        nome TEXT,
        tipo TEXT,
        idade INTEGER
    )
    """)

    cursor.execute("PRAGMA table_info(convidados)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if "limite" not in colunas:
        cursor.execute(
            "ALTER TABLE convidados ADD COLUMN limite INTEGER DEFAULT 1"
        )

    if "respondeu" not in colunas:
        cursor.execute(
            "ALTER TABLE convidados ADD COLUMN respondeu INTEGER DEFAULT 0"
        )

    conexao.commit()
    conexao.close()


if __name__ == "__main__":
    criar_banco()
    print("Banco criado com sucesso!")