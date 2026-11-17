import os

import pymysql
from dotenv import load_dotenv

load_dotenv()


def conectar():
    """Conexão com o MySQL usada pelos scripts de geração de dados (credenciais do .env)."""
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
