import io
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether


st.set_page_config(
    page_title="ITB Clinical",
    page_icon="🫀",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB = Path("itb_clinical.db")
APP_VERSION = "Versão 2.0 — 08/09/2026"
BRAZIL_TZ = timezone(timedelta(hours=-3))

FIELDS = [
    ("protocolo", "TEXT"),
    ("nome_sujeito", "TEXT"),
    ("avaliador", "TEXT"),
    ("data_avaliacao", "TEXT"),
    ("horario", "TEXT"),
    ("realizado_em", "TEXT"),
    ("sintoma_caminhar", "TEXT"),
    ("local_sintoma", "TEXT"),
    ("outro_local_sintoma", "TEXT"),
    ("melhora_repouso", "TEXT"),
    ("tempo_melhora", "INTEGER"),
    ("dor_repouso", "TEXT"),
    ("lesoes", "TEXT"),
    ("local_lesao", "TEXT"),
    ("achados_pele", "TEXT"),
    ("outro_achado_pele", "TEXT"),
    ("femoral_d", "TEXT"),
    ("femoral_e", "TEXT"),
    ("popliteo_d", "TEXT"),
    ("popliteo_e", "TEXT"),
    ("tibial_pulso_d", "TEXT"),
    ("tibial_pulso_e", "TEXT"),
    ("pedioso_pulso_d", "TEXT"),
    ("pedioso_pulso_e", "TEXT"),
    ("metodo_medida", "TEXT"),
    ("repouso_previo", "TEXT"),
    ("braquial_direita", "REAL"),
    ("braquial_esquerda", "REAL"),
    ("pediosa_direita", "REAL"),
    ("pediosa_esquerda", "REAL"),
    ("tibial_posterior_direita", "REAL"),
    ("tibial_posterior_esquerda", "REAL"),
    ("itb_direito", "REAL"),
    ("classificacao_direito", "TEXT"),
    ("itb_esquerdo", "REAL"),
    ("classificacao_esquerdo", "TEXT"),
    ("claudicacao_12m", "TEXT"),
    ("itb_menor_090", "TEXT"),
    ("observacoes", "TEXT"),
]


def now_br():
    return datetime.now(BRAZIL_TZ)


def init_db():
    con = sqlite3.connect(DB)
    cols = ", ".join(f"{name} {col_type}" for name, col_type in FIELDS)
    con.execute(
        f"CREATE TABLE IF NOT EXISTS avaliacoes "
        f"(id INTEGER PRIMARY KEY AUTOINCREMENT, {cols})"
    )

    # Migração simples: novos campos são acrescentados sem apagar registros antigos.
    existing = {
        row[1] for row in con.execute("PRAGMA table_info(avaliacoes)").fetchall()
    }
    for name, col_type in FIELDS:
        if name not in existing:
            con.execute(f"ALTER TABLE avaliacoes ADD COLUMN {name} {col_type}")

    con.commit()
    con.close()


init_db()


def clean_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def classify(x):
    if x is None:
        return "Não calculável"
    if x <= 0.90:
        return "Anormal"
    if x <= 0.99:
        return "Limítrofe"
    if x <= 1.40:
        return "Normal"
    return "Não compressível"


def eligibility_itb(itb_d, itb_e):
    vals = [v for v in (itb_d, itb_e) if v is not None]
    if any(v < 0.90 for v in vals):
        return "Sim"
    if len(vals) == 2:
        return "Não"
    return "Não avaliável"


def save_record(data):
    con = sqlite3.connect(DB)
    cols = list(data)
    placeholders = ",".join("?" for _ in cols)
    con.execute(
        f"INSERT INTO avaliacoes ({','.join(cols)}) VALUES ({placeholders})",
        tuple(data[c] for c in cols),
    )
    con.commit()
    con.close()


def get_data():
    con = sqlite3.connect(DB)
    df = pd.read_sql_query(
        "SELECT * FROM avaliacoes ORDER BY id DESC",
        con,
    )
    con.close()
    return df


def row_to_record(row):
    return {
        name: clean_value(row[name]) if name in row.index else None
        for name, _ in FIELDS
    }


EXPORT_COLUMNS = [
    "id",
    "protocolo",
    "nome_sujeito",
    "avaliador",
    "data_avaliacao",
    "horario",
    "realizado_em",
    "sintoma_caminhar",
    "local_sintoma",
    "outro_local_sintoma",
    "melhora_repouso",
    "tempo_melhora",
    "dor_repouso",
    "lesoes",
    "local_lesao",
    "achados_pele",
    "outro_achado_pele",
    "femoral_d",
    "femoral_e",
    "popliteo_d",
    "popliteo_e",
    "tibial_pulso_d",
    "tibial_pulso_e",
    "pedioso_pulso_d",
    "pedioso_pulso_e",
    "metodo_medida",
    "repouso_previo",
    "braquial_direita",
    "braquial_esquerda",
    "pediosa_direita",
    "pediosa_esquerda",
    "tibial_posterior_direita",
    "tibial_posterior_esquerda",
    "itb_direito",
    "classificacao_direito",
    "itb_esquerdo",
    "classificacao_esquerdo",
    "claudicacao_12m",
    "itb_menor_090",
    "observacoes",
]

EXPORT_LABELS = {
    "id": "ID",
    "protocolo": "Protocolo / estudo",
    "nome_sujeito": "Nome do sujeito",
    "avaliador": "Avaliador",
    "data_avaliacao": "Data da avaliação",
    "horario": "Horário da avaliação",
    "realizado_em": "Data/hora do registro",
    "sintoma_caminhar": "Sintomas ao caminhar",
    "local_sintoma": "Local do sintoma",
    "outro_local_sintoma": "Outro local do sintoma",
    "melhora_repouso": "Melhora com repouso",
    "tempo_melhora": "Tempo para melhora (min)",
    "dor_repouso": "Dor em repouso",
    "lesoes": "Feridas / úlceras / gangrena / lesões",
    "local_lesao": "Local da lesão",
    "achados_pele": "Achados de pele",
    "outro_achado_pele": "Outro achado de pele",
    "femoral_d": "Pulso femoral — Direito",
    "femoral_e": "Pulso femoral — Esquerdo",
    "popliteo_d": "Pulso poplíteo — Direito",
    "popliteo_e": "Pulso poplíteo — Esquerdo",
    "tibial_pulso_d": "Pulso tibial posterior — Direito",
    "tibial_pulso_e": "Pulso tibial posterior — Esquerdo",
    "pedioso_pulso_d": "Pulso pedioso — Direito",
    "pedioso_pulso_e": "Pulso pedioso — Esquerdo",
    "metodo_medida": "Método utilizado para aferição",
    "repouso_previo": "Repouso prévio",
    "braquial_direita": "PAS braquial — Direita (mmHg)",
    "braquial_esquerda": "PAS braquial — Esquerda (mmHg)",
    "pediosa_direita": "PAS pediosa — Direita (mmHg)",
    "pediosa_esquerda": "PAS pediosa — Esquerda (mmHg)",
    "tibial_posterior_direita": "PAS tibial posterior — Direita (mmHg)",
    "tibial_posterior_esquerda": "PAS tibial posterior — Esquerda (mmHg)",
    "itb_direito": "ITB — Direito",
    "classificacao_direito": "Classificação — Direito",
    "itb_esquerdo": "ITB — Esquerdo",
    "classificacao_esquerdo": "Classificação — Esquerdo",
    "claudicacao_12m": "Claudicação nos últimos 12 meses",
    "itb_menor_090": "ITB < 0,90",
    "observacoes": "Observações",
}

EXPORT_GROUPS = [
    ("Identificação", 0, 6),
    ("Sintomas e avaliação clínica", 7, 16),
    ("Pulsos periféricos", 17, 24),
    ("Pressões sistólicas", 25, 30),
    ("Resultado do ITB", 31, 34),
    ("Elegibilidade", 35, 36),
    ("Observações", 37, 37),
]


def organized_export_df(df):
    cols = [c for c in EXPORT_COLUMNS if c in df.columns]
    out = df[cols].copy()
    return out.rename(columns={c: EXPORT_LABELS.get(c, c) for c in cols})


def excel_export(df):
    export_df = organized_export_df(df)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, sheet_name="Avaliações", startrow=2, index=False)

        workbook = writer.book
        worksheet = writer.sheets["Avaliações"]

        fmt_group = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#17365D",
            "font_color": "#FFFFFF",
            "border": 1,
        })
        fmt_header = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#D9EAF7",
            "font_color": "#17365D",
            "border": 1,
            "text_wrap": True,
        })
        fmt_text = workbook.add_format({
            "valign": "top",
            "border": 1,
            "text_wrap": True,
        })
        fmt_center = workbook.add_format({
            "align": "center",
            "valign": "vcenter",
            "border": 1,
        })
        fmt_itb = workbook.add_format({
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "num_format": "0.00",
        })

        for title, start_col, end_col in EXPORT_GROUPS:
            if start_col >= len(export_df.columns):
                continue
            end_col = min(end_col, len(export_df.columns) - 1)
            if start_col == end_col:
                worksheet.write(0, start_col, title, fmt_group)
            else:
                worksheet.merge_range(0, start_col, 0, end_col, title, fmt_group)

        for col_idx, col_name in enumerate(export_df.columns):
            worksheet.write(2, col_idx, col_name, fmt_header)

        worksheet.freeze_panes(3, 4)
        worksheet.autofilter(
            2, 0, 2 + len(export_df), max(0, len(export_df.columns) - 1)
        )
        worksheet.set_row(0, 24)
        worksheet.set_row(1, 6)
        worksheet.set_row(2, 42)

        widths = {
            "ID": 8,
            "Protocolo / estudo": 20,
            "Nome do sujeito": 24,
            "Avaliador": 22,
            "Data da avaliação": 15,
            "Horário da avaliação": 15,
            "Data/hora do registro": 22,
            "Sintomas ao caminhar": 19,
            "Local do sintoma": 20,
            "Outro local do sintoma": 20,
            "Melhora com repouso": 18,
            "Tempo para melhora (min)": 18,
            "Dor em repouso": 16,
            "Feridas / úlceras / gangrena / lesões": 24,
            "Local da lesão": 20,
            "Achados de pele": 28,
            "Outro achado de pele": 22,
            "Pulso femoral — Direito": 20,
            "Pulso femoral — Esquerdo": 20,
            "Pulso poplíteo — Direito": 20,
            "Pulso poplíteo — Esquerdo": 20,
            "Pulso tibial posterior — Direito": 23,
            "Pulso tibial posterior — Esquerdo": 23,
            "Pulso pedioso — Direito": 20,
            "Pulso pedioso — Esquerdo": 20,
            "PAS braquial — Direita (mmHg)": 22,
            "PAS braquial — Esquerda (mmHg)": 22,
            "PAS pediosa — Direita (mmHg)": 22,
            "PAS pediosa — Esquerda (mmHg)": 22,
            "PAS tibial posterior — Direita (mmHg)": 26,
            "PAS tibial posterior — Esquerda (mmHg)": 26,
            "ITB — Direito": 13,
            "Classificação — Direito": 18,
            "ITB — Esquerdo": 13,
            "Classificação — Esquerdo": 18,
            "Claudicação nos últimos 12 meses": 24,
            "ITB < 0,90": 14,
            "Observações": 36,
        }

        for i, col_name in enumerate(export_df.columns):
            worksheet.set_column(i, i, widths.get(col_name, 18), fmt_text)

        center_names = {
            "ID",
            "Data da avaliação",
            "Horário da avaliação",
            "Sintomas ao caminhar",
            "Melhora com repouso",
            "Dor em repouso",
            "Classificação — Direito",
            "Classificação — Esquerdo",
            "Claudicação nos últimos 12 meses",
            "ITB < 0,90",
        }
        for i, col_name in enumerate(export_df.columns):
            if col_name in center_names:
                worksheet.set_column(i, i, widths.get(col_name, 18), fmt_center)
            if col_name in {"ITB — Direito", "ITB — Esquerdo"}:
                worksheet.set_column(i, i, widths.get(col_name, 13), fmt_itb)

        # Sinalização visual das classificações no Excel.
        for col_name in ("Classificação — Direito", "Classificação — Esquerdo"):
            if col_name in export_df.columns:
                col_idx = export_df.columns.get_loc(col_name)
                first = 3
                last = max(3, 2 + len(export_df))
                worksheet.conditional_format(first, col_idx, last, col_idx, {
                    "type": "text",
                    "criteria": "containing",
                    "value": "Anormal",
                    "format": workbook.add_format({"bg_color": "#F4CCCC"}),
                })
                worksheet.conditional_format(first, col_idx, last, col_idx, {
                    "type": "text",
                    "criteria": "containing",
                    "value": "Limítrofe",
                    "format": workbook.add_format({"bg_color": "#FCE5CD"}),
                })
                worksheet.conditional_format(first, col_idx, last, col_idx, {
                    "type": "text",
                    "criteria": "containing",
                    "value": "Normal",
                    "format": workbook.add_format({"bg_color": "#D9EAD3"}),
                })

        worksheet.hide_gridlines(2)

    output.seek(0)
    return output.getvalue()


def display_value(value):
    value = clean_value(value)
    if value is None or value == "":
        return "Não informado"
    return str(value)


def format_measurement(value):
    value = clean_value(value)
    if value is None:
        return "Não avaliado"
    try:
        numeric = float(value)
        return str(int(numeric)) if numeric.is_integer() else str(numeric)
    except Exception:
        return str(value)


def format_minutes(value):
    value = clean_value(value)
    if value is None:
        return "Não informado"
    try:
        return f"{int(float(value))} min"
    except Exception:
        return f"{value} min"


def pressure(label, key):
    na = st.checkbox(f"Não avaliado — {label}", key=key + "_na")
    if na:
        st.number_input(
            label,
            min_value=1,
            max_value=300,
            value=None,
            step=1,
            key=key,
            placeholder="Não avaliado",
            disabled=True,
        )
        return None, True

    value = st.number_input(
        label,
        min_value=1,
        max_value=300,
        value=None,
        step=1,
        key=key,
        placeholder="Digite a PAS em mmHg",
    )
    return value, value is not None


def pulse(label, key):
    return st.selectbox(
        label,
        ["Não avaliado", "Normal", "Reduzido", "Ausente"],
        index=None,
        placeholder="Selecione",
        key=key,
    )


def result_display(label, value, classification):
    st.markdown(f"**{label}**")
    if value is None:
        st.markdown("### Não calculável")
        st.caption("⚪ Não calculável")
        return

    st.markdown(f"### {value:.2f}")
    if classification == "Anormal":
        st.error("🔴 Anormal")
    elif classification == "Limítrofe":
        st.warning("🟠 Limítrofe")
    elif classification == "Normal":
        st.success("🟢 Normal")
    elif classification == "Não compressível":
        st.info("🔵 Não compressível")
    else:
        st.caption(f"⚪ {classification}")


def format_date_br(value):
    value = clean_value(value)
    if not value:
        return "Não informado"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def footer_datetime_text(d):
    date_text = format_date_br(d.get("data_avaliacao"))
    hour_text = display_value(d.get("horario"))
    if date_text == "Não informado" and hour_text == "Não informado":
        return "Avaliação realizada em: não informado"
    return f"Avaliação realizada em: {date_text} às {hour_text}"


def pdf_report(d):
    b = io.BytesIO()
    doc = SimpleDocTemplate(
        b,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.8 * cm,
    )
    styles = getSampleStyleSheet()
    # 6 pt corresponde ao padding esquerdo padrão das células das tabelas.
    # Assim, os títulos começam na mesma linha visual do texto dentro das caixas.
    styles["Heading2"].leftIndent = 6
    styles["Heading2"].firstLineIndent = 0
    styles["Heading2"].spaceBefore = 0
    styles["Heading2"].spaceAfter = 6
    body_aligned = ParagraphStyle(
        "BodyAligned",
        parent=styles["Normal"],
        leftIndent=6,
        firstLineIndent=0,
    )
    italic_aligned = ParagraphStyle(
        "ItalicAligned",
        parent=body_aligned,
        fontName="Helvetica-Oblique",
    )
    story = []

    header_path = Path("cabecalho_institucional.png")
    if header_path.exists():
        # Mantém a proporção da imagem institucional fornecida.
        story += [Image(str(header_path), width=17 * cm, height=2.6 * cm), Spacer(1, 0.15 * cm)]

    story += [
        Paragraph("ITB Clinical", styles["Title"]),
        Paragraph(
            "Triagem clínica considerando sintomas de claudicação e medida do "
            "Índice Tornozelo-Braquial (ITB)",
            styles["Normal"],
        ),
        Spacer(1, 0.35 * cm),
    ]

    sections = [
        (
            "Identificação",
            [
                ["Protocolo / estudo", display_value(d.get("protocolo"))],
                ["Nome do sujeito", display_value(d.get("nome_sujeito"))],
                ["Avaliador", display_value(d.get("avaliador"))],
                ["Data / horário", f"{format_date_br(d.get('data_avaliacao'))} — {display_value(d.get('horario'))}"],
            ],
        ),
        (
            "Avaliação de sintomas",
            [
                ["Sintomas ao caminhar", display_value(d.get("sintoma_caminhar"))],
                ["Local", display_value(d.get("local_sintoma"))],
                ["Melhora com repouso", display_value(d.get("melhora_repouso"))],
                ["Tempo para melhora", format_minutes(d.get("tempo_melhora"))],
                ["Dor em repouso", display_value(d.get("dor_repouso"))],
                ["Feridas/úlceras/gangrena/lesões", display_value(d.get("lesoes"))],
                ["Local da lesão", display_value(d.get("local_lesao"))],
                ["Achados de pele", display_value(d.get("achados_pele"))],
            ],
        ),
        (
            "Pulsos periféricos",
            [
                ["Pulso", "Direito", "Esquerdo"],
                ["Femoral", display_value(d.get("femoral_d")), display_value(d.get("femoral_e"))],
                ["Poplíteo", display_value(d.get("popliteo_d")), display_value(d.get("popliteo_e"))],
                ["Tibial posterior", display_value(d.get("tibial_pulso_d")), display_value(d.get("tibial_pulso_e"))],
                ["Pedioso", display_value(d.get("pedioso_pulso_d")), display_value(d.get("pedioso_pulso_e"))],
            ],
        ),
        (
            "Condições da aferição",
            [
                ["Método utilizado", display_value(d.get("metodo_medida"))],
                ["Repouso prévio", display_value(d.get("repouso_previo"))],
            ],
        ),
        (
            "Pressões",
            [
                ["Medida", "Direita", "Esquerda"],
                ["PAS braquial", format_measurement(d.get("braquial_direita")), format_measurement(d.get("braquial_esquerda"))],
                ["Artéria pediosa", format_measurement(d.get("pediosa_direita")), format_measurement(d.get("pediosa_esquerda"))],
                ["Tibial posterior", format_measurement(d.get("tibial_posterior_direita")), format_measurement(d.get("tibial_posterior_esquerda"))],
            ],
        ),
        (
            "Resultado",
            [
                ["Membro", "ITB", "Classificação"],
                [
                    "Direito",
                    "Não calculável" if clean_value(d.get("itb_direito")) is None else f"{float(d.get('itb_direito')):.2f}",
                    display_value(d.get("classificacao_direito")),
                ],
                [
                    "Esquerdo",
                    "Não calculável" if clean_value(d.get("itb_esquerdo")) is None else f"{float(d.get('itb_esquerdo')):.2f}",
                    display_value(d.get("classificacao_esquerdo")),
                ],
            ],
        ),
        (
            "Elegibilidade",
            [
                ["Sintomas atuais de claudicação", display_value(d.get("claudicacao_12m"))],
                ["ITB < 0,90", display_value(d.get("itb_menor_090"))],
            ],
        ),
    ]

    for title, rows in sections:
        story.append(Paragraph(title, styles["Heading2"]))
        if len(rows[0]) == 3:
            widths = [7 * cm, 5 * cm, 5 * cm]
        else:
            widths = [7 * cm, 10 * cm]
        table = Table(rows, colWidths=widths, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ]
            )
        )
        block = [Paragraph(title, styles["Heading2"]), table, Spacer(1, 0.28 * cm)]
        # Evita que o título ou parte da tabela de Resultado/Elegibilidade fique
        # isolado no final de uma página.
        if title in ("Resultado", "Elegibilidade"):
            # Remove o título que foi inserido acima e adiciona o bloco inteiro junto.
            story.pop()
            story.append(KeepTogether(block))
        else:
            story += [table, Spacer(1, 0.28 * cm)]

    story += [
        Paragraph("Observações", styles["Heading2"]),
        Paragraph(
            (display_value(d.get("observacoes")) if d.get("observacoes") else "Nenhuma observação registrada.").replace("\n", "<br/>"),
            body_aligned,
        ),
        # Espaço adicional para anotações manuais após as observações.
        Spacer(1, 1.35 * cm),
        Paragraph("Referência para cálculo e interpretação do ITB", styles["Heading2"]),
        Paragraph(
            "Cálculo e classificação do Índice Tornozelo-Braquial (ITB) realizados conforme "
            "os critérios da 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS "
            "Guideline for the Management of Lower Extremity Peripheral Artery Disease. "
            "Interpretação do ITB de repouso: ≤0,90 anormal; 0,91–0,99 limítrofe; "
            "1,00–1,40 normal; >1,40 não compressível.",
            italic_aligned,
        ),
        Spacer(1, 0.18 * cm),
        Paragraph(
            "<b>Observação:</b> Embora a classificação apresentada esteja fundamentada nas "
            "diretrizes vigentes, os critérios de interpretação do ITB podem variar conforme "
            "o protocolo do estudo. Para fins de elegibilidade, deverão prevalecer os critérios "
            "e pontos de corte definidos no protocolo específico da pesquisa.",
            italic_aligned,
        ),
        # Posiciona a área de assinatura mais abaixo, aproveitando o espaço da página.
        Spacer(1, 2.0 * cm),
        Paragraph("Assinatura do avaliador", styles["Heading2"]),
        Spacer(1, 0.9 * cm),
        Paragraph("_______________________________________________", styles["Normal"]),
        Paragraph(display_value(d.get("avaliador")), styles["Normal"]),
        Spacer(1, 0.45 * cm),
        Paragraph("Data: ____/____/________", styles["Normal"]),
        Spacer(1, 0.25 * cm),
    ]

    prototype_box = Table(
        [[Paragraph(
            "Protótipo destinado ao uso exclusivo por equipe qualificada de pesquisa clínica, "
            "como ferramenta de apoio à triagem clínica e à mensuração do "
            "Índice Tornozelo-Braquial (ITB).",
            styles["Normal"],
        )]],
        colWidths=[17 * cm],
        hAlign="LEFT",
    )
    prototype_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF3FB")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8D4EA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    # Empurra a caixa do protótipo para a parte inferior da última página.
    story.append(Spacer(1, 0.8 * cm))
    story.append(KeepTogether([prototype_box]))

    def add_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.grey)
        y = 0.75 * cm
        canvas.drawString(1.5 * cm, y, APP_VERSION)
        canvas.drawCentredString(A4[0] / 2, y, f"Página {doc_obj.page}")
        canvas.drawRightString(A4[0] - 1.5 * cm, y, footer_datetime_text(d))
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    b.seek(0)
    return b.getvalue()


def validate_form(
    protocolo,
    nome,
    avaliador,
    sint,
    locais,
    outro_local,
    melhora,
    tempo,
    dor,
    lesao,
    local_lesao,
    ach,
    outro_ach,
    pulses,
    metodo_medida,
    repouso_previo,
    pressure_statuses,
    claudicacao_12m,
    conflito,
):
    pending = []

    if not protocolo.strip():
        pending.append("Protocolo / estudo")
    if not nome.strip():
        pending.append("Nome do sujeito")
    if not avaliador.strip():
        pending.append("Avaliador")
    if sint is None:
        pending.append("Sintomas ao caminhar")
    if sint == "Sim" and not locais:
        pending.append("Local do sintoma")
    if "Outro" in locais and not outro_local.strip():
        pending.append("Especificação de outro local do sintoma")
    if sint == "Sim" and melhora is None:
        pending.append("Melhora com repouso")
    if melhora == "Sim" and tempo is None:
        pending.append("Tempo para melhora")
    if dor is None:
        pending.append("Dor em repouso")
    if lesao is None:
        pending.append("Feridas / úlceras / gangrena / lesões")
    if lesao == "Sim" and not local_lesao.strip():
        pending.append("Local da lesão")
    if not ach:
        pending.append("Achados de pele")
    if "Outro" in ach and not outro_ach.strip():
        pending.append("Especificação de outro achado de pele")
    if conflito:
        pending.append("Achados de pele: 'Normal' não pode coexistir com achados alterados")
    if any(p is None for p in pulses):
        pending.append("Todos os pulsos periféricos (se não avaliados, selecione 'Não avaliado')")
    if metodo_medida is None:
        pending.append("Método utilizado para aferição")
    if repouso_previo is None:
        pending.append("Repouso prévio")
    if not all(pressure_statuses):
        pending.append("Todas as pressões (preencha o valor ou marque 'Não avaliado')")
    if claudicacao_12m is None:
        pending.append("Sintomas atuais de claudicação")

    return pending


# Cabeçalho institucional
header_path = Path("cabecalho_institucional.png")
if header_path.exists():
    st.image(str(header_path), use_container_width=True)

st.title("ITB Clinical")
st.markdown(
    "**Triagem clínica considerando sintomas de claudicação e medida do "
    "Índice Tornozelo-Braquial (ITB)**"
)
st.info(
    "Protótipo destinado ao uso exclusivo por equipe qualificada de pesquisa clínica, "
    "como ferramenta de apoio à triagem clínica e à mensuração do "
    "Índice Tornozelo-Braquial (ITB)."
)

tab1, tab2 = st.tabs(["🫀 Nova avaliação", "📊 Banco de dados"])

with tab1:
    st.subheader("1. Identificação")
    protocolo = st.text_input(
        "Protocolo / estudo",
        placeholder="Ex.: ABC-123 ou nome do estudo",
    )
    nome = st.text_input("Nome do sujeito")
    avaliador = st.text_input("Avaliador")

    agora = now_br()
    c_data, c_hora = st.columns(2)
    with c_data:
        st.text_input(
            "Data da avaliação",
            value=agora.strftime("%d/%m/%Y"),
            disabled=True,
        )
    with c_hora:
        st.text_input(
            "Horário",
            value=agora.strftime("%H:%M:%S"),
            disabled=True,
        )
    st.caption(
        "A data e o horário são registrados automaticamente pelo sistema no momento do salvamento "
        "e não podem ser alterados manualmente."
    )

    st.subheader("2. Avaliação de sintomas")
    sint = st.radio(
        "O paciente apresenta dor, cansaço, peso, câimbra ou desconforto em membros inferiores ao caminhar?",
        ["Sim", "Não"],
        index=None,
        horizontal=True,
    )
    locais = st.multiselect(
        "Local do sintoma",
        ["Panturrilha", "Coxa", "Glúteo", "Pé", "Outro"],
    )
    outro_local = (
        st.text_input("Especifique outro local")
        if "Outro" in locais
        else ""
    )
    melhora = st.radio(
        "O sintoma melhora com repouso?",
        ["Sim", "Não"],
        index=None,
        horizontal=True,
    )
    tempo = (
        st.number_input(
            "Tempo para melhora (min)",
            min_value=0,
            value=None,
            step=1,
            format="%d",
        )
        if melhora == "Sim"
        else None
    )
    dor = st.radio(
        "Há dor em repouso?",
        ["Sim", "Não"],
        index=None,
        horizontal=True,
    )
    lesao = st.radio(
        "Há feridas, úlceras, gangrena ou lesões que não cicatrizam?",
        ["Sim", "Não"],
        index=None,
        horizontal=True,
    )
    local_lesao = (
        st.text_input("Local da lesão")
        if lesao == "Sim"
        else ""
    )
    ach = st.multiselect(
        "Achados de pele",
        [
            "Normal",
            "Palidez",
            "Cianose",
            "Rubor dependente",
            "Extremidade fria",
            "Rarefação de pelos",
            "Lesão/úlcera",
            "Outro",
        ],
    )
    outro_ach = (
        st.text_input("Especifique outro achado de pele")
        if "Outro" in ach
        else ""
    )
    conflito = "Normal" in ach and len(ach) > 1
    if conflito:
        st.warning(
            "“Normal” não pode ser selecionado junto com achados alterados."
        )

    st.subheader("3. Avaliação dos pulsos periféricos")
    fd = pulse("Femoral — Direito", "fd")
    fe = pulse("Femoral — Esquerdo", "fe")
    pop_d = pulse("Poplíteo — Direito", "pop_d")
    pop_e = pulse("Poplíteo — Esquerdo", "pop_e")
    td = pulse("Tibial posterior — Direito", "td")
    te = pulse("Tibial posterior — Esquerdo", "te")
    ped = pulse("Pedioso — Direito", "ped")
    pee = pulse("Pedioso — Esquerdo", "pee")

    st.subheader("4. Pressões sistólicas para cálculo do ITB (mmHg)")

    metodo_medida = st.radio(
        "Método utilizado:",
        ["Doppler portátil", "Oscilométrico"],
        index=None,
        horizontal=True,
    )
    repouso_previo = st.radio(
        "Repouso prévio:",
        ["Sim", "Não"],
        index=None,
        horizontal=True,
    )

    bd, bd_ok = pressure("PAS braquial direita", "bd")
    be, be_ok = pressure("PAS braquial esquerda", "be")
    pdd, pdd_ok = pressure("PAS artéria pediosa direita", "pdd")
    tpd, tpd_ok = pressure("PAS artéria tibial posterior direita", "tpd")
    pde, pde_ok = pressure("PAS artéria pediosa esquerda", "pde")
    tpe, tpe_ok = pressure("PAS artéria tibial posterior esquerda", "tpe")

    br = [x for x in [bd, be] if x is not None]
    rd = [x for x in [pdd, tpd] if x is not None]
    le = [x for x in [pde, tpe] if x is not None]
    den = max(br) if br else None

    itbd = max(rd) / den if den and rd else None
    itbe = max(le) / den if den and le else None
    cd = classify(itbd)
    ce = classify(itbe)

    st.subheader("5. Resultado")
    c1, c2 = st.columns(2)
    with c1:
        result_display("ITB direito", itbd, cd)
    with c2:
        result_display("ITB esquerdo", itbe, ce)

    st.subheader("6. Elegibilidade")
    claudicacao_12m = st.radio(
        "Sintomas atuais de claudicação:",
        ["Sim", "Não"],
        index=None,
        horizontal=True,
    )
    itb_lt_090 = eligibility_itb(itbd, itbe)
    st.text_input(
        "ITB < 0,90",
        value=itb_lt_090,
        disabled=True,
        help=(
            "Preenchimento automático. 'Sim' quando pelo menos um ITB calculável é "
            "estritamente menor que 0,90. Um ITB exatamente igual a 0,90 não marca este critério."
        ),
    )

    st.subheader("7. Observações")
    obs = st.text_area("Observações")

    pulses = [fd, fe, pop_d, pop_e, td, te, ped, pee]
    pressure_statuses = [bd_ok, be_ok, pdd_ok, tpd_ok, pde_ok, tpe_ok]

    pending = validate_form(
        protocolo,
        nome,
        avaliador,
        sint,
        locais,
        outro_local,
        melhora,
        tempo,
        dor,
        lesao,
        local_lesao,
        ach,
        outro_ach,
        pulses,
        metodo_medida,
        repouso_previo,
        pressure_statuses,
        claudicacao_12m,
        conflito,
    )

    if st.button("💾 Salvar avaliação", type="primary", width="stretch"):
        if pending:
            st.error(
                "Avaliação não salva. Preencha todos os campos obrigatórios antes de continuar."
            )
            st.markdown(
                "**Campos pendentes:**\n" + "\n".join(f"- {item}" for item in pending)
            )
        else:
            momento = now_br()
            rec = {
                "protocolo": protocolo.strip(),
                "nome_sujeito": nome.strip(),
                "avaliador": avaliador.strip(),
                "data_avaliacao": momento.strftime("%Y-%m-%d"),
                "horario": momento.strftime("%H:%M:%S"),
                "realizado_em": momento.isoformat(timespec="seconds"),
                "sintoma_caminhar": sint,
                "local_sintoma": ", ".join(locais),
                "outro_local_sintoma": outro_local.strip(),
                "melhora_repouso": melhora,
                "tempo_melhora": tempo,
                "dor_repouso": dor,
                "lesoes": lesao,
                "local_lesao": local_lesao.strip(),
                "achados_pele": ", ".join(ach),
                "outro_achado_pele": outro_ach.strip(),
                "femoral_d": fd,
                "femoral_e": fe,
                "popliteo_d": pop_d,
                "popliteo_e": pop_e,
                "tibial_pulso_d": td,
                "tibial_pulso_e": te,
                "pedioso_pulso_d": ped,
                "pedioso_pulso_e": pee,
                "metodo_medida": metodo_medida,
                "repouso_previo": repouso_previo,
                "braquial_direita": bd,
                "braquial_esquerda": be,
                "pediosa_direita": pdd,
                "pediosa_esquerda": pde,
                "tibial_posterior_direita": tpd,
                "tibial_posterior_esquerda": tpe,
                "itb_direito": itbd,
                "classificacao_direito": cd,
                "itb_esquerdo": itbe,
                "classificacao_esquerdo": ce,
                "claudicacao_12m": claudicacao_12m,
                "itb_menor_090": itb_lt_090,
                "observacoes": obs,
            }
            save_record(rec)
            st.session_state["last_saved_pdf"] = pdf_report(rec)
            safe_name = "".join(
                c for c in nome if c.isalnum() or c in " _-"
            ).strip().replace(" ", "_")
            st.session_state["last_saved_pdf_name"] = (
                f"ITB_Clinical_{safe_name or 'avaliacao'}_{momento.strftime('%Y-%m-%d')}.pdf"
            )
            st.success("Avaliação salva com data e horário registrados automaticamente.")

    if st.session_state.get("last_saved_pdf"):
        st.download_button(
            "📄 Baixar relatório PDF da avaliação salva",
            st.session_state["last_saved_pdf"],
            file_name=st.session_state.get(
                "last_saved_pdf_name",
                "ITB_Clinical_relatorio.pdf",
            ),
            mime="application/pdf",
            width="stretch",
        )


with tab2:
    st.subheader("Área administrativa")
    st.caption(
        "A visualização, a exportação e a segunda via dos relatórios são restritas ao administrador."
    )

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    try:
        admin_password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        admin_password = None

    # Para testes locais, permite criar uma senha temporária na própria sessão.
    # No Streamlit Cloud, a senha definitiva deve permanecer em Settings > Secrets.
    if not admin_password:
        admin_password = st.session_state.get("temporary_admin_password")

    if not admin_password:
        st.warning("A senha administrativa ainda não foi configurada.")
        st.caption(
            "Para testar localmente, crie uma senha temporária abaixo. "
            "Ela será válida somente enquanto esta sessão estiver aberta."
        )
        senha_nova = st.text_input(
            "Criar senha administrativa temporária",
            type="password",
            key="senha_admin_temporaria",
        )
        confirmar_senha = st.text_input(
            "Confirmar senha temporária",
            type="password",
            key="confirmar_senha_admin_temporaria",
        )

        if st.button(
            "Criar senha e entrar",
            type="primary",
            width="stretch",
        ):
            if len(senha_nova) < 8:
                st.error("A senha deve ter pelo menos 8 caracteres.")
            elif senha_nova != confirmar_senha:
                st.error("As duas senhas não coincidem.")
            else:
                st.session_state["temporary_admin_password"] = senha_nova
                st.session_state.admin_authenticated = True
                st.rerun()

    elif not st.session_state.admin_authenticated:
        senha_digitada = st.text_input(
            "Senha do administrador",
            type="password",
        )
        if st.button(
            "Entrar na área administrativa",
            type="primary",
            width="stretch",
        ):
            if senha_digitada == admin_password:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    else:
        st.success("Acesso administrativo ativo nesta sessão.")

        if st.button("Sair da área administrativa", width="stretch"):
            st.session_state.admin_authenticated = False
            st.rerun()

        st.subheader("Banco de dados")
        df = get_data()

        if df.empty:
            st.info("Nenhuma avaliação salva ainda.")
        else:
            df_export = organized_export_df(df)
            st.dataframe(
                df_export,
                use_container_width=True,
                hide_index=True,
            )

            csv = df_export.to_csv(index=False).encode("utf-8-sig")
            try:
                xlsx = excel_export(df)
                excel_error = None
            except Exception as exc:
                xlsx = None
                excel_error = str(exc)

            col_csv, col_xlsx = st.columns(2)
            with col_csv:
                st.download_button(
                    "📥 Exportar CSV organizado",
                    csv,
                    file_name="ITB_Clinical_banco_de_dados.csv",
                    mime="text/csv",
                    width="stretch",
                )
            with col_xlsx:
                if xlsx is not None:
                    st.download_button(
                        "📊 Exportar Excel organizado",
                        xlsx,
                        file_name="ITB_Clinical_banco_de_dados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                    )
                else:
                    st.error(
                        "Não foi possível gerar o Excel. Verifique se o pacote XlsxWriter está instalado."
                    )

            st.caption(
                "O CSV e o Excel usam cabeçalhos clínicos legíveis e ordem lógica. "
                "A exportação continua restrita à área administrativa."
            )

            st.divider()
            st.subheader("🖨️ Segunda via do relatório PDF")
            st.caption(
                "Selecione uma avaliação já salva para gerar novamente o relatório em PDF."
            )

            options = {}
            for _, row in df.iterrows():
                label = (
                    f'ID {row["id"]} — '
                    f'{clean_value(row.get("nome_sujeito")) or "Sem nome"} — '
                    f'{clean_value(row.get("data_avaliacao")) or ""} — '
                    f'{clean_value(row.get("protocolo")) or "Sem protocolo"}'
                )
                options[label] = row

            selected = st.selectbox(
                "Avaliação salva",
                list(options.keys()),
                key="segunda_via_select",
            )

            if selected:
                row = options[selected]
                record_pdf = row_to_record(row)
                pdf_second_copy = pdf_report(record_pdf)

                safe_name = str(
                    clean_value(row.get("nome_sujeito")) or "avaliacao"
                )
                safe_name = "".join(
                    c for c in safe_name if c.isalnum() or c in " _-"
                ).strip().replace(" ", "_")

                st.download_button(
                    "📄 Baixar segunda via em PDF",
                    pdf_second_copy,
                    file_name=(
                        f"ITB_Clinical_segunda_via_"
                        f"{safe_name or 'avaliacao'}_"
                        f"{clean_value(row.get('data_avaliacao')) or ''}.pdf"
                    ),
                    mime="application/pdf",
                    width="stretch",
                )


st.info(
    "📚 **Referência para cálculo e interpretação do ITB:** "
    "Cálculo e classificação do Índice Tornozelo-Braquial (ITB) realizados conforme "
    "os critérios da 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS "
    "Guideline for the Management of Lower Extremity Peripheral Artery Disease. "
    "Interpretação do ITB de repouso: ≤0,90 anormal; 0,91–0,99 limítrofe; "
    "1,00–1,40 normal; >1,40 não compressível."
)

st.warning(
    "⚠️ **Observação sobre protocolos específicos:** Embora a classificação apresentada "
    "esteja fundamentada nas diretrizes vigentes, os critérios de interpretação do ITB "
    "podem variar conforme o protocolo do estudo. Para fins de elegibilidade, deverão "
    "prevalecer os critérios e pontos de corte definidos no protocolo específico da pesquisa."
)

with st.expander("Classificação utilizada"):
    st.markdown(
        """| ITB | Classificação |
|---|---|
| ≤ 0,90 | Anormal |
| 0,91–0,99 | Limítrofe |
| 1,00–1,40 | Normal |
| > 1,40 | Não compressível |"""
    )
