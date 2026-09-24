import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Completo - Campeonato Brasileiro",
    page_icon="⚽",
    layout="wide"
)


@st.cache_data
def carregar_dados():
    df_full = pd.read_csv("campeonato-brasileiro-full.csv")
    df_stats = pd.read_csv("campeonato-brasileiro-estatisticas-full.csv")
    df_gols = pd.read_csv("campeonato-brasileiro-gols.csv")
    df_cartoes = pd.read_csv("campeonato-brasileiro-cartoes.csv")

    df_full["arena"] = df_full["arena"].astype(str).str.strip()

    df_full["data_dt"] = pd.to_datetime(df_full["data"], format="%d/%m/%Y", errors="coerce")
    df_full["temporada"] = df_full["data_dt"].dt.year

    df_full.loc[(df_full["data_dt"] >= "2021-01-01") & (df_full["data_dt"] <= "2021-02-28"), "temporada"] = 2020

    mapa_temporadas = df_full.set_index("ID")["temporada"].to_dict()

    df_stats["temporada"] = df_stats["partida_id"].map(mapa_temporadas)
    df_gols["temporada"] = df_gols["partida_id"].map(mapa_temporadas)
    df_cartoes["temporada"] = df_cartoes["partida_id"].map(mapa_temporadas)

    temporadas_analise = set(range(2015, 2024)) | {2025}
    df_full = df_full[df_full["temporada"].isin(temporadas_analise)].copy()
    partidas_analise = set(df_full["ID"])
    df_stats = df_stats[df_stats["partida_id"].isin(partidas_analise)].copy()
    df_gols = df_gols[df_gols["partida_id"].isin(partidas_analise)].copy()
    df_cartoes = df_cartoes[df_cartoes["partida_id"].isin(partidas_analise)].copy()
    df_cartoes["posicao"] = df_cartoes["posicao"].replace({"Zagueira": "Zagueiro"})

    df_gols["tipo_de_gol"] = df_gols["tipo_de_gol"].fillna("Gol Normal")

    return df_full, df_stats, df_gols, df_cartoes


df_full, df_stats, df_gols, df_cartoes = carregar_dados()

st.sidebar.header("🔍 Filtros Globais")

temporadas_disponiveis = sorted([int(t) for t in df_full["temporada"].dropna().unique()], reverse=True)
opcao_temporada = st.sidebar.selectbox("Temporada", ["Todas"] + temporadas_disponiveis)

if opcao_temporada != "Todas":
    f_full = df_full[df_full["temporada"] == opcao_temporada].copy()
    f_stats = df_stats[df_stats["temporada"] == opcao_temporada].copy()
    f_gols = df_gols[df_gols["temporada"] == opcao_temporada].copy()
    f_cartoes = df_cartoes[df_cartoes["temporada"] == opcao_temporada].copy()
else:
    f_full, f_stats, f_gols, f_cartoes = df_full.copy(), df_stats.copy(), df_gols.copy(), df_cartoes.copy()

clubes_mandantes = set(f_full["mandante"].dropna())
clubes_visitantes = set(f_full["visitante"].dropna())
todos_clubes = sorted(list(clubes_mandantes.union(clubes_visitantes)))
opcao_clube = st.sidebar.selectbox("Clube", ["Todos"] + todos_clubes)

if opcao_clube != "Todos":
    f_full = f_full[(f_full["mandante"] == opcao_clube) | (f_full["visitante"] == opcao_clube)]
    f_stats = f_stats[f_stats["clube"] == opcao_clube]
    f_gols = f_gols[f_gols["clube"] == opcao_clube]
    f_cartoes = f_cartoes[f_cartoes["clube"] == opcao_clube]

partidas_filtradas = set(f_full["ID"])
f_stats_partidas = df_stats[df_stats["partida_id"].isin(partidas_filtradas)].copy()
f_cartoes_partidas = df_cartoes[df_cartoes["partida_id"].isin(partidas_filtradas)].copy()

st.title("⚽ Dashboard Analítico do Campeonato Brasileiro")
st.caption("Temporadas analisadas: 2015–2023 e 2025. A temporada de 2024 não integra esta análise.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Visão Geral",
    "📊 Estatísticas de Equipes",
    "⚽ Artilharia & Gols",
    "🟨 Disciplina & Cartões",
    "🏟️ Estádios & Técnicos"
])

with tab1:
    st.subheader("Indicadores Chave")
    c1, c2, c3, c4 = st.columns(4)

    total_jogos = len(f_full)

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
        st.plotly_chart(fig_mando, width="stretch")

    with col_g2:
        st.subheader("Resultados das Partidas")
        df_res = f_full.copy()
        df_res["Resultado"] = "Empate"
        df_res.loc[df_res["vencedor"] == df_res["mandante"], "Resultado"] = "Vitória Mandante"
        df_res.loc[df_res["vencedor"] == df_res["visitante"], "Resultado"] = "Vitória Visitante"

        fig_res = px.histogram(df_res, x="Resultado", color="Resultado",
                               color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_res, width="stretch")

    st.markdown("---")
    st.subheader("Evolução por Temporada")
    serie_temporadas = df_full.copy() if opcao_temporada == "Todas" else f_full.copy()
    if opcao_clube != "Todos":
        serie_temporadas = serie_temporadas[
            (serie_temporadas["mandante"] == opcao_clube) |
            (serie_temporadas["visitante"] == opcao_clube)
        ]
    serie_temporadas["gols_jogo"] = (
        serie_temporadas["mandante_Placar"] + serie_temporadas["visitante_Placar"]
    )
    evolucao_gols = (
        serie_temporadas.groupby("temporada", as_index=False)
        .agg(media_gols=("gols_jogo", "mean"), partidas=("ID", "count"))
        .sort_values("temporada")
    )
    grafico_evolucao = px.line(
        evolucao_gols, x="temporada", y="media_gols", markers=True,
        labels={"temporada": "Temporada", "media_gols": "Média de gols por partida", "partidas": "Partidas"},
        hover_data={"partidas": True, "media_gols": ":.2f"}
    )
    grafico_evolucao.update_xaxes(type="category")
    st.plotly_chart(grafico_evolucao, width="stretch")

    st.markdown("---")
    st.subheader("Vitórias por Clube: Casa e Fora")
    mando_selecionado = st.radio(
        "Local da partida", ["Em casa", "Fora de casa"], horizontal=True,
        key="mando_ranking_vitorias"
    )
    coluna_clube = "mandante" if mando_selecionado == "Em casa" else "visitante"
    partidas_mando = f_full.copy()
    partidas_mando["vitoria"] = (
        partidas_mando["mandante_Placar"] > partidas_mando["visitante_Placar"]
        if mando_selecionado == "Em casa"
        else partidas_mando["visitante_Placar"] > partidas_mando["mandante_Placar"]
    )
    ranking_mando = (
        partidas_mando.groupby(coluna_clube, as_index=False)
        .agg(Jogos=("ID", "count"), Vitorias=("vitoria", "sum"))
        .rename(columns={coluna_clube: "Clube"})
    )
    if not ranking_mando.empty:
        ranking_mando["Percentual"] = 100 * ranking_mando["Vitorias"] / ranking_mando["Jogos"]
        ranking_mando = ranking_mando.sort_values(
            ["Percentual", "Jogos", "Clube"], ascending=[False, False, True]
        ).head(10)
        grafico_vitorias = px.bar(
            ranking_mando, x="Percentual", y="Clube", orientation="h",
            color="Clube", color_discrete_sequence=px.colors.qualitative.Bold,
            text="Percentual", custom_data=["Jogos", "Vitorias"],
            labels={"Percentual": "Vitórias (%)", "Clube": "Clube"}
        )
        grafico_vitorias.update_traces(
            texttemplate="%{x:.1f}%", textposition="outside", cliponaxis=False,
            hovertemplate="%{y}<br>Vitórias: %{customdata[1]}<br>Jogos: %{customdata[0]}<br>Vitórias: %{x:.2f}%<extra></extra>"
        )
        grafico_vitorias.update_layout(
            showlegend=False,
            yaxis=dict(title=None, categoryorder="array", categoryarray=ranking_mando["Clube"].tolist()[::-1]),
            xaxis=dict(range=[0, max(100, ranking_mando["Percentual"].max() * 1.14)])
        )
        st.plotly_chart(grafico_vitorias, width="stretch")
    else:
        st.info("Não há partidas para o local e os filtros selecionados.")

    st.subheader("Lista de Partidas")
    st.dataframe(
        f_full.assign(
            vencedor=lambda jogos: jogos["vencedor"].where(
                jogos["mandante_Placar"] != jogos["visitante_Placar"], "Empate"
            )
        )[["temporada", "data", "rodata", "mandante", "mandante_Placar", "visitante_Placar", "visitante", "arena", "vencedor"]].rename(
            columns={"temporada": "Temporada", "rodata": "Rodada", "mandante_Placar": "Placar M", "visitante_Placar": "Placar V", "vencedor": "Resultado"}
        ),
        hide_index=True,
        width="stretch"
    )

with tab2:
    st.subheader("Desempenho Coletivo")

    cols_stats = ["chutes", "passes", "faltas", "escanteios", "impedimentos"]
    for col in cols_stats:
        if col in f_stats.columns:
            f_stats[col] = pd.to_numeric(f_stats[col], errors="coerce").fillna(0)

    f_stats_validos = f_stats[f_stats[cols_stats].sum(axis=1) > 0]

    if not f_stats_validos.empty:
        df_agrupado_stats = f_stats_validos.groupby("clube")[cols_stats].mean().reset_index()

        st.write("Média por jogo de cada equipe no período selecionado:")
        st.dataframe(df_agrupado_stats.round(2), width="stretch")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Média de Chutes por Equipe")
            fig_chutes = px.bar(
                df_agrupado_stats.sort_values("chutes", ascending=False).head(10),
                x="clube", y="chutes", color="clube", title="Top 10 - Chutes / Jogo"
            )
            st.plotly_chart(fig_chutes, width="stretch")

        with col_s2:
            st.subheader("Média de Faltas Cometidas por Equipe")
            fig_faltas = px.bar(
                df_agrupado_stats.sort_values("faltas", ascending=False).head(10),
                x="clube", y="faltas", color="clube", title="Top 10 - Mais Faltosas / Jogo"
            )
            st.plotly_chart(fig_faltas, width="stretch")
    else:
        st.warning(
            "⚠️ Não existem estatísticas detalhadas (chutes, faltas, etc.) registradas para o ano/clube selecionado no dataset.")

    st.markdown("---")
    st.subheader("Posse de Bola do Mandante e Resultado da Partida")
    partidas_posse = f_full[["ID", "mandante", "visitante", "mandante_Placar", "visitante_Placar"]].copy()
    posse_mandantes = f_stats_partidas[["partida_id", "clube", "posse_de_bola"]].copy()
    posse_mandantes = posse_mandantes.merge(
        partidas_posse, left_on=["partida_id", "clube"], right_on=["ID", "mandante"], how="inner"
    )
    posse_mandantes["posse_mandante"] = pd.to_numeric(
        posse_mandantes["posse_de_bola"].astype("string").str.replace("%", "", regex=False).str.strip(),
        errors="coerce"
    )
    posse_mandantes = posse_mandantes.dropna(subset=["posse_mandante"])
    if not posse_mandantes.empty:
        posse_mandantes["faixa_posse"] = pd.cut(
            posse_mandantes["posse_mandante"],
            bins=[-0.01, 40, 50, 60, 100.01],
            labels=["Menos de 40%", "40% a menos de 50%", "50% a menos de 60%", "60% ou mais"],
            right=False
        )
        posse_mandantes["resultado"] = "Empate"
        posse_mandantes.loc[
            posse_mandantes["mandante_Placar"] > posse_mandantes["visitante_Placar"], "resultado"
        ] = "Vitória mandante"
        posse_mandantes.loc[
            posse_mandantes["mandante_Placar"] < posse_mandantes["visitante_Placar"], "resultado"
        ] = "Vitória visitante"
        contagem_posse = (
            posse_mandantes.groupby(["faixa_posse", "resultado"], observed=False)
            .size().reset_index(name="jogos")
        )
        contagem_posse["percentual"] = (
            100 * contagem_posse["jogos"] /
            contagem_posse.groupby("faixa_posse", observed=False)["jogos"].transform("sum")
        )
        grafico_posse = px.bar(
            contagem_posse, x="faixa_posse", y="percentual", color="resultado",
            barmode="stack", category_orders={"resultado": ["Vitória mandante", "Empate", "Vitória visitante"]},
            labels={"faixa_posse": "Posse de bola do mandante", "percentual": "Distribuição dos resultados (%)", "resultado": "Resultado", "jogos": "Partidas"},
            hover_data={"jogos": True, "percentual": ":.2f"}
        )
        grafico_posse.update_layout(yaxis_range=[0, 100])
        st.caption(f"Partidas com posse registrada: {len(posse_mandantes):,} de {len(f_full):,} partidas selecionadas.")
        st.plotly_chart(grafico_posse, width="stretch")
    else:
        st.info("Não há partidas com posse de bola registrada para os filtros selecionados.")

with tab3:
    st.subheader("Top Artilheiros")
    if opcao_clube != "Todos":
        st.caption("Artilharia e gols por minuto: gols atribuídos ao clube selecionado.")
    if not f_gols.empty:
        artilharia = f_gols["atleta"].value_counts().reset_index()
        artilharia.columns = ["Jogador", "Gols"]

        col_a1, col_a2 = st.columns([1, 2])
        with col_a1:
            st.dataframe(artilharia.head(15), width="stretch")

        with col_a2:
            fig_artilharia = px.bar(
                artilharia.head(10), x="Gols", y="Jogador", orientation="h",
                title="Top 10 Marcadores", color="Gols", color_continuous_scale="Viridis"
            )
            fig_artilharia.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_artilharia, width="stretch")

        st.markdown("---")
        st.subheader("Gols por Período do Jogo")
        gols_minutos = f_gols.copy()
        gols_minutos["minuto_base"] = pd.to_numeric(
            gols_minutos["minuto"].astype("string").str.extract(r"^(\d+)(?:\+\d+)?$")[0],
            errors="coerce"
        )
        gols_minutos = gols_minutos[gols_minutos["minuto_base"].between(0, 90)].copy()
        if not gols_minutos.empty:
            faixas = ["0–15", "16–30", "31–45+", "46–60", "61–75", "76–90+"]
            gols_minutos["Faixa"] = pd.cut(
                gols_minutos["minuto_base"],
                bins=[-1, 15, 30, 45, 60, 75, 90],
                labels=faixas
            )
            distribuicao_minutos = (
                gols_minutos["Faixa"].value_counts(sort=False)
                .rename_axis("Faixa").reset_index(name="Gols")
            )
            distribuicao_minutos["Percentual"] = distribuicao_minutos["Gols"] / len(gols_minutos) * 100
            fig_minutos = px.bar(
                distribuicao_minutos, x="Faixa", y="Percentual", color="Faixa",
                text="Percentual", category_orders={"Faixa": faixas},
                color_discrete_sequence=px.colors.qualitative.Plotly,
                custom_data=["Gols"],
                labels={"Percentual": "Gols (%)", "Faixa": "Período do jogo"}
            )
            fig_minutos.update_traces(
                texttemplate="%{y:.1f}%", textposition="outside",
                hovertemplate="%{x}<br>Gols: %{customdata[0]}<br>Participação: %{y:.2f}%<extra></extra>"
            )
            fig_minutos.update_layout(
                showlegend=False,
                yaxis_range=[0, max(distribuicao_minutos["Percentual"].max() * 1.2, 1)]
            )
            st.plotly_chart(fig_minutos, width="stretch")
        else:
            st.info("Não há gols com minuto válido para os filtros selecionados.")

        col_g_tipo, col_g_tempo = st.columns(2)
        with col_g_tipo:
            st.subheader("Tipos de Gols")
            tipos_gol = f_gols["tipo_de_gol"].value_counts().reset_index()
            tipos_gol.columns = ["Tipo", "Quantidade"]
            fig_tipo_gol = px.pie(tipos_gol, names="Tipo", values="Quantidade", hole=0.3)
            st.plotly_chart(fig_tipo_gol, width="stretch")

        with col_g_tempo:
            st.subheader("Gols por Tempo de Jogo")
            if not gols_minutos.empty:
                tempos = (
                    gols_minutos["minuto_base"].le(45)
                    .map({True: "1º tempo", False: "2º tempo"})
                    .value_counts()
                    .reindex(["1º tempo", "2º tempo"], fill_value=0)
                    .rename_axis("Tempo").reset_index(name="Gols")
                )
                tempos["Percentual"] = tempos["Gols"] / len(gols_minutos) * 100
                fig_tempos = px.bar(
                    tempos, x="Tempo", y="Percentual", color="Tempo",
                    text="Percentual", custom_data=["Gols"],
                    color_discrete_sequence=px.colors.qualitative.Plotly,
                    labels={"Percentual": "Gols (%)"}
                )
                fig_tempos.update_traces(
                    texttemplate="%{y:.1f}%", textposition="outside",
                    hovertemplate="%{x}<br>Gols: %{customdata[0]}<br>Participação: %{y:.2f}%<extra></extra>"
                )
                fig_tempos.update_layout(showlegend=False, yaxis_range=[0, 100])
                st.plotly_chart(fig_tempos, width="stretch")
            else:
                st.info("Não há gols com minuto válido para os filtros selecionados.")

    st.markdown("---")
    st.subheader("Distribuição de Gols por Partida e Valores Extremos")
    jogos_gols = f_full.copy()
    jogos_gols["Gols na partida"] = jogos_gols["mandante_Placar"] + jogos_gols["visitante_Placar"]
    fig_box_gols = px.box(jogos_gols, y="Gols na partida", points="outliers", title="Distribuição de gols por partida")
    st.plotly_chart(fig_box_gols, width="stretch")
    st.subheader("Partidas com Mais Gols")
    jogos_extremos = jogos_gols.sort_values("Gols na partida", ascending=False).head(10).copy()
    jogos_extremos["Placar"] = jogos_extremos["mandante_Placar"].astype(str) + " × " + jogos_extremos["visitante_Placar"].astype(str)
    st.dataframe(
        jogos_extremos[["temporada", "data", "mandante", "Placar", "visitante", "Gols na partida"]].rename(
            columns={"temporada": "Temporada", "data": "Data", "mandante": "Mandante", "visitante": "Visitante"}
        ), hide_index=True, width="stretch"
    )

with tab4:
    st.subheader("Análise de Disciplina")
    if not f_cartoes.empty:
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.subheader("Cartões Amarelos por Jogador")
            amarelos = f_cartoes[f_cartoes["cartao"] == "Amarelo"]["atleta"].value_counts().reset_index()
            amarelos.columns = ["Jogador", "Cartões Amarelos"]
            st.dataframe(amarelos.head(10), width="stretch")

        with col_c2:
            st.subheader("Cartões Vermelhos por Jogador")
            vermelhos = f_cartoes[f_cartoes["cartao"] == "Vermelho"]["atleta"].value_counts().reset_index()
            vermelhos.columns = ["Jogador", "Cartões Vermelhos"]
            st.dataframe(vermelhos.head(10), width="stretch")

        st.markdown("---")
        col_pos, col_tipo_c = st.columns(2)

        with col_pos:
            st.subheader("Cartões por Posição")
            cartoes_pos = f_cartoes["posicao"].value_counts().reset_index()
            cartoes_pos.columns = ["Posição", "Total Cartões"]
            fig_pos = px.bar(cartoes_pos.head(8), x="Posição", y="Total Cartões", color="Posição")
            st.plotly_chart(fig_pos, width="stretch")

        with col_tipo_c:
            st.subheader("Média de Cartões Amarelos por Clube")
            participacoes = pd.concat([f_full["mandante"], f_full["visitante"]]).value_counts()
            amarelos_clube = f_cartoes.loc[f_cartoes["cartao"] == "Amarelo", "clube"].value_counts()
            media_amarelos = (
                amarelos_clube.reindex(participacoes.index, fill_value=0)
                .div(participacoes)
                .sort_values(ascending=False)
                .head(10)
                .rename_axis("Clube")
                .reset_index(name="Amarelos por partida")
            )
            fig_media_amarelos = px.bar(
                media_amarelos,
                x="Amarelos por partida",
                y="Clube",
                orientation="h",
                color="Clube",
                color_discrete_sequence=px.colors.qualitative.Bold,
                text="Amarelos por partida",
            )
            fig_media_amarelos.update_traces(texttemplate="%{x:.2f}", textposition="outside", cliponaxis=False)
            fig_media_amarelos.update_layout(
                yaxis=dict(title=None, categoryorder="array", categoryarray=media_amarelos["Clube"].tolist()[::-1]),
                xaxis=dict(range=[0, max(media_amarelos["Amarelos por partida"].max() * 1.16, 1)]),
                showlegend=False,
            )
            st.plotly_chart(fig_media_amarelos, width="stretch")
    else:
        st.info("Sem dados de cartões para os filtros selecionados.")

    st.markdown("---")
    st.subheader("Expulsões nas Partidas Selecionadas e Resultados")
    partidas_cartoes = f_full[["ID", "mandante", "visitante", "mandante_Placar", "visitante_Placar"]].copy()
    cartoes_vermelhos = f_cartoes_partidas[f_cartoes_partidas["cartao"] == "Vermelho"].copy()
    contagem_vermelhos = (
        cartoes_vermelhos.groupby(["partida_id", "clube"]).size().rename("vermelhos").reset_index()
    )
    vermelhos_mandante = contagem_vermelhos.merge(
        partidas_cartoes[["ID", "mandante"]],
        left_on=["partida_id", "clube"], right_on=["ID", "mandante"], how="inner"
    ).groupby("ID")["vermelhos"].sum()
    vermelhos_visitante = contagem_vermelhos.merge(
        partidas_cartoes[["ID", "visitante"]],
        left_on=["partida_id", "clube"], right_on=["ID", "visitante"], how="inner"
    ).groupby("ID")["vermelhos"].sum()
    partidas_cartoes["vermelhos_mandante"] = partidas_cartoes["ID"].map(vermelhos_mandante).fillna(0)
    partidas_cartoes["vermelhos_visitante"] = partidas_cartoes["ID"].map(vermelhos_visitante).fillna(0)
    partidas_cartoes["situacao"] = "Sem expulsões"
    partidas_cartoes.loc[
        (partidas_cartoes["vermelhos_mandante"] > 0) & (partidas_cartoes["vermelhos_visitante"] == 0), "situacao"
    ] = "Só mandante expulso"
    partidas_cartoes.loc[
        (partidas_cartoes["vermelhos_mandante"] == 0) & (partidas_cartoes["vermelhos_visitante"] > 0), "situacao"
    ] = "Só visitante expulso"
    partidas_cartoes.loc[
        (partidas_cartoes["vermelhos_mandante"] > 0) & (partidas_cartoes["vermelhos_visitante"] > 0), "situacao"
    ] = "Ambos com expulsões"
    partidas_cartoes["resultado"] = "Empate"
    partidas_cartoes.loc[
        partidas_cartoes["mandante_Placar"] > partidas_cartoes["visitante_Placar"], "resultado"
    ] = "Vitória mandante"
    partidas_cartoes.loc[
        partidas_cartoes["mandante_Placar"] < partidas_cartoes["visitante_Placar"], "resultado"
    ] = "Vitória visitante"
    frequencia_vermelhos = (
        partidas_cartoes.groupby(["situacao", "resultado"]).size().reset_index(name="jogos")
    )
    frequencia_vermelhos["percentual"] = (
        100 * frequencia_vermelhos["jogos"] / frequencia_vermelhos.groupby("situacao")["jogos"].transform("sum")
    )
    totais_situacao = partidas_cartoes["situacao"].value_counts().to_dict()
    frequencia_vermelhos["situação e amostra"] = frequencia_vermelhos["situacao"].map(
        lambda situacao: f"{situacao} (n={totais_situacao[situacao]})"
    )
    grafico_vermelhos = px.bar(
        frequencia_vermelhos, x="situação e amostra", y="percentual", color="resultado", barmode="stack",
        category_orders={"situação e amostra": [
            f"{situacao} (n={totais_situacao[situacao]})" for situacao in
            ["Sem expulsões", "Só mandante expulso", "Só visitante expulso", "Ambos com expulsões"]
            if situacao in totais_situacao
        ], "resultado": ["Vitória mandante", "Empate", "Vitória visitante"]},
        labels={"situação e amostra": "Situação dos cartões vermelhos", "percentual": "Distribuição dos resultados (%)", "resultado": "Resultado", "jogos": "Partidas"},
        hover_data={"jogos": True, "percentual": ":.2f"}
    )
    grafico_vermelhos.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(grafico_vermelhos, width="stretch")

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
        st.plotly_chart(fig_estadios, width="stretch")

    with col_e2:
        st.subheader("Técnicos com Mais Jogos")
        tecnicos = pd.concat([f_full["tecnico_mandante"], f_full["tecnico_visitante"]]).value_counts().head(
            10).reset_index()
        tecnicos.columns = ["Técnico", "Jogos"]
        fig_tecnicos = px.bar(tecnicos, x="Jogos", y="Técnico", orientation="h", color="Jogos",
                              color_continuous_scale="Greens")
        fig_tecnicos.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_tecnicos, width="stretch")