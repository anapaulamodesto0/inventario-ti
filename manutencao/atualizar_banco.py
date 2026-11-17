
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "inventario.db"

if not BANCO.exists():
    raise FileNotFoundError(
        "Banco inventario.db não encontrado."
    )

# Criar cópia de segurança
data = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = PASTA / f"inventario_backup_{data}.db"

shutil.copy2(BANCO, BACKUP)

print(f"Backup criado: {BACKUP.name}")

conexao = sqlite3.connect(BANCO)

try:
    conexao.execute("PRAGMA foreign_keys = ON")

    # Verificar estrutura existente
    tabelas = {
        linha[0]
        for linha in conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table'"
        )
    }

    obrigatorias = {
        "usuarios",
        "responsaveis",
        "equipamentos"
    }

    if not obrigatorias.issubset(tabelas):
        raise RuntimeError(
            "O banco não possui todas as tabelas "
            "necessárias."
        )

    # Criar tabela de setores
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS setores (
            id_setor INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # Migrar setores existentes
    setores_antigos = conexao.execute("""
        SELECT DISTINCT setor
        FROM responsaveis
        WHERE setor IS NOT NULL
          AND TRIM(setor) != ''
    """).fetchall()

    for (nome_setor,) in setores_antigos:
        conexao.execute("""
            INSERT OR IGNORE INTO setores (nome)
            VALUES (?)
        """, (nome_setor.strip(),))

    # Adicionar setor vinculado ao responsável
    colunas_responsaveis = {
        coluna[1]
        for coluna in conexao.execute(
            "PRAGMA table_info(responsaveis)"
        )
    }

    if "id_setor" not in colunas_responsaveis:
        conexao.execute("""
            ALTER TABLE responsaveis
            ADD COLUMN id_setor INTEGER
            REFERENCES setores(id_setor)
        """)

    # Vincular responsáveis aos setores
    conexao.execute("""
        UPDATE responsaveis
        SET id_setor = (
            SELECT s.id_setor
            FROM setores s
            WHERE s.nome = TRIM(responsaveis.setor)
        )
        WHERE id_setor IS NULL
          AND setor IS NOT NULL
    """)

    # Adicionar observações aos equipamentos
    colunas_equipamentos = {
        coluna[1]
        for coluna in conexao.execute(
            "PRAGMA table_info(equipamentos)"
        )
    }

    if "observacoes" not in colunas_equipamentos:
        conexao.execute("""
            ALTER TABLE equipamentos
            ADD COLUMN observacoes TEXT
        """)

    # Adicionar perfil de administrador
    colunas_usuarios = {
        coluna[1]
        for coluna in conexao.execute(
            "PRAGMA table_info(usuarios)"
        )
    }

    if "administrador" not in colunas_usuarios:
        conexao.execute("""
            ALTER TABLE usuarios
            ADD COLUMN administrador INTEGER
            NOT NULL DEFAULT 0
        """)

    # Promover a conta de teste existente
    # apenas para desenvolvimento local
    conexao.execute("""
        UPDATE usuarios
        SET administrador = 1
        WHERE login = ?
    """, ("teste.ti",))

    conexao.commit()

    print("Banco atualizado com sucesso!")

    for tabela in [
        "usuarios",
        "setores",
        "responsaveis",
        "equipamentos"
    ]:
        quantidade = conexao.execute(
            f"SELECT COUNT(*) FROM {tabela}"
        ).fetchone()[0]

        print(f"{tabela}: {quantidade} registros")

except Exception:
    conexao.rollback()
    print("Erro durante a atualização.")
    print(f"Backup disponível: {BACKUP.name}")
    raise

finally:
    conexao.close()
