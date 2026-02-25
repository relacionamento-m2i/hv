import streamlit as st
import pandas as pd
import plotly.express as px
import os

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
# FUNÇÕES AUXILIARES
# =========================
MESES_ORDEM = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12
}

def normalizar_mes(valor):
    if pd.isna(valor):
        return None
    v = str(valor).strip()
    if v.isdigit():
        return int(v)
    return MESES_ORDEM.get(v.upper(), None)

def nome_mes(valor):
    mapa = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    return mapa.get(valor, str(valor))

def abreviar_mes(mes_num):
    mapa = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }
    return mapa.get(mes_num, str(mes_num))

def criar_ano_mes_label(row):
    ano = int(row["Ano"]) if pd.notna(row["Ano"]) else ""
    mes = int(row["MesNum"]) if pd.notna(row["MesNum"]) else ""
    return f"{abreviar_mes(mes)}/{ano}"

def classificar_perfil(row):
    consultas = row["Consultas"]
    cirurgias = row["Cirurgias"]
    exames = row["Exames"]

    if consultas == 0 and cirurgias > 0:
        return "Cirúrgico"
    if cirurgias == 0 and consultas > 0:
        return "Clínico"
    if consultas == 0 and cirurgias == 0 and exames > 0:
        return "Diagnóstico"
    if consultas > 0:
        taxa = cirurgias / consultas
        if taxa >= 0.35:
            return "Cirúrgico"
        elif taxa <= 0.10:
            return "Clínico"
        else:
            return "Misto"
    return "Baixo volume"

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

def adicionar_linha_total(df_tabela, colunas_soma, rotulo_col="Médico", rotulo="TOTAL"):
    if df_tabela.empty:
        return df_tabela
    total_row = {c: "" for c in df_tabela.columns}
    total_row[rotulo_col] = rotulo
    for c in colunas_soma:
        if c in df_tabela.columns:
            total_row[c] = pd.to_numeric(df_tabela[c], errors="coerce").fillna(0).sum()
    return pd.concat([df_tabela, pd.DataFrame([total_row])], ignore_index=True)

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
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Médico"] = df["Médico"].astype(str).str.strip().str.upper()

    df["MesNum"] = df["Mês"].apply(normalizar_mes)
    df["MesNome"] = df["MesNum"].apply(nome_mes)

    socios = [
        "FERNANDO GADELHA",
        "ALINE PAIVA",
        "ANA ELISABETH",
        "CAMILA GADELHA",
        "CAMILA LACERDA",
        "GABRIELLA ALVES",
        "ISABELLA W QUEIROGA",
        "KEYLLA MENEZES",
        "MARIELLE MEDEIROS",
    ]

    fellows = [
        "LUIZ CARLOS FILHO",
        "MARCELLA HANNAH",
        "TIAGO GRANA",
        "RODRIGO MACIEL",
        "ROBERTA FERNANDA",
        "JOAO VITOR BRUSQUI",
    ]

    def classificar_grupo(nome):
        if nome in socios:
            return "Sócios"
        elif nome in fellows:
            return "Fellows"
        return "Corpo Clínico"

    df["Grupo"] = df["Médico"].apply(classificar_grupo)
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

meses_ordenados = (
    df[["MesNum", "MesNome"]]
    .dropna()
    .drop_duplicates()
    .sort_values("MesNum")
)

lista_meses = meses_ordenados["MesNome"].tolist()
meses_sel = st.sidebar.multiselect("Mês(es)", lista_meses, default=lista_meses)

grupos_disp = ["Todos"] + sorted(df["Grupo"].dropna().unique().tolist())
grupo_sel = st.sidebar.selectbox("Grupo", grupos_disp)

medicos_disp_base = df_base_anos.copy()
if meses_sel:
    medicos_disp_base = medicos_disp_base[medicos_disp_base["MesNome"].isin(meses_sel)]
if grupo_sel != "Todos":
    medicos_disp_base = medicos_disp_base[medicos_disp_base["Grupo"] == grupo_sel]

medicos_lista = sorted(medicos_disp_base["Médico"].dropna().unique().tolist())
medicos_sel = st.sidebar.multiselect("Médicos (opcional)", medicos_lista)

# Aplicar filtros principais
df_filtrado = df_base_anos.copy()

if meses_sel:
    df_filtrado = df_filtrado[df_filtrado["MesNome"].isin(meses_sel)]

if grupo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Grupo"] == grupo_sel]

if medicos_sel:
    df_filtrado = df_filtrado[df_filtrado["Médico"].isin(medicos_sel)]

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
total_geral = total_cons + total_exam + total_ciru

c1, c2, c3, c4 = st.columns(4)
c1.metric("Consultas", formatar_num(total_cons))
c2.metric("Exames", formatar_num(total_exam))
c3.metric("Cirurgias", formatar_num(total_ciru))
c4.metric("Total geral", formatar_num(total_geral))

# Base cronológica Ano/Mês
df_base_mensal = df_base_anos.copy()
if grupo_sel != "Todos":
    df_base_mensal = df_base_mensal[df_base_mensal["Grupo"] == grupo_sel]
if medicos_sel:
    df_base_mensal = df_base_mensal[df_base_mensal["Médico"].isin(medicos_sel)]
if meses_sel:
    df_base_mensal = df_base_mensal[df_base_mensal["MesNome"].isin(meses_sel)]

df_mensal = (
    df_base_mensal
    .groupby(["Ano", "MesNum", "MesNome"], as_index=False)[["Consultas", "Exames", "Cirurgias"]]
    .sum()
)

df_mensal["Total"] = df_mensal["Consultas"] + df_mensal["Exames"] + df_mensal["Cirurgias"]
df_mensal["AnoMesOrd"] = (df_mensal["Ano"].astype(int) * 100) + df_mensal["MesNum"].astype(int)
df_mensal = df_mensal.sort_values("AnoMesOrd")
df_mensal["AnoMes"] = df_mensal.apply(criar_ano_mes_label, axis=1)

g1, g2 = st.columns(2)
g3, g4 = st.columns(2)

with g1:
    fig_cons = px.bar(df_mensal, x="AnoMes", y="Consultas", text="Consultas", title="Consultas mensais (Ano/Mês)")
    fig_cons.update_traces(textposition="outside")
    fig_cons.update_layout(margin=dict(l=10, r=10, t=40, b=10), xaxis_title="", yaxis_title="Quantidade")
    fig_cons.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_cons, use_container_width=True)

with g2:
    fig_exam = px.bar(df_mensal, x="AnoMes", y="Exames", text="Exames", title="Exames mensais (Ano/Mês)")
    fig_exam.update_traces(textposition="outside")
    fig_exam.update_layout(margin=dict(l=10, r=10, t=40, b=10), xaxis_title="", yaxis_title="Quantidade")
    fig_exam.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_exam, use_container_width=True)

with g3:
    fig_ciru = px.bar(df_mensal, x="AnoMes", y="Cirurgias", text="Cirurgias", title="Cirurgias mensais (Ano/Mês)")
    fig_ciru.update_traces(textposition="outside")
    fig_ciru.update_layout(margin=dict(l=10, r=10, t=40, b=10), xaxis_title="", yaxis_title="Quantidade")
    fig_ciru.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_ciru, use_container_width=True)

with g4:
    fig_total = px.bar(df_mensal, x="AnoMes", y="Total", text="Total", title="Total mensal (Consultas + Exames + Cirurgias)")
    fig_total.update_traces(textposition="outside")
    fig_total.update_layout(margin=dict(l=10, r=10, t=40, b=10), xaxis_title="", yaxis_title="Quantidade")
    fig_total.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_total, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# BASE POR MÉDICO (PERÍODO FILTRADO)
# =========================
df_medicos = (
    df_filtrado.groupby(["Médico", "Grupo"], as_index=False)[["Consultas", "Exames", "Cirurgias"]]
    .sum()
)
df_medicos["Total"] = df_medicos["Consultas"] + df_medicos["Exames"] + df_medicos["Cirurgias"]

# =========================
# ITEM 2 - PARTICIPAÇÃO (%) POR MÉDICO
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("2. Participação de cada médico no total do período (%)")

if df_medicos.empty:
    st.info("Sem dados para os filtros selecionados.")
else:
    base_perc = df_medicos.copy()

    soma_cons = base_perc["Consultas"].sum()
    soma_exam = base_perc["Exames"].sum()
    soma_ciru = base_perc["Cirurgias"].sum()

    base_perc["% Consultas"] = ((base_perc["Consultas"] / soma_cons) * 100).fillna(0)
    base_perc["% Exames"] = ((base_perc["Exames"] / soma_exam) * 100).fillna(0)
    base_perc["% Cirurgias"] = ((base_perc["Cirurgias"] / soma_ciru) * 100).fillna(0)
    base_perc = base_perc.sort_values("Total", ascending=False)

    p1, p2, p3 = st.columns(3)

    with p1:
        fig_p_cons = px.bar(
            base_perc.sort_values("% Consultas", ascending=True),
            x="% Consultas", y="Médico", color="Grupo",
            orientation="h", title="% Consultas por médico"
        )
        fig_p_cons.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="%")
        st.plotly_chart(fig_p_cons, use_container_width=True)

    with p2:
        fig_p_exam = px.bar(
            base_perc.sort_values("% Exames", ascending=True),
            x="% Exames", y="Médico", color="Grupo",
            orientation="h", title="% Exames por médico"
        )
        fig_p_exam.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="%")
        st.plotly_chart(fig_p_exam, use_container_width=True)

    with p3:
        fig_p_ciru = px.bar(
            base_perc.sort_values("% Cirurgias", ascending=True),
            x="% Cirurgias", y="Médico", color="Grupo",
            orientation="h", title="% Cirurgias por médico"
        )
        fig_p_ciru.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="%")
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

    top_cons = df_medicos.sort_values("Consultas", ascending=False).head(3).copy()
    top_exam = df_medicos.sort_values("Exames", ascending=False).head(3).copy()
    top_ciru = df_medicos.sort_values("Cirurgias", ascending=False).head(3).copy()

    with r1:
        fig_top_cons = px.bar(
            top_cons.sort_values("Consultas"),
            x="Consultas", y="Médico", color="Grupo",
            orientation="h", text="Consultas", title="Top 3 - Consultas"
        )
        fig_top_cons.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_top_cons, use_container_width=True)

    with r2:
        fig_top_exam = px.bar(
            top_exam.sort_values("Exames"),
            x="Exames", y="Médico", color="Grupo",
            orientation="h", text="Exames", title="Top 3 - Exames"
        )
        fig_top_exam.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_top_exam, use_container_width=True)

    with r3:
        fig_top_ciru = px.bar(
            top_ciru.sort_values("Cirurgias"),
            x="Cirurgias", y="Médico", color="Grupo",
            orientation="h", text="Cirurgias", title="Top 3 - Cirurgias"
        )
        fig_top_ciru.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_top_ciru, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ITEM 4 - PRODUÇÃO POR GRUPO + PIZZA (SÓCIOS X RESTANTE)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("4. Produção por grupo")

df_grupo = (
    df_filtrado.groupby("Grupo", as_index=False)[["Consultas", "Exames", "Cirurgias"]]
    .sum()
)

if df_grupo.empty:
    st.info("Sem dados para os grupos no filtro atual.")
else:
    df_grupo["Total"] = df_grupo["Consultas"] + df_grupo["Exames"] + df_grupo["Cirurgias"]

    g1, g2 = st.columns(2)

    with g1:
        fig_grupo = px.bar(
            df_grupo.melt(
                id_vars="Grupo",
                value_vars=["Consultas", "Exames", "Cirurgias"],
                var_name="Tipo",
                value_name="Quantidade"
            ),
            x="Grupo", y="Quantidade", color="Tipo",
            barmode="group", text="Quantidade", title="Comparativo por grupo"
        )
        fig_grupo.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
        st.plotly_chart(fig_grupo, use_container_width=True)

    with g2:
        df_socio_resto = df_filtrado.copy()
        df_socio_resto["Categoria"] = df_socio_resto["Grupo"].apply(lambda x: "Sócios" if x == "Sócios" else "Restante")
        df_socio_resto = (
            df_socio_resto.groupby("Categoria", as_index=False)[["Consultas", "Exames", "Cirurgias"]]
            .sum()
        )
        df_socio_resto["Total"] = df_socio_resto["Consultas"] + df_socio_resto["Exames"] + df_socio_resto["Cirurgias"]

        fig_pizza_socio = px.pie(
            df_socio_resto, names="Categoria", values="Total",
            title="Sócios x Restante (participação no total)"
        )
        fig_pizza_socio.update_traces(textposition="inside", textinfo="percent+label")
        fig_pizza_socio.update_layout(margin=dict(l=10, r=10, t=40, b=10))
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
    df_perfil["Taxa Cirúrgica"] = (df_perfil["Cirurgias"] / df_perfil["Consultas"].replace(0, pd.NA)).fillna(0)
    df_perfil["Perfil"] = df_perfil.apply(classificar_perfil, axis=1)

    p1, p2 = st.columns(2)

    with p1:
        df_perfil_pizza = (
            df_perfil.groupby("Perfil", as_index=False)["Médico"]
            .count()
            .rename(columns={"Médico": "QtdMedicos"})
        )
        fig_pizza_perfil = px.pie(
            df_perfil_pizza, names="Perfil", values="QtdMedicos",
            title="Distribuição de perfis médicos"
        )
        fig_pizza_perfil.update_traces(textposition="inside", textinfo="percent+label")
        fig_pizza_perfil.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_pizza_perfil, use_container_width=True)

    with p2:
        df_perfil_bar = (
            df_perfil.groupby("Perfil", as_index=False)[["Consultas", "Exames", "Cirurgias"]]
            .sum()
        )
        fig_perfil_bar = px.bar(
            df_perfil_bar.melt(
                id_vars="Perfil",
                value_vars=["Consultas", "Exames", "Cirurgias"],
                var_name="Tipo",
                value_name="Quantidade"
            ),
            x="Perfil", y="Quantidade", color="Tipo",
            barmode="group", title="Produção por perfil"
        )
        fig_perfil_bar.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
        st.plotly_chart(fig_perfil_bar, use_container_width=True)

    tabela_perfil = df_perfil[[
        "Médico", "Grupo", "Consultas", "Exames", "Cirurgias", "Taxa Cirúrgica", "Perfil"
    ]].copy()
    tabela_perfil["Taxa Cirúrgica"] = tabela_perfil["Taxa Cirúrgica"].map(lambda x: f"{x:.2f}")
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
    # Base de análise geral (respeitando filtros)
    base = df_filtrado.copy()
    base["Total"] = base["Consultas"] + base["Exames"] + base["Cirurgias"]
    base["Semestre"] = base["MesNum"].apply(lambda x: "1º semestre" if pd.notna(x) and int(x) <= 6 else "2º semestre")

    # Série mensal consolidada
    serie_mensal = (
        base.groupby(["Ano", "MesNum", "MesNome"], as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
        .sum()
    )
    serie_mensal["AnoMesOrd"] = (serie_mensal["Ano"].astype(int) * 100) + serie_mensal["MesNum"].astype(int)
    serie_mensal = serie_mensal.sort_values("AnoMesOrd")
    serie_mensal["AnoMes"] = serie_mensal.apply(criar_ano_mes_label, axis=1)

    # Variação mensal do total
    if len(serie_mensal) >= 2:
        ultimo = serie_mensal.iloc[-1]
        penultimo = serie_mensal.iloc[-2]
        var_ult_mensal = variacao_pct(ultimo["Total"], penultimo["Total"])
    else:
        ultimo = None
        penultimo = None
        var_ult_mensal = None

    # Picos e vales
    pico_total = serie_mensal.loc[serie_mensal["Total"].idxmax()] if not serie_mensal.empty else None
    vale_total = serie_mensal.loc[serie_mensal["Total"].idxmin()] if not serie_mensal.empty else None

    # Comparação anual consolidada
    anual = (
        base.groupby("Ano", as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
        .sum()
        .sort_values("Ano")
    )

    # Comparação por semestre
    semestral = (
        base.groupby(["Ano", "Semestre"], as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
        .sum()
    )

    # Tabela pivô para comparar semestres entre anos
    piv_semestral = semestral.pivot_table(index="Ano", columns="Semestre", values="Total", aggfunc="sum").reset_index()
    if "1º semestre" not in piv_semestral.columns:
        piv_semestral["1º semestre"] = pd.NA
    if "2º semestre" not in piv_semestral.columns:
        piv_semestral["2º semestre"] = pd.NA
    piv_semestral = piv_semestral.sort_values("Ano")

    # Evolução por médico (comparando primeiro vs último ano selecionado)
    anos_ord = sorted(base["Ano"].dropna().unique().tolist())
    ano_inicial = anos_ord[0]
    ano_final = anos_ord[-1]

    med_ano = (
        base.groupby(["Ano", "Médico"], as_index=False)[["Consultas", "Exames", "Cirurgias"]]
        .sum()
    )
    med_ano["Total"] = med_ano["Consultas"] + med_ano["Exames"] + med_ano["Cirurgias"]

    crescimento_medico = pd.DataFrame()
    if len(anos_ord) >= 2:
        ini = med_ano[med_ano["Ano"] == ano_inicial][["Médico", "Total"]].rename(columns={"Total": "Total_Inicial"})
        fim = med_ano[med_ano["Ano"] == ano_final][["Médico", "Total"]].rename(columns={"Total": "Total_Final"})
        crescimento_medico = ini.merge(fim, on="Médico", how="outer").fillna(0)
        crescimento_medico["Variação_Abs"] = crescimento_medico["Total_Final"] - crescimento_medico["Total_Inicial"]
        crescimento_medico["Variação_%"] = crescimento_medico.apply(
            lambda r: variacao_pct(r["Total_Final"], r["Total_Inicial"]) if r["Total_Inicial"] > 0 else None,
            axis=1
        )
        crescimento_medico = crescimento_medico.sort_values("Variação_Abs", ascending=False)

    # Concentração de produção (Top 5 / Top 10)
    conc = (
        base.groupby("Médico", as_index=False)["Total"]
        .sum()
        .sort_values("Total", ascending=False)
    )
    total_global = conc["Total"].sum() if not conc.empty else 0
    top5_total = conc.head(5)["Total"].sum() if not conc.empty else 0
    top10_total = conc.head(10)["Total"].sum() if not conc.empty else 0
    perc_top5 = (top5_total / total_global * 100) if total_global > 0 else 0
    perc_top10 = (top10_total / total_global * 100) if total_global > 0 else 0

    # Médicos com maior peso cirúrgico (mínimo volume)
    perfil_med = (
        base.groupby(["Médico", "Grupo"], as_index=False)[["Consultas", "Exames", "Cirurgias"]]
        .sum()
    )
    perfil_med["Total"] = perfil_med["Consultas"] + perfil_med["Exames"] + perfil_med["Cirurgias"]
    perfil_med["Taxa_Cirurgica"] = (perfil_med["Cirurgias"] / perfil_med["Consultas"].replace(0, pd.NA)).fillna(0)
    perfil_med = perfil_med[perfil_med["Total"] >= 30]

    top_cirurgico = perfil_med.sort_values("Taxa_Cirurgica", ascending=False).head(3)
    top_clinico = perfil_med.sort_values("Taxa_Cirurgica", ascending=True).head(3)

    # Volatilidade mensal
    volatilidade = None
    if len(serie_mensal) >= 3 and serie_mensal["Total"].mean() > 0:
        volatilidade = (serie_mensal["Total"].std() / serie_mensal["Total"].mean()) * 100

    # =========================
    # NOVO BLOCO: COMPARAÇÃO DO MESMO PERÍODO (YTD)
    # =========================
    comparativo_ytd_texto = None
    if len(anos_ord) >= 2:
        ultimo_ano = max(anos_ord)
        # Último mês disponível do ano mais recente dentro do recorte filtrado
        max_mes_ultimo_ano = base.loc[base["Ano"] == ultimo_ano, "MesNum"].dropna().max()

        if pd.notna(max_mes_ultimo_ano):
            max_mes_ultimo_ano = int(max_mes_ultimo_ano)

            # Base equivalente: todos os anos até o mesmo mês do último ano
            base_ytd = base[base["MesNum"] <= max_mes_ultimo_ano].copy()

            ytd_ano = (
                base_ytd.groupby("Ano", as_index=False)[["Consultas", "Exames", "Cirurgias", "Total"]]
                .sum()
                .sort_values("Ano")
            )

            # Compara ano a ano no mesmo período (ex.: Jan-Jul)
            comps = []
            for i in range(1, len(ytd_ano)):
                a_ant = int(ytd_ano.iloc[i-1]["Ano"])
                a_atu = int(ytd_ano.iloc[i]["Ano"])

                v_total = variacao_pct(ytd_ano.iloc[i]["Total"], ytd_ano.iloc[i-1]["Total"])
                v_cons = variacao_pct(ytd_ano.iloc[i]["Consultas"], ytd_ano.iloc[i-1]["Consultas"])
                v_exam = variacao_pct(ytd_ano.iloc[i]["Exames"], ytd_ano.iloc[i-1]["Exames"])
                v_ciru = variacao_pct(ytd_ano.iloc[i]["Cirurgias"], ytd_ano.iloc[i-1]["Cirurgias"])

                periodo_label = f"Jan-{abreviar_mes(max_mes_ultimo_ano)}"

                trecho = (
                    f"{periodo_label}/{a_atu} vs {periodo_label}/{a_ant}: "
                    f"Total {formatar_pct(v_total) if v_total is not None else 'n/a'} | "
                    f"Consultas {formatar_pct(v_cons) if v_cons is not None else 'n/a'} | "
                    f"Exames {formatar_pct(v_exam) if v_exam is not None else 'n/a'} | "
                    f"Cirurgias {formatar_pct(v_ciru) if v_ciru is not None else 'n/a'}"
                )
                comps.append(trecho)

            if comps:
                comparativo_ytd_texto = (
                    "Na comparação de mesmo período entre anos (ajuste de sazonalidade), os resultados foram: "
                    + " | ".join(comps)
                    + ". Essa leitura é a mais adequada quando o ano atual ainda está incompleto."
                )

    # =========================
    # TEXTO FINAL (INSIGHTS)
    # =========================
    textos = []

    textos.append(
        f"No recorte atual, o volume consolidado foi de {formatar_num(total_geral)} procedimentos, "
        f"sendo {formatar_num(total_cons)} consultas, {formatar_num(total_exam)} exames e {formatar_num(total_ciru)} cirurgias."
    )

    if pico_total is not None and vale_total is not None:
        textos.append(
            f"O maior volume mensal ocorreu em {pico_total['AnoMes']} ({formatar_num(pico_total['Total'])}), "
            f"enquanto o menor volume foi em {vale_total['AnoMes']} ({formatar_num(vale_total['Total'])}). "
            f"Isso ajuda a identificar sazonalidade operacional e meses de maior pressão sobre agenda e equipe."
        )

    if var_ult_mensal is not None and ultimo is not None and penultimo is not None:
        direcao = "crescimento" if var_ult_mensal >= 0 else "queda"
        textos.append(
            f"Na comparação do último mês da série ({ultimo['AnoMes']}) com o mês imediatamente anterior ({penultimo['AnoMes']}), "
            f"houve {direcao} de {formatar_pct(abs(var_ult_mensal))} no volume total. "
            f"Esse indicador é importante para monitorar aceleração ou perda de tração recente."
        )

    # NOVO: comparação YTD (mesmo período entre anos)
    if comparativo_ytd_texto:
        textos.append(comparativo_ytd_texto)

    # Comparação anual consolidada (mantém, mas é bom deixar claro que é consolidado do recorte)
    if len(anual) >= 2:
        comparacoes_anuais = []
        anual = anual.sort_values("Ano").reset_index(drop=True)
        for i in range(1, len(anual)):
            ano_atual = anual.loc[i, "Ano"]
            ano_ant = anual.loc[i-1, "Ano"]
            v = variacao_pct(anual.loc[i, "Total"], anual.loc[i-1, "Total"])
            if v is not None:
                comparacoes_anuais.append(f"{int(ano_atual)} vs {int(ano_ant)}: {formatar_pct(v)}")
        if comparacoes_anuais:
            textos.append(
                "Na comparação anual consolidada (considerando apenas o recorte filtrado), a variação do volume total foi: "
                + " | ".join(comparacoes_anuais)
                + "."
            )

    # Comparação semestral intranual (somente se os dois semestres estiverem presentes no ano)
    if not piv_semestral.empty:
        linhas_sem = []
        for _, row in piv_semestral.iterrows():
            ano = int(row["Ano"])
            s1 = row.get("1º semestre", pd.NA)
            s2 = row.get("2º semestre", pd.NA)

            # Só compara se há meses dos dois semestres no recorte
            meses_ano = set(base.loc[base["Ano"] == ano, "MesNum"].dropna().astype(int).tolist())
            tem_s1 = any(m in meses_ano for m in [1,2,3,4,5,6])
            tem_s2 = any(m in meses_ano for m in [7,8,9,10,11,12])

            if pd.notna(s1) and pd.notna(s2) and s1 != 0 and tem_s1 and tem_s2:
                v_sem = variacao_pct(s2, s1)
                if v_sem is not None:
                    linhas_sem.append(
                        f"{ano}: 2º semestre {'acima' if v_sem >= 0 else 'abaixo'} do 1º em {formatar_pct(abs(v_sem))}"
                    )

        if linhas_sem:
            textos.append(
                "Na leitura intranual por semestre, observou-se: " + " | ".join(linhas_sem) + ". "
                "Essa comparação é útil para identificar ganho de maturidade operacional ao longo do ano."
            )

    # Concentração
    if total_global > 0 and not conc.empty:
        textos.append(
            f"A produção está concentrada: os 5 médicos com maior volume representam {formatar_pct(perc_top5)} do total, "
            f"e os 10 primeiros concentram {formatar_pct(perc_top10)}. "
            "Esse indicador ajuda a avaliar risco de dependência operacional em poucos profissionais."
        )

    # Evolução por médico (primeiro vs último ano)
    if not crescimento_medico.empty:
        crescem = crescimento_medico[crescimento_medico["Variação_Abs"] > 0].head(3)
        caem = crescimento_medico.sort_values("Variação_Abs").head(3)

        trechos = []

        if not crescem.empty:
            top_up = []
            for _, r in crescem.iterrows():
                if pd.notna(r["Variação_%"]):
                    top_up.append(f"{r['Médico']} ({formatar_num(r['Variação_Abs'])}; {formatar_pct(r['Variação_%'])})")
                else:
                    top_up.append(f"{r['Médico']} ({formatar_num(r['Variação_Abs'])})")
            trechos.append("maiores avanços: " + ", ".join(top_up))

        if not caem.empty:
            top_down = []
            for _, r in caem.iterrows():
                if pd.notna(r["Variação_%"]):
                    top_down.append(f"{r['Médico']} ({formatar_num(r['Variação_Abs'])}; {formatar_pct(r['Variação_%'])})")
                else:
                    top_down.append(f"{r['Médico']} ({formatar_num(r['Variação_Abs'])})")
            trechos.append("maiores reduções: " + ", ".join(top_down))

        if trechos:
            textos.append(
                f"Comparando {int(ano_inicial)} com {int(ano_final)} no nível individual (volume total por médico), observam-se "
                + " | ".join(trechos)
                + ". Isso ajuda a identificar médicos em expansão, estabilidade ou retração de produção."
            )

    # Perfil clínico x cirúrgico
    if not perfil_med.empty:
        if not top_cirurgico.empty:
            lista_cir = ", ".join([f"{r['Médico']} (taxa {r['Taxa_Cirurgica']:.2f})" for _, r in top_cirurgico.iterrows()])
            textos.append(
                "Entre os médicos com maior peso cirúrgico (considerando volume mínimo para evitar distorção), destacam-se: "
                + lista_cir
                + ". Essa leitura ajuda a organizar agenda, bloco cirúrgico e suporte assistencial."
            )
        if not top_clinico.empty:
            lista_cli = ", ".join([f"{r['Médico']} (taxa {r['Taxa_Cirurgica']:.2f})" for _, r in top_clinico.iterrows()])
            textos.append(
                "No perfil mais clínico, destacam-se: "
                + lista_cli
                + ". Esses nomes tendem a sustentar fluxo de consultas e geração de demanda diagnóstica."
            )

    if volatilidade is not None:
        textos.append(
            f"A volatilidade mensal do volume total (desvio padrão relativo) está em {formatar_pct(volatilidade)}. "
            "Volatilidade mais alta costuma indicar necessidade de reforço de previsibilidade de agenda, campanhas e cadência comercial."
        )

    for t in textos:
        st.write(t)

    st.markdown("#### Direcionamentos sugeridos")
    st.markdown("""
    - Monitorar mensalmente o volume por Ano/Mês e tratar quedas acima de 10% como alerta operacional/comercial.
    - Priorizar a comparação de mesmo período entre anos (ex.: Jan-Jul vs Jan-Jul) quando o ano atual estiver incompleto.
    - Comparar semestres equivalentes entre anos para medir crescimento real sem efeito sazonal.
    - Criar acompanhamento individual dos médicos com foco em tendência: crescimento, estabilidade ou queda por tipo de produção.
    - Separar estratégias por perfil médico (clínico, misto, cirúrgico) para ajustar agenda, oferta de exames e ocupação de bloco.
    - Reduzir dependência dos top produtores quando a concentração estiver alta, fortalecendo distribuição de demanda e previsibilidade da operação.
    """)

st.markdown('</div>', unsafe_allow_html=True)