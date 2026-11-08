import pandas as pd
from extract import engine

assinaturas = pd.read_sql("SELECT * FROM assinaturas_limpo", engine)
planos = pd.read_sql("SELECT * FROM planos_limpo", engine)
cancelamentos = pd.read_sql("SELECT * FROM cancelamentos_limpo", engine)

# Junta o plano em cada assinatura
df = assinaturas.merge(planos[['id_plano', 'nome_plano', 'periodicidade']], on='id_plano', how='left')

# Valor por mês: plano anual vale 1/12 por mês
df['valor_mensal'] = df['valor_assinatura']
df.loc[df['periodicidade'] == 'anual', 'valor_mensal'] = df['valor_assinatura'] / 12

# MRR: soma do valor mensal das assinaturas ativas
ativas = df[df['status'] == 'ativa']
mrr = ativas['valor_mensal'].sum()

print(f"MRR atual: R$ {mrr:,.2f}")
print()
print("MRR por plano:")
print(ativas.groupby('nome_plano')['valor_mensal'].sum().round(2).sort_values(ascending=False))

# Churn
total = len(df)
canceladas = (df['status'] == 'cancelada').sum()

print()
print(f"Taxa de cancelamento: {canceladas / total:.1%} ({canceladas} de {total} assinaturas)")
print()
print("Cancelamentos por tipo:")
print(cancelamentos['tipo_cancelamento'].value_counts())
print()
print("Cancelamentos por motivo:")
print(cancelamentos['motivo_cancelamento'].value_counts())