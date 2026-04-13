# ISAQUE DE OLIVEIRA DOS SANTOS

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.ClienteSchema import ClienteCreate, ClienteResponse, ClienteUpdate
from infra.database import get_async_db
from infra.dependencies import get_current_active_user, require_group
from infra.orm.ClienteModel import ClienteDB
from infra.rate_limit import get_rate_limit, limiter
from services.AuditoriaService import AuditoriaService

router = APIRouter()


@router.get("/cliente/", response_model=List[ClienteResponse], tags=["Cliente"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_clientes(
    request: Request,
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome (parcial)"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    telefone: Optional[str] = Query(None, description="Filtrar por telefone"),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user),
):
    try:
        stmt = select(ClienteDB)
        if id is not None:
            stmt = stmt.where(ClienteDB.id == id)
        if nome is not None:
            stmt = stmt.where(ClienteDB.nome.ilike(f"%{nome}%"))
        if cpf is not None:
            stmt = stmt.where(ClienteDB.cpf == cpf)
        if telefone is not None:
            stmt = stmt.where(ClienteDB.telefone == telefone)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar clientes: {str(e)}")


@router.get("/cliente/{id}", response_model=ClienteResponse, tags=["Cliente"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_cliente(request: Request, id: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(get_current_active_user)):
    try:
        result = await db.execute(select(ClienteDB).where(ClienteDB.id == id))
        cliente = result.scalars().first()
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
        return cliente
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar cliente: {str(e)}")


@router.post("/cliente/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED, tags=["Cliente"])
@limiter.limit(get_rate_limit("restrictive"))
async def post_cliente(request: Request, cliente_data: ClienteCreate, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1, 3]))):
    try:
        if cliente_data.cpf:
            dup = await db.execute(select(ClienteDB).where(ClienteDB.cpf == cliente_data.cpf))
            if dup.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ja existe um cliente com este CPF")
        novo_cliente = ClienteDB(id=None, nome=cliente_data.nome, cpf=cliente_data.cpf, telefone=cliente_data.telefone)
        db.add(novo_cliente)
        await db.flush()
        await db.refresh(novo_cliente)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="CREATE", recurso="cliente", recurso_id=novo_cliente.id, dados_novos=novo_cliente, request=request)
        await db.commit()
        await db.refresh(novo_cliente)
        return novo_cliente
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar cliente: {str(e)}")


@router.put("/cliente/{id}", response_model=ClienteResponse, tags=["Cliente"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive"))
async def put_cliente(request: Request, id: int, cliente_data: ClienteUpdate, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1, 3]))):
    try:
        result = await db.execute(select(ClienteDB).where(ClienteDB.id == id))
        cliente = result.scalars().first()
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
        if cliente_data.cpf and cliente_data.cpf != cliente.cpf:
            dup = await db.execute(select(ClienteDB).where(ClienteDB.cpf == cliente_data.cpf))
            if dup.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ja existe um cliente com este CPF")
        dados_antigos = {col.name: getattr(cliente, col.name) for col in cliente.__table__.columns}
        for field, value in cliente_data.model_dump(exclude_unset=True).items():
            setattr(cliente, field, value)
        await db.flush()
        await db.refresh(cliente)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="UPDATE", recurso="cliente", recurso_id=cliente.id, dados_antigos=dados_antigos, dados_novos=cliente, request=request)
        await db.commit()
        await db.refresh(cliente)
        return cliente
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar cliente: {str(e)}")


@router.delete("/cliente/{id}", status_code=status.HTTP_200_OK, tags=["Cliente"])
@limiter.limit(get_rate_limit("critical"))
async def delete_cliente(request: Request, id: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        result = await db.execute(select(ClienteDB).where(ClienteDB.id == id))
        cliente = result.scalars().first()
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
        dados_antigos = {col.name: getattr(cliente, col.name) for col in cliente.__table__.columns}
        await db.delete(cliente)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="DELETE", recurso="cliente", recurso_id=id, dados_antigos=dados_antigos, request=request)
        await db.commit()
        return {"msg": "Cliente deletado com sucesso", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao deletar cliente: {str(e)}")
