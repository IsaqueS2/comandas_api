from datetime import datetime

from infra import database
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.sql import func


class ProdutoPrecoHistoricoDB(database.Base):
    __tablename__ = "tb_produto_preco_historico"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    produto_id = Column(Integer, ForeignKey("tb_produto.id"), nullable=False, index=True)
    valor_unitario = Column(Float, nullable=False)
    vigencia_inicio = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigencia_fim = Column(DateTime(timezone=True), nullable=True)

    def __init__(self, produto_id, valor_unitario, vigencia_inicio=None, vigencia_fim=None):
        self.produto_id = produto_id
        self.valor_unitario = valor_unitario
        self.vigencia_inicio = vigencia_inicio or datetime.now()
        self.vigencia_fim = vigencia_fim
