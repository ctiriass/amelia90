from flask import Flask, send_from_directory, send_file, request
import sqlite3
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment

app = Flask(__name__)

MAPS_LINK = "https://maps.app.goo.gl/T3QYpdr4MEtbXsJ96"
ADMIN_SECRET = "8F4K2X9P7Q"


def conectar():
    return sqlite3.connect("banco/amelia90.db")


@app.route("/")
def home():
    return """
    <h1>90 Anos da Amélia</h1>
    <p>Sistema RSVP funcionando!</p>
    <p><a href="/admin/convidados">Ver convidados importados</a></p>
    """


@app.route("/uploads/<nome_arquivo>")
def uploads(nome_arquivo):
    return send_from_directory("uploads", nome_arquivo)


@app.route("/admin/convidados")
def listar_convidados():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, telefone, respondeu
        FROM convidados
        ORDER BY nome
    """)

    convidados = cursor.fetchall()
    conexao.close()

    html = """
    <h1>Convidados Importados</h1>
    <table border="1" cellpadding="8">
        <tr>
            <th>ID</th>
            <th>Código</th>
            <th>Nome</th>
            <th>Telefone</th>
            <th>Link RSVP</th>
        </tr>
    """

    for id_, codigo, nome, telefone, respondeu in convidados:
        link = f"https://amelia90.onrender.com/rsvp/{codigo}"
        html += f"""
        <tr>
            <td>{id_}</td>
            <td>{codigo}</td>
            <td>{nome}</td>
            <td>{telefone}</td>
            <td><a href="{link}" target="_blank">{link}</a></td>
        </tr>
        """

    html += "</table>"
    return html


@app.route("/rsvp/<codigo>")
def rsvp(codigo):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, respondeu
        FROM convidados
        WHERE codigo = ?
    """, (codigo,))

    convidado = cursor.fetchone()
    conexao.close()

    if not convidado:
        return "<h1>Convite não encontrado.</h1>"

    id_, nome, respondeu = convidado

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>90 Anos da Amélia</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #fff4ec;
                color: #3b1f14;
                text-align: center;
            }}
            .container {{
                max-width: 720px;
                margin: 0 auto;
                padding: 20px;
            }}
            .convite {{
                width: 100%;
                max-width: 600px;
                border-radius: 16px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.18);
                margin-bottom: 24px;
            }}
            .card {{
                background: #ffffff;
                border-radius: 18px;
                padding: 24px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.12);
                margin-bottom: 24px;
            }}
            h1 {{
                color: #7a3b22;
            }}
            p {{
                font-size: 18px;
                line-height: 1.5;
            }}
            .botao {{
                display: inline-block;
                background: #c46b4f;
                color: white;
                text-decoration: none;
                padding: 14px 22px;
                border-radius: 12px;
                font-weight: bold;
                margin: 8px;
            }}
            .botao-secundario {{
                background: #8a5a44;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="/uploads/convite.png" class="convite" alt="Convite 90 anos da Amélia">

            <div class="card">
                <h1>Olá, {nome}!</h1>

                <p>
                    Ficamos muito felizes em convidar você para a comemoração dos
                    <strong>90 anos da Dona Amélia</strong>.
                </p>

                <p>
                    Para confirmar sua presença, clique no botão abaixo e informe
                    os nomes completos das pessoas que participarão.
                </p>

                <a class="botao" href="/rsvp/{codigo}/confirmar">
                    Confirmar Presença
                </a>

                <a class="botao botao-secundario" href="{MAPS_LINK}" target="_blank">
                    📍 Como Chegar
                </a>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/rsvp/<codigo>/confirmar", methods=["GET", "POST"])
def confirmar(codigo):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, respondeu
        FROM convidados
        WHERE codigo = ?
    """, (codigo,))

    convidado = cursor.fetchone()

    if not convidado:
        conexao.close()
        return "<h1>Convite não encontrado.</h1>"

    convidado_id, nome_convidado, respondeu = convidado

    if respondeu == 1:
        conexao.close()
        return """
        <h1>Confirmação já registrada</h1>
        <p>Sua solicitação já foi registrada anteriormente.</p>
        <p>
        Caso necessite de alguma alteração, entre em contato diretamente
        com a organização do evento.
        </p>
        """

    if request.method == "POST":
        observacoes = request.form.get("observacoes", "")

        cursor.execute("""
            INSERT INTO confirmacoes
            (convidado_id, observacoes)
            VALUES (?, ?)
        """, (convidado_id, observacoes))

        confirmacao_id = cursor.lastrowid

        nomes = request.form.getlist("nome[]")
        tipos = request.form.getlist("tipo[]")
        idades = request.form.getlist("idade[]")

        for nome, tipo, idade in zip(nomes, tipos, idades):
            nome = nome.strip()

            if not nome:
                continue

            idade_final = None

            if tipo == "Crianca" and idade:
                idade_final = int(idade)

            cursor.execute("""
                INSERT INTO participantes
                (confirmacao_id, nome, tipo, idade)
                VALUES (?, ?, ?, ?)
            """, (confirmacao_id, nome, tipo, idade_final))

        cursor.execute("""
            UPDATE convidados
            SET respondeu = 1
            WHERE id = ?
        """, (convidado_id,))

        conexao.commit()
        conexao.close()

        return """
        <h1>Solicitação recebida com sucesso!</h1>
        <p>
        Agradecemos seu interesse em participar da comemoração dos
        90 anos da Dona Amélia.
        </p>
        <p>
        Os nomes informados foram encaminhados ao cerimonial e serão analisados
        conforme a organização do evento.
        </p>
        <p>
        Após a validação, entraremos em contato para informar os nomes
        efetivamente confirmados.
        </p>
        """

    conexao.close()

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirmar Presença</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #fff4ec;
                color: #3b1f14;
                max-width: 900px;
                margin: auto;
                padding: 20px;
            }}
            .card {{
                background: white;
                padding: 24px;
                border-radius: 18px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            }}
            .participante {{
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 12px;
                border-radius: 10px;
                background: #fffaf7;
            }}
            input, select, textarea {{
                width: 100%;
                padding: 10px;
                margin-top: 5px;
                margin-bottom: 12px;
                box-sizing: border-box;
            }}
            button {{
                background: #c46b4f;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 10px;
                cursor: pointer;
                font-weight: bold;
            }}
            .secundario {{
                background: #8a5a44;
            }}
        </style>

        <script>
            function adicionarParticipante() {{
                let container = document.getElementById("participantes");
                let bloco = document.createElement("div");
                bloco.className = "participante";

                bloco.innerHTML = `
                    <label>Nome Completo</label>
                    <input type="text" name="nome[]" required>

                    <label>Tipo</label>
                    <select name="tipo[]">
                        <option value="Adulto">Adulto</option>
                        <option value="Crianca">Criança</option>
                    </select>

                    <label>Idade (somente criança)</label>
                    <input type="number" name="idade[]" min="0">
                `;

                container.appendChild(bloco);
            }}
        </script>
    </head>

    <body>
        <div class="card">
            <h1>Participantes da Família</h1>

            <p>
                Convite vinculado a:
                <strong>{nome_convidado}</strong>
            </p>

            <form method="POST">
                <div id="participantes">
                    <div class="participante">
                        <label>Nome Completo</label>
                        <input type="text" name="nome[]" required>

                        <label>Tipo</label>
                        <select name="tipo[]">
                            <option value="Adulto">Adulto</option>
                            <option value="Crianca">Criança</option>
                        </select>

                        <label>Idade (somente criança)</label>
                        <input type="number" name="idade[]" min="0">
                    </div>
                </div>

                <button type="button" class="secundario" onclick="adicionarParticipante()">
                    ➕ Adicionar Participante
                </button>

                <br><br>

                <label>Observações</label>
                <textarea name="observacoes" rows="5"></textarea>

                <br><br>

                <button type="submit">
                    ENVIAR SOLICITAÇÃO
                </button>
            </form>
        </div>
    </body>
    </html>
    """


@app.route("/admin/<segredo>")
def admin(segredo):
    if segredo != ADMIN_SECRET:
        return "<h1>Acesso negado.</h1>"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT 
            c.id,
            c.nome,
            c.telefone,
            c.codigo,
            c.respondeu,
            COUNT(p.id) as total_participantes
        FROM convidados c
        LEFT JOIN confirmacoes cf ON cf.convidado_id = c.id
        LEFT JOIN participantes p ON p.confirmacao_id = cf.id
        GROUP BY c.id
        ORDER BY c.nome
    """)

    registros = cursor.fetchall()
    conexao.close()

    html = f"""
    <h1>Painel Administrativo - 90 Anos da Amélia</h1>

    <p>
        <a href="/admin/{segredo}/exportar">
            Exportar Lista para Excel
        </a>
    </p>

    <table border="1" cellpadding="8">
        <tr>
            <th>Convidado</th>
            <th>Telefone</th>
            <th>Respondeu?</th>
            <th>Participantes</th>
            <th>Detalhes</th>
        </tr>
    """

    for id_, nome, telefone, codigo, respondeu, total in registros:
        status = "Sim" if respondeu else "Não"

        html += f"""
        <tr>
            <td>{nome}</td>
            <td>{telefone}</td>
            <td>{status}</td>
            <td>{total}</td>
            <td>
                <a href="/admin/{segredo}/convidado/{id_}">
                    Ver detalhes
                </a>
            </td>
        </tr>
        """

    html += "</table>"
    return html


@app.route("/admin/<segredo>/convidado/<int:convidado_id>")
def detalhes_convidado(segredo, convidado_id):
    if segredo != ADMIN_SECRET:
        return "<h1>Acesso negado.</h1>"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT nome, telefone
        FROM convidados
        WHERE id = ?
    """, (convidado_id,))

    convidado = cursor.fetchone()

    cursor.execute("""
        SELECT id, observacoes, data_confirmacao
        FROM confirmacoes
        WHERE convidado_id = ?
        ORDER BY id DESC
    """, (convidado_id,))

    confirmacao = cursor.fetchone()

    if not confirmacao:
        conexao.close()
        return "<h1>Este convidado ainda não respondeu.</h1>"

    confirmacao_id, observacoes, data = confirmacao

    cursor.execute("""
        SELECT nome, tipo, idade
        FROM participantes
        WHERE confirmacao_id = ?
        ORDER BY id
    """, (confirmacao_id,))

    participantes = cursor.fetchall()
    conexao.close()

    html = f"""
    <h1>Detalhes da Confirmação</h1>

    <p><strong>Convidado:</strong> {convidado[0]}</p>
    <p><strong>Telefone:</strong> {convidado[1]}</p>
    <p><strong>Data:</strong> {data}</p>

    <h2>Participantes informados</h2>
    <ul>
    """

    for nome, tipo, idade in participantes:
        if tipo == "Crianca" and idade:
            html += f"<li>{nome} - Criança, {idade} anos</li>"
        else:
            html += f"<li>{nome} - Adulto</li>"

    html += f"""
    </ul>

    <h2>Observações</h2>
    <p>{observacoes or "Nenhuma observação."}</p>

    <p>
        <a href="/admin/{segredo}">Voltar ao painel</a>
    </p>
    """

    return html


@app.route("/admin/<segredo>/exportar")
def exportar_excel(segredo):
    if segredo != ADMIN_SECRET:
        return "<h1>Acesso negado.</h1>"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT 
            c.nome as convidado,
            p.nome as participante,
            p.tipo,
            p.idade,
            cf.data_confirmacao
        FROM participantes p
        INNER JOIN confirmacoes cf ON cf.id = p.confirmacao_id
        INNER JOIN convidados c ON c.id = cf.convidado_id
        ORDER BY p.nome
    """)

    dados = cursor.fetchall()
    conexao.close()

    lista_completa = []
    criancas = []

    for convidado, participante, tipo, idade, data in dados:
        lista_completa.append({
            "Nome": participante,
            "Tipo": tipo,
            "Idade": idade if idade else "",
            "Convidado de origem": convidado,
            "Data da confirmação": data
        })

        if tipo == "Crianca":
            criancas.append({
                "Nome": participante,
                "Idade": idade if idade else "",
                "Convidado de origem": convidado
            })

    caminho = "exportacoes/lista_portaria.xlsx"

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        pd.DataFrame(lista_completa).to_excel(
            writer,
            sheet_name="Lista Portaria",
            index=False
        )

        pd.DataFrame(criancas).to_excel(
            writer,
            sheet_name="Crianças",
            index=False
        )

    workbook = load_workbook(caminho)

    for sheet in workbook.sheetnames:
        ws = workbook[sheet]

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter

            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))

            ws.column_dimensions[col_letter].width = max_length + 3

    workbook.save(caminho)

    return send_file(
        caminho,
        as_attachment=True,
        download_name="lista_portaria_amelia90.xlsx"
    )


if __name__ == "__main__":
    app.run(debug=True)