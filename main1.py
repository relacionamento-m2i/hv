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
# ESTILO
# =========================
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
    }
    .section-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .small-note {
        color: #6c757d;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# DICIONÁRIOS GLOBAIS (OTIMIZAÇÃO) E CORES
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

# Fixando as cores para evitar confusão no visual
CORES_GRUPO = {
    "Sócios": "#0d6efd",         # Azul Escuro
    "Fellows": "#6ea8fe",        # Azul Claro
    "Corpo Clínico": "#dc3545"   # Vermelho
}

# =========================
# FUNÇÕES AUXILIARES OTIMIZADAS
# =========================
def formatar_num(n):
    try:
        return f"{float(n):,.0f}".replace(",", ".")
    except Exception:
        return "0"

def formatar_pct(v):
    try:
        return f"{v:.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"

def variacao_pct(atual, anterior):
    if anterior is None or pd.isna(anterior) or anterior == 0:
        return None
    return ((atual - anterior) / anterior) * 100

def criar_ano_mes_label_vetorizado(anos, meses):
    meses_str = meses.map(MESES_ABREV).fillna("")
    return meses_str + "/" + anos.astype(str)

def classificar_perfil_vetorizado(df):
    condicoes = [
        (df["Consultas"] == 0) & (df["Cirurgias"] > 0),
        (df["Cirurgias"] == 0) & (df["Consultas"] > 0),
        (df["Consultas"] == 0) & (df["Cirurgias"] == 0) & (df["Exames"] > 0),
        (df["Consultas"] > 0) & ((df["Cirurgias"] / df["Consultas"]) >= 0.35),
        (df["Consultas"] > 0) & ((df["Cirurgias"] / df["Consultas"]) <= 0.10)
    ]
    escolhas = ["Cirúrgico", "Clínico", "Diagnóstico", "Cirúrgico", "Clínico"]
    return np.select(condicoes, escolhas, default="Misto")

# =========================
# CARREGAR DADOS
# =========================
@st.cache_data
def carregar_dados():
    caminho_arquivo = "EXAME_Base_BI.xlsx"

    if not os.path.exists(caminho_arquivo):
        return pd.DataFrame()

    df = pd.read_excel(caminho_arquivo, engine="openpyxl")

    colunas_esperadas = ["Ano", "Mês", "Médico", "Consultas", "Exames", "Cirurgias"]
    for c in colunas_esperadas:
        if c not in df.columns:
            df[c] = 0 if c in ["Consultas", "Exames", "Cirurgias"] else None

    for col in ["Consultas", "Exames", "Cirurgias"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    
    df["Total"] = df["Consultas"] + df["Exames"] + df["Cirurgias"]
    df["Médico"] = df["Médico"].astype(str).str.strip().str.upper()
    df["Mês"] = df["Mês"].astype(str).str.strip().str.upper()
    
    numeros_mes = df["Mês"].str.extract(r'(\d+)')[0]
    df["MesNum"] = pd.to_numeric(numeros_mes, errors='coerce')
    df["MesNum"] = df["MesNum"].fillna(df["Mês"].map(MESES_ORDEM))
    df["MesNome"] = df["MesNum"].map(MESES_NOME).fillna(df["Mês"])

    df["Grupo"] = np.where(df["Médico"].isin(SOCIOS), "Sócios", 
                  np.where(df["Médico"].isin(FELLOWS), "Fellows", "Corpo Clínico"))

    return df

df = carregar_dados()

if df.empty:
    st.error("Arquivo 'EXAME_Base_BI.xlsx' não encontrado ou inválido. Coloque o arquivo na mesma pasta do app.")
    st.stop()

# =========================
# SIDEBAR - FILTROS
# =========================
st.sidebar.title("Filtros")

anos_disponiveis = sorted(df["Ano"].dropna().unique().tolist())
anos_sel = st.sidebar.multiselect("Ano(s)", anos_disponiveis, default=anos_disponiveis)

if not anos_sel:
    st.sidebar.warning("Selecione pelo menos 1 ano.")
    st.stop()

df_base_anos = df[df["Ano"].isin(anos_sel)].copy()

meses_ordenados = df_base_anos[["MesNum", "MesNome"]].dropna().drop_duplicates().sort_values("MesNum")
lista_meses = meses_ordenados["MesNome"].tolist()
meses_sel = st.sidebar.multiselect("Mês(es)", lista_meses, default=lista_meses)

grupos_disp = ["Todos"] + sorted(df["Grupo"].dropna().unique().tolist())
grupo_sel = st.sidebar.selectbox("Grupo", grupos_disp)

mascara = pd.Series(True, index=df_base_anos.index)
if meses_sel:
    mascara &= df_base_anos["MesNome"].isin(meses_sel)
if grupo_sel != "Todos":
    mascara &= df_base_anos["Grupo"] == grupo_sel

medicos_disp_base = df_base_anos[mascara]
medicos_lista = sorted(medicos_disp_base["Médico"].dropna().unique().tolist())
medicos_sel = st.sidebar.multiselect("Médicos (opcional)", medicos_lista)

if medicos_sel:
    mascara &= df_base_anos["Médico"].isin(medicos_sel)

df_filtrado = df_base_anos[mascara].copy()

# =========================
# CABEÇALHO
# =========================
st.title("Dashboard de Produção Médica - HV")
st.caption("Visão consolidada de consultas, exames e cirurgias por médico, mês e grupo.")

# =========================
# ITEM 1 - TOTAIS + EVOLUÇÃO MENSAL (ANO/MÊS)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("1. Totais, Médias e Taxas de Conversão")

# Cálculos Totais
total_cons = df_filtrado["Consultas"].sum()
total_exam = df_filtrado["Exames"].sum()
total_ciru = df_filtrado["Cirurgias"].sum()
total_geral = df_filtrado["Total"].sum()

# Cálculos Médias
meses_unicos = df_filtrado[["Ano", "MesNum"]].drop_duplicates().shape[0]
if meses_unicos > 0:
    media_cons = total_cons / meses_unicos
    media_exam = total_exam / meses_unicos
    media_ciru = total_ciru / meses_unicos
    media_geral = total_geral / meses_unicos
else:
    media_cons = media_exam = media_ciru = media_geral = 0

# Cálculos de Conversão
taxa_exam_cons = (total_exam / total_cons) if total_cons > 0 else 0
taxa_ciru_cons = (total_ciru / total_cons) if total_cons > 0 else 0
cons_para_ciru = (1 / taxa_ciru_cons) if taxa_ciru_cons > 0 else 0

# Exibição Totais
st.markdown("**Volume Total**")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tot. Consultas", formatar_num(total_cons))
c2.metric("Tot. Exames", formatar_num(total_exam))
c3.metric("Tot. Cirurgias", formatar_num(total_ciru))
c4.metric("Total Geral", formatar_num(total_geral))

st.write("") # Espaço em branco
# Exibição Médias
st.markdown("**Média Mensal**")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Média/mês (Consultas)", formatar_num(media_cons))
m2.metric("Média/mês (Exames)", formatar_num(media_exam))
m3.metric("Média/mês (Cirurgias)", formatar_num(media_ciru))
m4.metric("Média/mês (Geral)", formatar_num(media_geral))

st.write("") # Espaço em branco
# Exibição Conversões
st.markdown("**Taxas de Conversão (Global do Filtro)**")
t1, t2, t3, t4 = st.columns(4)

# Formatando direto com 2 casas decimais e trocando ponto por vírgula
t1.metric("Exames por Consulta", f"{taxa_exam_cons:.2f}x".replace(".", ","), help="Para cada 1 consulta, quantos exames são realizados.")
t2.metric("Conversão (Exames/Cons)", formatar_pct(taxa_exam_cons * 100))
t3.metric("Cirurgias por Consulta", f"{taxa_ciru_cons:.2f}x".replace(".", ","), help="Para cada 1 consulta, quantas cirurgias são realizadas.")
t4.metric("Consultas p/ 1 Cirurgia", f"{cons_para_ciru:.2f}".replace(".", ","), help="Quantas consultas em média são necessárias para gerar 1 cirurgia.")


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

layout_padrao = dict(margin=dict(l=10, r=10, t=40, b=10), xaxis_title="", yaxis_title="Quantidade")

with g1:
    fig_cons = px.bar(df_mensal, x="AnoMes", y="Consultas", text="Consultas", title="Consultas mensais (Ano/Mês)")
    fig_cons.update_traces(textposition="outside").update_layout(**layout_padrao).update_xaxes(tickangle=-45)
    st.plotly_chart(fig_cons, use_container_width=True)

with g2:
    fig_exam = px.bar(df_mensal, x="AnoMes", y="Exames", text="Exames", title="Exames mensais (Ano/Mês)")
    fig_exam.update_traces(textposition="outside").update_layout(**layout_padrao).update_xaxes(tickangle=-45)
    st.plotly_chart(fig_exam, use_container_width=True)

with g3:
    fig_ciru = px.bar(df_mensal, x="AnoMes", y="Cirurgias", text="Cirurgias", title="Cirurgias mensais (Ano/Mês)")
    fig_ciru.update_traces(textposition="outside").update_layout(**layout_padrao).update_xaxes(tickangle=-45)
    st.plotly_chart(fig_ciru, use_container_width=True)

with g4:
    fig_total = px.bar(df_mensal, x="AnoMes", y="Total", text="Total", title="Total mensal (Consultas + Exames + Cirurgias)")
    fig_total.update_traces(textposition="outside").update_layout(**layout_padrao).update_xaxes(tickangle=-45)
    st.plotly_chart(fig_total, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
# =========================
# BASE POR MÉDICO (PERÍODO FILTRADO)
# =========================
df_medicos = (
    df_filtrado.groupby(["Médico", "Grupo"], as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
    .sum()
)

# =========================
# ITEM 2 - PARTICIPAÇÃO (%) POR MÉDICO (ISOLADOS COM VALORES)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("2. Participação de cada médico no total do período (%)")

if df_medicos.empty:
    st.info("Sem dados para os filtros selecionados.")
else:
    base_perc = df_medicos.copy()
    
    base_perc["% Consultas"] = np.where(total_cons > 0, (base_perc["Consultas"] / total_cons) * 100, 0)
    base_perc["% Exames"] = np.where(total_exam > 0, (base_perc["Exames"] / total_exam) * 100, 0)
    base_perc["% Cirurgias"] = np.where(total_ciru > 0, (base_perc["Cirurgias"] / total_ciru) * 100, 0)

    # Cálculo da altura dinâmica: garante pelo menos 400px e expande se tiver muitos médicos
    altura_dinamica = max(400, len(base_perc) * 30)
    layout_perc = dict(margin=dict(l=10, r=40, t=40, b=10), yaxis_title="", xaxis_title="%")

    # Gráfico 1 - Consultas isolado
    fig_p_cons = px.bar(
        base_perc.sort_values("% Consultas", ascending=True),
        x="% Consultas", y="Médico", color="Grupo", orientation="h", title="% Consultas por médico",
        text="% Consultas", # Adicionado o parâmetro text
        color_discrete_map=CORES_GRUPO
    )
    # Formatação do texto e posicionamento fora da barra para ficar mais legível
    fig_p_cons.update_traces(texttemplate='%{text:.1f}%', textposition='outside', cliponaxis=False)
    fig_p_cons.update_layout(**layout_perc, height=altura_dinamica)
    st.plotly_chart(fig_p_cons, use_container_width=True)

    st.divider()

    # Gráfico 2 - Exames isolado
    fig_p_exam = px.bar(
        base_perc.sort_values("% Exames", ascending=True),
        x="% Exames", y="Médico", color="Grupo", orientation="h", title="% Exames por médico",
        text="% Exames", # Adicionado o parâmetro text
        color_discrete_map=CORES_GRUPO
    )
    fig_p_exam.update_traces(texttemplate='%{text:.1f}%', textposition='outside', cliponaxis=False)
    fig_p_exam.update_layout(**layout_perc, height=altura_dinamica)
    st.plotly_chart(fig_p_exam, use_container_width=True)

    st.divider()

    # Gráfico 3 - Cirurgias isolado
    fig_p_ciru = px.bar(
        base_perc.sort_values("% Cirurgias", ascending=True),
        x="% Cirurgias", y="Médico", color="Grupo", orientation="h", title="% Cirurgias por médico",
        text="% Cirurgias", # Adicionado o parâmetro text
        color_discrete_map=CORES_GRUPO
    )
    fig_p_ciru.update_traces(texttemplate='%{text:.1f}%', textposition='outside', cliponaxis=False)
    fig_p_ciru.update_layout(**layout_perc, height=altura_dinamica)
    st.plotly_chart(fig_p_ciru, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ITEM 3 - TOP 5 RANKINGS (BARRAS)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("3. Ranking de médicos (Top 5)")

if df_medicos.empty:
    st.info("Sem dados para montar ranking.")
else:
    r1, r2, r3 = st.columns(3)
    
    layout_top = dict(
        margin=dict(l=10, r=10, t=40, b=10), 
        yaxis_title="", 
        xaxis_title="",
        yaxis={'categoryorder': 'total ascending'}
    )

    top_cons = df_medicos.nlargest(5, "Consultas")
    top_exam = df_medicos.nlargest(5, "Exames")
    top_ciru = df_medicos.nlargest(5, "Cirurgias")

    with r1:
        fig_top_cons = px.bar(top_cons, x="Consultas", y="Médico", color="Grupo", 
                              orientation="h", text="Consultas", title="Top 5 - Consultas",
                              color_discrete_map=CORES_GRUPO)
        fig_top_cons.update_layout(**layout_top)
        st.plotly_chart(fig_top_cons, use_container_width=True)

    with r2:
        fig_top_exam = px.bar(top_exam, x="Exames", y="Médico", color="Grupo", 
                              orientation="h", text="Exames", title="Top 5 - Exames",
                              color_discrete_map=CORES_GRUPO)
        fig_top_exam.update_layout(**layout_top)
        st.plotly_chart(fig_top_exam, use_container_width=True)

    with r3:
        fig_top_ciru = px.bar(top_ciru, x="Cirurgias", y="Médico", color="Grupo", 
                              orientation="h", text="Cirurgias", title="Top 5 - Cirurgias",
                              color_discrete_map=CORES_GRUPO)
        fig_top_ciru.update_layout(**layout_top)
        st.plotly_chart(fig_top_ciru, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ITEM 4 - PRODUÇÃO POR GRUPO + PIZZA (SÓCIOS X RESTANTE)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("4. Produção por grupo")

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
            x="Grupo", y="Quantidade", color="Tipo", barmode="group", text="Quantidade", title="Comparativo por grupo"
        )
        fig_grupo.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
        st.plotly_chart(fig_grupo, use_container_width=True)

    with g2:
        df_socio_resto = df_filtrado.copy()
        df_socio_resto["Categoria"] = np.where(df_socio_resto["Grupo"] == "Sócios", "Sócios", "Restante")
        df_socio_resto = df_socio_resto.groupby("Categoria", as_index=False)["Total"].sum()

        fig_pizza_socio = px.pie(df_socio_resto, names="Categoria", values="Total", title="Sócios x Restante (participação no total)")
        fig_pizza_socio.update_traces(textposition="inside", textinfo="percent+label").update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_pizza_socio, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ITEM 5 - PERFIL CLÍNICO X CIRÚRGICO (PIZZA + BARRAS)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("5. Avaliação do perfil médico (Clínico x Cirúrgico)")

if df_medicos.empty:
    st.info("Sem dados para avaliar perfil.")
else:
    df_perfil = df_medicos.copy()
    df_perfil["Taxa Cirúrgica"] = np.where(df_perfil["Consultas"] > 0, df_perfil["Cirurgias"] / df_perfil["Consultas"], 0)
    df_perfil["Perfil"] = classificar_perfil_vetorizado(df_perfil)

    p1, p2 = st.columns(2)

    with p1:
        df_perfil_pizza = df_perfil.groupby("Perfil", as_index=False)["Médico"].count().rename(columns={"Médico": "QtdMedicos"})
        fig_pizza_perfil = px.pie(df_perfil_pizza, names="Perfil", values="QtdMedicos", title="Distribuição de perfis médicos")
        fig_pizza_perfil.update_traces(textposition="inside", textinfo="percent+label").update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_pizza_perfil, use_container_width=True)

    with p2:
        df_perfil_bar = df_perfil.groupby("Perfil", as_index=False)[["Consultas", "Exames", "Cirurgias"]].sum()
        fig_perfil_bar = px.bar(
            df_perfil_bar.melt(id_vars="Perfil", value_vars=["Consultas", "Exames", "Cirurgias"], var_name="Tipo", value_name="Quantidade"),
            x="Perfil", y="Quantidade", color="Tipo", barmode="group", title="Produção por perfil"
        )
        fig_perfil_bar.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
        st.plotly_chart(fig_perfil_bar, use_container_width=True)

    tabela_perfil = df_perfil[["Médico", "Grupo", "Consultas", "Exames", "Cirurgias", "Taxa Cirúrgica", "Perfil"]].copy()
    tabela_perfil["Taxa Cirúrgica"] = tabela_perfil["Taxa Cirúrgica"].map("{:.2f}".format)
    tabela_perfil = tabela_perfil.sort_values(["Perfil", "Cirurgias", "Consultas"], ascending=[True, False, False])

    with st.expander("Ver tabela de classificação de perfil"):
        st.dataframe(tabela_perfil, use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)