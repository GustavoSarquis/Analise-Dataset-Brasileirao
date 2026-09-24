import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(
    page_title="Dashboard Completo - Campeonato Brasileiro",
    page_icon="⚽",
    layout="wide"
)


# 2. Carregamento e Tratamento dos Dados
@st.cache_data
def carregar_dados():
    df_full = pd.read_csv("campeonato-brasileiro-full.csv")
    df_stats = pd.read_csv("campeonato-brasileiro-estatisticas-full.csv")
    df_gols = pd.read_csv("campeonato-brasileiro-gols.csv")
    df_cartoes = pd.read_csv("campeonato-brasileiro-cartoes.csv")

    # Limpeza de espaços em branco nos estádios
    df_full["arena"] = df_full["arena"].astype(str).str.strip()

    # Datas e Temporada
    df_full["data_dt"] = pd.to_datetime(df_full["data"], format="%d/%m/%Y", errors="coerce")
    df_full["temporada"] = df_full["data_dt"].dt.year

    # Ajuste da Temporada de 2020 (jogos ocorridos no início de 2021)
    df_full.loc[(df_full["data_dt"] >= "2021-01-01") & (df_full["data_dt"] <= "2021-02-28"), "temporada"] = 2020

    # Relacionar temporada aos outros datasets via partida_id
    mapa_temporadas = df_full.set_index("ID")["temporada"].to_dict()

    df_stats["temporada"] = df_stats["partida_id"].map(mapa_temporadas)
    df_gols["temporada"] = df_gols["partida_id"].map(mapa_temporadas)
    df_cartoes["temporada"] = df_cartoes["partida_id"].map(mapa_temporadas)

    # Tratamento de valores nulos no tipo de golo
    df_gols["tipo_de_gol"] = df_gols["tipo_de_gol"].fillna("Gol Normal")

    return df_full, df_stats, df_gols, df_cartoes


df_full, df_stats, df_gols, df_cartoes = carregar_dados()

# 3. Filtros na Barra Lateral (Sidebar)
st.sidebar.header("🔍 Filtros Globais")

# Filtro Temporada
temporadas_disponiveis = sorted([int(t) for t in df_full["temporada"].dropna().unique()], reverse=True)
opcao_temporada = st.sidebar.selectbox("Temporada", ["Todas"] + temporadas_disponiveis)

# Filtrar por temporada
if opcao_temporada != "Todas":
    f_full = df_full[df_full["temporada"] == opcao_temporada].copy()
    f_stats = df_stats[df_stats["temporada"] == opcao_temporada].copy()
    f_gols = df_gols[df_gols["temporada"] == opcao_temporada].copy()
    f_cartoes = df_cartoes[df_cartoes["temporada"] == opcao_temporada].copy()
else:
    f_full, f_stats, f_gols, f_cartoes = df_full.copy(), df_stats.copy(), df_gols.copy(), df_cartoes.copy()

# Filtro Clube
clubes_mandantes = set(f_full["mandante"].dropna())
clubes_visitantes = set(f_full["visitante"].dropna())
todos_clubes = sorted(list(clubes_mandantes.union(clubes_visitantes)))
opcao_clube = st.sidebar.selectbox("Clube", ["Todos"] + todos_clubes)

if opcao_clube != "Todos":
    f_full = f_full[(f_full["mandante"] == opcao_clube) | (f_full["visitante"] == opcao_clube)]
    f_stats = f_stats[f_stats["clube"] == opcao_clube]
    f_gols = f_gols[f_gols["clube"] == opcao_clube]
    f_cartoes = f_cartoes[f_cartoes["clube"] == opcao_clube]

# 4. Título Principal
st.title("⚽ Dashboard Analítico do Campeonato Brasileiro")

# 5. Separadores de Conteúdo (Tabs)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Visão Geral",
    "📊 Estatísticas de Equipes",
    "⚽ Artilharia & Gols",
    "🟨 Disciplina & Cartões",
    "🏟️ Estádios & Técnicos"
])

# --- TAB 1: VISÃO GERAL ---
with tab1:
    st.subheader("Indicadores Chave")
    c1, c2, c3, c4 = st.columns(4)

    total_jogos = len(f_full)

    # Correção do cálculo dos gols quando há filtro de clube
    if opcao_clube != "Todos":
        gols_mand = f_full[f_full["mandante"] == opcao_clube]["mandante_Placar"].sum()
        gols_vis = f_full[f_full["visitante"] == opcao_clube]["visitante_Placar"].sum()
    else:
        gols_mand = f_full["mandante_Placar"].sum()
        gols_vis = f_full["visitante_Placar"].sum()

    total_gols = gols_mand + gols_vis
    media_gols = (total_gols / total_jogos) if total_jogos > 0 else 0
    total_cartoes = len(f_cartoes)

    c1.metric("Total de Partidas", f"{total_jogos:,}")
    c2.metric("Total de Gols", f"{total_gols:,}")
    c3.metric("Média Gols / Jogo", f"{media_gols:.2f}")
    c4.metric("Total de Cartões", f"{total_cartoes:,}")

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Distribuição de Gols (Mandantes vs Visitantes)")
        df_local_gols = pd.DataFrame({
            "Mando": ["Mandante", "Visitante"],
            "Gols": [gols_mand, gols_vis]
        })
        fig_mando = px.pie(df_local_gols, names="Mando", values="Gols", hole=0.4,
                           color_discrete_sequence=["#1f77b4", "#ff7f0e"])
        st.plotly_chart(fig_mando, use_container_width=True)

    with col_g2:
        st.subheader("Resultados das Partidas")
        df_res = f_full.copy()
        df_res["Resultado"] = "Empate"
        df_res.loc[df_res["vencedor"] == df_res["mandante"], "Resultado"] = "Vitória Mandante"
        df_res.loc[df_res["vencedor"] == df_res["visitante"], "Resultado"] = "Vitória Visitante"

        fig_res = px.histogram(df_res, x="Resultado", color="Resultado",
                               color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_res, use_container_width=True)

    st.subheader("Lista de Partidas")
    st.dataframe(
        f_full[["data", "rodata", "mandante", "mandante_Placar", "visitante_Placar", "visitante", "arena",
                "vencedor"]].rename(
            columns={"rodata": "Rodada", "mandante_Placar": "Placar M", "visitante_Placar": "Placar V"}
        ),
        use_container_width=True
    )

# --- TAB 2: ESTATÍSTICAS DE EQUIPAS ---
# --- TAB 2: ESTATÍSTICAS DE EQUIPAS ---
with tab2:
    st.subheader("Desempenho Coletivo")

    # 1. Converte colunas para numérico garantindo que nulos virem 0
    cols_stats = ["chutes", "chutes_no_alvo", "passes", "faltas", "escanteios", "impedimentos"]
    for col in cols_stats:
        if col in f_stats.columns:
            f_stats[col] = pd.to_numeric(f_stats[col], errors="coerce").fillna(0)

    # 2. Filtra apenas os registros que possuem alguma estatística real (> 0)
    f_stats_validos = f_stats[f_stats[cols_stats].sum(axis=1) > 0]

    if not f_stats_validos.empty:
        df_agrupado_stats = f_stats_validos.groupby("clube")[cols_stats].mean().reset_index()

        st.write("Média por jogo de cada equipe no período selecionado:")
        st.dataframe(df_agrupado_stats.round(2), use_container_width=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Média de Chutes ao Alvo por Equipe")
            fig_chutes = px.bar(
                df_agrupado_stats.sort_values("chutes_no_alvo", ascending=False).head(10),
                x="clube", y="chutes_no_alvo", color="clube", title="Top 10 - Chutes no Alvo / Jogo"
            )
            st.plotly_chart(fig_chutes, use_container_width=True)

        with col_s2:
            st.subheader("Média de Faltas Cometidas por Equipe")
            fig_faltas = px.bar(
                df_agrupado_stats.sort_values("faltas", ascending=False).head(10),
                x="clube", y="faltas", color="clube", title="Top 10 - Mais Faltosas / Jogo"
            )
            st.plotly_chart(fig_faltas, use_container_width=True)
    else:
        st.warning(
            "⚠️ Não existem estatísticas detalhadas (chutes, faltas, etc.) registradas para o ano/clube selecionado no dataset.")

# --- TAB 3: ARTILHARIA & GOLOS ---
with tab3:
    st.subheader("Top Artilheiros")
    if not f_gols.empty:
        artilharia = f_gols["atleta"].value_counts().reset_index()
        artilharia.columns = ["Jogador", "Gols"]

        col_a1, col_a2 = st.columns([1, 2])
        with col_a1:
            st.dataframe(artilharia.head(15), use_container_width=True)

        with col_a2:
            fig_artilharia = px.bar(
                artilharia.head(10), x="Gols", y="Jogador", orientation="h",
                title="Top 10 Marcadores", color="Gols", color_continuous_scale="Viridis"
            )
            fig_artilharia.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_artilharia, use_container_width=True)

        st.markdown("---")
        col_g_tipo, col_g_min = st.columns(2)

        with col_g_tipo:
            st.subheader("Tipos de Gols")
            tipos_gol = f_gols["tipo_de_gol"].value_counts().reset_index()
            tipos_gol.columns = ["Tipo", "Quantidade"]
            fig_tipo_gol = px.pie(tipos_gol, names="Tipo", values="Quantidade", hole=0.3)
            st.plotly_chart(fig_tipo_gol, use_container_width=True)

        with col_g_min:
            st.subheader("Minutos dos Gols")
            df_gols_temp = f_gols.copy()

            # Limpeza do campo de minutos (tratando acréscimos)
            minutos_limpos = df_gols_temp["minuto"].astype(str).str.extract(r'(\d+)')[0]
            df_gols_temp["minuto_num"] = pd.to_numeric(minutos_limpos, errors="coerce")
            df_validos = df_gols_temp.dropna(subset=["minuto_num"])

            if not df_validos.empty:
                # 1. Agrupamos por intervalo de tempo (bins de 5 em 5 minutos para maior precisão)
                df_validos["intervalo"] = pd.cut(df_validos["minuto_num"], bins=range(0, 96, 5), right=False)
                df_histograma = df_validos.groupby("intervalo", observed=False).size().reset_index(name="Quantidade")

                # Formatamos a legenda do eixo X para ficar legível (ex: "40-45 min")
                df_histograma["Intervalo_Texto"] = df_histograma["intervalo"].apply(
                    lambda x: f"{int(x.left)}-{int(x.right)} min")

                # 2. Criamos o gráfico de barras com gradiente de cor baseado na quantidade de gols
                fig_minutos = px.bar(
                    df_histograma,
                    x="Intervalo_Texto",
                    y="Quantidade",
                    color="Quantidade",
                    color_continuous_scale="Viridis",  # Gradiente: do azul/roxo ao amarelo nos picos de gols
                    title="Frequência de Gols por Minuto de Jogo",
                    labels={"Intervalo_Texto": "Minuto do Jogo", "Quantidade": "Gols Marcados"}
                )

                # 3. Ajustes estéticos: bordas brancas e ocultar a barra de cor redundante
                fig_minutos.update_traces(marker_line_color='white', marker_line_width=1)
                fig_minutos.update_layout(coloraxis_showscale=False)

                st.plotly_chart(fig_minutos, use_container_width=True)
            else:
                st.info("Sem dados de minutos registrados.")

# --- TAB 4: DISCIPLINA & CARTÕES ---
with tab4:
    st.subheader("Análise de Disciplina")
    if not f_cartoes.empty:
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.subheader("Cartões Amarelos por Jogador")
            amarelos = f_cartoes[f_cartoes["cartao"] == "Amarelo"]["atleta"].value_counts().reset_index()
            amarelos.columns = ["Jogador", "Cartões Amarelos"]
            st.dataframe(amarelos.head(10), use_container_width=True)

        with col_c2:
            st.subheader("Cartões Vermelhos por Jogador")
            vermelhos = f_cartoes[f_cartoes["cartao"] == "Vermelho"]["atleta"].value_counts().reset_index()
            vermelhos.columns = ["Jogador", "Cartões Vermelhos"]
            st.dataframe(vermelhos.head(10), use_container_width=True)

        st.markdown("---")
        col_pos, col_tipo_c = st.columns(2)

        with col_pos:
            st.subheader("Cartões por Posição")
            cartoes_pos = f_cartoes["posicao"].value_counts().reset_index()
            cartoes_pos.columns = ["Posição", "Total Cartões"]
            fig_pos = px.bar(cartoes_pos.head(8), x="Posição", y="Total Cartões", color="Posição")
            st.plotly_chart(fig_pos, use_container_width=True)

        with col_tipo_c:
            st.subheader("Distribuição Geral de Cartões")
            dist_cartoes = f_cartoes["cartao"].value_counts().reset_index()
            dist_cartoes.columns = ["Tipo", "Total"]
            fig_dist_c = px.pie(dist_cartoes, names="Tipo", values="Total", color="Tipo",
                                color_discrete_map={"Amarelo": "#f1c40f", "Vermelho": "#e74c3c"})
            st.plotly_chart(fig_dist_c, use_container_width=True)
    else:
        st.info("Sem dados de cartões para os filtros selecionados.")

# --- TAB 5: ESTÁDIOS & TÉCNICOS ---
with tab5:
    st.subheader("🏟️ Principais Estádios e Técnicos")
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.subheader("Estádios com Mais Jogos")
        estadios = f_full["arena"].value_counts().head(10).reset_index()
        estadios.columns = ["Estádio / Arena", "Jogos"]
        fig_estadios = px.bar(estadios, x="Jogos", y="Estádio / Arena", orientation="h", color="Jogos",
                              color_continuous_scale="Blues")
        fig_estadios.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_estadios, use_container_width=True)

    with col_e2:
        st.subheader("Técnicos com Mais Jogos")
        tecnicos = pd.concat([f_full["tecnico_mandante"], f_full["tecnico_visitante"]]).value_counts().head(
            10).reset_index()
        tecnicos.columns = ["Técnico", "Jogos"]
        fig_tecnicos = px.bar(tecnicos, x="Jogos", y="Técnico", orientation="h", color="Jogos",
                              color_continuous_scale="Greens")
        fig_tecnicos.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_tecnicos, use_container_width=True)