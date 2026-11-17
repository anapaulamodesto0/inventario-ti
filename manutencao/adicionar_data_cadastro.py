
import sqlite3
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "inventario.db"

conexao = sqlite3.connect(BANCO)

try:
    colunas = {
        coluna[1]
        for coluna in conexao.execute(
            "PRAGMA table_info(equipamentos)"
        )
    }

    if "data_cadastro" not in colunas:
        conexao.execute("""
            ALTER TABLE equipamentos
            ADD COLUMN data_cadastro TEXT
        """)

        print("Campo data_cadastro adicionado.")
    else:
        print("Campo data_cadastro já existe.")

    conexao.commit()

finally:
    conexao.close()
