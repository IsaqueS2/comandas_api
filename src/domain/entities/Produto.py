#ISAQUE DE OLIVEIRA DOS SANTOS

from pydantic import BaseModel
from typing import Optional

class Produto(BaseModel):
    id_produto: Optional[int] = None
    nome: str
    descricao: str
    foto: Optional[bytes] = None
    valor_unitario: float