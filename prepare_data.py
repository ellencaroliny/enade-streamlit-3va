import sqlite3
import re
import os

# ATENÇÃO: Este script foi substituído pelo etl_enade.py
# Use: python etl_enade.py
# Ele carrega o bancoBaseEnade.sql (normalizado) e transforma para o star schema.

DW_DUMP = r"C:\Users\valcann\Downloads\bancoBaseEnade.sql"
CREATE_DW = DW_DUMP
DB_PATH = os.path.join(os.path.dirname(__file__), "enade_dw.db")


def mysql_to_sqlite_type(raw: str) -> str:
    raw = raw.strip().upper()
    if raw.startswith("INT") or raw.startswith("TINYINT") or raw.startswith("SMALLINT"):
        return "INTEGER"
    if raw.startswith("DECIMAL") or raw.startswith("FLOAT") or raw.startswith("DOUBLE"):
        return "REAL"
    if raw.startswith("DATE") or raw.startswith("TIMESTAMP") or raw.startswith("VARCHAR") or raw.startswith("CHAR"):
        return "TEXT"
    return "TEXT"


def extract_columns_from_create(sql: str):
    """Extract column names and types from a single CREATE TABLE statement."""
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


def parse_and_create_sqlite():
    print("Lendo bancoEnadeDW.sql (DDL)...")
    with open(CREATE_DW, "r", encoding="latin-1", errors="replace") as f:
        create_sql = f.read()

    print("Lendo bancoEnadeDW.sql (dados)...")
    with open(DW_DUMP, "r", encoding="latin-1", errors="replace") as f:
        dump_content = f.read()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    create_blocks = re.findall(
        r"CREATE TABLE.*?`(\w+)`\s*\((.*?)\)\s*ENGINE\s*=\s*\w+",
        create_sql,
        re.DOTALL | re.IGNORECASE,
    )

    if not create_blocks:
        create_blocks = re.findall(
            r"CREATE TABLE.*?`(\w+)`\s*\((.*?)\)\s*ENGINE\s*=",
            dump_content,
            re.DOTALL | re.IGNORECASE,
        )

    all_cols = {}
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

        for vals in rows:
            vals = vals[: len(cols)]
            while len(vals) < len(cols):
                vals.append(None)
            placeholders = ", ".join("?" for _ in cols)
            col_names = ", ".join(f'"{c}"' for c in cols)
            try:
                cur.execute(
                    f'INSERT INTO "{tname}" ({col_names}) VALUES ({placeholders})',
                    vals,
                )
                row_count[tname] += 1
            except Exception:
                pass

    conn.commit()
    print("\nResumo final:")
    for t in all_cols:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {cnt} linhas")
    conn.close()
    print(f"\nBanco SQLite salvo em: {DB_PATH}")


if __name__ == "__main__":
    parse_and_create_sqlite()
