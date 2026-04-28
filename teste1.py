import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Dashboard de Produção Médica - HV",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# ESTILO CUSTOMIZADO (CLEAN / SOFT UI PREMIUM COM CARDS CUSTOMIZADOS)
# =========================
st.markdown("""
    <style>
    /* Fundo Principal: Cinza super claro/gelo para destacar os cartões brancos */
    .stApp {
        background-color: #f4f7fb;
        color: #2d3748;
    }
    
    /* Sidebar Branca com sombra sutil */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: none;
        box-shadow: 2px 0 20px rgba(0,0,0,0.03);
    }

    h1, h2, h3, .stMarkdown p {
        color: #1a202c !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Título principal do App */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    /* Espaçamento geral */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Estilo dos Blocos Grandes (Cards de Seção) */
    .section-card {
        background: #ffffff;
        border: none;
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(149, 157, 165, 0.1); 
    }
    .small-note {
        color: #718096;
        font-size: 0.9rem;
    }

    /* ---------------------------------------------------
       ESTRUTURA DOS NOVOS CARDS DE KPI (ALTO CONTRASTE)
       --------------------------------------------------- */
    .card-row {
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
        margin-bottom: 25px;
        margin-top: 10px;
    }
    
    .card-col-6 { flex: 1 1 calc(16.666% - 20px); min-width: 140px; }
    .card-col-4 { flex: 1 1 calc(25% - 20px); min-width: 200px; }

    .custom-metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .custom-metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }

    .custom-metric-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    .custom-metric-value {
        font-size: 2.2rem;
        font-weight: 900;
        color: #1a202c;
        margin: 0;
        line-height: 1.1;
    }
    
    .custom-metric-sub {
        font-size: 0.8rem;
        color: #a0aec0;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Tabs Customizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        color: #718096;
        border: none;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.02);
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #6b46c1 !important; 
        border-bottom: 3px solid #6b46c1 !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# DICIONÁRIOS GLOBAIS E CORES
# =========================
MESES_ORDEM = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12
}

MESES_NOME = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

MESES_ABREV = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

SOCIOS = {
    "FERNANDO GADELHA", "ALINE PAIVA", "ANA ELISABETH", "CAMILA GADELHA",
    "CAMILA LACERDA", "GABRIELLA ALVES", "ISABELLA W QUEIROGA", "KEYLLA MENEZES", "MARIELLE MEDEIROS", "AMANDA ELIZA", "RAQUEL MENEZES"
}

FELLOWS = {
    "LUIZ CARLOS FILHO", "MARCELLA HANNAH", "TIAGO GRANA",
    "RODRIGO MACIEL", "ROBERTA FERNANDA", "JOAO VITOR BRUSQUI"
}

PALETA_LIGHT = ["#4fd1c5", "#6b46c1", "#3182ce", "#ed64a6", "#f6ad55", "#cbd5e0", "#805ad5", "#e53e3e", "#dd6b20", "#38a169"]
CORES_GRUPO = {
    "Sócios": "#4fd1c5",        
    "Fellows": "#6b46c1",       
    "Corpo Clínico": "#f6ad55"  
}

# =========================
# FUNÇÕES AUXILIARES
# =========================
def formatar_num(n):
    try: return f"{float(n):,.0f}".replace(",", ".")
    except Exception: return "0"

def formatar_pct(v):
    try: return f"{v:.1f}%".replace(".", ",")
    except Exception: return "0,0%"

def classificar_perfil_vetorizado(df):
    condicoes = [
        (df["Consultas"] == 0) & (df["Cirurgias"] > 0), 
        (df["Cirurgias"] == 0) & (df["Total"] > 0),     
        (df["Consultas"] > 0) & ((df["Cirurgias"] / df["Consultas"]) >= 0.35), 
        (df["Consultas"] > 0) & ((df["Cirurgias"] / df["Consultas"]) <= 0.10)  
    ]
    escolhas = ["Cirúrgico", "Clínico", "Cirúrgico", "Clínico"]
    return np.select(condicoes, escolhas, default="Misto")

def criar_ano_mes_label_vetorizado(anos, meses):
    meses_str = meses.map(MESES_ABREV).fillna("")
    return meses_str + "/" + anos.astype(str)

# =========================
# CARREGAR DADOS
# =========================
@st.cache_data
def carregar_dados():
    caminho_arquivo = "Consolidado_Hospital_Visao.xlsx"

    if not os.path.exists(caminho_arquivo):
        return pd.DataFrame(), pd.DataFrame()

    df_bi = pd.read_excel(caminho_arquivo, sheet_name="BI_Consolidado", engine="openpyxl")
    
    try:
        df_det = pd.read_excel(caminho_arquivo, sheet_name="Detalhado_Klingo", engine="openpyxl")
    except:
        df_det = pd.DataFrame()

    colunas_esperadas = ["Ano", "Mês", "Médico", "Origem", "Consultas", "Exames", "Cirurgias", "Lentes", "Procedimentos", "Procedimentos e Lentes"]
    for c in colunas_esperadas:
        if c not in df_bi.columns:
            df_bi[c] = 0 if c not in ["Ano", "Mês", "Médico", "Origem"] else None

    cols_numericas = ["Consultas", "Exames", "Cirurgias", "Lentes", "Procedimentos", "Procedimentos e Lentes"]
    for col in cols_numericas:
        df_bi[col] = pd.to_numeric(df_bi[col], errors="coerce").fillna(0).astype(int)
    
    df_bi["Total"] = df_bi[["Consultas", "Exames", "Cirurgias", "Lentes", "Procedimentos"]].sum(axis=1)
    
    df_bi["Médico"] = df_bi["Médico"].astype(str).str.strip().str.upper()
    df_bi["Mês"] = df_bi["Mês"].astype(str).str.strip().str.upper()
    
    df_bi["MesNum"] = df_bi["Mês"].map(MESES_ORDEM).fillna(0).astype(int)
    df_bi["MesNome"] = df_bi["MesNum"].map(MESES_NOME).fillna(df_bi["Mês"])

    df_bi["Grupo"] = np.where(df_bi["Médico"].isin(SOCIOS), "Sócios", 
                  np.where(df_bi["Médico"].isin(FELLOWS), "Fellows", "Corpo Clínico"))

    if not df_det.empty:
        # LIMPANDO ERROS GRAMATICAIS E CARACTERES QUEBRADOS
        df_det["Procedimento"] = df_det["Procedimento"].astype(str)\
            .str.replace("Ã”", "Ô")\
            .str.replace("Ã\"", "Ô")\
            .str.replace("ULTRASSÃ", "ULTRASSÔ", regex=False)\
            .str.replace('ULTRASSÔ""NICA', 'ULTRASSÔNICA', regex=False)\
            .str.replace('ULTRASSÔ"NICA', 'ULTRASSÔNICA', regex=False)

        df_det["Médico"] = df_det["Médico"].astype(str).str.strip().str.upper()
        df_det["Mês"] = df_det["Mês"].astype(str).str.strip().str.upper()
        
        df_det["MesNum"] = df_det["Mês"].map(MESES_ORDEM).fillna(0).astype(int)
        df_det["MesNome"] = df_det["MesNum"].map(MESES_NOME).fillna(df_det["Mês"])
        
        df_det["Grupo"] = np.where(df_det["Médico"].isin(SOCIOS), "Sócios", 
                      np.where(df_det["Médico"].isin(FELLOWS), "Fellows", "Corpo Clínico"))
        
        df_det["Quantidade"] = pd.to_numeric(df_det["Quantidade"], errors="coerce").fillna(0)

    return df_bi, df_det

df_bi, df_det = carregar_dados()

if df_bi.empty:
    st.error("Arquivo 'Consolidado_Hospital_Visao.xlsx' não encontrado ou inválido.")
    st.stop()

# =========================
# SIDEBAR - FILTROS
# =========================
st.sidebar.title("Filtros")

anos_disponiveis = sorted(df_bi["Ano"].dropna().unique().tolist())
anos_sel = st.sidebar.multiselect("Ano(s)", anos_disponiveis, default=anos_disponiveis)

if not anos_sel:
    st.sidebar.warning("Selecione pelo menos 1 ano.")
    st.stop()

df_bi_anos = df_bi[df_bi["Ano"].isin(anos_sel)].copy()
df_det_anos = df_det[df_det["Ano"].isin(anos_sel)].copy() if not df_det.empty else pd.DataFrame()

meses_ordenados = df_bi_anos[["MesNum", "MesNome"]].dropna().drop_duplicates().sort_values("MesNum")
lista_meses = meses_ordenados["MesNome"].tolist()
meses_sel = st.sidebar.multiselect("Mês(es)", lista_meses, default=lista_meses)

grupos_disp = ["Todos"] + sorted(df_bi["Grupo"].dropna().unique().tolist())
grupo_sel = st.sidebar.selectbox("Grupo", grupos_disp)

mascara_bi = pd.Series(True, index=df_bi_anos.index)
if not df_det_anos.empty:
    mascara_det = pd.Series(True, index=df_det_anos.index)

if meses_sel: 
    mascara_bi &= df_bi_anos["MesNome"].isin(meses_sel)
    if not df_det_anos.empty: mascara_det &= df_det_anos["MesNome"].isin(meses_sel)
        
if grupo_sel != "Todos": 
    mascara_bi &= df_bi_anos["Grupo"] == grupo_sel
    if not df_det_anos.empty: mascara_det &= df_det_anos["Grupo"] == grupo_sel

medicos_disp_base = df_bi_anos[mascara_bi]
medicos_lista = sorted(medicos_disp_base["Médico"].dropna().unique().tolist())
medicos_sel = st.sidebar.multiselect("Médicos (opcional)", medicos_lista)

if medicos_sel: 
    mascara_bi &= df_bi_anos["Médico"].isin(medicos_sel)
    if not df_det_anos.empty: mascara_det &= df_det_anos["Médico"].isin(medicos_sel)

df_filtrado = df_bi_anos[mascara_bi].copy()

if not df_det_anos.empty:
    df_det_filtrado = df_det_anos[mascara_det].copy()
    df_det_filtrado["AnoMesOrd"] = (df_det_filtrado["Ano"].astype(int) * 100) + df_det_filtrado["MesNum"].astype(int)
    df_det_filtrado = df_det_filtrado.sort_values("AnoMesOrd")
    df_det_filtrado["AnoMes"] = criar_ano_mes_label_vetorizado(df_det_filtrado["Ano"], df_det_filtrado["MesNum"])
else:
    df_det_filtrado = pd.DataFrame()

# =========================
# CABEÇALHO
# =========================
st.title("Dashboard de Produção Médica - HV")
st.caption("Visão consolidada de consultas, exames, cirurgias, lentes e procedimentos por médico, mês e grupo.")

# =========================
# ABAS (TABS)
# =========================
aba_geral, aba_rankings, aba_detalhada = st.tabs([
    "📊 Visão Geral e Perfil", 
    "🏆 Rankings (Top 10)",
    "🔍 Visão Detalhada (Raio-X)"
])

# ==========================================
# ABA 1 - VISÃO GERAL
# ==========================================
with aba_geral:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("1. Totais, Médias e Taxas de Conversão")

    total_cons = df_filtrado["Consultas"].sum()
    total_exam = df_filtrado["Exames"].sum()
    total_ciru = df_filtrado["Cirurgias"].sum()
    total_lent = df_filtrado["Lentes"].sum()
    total_proc = df_filtrado["Procedimentos"].sum()
    total_geral = df_filtrado["Total"].sum()

    meses_unicos = df_filtrado[["Ano", "MesNum"]].drop_duplicates().shape[0]
    if meses_unicos > 0:
        media_cons = total_cons / meses_unicos
        media_exam = total_exam / meses_unicos
        media_ciru = total_ciru / meses_unicos
        media_geral = total_geral / meses_unicos
    else:
        media_cons = media_exam = media_ciru = media_geral = 0

    taxa_exam_cons = (total_exam / total_cons) if total_cons > 0 else 0
    taxa_ciru_cons = (total_ciru / total_cons) if total_cons > 0 else 0
    cons_para_ciru = (1 / taxa_ciru_cons) if taxa_ciru_cons > 0 else 0

    st.markdown("**Volume Total**")
    st.markdown(f"""
        <div class="card-row">
            <div class="custom-metric-card card-col-6" style="border-left: 5px solid #4fd1c5;">
                <div class="custom-metric-title">Consultas</div>
                <div class="custom-metric-value">{formatar_num(total_cons)}</div>
            </div>
            <div class="custom-metric-card card-col-6" style="border-left: 5px solid #6b46c1;">
                <div class="custom-metric-title">Exames</div>
                <div class="custom-metric-value">{formatar_num(total_exam)}</div>
            </div>
            <div class="custom-metric-card card-col-6" style="border-left: 5px solid #3182ce;">
                <div class="custom-metric-title">Cirurgias</div>
                <div class="custom-metric-value">{formatar_num(total_ciru)}</div>
            </div>
            <div class="custom-metric-card card-col-6" style="border-left: 5px solid #ed64a6;">
                <div class="custom-metric-title">Lentes</div>
                <div class="custom-metric-value">{formatar_num(total_lent)}</div>
            </div>
            <div class="custom-metric-card card-col-6" style="border-left: 5px solid #f6ad55;">
                <div class="custom-metric-title">Procedimentos</div>
                <div class="custom-metric-value">{formatar_num(total_proc)}</div>
            </div>
            <div class="custom-metric-card card-col-6" style="border-left: 5px solid #2d3748; background-color: #f8fafc;">
                <div class="custom-metric-title" style="color: #4a5568;">Total Geral</div>
                <div class="custom-metric-value">{formatar_num(total_geral)}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("**Média Mensal**")
    st.markdown(f"""
        <div class="card-row">
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Média/mês (Consultas)</div>
                <div class="custom-metric-value">{formatar_num(media_cons)}</div>
            </div>
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Média/mês (Exames)</div>
                <div class="custom-metric-value">{formatar_num(media_exam)}</div>
            </div>
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Média/mês (Cirurgias)</div>
                <div class="custom-metric-value">{formatar_num(media_ciru)}</div>
            </div>
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Média/mês (Geral)</div>
                <div class="custom-metric-value">{formatar_num(media_geral)}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("**Taxas de Conversão (Global do Filtro)**")
    st.markdown(f"""
        <div class="card-row">
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Exames por Consulta</div>
                <div class="custom-metric-value">{taxa_exam_cons:.3f}x</div>
                <div class="custom-metric-sub">Para cada 1 consulta</div>
            </div>
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Conversão (Exames/Cons)</div>
                <div class="custom-metric-value">{formatar_pct(taxa_exam_cons * 100)}</div>
            </div>
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Conversão (Cirurgias/Cons)</div>
                <div class="custom-metric-value">{formatar_pct(taxa_ciru_cons * 100)}</div>
                <div class="custom-metric-sub">% de consultas que viram cirurgia</div>
            </div>
            <div class="custom-metric-card card-col-4" style="border-left: 4px solid #cbd5e0;">
                <div class="custom-metric-title">Consultas p/ 1 Cirurgia</div>
                <div class="custom-metric-value">{cons_para_ciru:.2f}</div>
                <div class="custom-metric-sub">Qtd média necessária</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    st.markdown("**Distribuição do Volume de Produção**")
    df_pizza_totais = pd.DataFrame({
        "Tipo": ["Consultas", "Exames", "Cirurgias", "Lentes", "Procedimentos"],
        "Volume": [total_cons, total_exam, total_ciru, total_lent, total_proc]
    })
    
    df_pizza_totais = df_pizza_totais[df_pizza_totais["Volume"] > 0]

    fig_pizza_totais = px.pie(
        df_pizza_totais, 
        names="Tipo", 
        values="Volume", 
        hole=0.4, 
        color_discrete_sequence=PALETA_LIGHT,
        template="plotly_white"
    )
    fig_pizza_totais.update_traces(textposition="inside", textinfo="percent+label")
    fig_pizza_totais.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    col_vazia1, col_grafico, col_vazia2 = st.columns([1, 2, 1])
    with col_grafico:
        st.plotly_chart(fig_pizza_totais, use_container_width=True)

    st.divider()

    df_mensal = (
        df_filtrado
        .groupby(["Ano", "MesNum", "MesNome"], as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
        .sum()
    )

    df_mensal["AnoMesOrd"] = (df_mensal["Ano"].astype(int) * 100) + df_mensal["MesNum"].astype(int)
    df_mensal = df_mensal.sort_values("AnoMesOrd")
    df_mensal["AnoMes"] = criar_ano_mes_label_vetorizado(df_mensal["Ano"], df_mensal["MesNum"])

    g1, g2 = st.columns(2)
    g3, g4 = st.columns(2)

    layout_padrao = dict(margin=dict(l=10, r=10, t=40, b=10), xaxis_title="", yaxis_title="Quantidade", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    with g1:
        fig_cons = px.area(df_mensal, x="AnoMes", y="Consultas", title="Consultas mensais (Ano/Mês)", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[0]])
        fig_cons.update_traces(mode='lines+markers').update_layout(**layout_padrao).update_xaxes(tickangle=-45)
        st.plotly_chart(fig_cons, use_container_width=True)

    with g2:
        fig_exam = px.area(df_mensal, x="AnoMes", y="Exames", title="Exames mensais (Ano/Mês)", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[1]])
        fig_exam.update_traces(mode='lines+markers').update_layout(**layout_padrao).update_xaxes(tickangle=-45)
        st.plotly_chart(fig_exam, use_container_width=True)

    with g3:
        fig_ciru = px.area(df_mensal, x="AnoMes", y="Cirurgias", title="Cirurgias mensais (Ano/Mês)", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[2]])
        fig_ciru.update_traces(mode='lines+markers').update_layout(**layout_padrao).update_xaxes(tickangle=-45)
        st.plotly_chart(fig_ciru, use_container_width=True)

    with g4:
        fig_total = px.area(df_mensal, x="AnoMes", y="Total", title="Total mensal (Todas as frentes)", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[3]])
        fig_total.update_traces(mode='lines+markers').update_layout(**layout_padrao).update_xaxes(tickangle=-45)
        st.plotly_chart(fig_total, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Item 2 - Participação por Médico
    df_medicos = (
        df_filtrado.groupby(["Médico", "Grupo"], as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
        .sum()
    )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("2. Participação de cada médico no total do período (%)")

    if df_medicos.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        base_perc = df_medicos.copy()
        base_perc["% Consultas"] = np.where(total_cons > 0, (base_perc["Consultas"] / total_cons) * 100, 0)
        base_perc["% Exames"] = np.where(total_exam > 0, (base_perc["Exames"] / total_exam) * 100, 0)
        base_perc["% Cirurgias"] = np.where(total_ciru > 0, (base_perc["Cirurgias"] / total_ciru) * 100, 0)

        altura_dinamica = max(400, len(base_perc) * 30)
        layout_perc = dict(margin=dict(l=10, r=40, t=40, b=10), yaxis_title="", xaxis_title="%", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

        fig_p_cons = px.bar(
            base_perc.sort_values("% Consultas", ascending=True),
            x="% Consultas", y="Médico", color="Grupo", orientation="h", title="% Consultas por médico",
            text="% Consultas", color_discrete_map=CORES_GRUPO, template="plotly_white"
        )
        fig_p_cons.update_traces(texttemplate='%{text:.1f}%', textposition='outside', cliponaxis=False, textangle=0)
        fig_p_cons.update_layout(**layout_perc, height=altura_dinamica)
        st.plotly_chart(fig_p_cons, use_container_width=True)

        st.divider()

        fig_p_exam = px.bar(
            base_perc.sort_values("% Exames", ascending=True),
            x="% Exames", y="Médico", color="Grupo", orientation="h", title="% Exames por médico",
            text="% Exames", color_discrete_map=CORES_GRUPO, template="plotly_white"
        )
        fig_p_exam.update_traces(texttemplate='%{text:.1f}%', textposition='outside', cliponaxis=False, textangle=0)
        fig_p_exam.update_layout(**layout_perc, height=altura_dinamica)
        st.plotly_chart(fig_p_exam, use_container_width=True)

        st.divider()

        fig_p_ciru = px.bar(
            base_perc.sort_values("% Cirurgias", ascending=True),
            x="% Cirurgias", y="Médico", color="Grupo", orientation="h", title="% Cirurgias por médico",
            text="% Cirurgias", color_discrete_map=CORES_GRUPO, template="plotly_white"
        )
        fig_p_ciru.update_traces(texttemplate='%{text:.1f}%', textposition='outside', cliponaxis=False, textangle=0)
        fig_p_ciru.update_layout(**layout_perc, height=altura_dinamica)
        st.plotly_chart(fig_p_ciru, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Item 3 - Produção por grupo 
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("3. Produção por grupo")

    df_grupo = (
        df_filtrado.groupby("Grupo", as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
        .sum()
    )

    if df_grupo.empty:
        st.info("Sem dados para os grupos no filtro atual.")
    else:
        g1, g2 = st.columns(2)

        with g1:
            fig_grupo = px.bar(
                df_grupo.melt(id_vars="Grupo", value_vars=["Consultas", "Exames", "Cirurgias"], var_name="Tipo", value_name="Quantidade"),
                x="Grupo", y="Quantidade", color="Tipo", barmode="group", text="Quantidade", title="Comparativo por grupo",
                template="plotly_white", color_discrete_sequence=PALETA_LIGHT
            )
            fig_grupo.update_traces(textangle=0, textposition='outside', cliponaxis=False)
            fig_grupo.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_grupo, use_container_width=True)

        with g2:
            df_socio_resto = df_filtrado.copy()
            df_socio_resto["Categoria"] = np.where(df_socio_resto["Grupo"] == "Sócios", "Sócios", "Restante")
            df_socio_resto = df_socio_resto.groupby("Categoria", as_index=False)["Total"].sum()

            fig_pizza_socio = px.pie(df_socio_resto, names="Categoria", values="Total", title="Sócios x Restante (Total de Atendimentos)", template="plotly_white", color_discrete_sequence=PALETA_LIGHT)
            fig_pizza_socio.update_traces(textposition="inside", textinfo="percent+label").update_layout(margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pizza_socio, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Item 4 - Perfil Clínico x Cirúrgico
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("4. Avaliação do perfil médico (Clínico x Cirúrgico)")

    st.markdown("""
    <div class='small-note'>
        <b>Entenda a classificação:</b><br>
        • <b>Clínico:</b> Foco em consultas e exames (baixa ou nenhuma taxa de cirurgias).<br>
        • <b>Cirúrgico:</b> Alta taxa de conversão para cirurgias (ou apenas realiza cirurgias).<br>
        • <b>Misto:</b> Perfil equilibrado entre consultas e cirurgias.
    </div><br>
    """, unsafe_allow_html=True)

    if df_medicos.empty:
        st.info("Sem dados para avaliar perfil.")
    else:
        df_perfil = df_medicos.copy()
        df_perfil["Taxa Cirúrgica"] = np.where(df_perfil["Consultas"] > 0, df_perfil["Cirurgias"] / df_perfil["Consultas"], 0)
        df_perfil["Perfil"] = classificar_perfil_vetorizado(df_perfil)

        p1, p2 = st.columns(2)

        with p1:
            df_perfil_pizza = df_perfil.groupby("Perfil", as_index=False)["Total"].sum()
            fig_pizza_perfil = px.pie(df_perfil_pizza, names="Perfil", values="Total", hole=0.4, title="Distribuição de atendimentos por perfil", template="plotly_white", color_discrete_sequence=PALETA_LIGHT)
            fig_pizza_perfil.update_traces(textposition="inside", textinfo="percent+label").update_layout(margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pizza_perfil, use_container_width=True)

        with p2:
            df_perfil_bar = df_perfil.groupby("Perfil", as_index=False)[["Consultas", "Exames", "Cirurgias"]].sum()
            fig_perfil_bar = px.bar(
                df_perfil_bar.melt(id_vars="Perfil", value_vars=["Consultas", "Exames", "Cirurgias"], var_name="Tipo", value_name="Quantidade"),
                x="Perfil", y="Quantidade", color="Tipo", barmode="group", title="Produção por perfil", template="plotly_white", color_discrete_sequence=PALETA_LIGHT
            )
            fig_perfil_bar.update_traces(textangle=0, textposition='outside', cliponaxis=False)
            fig_perfil_bar.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_perfil_bar, use_container_width=True)

        tabela_perfil = df_perfil[["Médico", "Grupo", "Consultas", "Exames", "Cirurgias", "Taxa Cirúrgica", "Perfil"]].copy()
        tabela_perfil["Taxa Cirúrgica"] = tabela_perfil["Taxa Cirúrgica"].map("{:.2f}".format)
        tabela_perfil = tabela_perfil.sort_values(["Perfil", "Cirurgias", "Consultas"], ascending=[True, False, False])

        with st.expander("Ver tabela de classificação de perfil"):
            st.dataframe(tabela_perfil, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 2 - RANKINGS (TOP 10 LÍDERES)
# ==========================================
with aba_rankings:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Líderes de Produção (Top 10)")
    st.caption("Ranking dinâmico baseado no filtro de data e grupo selecionado.")

    df_rank = df_filtrado.groupby(["Médico", "Grupo"], as_index=False).agg({
        "Consultas": "sum",
        "Exames": "sum",
        "Cirurgias": "sum",
        "Lentes": "sum",
        "Procedimentos": "sum",
        "Procedimentos e Lentes": "sum",
        "Total": "sum"
    })

    def plot_ranking(df, col, titulo, cor):
        top_df = df[df[col] > 0].nlargest(10, col).sort_values(col, ascending=True)
        if top_df.empty: return None
        
        fig = px.bar(top_df, x=col, y="Médico", orientation='h', 
                     title=titulo, text=col, color_discrete_sequence=[cor], template="plotly_white")
        
        fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)
        fig.update_layout(margin=dict(l=10, r=40, t=40, b=10), height=350, yaxis_title="", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    r1, r2 = st.columns(2)
    
    with r1:
        fig_geral = plot_ranking(df_rank, "Total", "🏆 Top 10 - Produção Geral", PALETA_LIGHT[0])
        if fig_geral: st.plotly_chart(fig_geral, use_container_width=True)
        else: st.info("Sem dados para Produção Geral")

        fig_exames = plot_ranking(df_rank, "Exames", "🔍 Top 10 - Exames", PALETA_LIGHT[1])
        if fig_exames: st.plotly_chart(fig_exames, use_container_width=True)
        else: st.info("Sem dados para Exames")

        fig_proc = plot_ranking(df_rank, "Procedimentos e Lentes", "⚙️ Top 10 - Proced. & Lentes", PALETA_LIGHT[5])
        if fig_proc: st.plotly_chart(fig_proc, use_container_width=True)
        else: st.info("Sem dados para Procedimentos e Lentes")

    with r2:
        fig_cons = plot_ranking(df_rank, "Consultas", "👨‍⚕️ Top 10 - Consultas", PALETA_LIGHT[2])
        if fig_cons: st.plotly_chart(fig_cons, use_container_width=True)
        else: st.info("Sem dados para Consultas")

        fig_ciru = plot_ranking(df_rank, "Cirurgias", "🔪 Top 10 - Cirurgias", PALETA_LIGHT[3])
        if fig_ciru: st.plotly_chart(fig_ciru, use_container_width=True)
        else: st.info("Sem dados para Cirurgias")

    st.divider()
    with st.expander("Ver Tabela Completa de Produção"):
        st.dataframe(
            df_rank[["Médico", "Grupo", "Total", "Consultas", "Exames", "Cirurgias", "Procedimentos e Lentes"]]
            .rename(columns={'Procedimentos e Lentes': 'Procedimentos & Lentes'})
            .sort_values("Total", ascending=False), 
            use_container_width=True, 
            hide_index=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# ABA 3 - VISÃO DETALHADA (KLINGO) "O Raio-X"
# ==========================================
with aba_detalhada:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Raio-X Analítico: Especialidades, Exames e Cirurgias")
    st.caption("Visão granular mês a mês e por médico (Dados mapeados pelo sistema Klingo).")

    if df_det_filtrado.empty:
        st.warning("Não há dados detalhados (Klingo) para os filtros atuais.")
    else:
        # ----- VISÃO GERAL DE ESPECIALIDADES -----
        df_cat_total = df_det_filtrado.groupby("Categoria", as_index=False)["Quantidade"].sum()
        df_cat_total = df_cat_total[df_cat_total["Quantidade"] > 0].sort_values("Quantidade", ascending=True)
        
        st.markdown("**1. Produção por Especialidade Mapeada**")
        if not df_cat_total.empty:
            fig_cat = px.bar(
                df_cat_total, x="Quantidade", y="Categoria", orientation="h",
                text="Quantidade", template="plotly_white", 
                color_discrete_sequence=[PALETA_LIGHT[0]]
            )
            fig_cat.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_cat.update_layout(margin=dict(t=10, l=10, r=40, b=10), height=350, yaxis_title="")
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nenhuma categoria encontrada.")

        st.divider()

        # ==========================================
        # BLOCO 2: FOCO EM EXAMES
        # ==========================================
        st.markdown("### 🔬 Foco Operacional: EXAMES")
        df_top_exames = df_det_filtrado[df_det_filtrado["Grupo_Geral"].str.upper() == "EXAMES"]
        
        if not df_top_exames.empty:
            # 1. Ranking Full Width dos Exames
            df_ex = df_top_exames.groupby("Procedimento", as_index=False)["Quantidade"].sum().nlargest(15, "Quantidade").sort_values("Quantidade", ascending=True)
            fig_ex = px.bar(df_ex, x="Quantidade", y="Procedimento", orientation="h", title="Top 15 Exames Mais Realizados", text="Quantidade", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[1]])
            fig_ex.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_ex.update_layout(margin=dict(t=40, l=10, r=40, b=10), height=450, yaxis_title="")
            st.plotly_chart(fig_ex, use_container_width=True)

            # 2. Evolução dos Exames (Gráfico de Barras Agrupadas)
            top_5_ex = df_ex.nlargest(5, "Quantidade")["Procedimento"].tolist()
            df_evo_ex = df_top_exames[df_top_exames["Procedimento"].isin(top_5_ex)]
            df_evo_ex = df_evo_ex.groupby(["AnoMesOrd", "AnoMes", "Procedimento"], as_index=False)["Quantidade"].sum().sort_values("AnoMesOrd")
            
            fig_evo_ex = px.bar(
                df_evo_ex, x="AnoMes", y="Quantidade", color="Procedimento", barmode="group", 
                text="Quantidade", title="Evolução Mensal em Barras (Top 5 Exames)", 
                template="plotly_white", color_discrete_sequence=PALETA_LIGHT
            )
            fig_evo_ex.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_evo_ex.update_layout(margin=dict(t=40, l=10, r=10, b=10), height=400, xaxis_title="", yaxis_title="Qtd")
            st.plotly_chart(fig_evo_ex, use_container_width=True)

            # 3. Top 10 Médicos em Exames Clássico
            df_med_ex = df_top_exames.groupby("Médico", as_index=False)["Quantidade"].sum().nlargest(10, "Quantidade").sort_values("Quantidade", ascending=True)
            fig_med_ex = px.bar(df_med_ex, x="Quantidade", y="Médico", orientation="h", title="Top 10 Médicos em Volume Geral de Exames", text="Quantidade", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[0]])
            fig_med_ex.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_med_ex.update_layout(margin=dict(t=40, l=10, r=40, b=10), height=400, yaxis_title="")
            st.plotly_chart(fig_med_ex, use_container_width=True)

        else:
            st.info("Nenhum exame detalhado encontrado.")

        st.divider()

        # ==========================================
        # BLOCO 3: FOCO EM CIRURGIAS
        # ==========================================
        st.markdown("### 🔪 Foco Operacional: CIRURGIAS")
        df_top_cirurgias = df_det_filtrado[df_det_filtrado["Grupo_Geral"].str.upper() == "CIRURGIAS"]
        
        if not df_top_cirurgias.empty:
            # 1. Ranking Full Width das Cirurgias
            df_cir = df_top_cirurgias.groupby("Procedimento", as_index=False)["Quantidade"].sum().nlargest(15, "Quantidade").sort_values("Quantidade", ascending=True)
            fig_cir = px.bar(df_cir, x="Quantidade", y="Procedimento", orientation="h", title="Top 15 Cirurgias Mais Realizadas", text="Quantidade", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[2]])
            fig_cir.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_cir.update_layout(margin=dict(t=40, l=10, r=40, b=10), height=450, yaxis_title="")
            st.plotly_chart(fig_cir, use_container_width=True)

            # 2. Evolução das Cirurgias (Gráfico de Barras Agrupadas)
            top_5_cir = df_cir.nlargest(5, "Quantidade")["Procedimento"].tolist()
            df_evo_cir = df_top_cirurgias[df_top_cirurgias["Procedimento"].isin(top_5_cir)]
            df_evo_cir = df_evo_cir.groupby(["AnoMesOrd", "AnoMes", "Procedimento"], as_index=False)["Quantidade"].sum().sort_values("AnoMesOrd")
            
            fig_evo_cir = px.bar(
                df_evo_cir, x="AnoMes", y="Quantidade", color="Procedimento", barmode="group", 
                text="Quantidade", title="Evolução Mensal em Barras (Top 5 Cirurgias)", 
                template="plotly_white", color_discrete_sequence=PALETA_LIGHT
            )
            fig_evo_cir.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_evo_cir.update_layout(margin=dict(t=40, l=10, r=10, b=10), height=400, xaxis_title="", yaxis_title="Qtd")
            st.plotly_chart(fig_evo_cir, use_container_width=True)

            # 3. Top 10 Médicos em Cirurgias Clássico
            df_med_cir = df_top_cirurgias.groupby("Médico", as_index=False)["Quantidade"].sum().nlargest(10, "Quantidade").sort_values("Quantidade", ascending=True)
            fig_med_cir = px.bar(df_med_cir, x="Quantidade", y="Médico", orientation="h", title="Top 10 Cirurgiões em Volume Geral", text="Quantidade", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[0]])
            fig_med_cir.update_traces(textposition="outside", textangle=0, cliponaxis=False)
            fig_med_cir.update_layout(margin=dict(t=40, l=10, r=40, b=10), height=400, yaxis_title="")
            st.plotly_chart(fig_med_cir, use_container_width=True)
        else:
            st.info("Nenhuma cirurgia detalhada encontrada.")

        st.divider()

        # ==========================================
        # BLOCO 4: RAIO-X INDIVIDUAL (O PERFIL DO MÉDICO)
        # ==========================================
        st.markdown("### 👨‍⚕️ Raio-X Individual por Médico")
        st.caption("Selecione um médico abaixo para destrinchar exatamente quais categorias e procedimentos compõem o volume dele.")
        
        medicos_detalhe = sorted(df_det_filtrado["Médico"].unique().tolist())
        if medicos_detalhe:
            medico_sel_raiox = st.selectbox("Selecione o Médico para análise:", medicos_detalhe)
            df_med_raiox = df_det_filtrado[df_det_filtrado["Médico"] == medico_sel_raiox]
            
            rx1, rx2 = st.columns(2)
            with rx1:
                df_cat_med = df_med_raiox.groupby("Categoria", as_index=False)["Quantidade"].sum().sort_values("Quantidade", ascending=True)
                fig_rx_cat = px.bar(df_cat_med, x="Quantidade", y="Categoria", orientation="h", title=f"Foco de Especialidade - {medico_sel_raiox}", text="Quantidade", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[6]])
                fig_rx_cat.update_traces(textposition="outside", textangle=0, cliponaxis=False)
                fig_rx_cat.update_layout(height=400, yaxis_title="", margin=dict(r=40))
                st.plotly_chart(fig_rx_cat, use_container_width=True)
                
            with rx2:
                df_proc_med = df_med_raiox.groupby("Procedimento", as_index=False)["Quantidade"].sum().nlargest(10, "Quantidade").sort_values("Quantidade", ascending=True)
                fig_rx_proc = px.bar(df_proc_med, x="Quantidade", y="Procedimento", orientation="h", title=f"Top 10 Procedimentos Específicos - {medico_sel_raiox}", text="Quantidade", template="plotly_white", color_discrete_sequence=[PALETA_LIGHT[7]])
                fig_rx_proc.update_traces(textposition="outside", textangle=0, cliponaxis=False)
                fig_rx_proc.update_layout(height=400, yaxis_title="", margin=dict(r=40))
                st.plotly_chart(fig_rx_proc, use_container_width=True)

        st.divider()

        # ----- LINHA 5: Tabela Analítica de Cruzamento -----
        st.markdown("**Tabela Analítica (Cruzamento Flexível de Dados)**")
        
        filtro_col1, filtro_col2, filtro_col3 = st.columns(3)
        
        grupos_det = ["Todos"] + sorted(df_det_filtrado["Grupo_Geral"].unique().tolist())
        g_sel = filtro_col1.selectbox("Filtrar por Frente (Ex: Cirurgias)", grupos_det)
        
        df_mostrar = df_det_filtrado.copy()
        if g_sel != "Todos":
            df_mostrar = df_mostrar[df_mostrar["Grupo_Geral"] == g_sel]

        categorias_det = ["Todas"] + sorted(df_mostrar["Categoria"].unique().tolist())
        cat_sel = filtro_col2.selectbox("Filtrar por Especialidade (Ex: Córnea)", categorias_det)
        if cat_sel != "Todas":
            df_mostrar = df_mostrar[df_mostrar["Categoria"] == cat_sel]
            
        procedimentos_det = ["Todos"] + sorted(df_mostrar["Procedimento"].unique().tolist())
        proc_sel = filtro_col3.selectbox("Procedimento Específico", procedimentos_det)
        if proc_sel != "Todos":
            df_mostrar = df_mostrar[df_mostrar["Procedimento"] == proc_sel]
            
        df_tabela_final = df_mostrar.groupby(["Ano", "MesNome", "Médico", "Grupo_Geral", "Categoria", "Procedimento"], as_index=False)["Quantidade"].sum()
        df_tabela_final = df_tabela_final.sort_values(by="Quantidade", ascending=False).rename(columns={"MesNome": "Mês"})
        
        st.dataframe(df_tabela_final, use_container_width=True, hide_index=True)
        
    st.markdown('</div>', unsafe_allow_html=True)