import unittest
from datetime import datetime, timedelta

from app.domain.entities import Denuncia
from app.repositories.denuncia_repository import SinalInteresse
from app.services.recomendacao_service import PerfilInteresse, ranquear

BASE = datetime(2026, 10, 1, 12, 0)


def den(id, categoria, bairro, likes=0, dias=0):
    return Denuncia(
        id=id,
        categoria=categoria,
        descricao="x",
        cep="20000-000",
        email="a@b.com",
        telefone="21999999999",
        bairro=bairro,
        likes=likes,
        criado_em=BASE + timedelta(days=dias),
    )


def ids(itens):
    return [i.denuncia.id for i in itens]


class RanquearTest(unittest.TestCase):
    def test_categoria_vence_bairro_que_vence_curtidas(self):
        perfil = PerfilInteresse.a_partir_de([
            SinalInteresse("Queimada", "Tijuca", 2),
        ])
        feed = ranquear([
            den(1, "Lixo Irregular", "Tijuca", likes=99),
            den(2, "Queimada", "Centro", likes=5),
            den(3, "Queimada", "Tijuca", likes=0),
            den(4, "Lixo Irregular", "Centro", likes=50),
        ], perfil)
        self.assertEqual(ids(feed), [3, 2, 1, 4])

    def test_curtidas_desempatam_dentro_da_mesma_faixa(self):
        perfil = PerfilInteresse.a_partir_de([
            SinalInteresse("Queimada", "Tijuca", 2),
        ])
        feed = ranquear([
            den(1, "Queimada", "Tijuca", likes=3),
            den(2, "Queimada", "Tijuca", likes=10),
        ], perfil)
        self.assertEqual(ids(feed), [2, 1])

    def test_recencia_desempata_curtidas_iguais(self):
        feed = ranquear([
            den(1, "Queimada", "Tijuca", likes=4, dias=0),
            den(2, "Queimada", "Tijuca", likes=4, dias=3),
        ], PerfilInteresse())
        self.assertEqual(ids(feed), [2, 1])

    def test_cold_start_ordena_por_curtidas(self):
        feed = ranquear([
            den(1, "Queimada", "Tijuca", likes=1),
            den(2, "Lixo Irregular", "Centro", likes=7),
        ], PerfilInteresse())
        self.assertEqual(ids(feed), [2, 1])
        self.assertIsNone(feed[0].motivo)

    def test_afinidade_maior_vence_na_mesma_dimensao(self):
        perfil = PerfilInteresse.a_partir_de([
            SinalInteresse("Queimada", None, 2),
            SinalInteresse("Lixo Irregular", None, 2),
            SinalInteresse("Lixo Irregular", None, 1),
        ])
        feed = ranquear([
            den(1, "Queimada", None, likes=100),
            den(2, "Lixo Irregular", None, likes=0),
        ], perfil)
        self.assertEqual(ids(feed), [2, 1])

    def test_bairro_normalizado_e_ausente(self):
        perfil = PerfilInteresse.a_partir_de([
            SinalInteresse("Queimada", "  TIJUCA ", 1),
            SinalInteresse("Queimada", None, 1),
        ])
        feed = ranquear([
            den(1, "Queimada", None, likes=9),
            den(2, "Queimada", "Tijuca", likes=0),
        ], perfil)
        self.assertEqual(ids(feed), [2, 1])
        self.assertEqual(feed[0].motivo, "Recomendado: você acompanha Queimada · Tijuca")


if __name__ == "__main__":
    unittest.main()
