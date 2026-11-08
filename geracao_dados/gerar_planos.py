import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conexao = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conexao.cursor()

planos = [
    ('Free', 'mensal', 0.00, 3),
    ('Basic', 'mensal', 49.90, 10),
    ('Basic', 'anual', 499.00, 10),
    ('Pro', 'mensal', 149.90, 50),
    ('Pro', 'anual', 1499.00, 50),
    ('Enterprise', 'mensal', 499.90, None),
]

sql_insert = """
    INSERT INTO planos (nome_plano, periodicidade, preco, limite_usuarios)
    VALUES (%s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, planos)
#conexao.commit()

#print(f"{cursor.rowcount} planos inseridos no banco!")