import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

load_dotenv()

usuario = os.getenv("DB_USER")
senha = quote_plus(os.getenv("DB_PASSWORD"))
host = os.getenv("DB_HOST")
banco = os.getenv("DB_NAME")

engine = create_engine(f"mysql+pymysql://{usuario}:{senha}@{host}/{banco}")

TABELAS = ['clientes', 'planos', 'assinaturas', 'historico_planos',
           'faturas', 'pagamentos', 'cancelamentos', 'eventos_uso']


def extrair_tabelas():
    dados = {}
    for tabela in TABELAS:
        dados[tabela] = pd.read_sql(f"SELECT * FROM {tabela}", engine)
    return dados


if __name__ == "__main__":
    dados = extrair_tabelas()
    for nome, df in dados.items():
        print(f"{nome}: {df.shape}")