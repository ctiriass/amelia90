from flask import Flask, send_from_directory, send_file, request, redirect
import sqlite3
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
from models import criar_banco

app = Flask(__name__)
criar_banco()

BASE_URL = "https://amelia90.onrender.com"
MAPS_LINK = "https://maps.app.goo.gl/T3QYpdr4MEtbXsJ96"
ADMIN_SECRET = "8F4K2X9P7Q"


def conectar():
    return sqlite3.connect("banco/amelia90.db")


@app.route("/")
def home():
    return """
    <h1>90 Anos da Amélia</h1>
    <p>Sistema RSVP funcionando!</p>
    """


@app.route("/uploads/<nome_arquivo>")
def uploads(nome_arquivo):
    return send_from_directory("uploads", nome_arquivo)


@app.route("/admin/convidados")
def convidados_publico():
    return "<h1>Acesso restrito.</h1>"


@app.route("/admin/<segredo>/convidados")
def listar_convidados(segredo):
    if segredo != ADMIN_SECRET:
        return "<h1>Acesso negado.</h1>"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, telefone, limite, respondeu
        FROM convidados
        ORDER BY nome
    """)

    convidados = cursor.fetchall()
    conexao.close()

    html = f"""
    <h1>Links dos Convidados</h1>

    <p><a href="/admin/{segredo}">Voltar ao painel</a></p>

    <table border="1" cellpadding="8">
        <tr>
            <th>ID</th>
            <th>Código</th>
            <th>Nome</th>
            <th>Telefone</th>
            <th>Limite</th>
            <th>Link RSVP</th>
        </tr>
    """

    for id_, codigo, nome, telefone, limite, respondeu in convidados:
        link = f"{BASE_URL}/rsvp/{codigo}"
        html += f"""
        <tr>
            <td>{id_}</td>
            <td>{codigo}</td>
            <td>{nome}</td>
            <td>{telefone}</td>
            <td>{limite}</td>
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
        SELECT id, nome, respondeu, limite
        FROM convidados
        WHERE codigo = ?
    """, (codigo,))

    convidado = cursor.fetchone()

    if not convidado:
        conexao.close()
        return "<h1>Convite não encontrado.</h1>"

    convidado_id, nome_convidado, respondeu, limite = convidado
    limite = int(limite or 1)

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

        nomes = request.form.getlist("nome[]")
        tipos = request.form.getlist("tipo[]")
        idades = request.form.getlist("idade[]")

        nomes_validos = [n.strip() for n in nomes if n.strip()]

        if len(nomes_validos) > limite:
            conexao.close()
            return f"""
            <h1>Limite excedido</h1>
            <p>Este convite permite informar até {limite} participante(s).</p>
            <p>Volte e ajuste a lista antes de enviar.</p>
            """

        for nome, tipo, idade in zip(nomes, tipos, idades):
            if tipo == "Crianca" and not str(idade).strip():
                conexao.close()
                return """
                <h1>Idade obrigatória</h1>
                <p>Para crianças, informe a idade antes de enviar.</p>
                <p>Volte e ajuste o formulário.</p>
                """

        cursor.execute("""
            INSERT INTO confirmacoes
            (convidado_id, observacoes)
            VALUES (?, ?)
        """, (convidado_id, observacoes))

        confirmacao_id = cursor.lastrowid

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
            const LIMITE = {limite};

            function adicionarParticipante() {{
                let container = document.getElementById("participantes");
                let total = container.getElementsByClassName("participante").length;

                if (total >= LIMITE) {{
                    alert("Este convite permite informar até " + LIMITE + " participante(s).");
                    return;
                }}

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

            <p>
                Este convite permite informar até
                <strong>{limite}</strong> participante(s).
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

    cursor.execute("SELECT COUNT(*) FROM convidados")
    total_convidados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM convidados WHERE respondeu = 1")
    total_responderam = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM convidados WHERE respondeu = 0")
    total_pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM participantes")
    total_participantes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM participantes WHERE tipo = 'Adulto'")
    total_adultos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM participantes WHERE tipo = 'Crianca'")
    total_criancas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT 
            c.id,
            c.nome,
            c.telefone,
            c.codigo,
            c.limite,
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

    <h2>Resumo</h2>
    <ul>
        <li>Total de convites: {total_convidados}</li>
        <li>Responderam: {total_responderam}</li>
        <li>Pendentes: {total_pendentes}</li>
        <li>Participantes informados: {total_participantes}</li>
        <li>Adultos informados: {total_adultos}</li>
        <li>Crianças informadas: {total_criancas}</li>
    </ul>

    <p>
        <a href="/admin/{segredo}/convidados">Ver links dos convidados</a>
    </p>

    <p>
        <a href="/admin/{segredo}/exportar">
            Exportar Lista para Excel
        </a>
    </p>

    <table border="1" cellpadding="8">
        <tr>
            <th>Convidado</th>
            <th>Telefone</th>
            <th>Limite</th>
            <th>Confirmados / Limite</th>
            <th>Vagas restantes</th>
            <th>Status</th>
            <th>Ações</th>
        </tr>
    """

    for id_, nome, telefone, codigo, limite, respondeu, total in registros:
        limite = int(limite or 1)
        total = int(total or 0)
        restantes = max(limite - total, 0)

        if not respondeu:
            status = "Pendente"
        elif total >= limite:
            status = "Completo"
        else:
            status = "Parcial"

        html += f"""
        <tr>
            <td>{nome}</td>
            <td>{telefone}</td>
            <td>{limite}</td>
            <td>{total} / {limite}</td>
            <td>{restantes}</td>
            <td>{status}</td>
            <td>
                <a href="/admin/{segredo}/convidado/{id_}">
                    Ver detalhes
                </a>
                |
                <a href="/admin/{segredo}/convidado/{id_}/limite">
                    Alterar limite
                </a>
                |
                <a href="/admin/{segredo}/convidado/{id_}/resetar"
                   onclick="return confirm('Tem certeza que deseja limpar a confirmação deste convidado?');">
                    Limpar confirmação
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
        SELECT nome, telefone, limite
        FROM convidados
        WHERE id = ?
    """, (convidado_id,))

    convidado = cursor.fetchone()

    if not convidado:
        conexao.close()
        return "<h1>Convidado não encontrado.</h1>"

    cursor.execute("""
        SELECT id, observacoes, data_confirmacao
        FROM confirmacoes
        WHERE convidado_id = ?
        ORDER BY id DESC
    """, (convidado_id,))

    confirmacao = cursor.fetchone()

    if not confirmacao:
        conexao.close()
        return f"""
        <h1>Este convidado ainda não respondeu.</h1>

        <p><strong>Convidado:</strong> {convidado[0]}</p>
        <p><strong>Telefone:</strong> {convidado[1]}</p>
        <p><strong>Limite:</strong> {convidado[2]}</p>

        <p>
            <a href="/admin/{segredo}/convidado/{convidado_id}/limite">
                Alterar limite
            </a>
        </p>

        <p>
            <a href="/admin/{segredo}">Voltar ao painel</a>
        </p>
        """

    confirmacao_id, observacoes, data = confirmacao

    cursor.execute("""
        SELECT nome, tipo, idade
        FROM participantes
        WHERE confirmacao_id = ?
        ORDER BY id
    """, (confirmacao_id,))

    participantes = cursor.fetchall()
    conexao.close()

    total_participantes = len(participantes)
    limite = int(convidado[2] or 1)
    restantes = max(limite - total_participantes, 0)

    html = f"""
    <h1>Detalhes da Confirmação</h1>

    <p><strong>Convidado:</strong> {convidado[0]}</p>
    <p><strong>Telefone:</strong> {convidado[1]}</p>
    <p><strong>Limite:</strong> {limite}</p>
    <p><strong>Confirmados:</strong> {total_participantes} / {limite}</p>
    <p><strong>Vagas restantes:</strong> {restantes}</p>
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
        <a href="/admin/{segredo}/convidado/{convidado_id}/limite">
            Alterar limite
        </a>
    </p>

    <p>
        <a href="/admin/{segredo}/convidado/{convidado_id}/resetar"
           onclick="return confirm('Tem certeza que deseja limpar esta confirmação?');">
            Limpar confirmação deste convidado
        </a>
    </p>

    <p>
        <a href="/admin/{segredo}">Voltar ao painel</a>
    </p>
    """

    return html


@app.route("/admin/<segredo>/convidado/<int:convidado_id>/limite", methods=["GET", "POST"])
def alterar_limite(segredo, convidado_id):
    if segredo != ADMIN_SECRET:
        return "<h1>Acesso negado.</h1>"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT nome, telefone, limite
        FROM convidados
        WHERE id = ?
    """, (convidado_id,))

    convidado = cursor.fetchone()

    if not convidado:
        conexao.close()
        return "<h1>Convidado não encontrado.</h1>"

    nome, telefone, limite_atual = convidado

    if request.method == "POST":
        novo_limite = request.form.get("limite", "1")

        try:
            novo_limite = int(novo_limite)
        except ValueError:
            novo_limite = 1

        if novo_limite < 1:
            novo_limite = 1

        cursor.execute("""
            UPDATE convidados
            SET limite = ?
            WHERE id = ?
        """, (novo_limite, convidado_id))

        conexao.commit()
        conexao.close()

        return redirect(f"/admin/{segredo}")

    conexao.close()

    return f"""
    <h1>Alterar Limite</h1>

    <p><strong>Convidado:</strong> {nome}</p>
    <p><strong>Telefone:</strong> {telefone}</p>
    <p><strong>Limite atual:</strong> {limite_atual}</p>

    <form method="POST">
        <label>Novo limite de participantes:</label><br>
        <input type="number" name="limite" min="1" value="{limite_atual}" required>
        <br><br>
        <button type="submit">Salvar novo limite</button>
    </form>

    <p>
        <a href="/admin/{segredo}">Voltar ao painel</a>
    </p>
    """


@app.route("/admin/<segredo>/convidado/<int:convidado_id>/resetar")
def resetar_convidado(segredo, convidado_id):
    if segredo != ADMIN_SECRET:
        return "<h1>Acesso negado.</h1>"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id
        FROM confirmacoes
        WHERE convidado_id = ?
    """, (convidado_id,))

    confirmacoes = cursor.fetchall()

    for confirmacao in confirmacoes:
        confirmacao_id = confirmacao[0]

        cursor.execute("""
            DELETE FROM participantes
            WHERE confirmacao_id = ?
        """, (confirmacao_id,))

    cursor.execute("""
        DELETE FROM confirmacoes
        WHERE convidado_id = ?
    """, (convidado_id,))

    cursor.execute("""
        UPDATE convidados
        SET respondeu = 0
        WHERE id = ?
    """, (convidado_id,))

    conexao.commit()
    conexao.close()

    return redirect(f"/admin/{segredo}")


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

    colunas_lista = [
        "Nome",
        "Tipo",
        "Idade",
        "Convidado de origem",
        "Data da confirmação"
    ]

    colunas_criancas = [
        "Nome",
        "Idade",
        "Convidado de origem"
    ]

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        pd.DataFrame(lista_completa, columns=colunas_lista).to_excel(
            writer,
            sheet_name="Lista Portaria",
            index=False
        )

        pd.DataFrame(criancas, columns=colunas_criancas).to_excel(
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