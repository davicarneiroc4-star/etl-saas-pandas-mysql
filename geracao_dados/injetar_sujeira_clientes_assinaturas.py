# JÁ EXECUTADO. Registro da sujeira aplicada em clientes e assinaturas. Não rodar de novo.
import mysql.connector
from faker import Faker
from dotenv import load_dotenv
import random
import os

load_dotenv()

conexao = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conexao.cursor()
fake = Faker('pt_BR')

resposta = input("Isto altera clientes e assinaturas. Digite SIM para continuar: ")

if resposta != "SIM":
    print("Cancelado. Nada foi alterado.")
    raise SystemExit

cursor.execute("ALTER TABLE clientes MODIFY email VARCHAR(100) NULL")

# 1) E-mails duplicados
cursor.execute("SELECT id_cliente, email FROM clientes WHERE email IS NOT NULL ORDER BY RAND() LIMIT 40")
sorteados = cursor.fetchall()
for i in range(0, 40, 2):
    cursor.execute("UPDATE clientes SET email = %s WHERE id_cliente = %s", (sorteados[i][1], sorteados[i + 1][0]))

# 2) E-mails vazios
cursor.execute("UPDATE clientes SET email = NULL ORDER BY RAND() LIMIT 40")

# 3) Nomes bagunçados
cursor.execute("UPDATE clientes SET nome_empresa = CONCAT('  ', nome_empresa, ' ') ORDER BY RAND() LIMIT 60")
cursor.execute("UPDATE clientes SET nome_empresa = UPPER(nome_empresa) ORDER BY RAND() LIMIT 60")
cursor.execute("UPDATE clientes SET nome_empresa = LOWER(nome_empresa) ORDER BY RAND() LIMIT 60")

# 4) Status das assinaturas
cursor.execute("UPDATE assinaturas SET status = 'ATIVA' WHERE status = 'ativa' ORDER BY RAND() LIMIT 40")
cursor.execute("UPDATE assinaturas SET status = 'Ativa' WHERE status = 'ativa' ORDER BY RAND() LIMIT 40")

conexao.commit()