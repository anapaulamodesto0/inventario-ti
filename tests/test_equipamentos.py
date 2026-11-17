from contextlib import closing
import sqlite3

from app import app


def test_cadastrar_equipamento(banco_temporario):
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        # Simular um usuario autenticado
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1

        # Cadastrar equipamento ficticio
        resposta = cliente.post(
            "/cadastro",
            data={
                "patrimonio": "PAT001",
                "tipo": "Notebook",
                "modelo": "Dell Latitude",
                "numero_serie": "SN123456",
                "id_responsavel": "1",
                "observacoes": "Equipamento de teste"
            }
        )

        # Verificar redirecionamento apos cadastro
        assert resposta.status_code == 302
        assert resposta.headers["Location"].endswith(
            "/consultar"
        )

    # Conferir o registro no banco temporario
    with closing(sqlite3.connect(banco_temporario)) as conexao:
        equipamento = conexao.execute(
            """
            SELECT patrimonio, tipo, modelo
            FROM equipamentos
            WHERE patrimonio = ?
            """,
            ("PAT001",)
        ).fetchone()

    assert equipamento is not None
    assert equipamento[0] == "PAT001"
    assert equipamento[1] == "Notebook"
    assert equipamento[2] == "Dell Latitude"


def test_impedir_patrimonio_duplicado(banco_temporario):
    app.config["TESTING"] = True

    dados = {
        "patrimonio": "PAT002",
        "tipo": "Notebook",
        "modelo": "Dell Latitude",
        "numero_serie": "SN789",
        "id_responsavel": "1",
        "observacoes": "Teste de duplicidade"
    }

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1

        # Primeiro cadastro
        primeira_resposta = cliente.post(
            "/cadastro",
            data=dados
        )

        assert primeira_resposta.status_code == 302

        # Tentativa de cadastrar o mesmo patrimonio
        segunda_resposta = cliente.post(
            "/cadastro",
            data=dados
        )

        assert segunda_resposta.status_code == 200
        assert b"patrimonio ja existe" in segunda_resposta.data

    # Confirmar que somente um equipamento foi gravado
    with closing(sqlite3.connect(banco_temporario)) as conexao:
        quantidade = conexao.execute(
            """
            SELECT COUNT(*)
            FROM equipamentos
            WHERE patrimonio = ?
            """,
            ("PAT002",)
        ).fetchone()[0]

    assert quantidade == 1


def test_editar_equipamento(banco_temporario):
    app.config["TESTING"] = True

    # Preparar equipamento no banco temporario
    with closing(sqlite3.connect(banco_temporario)) as conexao:
        conexao.execute(
            """
            INSERT INTO equipamentos (
                patrimonio,
                tipo,
                modelo,
                id_usuario,
                data_cadastro
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "PAT003",
                "Notebook",
                "Modelo Antigo",
                1,
                "17/11/2026 10:00"
            )
        )
        conexao.commit()

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1

        resposta = cliente.post(
            "/editar/1",
            data={
                "patrimonio": "PAT003",
                "tipo": "Notebook",
                "modelo": "Modelo Atualizado",
                "numero_serie": "SN003",
                "id_responsavel": "1",
                "observacoes": "Equipamento atualizado"
            }
        )

        assert resposta.status_code == 302
        assert resposta.headers["Location"].endswith(
            "/consultar"
        )

    # Confirmar alteracao no banco
    with closing(sqlite3.connect(banco_temporario)) as conexao:
        equipamento = conexao.execute(
            """
            SELECT modelo, numero_serie, observacoes
            FROM equipamentos
            WHERE patrimonio = ?
            """,
            ("PAT003",)
        ).fetchone()

    assert equipamento is not None
    assert equipamento[0] == "Modelo Atualizado"
    assert equipamento[1] == "SN003"
    assert equipamento[2] == "Equipamento atualizado"

def test_consultar_equipamentos_com_filtros(banco_temporario):
    app.config["TESTING"] = True

    # Inserir equipamento no banco temporario
    with closing(sqlite3.connect(banco_temporario)) as conexao:
        conexao.execute(
            """
            INSERT INTO equipamentos (
                patrimonio,
                tipo,
                modelo,
                id_responsavel,
                id_usuario,
                data_cadastro
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "PAT004",
                "Notebook",
                "Dell Latitude",
                1,
                1,
                "17/11/2026 10:00"
            )
        )
        conexao.commit()

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1

        resposta = cliente.get(
            "/consultar?setor=TI&tipo=Notebook"
        )

        assert resposta.status_code == 200
        assert b"PAT004" in resposta.data
        assert b"Dell Latitude" in resposta.data
