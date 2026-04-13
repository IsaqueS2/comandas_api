# ISAQUE DE OLIVEIRA DOS SANTOS
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.ProdutoSchema import (
    ProdutoCreate,
    ProdutoPrecoHistoricoResponse,
    ProdutoPublicoResponse,
    ProdutoResponse,
    ProdutoUpdate,
)
from infra.database import get_async_db
from infra.dependencies import get_current_active_user, require_group
from infra.orm.ProdutoModel import ProdutoDB
from infra.orm.ProdutoPrecoHistoricoModel import ProdutoPrecoHistoricoDB
from infra.rate_limit import get_rate_limit, limiter
from services.AuditoriaService import AuditoriaService

router = APIRouter()


@router.get("/produto/publico", response_model=List[ProdutoPublicoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("light"))
async def get_produtos_publicos(
    request: Request,
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome (parcial)"),
    descricao: Optional[str] = Query(None, description="Filtrar por descrição (parcial)"),
    valor: Optional[float] = Query(None, description="Filtrar por valor exato"),
    valor_min: Optional[float] = Query(None, description="Filtrar por valor mínimo (>=)"),
    valor_max: Optional[float] = Query(None, description="Filtrar por valor máximo (<=)"),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        stmt = select(ProdutoDB)
        if id is not None:
            stmt = stmt.where(ProdutoDB.id == id)
        if nome is not None:
            stmt = stmt.where(ProdutoDB.nome.ilike(f"%{nome}%"))
        if descricao is not None:
            stmt = stmt.where(ProdutoDB.descricao.ilike(f"%{descricao}%"))
        if valor is not None:
            stmt = stmt.where(ProdutoDB.valor_unitario == valor)
        if valor_min is not None:
            stmt = stmt.where(ProdutoDB.valor_unitario >= valor_min)
        if valor_max is not None:
            stmt = stmt.where(ProdutoDB.valor_unitario <= valor_max)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar produtos publicos: {str(e)}")


@router.get("/produto/", response_model=List[ProdutoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_produtos(
    request: Request,
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome (parcial)"),
    descricao: Optional[str] = Query(None, description="Filtrar por descrição (parcial)"),
    valor: Optional[float] = Query(None, description="Filtrar por valor exato"),
    valor_min: Optional[float] = Query(None, description="Filtrar por valor mínimo (>=)"),
    valor_max: Optional[float] = Query(None, description="Filtrar por valor máximo (<=)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user),
):
    try:
        stmt = select(ProdutoDB)
        if id is not None:
            stmt = stmt.where(ProdutoDB.id == id)
        if nome is not None:
            stmt = stmt.where(ProdutoDB.nome.ilike(f"%{nome}%"))
        if descricao is not None:
            stmt = stmt.where(ProdutoDB.descricao.ilike(f"%{descricao}%"))
        if valor is not None:
            stmt = stmt.where(ProdutoDB.valor_unitario == valor)
        if valor_min is not None:
            stmt = stmt.where(ProdutoDB.valor_unitario >= valor_min)
        if valor_max is not None:
            stmt = stmt.where(ProdutoDB.valor_unitario <= valor_max)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar produtos: {str(e)}")


@router.get("/produto/{id_prod}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_produto(request: Request, id_prod: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(get_current_active_user)):
    try:
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id_prod))
        produto = result.scalars().first()
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")
        return produto
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar produto: {str(e)}")


@router.get("/produto/{id_prod}/historico-precos", response_model=List[ProdutoPrecoHistoricoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_historico_precos(request: Request, id_prod: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(get_current_active_user)):
    try:
        res = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id_prod))
        if not res.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")
        result = await db.execute(
            select(ProdutoPrecoHistoricoDB)
            .where(ProdutoPrecoHistoricoDB.produto_id == id_prod)
            .order_by(desc(ProdutoPrecoHistoricoDB.vigencia_inicio))
        )
        return result.scalars().all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar historico de precos: {str(e)}")


@router.post("/produto/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED, tags=["Produto"])
@limiter.limit(get_rate_limit("restrictive"))
async def post_produto(request: Request, produto_data: ProdutoCreate, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        novo_produto = ProdutoDB(id=None, nome=produto_data.nome, descricao=produto_data.descricao, foto=produto_data.foto, valor_unitario=produto_data.valor_unitario)
        db.add(novo_produto)
        await db.flush()
        db.add(ProdutoPrecoHistoricoDB(produto_id=novo_produto.id, valor_unitario=produto_data.valor_unitario, vigencia_inicio=datetime.now()))
        await db.refresh(novo_produto)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="CREATE", recurso="produto", recurso_id=novo_produto.id, dados_novos=novo_produto, request=request)
        await db.commit()
        await db.refresh(novo_produto)
        return novo_produto
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar produto: {str(e)}")


@router.put("/produto/{id_prod}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive"))
async def put_produto(request: Request, id_prod: int, produto_data: ProdutoUpdate, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id_prod))
        produto = result.scalars().first()
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")

        valor_alterado = produto_data.valor_unitario is not None and produto_data.valor_unitario != produto.valor_unitario
        dados_antigos = {col.name: getattr(produto, col.name) for col in produto.__table__.columns}
        for field, value in produto_data.model_dump(exclude_unset=True).items():
            setattr(produto, field, value)

        if valor_alterado:
            agora = datetime.now()
            res_hist = await db.execute(
                select(ProdutoPrecoHistoricoDB)
                .where(ProdutoPrecoHistoricoDB.produto_id == id_prod, ProdutoPrecoHistoricoDB.vigencia_fim.is_(None))
                .order_by(desc(ProdutoPrecoHistoricoDB.vigencia_inicio))
            )
            historico_atual = res_hist.scalars().first()
            if historico_atual:
                historico_atual.vigencia_fim = agora
            db.add(ProdutoPrecoHistoricoDB(produto_id=id_prod, valor_unitario=produto_data.valor_unitario, vigencia_inicio=agora))

        await db.flush()
        await db.refresh(produto)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="UPDATE", recurso="produto", recurso_id=produto.id, dados_antigos=dados_antigos, dados_novos=produto, request=request)
        await db.commit()
        await db.refresh(produto)
        return produto
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar produto: {str(e)}")


@router.delete("/produto/{id_prod}", status_code=status.HTTP_200_OK, tags=["Produto"])
@limiter.limit(get_rate_limit("critical"))
async def delete_produto(request: Request, id_prod: int, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    try:
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id_prod))
        produto = result.scalars().first()
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")
        dados_antigos = {col.name: getattr(produto, col.name) for col in produto.__table__.columns}
        await db.delete(produto)
        await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="DELETE", recurso="produto", recurso_id=id_prod, dados_antigos=dados_antigos, request=request)
        await db.commit()
        return {"msg": "Produto deletado com sucesso", "id": id_prod}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao deletar produto: {str(e)}")
