import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile
import os

# 1. Configuração e Cache
st.set_page_config(page_title="CASH FLOW - DASHBOARD", layout="wide")

# Otimização do Processamento de Dados
@st.cache_data(ttl=600)
def load_and_process():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?output=csv"
    df = pd.read_csv(url)
    
    col_v = 'Valor categoria/centro de custo'
    
    # Vetorização: muito mais rápido que .apply(clean_val)
    if df[col_v].dtype == 'object':
        df[col_v] = df[col_v].str.replace('R$', '', regex=False)\
                             .str.replace('.', '', regex=False)\
                             .str.replace(' ', '', regex=False)\
                             .str.replace(',', '.', regex=False).astype(float)

    df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data de pagamento']).sort_values('Data de pagamento')
    
    df['Mes_Ano'] = df['Data de pagamento'].dt.strftime('%m/%Y')
    df['Periodo_Sort'] = df['Data de pagamento'].dt.to_period('M')

    keywords_imposto = ['ISS', 'IRPJ', 'CSLL', 'PIS', 'COFINS', 'RETIDO', 'IMPOSTO', 'TAXA', 'DARF']
    pattern = '|'.join(keywords_imposto)
    df['Tipo'] = np.where(df['Categoria'].str.upper().str.contains(pattern, na=False), 'Fiscal', 'Operacional')
    
    return df

# --- UI CSS (Resumido para o exemplo) ---
st.markdown("""<style>...</style>""", unsafe_allow_html=True)

# --- FRAGMENTO PARA EXPORTAÇÃO (Não recarrega o app ao clicar) ---
@st.fragment
def render_pdf_section(df_mes, df_full, mes, total_saida):
    st.header("📥 Relatório Executivo")
    if st.button("🎨 Gerar e Baixar PDF Premium"):
        with st.spinner("Compilando..."):
            # A função gerar_pdf_investidor permanece a mesma
            from __main__ import gerar_pdf_investidor 
            pdf_output = gerar_pdf_investidor(df_mes, df_full, mes, total_saida)
            st.download_button("💾 Baixar Agora", pdf_output, f"Relatorio_{mes}.pdf", "application/pdf")

# --- MAIN ---
try:
    df_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'

    # Sidebar
    with st.sidebar:
        if st.button("🔄 Forçar Sincronização"):
            st.cache_data.clear()
            st.rerun()

    st.title("💎 CFO STRATEGIC DASHBOARD")
    
    lista_meses = ["Todos os Meses"] + sorted(df_raw['Mes_Ano'].unique().tolist(), 
                                             key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    
    mes_selecionado = st.selectbox("📅 Período:", lista_meses)

    # Filtragem rápida
    if mes_selecionado != "Todos os Meses":
        df = df_raw[df_raw['Mes_Ano'] == mes_selecionado]
    else:
        df = df_raw

    # Métricas calculadas apenas uma vez
    saidas_df = df[df[col_v] < 0]
    saidas_totais = abs(saidas_df[col_v].sum())
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Cash Out Total", f"R$ {saidas_totais:,.2f}")
    # ... outras métricas

    tab_proj, tab_burn, tab_raw, tab_pdf = st.tabs(["📊 Evolução", "🔥 Burn Rate", "📋 Dados", "📥 PDF"])

    with tab_proj:
        # Cálculo apenas quando a aba é aberta
        proj = df_raw[df_raw[col_v] < 0].groupby('Periodo_Sort')[col_v].sum().abs()
        st.bar_chart(proj)

    with tab_burn:
        # Gráficos nativos do Streamlit são rápidos, mas evite processar o DF aqui
        burn = df.groupby('Data de pagamento')[col_v].sum().cumsum()
        st.area_chart(burn)

    with tab_raw:
        # Fragmento de busca para não travar o dashboard ao digitar
        busca = st.text_input("Filtrar categoria...")
        if busca:
            st.dataframe(df[df['Categoria'].str.contains(busca, case=False)])
        else:
            st.dataframe(df.head(100)) # Mostra apenas os primeiros 100 por padrão

    with tab_pdf:
        render_pdf_section(df, df_raw, mes_selecionado, saidas_totais)

except Exception as e:
    st.error(f"Erro: {e}")
