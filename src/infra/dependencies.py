from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database import get_async_db
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.security import verify_access_token

from domain.schemas.AuthSchema import FuncionarioAuth

# Scheme para extrair token do header Authorization: Bearer <token>
security = HTTPBearer()

# Dependency para validar token e retornar usuário atual
async def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: AsyncSession = Depends(get_async_db),
) -> FuncionarioAuth:
	"""Dependency que valida o token e retorna o usuário atual"""
	payload = verify_access_token(credentials.credentials)
	cpf: str = payload.get("sub")
	id_funcionario: int = payload.get("id")
	if cpf is None or id_funcionario is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Token inválido - dados incompletos",
			headers={"WWW-Authenticate": "Bearer"},
		)
	result = await db.execute(select(FuncionarioDB).where(FuncionarioDB.id == id_funcionario))
	funcionario = result.scalars().first()
	if not funcionario:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Funcionário não encontrado",
			headers={"WWW-Authenticate": "Bearer"},
		)
	if funcionario.cpf != cpf:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Token inválido - CPF não corresponde",
			headers={"WWW-Authenticate": "Bearer"},
		)
	return FuncionarioAuth(
		id=funcionario.id,
		nome=funcionario.nome,
		matricula=funcionario.matricula,
		cpf=funcionario.cpf,
		grupo=funcionario.grupo,
	)

# Dependency para verificar se o usuário está ativo
async def get_current_active_user(
	current_user: FuncionarioAuth = Depends(get_current_user),
) -> FuncionarioAuth:
	return current_user

# Dependency para verificar se o usuário tem um grupo específico
def require_group(group_required: list[int] = None):
	"""
	Factory function que cria dependency para verificar grupo do usuário.
	- list[int]: permite somente esses grupos
	- None: qualquer usuário autenticado
	"""
	async def check_group(
		current_user: FuncionarioAuth = Depends(get_current_active_user),
	) -> FuncionarioAuth:
		if group_required is None:
			return current_user
		if current_user.grupo not in group_required:
			groups_str = ", ".join(map(str, group_required))
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail=f"Permissão negada - requerido um dos grupos: {groups_str}",
			)
		return current_user
	return check_group
