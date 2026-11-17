"""Ferramentas que o agente pode chamar.

Tudo roda em cima dos CSVs de dados_limpos/ (saída do pipeline ETL), então
o assistente funciona sem o MySQL ligado. As métricas reaproveitam as mesmas
regras de metricas.py e churn_ltv.py.
"""
import os
import sys

import duckdb
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from churn_ltv import calcular_churn_mensal, calcular_ltv, periodo_analise, preparar_dados, valor_mensal  # noqa: E402

PASTA_DADOS = os.path.join(RAIZ, 'dados_limpos')
TABELAS = ['clientes', 'planos', 'assinaturas', 'historico_planos',
           'faturas', 'pagamentos', 'cancelamentos', 'eventos_uso']
LIMITE_LINHAS = 100

_dados = {t: pd.read_csv(os.path.join(PASTA_DADOS, f'{t}.csv')) for t in TABELAS}

# Banco DuckDB em memória, só para as consultas SQL do agente
_con = duckdb.connect()
for _nome, _df in _dados.items():
    _con.register('_tmp', _df)
    _con.execute(f'CREATE TABLE {_nome} AS SELECT * FROM _tmp')
    _con.unregister('_tmp')
# Visão pronta com o MRR de cada assinatura, para recortes por segmento, estado etc.
# Mesma regra de churn_ltv.valor_mensal (SQL não chama Python): se a regra mudar, mudar aqui também.
_con.execute("""
    CREATE VIEW mrr_assinaturas AS
    SELECT a.id_assinatura, a.id_cliente, a.status, p.nome_plano, p.periodicidade,
           CASE WHEN p.periodicidade = 'anual' THEN a.valor_assinatura / 12 ELSE a.valor_assinatura END AS valor_mensal
    FROM assinaturas a JOIN planos p USING (id_plano)
""")
# Depois de carregar, bloqueia acesso a arquivos e rede e trava a configuração
_con.execute('SET enable_external_access = false')
_con.execute('SET lock_configuration = true')

_df_pagas = preparar_dados(_dados['assinaturas'], _dados['planos'], _dados['cancelamentos'])
_meses, _janela = periodo_analise(_df_pagas)


def _registros(df):
    """DataFrame -> lista de dicionários com tipos simples (o modelo recebe JSON)."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].round(4)
        elif not pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype(str)
    return df.to_dict(orient='records')


def _em_porcentagem(df, colunas):
    """Troca frações (0.0389) por percentuais já arredondados (3.9) em colunas *_pct,
    para o modelo não precisar fazer conta nem arredondar."""
    df = df.copy()
    for col in colunas:
        df[f'{col}_pct'] = (df.pop(col) * 100).round(1)
    return df


def _valores_possiveis(tabela, coluna):
    """Valores distintos de uma coluna de texto, se forem poucos (status, plano, segmento...)."""
    valores = _con.cursor().execute(f'SELECT DISTINCT "{coluna}" FROM {tabela} WHERE "{coluna}" IS NOT NULL LIMIT 16').fetchall()
    return sorted(v[0] for v in valores) if len(valores) <= 15 else None


def descrever_tabelas() -> dict:
    """Lista as tabelas do banco SaaS (dados sintéticos): colunas, tipos, número de linhas e, nas colunas de texto
    com poucos valores, a lista exata de valores (use esses valores, com as mesmas letras, nos filtros SQL).
    Inclui a visão mrr_assinaturas, com o valor mensal (MRR) de cada assinatura já calculado.
    Use antes de escrever uma consulta SQL."""
    cur = _con.cursor()
    descricao = cur.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns ORDER BY table_name, ordinal_position"
    ).df()
    resultado = {}
    for tabela, grupo in descricao.groupby('table_name'):
        colunas = {}
        for coluna, tipo in zip(grupo['column_name'], grupo['data_type']):
            info = {'tipo': tipo}
            if tipo == 'VARCHAR':
                valores = _valores_possiveis(tabela, coluna)
                if valores:
                    info['valores'] = valores
            colunas[coluna] = info
        linhas = cur.execute(f'SELECT COUNT(*) FROM {tabela}').fetchone()[0]
        resultado[tabela] = {'linhas': linhas, 'colunas': colunas}
    resultado['mrr_assinaturas']['observacao'] = (
        "MRR por assinatura já normalizado (anual / 12). Para MRR atual por qualquer recorte, "
        "filtre status = 'ativa' e some valor_mensal.")
    return resultado


def consultar_sql(consulta: str) -> dict:
    """Executa UMA consulta SQL somente leitura (SELECT ou WITH, dialeto DuckDB) nas tabelas do banco SaaS.
    Retorna no máximo 100 linhas. Use para perguntas que as outras ferramentas não respondem.

    Args:
        consulta: a consulta SQL, por exemplo "SELECT segmento, COUNT(*) AS clientes FROM clientes GROUP BY segmento".
    """
    sql = consulta.strip()
    cur = _con.cursor()  # um cursor por chamada: a conexão não aceita duas consultas ao mesmo tempo
    try:
        # O parser do DuckDB diz o tipo real do comando (pega "WITH ... DELETE", que começa com WITH)
        if [s.type for s in cur.extract_statements(sql)] != [duckdb.StatementType.SELECT]:
            return {'erro': 'Só é permitida UMA consulta de leitura (SELECT).'}
        cur.execute(sql)
        # fetchmany não monta o resultado inteiro na memória (um JOIN sem filtro pode ter milhões de linhas)
        linhas = cur.fetchmany(LIMITE_LINHAS + 1)
    except duckdb.Error as e:
        return {'erro': str(e)}
    resultado = pd.DataFrame(linhas[:LIMITE_LINHAS], columns=[c[0] for c in cur.description])
    return {
        'consulta': sql,
        'linhas': _registros(resultado),
        'cortado': len(linhas) > LIMITE_LINHAS,
    }


def calcular_mrr() -> dict:
    """Calcula o MRR (receita recorrente mensal) atual, total e por plano.
    Regra: soma do valor mensal das assinaturas ativas; plano anual conta 1/12 do valor por mês."""
    df = _dados['assinaturas'].merge(_dados['planos'][['id_plano', 'nome_plano', 'periodicidade']], on='id_plano', how='left')
    df['valor_mensal'] = valor_mensal(df)
    ativas = df[df['status'] == 'ativa']
    por_plano = ativas.groupby('nome_plano')['valor_mensal'].agg(['sum', 'count']).sort_values('sum', ascending=False)
    return {
        'mrr_total': round(float(ativas['valor_mensal'].sum()), 2),
        'assinaturas_ativas': int(len(ativas)),
        'por_plano': [
            {'plano': p, 'mrr': round(float(v['sum']), 2), 'assinaturas_ativas': int(v['count'])}
            for p, v in por_plano.iterrows()
        ],
    }


def churn_mensal(mes_inicial: str = '', mes_final: str = '') -> dict:
    """Churn mês a mês das assinaturas pagas (sem trial e sem plano Free): ativas no dia 1º, canceladas no mês
    (voluntárias e involuntárias), churn de clientes e churn de receita. Inclui o churn médio dos últimos 12 meses.

    Args:
        mes_inicial: primeiro mês no formato AAAA-MM (vazio = início da série).
        mes_final: último mês no formato AAAA-MM (vazio = último mês com dados).
    """
    churn = calcular_churn_mensal(_df_pagas, _meses)
    try:
        if mes_inicial:
            churn = churn[churn.index >= pd.Period(mes_inicial, freq='M')]
        if mes_final:
            churn = churn[churn.index <= pd.Period(mes_final, freq='M')]
    except ValueError:
        return {'erro': 'Use meses no formato AAAA-MM, por exemplo 2025-03.'}

    janela = calcular_churn_mensal(_df_pagas, _janela)
    tabela = churn.reset_index()
    tabela['mes'] = tabela['mes'].astype(str)
    tabela = _em_porcentagem(tabela, ['churn_clientes', 'churn_receita'])
    return {
        'periodo_disponivel': f'{_meses[0]} a {_meses[-1]}',
        'meses': _registros(tabela),
        'media_ultimos_12_meses': {
            'periodo': f'{_janela[0]} a {_janela[-1]}',
            'churn_clientes_pct': round(float(janela['canceladas'].sum() / janela['ativas_inicio'].sum()) * 100, 1),
            'churn_receita_pct': round(float(janela['mrr_perdido'].sum() / janela['mrr_inicio'].sum()) * 100, 1),
        },
    }


def ltv_por_plano() -> dict:
    """LTV (receita média que uma assinatura paga gera durante toda a vida) por plano e geral,
    com ticket mensal, churn mensal e vida média, usando a janela dos últimos 12 meses."""
    ltv = _em_porcentagem(calcular_ltv(_df_pagas, _janela).reset_index(), ['churn_mensal'])
    ltv[['ticket_mensal', 'ltv']] = ltv[['ticket_mensal', 'ltv']].round(2)
    ltv['vida_media_meses'] = ltv['vida_media_meses'].round(1)
    return {'periodo': f'{_janela[0]} a {_janela[-1]}', 'planos': _registros(ltv)}


FERRAMENTAS = [descrever_tabelas, consultar_sql, calcular_mrr, churn_mensal, ltv_por_plano]
