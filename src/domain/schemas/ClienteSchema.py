from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClienteCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    telefone: Optional[str] = Field(None, min_length=10, max_length=11)


class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1)
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    telefone: Optional[str] = Field(None, min_length=10, max_length=11)


class ClienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    cpf: Optional[str] = None
    telefone: Optional[str] = None
