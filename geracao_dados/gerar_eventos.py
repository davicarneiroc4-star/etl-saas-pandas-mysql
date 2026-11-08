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

cursor.execute("SELECT id_cliente, data_cadastro FROM clientes")
clientes_info = cursor.fetchall()

tipos_evento = ['login', 'criou_relatorio', 'exportou_dados', 'convidou_usuario', 'usou_integracao', 'abriu_suporte']
pesos_evento = [50, 20, 10, 8, 8, 4]

eventos = []

for i in range(16000):
    id_cliente, data_cadastro = random.choice(clientes_info)

    tipo_evento = random.choices(tipos_evento, weights=pesos_evento)[0]
    data_evento = fake.date_time_between(start_date=data_cadastro, end_date='now')

    eventos.append((id_cliente, tipo_evento, data_evento))

print(f"{len(eventos)} eventos gerados na memória!")

sql_insert = """
    INSERT INTO eventos_uso (id_cliente, tipo_evento, data_evento)
    VALUES (%s, %s, %s)
"""

#cursor.executemany(sql_insert, eventos)
#conexao.commit()

#print(f"{cursor.rowcount} eventos inseridos no banco!")