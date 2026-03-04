#ISAQUE DE OLIVEIRA DOS SANTOS

from pydantic import BaseModel

class Cliente(BaseModel):
	id_cliente: int = None
	nome: str
	cpf: str
	telefone: str = None