import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from extract import engine

assinaturas = pd.read_sql("SELECT * FROM assinaturas_limpo", engine)
planos = pd.read_sql("SELECT * FROM planos_limpo", engine)

df = assinaturas.merge(planos[['id_plano', 'periodicidade']], on='id_plano', how='left')
df = df[df['status'] != 'trial']

df['valor_mensal'] = df['valor_assinatura']
df.loc[df['periodicidade'] == 'anual', 'valor_mensal'] = df['valor_assinatura'] / 12

df['data_inicio'] = pd.to_datetime(df['data_inicio'])
df['data_fim'] = pd.to_datetime(df['data_fim'])

meses = pd.date_range(df['data_inicio'].min(), pd.Timestamp.today(), freq='MS')

mrr_por_mes = []
for mes in meses:
    ativa_no_mes = (df['data_inicio'] <= mes) & (df['data_fim'].isna() | (df['data_fim'] > mes))
    mrr_por_mes.append(df.loc[ativa_no_mes, 'valor_mensal'].sum())

mrr = pd.Series(mrr_por_mes, index=meses)


def formatar_reais(valor, _posicao):
    # 64500 -> "R$ 64,5 mil" (padrão brasileiro: vírgula decimal)
    if valor == 0:
        return "R$ 0"
    return f"R$ {valor / 1000:.1f} mil".replace(".", ",").replace(",0 mil", " mil")


fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(mrr.index, mrr.values, marker='o')

# Destaca o pico (maior MRR da série)
mes_pico = mrr.idxmax()
valor_pico = mrr.max()
ax.plot(mes_pico, valor_pico, marker='o', markersize=10, color='tab:orange')
ax.annotate(
    f"Pico: {formatar_reais(valor_pico, None)}\n({mes_pico:%m/%Y})",
    xy=(mes_pico, valor_pico),
    xytext=(0, -45),
    textcoords='offset points',
    ha='center',
    arrowprops=dict(arrowstyle='->', color='gray'),
)

ax.yaxis.set_major_formatter(FuncFormatter(formatar_reais))
ax.set_title('MRR mês a mês')
ax.set_xlabel('Mês')
ax.set_ylabel('MRR')
ax.grid(True, alpha=0.3)
fig.tight_layout()

pasta_imagens = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagens')
os.makedirs(pasta_imagens, exist_ok=True)
caminho = os.path.join(pasta_imagens, 'grafico_mrr.png')
fig.savefig(caminho, dpi=150)
print("Gráfico salvo em:", caminho)

plt.show()
