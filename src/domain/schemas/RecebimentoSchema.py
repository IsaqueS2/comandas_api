from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.ComandaSchema import ComandaResponse, ClienteResponse, FuncionarioResponse

class RecebimentoCreate(BaseModel):
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    desconto: float = Field(0.0, description="Valor do desconto em Reais")
    acrescimo: float = Field(0.0, description="Valor de acréscimo em Reais")
    comandas_ids: List[int] = Field(..., description="Lista de IDs das comandas que estão sendo pagas")

class RecebimentoResponse(BaseModel):
    id: int
    funcionario_id: int
    cliente_id: Optional[int]
    data_hora: datetime
    valor_subtotal: float
    desconto: float
    acrescimo: float
    valor_total_final: float
    comandas: List[ComandaResponse] = []
    funcionario: Optional[FuncionarioResponse] = None
    cliente: Optional[ClienteResponse] = None

    class Config:
        from_attributes = True
