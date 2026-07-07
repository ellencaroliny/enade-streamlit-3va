"""ETL: bancoBaseEnade.sql (normalized) -> enade_dw.db (star schema)"""
import sqlite3
import re
import os
import time

BASE_DUMP = r"C:\Users\valcann\Downloads\bancoBaseEnade.sql"
BASE_DB = os.path.join(os.path.dirname(__file__), "enade_base.db")
DW_PATH = os.path.join(os.path.dirname(__file__), "enade_dw.db")


def mysql_to_sqlite_type(raw: str) -> str:
    raw = raw.strip().upper()
    if raw.startswith("INT") or raw.startswith("TINYINT") or raw.startswith("SMALLINT"):
        return "INTEGER"
    if raw.startswith("DECIMAL") or raw.startswith("FLOAT") or raw.startswith("DOUBLE"):
        return "REAL"
    return "TEXT"


def extract_columns_from_create(sql: str):
    cols = []
    m = re.search(r"\((.*)\)", sql, re.DOTALL)
    if not m:
        return cols
    body = m.group(1)
    parts = []
    depth = 0
    current = []
    for ch in body:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    kw_skip = {"PRIMARY", "KEY", "INDEX", "CONSTRAINT", "FOREIGN", "UNIQUE", "CHECK"}
    for part in parts:
        first_word = part.split(None, 1)[0].strip("`").upper()
        if first_word in kw_skip:
            continue
        tokens = part.split(None, 2)
        if len(tokens) < 2:
            continue
        cname = tokens[0].strip("`")
        ctype = mysql_to_sqlite_type(tokens[1])
        cols.append((cname, ctype))
    return cols


def parse_insert_values(text: str):
    text = text.strip().rstrip(";").strip()
    rows = []
    i = 0
    while i < len(text):
        if text[i] == "(":
            depth = 1
            j = i + 1
            while j < len(text) and depth > 0:
                if text[j] == "'":
                    j += 1
                    while j < len(text):
                        if text[j] == "\\":
                            j += 2
                            continue
                        if text[j] == "'":
                            break
                        j += 1
                elif text[j] == "(":
                    depth += 1
                elif text[j] == ")":
                    depth -= 1
                j += 1
            row_text = text[i + 1 : j - 1]
            vals = []
            k = 0
            while k < len(row_text):
                ch = row_text[k]
                if ch in " \t\r\n,":
                    k += 1
                    continue
                if ch == "'":
                    k += 1
                    buf = []
                    while k < len(row_text):
                        if row_text[k] == "\\":
                            buf.append(row_text[k + 1])
                            k += 2
                            continue
                        if row_text[k] == "'":
                            k += 1
                            break
                        buf.append(row_text[k])
                        k += 1
                    vals.append("".join(buf))
                elif row_text[k:k+4] == "NULL" or row_text[k:k+4] == "null":
                    vals.append(None)
                    k += 4
                else:
                    buf = []
                    while k < len(row_text) and row_text[k] not in ",)":
                        buf.append(row_text[k])
                        k += 1
                    val = "".join(buf).strip()
                    vals.append(None if val.upper() == "NULL" or val == "" else val)
                while k < len(row_text) and row_text[k] in " \t\r\n,":
                    k += 1
            rows.append(vals)
            i = j
        else:
            i += 1
    return rows


def import_base_dump():
    """Import bancoBaseEnade.sql into enade_base.db (normalized schema)."""
    if os.path.exists(BASE_DB):
        os.remove(BASE_DB)

    print("Lendo bancoBaseEnade.sql...")
    with open(BASE_DUMP, "r", encoding="latin-1", errors="replace") as f:
        dump_content = f.read()

    conn = sqlite3.connect(BASE_DB)
    cur = conn.cursor()

    all_cols = {}
    # Find CREATE TABLE in the entire dump
    create_blocks = re.findall(
        r"CREATE TABLE.*?`(\w+)`\s*\((.*?)\)\s*ENGINE\s*=",
        dump_content,
        re.DOTALL | re.IGNORECASE,
    )
    if not create_blocks:
        create_blocks = re.findall(
            r"CREATE TABLE.*?`(\w+)`\s*\((.*?)\)",
            dump_content,
            re.DOTALL | re.IGNORECASE,
        )

    for tname, body in create_blocks:
        full_sql = f"CREATE TABLE `{tname}` ({body})"
        cols = extract_columns_from_create(full_sql)
        if cols:
            cur.execute(f'DROP TABLE IF EXISTS "{tname}"')
            col_defs = [f'"{c}" {t}' for c, t in cols]
            sql = f'CREATE TABLE "{tname}" (\n  {", ".join(col_defs)}\n)'
            cur.execute(sql)
            all_cols[tname] = [c for c, t in cols]
            print(f"  Tabela criada: {tname} ({len(cols)} colunas)")

    insert_pattern = re.compile(
        r"INSERT\s+INTO\s+`(\w+)`\s*VALUES\s*",
        re.IGNORECASE,
    )
    row_count = {t: 0 for t in all_cols}

    for m in insert_pattern.finditer(dump_content):
        tname = m.group(1)
        if tname not in all_cols:
            continue
        start = m.end()
        end = start
        depth = 0
        in_string = False
        while end < len(dump_content):
            ch = dump_content[end]
            if in_string:
                if ch == "\\":
                    end += 1
                elif ch == "'":
                    in_string = False
            else:
                if ch == "'":
                    in_string = True
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == ";" and depth == 0:
                    break
            end += 1
        values_text = dump_content[start:end]
        if values_text.endswith(";"):
            values_text = values_text[:-1]

        rows = parse_insert_values(values_text)
        cols = all_cols[tname]
        batch = []
        for vals in rows:
            vals = vals[: len(cols)]
            while len(vals) < len(cols):
                vals.append(None)
            batch.append(vals)
            if len(batch) >= 5000:
                placeholders = ", ".join("?" for _ in cols)
                col_names = ", ".join(f'"{c}"' for c in cols)
                try:
                    cur.executemany(
                        f'INSERT INTO "{tname}" ({col_names}) VALUES ({placeholders})',
                        batch,
                    )
                    row_count[tname] += len(batch)
                except Exception:
                    pass
                batch = []
        if batch:
            placeholders = ", ".join("?" for _ in cols)
            col_names = ", ".join(f'"{c}"' for c in cols)
            try:
                cur.executemany(
                    f'INSERT INTO "{tname}" ({col_names}) VALUES ({placeholders})',
                    batch,
                )
                row_count[tname] += len(batch)
            except Exception:
                pass

    conn.commit()
    for t in all_cols:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {cnt} linhas")
    conn.close()
    print(f"Base importada em: {BASE_DB}")


def build_star_schema():
    """Transform enade_base.db (normalized) -> enade_dw.db (star schema)."""
    if os.path.exists(DW_PATH):
        os.remove(DW_PATH)

    base = sqlite3.connect(BASE_DB)
    dw = sqlite3.connect(DW_PATH)
    base.row_factory = sqlite3.Row
    cur_dw = dw.cursor()

    print("\n--- Criando star schema ---")

    # =============================================
    # dim_tempo
    # =============================================
    cur_dw.execute("""
        CREATE TABLE dim_tempo (
            sk_tempo INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tempo INTEGER,
            ano_enade INTEGER,
            data_aplicacao_prova TEXT,
            ano_extenso TEXT,
            decada INTEGER,
            decada_extenso TEXT,
            ciclo INTEGER,
            ano_relativo_ciclo INTEGER,
            flag_ultimo_enade INTEGER,
            edicao_anterior INTEGER,
            date_from TEXT,
            date_to TEXT,
            version INTEGER DEFAULT 1
        )
    """)
    anos = base.execute("SELECT DISTINCT ano_enade FROM enade ORDER BY ano_enade").fetchall()
    for sk, row in enumerate(anos, start=1):
        ano = row["ano_enade"]
        cur_dw.execute(
            "INSERT INTO dim_tempo (sk_tempo, id_tempo, ano_enade, data_aplicacao_prova, ano_extenso, version) VALUES (?, ?, ?, ?, ?, 1)",
            (sk, ano, ano, f"{ano}-01-01", str(ano)),
        )
    cnt = cur_dw.execute("SELECT COUNT(*) FROM dim_tempo").fetchone()[0]
    print(f"  dim_tempo: {cnt} linhas")

    # =============================================
    # dim_curso  (via oferta -> cursos, municipios, estados, regiao)
    # =============================================
    cur_dw.execute("""
        CREATE TABLE dim_curso (
            sk_curso INTEGER PRIMARY KEY AUTOINCREMENT,
            id_curso INTEGER,
            nome_curso TEXT,
            nome_municipio TEXT,
            uf TEXT,
            nome_estado TEXT,
            nome_regiao TEXT,
            modalidade_graduacao TEXT,
            turno_graduacao TEXT,
            categoria_administrativa TEXT,
            date_from TEXT,
            date_to TEXT,
            version INTEGER DEFAULT 1
        )
    """)
    # Create a temporary mapping table to link id_oferta to sk_curso
    cur_dw.execute("""
        CREATE TABLE _curso_map (
            id_oferta INTEGER PRIMARY KEY,
            sk_curso INTEGER
        )
    """)
    ofertas = base.execute("""
        SELECT o.id_oferta, o.id_curso, c.nome_curso,
               m.id_municipio, m.nome_municipio, m.uf,
               es.nome_estado, r.nome_regiao,
               o.modalidade_graduacao, o.turno_graduacao, o.categoria_administrativa
        FROM oferta o
        JOIN cursos c ON o.id_curso = c.id_curso
        JOIN municipios m ON o.id_municipio = m.id_municipio
        JOIN estados es ON m.uf = es.uf
        JOIN regiao r ON es.id_regiao = r.id_regiao
        ORDER BY o.id_oferta
    """).fetchall()

    curso_batch = []
    for oferta in ofertas:
        curso_batch.append((
            oferta["id_curso"],
            oferta["nome_curso"],
            oferta["nome_municipio"],
            oferta["uf"],
            oferta["nome_estado"],
            oferta["nome_regiao"],
            oferta["modalidade_graduacao"],
            oferta["turno_graduacao"],
            oferta["categoria_administrativa"],
            None,
            None,
            1,
        ))
        if len(curso_batch) >= 5000:
            cur_dw.executemany(
                "INSERT INTO dim_curso (id_curso, nome_curso, nome_municipio, uf, nome_estado, nome_regiao, modalidade_graduacao, turno_graduacao, categoria_administrativa, date_from, date_to, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                curso_batch,
            )
            curso_batch = []
    if curso_batch:
        cur_dw.executemany(
            "INSERT INTO dim_curso (id_curso, nome_curso, nome_municipio, uf, nome_estado, nome_regiao, modalidade_graduacao, turno_graduacao, categoria_administrativa, date_from, date_to, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            curso_batch,
        )

    cnt = cur_dw.execute("SELECT COUNT(*) FROM dim_curso").fetchone()[0]
    print(f"  dim_curso: {cnt} linhas")

    # Map id_oferta -> sk_curso (inserted in id_oferta order, so sk_curso = row_number)
    curso_map_data = [(o["id_oferta"], i + 1) for i, o in enumerate(ofertas)]
    cur_dw.executemany(
        "INSERT INTO _curso_map (id_oferta, sk_curso) VALUES (?, ?)",
        curso_map_data,
    )
    dw.commit()

    # =============================================
    # dim_avaliacao
    # =============================================
    cur_dw.execute("""
        CREATE TABLE dim_avaliacao (
            sk_avaliacao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_avaliacao INTEGER,
            grau_dificuldade_prova_formacao_geral TEXT,
            grau_dificuldade_prova_componente_especifico TEXT,
            avaliacao_da_relacao_extensao_tempo_prova TEXT,
            avaliacao_enunciados_componente_especifico TEXT,
            avaliacao_enunciados_formacao_geral TEXT,
            tempo_de_prova TEXT,
            avaliacao_equipamentos_curso TEXT,
            avaliacao_ambiente_curso TEXT,
            date_from TEXT,
            date_to TEXT,
            version INTEGER DEFAULT 1
        )
    """)
    avaliacoes = base.execute("""
        SELECT id_avaliacao,
               grau_dificuldade_prova_formacao_geral,
               grau_dificuldade_prova_componente_especifico,
               avaliacao_de_extensao_versus_tempo_de_prova,
               avaliacao_enunciados_componente_especifico,
               avaliacao_enunciados_formacao_geral,
               tempo_de_prova,
               avaliacao_equipamentos_curso,
               avaliacao_ambiente_curso
        FROM questionario_de_avaliacao
        ORDER BY id_avaliacao
    """).fetchall()

    av_batch = [(a["id_avaliacao"],
                 a["grau_dificuldade_prova_formacao_geral"],
                 a["grau_dificuldade_prova_componente_especifico"],
                 a["avaliacao_de_extensao_versus_tempo_de_prova"],
                 a["avaliacao_enunciados_componente_especifico"],
                 a["avaliacao_enunciados_formacao_geral"],
                 a["tempo_de_prova"],
                 a["avaliacao_equipamentos_curso"],
                 a["avaliacao_ambiente_curso"],
                 None, None, 1) for a in avaliacoes]

    cur_dw.executemany(
        "INSERT INTO dim_avaliacao (id_avaliacao, grau_dificuldade_prova_formacao_geral, grau_dificuldade_prova_componente_especifico, avaliacao_da_relacao_extensao_tempo_prova, avaliacao_enunciados_componente_especifico, avaliacao_enunciados_formacao_geral, tempo_de_prova, avaliacao_equipamentos_curso, avaliacao_ambiente_curso, date_from, date_to, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        av_batch,
    )
    cnt = cur_dw.execute("SELECT COUNT(*) FROM dim_avaliacao").fetchone()[0]
    print(f"  dim_avaliacao: {cnt} linhas")

    # =============================================
    # dim_estudante
    # =============================================
    cur_dw.execute("""
        CREATE TABLE dim_estudante (
            sk_estudante INTEGER PRIMARY KEY AUTOINCREMENT,
            id_estudante INTEGER,
            sexo TEXT,
            idade INTEGER,
            cor_raca TEXT,
            ano_fim_ensino_medio INTEGER,
            ano_ingresso_graduacao INTEGER,
            tipo_escola_ensino_medio TEXT,
            primeira_geracao TEXT,
            escolaridade_pai TEXT,
            escolaridade_mae TEXT,
            motivacao_curso TEXT,
            renda_familiar TEXT,
            horas_trabalho TEXT,
            cotas TEXT,
            date_from TEXT,
            date_to TEXT,
            version INTEGER DEFAULT 1
        )
    """)
    estudantes = base.execute("""
        SELECT id_perfil, sexo, idade, cor_raca, ano_fim_ensino_medio,
               ano_ingresso_graduacao, tipo_escola_ensino_medio, primeira_geracao,
               escolaridade_pai, escolaridade_mae, motivacao_curso,
               renda_familiar, horas_trabalho, cotas
        FROM estudante
        ORDER BY id_perfil
    """).fetchall()

    est_batch = [(e["id_perfil"], e["sexo"], e["idade"], e["cor_raca"],
                  e["ano_fim_ensino_medio"], e["ano_ingresso_graduacao"],
                  e["tipo_escola_ensino_medio"], e["primeira_geracao"],
                  e["escolaridade_pai"], e["escolaridade_mae"],
                  e["motivacao_curso"], e["renda_familiar"],
                  e["horas_trabalho"], e["cotas"],
                  None, None, 1) for e in estudantes]

    cur_dw.executemany(
        "INSERT INTO dim_estudante (id_estudante, sexo, idade, cor_raca, ano_fim_ensino_medio, ano_ingresso_graduacao, tipo_escola_ensino_medio, primeira_geracao, escolaridade_pai, escolaridade_mae, motivacao_curso, renda_familiar, horas_trabalho, cotas, date_from, date_to, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        est_batch,
    )
    cnt = cur_dw.execute("SELECT COUNT(*) FROM dim_estudante").fetchone()[0]
    print(f"  dim_estudante: {cnt} linhas")

    # =============================================
    # fato_enade
    # =============================================
    cur_dw.execute("""
        CREATE TABLE fato_enade (
            sk_tempo INTEGER NOT NULL,
            sk_curso INTEGER NOT NULL,
            sk_avaliacao INTEGER NOT NULL,
            sk_estudante INTEGER NOT NULL,
            nota_geral REAL,
            nota_formacao_geral REAL,
            nota_parte_objetiva_formacao_geral REAL,
            nota_parte_discursiva_formacao_geral REAL,
            nota_componente_especifico REAL,
            nota_parte_objetiva_componente_especifico REAL,
            nota_parte_discursiva_componente_especifico REAL
        )
    """)

    print("  Construindo fato_enade (pode levar alguns minutos)...")

    # Build lookup dicts once
    tempo_map = dict(dw.execute("SELECT ano_enade, sk_tempo FROM dim_tempo").fetchall())
    curso_map = dict(dw.execute("SELECT id_oferta, sk_curso FROM _curso_map").fetchall())
    av_map = dict(dw.execute("SELECT id_avaliacao, sk_avaliacao FROM dim_avaliacao").fetchall())
    est_map = dict(dw.execute("SELECT id_estudante, sk_estudante FROM dim_estudante").fetchall())

    # Process in chunks to avoid huge memory usage
    offset = 0
    chunk = 50000
    total_inserted = 0
    while True:
        enades = base.execute(f"""
            SELECT e.id_participacao, e.ano_enade, e.id_oferta, e.id_perfil, e.id_desempenho, e.id_avaliacao,
                   d.nota_geral, d.nota_formacao_geral,
                   d.nota_parte_objetiva_formacao_geral, d.nota_parte_discursiva_formacao_geral,
                   d.nota_componente_especifico,
                   d.nota_parte_objetiva_componente_especifico, d.nota_parte_discursiva_componente_especifico
            FROM enade e
            JOIN desempenho d ON e.id_desempenho = d.id_desempenho
            ORDER BY e.id_participacao
            LIMIT {chunk} OFFSET {offset}
        """).fetchall()
        if not enades:
            break

        fato_batch = []
        for e in enades:
            sk_tempo = tempo_map.get(e["ano_enade"])
            sk_curso = curso_map.get(e["id_oferta"])
            sk_av = av_map.get(e["id_avaliacao"])
            sk_est = est_map.get(e["id_perfil"])
            if not all([sk_tempo, sk_curso, sk_av, sk_est]):
                continue
            fato_batch.append((
                sk_tempo, sk_curso, sk_av, sk_est,
                e["nota_geral"], e["nota_formacao_geral"],
                e["nota_parte_objetiva_formacao_geral"], e["nota_parte_discursiva_formacao_geral"],
                e["nota_componente_especifico"],
                e["nota_parte_objetiva_componente_especifico"], e["nota_parte_discursiva_componente_especifico"],
            ))

        cur_dw.executemany(
            "INSERT INTO fato_enade (sk_tempo, sk_curso, sk_avaliacao, sk_estudante, nota_geral, nota_formacao_geral, nota_parte_objetiva_formacao_geral, nota_parte_discursiva_formacao_geral, nota_componente_especifico, nota_parte_objetiva_componente_especifico, nota_parte_discursiva_componente_especifico) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            fato_batch,
        )
        total_inserted += len(fato_batch)
        dw.commit()
        offset += chunk
        print(f"    {total_inserted} registros inseridos...")

    cnt = cur_dw.execute("SELECT COUNT(*) FROM fato_enade").fetchone()[0]
    print(f"  fato_enade: {cnt} linhas")

    # Cleanup temp table
    cur_dw.execute("DROP TABLE IF EXISTS _curso_map")
    dw.commit()
    dw.close()
    base.close()
    print(f"\nStar schema salvo em: {DW_PATH}")


def verify():
    conn = sqlite3.connect(DW_PATH)
    cur = conn.cursor()
    print("\n--- Verificação ---")
    for t in ["dim_tempo", "dim_curso", "dim_avaliacao", "dim_estudante", "fato_enade"]:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {cnt} linhas")
    print("\nRegiões na fato_enade:")
    cur.execute("""
        SELECT c.nome_regiao, COUNT(*) as qtde
        FROM fato_enade f
        JOIN dim_curso c ON f.sk_curso = c.sk_curso
        GROUP BY c.nome_regiao
        ORDER BY c.nome_regiao
    """)
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")
    conn.close()


if __name__ == "__main__":
    t0 = time.time()
    import_base_dump()
    build_star_schema()
    verify()
    print(f"\nTempo total: {time.time() - t0:.1f}s")
