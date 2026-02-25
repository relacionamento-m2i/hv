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
# DICIONÁRIOS GLOBAIS (OTIMIZAÇÃO)
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
    "CAMILA LACERDA", "GABRIELLA ALVES", "ISABELLA W QUEIROGA", "KEYLLA MENEZES", "MARIELLE MEDEIROS"
}

FELLOWS = {
    "LUIZ CARLOS FILHO", "MARCELLA HANNAH", "TIAGO GRANA",
    "RODRIGO MACIEL", "ROBERTA FERNANDA", "JOAO VITOR BRUSQUI"
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
    # Usa vetorização do Pandas em vez de apply linha a linha
    meses_str = meses.map(MESES_ABREV).fillna("")
    return meses_str + "/" + anos.astype(str)

def classificar_perfil_vetorizado(df):
    # Classificação extremamente mais rápida usando Numpy Select
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

    # Otimização: Força para numérico de forma vetorizada e já soma o total na base
    for col in ["Consultas", "Exames", "Cirurgias"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    
    df["Total"] = df["Consultas"] + df["Exames"] + df["Cirurgias"]

    df["Médico"] = df["Médico"].astype(str).str.strip().str.upper()

    # Otimização: Uso de Map em vez de apply para normalizar meses
    df["Mês"] = df["Mês"].astype(str).str.strip().str.upper()
    
    # Extrai números se for string com número, senão usa o dicionário MESES_ORDEM
    numeros_mes = df["Mês"].str.extract(r'(\d+)')[0]
    df["MesNum"] = pd.to_numeric(numeros_mes, errors='coerce')
    df["MesNum"] = df["MesNum"].fillna(df["Mês"].map(MESES_ORDEM))
    
    df["MesNome"] = df["MesNum"].map(MESES_NOME).fillna(df["Mês"])

    # Otimização: Uso de Numpy Where em vez de apply para classificar grupos
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

# Lógica de filtro encadeada otimizada
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
st.subheader("1. Totais gerais e evolução mensal")

total_cons = df_filtrado["Consultas"].sum()
total_exam = df_filtrado["Exames"].sum()
total_ciru = df_filtrado["Cirurgias"].sum()
total_geral = df_filtrado["Total"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Consultas", formatar_num(total_cons))
c2.metric("Exames", formatar_num(total_exam))
c3.metric("Cirurgias", formatar_num(total_ciru))
c4.metric("Total geral", formatar_num(total_geral))

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

# Otimização nos gráficos: Redução de repetição no update_layout
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
# ITEM 2 - PARTICIPAÇÃO (%) POR MÉDICO
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("2. Participação de cada médico no total do período (%)")

if df_medicos.empty:
    st.info("Sem dados para os filtros selecionados.")
else:
    base_perc = df_medicos.copy()
    
    # Evitando divisão por zero na criação das porcentagens
    base_perc["% Consultas"] = np.where(total_cons > 0, (base_perc["Consultas"] / total_cons) * 100, 0)
    base_perc["% Exames"] = np.where(total_exam > 0, (base_perc["Exames"] / total_exam) * 100, 0)
    base_perc["% Cirurgias"] = np.where(total_ciru > 0, (base_perc["Cirurgias"] / total_ciru) * 100, 0)

    p1, p2, p3 = st.columns(3)
    layout_perc = dict(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="%")

    with p1:
        fig_p_cons = px.bar(
            base_perc.sort_values("% Consultas", ascending=True),
            x="% Consultas", y="Médico", color="Grupo", orientation="h", title="% Consultas por médico"
        )
        fig_p_cons.update_layout(**layout_perc)
        st.plotly_chart(fig_p_cons, use_container_width=True)

    with p2:
        fig_p_exam = px.bar(
            base_perc.sort_values("% Exames", ascending=True),
            x="% Exames", y="Médico", color="Grupo", orientation="h", title="% Exames por médico"
        )
        fig_p_exam.update_layout(**layout_perc)
        st.plotly_chart(fig_p_exam, use_container_width=True)

    with p3:
        fig_p_ciru = px.bar(
            base_perc.sort_values("% Cirurgias", ascending=True),
            x="% Cirurgias", y="Médico", color="Grupo", orientation="h", title="% Cirurgias por médico"
        )
        fig_p_ciru.update_layout(**layout_perc)
        st.plotly_chart(fig_p_ciru, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ITEM 3 - TOP 3 RANKINGS (BARRAS)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("3. Ranking de médicos (1º, 2º e 3º lugar)")

if df_medicos.empty:
    st.info("Sem dados para montar ranking.")
else:
    r1, r2, r3 = st.columns(3)
    layout_top = dict(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="")

    # nlargest é mais eficiente que sort_values().head()
    top_cons = df_medicos.nlargest(3, "Consultas").sort_values("Consultas", ascending=True)
    top_exam = df_medicos.nlargest(3, "Exames").sort_values("Exames", ascending=True)
    top_ciru = df_medicos.nlargest(3, "Cirurgias").sort_values("Cirurgias", ascending=True)

    with r1:
        fig_top_cons = px.bar(top_cons, x="Consultas", y="Médico", color="Grupo", orientation="h", text="Consultas", title="Top 3 - Consultas")
        fig_top_cons.update_layout(**layout_top)
        st.plotly_chart(fig_top_cons, use_container_width=True)

    with r2:
        fig_top_exam = px.bar(top_exam, x="Exames", y="Médico", color="Grupo", orientation="h", text="Exames", title="Top 3 - Exames")
        fig_top_exam.update_layout(**layout_top)
        st.plotly_chart(fig_top_exam, use_container_width=True)

    with r3:
        fig_top_ciru = px.bar(top_ciru, x="Cirurgias", y="Médico", color="Grupo", orientation="h", text="Cirurgias", title="Top 3 - Cirurgias")
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
    # Usando np.where para evitar divisão por zero
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

# =========================
# ITEM 6 - RESUMO ANALÍTICO E INSIGHTS
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("6. Resumo analítico e insights")

if df_filtrado.empty:
    st.info("Sem dados para gerar insights com os filtros selecionados.")
else:
    # A base já tem a coluna 'Total' devido a otimização inicial
    df_filtrado["Semestre"] = np.where(df_filtrado["MesNum"] <= 6, "1º semestre", "2º semestre")

    serie_mensal = df_mensal.copy()

    if len(serie_mensal) >= 2:
        ultimo = serie_mensal.iloc[-1]
        penultimo = serie_mensal.iloc[-2]
        var_ult_mensal = variacao_pct(ultimo["Total"], penultimo["Total"])
    else:
        ultimo = penultimo = var_ult_mensal = None

    pico_total = serie_mensal.loc[serie_mensal["Total"].idxmax()] if not serie_mensal.empty else None
    vale_total = serie_mensal.loc[serie_mensal["Total"].idxmin()] if not serie_mensal.empty else None

    anual = df_filtrado.groupby("Ano", as_index=False)["Total"].sum().sort_values("Ano")
    semestral = df_filtrado.groupby(["Ano", "Semestre"], as_index=False)["Total"].sum()
    piv_semestral = semestral.pivot_table(index="Ano", columns="Semestre", values="Total", aggfunc="sum").reset_index()

    anos_ord = sorted(df_filtrado["Ano"].dropna().unique().tolist())
    ano_inicial = anos_ord[0] if anos_ord else None
    ano_final = anos_ord[-1] if anos_ord else None

    med_ano = df_filtrado.groupby(["Ano", "Médico"], as_index=False)["Total"].sum()

    crescimento_medico = pd.DataFrame()
    if len(anos_ord) >= 2:
        ini = med_ano[med_ano["Ano"] == ano_inicial][["Médico", "Total"]].rename(columns={"Total": "Total_Inicial"})
        fim = med_ano[med_ano["Ano"] == ano_final][["Médico", "Total"]].rename(columns={"Total": "Total_Final"})
        crescimento_medico = ini.merge(fim, on="Médico", how="outer").fillna(0)
        crescimento_medico["Variação_Abs"] = crescimento_medico["Total_Final"] - crescimento_medico["Total_Inicial"]
        crescimento_medico["Variação_%"] = np.where(
            crescimento_medico["Total_Inicial"] > 0,
            ((crescimento_medico["Total_Final"] - crescimento_medico["Total_Inicial"]) / crescimento_medico["Total_Inicial"]) * 100,
            np.nan
        )
        crescimento_medico = crescimento_medico.sort_values("Variação_Abs", ascending=False)

    conc = df_filtrado.groupby("Médico", as_index=False)["Total"].sum().sort_values("Total", ascending=False)
    total_global = conc["Total"].sum() if not conc.empty else 0
    perc_top5 = (conc.head(5)["Total"].sum() / total_global * 100) if total_global > 0 else 0
    perc_top10 = (conc.head(10)["Total"].sum() / total_global * 100) if total_global > 0 else 0

    perfil_med = df_medicos.copy()
    perfil_med["Taxa_Cirurgica"] = np.where(perfil_med["Consultas"] > 0, perfil_med["Cirurgias"] / perfil_med["Consultas"], 0)
    perfil_med = perfil_med[perfil_med["Total"] >= 30]

    top_cirurgico = perfil_med.nlargest(3, "Taxa_Cirurgica")
    top_clinico = perfil_med.nsmallest(3, "Taxa_Cirurgica")

    volatilidade = None
    if len(serie_mensal) >= 3 and serie_mensal["Total"].mean() > 0:
        volatilidade = (serie_mensal["Total"].std() / serie_mensal["Total"].mean()) * 100

    comparativo_ytd_texto = None
    if len(anos_ord) >= 2:
        ultimo_ano = max(anos_ord)
        max_mes_ultimo_ano = df_filtrado.loc[df_filtrado["Ano"] == ultimo_ano, "MesNum"].max()

        if pd.notna(max_mes_ultimo_ano):
            max_mes_ultimo_ano = int(max_mes_ultimo_ano)
            base_ytd = df_filtrado[df_filtrado["MesNum"] <= max_mes_ultimo_ano]
            ytd_ano = base_ytd.groupby("Ano", as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]].sum().sort_values("Ano")

            comps = []
            for i in range(1, len(ytd_ano)):
                a_ant, a_atu = int(ytd_ano.iloc[i-1]["Ano"]), int(ytd_ano.iloc[i]["Ano"])
                v_total = variacao_pct(ytd_ano.iloc[i]["Total"], ytd_ano.iloc[i-1]["Total"])
                v_cons = variacao_pct(ytd_ano.iloc[i]["Consultas"], ytd_ano.iloc[i-1]["Consultas"])
                v_exam = variacao_pct(ytd_ano.iloc[i]["Exames"], ytd_ano.iloc[i-1]["Exames"])
                v_ciru = variacao_pct(ytd_ano.iloc[i]["Cirurgias"], ytd_ano.iloc[i-1]["Cirurgias"])
                
                periodo_label = f"Jan-{MESES_ABREV.get(max_mes_ultimo_ano, str(max_mes_ultimo_ano))}"

                comps.append(
                    f"{periodo_label}/{a_atu} vs {periodo_label}/{a_ant}: "
                    f"Total {formatar_pct(v_total) if v_total is not None else 'n/a'} | "
                    f"Consultas {formatar_pct(v_cons) if v_cons is not None else 'n/a'} | "
                    f"Exames {formatar_pct(v_exam) if v_exam is not None else 'n/a'} | "
                    f"Cirurgias {formatar_pct(v_ciru) if v_ciru is not None else 'n/a'}"
                )

            if comps:
                comparativo_ytd_texto = "Na comparação de mesmo período entre anos (ajuste de sazonalidade), os resultados foram: " + " | ".join(comps) + ". Essa leitura é a mais adequada quando o ano atual ainda está incompleto."

    # =========================
    # TEXTOS FINAIS
    # =========================
    st.write(f"No recorte atual, o volume consolidado foi de {formatar_num(total_geral)} procedimentos, sendo {formatar_num(total_cons)} consultas, {formatar_num(total_exam)} exames e {formatar_num(total_ciru)} cirurgias.")

    if pico_total is not None and vale_total is not None:
        st.write(f"O maior volume mensal ocorreu em {pico_total['AnoMes']} ({formatar_num(pico_total['Total'])}), enquanto o menor volume foi em {vale_total['AnoMes']} ({formatar_num(vale_total['Total'])}). Isso ajuda a identificar sazonalidade operacional e meses de maior pressão sobre agenda e equipe.")

    if var_ult_mensal is not None and ultimo is not None and penultimo is not None:
        st.write(f"Na comparação do último mês da série ({ultimo['AnoMes']}) com o mês imediatamente anterior ({penultimo['AnoMes']}), houve {'crescimento' if var_ult_mensal >= 0 else 'queda'} de {formatar_pct(abs(var_ult_mensal))} no volume total. Esse indicador é importante para monitorar aceleração ou perda de tração recente.")

    if comparativo_ytd_texto:
        st.write(comparativo_ytd_texto)

    if len(anual) >= 2:
        comparacoes_anuais = [f"{int(anual.loc[i, 'Ano'])} vs {int(anual.loc[i-1, 'Ano'])}: {formatar_pct(variacao_pct(anual.loc[i, 'Total'], anual.loc[i-1, 'Total']))}" for i in range(1, len(anual)) if variacao_pct(anual.loc[i, 'Total'], anual.loc[i-1, 'Total']) is not None]
        if comparacoes_anuais:
            st.write("Na comparação anual consolidada (considerando apenas o recorte filtrado), a variação do volume total foi: " + " | ".join(comparacoes_anuais) + ".")

    if not piv_semestral.empty:
        linhas_sem = []
        for _, row in piv_semestral.iterrows():
            ano = int(row["Ano"])
            s1, s2 = row.get("1º semestre", pd.NA), row.get("2º semestre", pd.NA)
            meses_ano = set(df_filtrado.loc[df_filtrado["Ano"] == ano, "MesNum"].dropna().astype(int).tolist())
            if pd.notna(s1) and pd.notna(s2) and s1 != 0 and any(m in meses_ano for m in range(1,7)) and any(m in meses_ano for m in range(7,13)):
                v_sem = variacao_pct(s2, s1)
                if v_sem is not None:
                    linhas_sem.append(f"{ano}: 2º semestre {'acima' if v_sem >= 0 else 'abaixo'} do 1º em {formatar_pct(abs(v_sem))}")
        if linhas_sem:
            st.write("Na leitura intranual por semestre, observou-se: " + " | ".join(linhas_sem) + ". Essa comparação é útil para identificar ganho de maturidade operacional ao longo do ano.")

    if total_global > 0 and not conc.empty:
        st.write(f"A produção está concentrada: os 5 médicos com maior volume representam {formatar_pct(perc_top5)} do total, e os 10 primeiros concentram {formatar_pct(perc_top10)}. Esse indicador ajuda a avaliar risco de dependência operacional em poucos profissionais.")

    if not crescimento_medico.empty:
        crescem = crescimento_medico[crescimento_medico["Variação_Abs"] > 0].head(3)
        caem = crescimento_medico.sort_values("Variação_Abs").head(3)
        trechos = []
        
        def formatar_medico_var(r):
             return f"{r['Médico']} ({formatar_num(r['Variação_Abs'])}; {formatar_pct(r['Variação_%'])})" if pd.notna(r["Variação_%"]) else f"{r['Médico']} ({formatar_num(r['Variação_Abs'])})"

        if not crescem.empty:
            trechos.append("maiores avanços: " + ", ".join([formatar_medico_var(r) for _, r in crescem.iterrows()]))
        if not caem.empty:
            trechos.append("maiores reduções: " + ", ".join([formatar_medico_var(r) for _, r in caem.iterrows()]))

        if trechos:
            st.write(f"Comparando {int(ano_inicial)} com {int(ano_final)} no nível individual (volume total por médico), observam-se " + " | ".join(trechos) + ". Isso ajuda a identificar médicos em expansão, estabilidade ou retração de produção.")

    if not perfil_med.empty:
        if not top_cirurgico.empty:
            st.write("Entre os médicos com maior peso cirúrgico (considerando volume mínimo para evitar distorção), destacam-se: " + ", ".join([f"{r['Médico']} (taxa {r['Taxa_Cirurgica']:.2f})" for _, r in top_cirurgico.iterrows()]) + ". Essa leitura ajuda a organizar agenda, bloco cirúrgico e suporte assistencial.")
        if not top_clinico.empty:
            st.write("No perfil mais clínico, destacam-se: " + ", ".join([f"{r['Médico']} (taxa {r['Taxa_Cirurgica']:.2f})" for _, r in top_clinico.iterrows()]) + ". Esses nomes tendem a sustentar fluxo de consultas e geração de demanda diagnóstica.")

    if volatilidade is not None:
        st.write(f"A volatilidade mensal do volume total (desvio padrão relativo) está em {formatar_pct(volatilidade)}. Volatilidade mais alta costuma indicar necessidade de reforço de previsibilidade de agenda, campanhas e cadência comercial.")

st.markdown('</div>', unsafe_allow_html=True)