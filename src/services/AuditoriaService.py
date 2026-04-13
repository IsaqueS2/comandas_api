from datetime import datetime
from typing import Any, Dict, Optional
import json

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from infra.orm.AuditoriaModel import AuditoriaDB


class AuditoriaService:
	"""Serviço para registrar auditoria de acessos e ações"""

	@staticmethod
	async def registrar_acao(
		db: AsyncSession,
		funcionario_id: int,
		acao: str,
		recurso: str,
		recurso_id: Optional[int] = None,
		dados_antigos: Optional[Dict[str, Any]] = None,
		dados_novos: Optional[Dict[str, Any]] = None,
		request: Optional[Request] = None,
	) -> bool:
		try:
			ip_address = None
			user_agent = None

			if request:
				forwarded_for = request.headers.get("X-Forwarded-For")
				if forwarded_for:
					ip_address = forwarded_for.split(",")[0].strip()
				else:
					ip_address = request.client.host
				user_agent = request.headers.get("User-Agent")

			def _serialize(obj):
				if obj is None:
					return None
				if hasattr(obj, "__table__"):
					return json.dumps(
						{col.name: getattr(obj, col.name) for col in obj.__table__.columns},
						default=str,
					)
				return json.dumps(obj, default=str)

			auditoria = AuditoriaDB(
				funcionario_id=funcionario_id,
				acao=acao,
				recurso=recurso,
				recurso_id=recurso_id,
				dados_antigos=_serialize(dados_antigos),
				dados_novos=_serialize(dados_novos),
				ip_address=ip_address,
				user_agent=user_agent,
				data_hora=datetime.now(),
			)
			db.add(auditoria)
			await db.commit()
			return True
		except Exception:
			await db.rollback()
			return False
