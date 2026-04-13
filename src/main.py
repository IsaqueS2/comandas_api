from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from infra import database
from infra.ip_filter import IPFilterMiddleware
from infra.rate_limit import limiter, rate_limit_exceeded_handler
from routers import (
    AuditoriaRouter,
    AuthRouter,
    ClienteRouter,
    ComandaRouter,
    FuncionarioRouter,
    HealthRouter,
    ProdutoRouter,

)
from settings import CORS_ORIGINS, HOST, PORT, RELOAD


@asynccontextmanager
async def lifespan(app: FastAPI):
    # executa no startup
    print("API has started")
    await database.cria_tabelas()
    yield
    # executa no shutdown
    print("API is shutting down")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False if "*" in CORS_ORIGINS else True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["*"],
    max_age=600,
)
# Adicionado por último = executado primeiro (camada mais externa).
# Bloqueia requisições de origens/IPs não listados em CORS_ORIGINS.
# Inativo quando CORS_ORIGINS="*" (padrão de desenvolvimento).
app.add_middleware(IPFilterMiddleware, allowed_origins=CORS_ORIGINS)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.get("/", tags=["Root"], status_code=200, summary="Informações da API - pública")
async def root():
    return {
        "detail": "API Comandas",
        "Swagger UI": "http://127.0.0.1:8000/docs",
        "ReDoc": "http://127.0.0.1:8000/redoc",
    }


app.include_router(AuditoriaRouter.router)
app.include_router(AuthRouter.router)
app.include_router(FuncionarioRouter.router)
app.include_router(ClienteRouter.router)
app.include_router(ProdutoRouter.router)
app.include_router(ComandaRouter.router)
app.include_router(HealthRouter.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=int(PORT), reload=RELOAD)
