import pandas as pd


def transformar_clientes(df):
    df = df.copy()
    df.columns = df.columns.str.lower()

    df['nome_empresa'] = df['nome_empresa'].str.strip().str.title()

    df['email'] = df['email'].str.strip().str.lower()
    df['email_ausente'] = df['email'].isna()
    df['email_duplicado'] = df['email'].notna() & df['email'].duplicated(keep=False)

    df['status'] = df['status'].str.strip().str.lower()
    df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])

    return df


def transformar_planos(df):
    df = df.copy()
    df.columns = df.columns.str.lower()

    df['nome_plano'] = df['nome_plano'].str.strip()
    df['periodicidade'] = df['periodicidade'].str.strip().str.lower()

    return df


def transformar_assinaturas(df):
    df = df.copy()
    df.columns = df.columns.str.lower()

    df['status'] = df['status'].str.strip().str.lower()
    df['data_inicio'] = pd.to_datetime(df['data_inicio'])
    df['data_fim'] = pd.to_datetime(df['data_fim'])

    return df


def corrigir_valores_assinaturas(assinaturas, planos):
    precos = planos[['id_plano', 'preco']]

    df = assinaturas.merge(precos, on='id_plano', how='left')

    df['valor_divergente'] = df['valor_assinatura'].round(2) != df['preco'].round(2)
    df.loc[df['valor_divergente'], 'valor_assinatura'] = df['preco']
    df = df.drop(columns='preco')

    return df


def transformar_faturas(df):
    df = df.copy()
    df.columns = df.columns.str.lower()

    df['status_pagamento'] = df['status_pagamento'].str.strip().str.lower()

    df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])
    df['data_pagamento'] = pd.to_datetime(df['data_pagamento'])

    df['valor_negativo'] = df['valor_fatura'] < 0
    df['valor_fatura'] = df['valor_fatura'].abs()

    df['pago_sem_data'] = (df['status_pagamento'] == 'paga') & df['data_pagamento'].isna()
    df['pago_antes_vencimento'] = df['data_pagamento'] < df['data_vencimento']

    return df


def transformar_pagamentos(df):
    df = df.copy()
    df.columns = df.columns.str.lower()

    df['status_tentativa'] = df['status_tentativa'].str.strip().str.lower()
    df['data_tentativa'] = pd.to_datetime(df['data_tentativa'])

    return df


def corrigir_datas_faturas(faturas, pagamentos):
    sucesso = pagamentos[pagamentos['status_tentativa'] == 'sucesso']
    sucesso = sucesso[['id_fatura', 'data_tentativa']]
    sucesso = sucesso.rename(columns={'data_tentativa': 'data_confirmada'})

    df = faturas.merge(sucesso, on='id_fatura', how='left')

    precisa_corrigir = df['pago_sem_data'] | df['pago_antes_vencimento']
    df['data_corrigida'] = precisa_corrigir & df['data_confirmada'].notna()

    df.loc[df['data_corrigida'], 'data_pagamento'] = df['data_confirmada']
    df = df.drop(columns='data_confirmada')

    return df


if __name__ == "__main__":
    from extract import extrair_tabelas

    dados = extrair_tabelas()

    # ---------- FATURAS ----------
    faturas = transformar_faturas(dados['faturas'])
    pagamentos = transformar_pagamentos(dados['pagamentos'])
    faturas = corrigir_datas_faturas(faturas, pagamentos)

    print("FATURAS")
    print("Datas corrigidas:", faturas['data_corrigida'].sum())
    print("Linhas:", len(faturas))

    # ---------- ASSINATURAS ----------
    planos = transformar_planos(dados['planos'])
    assinaturas = transformar_assinaturas(dados['assinaturas'])
    linhas_antes = len(assinaturas)

    assinaturas = corrigir_valores_assinaturas(assinaturas, planos)

    conferencia = assinaturas.merge(planos[['id_plano', 'preco']], on='id_plano')
    divergentes_depois = (conferencia['valor_assinatura'].round(2) != conferencia['preco'].round(2)).sum()

    print()
    print("ASSINATURAS")
    print("Valores divergentes corrigidos:", assinaturas['valor_divergente'].sum())
    print("Divergentes depois da correção:", divergentes_depois)
    print("Linhas antes:", linhas_antes)
    print("Linhas depois:", len(assinaturas))