from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.FuncionarioSchema import FuncionarioCreate, FuncionarioResponse, FuncionarioUpdate
from infra.database import get_async_db
from infra.dependencies import get_current_active_user, require_group
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.rate_limit import get_rate_limit, limiter
from infra.security import get_password_hash
from services.AuditoriaService import AuditoriaService

router = APIRouter()


@router.get("/funcionario/", response_model=List[FuncionarioResponse], tags=["Funcionário"], status_code=status.HTTP_200_OK, summary="Listar todos os funcionários")
@limiter.limit(get_rate_limit("moderate"))
async def get_funcionario(
    request: Request,
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome (parcial)"),
    matricula: Optional[str] = Query(None, description="Filtrar por matrícula"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo(s), separados por vírgula (ex: 1,2)"),
    telefone: Optional[str] = Query(None, description="Filtrar por telefone"),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1])),
):
    try:
        stmt = select(FuncionarioDB)
        if id is not None:
            stmt = stmt.where(FuncionarioDB.id == id)
        if nome is not None:
            stmt = stmt.where(FuncionarioDB.nome.ilike(f"%{nome}%"))
        if matricula is not None:
            stmt = stmt.where(FuncionarioDB.matricula == matricula)
        if cpf is not None:
            stmt = stmt.where(FuncionarioDB.cpf == cpf)
        if grupo is not None:
            grupos = [int(g.strip()) for g in grupo.split(",") if g.strip().isdigit()]
            if grupos:
                stmt = stmt.where(FuncionarioDB.grupo.in_(grupos))
        if telefone is not None:
            stmt = stmt.where(FuncionarioDB.telefone == telefone)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar funcionários: {str(e)}")


@router.get("/funcionario/{id}", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_funcionario_by_id(request: Request, id: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(get_current_active_user)):
    try:
        result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.id == id))
        funcionario = result.scalars().first()
        if not funcionario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
        return funcionario
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar funcionário: {str(e)}")


@router.post("/funcionario/", response_model=FuncionarioResponse, status_code=status.HTTP_201_CREATED, tags=["Funcionário"])
@limiter.limit(get_rate_limit("restrictive"))
async def post_funcionario(request: Request, funcionario_data: FuncionarioCreate, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.cpf == funcionario_data.cpf))
        if result.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um funcionário com este CPF")

        novo_funcionario = FuncionarioDB(
            id=None,
            nome=funcionario_data.nome,
            matricula=funcionario_data.matricula,
            cpf=funcionario_data.cpf,
            telefone=funcionario_data.telefone,
            grupo=funcionario_data.grupo,
            senha=get_password_hash(funcionario_data.senha),
        )
        db.add(novo_funcionario)
        await db.flush()
        await db.refresh(novo_funcionario)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="CREATE", recurso="funcionario", recurso_id=novo_funcionario.id, dados_novos=novo_funcionario, request=request)
        await db.commit()
        await db.refresh(novo_funcionario)
        return novo_funcionario
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar funcionário: {str(e)}")


@router.put("/funcionario/{id}", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive"))
async def put_funcionario(request: Request, id: int, funcionario_data: FuncionarioUpdate, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.id == id))
        funcionario = result.scalars().first()
        if not funcionario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")

        if funcionario_data.cpf and funcionario_data.cpf != funcionario.cpf:
            dup = await db.execute(select(FuncionarioDB).where(FuncionarioDB.cpf == funcionario_data.cpf))
            if dup.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um funcionário com este CPF")

        dados_antigos = {col.name: getattr(funcionario, col.name) for col in funcionario.__table__.columns}

        update_data = funcionario_data.model_dump(exclude_unset=True)
        if "senha" in update_data and update_data["senha"]:
            update_data["senha"] = get_password_hash(update_data["senha"])
        for field, value in update_data.items():
            setattr(funcionario, field, value)

        await db.flush()
        await db.refresh(funcionario)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="UPDATE", recurso="funcionario", recurso_id=funcionario.id, dados_antigos=dados_antigos, dados_novos=funcionario, request=request)
        await db.commit()
        await db.refresh(funcionario)
        return funcionario
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar funcionário: {str(e)}")


@router.delete("/funcionario/{id}", status_code=status.HTTP_200_OK, tags=["Funcionário"], summary="Remover funcionário")
@limiter.limit(get_rate_limit("critical"))
async def delete_funcionario(request: Request, id: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.id == id))
        funcionario = result.scalars().first()
        if not funcionario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")

        dados_antigos = {col.name: getattr(funcionario, col.name) for col in funcionario.__table__.columns}
        await db.delete(funcionario)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="DELETE", recurso="funcionario", recurso_id=id, dados_antigos=dados_antigos, request=request)
        await db.commit()
        return {"msg": "Funcionário deletado com sucesso", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao deletar funcionário: {str(e)}")

