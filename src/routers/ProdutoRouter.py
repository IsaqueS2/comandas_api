#ISAQUE DE OLIVEIRA DOS SANTOS

from fastapi import APIRouter, HTTPException
from domain.entities.Produto import Produto

router = APIRouter()


db_produtos = []

@router.get("/produto/", tags=["Produto"], status_code=200)
def get_produtos():
    return db_produtos 

@router.get("/produto/{id_prod}", tags=["Produto"], status_code=200)
def get_produto(id_prod: int):
 
    for p in db_produtos:
        if p.id_produto == id_prod:
            return p
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@router.post("/produto/", tags=["Produto"], status_code=200)
def post_produto(corpo: Produto):

    corpo.id_produto = len(db_produtos) + 1
    db_produtos.append(corpo)
    return {"msg": "Produto cadastrado com sucesso!", "produto": corpo}

@router.put("/produto/{id_prod}", tags=["Produto"], status_code=200)
def put_produto(id_prod: int, corpo: Produto):
    for i, p in enumerate(db_produtos):
        if p.id_produto == id_prod:
            corpo.id_produto = id_prod
            db_produtos[i] = corpo
            return {"msg": "Produto atualizado", "produto": corpo}
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@router.delete("/produto/{id_prod}", tags=["Produto"], status_code=200)
def delete_produto(id_prod: int):
    for i, p in enumerate(db_produtos):
        if p.id_produto == id_prod:
            db_produtos.pop(i)
            return {"msg": f"Produto {id_prod} removido"}
    raise HTTPException(status_code=404, detail="Produto não encontrado")