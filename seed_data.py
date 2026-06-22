import sqlite3
import datetime
import bcrypt

def get_password_hash(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_data():
    conn = sqlite3.connect('apiDatabase.db')
    cursor = conn.cursor()

    try:
        # Senha padrão para os funcionários criados
        hashed_password = get_password_hash("123456")
        
        # Inserir Funcionários
        funcionarios = [
            ("Isaque", "1001", "123.456.789-01", "(11) 98888-1111", 1, hashed_password),
            ("Carlos Gerente", "1002", "123.456.789-02", "(11) 98888-2222", 1, hashed_password),
            ("Maria Garçonete", "1003", "123.456.789-03", "(11) 98888-3333", 2, hashed_password),
            ("João Caixa", "1004", "123.456.789-04", "(11) 98888-4444", 3, hashed_password)
        ]
        
        cursor.executemany('''
            INSERT INTO tb_funcionario (nome, matricula, cpf, telefone, grupo, senha)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', funcionarios)
        
        # Pega IDs dos funcionários
        cursor.execute("SELECT id, nome FROM tb_funcionario")
        func_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Inserir Clientes
        clientes = [
            ("Isaque Cliente", "111.222.333-44", "(11) 97777-1111"),
            ("Ana Souza", "222.333.444-55", "(11) 97777-2222"),
            ("Pedro Santos", "333.444.555-66", "(11) 97777-3333")
        ]
        
        cursor.executemany('''
            INSERT INTO tb_cliente (nome, cpf, telefone)
            VALUES (?, ?, ?)
        ''', clientes)
        
        # Pega IDs dos clientes
        cursor.execute("SELECT id, nome FROM tb_cliente")
        cli_map = {row[1]: row[0] for row in cursor.fetchall()}

        # Inserir Produtos
        produtos = [
            ("Hambúrguer Artesanal", "Pão brioche, blend 180g, queijo cheddar, bacon e cebola caramelizada", "", 35.90),
            ("Pizza Calabresa", "Pizza média com muita calabresa, cebola e queijo mussarela", "", 45.00),
            ("Suco de Laranja", "Copo 500ml de suco natural da fruta sem açúcar", "", 12.00),
            ("Coca-Cola Lata", "Lata 350ml gelada", "", 6.50),
            ("Porção de Fritas", "Batatas fritas rústicas acompanhadas de maionese temperada", "", 25.00)
        ]
        
        cursor.executemany('''
            INSERT INTO tb_produto (nome, descricao, foto, valor_unitario)
            VALUES (?, ?, ?, ?)
        ''', produtos)
        
        # Pega IDs dos produtos
        cursor.execute("SELECT id, nome, valor_unitario FROM tb_produto")
        prod_map = {row[1]: (row[0], row[2]) for row in cursor.fetchall()}

        # Inserir Comandas Abertas
        now = datetime.datetime.now()
        
        comandas = [
            # 1: Comanda do Isaque
            ("COM-100", now, 0, cli_map["Isaque Cliente"], func_map["Maria Garçonete"]),
            # 2: Comanda da Ana
            ("COM-101", now, 0, cli_map["Ana Souza"], func_map["Isaque"]),
            # 3: Comanda Avulsa sem cliente
            ("COM-102", now, 0, None, func_map["Maria Garçonete"])
        ]
        
        cursor.executemany('''
            INSERT INTO tb_comanda (comanda, data_hora, status, cliente_id, funcionario_id)
            VALUES (?, ?, ?, ?, ?)
        ''', comandas)
        
        # Pega as comandas inseridas
        cursor.execute("SELECT id, comanda FROM tb_comanda WHERE status = 0")
        com_map = {row[1]: row[0] for row in cursor.fetchall()}

        # Inserir Produtos nas Comandas
        comanda_produtos = [
            # Produtos na comanda COM-100 (Isaque)
            (com_map["COM-100"], prod_map["Hambúrguer Artesanal"][0], func_map["Maria Garçonete"], 2, prod_map["Hambúrguer Artesanal"][1]),
            (com_map["COM-100"], prod_map["Coca-Cola Lata"][0], func_map["Maria Garçonete"], 2, prod_map["Coca-Cola Lata"][1]),
            
            # Produtos na comanda COM-101 (Ana)
            (com_map["COM-101"], prod_map["Pizza Calabresa"][0], func_map["Isaque"], 1, prod_map["Pizza Calabresa"][1]),
            (com_map["COM-101"], prod_map["Suco de Laranja"][0], func_map["Isaque"], 2, prod_map["Suco de Laranja"][1]),
            
            # Produtos na comanda COM-102 (Avulsa)
            (com_map["COM-102"], prod_map["Porção de Fritas"][0], func_map["Maria Garçonete"], 1, prod_map["Porção de Fritas"][1])
        ]
        
        cursor.executemany('''
            INSERT INTO tb_comanda_produto (comanda_id, produto_id, funcionario_id, quantidade, valor_unitario)
            VALUES (?, ?, ?, ?, ?)
        ''', comanda_produtos)

        conn.commit()
        print("Dados inseridos com sucesso!")

    except Exception as e:
        print("Erro ao inserir dados:", e)
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
