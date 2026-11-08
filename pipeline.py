import os
import pandas as pd

from extract import extrair_tabelas, engine
from transform import (
    transformar_clientes,
    transformar_planos,
    transformar_assinaturas,
    corrigir_valores_assinaturas,
    transformar_faturas,
    transformar_pagamentos,
    corrigir_datas_faturas,
)

PASTA_SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_limpos")


def transformar_tudo(dados):
    clientes = transformar_clientes(dados['clientes'])
    planos = transformar_planos(dados['planos'])

    assinaturas = transformar_assinaturas(dados['assinaturas'])
    assinaturas = corrigir_valores_assinaturas(assinaturas, planos)

    pagamentos = transformar_pagamentos(dados['pagamentos'])
    faturas = transformar_faturas(dados['faturas'])
    faturas = corrigir_datas_faturas(faturas, pagamentos)

    historico = dados['historico_planos'].copy()
    historico.columns = historico.columns.str.lower()
    historico['tipo_alteracao'] = historico['tipo_alteracao'].str.strip().str.lower()
    historico['data_alteracao'] = pd.to_datetime(historico['data_alteracao'])

    cancelamentos = dados['cancelamentos'].copy()
    cancelamentos.columns = cancelamentos.columns.str.lower()
    cancelamentos['data_cancelamento'] = pd.to_datetime(cancelamentos['data_cancelamento'])

    eventos = dados['eventos_uso'].copy()
    eventos.columns = eventos.columns.str.lower()
    eventos['data_evento'] = pd.to_datetime(eventos['data_evento'])

    return {
        'clientes': clientes,
        'planos': planos,
        'assinaturas': assinaturas,
        'historico_planos': historico,
        'faturas': faturas,
        'pagamentos': pagamentos,
        'cancelamentos': cancelamentos,
        'eventos_uso': eventos,
    }


def carregar_csv(tabelas):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    for nome, df in tabelas.items():
        df.to_csv(os.path.join(PASTA_SAIDA, f"{nome}.csv"), index=False)


def carregar_mysql(tabelas):
    for nome, df in tabelas.items():
        df.to_sql(f"{nome}_limpo", engine, if_exists="replace", index=False, chunksize=1000)


if __name__ == "__main__":
    print("1/3 EXTRACT: lendo as tabelas do MySQL...")
    dados = extrair_tabelas()

    print("2/3 TRANSFORM: limpando e corrigindo...")
    tabelas = transformar_tudo(dados)

    print("3/3 LOAD: salvando o resultado...")
    carregar_csv(tabelas)
    carregar_mysql(tabelas)

    print()
    for nome, df in tabelas.items():
        print(f"{nome}: {df.shape[0]} linhas, {df.shape[1]} colunas")

    print()
    print("Pipeline concluído!")