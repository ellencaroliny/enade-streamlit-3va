import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).parent / "enade_dw.db"

# Verificar se o banco de dados existe
if not DB_PATH.exists():
    st.error("""
    ⚠️ **Banco de dados não encontrado!**

    O arquivo `enade_dw.db` não está presente no repositório devido ao seu tamanho (88 MB).

    **Para usar esta aplicação localmente:**
    1. Faça o download do banco de dados `enade_dw.db`
    2. Coloque-o na mesma pasta do arquivo `app.py`
    3. Execute novamente com: `streamlit run app.py`

    **Para deploy no Streamlit Cloud:**
    - O banco de dados precisa estar incluído no repositório, ou
    - Use uma solução de armazenamento externa (como AWS S3, Google Drive, etc.)

    📊 **Dados disponíveis:**
    - Total de registros: 714.580
    - Anos: 2018, 2019, 2021, 2022, 2023
    - Tamanho do banco: ~88 MB
    """)
    st.stop()


@st.cache_resource
def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def query_data(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(sql, conn)


@st.cache_data(ttl=600)
def cached_query(sql: str) -> pd.DataFrame:
    return query_data(sql)


def get_simple_query(
    anos=None,
    regioes=None,
    ufs=None,
    cursos=None,
    sexo=None,
    cor_raca=None,
    renda=None,
    modalidade=None,
    categoria=None,
    limit=None,
    force_curso=False,
    force_estudante=False,
):
    wheres = ["f.sk_avaliacao = a.sk_avaliacao"]
    tables = ["fato_enade f", "dim_avaliacao a"]

    # Sempre incluir dim_tempo para ter ano_enade disponível
    tables.append("dim_tempo t")
    wheres.append("f.sk_tempo = t.sk_tempo")

    if anos:
        anos_str = ", ".join(str(a) for a in anos)
        wheres.append(f"t.ano_enade IN ({anos_str})")

    needs_curso = regioes or ufs or cursos or modalidade or categoria or force_curso
    needs_estudante = sexo or cor_raca or renda or force_estudante

    if needs_curso:
        tables.append("dim_curso c")
        wheres.append("f.sk_curso = c.sk_curso")
    if needs_estudante:
        tables.append("dim_estudante e")
        wheres.append("f.sk_estudante = e.sk_estudante")

    if regioes:
        reg_str = ", ".join(f"'{r}'" for r in regioes)
        wheres.append(f"c.nome_regiao IN ({reg_str})")
    if ufs:
        uf_str = ", ".join(f"'{u}'" for u in ufs)
        wheres.append(f"c.uf IN ({uf_str})")
    if cursos:
        cur_str = ", ".join(f"'{c}'" for c in cursos)
        wheres.append(f"c.nome_curso IN ({cur_str})")
    if modalidade:
        mod_str = ", ".join(f"'{m}'" for m in modalidade)
        wheres.append(f"c.modalidade_graduacao IN ({mod_str})")
    if categoria:
        cat_str = ", ".join(f"'{c}'" for c in categoria)
        wheres.append(f"c.categoria_administrativa IN ({cat_str})")
    if sexo:
        sex_str = ", ".join(f"'{s}'" for s in sexo)
        wheres.append(f"e.sexo IN ({sex_str})")
    if cor_raca:
        cr_str = ", ".join(f"'{cr}'" for cr in cor_raca)
        wheres.append(f"e.cor_raca IN ({cr_str})")
    if renda:
        ren_str = ", ".join(f"'{r}'" for r in renda)
        wheres.append(f"e.renda_familiar IN ({ren_str})")

    tables = list(dict.fromkeys(tables))

    select_cols = ["f.*"]
    select_cols.append("a.grau_dificuldade_prova_formacao_geral")
    select_cols.append("a.grau_dificuldade_prova_componente_especifico")
    select_cols.append("a.avaliacao_da_relacao_extensao_tempo_prova")
    select_cols.append("a.tempo_de_prova")
    select_cols.append("t.ano_enade")
    if needs_curso:
        select_cols.extend([
            "c.nome_curso", "c.nome_regiao", "c.nome_estado", "c.uf",
            "c.nome_municipio", "c.modalidade_graduacao",
            "c.categoria_administrativa", "c.turno_graduacao",
        ])
    if needs_estudante:
        select_cols.extend([
            "e.sexo", "e.idade", "e.cor_raca", "e.renda_familiar",
            "e.escolaridade_pai", "e.escolaridade_mae",
            "e.tipo_escola_ensino_medio", "e.primeira_geracao",
            "e.motivacao_curso", "e.horas_trabalho", "e.cotas",
        ])

    query = "SELECT " + ", ".join(select_cols)
    query += " FROM " + ", ".join(tables)
    query += " WHERE " + " AND ".join(wheres)
    if limit:
        query += f" LIMIT {limit}"
    return query


st.set_page_config(
    page_title="Cubo ENADE - Análise de Dados",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Cubo ENADE - Análise Multidimensional")
st.markdown(
    "Dashboard interativo para análise dos dados do ENADE com base no esquema estrela "
    "(fato_enade + dimensões Tempo, Curso, Estudante, Avaliação)."
)

with st.sidebar:
    st.header("Filtros")

    anos = cached_query('SELECT DISTINCT ano_enade FROM "dim_tempo" WHERE ano_enade > 0 ORDER BY ano_enade')
    anos_list = [int(a) for a in anos["ano_enade"].tolist()]
    anos_sel = st.multiselect("Ano ENADE", anos_list, default=anos_list)

    regioes = cached_query('SELECT DISTINCT nome_regiao FROM "dim_curso" WHERE nome_regiao != "Não Informado" ORDER BY nome_regiao')
    reg_list = regioes["nome_regiao"].tolist()
    reg_sel = st.multiselect("Região", reg_list, default=[])

    if reg_sel:
        reg_str = ", ".join(f"'{r}'" for r in reg_sel)
        uf_df = cached_query(f'SELECT DISTINCT uf FROM "dim_curso" WHERE nome_regiao IN ({reg_str}) AND uf != "NI" ORDER BY uf')
    else:
        uf_df = cached_query('SELECT DISTINCT uf FROM "dim_curso" WHERE uf != "NI" ORDER BY uf')
    uf_sel = st.multiselect("UF", uf_df["uf"].tolist(), default=[])

    cursos_df = cached_query('SELECT DISTINCT nome_curso FROM "dim_curso" ORDER BY nome_curso')
    cursos_sel = st.multiselect("Curso", cursos_df["nome_curso"].tolist(), default=[])

    modalidades = cached_query('SELECT DISTINCT modalidade_graduacao FROM "dim_curso" WHERE modalidade_graduacao NOT IN ("Não Informado", "") ORDER BY modalidade_graduacao')
    modal_sel = st.multiselect("Modalidade", modalidades["modalidade_graduacao"].tolist(), default=[])

    categorias = cached_query('SELECT DISTINCT categoria_administrativa FROM "dim_curso" WHERE categoria_administrativa NOT IN ("Não Informado", "") ORDER BY categoria_administrativa')
    cat_sel = st.multiselect("Categoria Administrativa", categorias["categoria_administrativa"].tolist(), default=[])

    with st.expander("Filtros de Perfil do Estudante"):
        sexos = cached_query('SELECT DISTINCT sexo FROM "dim_estudante" WHERE sexo IN ("F", "M") ORDER BY sexo')
        sex_sel = st.multiselect("Sexo", sexos["sexo"].tolist(), default=[])

        cor_raca_df = cached_query('SELECT DISTINCT cor_raca FROM "dim_estudante" WHERE cor_raca NOT IN ("Não Informado", "") ORDER BY cor_raca')
        cor_sel = st.multiselect("Cor/Raça", cor_raca_df["cor_raca"].tolist(), default=[])

        renda_df = cached_query('SELECT DISTINCT renda_familiar FROM "dim_estudante" WHERE renda_familiar NOT IN ("Não Informado", "") ORDER BY renda_familiar')
        renda_sel = st.multiselect("Renda Familiar", renda_df["renda_familiar"].tolist(), default=[])

    st.divider()
    st.markdown("**Fonte:** Dados ENADE (MySQL → SQLite)")
    st.markdown(f"**Base:** {Path(DB_PATH).stat().st_size / 1e6:.1f} MB")

filters_active = anos_sel or reg_sel or uf_sel or cursos_sel or modal_sel or cat_sel or sex_sel or cor_sel or renda_sel

params = {
    "anos": anos_sel or None,
    "regioes": reg_sel or None,
    "ufs": uf_sel or None,
    "cursos": cursos_sel or None,
    "sexo": sex_sel or None,
    "cor_raca": cor_sel or None,
    "renda": renda_sel or None,
    "modalidade": modal_sel or None,
    "categoria": cat_sel or None,
}

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Visão Geral", "Desempenho", "Geográfico",
    "Perfil Estudante", "Avaliação da Prova",
    "Dados Detalhados",
])

if filters_active:
    df = query_data(get_simple_query(**params, limit=None))
else:
    df = query_data(get_simple_query(limit=None))

with tab1:
    st.subheader("Indicadores Gerais")

    if df.empty:
        st.warning("Nenhum dado encontrado com os filtros atuais.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Avaliações", f"{len(df):,}")
        with col2:
            st.metric("Média Nota Geral", f"{df['nota_geral'].mean():.2f}")
        with col3:
            st.metric("Média Formação Geral", f"{df['nota_formacao_geral'].mean():.2f}")
        with col4:
            st.metric("Média Componente Específico", f"{df['nota_componente_especifico'].mean():.2f}")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(
                df, x="nota_geral", nbins=50,
                title="Distribuição da Nota Geral",
                labels={"nota_geral": "Nota Geral"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            nota_cols = [
                "nota_formacao_geral", "nota_componente_especifico",
                "nota_parte_objetiva_formacao_geral", "nota_parte_discursiva_formacao_geral",
                "nota_parte_objetiva_componente_especifico", "nota_parte_discursiva_componente_especifico",
            ]
            available = [c for c in nota_cols if c in df.columns]
            if available:
                means = df[available].mean().reset_index()
                means.columns = ["Componente", "Média"]
                fig = px.bar(means, x="Componente", y="Média", title="Média por Componente de Nota")
                fig.update_layout(height=350, xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Estatísticas Descritivas")
        desc = df[["nota_geral", "nota_formacao_geral", "nota_componente_especifico"]].describe().T
        desc.columns = ["Contagem", "Média", "Desvio Padrão", "Mínimo", "25%", "50%", "75%", "Máximo"]
        desc.index = ["Nota Geral", "Formação Geral", "Componente Específico"]
        st.dataframe(desc.style.format("{:.2f}"), use_container_width=True)

with tab2:
    st.subheader("Análise de Desempenho")

    if df.empty:
        st.warning("Nenhum dado encontrado.")
    else:
        if "ano_enade" in df.columns:
            perf_ano = df.groupby("ano_enade")["nota_geral"].agg(["mean", "count"]).reset_index()
            perf_ano.columns = ["Ano", "Média", "Quantidade"]
            fig = px.line(perf_ano, x="Ano", y="Média", title="Evolução da Nota Geral por Ano", markers=True)
            st.plotly_chart(fig, use_container_width=True)

        dim_options = ["nome_curso", "nome_regiao", "modalidade_graduacao", "categoria_administrativa", "turno_graduacao"]
        dim_options = [d for d in dim_options if d in df.columns]
        if dim_options:
            dim_choice = st.selectbox(
                "Agrupar por",
                options=dim_options,
                format_func=lambda x: {
                    "nome_curso": "Curso",
                    "nome_regiao": "Região",
                    "modalidade_graduacao": "Modalidade",
                    "categoria_administrativa": "Categoria Administrativa",
                    "turno_graduacao": "Turno",
                }.get(x, x),
            )
            if dim_choice in df.columns:
                perf_dim = (
                    df.groupby(dim_choice)["nota_geral"]
                    .agg(["mean", "count"])
                    .reset_index()
                    .sort_values("mean", ascending=False)
                )
                perf_dim.columns = [dim_choice, "Média", "Quantidade"]
                fig = px.bar(
                    perf_dim.head(20), x=dim_choice, y="Média",
                    color="Quantidade",
                    title=f"Média da Nota Geral por {dim_choice} (Top 20)",
                    text_auto=".1f",
                )
                fig.update_layout(xaxis_tickangle=45, height=450)
                st.plotly_chart(fig, use_container_width=True)

        if "sexo" in df.columns and "cor_raca" in df.columns:
            col1, col2 = st.columns(2)
            with col1:
                perf_sexo = df.groupby("sexo")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_sexo, x="sexo", y="nota_geral", title="Média por Sexo")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                perf_cor = df.groupby("cor_raca")["nota_geral"].mean().reset_index().sort_values("nota_geral", ascending=False)
                fig = px.bar(perf_cor, x="cor_raca", y="nota_geral", title="Média por Cor/Raça")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Análise Geográfica")

    # Carregar dados com dimensão curso sempre para essa aba
    params_geo = params.copy()
    df_geo = query_data(get_simple_query(**params_geo, force_curso=True, limit=None))

    has_geo = "nome_regiao" in df_geo.columns and "uf" in df_geo.columns
    if df_geo.empty or not has_geo:
        st.warning("Dados geográficos indisponíveis.")
    else:
        df = df_geo
        col1, col2 = st.columns(2)
        with col1:
            perf_reg = df.groupby("nome_regiao").agg(
                Média=("nota_geral", "mean"), Quantidade=("nota_geral", "count")
            ).reset_index().sort_values("Média", ascending=False)
            fig = px.bar(perf_reg, x="nome_regiao", y="Média", color="Quantidade", title="Média por Região", text_auto=".1f")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            if len(df["nome_regiao"].unique()) > 1 and "modalidade_graduacao" in df.columns:
                heat = df.pivot_table(values="nota_geral", index="nome_regiao", columns="modalidade_graduacao", aggfunc="mean")
                fig = px.imshow(heat, text_auto=".1f", title="Nota Geral Média: Região x Modalidade", aspect="auto")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        perf_uf = df.groupby("uf").agg(
            Média=("nota_geral", "mean"), Quantidade=("nota_geral", "count")
        ).reset_index().sort_values("Média", ascending=False)
        fig = px.bar(perf_uf, x="uf", y="Média", color="Quantidade", title="Média por UF", text_auto=".1f")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Análise do Perfil do Estudante")

    # Carregar dados com dimensão estudante sempre para essa aba
    params_estudante = params.copy()
    df_perfil = query_data(get_simple_query(**params_estudante, force_estudante=True, limit=None))

    has_perfil = "sexo" in df_perfil.columns and "cor_raca" in df_perfil.columns
    if df_perfil.empty or not has_perfil:
        st.warning("Dados de perfil indisponíveis.")
    else:
        df = df_perfil
        col1, col2 = st.columns(2)
        with col1:
            perf = df.groupby(["sexo", "cor_raca"])["nota_geral"].mean().reset_index()
            fig = px.bar(perf, x="cor_raca", y="nota_geral", color="sexo", barmode="group", title="Nota Geral por Sexo e Cor/Raça")
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "renda_familiar" in df.columns:
                perf_renda = df.groupby("renda_familiar")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_renda, x="renda_familiar", y="nota_geral", title="Média por Renda Familiar")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if "tipo_escola_ensino_medio" in df.columns:
                perf_esc = df.groupby("tipo_escola_ensino_medio")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_esc, x="tipo_escola_ensino_medio", y="nota_geral", title="Média por Tipo de Escola (Ensino Médio)")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "escolaridade_pai" in df.columns:
                perf_pai = df.groupby("escolaridade_pai")["nota_geral"].mean().reset_index().sort_values("nota_geral", ascending=False)
                fig = px.bar(perf_pai, x="escolaridade_pai", y="nota_geral", title="Média por Escolaridade do Pai")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if "horas_trabalho" in df.columns:
                perf_hr = df.groupby("horas_trabalho")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_hr, x="horas_trabalho", y="nota_geral", title="Média por Carga Horária de Trabalho")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "cotas" in df.columns:
                perf_cotas = df.groupby("cotas")["nota_geral"].mean().reset_index().sort_values("nota_geral", ascending=False)
                fig = px.bar(perf_cotas.head(15), x="cotas", y="nota_geral", title="Média por Tipo de Cota (Top 15)")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Análise da Avaliação da Prova")

    has_av = "grau_dificuldade_prova_formacao_geral" in df.columns
    if df.empty or not has_av:
        st.warning("Dados de avaliação indisponíveis.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if "nota_geral" in df.columns:
                ordem = ["Muito fácil", "Fácil", "Médio", "Difícil", "Muito difícil", "Não informado"]
                dif_fg = df.groupby("grau_dificuldade_prova_formacao_geral")["nota_geral"].mean().reset_index()
                dif_fg["ordem"] = dif_fg["grau_dificuldade_prova_formacao_geral"].apply(lambda x: ordem.index(x) if x in ordem else 99)
                dif_fg = dif_fg.sort_values("ordem")
                fig = px.line(dif_fg, x="grau_dificuldade_prova_formacao_geral", y="nota_geral", markers=True, title="Nota Geral vs. Dificuldade (Formação Geral)")
                fig.update_layout(xaxis_categoryorder="array", xaxis_categoryarray=ordem)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "nota_componente_especifico" in df.columns:
                ordem = ["Muito fácil", "Fácil", "Médio", "Difícil", "Muito difícil", "Não informado"]
                dif_ce = df.groupby("grau_dificuldade_prova_componente_especifico")["nota_componente_especifico"].mean().reset_index()
                dif_ce["ordem"] = dif_ce["grau_dificuldade_prova_componente_especifico"].apply(lambda x: ordem.index(x) if x in ordem else 99)
                dif_ce = dif_ce.sort_values("ordem")
                fig = px.line(dif_ce, x="grau_dificuldade_prova_componente_especifico", y="nota_componente_especifico", markers=True, title="Nota Comp. Específico vs. Dificuldade")
                fig.update_layout(xaxis_categoryorder="array", xaxis_categoryarray=ordem)
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if "avaliacao_da_relacao_extensao_tempo_prova" in df.columns and "nota_geral" in df.columns:
                perf_tmp = df.groupby("avaliacao_da_relacao_extensao_tempo_prova")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_tmp, x="avaliacao_da_relacao_extensao_tempo_prova", y="nota_geral", title="Nota Geral vs. Relação Extensão/Tempo")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "tempo_de_prova" in df.columns and "nota_geral" in df.columns:
                perf_tp = df.groupby("tempo_de_prova")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_tp, x="tempo_de_prova", y="nota_geral", title="Nota Geral vs. Tempo de Prova")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        if "avaliacao_equipamentos_curso" in df.columns and "avaliacao_ambiente_curso" in df.columns:
            col1, col2 = st.columns(2)
            with col1:
                if "nota_geral" in df.columns:
                    perf_eq = df.groupby("avaliacao_equipamentos_curso")["nota_geral"].mean().reset_index()
                    fig = px.bar(perf_eq, x="avaliacao_equipamentos_curso", y="nota_geral", title="Nota Geral vs. Avaliação dos Equipamentos")
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                if "nota_geral" in df.columns:
                    perf_amb = df.groupby("avaliacao_ambiente_curso")["nota_geral"].mean().reset_index()
                    fig = px.bar(perf_amb, x="avaliacao_ambiente_curso", y="nota_geral", title="Nota Geral vs. Avaliação do Ambiente")
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.subheader("Dados Detalhados")

    # Limitar a 10000 registros para não sobrecarregar a visualização
    if filters_active:
        df_detail = query_data(get_simple_query(**params, limit=10000))
    else:
        df_detail = query_data(get_simple_query(limit=10000))

    if df_detail.empty:
        st.warning("Nenhum dado encontrado.")
    else:
        st.dataframe(df_detail, use_container_width=True, height=500)
        st.download_button(
            label="Download CSV",
            data=df_detail.to_csv(index=False).encode("utf-8"),
            file_name="enade_dados_filtrados.csv",
            mime="text/csv",
        )