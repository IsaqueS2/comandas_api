from passlib.context import CryptContext
import sqlite3

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
h = pwd_context.hash("123456")

conn = sqlite3.connect("apiDatabase.db")
conn.execute("UPDATE tb_funcionario SET senha=? WHERE matricula='1001'", (h,))
conn.commit()
print("Password updated")
