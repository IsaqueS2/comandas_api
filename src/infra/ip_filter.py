from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class IPFilterMiddleware(BaseHTTPMiddleware):
    """
    Middleware opcional de allowlist de origens/IPs.

    - Quando CORS_ORIGINS == "*" (padrão), nenhum bloqueio é aplicado.
    - Quando CORS_ORIGINS contém domínios/IPs específicos, apenas requisições
      cuja origem (header Origin) ou IP cliente estejam na lista são aceitas.
      Essa verificação complementa o CORS do navegador com uma camada de
      bloqueio no próprio servidor, equivalente a um firewall de aplicação.

    Observação: em produção, essa função normalmente é delegada ao firewall
    de rede/infra. Use este middleware apenas quando não houver outra camada
    de proteção configurada.
    """

    def __init__(self, app, allowed_origins):
        super().__init__(app)
        # Se "*" presente ou lista vazia: libera tudo
        if (
            allowed_origins == "*"
            or (isinstance(allowed_origins, list) and ("*" in allowed_origins or not allowed_origins))
        ):
            self.allow_all = True
            self.allowed: set[str] = set()
        else:
            self.allow_all = False
            # Normaliza removendo barra final e espaços
            self.allowed = {o.strip().rstrip("/") for o in allowed_origins}

    async def dispatch(self, request: Request, call_next):
        if self.allow_all:
            return await call_next(request)

        # 1. Verifica header Origin (requisições de browsers)
        origin = request.headers.get("origin", "").rstrip("/")
        if origin and origin in self.allowed:
            return await call_next(request)

        # 2. Verifica IP do cliente (ferramentas como curl, Postman, serviços internos)
        client_ip = request.client.host if request.client else None

        # Respeita proxy reverso (nginx, load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        if client_ip and client_ip in self.allowed:
            return await call_next(request)

        return JSONResponse(
            status_code=403,
            content={"detail": "Acesso negado: origem não autorizada."},
        )
