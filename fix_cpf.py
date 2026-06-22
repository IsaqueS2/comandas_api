import sqlite3
conn = sqlite3.connect('apiDatabase.db')
cursor = conn.cursor()
cursor.execute("UPDATE tb_funcionario SET cpf = REPLACE(REPLACE(cpf, '.', ''), '-', '')")
cursor.execute("UPDATE tb_cliente SET cpf = REPLACE(REPLACE(cpf, '.', ''), '-', '')")
conn.commit()
conn.close()
