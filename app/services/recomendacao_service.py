from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from app.domain.entities import Denuncia
from app.repositories.denuncia_repository import DenunciaRepository, SinalInteresse


def _normalizar(texto: Optional[str]) -> str:
    return (texto or "").strip().casefold()


@dataclass
class PerfilInteresse:
    categorias: Counter = field(default_factory=Counter)
    bairros: Counter = field(default_factory=Counter)

    @classmethod
    def a_partir_de(cls, sinais: Iterable[SinalInteresse]) -> "PerfilInteresse":
        perfil = cls()
        for s in sinais:
            perfil.categorias[_normalizar(s.categoria)] += s.peso
            bairro = _normalizar(s.bairro)
            if bairro:
                perfil.bairros[bairro] += s.peso
        return perfil


@dataclass
class ItemRecomendado:
    denuncia: Denuncia
    afinidade_categoria: int
    afinidade_bairro: int

    @property
    def motivo(self) -> Optional[str]:
        partes = []
        if self.afinidade_categoria:
            partes.append(self.denuncia.categoria)
        if self.afinidade_bairro and self.denuncia.bairro:
            partes.append(self.denuncia.bairro)
        if not partes:
            return None
        return "Recomendado: você acompanha " + " · ".join(partes)


def ranquear(denuncias: Iterable[Denuncia], perfil: PerfilInteresse) -> List[ItemRecomendado]:
    itens = [
        ItemRecomendado(
            denuncia=d,
            afinidade_categoria=perfil.categorias.get(_normalizar(d.categoria), 0),
            afinidade_bairro=perfil.bairros.get(_normalizar(d.bairro), 0) if d.bairro else 0,
        )
        for d in denuncias
    ]
    itens.sort(
        key=lambda i: (
            i.afinidade_categoria,
            i.afinidade_bairro,
            i.denuncia.likes,
            i.denuncia.criado_em,
        ),
        reverse=True,
    )
    return itens


class RecomendacaoService:
    def __init__(self, repository: Optional[DenunciaRepository] = None):
        self.repository = repository or DenunciaRepository()

    def feed_para(self, usuario_id: int) -> List[ItemRecomendado]:
        perfil = PerfilInteresse.a_partir_de(self.repository.sinais_interesse(usuario_id))
        return ranquear(self.repository.listar(), perfil)
