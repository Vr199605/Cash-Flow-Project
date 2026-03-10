import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile
import os

# 1. Configuração de Página e Estilo Dark Premium
st.set_page_config(
    page_title="CASH FLOW - INVESTOR DASHBOARD", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; }
    
    /* Cards de Métricas */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 20px;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-weight: 700; }
    
    /* Abas Customizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px 10px 0px 0px;
        color: white;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #000 !important; }
    
    /* Botões */
    .stButton>button {
        background: linear-gradient(90deg, #d946ef, #a21caf); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE SUPORTE ---
def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_unicode(text):
    """Limpa caracteres para evitar erro de encoding no PDF"""
    return str(text).encode('ascii', 'ignore').decode('ascii')

# --- GERADOR DE PDF PREMIUM ---
def gerar_pdf_investidor(df_mes, df_full, mes, total_saida):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # PÁGINA 1: DASHBOARD EXECUTIVO
    pdf.add_page()
    
    # Cabeçalho Profissional
    pdf.set_fill_color(15, 23, 42) # Azul Marinho Escuro
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 22)
    pdf.cell(190, 15, "RELATORIO ESTRATEGICO DE FLUXO DE CAIXA", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Periodo: {mes} | Analise de Desembolsos Reais", ln=True, align="C")
    
    pdf.ln(25)
    pdf.set_text_color(0, 0, 0)
    
    # KPIs no PDF
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(95, 10, "DESEMBOLSO TOTAL NO PERIODO", border=1, align="C", fill=True)
    pdf.cell(95, 10, "QUANTIDADE DE LANCAMENTOS", border=1, ln=True, align="C", fill=True)
    
    pdf.set_font("Arial", "", 14)
    pdf.cell(95, 15, format_brl(total_saida), border=1, align="C")
    pdf.cell(95, 15, str(len(df_mes)), border=1, ln=True, align="C")
    
    pdf.ln(10)

    # Inserção de Gráficos no PDF
    temp_imgs = []
    
    # Gráfico 1: Pareto
    plt.figure(figsize=(10, 4))
    p_data = df_mes[df_mes['Valor categoria/centro de custo'] < 0].groupby('Categoria')['Valor categoria/centro de custo'].sum().abs().sort_values(ascending=True).tail(8)
    p_data.plot(kind='barh', color='#38bdf8')
    plt.title("Maiores Saidas por Categoria", fontsize=12, fontweight='bold')
    plt.tight_layout()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        plt.savefig(tmp.name, dpi=150)
        temp_imgs.append(tmp.name)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "1. Analise de Pareto (Maiores Custos)", ln=True)
        pdf.image(tmp.name, x=15, w=180)

    pdf.ln(5)

    # Gráfico 2: Evolução
    plt.figure(figsize=(10, 3))
    h_data = df_full[df_full['Valor categoria/centro de custo'] < 0].groupby('Periodo_Sort')['Valor categoria/centro de custo'].sum().abs()
    h_data.index = h_data.index.astype(str)
    plt.plot(h_data.index, h_data.values, marker='o', color='#f43f5e', linewidth=2)
    plt.title("Tendencia Mensal de Caixa", fontsize=12, fontweight='bold')
    plt.tight_layout()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp2:
        plt.savefig(tmp2.name, dpi=150)
        temp_imgs.append(tmp2.name)
        pdf.cell(190, 10, "2. Evolucao Historica de Desembolsos", ln=True)
        pdf.image(tmp2.name, x=15, w=180)

    # PÁGINA 2: TABELAS DE AUDITORIA
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "Detalhamento de Lancamentos (Audit Trail)", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(30, 8, " Data", border=1, fill=True)
    pdf.cell(100, 8, " Categoria", border=1, fill=True)
    pdf.cell(60, 8, " Valor", border=1, ln=True, fill=True)
    
    pdf.set_font("Arial", "", 8)
    audit = df_mes.sort_values('Valor categoria/centro de custo').head(25)
    for _, row in audit.iterrows():
        pdf.cell(30, 7, f" {row['Data de pagamento'].strftime('%d/%m/%Y')}", border=1)
        pdf.cell(100, 7, f" {clean_unicode(row['Categoria'])[:55]}", border=1)
        pdf.cell(60, 7, f" {format_brl(abs(row['Valor categoria/centro de custo']))}", border=1, ln=True)

    # Limpeza
    for f in temp_imgs: os.remove(f)
    plt.close('all')
    return bytes(pdf.output())

# 3. Motor de Processamento (Google Sheets)
@st.cache_data(ttl=600)
def load_and_process():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?output=csv"
    df = pd.read_csv(url)
    
    def clean_val(v):
        if isinstance(v, str):
            v = v.replace('R$', '').replace('.', '').replace(' ', '').replace(',', '.')
            try: return float(v)
            except: return 0.0
        return v

    col_v = 'Valor categoria/centro de custo'
    df[col_v] = df[col_v].apply(clean_val)
    df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data de pagamento']).sort_values('Data de pagamento')
    
    df['Mes_Ano'] = df['Data de pagamento'].dt.strftime('%m/%Y')
    df['Periodo_Sort'] = df['Data de pagamento'].dt.to_period('M')

    keywords_imposto = ['ISS', 'IRPJ', 'CSLL', 'PIS', 'COFINS', 'RETIDO', 'IMPOSTO', 'TAXA', 'DARF']
    df['Tipo'] = df['Categoria'].apply(
        lambda x: 'Fiscal' if any(k in str(x).upper() for k in keywords_imposto) else 'Operacional'
    )
    return df

# --- INTERFACE PRINCIPAL ---
try:
    df_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'

    # Sidebar simplificada
    with st.sidebar:
        st.header("⚙️ Painel")
        if st.button("🔄 Sincronizar Agora"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.caption("CFO Dashboard v6.1")

    # Header
    st.title("💎 CFO STRATEGIC DASHBOARD")
    
    # Filtro de Mês
    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    lista_meses.insert(0, "Todos os Meses")
    mes_selecionado = st.selectbox("📅 Selecionar Periodo de Analise:", lista_meses)

    df = df_raw[df_raw['Mes_Ano'] == mes_selecionado].copy() if mes_selecionado != "Todos os Meses" else df_raw.copy()

    # Métricas de Impacto (Sem Budget)
    saidas_totais = abs(df[df[col_v] < 0][col_v].sum())
    fiscal_totais = abs(df[df['Tipo'] == 'Fiscal'][col_v].sum())
    operacional_puro = abs(df[df['Tipo'] == 'Operacional'][col_v].sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash Out Total", format_brl(saidas_totais))
    m2.metric("Custos Fiscais", format_brl(fiscal_totais))
    m3.metric("Custos Operacionais", format_brl(operacional_puro))
    m4.metric("Aging (Lançamentos)", len(df))

    st.write("---")

    # SISTEMA DE ABAS COMPLETO
    tab_proj, tab_burn, tab_pareto, tab_tax, tab_raw, tab_pdf = st.tabs([
        "📊 Evolução Mensal", "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "🏛️ Fiscal vs Op", "📋 Dados Brutos", "📥 Exportar Premium"
    ])

    with tab_proj:
        st.subheader("Tendencia de Saidas Mensais")
        proj_mensal = df_raw[df_raw[col_v] < 0].groupby('Periodo_Sort')[col_v].sum().abs().reset_index()
        proj_mensal['Mês'] = proj_mensal['Periodo_Sort'].astype(str)
        st.bar_chart(proj_mensal.set_index('Mês')[col_v], color="#38bdf8")
        st.dataframe(proj_mensal.style.format({col_v: "R$ {:,.2f}"}), use_container_width=True)

    with tab_burn:
        st.subheader("Burn Rate Acumulado")
        burn_df = df.groupby('Data de pagamento')[col_v].sum().cumsum().reset_index()
        st.area_chart(burn_df.set_index('Data de pagamento'), color="#f43f5e")

    with tab_pareto:
        st.subheader("Principais Centros de Custo")
        p_df = df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).head(10)
        st.bar_chart(p_df, color="#38bdf8")

    with tab_tax:
        st.subheader("Composição Fiscal")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            st.bar_chart(df.groupby('Tipo')[col_v].sum().abs(), color="#a21caf")
        with c_t2:
            st.dataframe(df[df['Tipo'] == 'Fiscal'][['Data de pagamento', 'Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}))

    with tab_raw:
        busca = st.text_input("Filtrar registros...")
        df_edit = df[df['Categoria'].str.contains(busca, case=False)]
        st.data_editor(df_edit, hide_index=True, use_container_width=True)

    with tab_pdf:
        st.header("📥 Relatorio Executivo para Socios")
        st.write("Gere um documento formatado com graficos e KPIs para apresentacoes oficiais.")
        if st.button("🎨 Gerar e Baixar PDF Premium"):
            with st.spinner("Compilando relatorio..."):
                pdf_output = gerar_pdf_investidor(df, df_raw, mes_selecionado, saidas_totais)
                st.download_button(
                    label="💾 Clique aqui para baixar o PDF",
                    data=pdf_output,
                    file_name=f"RELATORIO_CFO_{mes_selecionado.replace('/', '_')}.pdf",
                    mime="application/pdf"
                )

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")