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

#Busca os IDs que já existem no banco

cursor.execute("SELECT id_cliente FROM clientes")
ids_clientes = [linha[0] for linha in cursor.fetchall()]

cursor.execute("SELECT id_plano, preco FROM planos")
planos_precos = {linha[0]: linha[1] for linha in cursor.fetchall()}
ids_planos = list(planos_precos.keys())

print(f"Encontrados {len(ids_clientes)} clientes e {len(ids_planos)} planos")

assinaturas = []
fake = Faker('pt_BR')

for i in range(700):
    id_cliente = random.choice(ids_clientes)
    id_plano = random.choice(ids_planos)

    data_inicio = fake.date_between(start_date='-2y', end_date='-1m')

    status = random.choices(
        ['ativa', 'cancelada', 'trial'],
        weights=[60, 30, 10]
    )[0]

    if status == 'cancelada':
        data_fim = fake.date_between(start_date=data_inicio, end_date='today')
    else:
        data_fim = None

    if random.random() < 0.9:
        valor_assinatura = planos_precos[id_plano]
    else:
        valor_assinatura = round(random.uniform(0, 500), 2)

    assinaturas.append((id_cliente, id_plano, valor_assinatura, data_inicio, data_fim, status))

print(f"{len(assinaturas)} assinaturas geradas na memória!")

sql_insert = """
    INSERT INTO assinaturas (id_cliente, id_plano, valor_assinatura, data_inicio, data_fim, status)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, assinaturas)
#conexao.commit()

#print(f"{cursor.rowcount} assinaturas inseridas no banco!")