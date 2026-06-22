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
    
    # Atualiza apenas os campos permitidos (desconto, acrescimo e valor_total_final)
    # Refazer o cálculo seria ideal, mas usaremos o que foi enviado para simplificar
    if recebimento_data.cliente_id is not None:
        r.cliente_id = recebimento_data.cliente_id
    
    # Atualiza valores financeiros
    r.desconto = recebimento_data.desconto
    r.acrescimo = recebimento_data.acrescimo
    r.valor_total_final = r.valor_subtotal - recebimento_data.desconto + recebimento_data.acrescimo
    
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
