import sqlite3
import pandas as pd

BASE_URL = "https://amelia90.onrender.com"


def conectar():
    return sqlite3.connect("banco/amelia90.db")


def montar_mensagem(nome, codigo):
    link = f"{BASE_URL}/rsvp/{codigo}"

    return f"""Olá, {nome}!

É com muita alegria que convidamos você para a comemoração dos 90 anos da Dona Amélia.

Sua presença será muito especial para nós.

Para confirmar sua presença e informar os nomes dos participantes, acesse o link abaixo:

{link}

Os nomes informados serão encaminhados ao cerimonial para análise e validação.

Aguardamos você!"""


conexao = conectar()
cursor = conexao.cursor()

cursor.execute("""
    SELECT nome, telefone, codigo, limite
    FROM convidados
    ORDER BY nome
""")

dados = cursor.fetchall()
conexao.close()

linhas = []

for nome, telefone, codigo, limite in dados:
    link = f"{BASE_URL}/rsvp/{codigo}"

    linhas.append({
        "Nome": nome,
        "Telefone": telefone,
        "Código": codigo,
        "Limite": limite,
        "Link RSVP": link,
        "Mensagem WhatsApp": montar_mensagem(nome, codigo)
    })

df = pd.DataFrame(linhas)

caminho = "exportacoes/disparo_whatsapp.xlsx"
df.to_excel(caminho, index=False)

print("Planilha de disparo gerada com sucesso!")
print(caminho)