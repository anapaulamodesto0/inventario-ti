
import os
import sqlite3

from contextlib import closing
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from werkzeug.security import check_password_hash


# ==================================================
# CONFIGURACAO
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
BANCO = BASE_DIR / "inventario.db"

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "Configure a variavel de ambiente SECRET_KEY."
    )

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)


# ==================================================
# BANCO DE DADOS
# ==================================================

def conectar_banco():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def buscar_todos(sql, parametros=()):
    with closing(conectar_banco()) as conexao:
        return conexao.execute(
            sql, parametros
        ).fetchall()


def buscar_um(sql, parametros=()):
    with closing(conectar_banco()) as conexao:
        return conexao.execute(
            sql, parametros
        ).fetchone()


def listar_setores():
    return buscar_todos(
        "SELECT id_setor, nome FROM setores ORDER BY nome"
    )


def listar_responsaveis():
    return buscar_todos(
        """
        SELECT
            r.id_responsavel,
            r.nome,
            COALESCE(s.nome, r.setor) AS setor
        FROM responsaveis r
        LEFT JOIN setores s
            ON s.id_setor = r.id_setor
        ORDER BY r.nome
        """
    )


# ==================================================
# AUTENTICACAO E PERMISSOES
# ==================================================

def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("login"))

        return funcao(*args, **kwargs)

    return verificar


def admin_obrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        usuario_id = session.get("usuario_id")

        if not usuario_id:
            return redirect(url_for("login"))

        usuario = buscar_um(
            """
            SELECT administrador
            FROM usuarios
            WHERE id_usuario = ?
            """,
            (usuario_id,)
        )

        if not usuario or not usuario["administrador"]:
            abort(403)

        return funcao(*args, **kwargs)

    return verificar


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return redirect(url_for("inicio"))

    erro = None

    if request.method == "POST":
        usuario_digitado = request.form.get(
            "usuario", ""
        ).strip()

        senha = request.form.get("senha", "")

        usuario = buscar_um(
            """
            SELECT id_usuario, senha_hash, administrador
            FROM usuarios
            WHERE login = ?
            """,
            (usuario_digitado,)
        )

        if usuario and check_password_hash(
            usuario["senha_hash"], senha
        ):
            session.clear()
            session["usuario_id"] = usuario["id_usuario"]
            session["administrador"] = bool(
                usuario["administrador"]
            )

            return redirect(url_for("inicio"))

        erro = "Usuario ou senha invalidos."

    return render_template("login.html", erro=erro)


@app.route("/sair", methods=["POST"])
@login_obrigatorio
def sair():
    session.clear()
    return redirect(url_for("login"))


# ==================================================
# PAGINA INICIAL
# ==================================================

@app.route("/inicio")
@login_obrigatorio
def inicio():
    return render_template("inicio.html")


# ==================================================
# CONSULTA DE EQUIPAMENTOS
# ==================================================

@app.route("/consultar")
@login_obrigatorio
def consultar():
    setor = request.args.get("setor", "").strip()
    tipo = request.args.get("tipo", "").strip()

    sql = """
        SELECT
            e.id_equipamento,
            e.patrimonio,
            e.tipo,
            e.modelo,
            e.numero_serie,
            e.observacoes,
            e.data_cadastro,
            r.nome AS responsavel,
            s.nome AS setor
        FROM equipamentos e
        LEFT JOIN responsaveis r
            ON r.id_responsavel = e.id_responsavel
        LEFT JOIN setores s
            ON s.id_setor = r.id_setor
        WHERE 1 = 1
    """

    parametros = []

    if setor:
        sql += " AND s.nome = ?"
        parametros.append(setor)

    if tipo:
        sql += " AND e.tipo = ?"
        parametros.append(tipo)

    sql += " ORDER BY e.id_equipamento DESC"

    equipamentos = buscar_todos(
        sql, tuple(parametros)
    )

    tipos = buscar_todos(
        """
        SELECT DISTINCT tipo
        FROM equipamentos
        ORDER BY tipo
        """
    )

    return render_template(
        "equipamentos.html",
        equipamentos=equipamentos,
        setores=listar_setores(),
        tipos=tipos,
        setor_selecionado=setor,
        tipo_selecionado=tipo
    )


# ==================================================
# FORMULARIO DE EQUIPAMENTOS
# ==================================================

def obter_dados_equipamento():
    campos = (
        "patrimonio",
        "tipo",
        "modelo",
        "numero_serie",
        "id_responsavel",
        "observacoes"
    )

    return {
        campo: request.form.get(campo, "").strip()
        for campo in campos
    }


def validar_equipamento(conexao, dados):
    limites = {
        "patrimonio": 50,
        "tipo": 100,
        "modelo": 100,
        "numero_serie": 100,
        "observacoes": 2000
    }

    for campo in ("patrimonio", "tipo", "modelo"):
        if not dados[campo]:
            return "Preencha patrimonio, tipo e modelo."

    for campo, limite in limites.items():
        if len(dados[campo]) > limite:
            return (
                f"O campo {campo} deve ter "
                f"no maximo {limite} caracteres."
            )

    responsavel = dados["id_responsavel"]

    if responsavel:
        if not responsavel.isdigit():
            return "Selecione um responsavel valido."

        existe = conexao.execute(
            """
            SELECT 1
            FROM responsaveis
            WHERE id_responsavel = ?
            """,
            (int(responsavel),)
        ).fetchone()

        if not existe:
            return "O responsavel selecionado nao existe."

    return None


def preparar_valores_equipamento(dados):
    return (
        dados["patrimonio"],
        dados["tipo"],
        dados["modelo"],
        dados["numero_serie"] or None,
        int(dados["id_responsavel"])
        if dados["id_responsavel"] else None,
        dados["observacoes"] or None
    )


# ==================================================
# CADASTRAR EQUIPAMENTO
# ==================================================

@app.route("/cadastro", methods=["GET", "POST"])
@login_obrigatorio
def cadastro():
    erro = None
    equipamento = None

    if request.method == "POST":
        equipamento = obter_dados_equipamento()

        with closing(conectar_banco()) as conexao:
            erro = validar_equipamento(
                conexao, equipamento
            )

            if not erro:
                valores = preparar_valores_equipamento(
                    equipamento
                )

                data_cadastro = datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                )

                try:
                    conexao.execute(
                        """
                        INSERT INTO equipamentos (
                            patrimonio,
                            tipo,
                            modelo,
                            numero_serie,
                            id_responsavel,
                            observacoes,
                            id_usuario,
                            data_cadastro
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        valores + (
                            session["usuario_id"],
                            data_cadastro
                        )
                    )

                    conexao.commit()
                    return redirect(url_for("consultar"))

                except sqlite3.IntegrityError:
                    conexao.rollback()
                    erro = (
                        "Nao foi possivel cadastrar. "
                        "Verifique se o patrimonio ja existe."
                    )

    return render_template(
        "cadastro.html",
        equipamento=equipamento,
        responsaveis=listar_responsaveis(),
        erro=erro
    )


# ==================================================
# EDITAR EQUIPAMENTO
# ==================================================

@app.route(
    "/editar/<int:id_equipamento>",
    methods=["GET", "POST"]
)
@login_obrigatorio
def editar(id_equipamento):
    equipamento = buscar_um(
        """
        SELECT *
        FROM equipamentos
        WHERE id_equipamento = ?
        """,
        (id_equipamento,)
    )

    if not equipamento:
        abort(404)

    erro = None

    if request.method == "POST":
        dados = obter_dados_equipamento()
        dados["id_equipamento"] = id_equipamento

        with closing(conectar_banco()) as conexao:
            erro = validar_equipamento(conexao, dados)

            if not erro:
                valores = preparar_valores_equipamento(
                    dados
                )

                try:
                    conexao.execute(
                        """
                        UPDATE equipamentos
                        SET
                            patrimonio = ?,
                            tipo = ?,
                            modelo = ?,
                            numero_serie = ?,
                            id_responsavel = ?,
                            observacoes = ?
                        WHERE id_equipamento = ?
                        """,
                        valores + (id_equipamento,)
                    )

                    conexao.commit()
                    return redirect(url_for("consultar"))

                except sqlite3.IntegrityError:
                    conexao.rollback()
                    erro = (
                        "Nao foi possivel salvar. "
                        "Verifique se o patrimonio ja existe."
                    )

        equipamento = dados

    return render_template(
        "cadastro.html",
        equipamento=equipamento,
        responsaveis=listar_responsaveis(),
        erro=erro
    )


# ==================================================
# ADMINISTRACAO DE SETORES
# ==================================================

@app.route("/admin/setores", methods=["GET", "POST"])
@admin_obrigatorio
def cadastrar_setor():
    erro = None
    sucesso = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()

        if not nome:
            erro = "Informe o nome do setor."

        elif len(nome) > 100:
            erro = "O nome deve ter ate 100 caracteres."

        else:
            with closing(conectar_banco()) as conexao:
                try:
                    conexao.execute(
                        "INSERT INTO setores (nome) VALUES (?)",
                        (nome,)
                    )

                    conexao.commit()
                    sucesso = "Setor cadastrado com sucesso."

                except sqlite3.IntegrityError:
                    conexao.rollback()
                    erro = "Este setor ja esta cadastrado."

    return render_template(
        "setores.html",
        setores=listar_setores(),
        erro=erro,
        sucesso=sucesso
    )


# ==================================================
# ADMINISTRACAO DE RESPONSAVEIS
# ==================================================

@app.route(
    "/admin/responsaveis",
    methods=["GET", "POST"]
)
@admin_obrigatorio
def cadastrar_responsavel():
    erro = None
    sucesso = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()

        id_setor = request.form.get(
            "id_setor", ""
        ).strip()

        if not nome:
            erro = "Informe o nome do responsavel."

        elif len(nome) > 150:
            erro = "O nome deve ter ate 150 caracteres."

        elif not id_setor.isdigit():
            erro = "Selecione um setor valido."

        else:
            setor = buscar_um(
                """
                SELECT id_setor, nome
                FROM setores
                WHERE id_setor = ?
                """,
                (int(id_setor),)
            )

            if not setor:
                erro = "O setor selecionado nao existe."

            else:
                with closing(conectar_banco()) as conexao:
                    try:
                        conexao.execute(
                            """
                            INSERT INTO responsaveis (
                                nome,
                                setor,
                                id_setor
                            )
                            VALUES (?, ?, ?)
                            """,
                            (
                                nome,
                                setor["nome"],
                                setor["id_setor"]
                            )
                        )

                        conexao.commit()
                        sucesso = (
                            "Responsavel cadastrado com sucesso."
                        )

                    except sqlite3.IntegrityError:
                        conexao.rollback()
                        erro = (
                            "Nao foi possivel cadastrar "
                            "o responsavel."
                        )

    return render_template(
        "responsaveis.html",
        setores=listar_setores(),
        responsaveis=listar_responsaveis(),
        erro=erro,
        sucesso=sucesso
    )


# ==================================================
# INICIALIZACAO
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)
