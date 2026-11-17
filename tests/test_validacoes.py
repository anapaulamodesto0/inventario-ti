
from app import preparar_valores_equipamento, validar_equipamento


def dados_validos():
    return {
        "patrimonio": "PAT001",
        "tipo": "Notebook",
        "modelo": "Dell Latitude",
        "numero_serie": "",
        "id_responsavel": "",
        "observacoes": ""
    }


def test_campos_obrigatorios():
    dados = dados_validos()
    dados["patrimonio"] = ""

    resultado = validar_equipamento(None, dados)

    assert resultado == "Preencha patrimonio, tipo e modelo."


def test_limite_de_caracteres():
    dados = dados_validos()
    dados["modelo"] = "A" * 101

    resultado = validar_equipamento(None, dados)

    assert "no maximo 100 caracteres" in resultado


def test_responsavel_invalido():
    dados = dados_validos()
    dados["id_responsavel"] = "abc"

    resultado = validar_equipamento(None, dados)

    assert resultado == "Selecione um responsavel valido."


def test_preparacao_dos_valores():
    dados = dados_validos()

    resultado = preparar_valores_equipamento(dados)

    assert resultado == (
        "PAT001",
        "Notebook",
        "Dell Latitude",
        None,
        None,
        None
    )
