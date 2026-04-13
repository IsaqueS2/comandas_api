from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from domain.schemas.AuthSchema import LoginRequest, TokenResponse, RefreshTokenRequest, FuncionarioAuth
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.database import get_async_db
from infra.security import verify_password, create_access_token, create_refresh_token, verify_refresh_token
from infra.dependencies import get_current_active_user
from infra.rate_limit import limiter, get_rate_limit
from settings import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from services.AuditoriaService import AuditoriaService

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse, tags=["Autenticação"], summary="Login de funcionário - pública - retorna access e refresh token")
@limiter.limit(get_rate_limit("critical"))
async def login(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_async_db)):
	try:
		result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.cpf == login_data.cpf))
		funcionario = result.scalars().first()
		if not funcionario:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="CPF ou senha inválidos", headers={"WWW-Authenticate": "Bearer"})
		if not verify_password(login_data.senha, funcionario.senha):
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="CPF ou senha inválidos", headers={"WWW-Authenticate": "Bearer"})

		access_token = create_access_token(
			data={"sub": funcionario.cpf, "id": funcionario.id, "grupo": funcionario.grupo},
			expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
		)
		refresh_token = create_refresh_token(
			data={"sub": funcionario.cpf, "id": funcionario.id, "grupo": funcionario.grupo},
		)
		token_response = TokenResponse(
			access_token=access_token,
			refresh_token=refresh_token,
			token_type="bearer",
			expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
			refresh_expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
		)
		await AuditoriaService.registrar_acao(db=db, funcionario_id=funcionario.id, acao="LOGIN", recurso="auth", recurso_id=funcionario.id, request=request)
		return token_response
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao realizar login: {str(e)}")


@router.post("/auth/refresh", response_model=TokenResponse, tags=["Autenticação"], summary="Refresh token - pública - renova access token")
@limiter.limit(get_rate_limit("critical"))
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
	try:
		payload = verify_refresh_token(refresh_data.refresh_token)
		cpf = payload.get("sub")
		result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.cpf == cpf))
		funcionario = result.scalars().first()
		if not funcionario:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Funcionário não encontrado", headers={"WWW-Authenticate": "Bearer"})

		access_token = create_access_token(
			data={"sub": funcionario.cpf, "id": funcionario.id, "grupo": funcionario.grupo},
			expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
		)
		new_refresh_token = create_refresh_token(
			data={"sub": funcionario.cpf, "id": funcionario.id, "grupo": funcionario.grupo},
		)
		token_response = TokenResponse(
			access_token=access_token,
			refresh_token=new_refresh_token,
			token_type="bearer",
			expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
			refresh_expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
		)
		await AuditoriaService.registrar_acao(db=db, funcionario_id=funcionario.id, acao="REFRESH_TOKEN", recurso="auth", recurso_id=funcionario.id, request=request)
		return token_response
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Erro ao renovar token: {str(e)}", headers={"WWW-Authenticate": "Bearer"})


@router.get("/auth/me", response_model=FuncionarioAuth, tags=["Autenticação"], summary="Dados do usuário atual - protegida por autenticação")
@limiter.limit(get_rate_limit("moderate"))
async def get_current_user_info(request: Request, current_user: FuncionarioAuth = Depends(get_current_active_user)):
	return current_user


@router.post("/auth/logout", tags=["Autenticação"], summary="Logout - protegida por autenticação")
@limiter.limit(get_rate_limit("critical"))
async def logout(request: Request, db: AsyncSession = Depends(get_async_db), current_user: FuncionarioAuth = Depends(get_current_active_user)):
	await AuditoriaService.registrar_acao(db=db, funcionario_id=current_user.id, acao="LOGOUT", recurso="auth", recurso_id=current_user.id, request=request)
	return {"message": "Logout realizado com sucesso"}
