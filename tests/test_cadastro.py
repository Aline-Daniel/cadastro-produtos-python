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

    def test_exportacao_excel_csv(self):
        self.db.adicionar('Produto','34,50','Fornecedor','Categoria','Responsável')
        dest = Path(self.tmp.name) / 'saida.csv'
        self.assertEqual(self.db.exportar_csv(dest), 1)
        data=dest.read_text(encoding='utf-8-sig')
        self.assertIn('Produto;34,50', data)
        self.assertIn('Responsável', data)


if __name__=='__main__': unittest.main()
