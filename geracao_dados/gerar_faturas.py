import mysql.connector
from faker import Faker
from dotenv import load_dotenv
from datetime import date, timedelta
import random
import os
from dateutil.relativedelta import relativedelta
load_dotenv()

conexao = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conexao.cursor()
fake = Faker('pt_BR')

cursor.execute("SELECT id_assinatura, data_inicio, data_fim, status FROM assinaturas")
assinaturas_info = cursor.fetchall()

faturas = []
total_assinaturas = len(assinaturas_info)

for indice, (id_assinatura, data_inicio, data_fim, status) in enumerate(assinaturas_info):
    if indice % 50 == 0:
        print(f"Processando assinatura {indice} de {total_assinaturas}...")

    data_final_cobranca = data_fim if data_fim else fake.date_between(start_date=data_inicio, end_date='today')

    data_fatura = data_inicio
    while data_fatura <= data_final_cobranca:
        valor_fatura = round(random.uniform(20, 500), 2)

        status_pagamento = random.choices(
            ['paga', 'atrasada', 'pendente'],
            weights=[85, 10, 5]
        )[0]

        if status_pagamento == 'paga':
            limite_pagamento = min(data_fatura + timedelta(days=5), date.today())
            if limite_pagamento < data_fatura:
                limite_pagamento = data_fatura
            data_pagamento = fake.date_between(start_date=data_fatura, end_date=limite_pagamento)
        else:
            data_pagamento = None

        faturas.append((id_assinatura, valor_fatura, data_fatura, data_pagamento, status_pagamento))

        data_fatura = data_fatura + relativedelta(months=1)


print(f"{len(faturas)} faturas geradas na memória!")

sql_insert = """
    INSERT INTO faturas (id_assinatura, valor_fatura, data_vencimento, data_pagamento, status_pagamento)
    VALUES (%s, %s, %s, %s, %s)
"""

#cursor.executemany(sql_insert, faturas)
#conexao.commit()

#print(f"{cursor.rowcount} faturas inseridas no banco!")