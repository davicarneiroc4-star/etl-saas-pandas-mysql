import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
from extract import engine

PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagens')

# Antes de 2025 a base tem poucas dezenas de assinaturas: 1 cancelamento já vira
# um pico de vários %. O gráfico começa aqui para não distorcer a leitura.
INICIO_GRAFICO = pd.Period('2025-01', freq='M')

# Janela usada no churn médio e no LTV
MESES_JANELA = 12


def carregar_dados():
    assinaturas = pd.read_sql("SELECT * FROM assinaturas_limpo", engine)
    planos = pd.read_sql("SELECT * FROM planos_limpo", engine)
    cancelamentos = pd.read_sql("SELECT * FROM cancelamentos_limpo", engine)

    df = assinaturas.merge(planos[['id_plano', 'nome_plano', 'periodicidade']], on='id_plano', how='left')
    df = df.merge(cancelamentos[['id_assinatura', 'tipo_cancelamento']], on='id_assinatura', how='left')

    # Só assinaturas pagas: trial e plano Free não geram receita
    df = df[(df['status'] != 'trial') & (df['nome_plano'] != 'Free')].copy()

    # Valor por mês: plano anual vale 1/12 por mês (mesma regra de metricas.py)
    df['valor_mensal'] = df['valor_assinatura']
    df.loc[df['periodicidade'] == 'anual', 'valor_mensal'] = df['valor_assinatura'] / 12

    df['data_inicio'] = pd.to_datetime(df['data_inicio'])
    df['data_fim'] = pd.to_datetime(df['data_fim'])

    return df


def calcular_churn_mensal(df, meses):
    """Para cada mês: quantas assinaturas estavam ativas no dia 1º e quantas delas cancelaram até o fim do mês."""
    linhas = []
    for mes in meses:
        inicio = mes.start_time
        fim = (mes + 1).start_time

        # Mesma regra do gráfico de MRR: ativa no dia 1º do mês
        ativas = df[(df['data_inicio'] <= inicio) & (df['data_fim'].isna() | (df['data_fim'] > inicio))]
        canceladas = ativas[ativas['data_fim'] <= fim]

        linhas.append({
            'mes': mes,
            'ativas_inicio': len(ativas),
            'canceladas': len(canceladas),
            'voluntarias': (canceladas['tipo_cancelamento'] == 'voluntário').sum(),
            'involuntarias': (canceladas['tipo_cancelamento'] == 'involuntário').sum(),
            'mrr_inicio': ativas['valor_mensal'].sum(),
            'mrr_perdido': canceladas['valor_mensal'].sum(),
        })

    churn = pd.DataFrame(linhas).set_index('mes')
    churn['churn_clientes'] = churn['canceladas'] / churn['ativas_inicio']
    churn['churn_receita'] = churn['mrr_perdido'] / churn['mrr_inicio']
    return churn


def resumir_janela(churn):
    """Churn médio e ticket médio de um período, somando os meses (meses com base maior pesam mais)."""
    churn_medio = churn['canceladas'].sum() / churn['ativas_inicio'].sum()
    ticket_medio = churn['mrr_inicio'].sum() / churn['ativas_inicio'].sum()
    return churn_medio, ticket_medio


def calcular_ltv(df, meses):
    linhas = []
    grupos = [('Geral', df)] + list(df.groupby('nome_plano'))
    for nome, grupo in grupos:
        churn_medio, ticket_medio = resumir_janela(calcular_churn_mensal(grupo, meses))
        vida_media = 1 / churn_medio if churn_medio > 0 else float('inf')
        linhas.append({
            'plano': nome,
            'ticket_mensal': ticket_medio,
            'churn_mensal': churn_medio,
            'vida_media_meses': vida_media,
            'ltv': ticket_medio * vida_media,
        })
    return pd.DataFrame(linhas).set_index('plano')


def formatar_reais(valor, _posicao=None):
    return f"R$ {valor:,.0f}".replace(",", ".")


def grafico_churn(churn, caminho):
    dados = churn[churn.index >= INICIO_GRAFICO]
    rotulos = [m.strftime('%m/%y') for m in dados.index]
    vol = dados['voluntarias'] / dados['ativas_inicio']
    invol = dados['involuntarias'] / dados['ativas_inicio']

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(rotulos, vol, label='Voluntário', color='tab:blue')
    ax.bar(rotulos, invol, bottom=vol, label='Involuntário (falha de pagamento)', color='tab:red')
    ax.plot(rotulos, dados['churn_receita'], marker='o', color='black', label='Churn de receita (MRR perdido)')

    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_title('Churn mensal das assinaturas pagas')
    ax.set_xlabel('Mês')
    ax.set_ylabel('% das assinaturas ativas no início do mês')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, axis='y', alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)


def grafico_ltv(ltv, caminho):
    dados = ltv.drop(index='Geral').sort_values('ltv')

    fig, ax = plt.subplots(figsize=(9, 4))
    barras = ax.barh(dados.index, dados['ltv'], color='tab:blue')
    ax.bar_label(barras, labels=[formatar_reais(v) for v in dados['ltv']], padding=4)
    ax.axvline(ltv.loc['Geral', 'ltv'], color='gray', linestyle='--',
               label=f"Média geral: {formatar_reais(ltv.loc['Geral', 'ltv'])}")

    ax.xaxis.set_major_formatter(FuncFormatter(formatar_reais))
    ax.set_xlim(0, dados['ltv'].max() * 1.2)
    ax.set_title('LTV por plano (receita média de uma assinatura durante toda a vida)')
    ax.set_xlabel('LTV')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)


if __name__ == "__main__":
    df = carregar_dados()

    # Os dados de cancelamento vão só até a data em que foram gerados.
    # Usar meses depois disso daria churn 0% falso, então a análise para no último mês com cancelamentos.
    ultimo_mes = df['data_fim'].max().to_period('M')
    # No mês da primeira assinatura ninguém estava ativo no dia 1º, então a série começa no mês seguinte
    primeiro_mes = df['data_inicio'].min().to_period('M') + 1
    meses = pd.period_range(primeiro_mes, ultimo_mes, freq='M')
    janela = meses[-MESES_JANELA:]

    churn = calcular_churn_mensal(df, meses)

    tabela = churn[['ativas_inicio', 'canceladas', 'voluntarias', 'involuntarias']].copy()
    tabela['churn_clientes'] = (churn['churn_clientes'] * 100).round(1).astype(str) + '%'
    tabela['churn_receita'] = (churn['churn_receita'] * 100).round(1).astype(str) + '%'
    print("CHURN MENSAL (assinaturas pagas)")
    print(tabela.to_string())

    churn_medio, ticket_medio = resumir_janela(churn.loc[janela])
    print()
    print(f"Últimos {MESES_JANELA} meses ({janela[0].strftime('%m/%Y')} a {janela[-1].strftime('%m/%Y')}):")
    print(f"  Churn médio de clientes: {churn_medio:.2%} ao mês")
    print(f"  Churn médio de receita:  {churn.loc[janela, 'mrr_perdido'].sum() / churn.loc[janela, 'mrr_inicio'].sum():.2%} ao mês")
    print(f"  Cancelamentos involuntários: {churn.loc[janela, 'involuntarias'].sum()} de {churn.loc[janela, 'canceladas'].sum()}")

    ltv = calcular_ltv(df, janela)
    print()
    print("LTV POR PLANO")
    print(pd.DataFrame({
        'ticket mensal': ltv['ticket_mensal'].map(formatar_reais),
        'churn mensal': ltv['churn_mensal'].map('{:.2%}'.format),
        'vida média': ltv['vida_media_meses'].map('{:.0f} meses'.format),
        'LTV': ltv['ltv'].map(formatar_reais),
    }).to_string())

    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    grafico_churn(churn, os.path.join(PASTA_IMAGENS, 'churn_mensal.png'))
    grafico_ltv(ltv, os.path.join(PASTA_IMAGENS, 'ltv_por_plano.png'))
    print()
    print("Gráficos salvos em:", PASTA_IMAGENS)
