from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    descricao: str = Field(..., min_length=1)
    foto: bytes = None
    valor_unitario: float = Field(..., gt=0)


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1)
    descricao: Optional[str] = Field(None, min_length=1)
    foto: Optional[bytes] = None
    valor_unitario: Optional[float] = Field(None, gt=0)


class ProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    descricao: str
    foto: Optional[bytes] = None
    valor_unitario: float


class ProdutoPublicoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nome: str
    descricao: str
    foto: Optional[bytes] = None


class ProdutoPrecoHistoricoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    produto_id: int
    valor_unitario: float
    vigencia_inicio: datetime
    vigencia_fim: Optional[datetime] = None
