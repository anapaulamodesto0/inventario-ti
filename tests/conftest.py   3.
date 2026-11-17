
import sqlite3
from contextlib import closing

import pytest

import app as modulo_app


@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    caminho = tmp_path / "inventario_teste.db"

    monkeypatch.setattr(
        modulo_app,
        "BANCO",
        caminho
    )

    with closing(sqlite3.connect(caminho)) as conexao:
        conexao.execute("PRAGMA foreign_keys = ON")

        conexao.executescript(
            """
            CREATE TABLE usuarios (
                id_usuario INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                administrador INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE setores (
                id_setor INTEGER PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            );

            CREATE TABLE responsaveis (
                id_responsavel INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                setor TEXT NOT NULL,
                id_setor INTEGER,
                FOREIGN KEY (id_setor)
                    REFERENCES setores(id_setor)
            );

            CREATE TABLE equipamentos (
                id_equipamento INTEGER PRIMARY KEY,
                patrimonio TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL,
                modelo TEXT NOT NULL,
                numero_serie TEXT,
                id_responsavel INTEGER,
                id_usuario INTEGER NOT NULL,
                observacoes TEXT,
                data_cadastro TEXT,
                FOREIGN KEY (id_responsavel)
                    REFERENCES responsaveis(id_responsavel),
                FOREIGN KEY (id_usuario)
                    REFERENCES usuarios(id_usuario)
            );

            INSERT INTO usuarios (
                id_usuario,
                nome,
                login,
                senha_hash,
                administrador
            )
            VALUES (
                1,
                'Usuario Teste',
                'teste',
                'hash_teste',
                1
            );

            INSERT INTO setores (
                id_setor,
                nome
            )
            VALUES (1, 'TI');

            INSERT INTO responsaveis (
                id_responsavel,
                nome,
                setor,
                id_setor
            )
            VALUES (
                1,
                'Colaborador Teste',
                'TI',
                1
            );
            """
        )

        conexao.commit()

    return caminho

