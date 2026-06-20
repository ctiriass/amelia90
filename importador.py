import pandas as pd
import random
import string
import requests

SUPABASE_URL = "https://oqfokoxdnwvfbkvzeqew.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9xZm9rb3hkbnd2ZmJrdnplcWV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MDc5NDEsImV4cCI6MjA5NjE4Mzk0MX0.JuC0RPkYZlUJM7itCVOAQCV_-XFv2v2ZkOVqeMe3Q-c"

arquivo = "planilhas/convidados.xlsx"


def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


def gerar_codigo():
    return ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )


def supabase_get(tabela, query=""):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}{query}"
    r = requests.get(url, headers=headers())
    r.raise_for_status()
    return r.json()


def supabase_post(tabela, dados):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"
    r = requests.post(url, headers=headers(), json=dados)
    r.raise_for_status()
    return r.json()


def supabase_delete(tabela, filtro):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}{filtro}"
    r = requests.delete(url, headers=headers())
    r.raise_for_status()


def limpar_tudo():
    # A ordem é importante: primeiro filhos, depois pais
    supabase_delete("participantes", "?id=gte.0")
    supabase_delete("confirmacoes", "?id=gte.0")
    supabase_delete("convidados", "?id=gte.0")


def preparar_convidados():
    df = pd.read_excel(arquivo)

    convidados = []

    for _, linha in df.iterrows():

        nome = str(linha["CONTATO"]).strip()
        telefone = str(linha["TELEFONE"]).strip()

        try:
            limite = int(linha["LIMITE"])
        except:
            limite = 1

        if not nome or nome.lower() == "nan":
            continue

        convidados.append({
            "codigo": gerar_codigo(),
            "nome": nome,
            "telefone": telefone,
            "limite": limite,
            "respondeu": False,
            "whatsapp_enviado": False
        })

    return convidados


def importar_substituindo_tudo():
    print("Limpando lista anterior...")
    limpar_tudo()

    convidados = preparar_convidados()

    if convidados:
        supabase_post("convidados", convidados)

    print("Importação concluída!")
    print("A lista anterior foi apagada e substituída pela nova planilha.")
    print(f"Total importado: {len(convidados)}")


def adicionar_nova_lista():
    convidados = preparar_convidados()

    if convidados:
        supabase_post("convidados", convidados)

    print("Importação concluída!")
    print("A nova lista foi adicionada sem apagar os convidados anteriores.")
    print(f"Total adicionado: {len(convidados)}")


print("Escolha uma opção:")
print("1 - Substituir tudo")
print("2 - Adicionar nova lista sem apagar a anterior")

opcao = input("Digite 1 ou 2: ").strip()

if opcao == "1":
    confirmar = input(
        "ATENÇÃO: isso apagará convidados, confirmações e participantes. Digite SIM para confirmar: "
    ).strip().upper()

    if confirmar == "SIM":
        importar_substituindo_tudo()
    else:
        print("Operação cancelada.")

elif opcao == "2":
    adicionar_nova_lista()

else:
    print("Opção inválida.")