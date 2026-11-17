
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Caminho do banco de dados
CAMINHO_BANCO = Path(__file__).resolve().parent / "inventario.db"

# Conectar ao banco
conexao = sqlite3.connect(CAMINHO_BANCO)
cursor = conexao.cursor()

# Criar tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL
)
""")

# Criar usuário fictício de teste
senha = generate_password_hash("Teste@12345")

cursor.execute("""
INSERT OR IGNORE INTO usuarios (nome, login, senha_hash)
VALUES (?, ?, ?)
""", ("Usuário de Teste", "teste.ti", senha))


# Criar tabela de responsáveis
cursor.execute("""
CREATE TABLE IF NOT EXISTS responsaveis (
    id_responsavel INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    setor TEXT NOT NULL
)
""")

# Criar tabela de equipamentos
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipamentos (
    id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
    patrimonio TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL,
    modelo TEXT NOT NULL,
    numero_serie TEXT,
    id_responsavel INTEGER,
    id_usuario INTEGER NOT NULL,

    FOREIGN KEY (id_responsavel)
        REFERENCES responsaveis(id_responsavel),

    FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
)
""")

# Criar responsáveis fictícios para testes
cursor.executemany("""
INSERT INTO responsaveis (nome, setor)
SELECT ?, ?
WHERE NOT EXISTS (
    SELECT 1 FROM responsaveis
    WHERE nome = ? AND setor = ?
)
""", [
    ("Colaborador Teste", "TI", "Colaborador Teste", "TI"),
    ("Colaborador Exemplo", "Administrativo",
     "Colaborador Exemplo", "Administrativo")
])


# Salvar e fechar
conexao.commit()
conexao.close()

print("Banco de dados criado com sucesso!")
