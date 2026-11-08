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

# Geração dos dados
fake = Faker('pt_BR')

segmentos = ['Varejo', 'Saúde', 'Educação', 'Tecnologia', 'Financeiro', 'Logística']
tamanhos = ['Pequena', 'Média', 'Grande']
estados = ['SP', 'RJ', 'MG', 'PA', 'BA', 'RS', 'PR', 'SC', 'CE', 'PE']

clientes = []

for i in range(600):
    nome_empresa = fake.company()
    email = fake.company_email()
    segmento = random.choice(segmentos)
    tamanho_empresa = random.choice(tamanhos)
    estado = random.choice(estados)
    data_cadastro = fake.date_between(start_date='-3y', end_date='today')
    status = random.choice(['ativo', 'trial', 'cancelado'])

    clientes.append((nome_empresa, email, segmento, tamanho_empresa, estado, data_cadastro, status))

print(f"{len(clientes)} clientes gerados na memória!")


#SQL Insert
sql_insert = """
    INSERT INTO clientes (nome_empresa, email, segmento, tamanho_empresa, estado, data_cadastro, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, clientes)
#conexao.commit()

#print(f"{cursor.rowcount} clientes inseridos no banco!")