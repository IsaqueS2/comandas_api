from domain.schemas.ProdutoSchema import ProdutoResponse
prod = ProdutoResponse(id=1, nome="Teste", descricao="Teste", foto="data:image/png;base64,iVBORw0KGgo=", valor_unitario=10.0)
print(prod.model_dump_json())
