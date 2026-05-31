import sqlite3
import re
import time
import random
import pywhatkit

BASE_URL = "http://127.0.0.1:5000"
CAMINHO_CONVITE = r"C:\Projetos\amelia90\uploads\convite.png"


def limpar_telefone(telefone):
    numeros = re.sub(r"\D", "", str(telefone))

    if numeros.startswith("55"):
        return "+" + numeros

    return "+55" + numeros


def conectar():
    return sqlite3.connect("banco/amelia90.db")


def buscar_convidados():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT nome, telefone, codigo
        FROM convidados
        ORDER BY nome
    """)

    convidados = cursor.fetchall()
    conexao.close()
    return convidados


def montar_mensagem(nome, codigo):
    link = f"{BASE_URL}/rsvp/{codigo}"

    return f"""Olá, {nome}!

É com muita alegria que convidamos você para a comemoração dos 90 anos da Dona Amélia.

Sua presença será muito especial para nós.

Para confirmar sua presença e informar os nomes dos participantes, acesse o link abaixo:

{link}

Os nomes informados serão encaminhados ao cerimonial para análise e validação.

Aguardamos você!"""


def enviar_convites():
    convidados = buscar_convidados()

    print(f"Total de convidados encontrados: {len(convidados)}")

    for nome, telefone, codigo in convidados:
        telefone_formatado = limpar_telefone(telefone)
        mensagem = montar_mensagem(nome, codigo)

        print(f"Enviando para {nome} - {telefone_formatado}")

        pywhatkit.sendwhats_image(
            receiver=telefone_formatado,
            img_path=CAMINHO_CONVITE,
            caption=mensagem,
            wait_time=20,
            tab_close=True,
            close_time=5
        )

        pausa = random.randint(25, 45)
        print(f"Aguardando {pausa} segundos...")
        time.sleep(pausa)

    print("Disparo concluído!")


if __name__ == "__main__":
    enviar_convites()