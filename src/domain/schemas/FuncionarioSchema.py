from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FuncionarioCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    matricula: str = Field(..., min_length=1, max_length=10)
    cpf: str = Field(..., min_length=11, max_length=11)
    telefone: str = Field(..., min_length=10, max_length=11)
    senha: str = Field(..., min_length=6)
    grupo: Literal[1, 2, 3]


class FuncionarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1)
    matricula: Optional[str] = Field(None, min_length=1, max_length=10)
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    telefone: Optional[str] = Field(None, min_length=10, max_length=11)
    senha: Optional[str] = Field(None, min_length=6)
    grupo: Optional[Literal[1, 2, 3]] = None


class FuncionarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    matricula: str
    cpf: str
    telefone: str
    grupo: int
