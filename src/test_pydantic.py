import base64
from domain.schemas.ProdutoSchema import ProdutoResponse
from pydantic import ValidationError

try:
    # Simula o banco retornando uma string com o prefixo
    data = "data:image/png;base64,iVBORw0KGgo="
    prod = ProdutoResponse(id=1, nome="Teste", descricao="Teste", foto=data, valor_unitario=10.0)
    print("Sucesso com string!")
    print(prod.foto)
except ValidationError as e:
    print("Erro com string:", e)

try:
    # Simula o banco retornando bytes puros
    data_bytes = b"data:image/png;base64,iVBORw0KGgo="
    prod = ProdutoResponse(id=1, nome="Teste", descricao="Teste", foto=data_bytes, valor_unitario=10.0)
    print("Sucesso com bytes!")
    print(prod.foto)
except ValidationError as e:
    print("Erro com bytes:", e)
