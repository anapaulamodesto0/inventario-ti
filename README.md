Sistema de Inventário de TI

Sistema web desenvolvido para auxiliar no cadastro, organização e gerenciamento de equipamentos de Tecnologia da Informação.

Objetivo

Centralizar as informações dos equipamentos de TI, facilitando a consulta, a identificação dos responsáveis e o acompanhamento dos ativos cadastrados.

Funcionalidades

Autenticação de usuários.

Controle de acesso administrativo.

Cadastro e edição de equipamentos.

Cadastro de setores e responsáveis.

Associação de equipamentos aos responsáveis.

Consulta de equipamentos por setor e tipo.

Registro de observações.

Registro automático da data de cadastro.

Tecnologias utilizadas

Python

Flask

SQLite

HTML

CSS

JavaScript

Estrutura do projeto

app.py — Aplicação principal.

templates/ — Páginas HTML.

static/ — Estilos CSS.

manutencao/ — Scripts de criação e atualização do banco de dados.

requirements.txt — Dependências do projeto.

Execução local

Instale as dependências:

pip install -r requirements.txt

Configure a variável de ambiente SECRET_KEY e execute:

python app.py

Acesse o sistema em:

http://127.0.0.1:5000

Observação: o banco de dados não está incluído no repositório. A aplicação requer um banco SQLite com a estrutura compatível e pelo menos um usuário previamente cadastrado.

Status

Protótipo funcional em desenvolvimento e validação.

Contexto

Projeto acadêmico de desenvolvimento de software, com foco na organização e no controle de equipamentos de TI.

## Revisão técnica do MVP

A revisão técnica do Sistema de Inventário de TI contempla a organização do código, a legibilidade, a manutenção e a segurança da aplicação.

Os principais pontos de atenção são a validação dos dados cadastrados, o controle de acesso dos usuários, a proteção das informações e a rastreabilidade das movimentações de equipamentos.

As melhorias identificadas serão registradas e acompanhadas por meio de commits e Pull Requests, antes da integração à branch principal.
