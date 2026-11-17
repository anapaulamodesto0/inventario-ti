
import pytest

from app import app


@pytest.fixture
def cliente():
    app.config.update(TESTING=True)

    with app.test_client() as cliente:
        yield cliente


def test_login_exibe_pagina(cliente):
    resposta = cliente.get("/")

    assert resposta.status_code == 200


def test_inicio_exige_login(cliente):
    resposta = cliente.get("/inicio")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_consulta_exige_login(cliente):
    resposta = cliente.get("/consultar")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_cadastro_exige_login(cliente):
    resposta = cliente.get("/cadastro")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_admin_exige_login(cliente):
    resposta = cliente.get("/admin/setores")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_usuario_comum_nao_acessa_admin(cliente, monkeypatch):
    def buscar_usuario_simulado(sql, parametros=()):
        return {"administrador": 0}

    monkeypatch.setattr(
        "app.buscar_um",
        buscar_usuario_simulado
    )

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1

    resposta = cliente.get("/admin/setores")

    assert resposta.status_code == 403


def test_administrador_acessa_setores(cliente, monkeypatch):
    def buscar_usuario_simulado(sql, parametros=()):
        return {"administrador": 1}

    monkeypatch.setattr(
        "app.buscar_um",
        buscar_usuario_simulado
    )

    monkeypatch.setattr(
        "app.listar_setores",
        lambda: []
    )

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1

    resposta = cliente.get("/admin/setores")

    assert resposta.status_code == 200

from werkzeug.security import generate_password_hash
import sqlite3
from contextlib import closing


def test_login_com_senha_correta(banco_temporario):
    senha_hash = generate_password_hash("SenhaTeste123")

    with closing(sqlite3.connect(banco_temporario)) as conexao:
        conexao.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?
            WHERE id_usuario = 1
            """,
            (senha_hash,)
        )
        conexao.commit()

    with app.test_client() as cliente:
        resposta = cliente.post(
            "/",
            data={
                "usuario": "teste",
                "senha": "SenhaTeste123"
            }
        )

        assert resposta.status_code == 302
        assert resposta.headers["Location"].endswith("/inicio")

        with cliente.session_transaction() as sessao:
            assert sessao["usuario_id"] == 1
            assert sessao["administrador"] is True


def test_login_com_senha_incorreta(banco_temporario):
    with app.test_client() as cliente:
        resposta = cliente.post(
            "/",
            data={
                "usuario": "teste",
                "senha": "SenhaIncorreta"
            }
        )

        assert resposta.status_code == 200
        assert b"Usuario ou senha invalidos" in resposta.data

def test_logout_encerra_sessao():
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        # Simular usuario autenticado
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1
            sessao["administrador"] = True

        # Encerrar sessao
        resposta = cliente.post("/sair")

        assert resposta.status_code == 302
        assert resposta.headers["Location"].endswith("/")

        # Confirmar que a sessao foi limpa
        with cliente.session_transaction() as sessao:
            assert "usuario_id" not in sessao
            assert "administrador" not in sessao

        # Tentar acessar pagina protegida
        resposta = cliente.get("/inicio")

        assert resposta.status_code == 302
        assert resposta.headers["Location"].endswith("/")

def test_admin_cadastra_setor(banco_temporario):
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1
            sessao["administrador"] = True

        resposta = cliente.post(
            "/admin/setores",
            data={"nome": "Financeiro"}
        )

        assert resposta.status_code == 200
        assert b"Financeiro" in resposta.data

    with closing(sqlite3.connect(banco_temporario)) as conexao:
        setor = conexao.execute(
            "SELECT nome FROM setores WHERE nome = ?",
            ("Financeiro",)
        ).fetchone()

    assert setor is not None
    assert setor[0] == "Financeiro"
