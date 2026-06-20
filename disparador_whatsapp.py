import sqlite3
import re
import time
import random
import pywhatkit

BASE_URL = "https://amelia90.onrender.com"
CAMINHO_CONVITE = r"C:\Projetos\amelia90\uploads\convite.png"

# Quantidade máxima para enviar por execução.
# Para teste, use 1.
# Para envio oficial, sugiro 10 ou 15 por lote.
LIMITE_DE_ENVIO = 1


def conectar():
    return sqlite3.connect("banco/amelia90.db")


def preparar_banco():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("PRAGMA table_info(convidados)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if "whatsapp_enviado" not in colunas:
        cursor.execute(
            "ALTER TABLE convidados ADD COLUMN whatsapp_enviado INTEGER DEFAULT 0"
        )

    conexao.commit()
    conexao.close()


def limpar_telefone(telefone):
    numeros = re.sub(r"\D", "", str(telefone))

    if numeros.startswith("55"):
        return "+" + numeros

    return "+55" + numeros


def buscar_convidados():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, telefone, codigo
        FROM convidados
        WHERE whatsapp_enviado = 0
        ORDER BY nome
        LIMIT ?
    """, (LIMITE_DE_ENVIO,))

    convidados = cursor.fetchall()
    conexao.close()
    return convidados


def marcar_como_enviado(convidado_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE convidados
        SET whatsapp_enviado = 1
        WHERE id = ?
    """, (convidado_id,))

    conexao.commit()
    conexao.close()


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
    preparar_banco()

    convidados = buscar_convidados()

    print(f"Total de convidados neste lote: {len(convidados)}")

    if not convidados:
        print("Nenhum convidado pendente de envio.")
        return

    for convidado_id, nome, telefone, codigo in convidados:
        telefone_formatado = limpar_telefone(telefone)
        mensagem = montar_mensagem(nome, codigo)

        print("----------------------------------------")
        print(f"Enviando para: {nome}")
        print(f"Telefone: {telefone_formatado}")
        print(f"Link: {BASE_URL}/rsvp/{codigo}")

        try:
            pywhatkit.sendwhats_image(
                receiver=telefone_formatado,
                img_path=CAMINHO_CONVITE,
                caption=mensagem,
                wait_time=25,
                tab_close=True,
                close_time=5
            )

            marcar_como_enviado(convidado_id)
            print(f"Enviado e marcado no banco: {nome}")

        except Exception as erro:
            print(f"Erro ao enviar para {nome}: {erro}")
            print("Este convidado NÃO foi marcado como enviado.")

        pausa = random.randint(35, 60)
        print(f"Aguardando {pausa} segundos...")
        time.sleep(pausa)

    print("Lote concluído!")


if __name__ == "__main__":
    enviar_convites()