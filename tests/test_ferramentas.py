"""Testes da trava de segurança do SQL do assistente.  Rodar:  python -m pytest tests"""
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assistente_ia'))
import ferramentas as f  # noqa: E402


def contar_clientes():
    return f.consultar_sql('SELECT COUNT(*) AS n FROM clientes')['linhas'][0]['n']


def test_bloqueia_escrita_e_leitura_de_arquivos():
    for sql in ['DELETE FROM clientes',
                'WITH x AS (SELECT 1) DELETE FROM clientes',
                'WITH x AS (SELECT 1) INSERT INTO planos SELECT * FROM planos',
                'DROP TABLE clientes',
                'SELECT 1; DROP TABLE clientes',
                "SELECT * FROM read_csv('.env')"]:
        assert 'erro' in f.consultar_sql(sql), sql
    assert contar_clientes() == 600


def test_corta_em_100_linhas_sem_montar_tudo():
    # Produto cartesiano de 256 milhões de linhas: só passa se não materializar o resultado
    r = f.consultar_sql('SELECT a.id_evento FROM eventos_uso a, eventos_uso b')
    assert len(r['linhas']) == 100 and r['cortado']


def test_consultas_em_paralelo():
    erros = []

    def rodar():
        for _ in range(50):
            r = f.consultar_sql('SELECT COUNT(*) AS n FROM clientes')
            if r.get('linhas') != [{'n': 600}]:  # erro de "connection is busy" chega aqui como {'erro': ...}
                erros.append(r)

    threads = [threading.Thread(target=rodar) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not erros


def test_aviso_quando_numeros_nao_vem_das_ferramentas():
    import agente
    a = agente.Assistente.__new__(agente.Assistente)  # sem chamar a API
    respostas = iter([('LTV de R$ 2.056', []), ('LTV de R$ 2.056', [])])
    a._enviar = lambda mensagem: next(respostas)
    assert '⚠️' in a.perguntar('LTV do Basic?')[0]


def test_visao_sql_e_python_dao_o_mesmo_mrr():
    # A regra do MRR existe em Python (churn_ltv.valor_mensal) e em SQL (visão mrr_assinaturas)
    sql = f.consultar_sql("SELECT ROUND(SUM(valor_mensal), 2) AS mrr FROM mrr_assinaturas WHERE status = 'ativa'")
    assert sql['linhas'][0]['mrr'] == f.calcular_mrr()['mrr_total']
