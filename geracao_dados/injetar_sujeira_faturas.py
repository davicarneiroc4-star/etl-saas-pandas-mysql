#ja foi executado, nao executar novamente

from conexao import conectar
from faker import Faker
import random

conexao = conectar()

cursor = conexao.cursor()
fake = Faker('pt_BR')

resposta = input("Isto altera as faturas de forma permanente. Digite SIM para continuar: ")

if resposta != "SIM":
    print("Cancelado. Nada foi alterado.")
    raise SystemExit

# 1) Status com maiúscula
cursor.execute("UPDATE faturas SET status_pagamento = 'Paga' WHERE status_pagamento = 'paga' ORDER BY RAND() LIMIT 60")
print("Status com maiúscula:", cursor.rowcount)

# 2) Pagas sem data de pagamento
cursor.execute("UPDATE faturas SET data_pagamento = NULL WHERE status_pagamento = 'paga' ORDER BY RAND() LIMIT 50")
print("Pagas sem data:", cursor.rowcount)

# 3) Valores negativos
cursor.execute("UPDATE faturas SET valor_fatura = -valor_fatura ORDER BY RAND() LIMIT 25")
print("Valores negativos:", cursor.rowcount)

# 4) Pagamento antes do vencimento
cursor.execute("""
    UPDATE faturas
    SET data_pagamento = DATE_SUB(data_vencimento, INTERVAL 10 DAY)
    WHERE status_pagamento = 'paga' AND data_pagamento IS NOT NULL
    ORDER BY RAND() LIMIT 30
""")
print("Pagamento antes do vencimento:", cursor.rowcount)

conexao.commit()
print("Sujeira injetada com sucesso!")