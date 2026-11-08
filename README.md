# 02 — Sistema de Cadastro de Produtos com SQLite

Projeto desktop baseado no exercício **Cadastro Produtos** do ZIP Python–SGBDS. Interface profissional com Python/Tkinter, banco SQLite e exportação CSV para abrir no Excel.

## Executar no Windows

Instale Python 3.10+ e abra o terminal nesta pasta:

```powershell
python interface.py
```

**Não é necessário instalar pacotes externos.** Ao abrir, o sistema cria `dados/produtos.db` automaticamente. Você pode adicionar, pesquisar, editar e excluir produtos e exportar CSV.

## Regras do sistema

- Nome, valor, fornecedor, categoria e responsável são obrigatórios.
- Valores monetários ficam armazenados em **centavos**, sem erros de ponto flutuante.
- ID de produto é automático e exclusivo.
- Consultas SQL são parametrizadas para segurança.
- Exclusão exige confirmação.
- CSV separado por `;`, codificado como UTF-8 com BOM, abre no Excel em português.
- A busca encontra produtos pelo **nome, categoria, fornecedor ou responsável**.
- A exportação CSV protege campos de texto iniciados com sinais de fórmulas do Excel (`=`, `+`, `-`, `@`).
- A formatação dos valores monetários usa somente aritmética inteira, evitando arredondamentos de ponto flutuante.

## Testes

```powershell
python -m unittest discover -s tests -v
```

Todos os dados ficam no seu computador. Para fazer backup, feche a interface e copie `dados/produtos.db`.
