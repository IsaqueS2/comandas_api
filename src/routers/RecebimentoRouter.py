from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.RecebimentoSchema import RecebimentoCreate, RecebimentoResponse
from infra.database import get_async_db
from infra.dependencies import get_current_active_user, require_group
from infra.orm.ClienteModel import ClienteDB
from infra.orm.ComandaModel import ComandaDB, ComandaProdutoDB
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.orm.RecebimentoModel import RecebimentoDB, RecebimentoComandaDB
from infra.rate_limit import get_rate_limit, limiter
from services.AuditoriaService import AuditoriaService

router = APIRouter()

@router.post("/recebimento/", response_model=RecebimentoResponse, status_code=status.HTTP_201_CREATED, tags=["Recebimento"], summary="Realizar pagamento de comandas")
@limiter.limit(get_rate_limit("restrictive"))
async def create_recebimento(
    recebimento_data: RecebimentoCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1, 3])),
):
    try:
        if not recebimento_data.comandas_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma comanda informada")

        if recebimento_data.cliente_id:
            result = await db.execute(select(ClienteDB).where(ClienteDB.id == recebimento_data.cliente_id))
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cliente não encontrado")

        subtotal = 0.0
        comandas = []
        
        # Processar cada comanda
        for comanda_id in recebimento_data.comandas_ids:
            result = await db.execute(select(ComandaDB).where(ComandaDB.id == comanda_id))
            comanda = result.scalar_one_or_none()
            
            if not comanda:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comanda {comanda_id} não encontrada")
            if comanda.status != 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Comanda {comanda_id} não está aberta")
            
            # Atualizar cliente se informado e mudar status
            if recebimento_data.cliente_id:
                comanda.cliente_id = recebimento_data.cliente_id
            comanda.status = 1  # Fechada
            comandas.append(comanda)

            # Calcular subtotal
            prod_result = await db.execute(
                select(ComandaProdutoDB).where(ComandaProdutoDB.comanda_id == comanda_id)
            )
            for cp in prod_result.scalars():
                subtotal += float(cp.quantidade * cp.valor_unitario)

        valor_total_final = subtotal - recebimento_data.desconto + recebimento_data.acrescimo

        if valor_total_final < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor total não pode ser negativo")

        novo_recebimento = RecebimentoDB(
            funcionario_id=current_user.id,
            cliente_id=recebimento_data.cliente_id,
            data_hora=datetime.now(),
            valor_subtotal=subtotal,
            desconto=recebimento_data.desconto,
            acrescimo=recebimento_data.acrescimo,
            valor_total_final=valor_total_final
        )
        db.add(novo_recebimento)
        await db.flush()  # Para pegar o ID do recebimento

        for comanda in comandas:
            db.add(RecebimentoComandaDB(recebimento_id=novo_recebimento.id, comanda_id=comanda.id))

        await db.commit()
        await db.refresh(novo_recebimento)

        # Retorno simplificado para otimizar.
        # Em um app real, populariamos as respostas de comanda/cliente aqui, mas o frontend pode buscar se precisar.
        return RecebimentoResponse(
            id=novo_recebimento.id,
            funcionario_id=novo_recebimento.funcionario_id,
            cliente_id=novo_recebimento.cliente_id,
            data_hora=novo_recebimento.data_hora,
            valor_subtotal=float(novo_recebimento.valor_subtotal),
            desconto=float(novo_recebimento.desconto),
            acrescimo=float(novo_recebimento.acrescimo),
            valor_total_final=float(novo_recebimento.valor_total_final)
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao processar recebimento: {str(e)}")

@router.get("/recebimento/dashboard", tags=["Recebimento"], summary="Dados consolidados para o painel principal")
@limiter.limit(get_rate_limit("moderate"))
async def get_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1, 2, 3]))
):
    try:
        # Hoje
        today = datetime.now().date()
        hoje_str = today.strftime("%Y-%m-%d")
        
        # 1. Obter soma do Caixa Hoje
        # Considerando que data_hora pode conter o tempo, procuramos tudo que seja da data atual
        stmt = select(func.sum(RecebimentoDB.valor_total_final)).where(
            func.date(RecebimentoDB.data_hora) == today
        )
        result = await db.execute(stmt)
        caixa_hoje = result.scalar() or 0.0

        return {
            "caixa_hoje": float(caixa_hoje)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados do dashboard: {str(e)}")

@router.get("/recebimento/", response_model=List[RecebimentoResponse], tags=["Recebimento"])
@limiter.limit(get_rate_limit("moderate"))
async def get_recebimentos(
    request: Request,
    skip: int = Query(0),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1, 3]))
):
    result = await db.execute(select(RecebimentoDB).offset(skip).limit(limit))
    items = result.scalars().all()
    # Retorno simples sem joins (pode ser evoluído)
    return [
        RecebimentoResponse(
            id=r.id,
            funcionario_id=r.funcionario_id,
            cliente_id=r.cliente_id,
            data_hora=r.data_hora,
            valor_subtotal=float(r.valor_subtotal),
            desconto=float(r.desconto),
            acrescimo=float(r.acrescimo),
            valor_total_final=float(r.valor_total_final)
        ) for r in items
    ]

@router.get("/recebimento/{id}", response_model=RecebimentoResponse, tags=["Recebimento"])
@limiter.limit(get_rate_limit("moderate"))
async def get_recebimento(id: int, request: Request, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1, 3]))):
    result = await db.execute(select(RecebimentoDB).where(RecebimentoDB.id == id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Recebimento não encontrado")
    
    # Buscar comandas
    rc_result = await db.execute(select(RecebimentoComandaDB.comanda_id).where(RecebimentoComandaDB.recebimento_id == id))
    comanda_ids = rc_result.scalars().all()
    
    # Para simplicidade, retornamos as comandas vazias no response base
    return RecebimentoResponse(
        id=r.id,
        funcionario_id=r.funcionario_id,
        cliente_id=r.cliente_id,
        data_hora=r.data_hora,
        valor_subtotal=float(r.valor_subtotal),
        desconto=float(r.desconto),
        acrescimo=float(r.acrescimo),
        valor_total_final=float(r.valor_total_final)
    )

@router.put("/recebimento/{id}", response_model=RecebimentoResponse, tags=["Recebimento"])
@limiter.limit(get_rate_limit("restrictive"))
async def update_recebimento(
    id: int, 
    recebimento_data: RecebimentoCreate, 
    request: Request, 
    db: AsyncSession = Depends(get_async_db), 
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    result = await db.execute(select(RecebimentoDB).where(RecebimentoDB.id == id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Recebimento não encontrado")
    
    if recebimento_data.cliente_id is not None:
        r.cliente_id = recebimento_data.cliente_id
    
    r.desconto = recebimento_data.desconto
    r.acrescimo = recebimento_data.acrescimo
    r.valor_total_final = float(r.valor_subtotal) - recebimento_data.desconto + recebimento_data.acrescimo
    
    if r.valor_total_final < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor total não pode ser negativo")
    
    await db.commit()
    await db.refresh(r)
    
    return RecebimentoResponse(
        id=r.id,
        funcionario_id=r.funcionario_id,
        cliente_id=r.cliente_id,
        data_hora=r.data_hora,
        valor_subtotal=float(r.valor_subtotal),
        desconto=float(r.desconto),
        acrescimo=float(r.acrescimo),
        valor_total_final=float(r.valor_total_final)
    )

@router.delete("/recebimento/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Recebimento"])
@limiter.limit(get_rate_limit("critical"))
async def delete_recebimento(id: int, request: Request, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(require_group([1]))):
    # Apenas logamos que um recibo foi cancelado e devolvemos comandas para status 0
    # Na vida real, haveria estorno financeiro.
    result = await db.execute(select(RecebimentoDB).where(RecebimentoDB.id == id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Recebimento não encontrado")
    
    rc_result = await db.execute(select(RecebimentoComandaDB).where(RecebimentoComandaDB.recebimento_id == id))
    for rc in rc_result.scalars():
        c_res = await db.execute(select(ComandaDB).where(ComandaDB.id == rc.comanda_id))
        comanda = c_res.scalar_one_or_none()
        if comanda:
            comanda.status = 0
        await db.delete(rc)
    
    await db.delete(r)
    await db.commit()
