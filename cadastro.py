"""Regras de negócio e persistência do cadastro de produtos com SQLite."""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "dados" / "produtos.db"


def preco_para_centavos(texto: str) -> int:
    value = str(texto).strip()
    if not value:
        raise ValueError("Informe um valor.")
    value = value.replace("R$", "").replace(" ", "")
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    try:
        decimal = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Valor deve ser um número, como 25,90.") from error
    if not decimal.is_finite() or decimal < 0 or decimal > 100_000_000:
        raise ValueError("Valor deve ser positivo e dentro do limite permitido.")
    return int((decimal * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def formatar_preco(centavos: int) -> str:
    return f"{centavos / 100:.2f}".replace(".", ",")


class Cadastro:
    def __init__(self, caminho: Path = DEFAULT_DB):
        self.path = Path(caminho)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.conectar() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, valor_centavos INTEGER NOT NULL CHECK(valor_centavos >= 0),
                fornecedor TEXT NOT NULL, categoria TEXT NOT NULL, responsavel TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            con.execute("CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome)")

    def conectar(self):
        con = sqlite3.connect(self.path, timeout=8)
        con.row_factory = sqlite3.Row
        return con

    @staticmethod
    def validar(nome, valor, fornecedor, categoria, responsavel):
        campos = {"Nome": nome, "Fornecedor": fornecedor, "Categoria": categoria, "Responsável": responsavel}
        for label, texto in campos.items():
            if not texto or not str(texto).strip():
                raise ValueError(f"{label} não pode ficar em branco.")
            if len(str(texto).strip()) > 150:
                raise ValueError(f"{label} excede 150 caracteres.")
        return (str(nome).strip(), preco_para_centavos(valor), str(fornecedor).strip(),
                str(categoria).strip(), str(responsavel).strip())

    def adicionar(self, nome, valor, fornecedor, categoria, responsavel) -> int:
        row = self.validar(nome, valor, fornecedor, categoria, responsavel)
        with self.conectar() as con:
            result = con.execute("""INSERT INTO produtos(nome,valor_centavos,fornecedor,categoria,responsavel)
                VALUES(?,?,?,?,?)""", row)
            return result.lastrowid

    def atualizar(self, produto_id: int, nome, valor, fornecedor, categoria, responsavel):
        row = self.validar(nome, valor, fornecedor, categoria, responsavel)
        with self.conectar() as con:
            result = con.execute("""UPDATE produtos SET nome=?,valor_centavos=?,fornecedor=?,categoria=?,
                responsavel=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?""", (*row, produto_id))
            if result.rowcount != 1:
                raise ValueError("Produto não encontrado.")

    def apagar(self, produto_id: int):
        with self.conectar() as con:
            result = con.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
            if result.rowcount != 1:
                raise ValueError("Produto não encontrado.")

    def listar(self, filtro: str = "") -> list[dict]:
        term = '%' + filtro.strip().lower().replace('%', r'\%').replace('_', r'\_') + '%'
        with self.conectar() as con:
            items = con.execute("""SELECT id,nome,valor_centavos,fornecedor,categoria,responsavel,criado_em
                FROM produtos WHERE LOWER(nome) LIKE ? ESCAPE '\\' OR LOWER(categoria) LIKE ? ESCAPE '\\'
                ORDER BY id DESC""", (term, term)).fetchall()
        return [dict(r) for r in items]

    def exportar_csv(self, destino: Path) -> int:
        dados = self.listar()
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(("ID", "Nome", "Valor (R$)", "Fornecedor", "Categoria", "Responsável", "Data de cadastro"))
            for d in dados:
                w.writerow((d["id"], d["nome"], formatar_preco(d["valor_centavos"]),
                            d["fornecedor"], d["categoria"], d["responsavel"], d["criado_em"]))
        return len(dados)
