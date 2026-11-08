from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cadastro import Cadastro, preco_para_centavos, formatar_preco


class TestCadastro(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db = Cadastro(Path(self.tmp.name) / 'sub' / 'produtos.db')

    def tearDown(self):
        self.tmp.cleanup()

    def test_preco(self):
        self.assertEqual(preco_para_centavos('1.234,56'), 123456)
        self.assertEqual(preco_para_centavos('25.90'), 2590)
        self.assertEqual(formatar_preco(2590), '25,90')
        for x in ('-5', 'texto', 'NaN'):
            with self.assertRaises(ValueError): preco_para_centavos(x)

    def test_crud(self):
        key=self.db.adicionar('Mouse','55,50','Acme','Informática','Aline')
        self.assertEqual(self.db.listar()[0]['id'], key)
        self.db.atualizar(key,'Mouse sem fio','60,00','Acme','Informática','Aline')
        self.assertEqual(self.db.listar('sem fio')[0]['valor_centavos'], 6000)
        self.assertEqual(self.db.listar('categoria inexistente'), [])
        self.db.apagar(key)
        self.assertEqual(self.db.listar(), [])

    def test_injecao_sql_e_campos_obrigatorios(self):
        self.db.adicionar("A'; DROP TABLE produtos;--", '1,00','Acme','Testes','Aline')
        self.assertEqual(len(self.db.listar()), 1)
        with self.assertRaises(ValueError): self.db.adicionar('', '1,00','Acme','Testes','Aline')
        with self.assertRaises(ValueError): self.db.apagar(9999)

    def test_preco_grande_sem_arredondamento_float(self):
        self.assertEqual(formatar_preco(10000000000000001), '100000000000000,01')
        self.assertEqual(formatar_preco(1), '0,01')
        self.assertEqual(formatar_preco(-1), '-0,01')

    def test_pesquisa_por_fornecedor_e_responsavel(self):
        self.db.adicionar('Teclado', '12,90', 'Fornecedor Exemplo', 'Acessórios', 'Responsavel Teste')
        self.db.adicionar('Mouse', '9,90', 'Outro Fornecedor', 'Informática', 'Outra Pessoa')
        self.assertEqual([x['nome'] for x in self.db.listar('exemplo')], ['Teclado'])
        self.assertEqual([x['nome'] for x in self.db.listar('responsavel')], ['Teclado'])
        self.assertEqual([x['nome'] for x in self.db.listar('Mouse')], ['Mouse'])
        self.assertEqual(self.db.listar('nome inexistente'), [])

    def test_csv_exportacao_protege_contra_formulas_excel(self):
        import csv
        self.db.adicionar('=2+2', '10,00', '+EXEMPLO', '@Categoria', '-Responsavel')
        destino = Path(self.tmp.name) / 'seguro.csv'
        self.db.exportar_csv(destino)
        with destino.open('r', encoding='utf-8-sig', newline='') as arquivo:
            registros = list(csv.DictReader(arquivo, delimiter=';'))
        self.assertEqual(len(registros), 1)
        item = registros[0]
        self.assertEqual(item['Nome'], "'=2+2")
        self.assertEqual(item['Fornecedor'], "'+EXEMPLO")
        self.assertEqual(item['Categoria'], "'@Categoria")
        self.assertEqual(item['Responsável'], "'-Responsavel")
        self.assertEqual(item['Valor (R$)'], '10,00')

    def test_exportacao_excel_csv(self):
        self.db.adicionar('Produto','34,50','Fornecedor','Categoria','Responsável')
        dest = Path(self.tmp.name) / 'saida.csv'
        self.assertEqual(self.db.exportar_csv(dest), 1)
        data=dest.read_text(encoding='utf-8-sig')
        self.assertIn('Produto;34,50', data)
        self.assertIn('Responsável', data)


if __name__=='__main__': unittest.main()
