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

cursor.execute("SELECT id_assinatura, data_fim FROM assinaturas WHERE status = 'cancelada'")
canceladas = cursor.fetchall()

motivos_voluntarios = ['preço alto', 'falta de recurso', 'migrou para concorrente', 'insatisfação com o suporte']

cancelamentos = []

for id_assinatura, data_fim in canceladas:
    tipo_cancelamento = random.choices(['voluntário', 'involuntário'], weights=[70, 30])[0]

    if tipo_cancelamento == 'voluntário':
        motivo_cancelamento = random.choice(motivos_voluntarios)
    else:
        motivo_cancelamento = 'falha de pagamento'

    cancelamentos.append((id_assinatura, data_fim, motivo_cancelamento, tipo_cancelamento))

print(f"{len(cancelamentos)} cancelamentos gerados na memória!")

sql_insert = """
    INSERT INTO cancelamentos (id_assinatura, data_cancelamento, motivo_cancelamento, tipo_cancelamento)
    VALUES (%s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, cancelamentos)
#conexao.commit()

#print(f"{cursor.rowcount} cancelamentos inseridos no banco!")