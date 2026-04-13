from infra import database
from sqlalchemy import CHAR, Column, Integer, VARCHAR


class ClienteDB(database.Base):
    __tablename__ = "tb_cliente"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(VARCHAR(100), nullable=False)
    cpf = Column(CHAR(11), unique=True, nullable=True, index=True)
    telefone = Column(CHAR(11), nullable=True)

    def __init__(self, id, nome, cpf=None, telefone=None):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.telefone = telefone
