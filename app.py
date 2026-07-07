import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

pio.templates["custom"] = pio.templates["plotly_white"]
pio.templates["custom"].layout.font = {"family": "Arial, sans-serif"}
pio.templates.default = "custom"

DB_PATH = Path(__file__).parent / "enade_dw.db"

if not DB_PATH.exists():
    st.error("""
    **Banco de dados não encontrado!**

    O arquivo `enade_dw.db` não está presente.

    **Para criar o banco:**
    ```
    python etl_enade.py
    ```
    """)
    st.stop()


@st.cache_resource
def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda x: x.decode("utf-8", errors="replace")
    return conn


def query_data(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(sql, conn)


@st.cache_data(ttl=600)
def cached_query(sql: str) -> pd.DataFrame:
    return query_data(sql)


def _build_query_parts(
    anos=None,
    regioes=None,
    ufs=None,
    cursos=None,
    sexo=None,
    cor_raca=None,
    renda=None,
    modalidade=None,
    categoria=None,
    force_curso=False,
    force_estudante=False,
):
    wheres = ["f.sk_avaliacao = a.sk_avaliacao"]
    tables = ["fato_enade f", "dim_avaliacao a"]

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
    return tables, wheres, needs_curso, needs_estudante


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
    random_limit=None,
    force_curso=False,
    force_estudante=False,
):
    tables, wheres, needs_curso, needs_estudante = _build_query_parts(
        anos, regioes, ufs, cursos, sexo, cor_raca, renda,
        modalidade, categoria, force_curso, force_estudante,
    )

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
    if random_limit:
        query += f" ORDER BY RANDOM() LIMIT {random_limit}"
    elif limit:
        query += f" LIMIT {limit}"
    return query


def build_geo_region_query(anos=None, regioes=None, ufs=None, cursos=None):
    tempo_join = "LEFT JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo"
    wheres = ["c.nome_regiao != 'Não Informado'"]
    if anos:
        anos_str = ", ".join(str(a) for a in anos)
        tempo_join += f" AND t.ano_enade IN ({anos_str})"
    if regioes:
        reg_str = ", ".join(f"'{r}'" for r in regioes)
        wheres.append(f"c.nome_regiao IN ({reg_str})")
    if ufs:
        uf_str = ", ".join(f"'{u}'" for u in ufs)
        wheres.append(f"c.uf IN ({uf_str})")
    if cursos:
        cur_str = ", ".join(f"'{c}'" for c in cursos)
        wheres.append(f"c.nome_curso IN ({cur_str})")

    return f"""
        SELECT c.nome_regiao, AVG(f.nota_geral) as Média, COUNT(f.nota_geral) as Quantidade
        FROM dim_curso c
        LEFT JOIN fato_enade f ON f.sk_curso = c.sk_curso
        {tempo_join}
        WHERE {' AND '.join(wheres)}
        GROUP BY c.nome_regiao
        ORDER BY Média DESC
    """


def build_geo_uf_query(anos=None, regioes=None, ufs=None, cursos=None):
    tempo_join = "LEFT JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo"
    wheres = ["c.uf != 'NI'"]
    if anos:
        anos_str = ", ".join(str(a) for a in anos)
        tempo_join += f" AND t.ano_enade IN ({anos_str})"
    if regioes:
        reg_str = ", ".join(f"'{r}'" for r in regioes)
        wheres.append(f"c.nome_regiao IN ({reg_str})")
    if ufs:
        uf_str = ", ".join(f"'{u}'" for u in ufs)
        wheres.append(f"c.uf IN ({uf_str})")
    if cursos:
        cur_str = ", ".join(f"'{c}'" for c in cursos)
        wheres.append(f"c.nome_curso IN ({cur_str})")

    return f"""
        SELECT c.uf, AVG(f.nota_geral) as Média, COUNT(f.nota_geral) as Quantidade
        FROM dim_curso c
        LEFT JOIN fato_enade f ON f.sk_curso = c.sk_curso
        {tempo_join}
        WHERE {' AND '.join(wheres)}
        GROUP BY c.uf
        ORDER BY Média DESC
    """


def build_olap_query(
    rows=None,
    cols=None,
    measure="nota_geral",
    agg="AVG",
    anos=None,
    regioes=None,
    ufs=None,
    cursos=None,
    sexo=None,
    cor_raca=None,
    renda=None,
    modalidade=None,
    categoria=None,
):
    dim_map = {
        "ano_enade": ("dim_tempo t", "t.ano_enade", "f.sk_tempo = t.sk_tempo"),
        "nome_regiao": ("dim_curso c", "c.nome_regiao", "f.sk_curso = c.sk_curso"),
        "nome_estado": ("dim_curso c", "c.nome_estado", "f.sk_curso = c.sk_curso"),
        "uf": ("dim_curso c", "c.uf", "f.sk_curso = c.sk_curso"),
        "nome_municipio": ("dim_curso c", "c.nome_municipio", "f.sk_curso = c.sk_curso"),
        "nome_curso": ("dim_curso c", "c.nome_curso", "f.sk_curso = c.sk_curso"),
        "modalidade_graduacao": ("dim_curso c", "c.modalidade_graduacao", "f.sk_curso = c.sk_curso"),
        "turno_graduacao": ("dim_curso c", "c.turno_graduacao", "f.sk_curso = c.sk_curso"),
        "categoria_administrativa": ("dim_curso c", "c.categoria_administrativa", "f.sk_curso = c.sk_curso"),
        "sexo": ("dim_estudante e", "e.sexo", "f.sk_estudante = e.sk_estudante"),
        "cor_raca": ("dim_estudante e", "e.cor_raca", "f.sk_estudante = e.sk_estudante"),
        "renda_familiar": ("dim_estudante e", "e.renda_familiar", "f.sk_estudante = e.sk_estudante"),
    }

    tables = ["fato_enade f"]
    joins = set()
    select_parts = []
    group_parts = []
    where_parts = []

    all_dims = [d for d in [rows, cols] if d]
    for dim in all_dims:
        if dim in dim_map:
            tbl, col, join_cond = dim_map[dim]
            label = tbl.split()[-1]
            if label not in joins:
                tables.append(tbl)
                joins.add(label)
                where_parts.append(join_cond)
            select_parts.append(col)
            group_parts.append(col)

    agg_funcs = {"AVG": f"AVG(f.{measure})", "COUNT": "COUNT(*)", "SUM": f"SUM(f.{measure})", "MIN": f"MIN(f.{measure})", "MAX": f"MAX(f.{measure})"}
    agg_col = agg_funcs.get(agg, f"AVG(f.{measure})")
    select_parts.append(f"{agg_col} as Valor")

    if anos:
        if "t" not in joins:
            tables.append("dim_tempo t")
            joins.add("t")
            where_parts.append("f.sk_tempo = t.sk_tempo")
        anos_str = ", ".join(str(a) for a in anos)
        where_parts.append(f"t.ano_enade IN ({anos_str})")

    filter_map = {
        "nome_regiao": regioes, "uf": ufs, "nome_curso": cursos,
        "sexo": sexo, "cor_raca": cor_raca, "renda_familiar": renda,
        "modalidade_graduacao": modalidade, "categoria_administrativa": categoria,
    }
    for dim_name, values in filter_map.items():
        if values:
            tbl, col, join_cond = dim_map[dim_name]
            label = tbl.split()[-1]
            if label not in joins:
                tables.append(tbl)
                joins.add(label)
                where_parts.append(join_cond)
            v_str = ", ".join(f"'{v}'" for v in values)
            where_parts.append(f"{col} IN ({v_str})")

    query = f"SELECT {', '.join(select_parts)} FROM {' JOIN '.join(tables)} WHERE {' AND '.join(where_parts)}"
    if group_parts:
        query += f" GROUP BY {', '.join(group_parts)}"
    query += " ORDER BY Valor DESC"
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Visão Geral", "Desempenho", "Geográfico",
    "Perfil Estudante", "Avaliação da Prova",
    "OLAP", "Dados Detalhados",
])

MAX_ROWS = 100000
if filters_active:
    df = query_data(get_simple_query(**params, random_limit=MAX_ROWS))
else:
    df = query_data(get_simple_query(random_limit=MAX_ROWS))

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
            st.plotly_chart(fig, width='stretch')
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
                fig = px.bar(means, y="Componente", x="Média", title="Média por Componente de Nota", orientation="h")
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

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
            st.plotly_chart(fig, width='stretch')

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
                    perf_dim, x="Média", y=dim_choice,
                    color="Quantidade",
                    title=f"Média da Nota Geral por {dim_choice}",
                    text_auto=".1f",
                    orientation="h",
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, width='stretch')

        if "sexo" in df.columns and "cor_raca" in df.columns:
            col1, col2 = st.columns(2)
            with col1:
                perf_sexo = df.groupby("sexo")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_sexo, y="sexo", x="nota_geral", title="Média por Sexo", orientation="h")
                st.plotly_chart(fig, width='stretch')
            with col2:
                perf_cor = df.groupby("cor_raca")["nota_geral"].mean().reset_index().sort_values("nota_geral", ascending=False)
                fig = px.bar(perf_cor, y="cor_raca", x="nota_geral", title="Média por Cor/Raça", orientation="h")
                st.plotly_chart(fig, width='stretch')

with tab3:
    st.subheader("Análise Geográfica")

    geo_params = {
        "anos": anos_sel or None,
        "regioes": reg_sel or None,
        "ufs": uf_sel or None,
        "cursos": cursos_sel or None,
    }

    perf_reg = query_data(build_geo_region_query(**geo_params))
    if perf_reg.empty:
        st.warning("Dados geográficos indisponíveis.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(perf_reg, y="nome_regiao", x="Média", color="Quantidade", title="Média por Região", text_auto=".1f", orientation="h")
            st.plotly_chart(fig, width='stretch')
        with col2:
            if len(perf_reg) > 1:
                anos = geo_params["anos"]
                tempo_join = "LEFT JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo"
                if anos:
                    anos_str = ", ".join(str(a) for a in anos)
                    tempo_join += f" AND t.ano_enade IN ({anos_str})"
                heat_sql = f"""
                    SELECT c.nome_regiao, c.modalidade_graduacao, AVG(f.nota_geral) as media
                    FROM dim_curso c
                    LEFT JOIN fato_enade f ON f.sk_curso = c.sk_curso
                    {tempo_join}
                    WHERE c.nome_regiao != 'Não Informado'
                    AND c.modalidade_graduacao NOT IN ('Não Informado', '')
                    GROUP BY c.nome_regiao, c.modalidade_graduacao
                """
                heat_df = query_data(heat_sql)
                if not heat_df.empty:
                    heat = heat_df.pivot_table(values="media", index="nome_regiao", columns="modalidade_graduacao", aggfunc="mean")
                    fig = px.imshow(heat, text_auto=".1f", title="Nota Geral Média: Região x Modalidade", aspect="auto")
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')

        perf_uf = query_data(build_geo_uf_query(**geo_params))
        fig = px.bar(perf_uf, y="uf", x="Média", color="Quantidade", title="Média por UF", text_auto=".1f", orientation="h")
        fig.update_layout(height=600)
        st.plotly_chart(fig, width='stretch')

with tab4:
    st.subheader("Análise do Perfil do Estudante")

    params_estudante = params.copy()
    df_perfil = query_data(get_simple_query(**params_estudante, force_estudante=True, random_limit=MAX_ROWS))

    has_perfil = "sexo" in df_perfil.columns and "cor_raca" in df_perfil.columns
    if df_perfil.empty or not has_perfil:
        st.warning("Dados de perfil indisponíveis.")
    else:
        df = df_perfil
        col1, col2 = st.columns(2)
        with col1:
            perf = df.groupby(["sexo", "cor_raca"])["nota_geral"].mean().reset_index()
            fig = px.bar(perf, y="cor_raca", x="nota_geral", color="sexo", barmode="group", title="Nota Geral por Sexo e Cor/Raça", orientation="h")
            st.plotly_chart(fig, width='stretch')
        with col2:
            if "renda_familiar" in df.columns:
                perf_renda = df.groupby("renda_familiar")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_renda, y="renda_familiar", x="nota_geral", title="Média por Renda Familiar", orientation="h")
                st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)
        with col1:
            if "tipo_escola_ensino_medio" in df.columns:
                perf_esc = df.groupby("tipo_escola_ensino_medio")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_esc, y="tipo_escola_ensino_medio", x="nota_geral", title="Média por Tipo de Escola (Ensino Médio)", orientation="h")
                st.plotly_chart(fig, width='stretch')
        with col2:
            if "escolaridade_pai" in df.columns:
                perf_pai = df.groupby("escolaridade_pai")["nota_geral"].mean().reset_index().sort_values("nota_geral", ascending=False)
                fig = px.bar(perf_pai, y="escolaridade_pai", x="nota_geral", title="Média por Escolaridade do Pai", orientation="h")
                st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)
        with col1:
            if "horas_trabalho" in df.columns:
                perf_hr = df.groupby("horas_trabalho")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_hr, y="horas_trabalho", x="nota_geral", title="Média por Carga Horária de Trabalho", orientation="h")
                st.plotly_chart(fig, width='stretch')
        with col2:
            if "cotas" in df.columns:
                perf_cotas = df.groupby("cotas")["nota_geral"].mean().reset_index().sort_values("nota_geral", ascending=False)
                fig = px.bar(perf_cotas, y="cotas", x="nota_geral", title="Média por Tipo de Cota", orientation="h")
                st.plotly_chart(fig, width='stretch')

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
                fig = px.line(dif_fg, y="grau_dificuldade_prova_formacao_geral", x="nota_geral", markers=True, title="Nota Geral vs. Dificuldade (Formação Geral)")
                fig.update_layout(yaxis_categoryorder="array", yaxis_categoryarray=list(reversed(ordem)))
                st.plotly_chart(fig, width='stretch')
        with col2:
            if "nota_componente_especifico" in df.columns:
                ordem = ["Muito fácil", "Fácil", "Médio", "Difícil", "Muito difícil", "Não informado"]
                dif_ce = df.groupby("grau_dificuldade_prova_componente_especifico")["nota_componente_especifico"].mean().reset_index()
                dif_ce["ordem"] = dif_ce["grau_dificuldade_prova_componente_especifico"].apply(lambda x: ordem.index(x) if x in ordem else 99)
                dif_ce = dif_ce.sort_values("ordem")
                fig = px.line(dif_ce, y="grau_dificuldade_prova_componente_especifico", x="nota_componente_especifico", markers=True, title="Nota Comp. Específico vs. Dificuldade")
                fig.update_layout(yaxis_categoryorder="array", yaxis_categoryarray=list(reversed(ordem)))
                st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)
        with col1:
            if "avaliacao_da_relacao_extensao_tempo_prova" in df.columns and "nota_geral" in df.columns:
                perf_tmp = df.groupby("avaliacao_da_relacao_extensao_tempo_prova")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_tmp, y="avaliacao_da_relacao_extensao_tempo_prova", x="nota_geral", title="Nota Geral vs. Relação Extensão/Tempo", orientation="h")
                st.plotly_chart(fig, width='stretch')
        with col2:
            if "tempo_de_prova" in df.columns and "nota_geral" in df.columns:
                perf_tp = df.groupby("tempo_de_prova")["nota_geral"].mean().reset_index()
                fig = px.bar(perf_tp, y="tempo_de_prova", x="nota_geral", title="Nota Geral vs. Tempo de Prova", orientation="h")
                st.plotly_chart(fig, width='stretch')

        if "avaliacao_equipamentos_curso" in df.columns and "avaliacao_ambiente_curso" in df.columns:
            col1, col2 = st.columns(2)
            with col1:
                if "nota_geral" in df.columns:
                    perf_eq = df.groupby("avaliacao_equipamentos_curso")["nota_geral"].mean().reset_index()
                    fig = px.bar(perf_eq, y="avaliacao_equipamentos_curso", x="nota_geral", title="Nota Geral vs. Avaliação dos Equipamentos", orientation="h")
                    st.plotly_chart(fig, width='stretch')
            with col2:
                if "nota_geral" in df.columns:
                    perf_amb = df.groupby("avaliacao_ambiente_curso")["nota_geral"].mean().reset_index()
                    fig = px.bar(perf_amb, y="avaliacao_ambiente_curso", x="nota_geral", title="Nota Geral vs. Avaliação do Ambiente", orientation="h")
                    st.plotly_chart(fig, width='stretch')

with tab6:
    st.subheader("Consulta OLAP")

    dim_opcoes = {
        "ano_enade": "Ano",
        "nome_regiao": "Região",
        "nome_estado": "Estado",
        "uf": "UF",
        "nome_municipio": "Município",
        "nome_curso": "Curso",
        "modalidade_graduacao": "Modalidade",
        "turno_graduacao": "Turno",
        "categoria_administrativa": "Categoria Adm.",
        "sexo": "Sexo",
        "cor_raca": "Cor/Raça",
        "renda_familiar": "Renda Familiar",
    }
    medidas = {
        "nota_geral": "Nota Geral",
        "nota_formacao_geral": "Formação Geral",
        "nota_componente_especifico": "Componente Específico",
        "nota_parte_objetiva_formacao_geral": "Objetiva (Formação Geral)",
        "nota_parte_discursiva_formacao_geral": "Discursiva (Formação Geral)",
        "nota_parte_objetiva_componente_especifico": "Objetiva (Comp. Específico)",
        "nota_parte_discursiva_componente_especifico": "Discursiva (Comp. Específico)",
    }
    agregacoes = {
        "AVG": "Média",
        "COUNT": "Contagem",
        "SUM": "Soma",
        "MIN": "Mínimo",
        "MAX": "Máximo",
    }

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        dim_linha = st.selectbox("Dimensão (linhas)", options=list(dim_opcoes.keys()), format_func=lambda x: dim_opcoes[x])
    with col2:
        dim_coluna_opts = {"": "(Nenhuma)"}
        dim_coluna_opts.update(dim_opcoes)
        dim_coluna = st.selectbox("Dimensão (colunas)", options=list(dim_coluna_opts.keys()), format_func=lambda x: dim_coluna_opts[x])
    with col3:
        medida = st.selectbox("Medida", options=list(medidas.keys()), format_func=lambda x: medidas[x])
    with col4:
        agregacao = st.selectbox("Agregação", options=list(agregacoes.keys()), format_func=lambda x: agregacoes[x])

    olap_params = {
        "rows": dim_linha,
        "cols": dim_coluna if dim_coluna else None,
        "measure": medida,
        "agg": agregacao,
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

    try:
        olap_sql = build_olap_query(**olap_params)
        olap_df = query_data(olap_sql)

        if olap_df.empty:
            st.warning("Nenhum resultado para essa consulta.")
        else:
            if dim_coluna:
                pivot = olap_df.pivot_table(
                    values="Valor",
                    index=dim_linha,
                    columns=dim_coluna,
                    aggfunc="first",
                )
                st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)

                if len(pivot) > 1 and len(pivot.columns) > 1:
                    fig = px.imshow(
                        pivot,
                        text_auto=".2f",
                        title=f"{agregacoes[agregacao]} de {medidas[medida]} por {dim_opcoes[dim_linha]} x {dim_opcoes[dim_coluna]}",
                        aspect="auto",
                        color_continuous_scale="RdBu_r",
                    )
                    fig.update_layout(height=max(400, len(pivot) * 35))
                    st.plotly_chart(fig, width='stretch')
            else:
                fig = px.bar(
                    olap_df,
                    x="Valor",
                    y=dim_linha,
                    title=f"{agregacoes[agregacao]} de {medidas[medida]} por {dim_opcoes[dim_linha]}",
                    text_auto=".2f",
                    orientation="h",
                )
                fig.update_layout(height=max(400, len(olap_df) * 30))
                st.plotly_chart(fig, width='stretch')

                st.dataframe(olap_df.style.format({"Valor": "{:.2f}"}), use_container_width=True)

            st.caption(f"SQL: `{olap_sql}`")
    except Exception as e:
        st.error(f"Erro na consulta OLAP: {e}")

with tab7:
    st.subheader("Dados Detalhados")

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
