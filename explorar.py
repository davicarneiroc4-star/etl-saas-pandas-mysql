from extract import extrair_tabelas

dados = extrair_tabelas()

clientes = dados['clientes']
clientes.columns = clientes.columns.str.lower()

clientes.info()
print()
print("E-mails vazios:", clientes['email'].isna().sum())
print("E-mails duplicados:", clientes['email'].dropna().duplicated().sum())
print("Nomes com espaço sobrando:", (clientes['nome_empresa'] != clientes['nome_empresa'].str.strip()).sum())
print("Nomes todos em maiúsculo:", (clientes['nome_empresa'] == clientes['nome_empresa'].str.upper()).sum())