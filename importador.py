import pandas as pd
import sqlite3
import random
import string

def gerar_codigo():
    return ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

arquivo = "planilhas/convidados.xlsx"

df = pd.read_excel(arquivo)

conexao = sqlite3.connect(
    "banco/amelia90.db"
)

cursor = conexao.cursor()

for _, linha in df.iterrows():

    codigo = gerar_codigo()

    cursor.execute("""
        INSERT INTO convidados
        (codigo,nome,telefone)
        VALUES (?,?,?)
    """, (
        codigo,
        str(linha["CONTATO"]),
        str(linha["TELEFONE"])
    ))

conexao.commit()
conexao.close()

print("Importação concluída!")