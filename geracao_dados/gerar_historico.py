from conexao import conectar
from faker import Faker
import random

conexao = conectar()

cursor = conexao.cursor()
fake = Faker('pt_BR')

cursor.execute("SELECT id_cliente FROM clientes")
ids_clientes = [linha[0] for linha in cursor.fetchall()]

cursor.execute("SELECT id_plano FROM planos")
ids_planos = [linha[0] for linha in cursor.fetchall()]

historico = []

for i in range(300):
    id_cliente = random.choice(ids_clientes)
    id_plano_anterior = random.choice(ids_planos)
    id_plano_novo = random.choice(ids_planos)

    while id_plano_novo == id_plano_anterior:
        id_plano_novo = random.choice(ids_planos)

    data_alteracao = fake.date_between(start_date='-2y', end_date='today')

    tipo_alteracao = 'upgrade' if id_plano_novo > id_plano_anterior else 'downgrade'

    historico.append((id_cliente, id_plano_anterior, id_plano_novo, data_alteracao, tipo_alteracao))

print(f"{len(historico)} registros de histórico gerados na memória!")

sql_insert = """
    INSERT INTO historico_planos (id_cliente, id_plano_anterior, id_plano_novo, data_alteracao, tipo_alteracao)
    VALUES (%s, %s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, historico)
#conexao.commit()

#print(f"{cursor.rowcount} registros de histórico inseridos no banco!")