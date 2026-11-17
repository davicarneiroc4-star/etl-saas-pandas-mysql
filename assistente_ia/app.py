"""Tela de chat do assistente.  Rodar:  streamlit run assistente_ia/app.py"""
import os

import streamlit as st

# No Streamlit Community Cloud a chave vem dos "Secrets"; no computador, do .env
try:
    if 'GEMINI_API_KEY' in st.secrets:
        os.environ['GEMINI_API_KEY'] = st.secrets['GEMINI_API_KEY']
except FileNotFoundError:
    pass

from agente import Assistente  # noqa: E402

st.set_page_config(page_title='Pergunte ao ETL', page_icon='📊')

st.title('📊 Pergunte ao ETL')
st.caption('Agente com Gemini que responde perguntas sobre os dados de uma empresa SaaS fictícia, '
           'usando as métricas do pipeline ETL e SQL somente leitura. Todos os dados são sintéticos.')

EXEMPLOS = [
    'Qual é o MRR atual e qual plano mais contribui?',
    'Qual plano tem o maior churn nos últimos 12 meses?',
    'Quais são os 3 motivos de cancelamento mais comuns?',
    'Quantos clientes temos por segmento?',
]


def mostrar_ferramentas(chamadas):
    if not chamadas:
        return
    with st.expander(f'Como cheguei nessa resposta ({len(chamadas)} ferramenta(s))'):
        for c in chamadas:
            st.markdown(f"**{c['ferramenta']}**")
            consulta = c['argumentos'].get('consulta')
            if consulta:
                st.code(consulta, language='sql')
            elif c['argumentos']:
                st.json(c['argumentos'])


if 'assistente' not in st.session_state:
    if not os.getenv('GEMINI_API_KEY') and not os.path.exists(os.path.join(os.path.dirname(__file__), '..', '.env')):
        st.error('Falta a chave GEMINI_API_KEY (no .env ou nos Secrets do Streamlit).')
        st.stop()
    st.session_state.assistente = Assistente()
    st.session_state.mensagens = []

with st.sidebar:
    st.subheader('Experimente perguntar')
    for exemplo in EXEMPLOS:
        if st.button(exemplo, use_container_width=True):
            st.session_state.pergunta_exemplo = exemplo
    st.divider()
    if st.button('Nova conversa', use_container_width=True):
        del st.session_state['assistente']
        st.rerun()
    st.caption('Código: github.com/davicarneiroc4-star/etl-saas-pandas-mysql')

for m in st.session_state.mensagens:
    with st.chat_message(m['papel']):
        st.markdown(m['texto'])
        mostrar_ferramentas(m.get('chamadas'))

pergunta = st.chat_input('Pergunte sobre MRR, churn, LTV, clientes, faturas...')
pergunta = pergunta or st.session_state.pop('pergunta_exemplo', None)

if pergunta:
    st.session_state.mensagens.append({'papel': 'user', 'texto': pergunta})
    with st.chat_message('user'):
        st.markdown(pergunta)
    with st.chat_message('assistant'):
        with st.spinner('Consultando os dados...'):
            try:
                texto, chamadas = st.session_state.assistente.perguntar(pergunta)
            except Exception as e:  # noqa: BLE001 - mostra o erro na tela em vez de quebrar a página
                texto, chamadas = f'Não consegui responder agora ({type(e).__name__}). Tente de novo em instantes.', []
        st.markdown(texto)
        mostrar_ferramentas(chamadas)
    st.session_state.mensagens.append({'papel': 'assistant', 'texto': texto, 'chamadas': chamadas})
