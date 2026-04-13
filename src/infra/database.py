from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from settings import ASYNC_STR_DATABASE, STR_DATABASE

# engine síncrono (usado em migrations e scripts)
engine = create_engine(STR_DATABASE, echo=True)
# engine assíncrono (usado pelas rotas da API)
async_engine = create_async_engine(ASYNC_STR_DATABASE, echo=True)

# sessão síncrona (mantida para scripts/migrations)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=True)
# sessão assíncrona
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# para trabalhar com tabelas
Base = declarative_base()


# cria, caso não existam, as tabelas de todos os modelos que encontrar na aplicação (importados)
async def cria_tabelas():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# importa modelos para garantir montagem de tabela no startup
from infra.orm import ClienteModel, FuncionarioModel, ProdutoModel, ProdutoPrecoHistoricoModel


# dependência para injetar a sessão síncrona nas rotas
def get_db():
    db_session = Session()
    try:
        yield db_session
    finally:
        db_session.close()


# dependência para injetar a sessão assíncrona nas rotas
async def get_async_db():
    async with AsyncSessionLocal() as db_session:
        yield db_session
