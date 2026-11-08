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

cursor.execute("SELECT id_fatura, data_vencimento, data_pagamento, status_pagamento FROM faturas")
faturas_info = cursor.fetchall()

metodos = ['cartão de crédito', 'boleto', 'pix']
motivos_falha = ['cartão recusado', 'saldo insuficiente', 'cartão expirado']

pagamentos = []

for id_fatura, data_vencimento, data_pagamento, status_fatura in faturas_info:
    if status_fatura == 'pendente':
        continue

    if status_fatura == 'paga':
        qtd_falhas = random.choices([0, 1, 2], weights=[80, 15, 5])[0]
    else:
        qtd_falhas = random.randint(1, 3)

    for tentativa in range(qtd_falhas):
        pagamentos.append((
            id_fatura,
            random.choice(metodos),
            data_vencimento,
            'falha',
            random.choice(motivos_falha)
        ))

    if status_fatura == 'paga':
        pagamentos.append((
            id_fatura,
            random.choice(metodos),
            data_pagamento,
            'sucesso',
            None
        ))

print(f"{len(pagamentos)} pagamentos gerados na memória!")

sql_insert = """
    INSERT INTO pagamentos (id_fatura, metodo_pagamento, data_tentativa, status_tentativa, motivo_falha)
    VALUES (%s, %s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, pagamentos)
#conexao.commit()

#print(f"{cursor.rowcount} pagamentos inseridos no banco!")