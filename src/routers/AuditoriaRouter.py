from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from domain.schemas.AuditoriaSchema import AuditoriaResponse
from domain.schemas.AuthSchema import FuncionarioAuth
from infra.orm.AuditoriaModel import AuditoriaDB
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.database import get_async_db
from infra.dependencies import require_group
from infra.rate_limit import limiter, get_rate_limit

router = APIRouter()


@router.get("/auditoria", response_model=List[AuditoriaResponse], tags=["Auditoria"], summary="Listar registros de auditoria - protegida por JWT e grupo 1")
@limiter.limit(get_rate_limit("moderate"))
async def listar_auditoria(
    request: Request,
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limite: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    funcionario_id: Optional[int] = Query(None, description="Filtrar por funcionário"),
    acao: Optional[str] = Query(None, description="Filtrar por ação(ões), separadas por vírgula (ex: CREATE,UPDATE)"),
    recurso: Optional[str] = Query(None, description="Filtrar por recurso(s), separados por vírgula (ex: comanda,produto)"),
    recurso_id: Optional[int] = Query(None, description="Filtrar por ID do recurso"),
    ip_address: Optional[str] = Query(None, description="Filtrar por IP (parcial)"),
    user_agent: Optional[str] = Query(None, description="Filtrar por user agent (parcial)"),
    data_inicio: Optional[str] = Query(None, description="Filtrar a partir desta data (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Filtrar até esta data (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1])),
):
    try:
        stmt = select(AuditoriaDB, FuncionarioDB).join(FuncionarioDB, FuncionarioDB.id == AuditoriaDB.funcionario_id)

        if id is not None:
            stmt = stmt.where(AuditoriaDB.id == id)
        if funcionario_id:
            stmt = stmt.where(AuditoriaDB.funcionario_id == funcionario_id)
        if acao:
            stmt = stmt.where(AuditoriaDB.acao.in_([a.strip().upper() for a in acao.split(",")]))
        if recurso:
            stmt = stmt.where(AuditoriaDB.recurso.in_([r.strip().lower() for r in recurso.split(",")]))
        if recurso_id is not None:
            stmt = stmt.where(AuditoriaDB.recurso_id == recurso_id)
        if ip_address:
            stmt = stmt.where(AuditoriaDB.ip_address.ilike(f"%{ip_address}%"))
        if user_agent:
            stmt = stmt.where(AuditoriaDB.user_agent.ilike(f"%{user_agent}%"))
        if data_inicio:
            try:
                stmt = stmt.where(AuditoriaDB.data_hora >= datetime.strptime(data_inicio, "%Y-%m-%d"))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data inicio invalida. Use YYYY-MM-DD")
        if data_fim:
            try:
                stmt = stmt.where(AuditoriaDB.data_hora <= datetime.strptime(data_fim, "%Y-%m-%d"))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data fim invalida. Use YYYY-MM-DD")

        stmt = stmt.order_by(desc(AuditoriaDB.data_hora)).offset(skip).limit(limite)
        result = await db.execute(stmt)
        rows = result.all()

        return [
            AuditoriaResponse(
                id=a.id,
                funcionario_id=a.funcionario_id,
                funcionario={"id": f.id, "nome": f.nome, "matricula": f.matricula, "grupo": f.grupo},
                acao=a.acao,
                recurso=a.recurso,
                recurso_id=a.recurso_id,
                dados_antigos=a.dados_antigos,
                dados_novos=a.dados_novos,
                ip_address=a.ip_address,
                user_agent=a.user_agent,
                data_hora=a.data_hora,
            )
            for a, f in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao listar auditoria: {str(e)}")


@router.get("/auditoria/acoes", tags=["Auditoria"], summary="Listar tipos de acoes disponiveis")
@limiter.limit(get_rate_limit("light"))
async def listar_acoes_disponiveis(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1])),
):
    try:
        res_acoes = await db.execute(select(AuditoriaDB.acao).distinct())
        res_recursos = await db.execute(select(AuditoriaDB.recurso).distinct())
        return {
            "acoes": [{"codigo": row[0]} for row in res_acoes.all()],
            "recursos": [{"codigo": row[0]} for row in res_recursos.all()],
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao listar acoes: {str(e)}")
