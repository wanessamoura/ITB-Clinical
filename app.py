
import io
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(
    page_title="ITB-Enf",
    page_icon="🫀",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB = Path("itb_enf.db")

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        avaliador TEXT,
        data_avaliacao TEXT,
        horario TEXT,
        equipamento_nome TEXT,
        equipamento_modelo TEXT,
        equipamento_patrimonio TEXT,
        manguito TEXT,
        braquial_direita REAL,
        braquial_esquerda REAL,
        pediosa_direita REAL,
        tibial_posterior_direita REAL,
        pediosa_esquerda REAL,
        tibial_posterior_esquerda REAL,
        itb_direito REAL,
        classificacao_direito TEXT,
        itb_esquerdo REAL,
        classificacao_esquerdo TEXT,
        observacoes TEXT
    )
    """)
    con.commit()
    con.close()

init_db()

def classify(abi):
    if abi <= 0.90:
        return "Anormal"
    if abi <= 0.99:
        return "Limítrofe"
    if abi <= 1.40:
        return "Normal"
    return "Não compressível"

def save_record(data):
    con = sqlite3.connect(DB)
    con.execute("""
    INSERT INTO avaliacoes (
        codigo, avaliador, data_avaliacao, horario,
        equipamento_nome, equipamento_modelo, equipamento_patrimonio, manguito,
        braquial_direita, braquial_esquerda,
        pediosa_direita, tibial_posterior_direita,
        pediosa_esquerda, tibial_posterior_esquerda,
        itb_direito, classificacao_direito, itb_esquerdo, classificacao_esquerdo,
        observacoes
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, tuple(data.values()))
    con.commit()
    con.close()

def get_data():
    con = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM avaliacoes ORDER BY id DESC", con)
    con.close()
    return df

def pdf_report(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ITB-Enf — Relatório de Avaliação", styles["Title"]),
        Spacer(1, 0.3*cm),
        Paragraph("Sistema de apoio à mensuração e interpretação do Índice Tornozelo-Braquial", styles["Normal"]),
        Spacer(1, 0.5*cm),
    ]

    info = [
        ["Código", data["codigo"] or "Não informado"],
        ["Avaliador", data["avaliador"] or "Não informado"],
        ["Data / horário", f'{data["data_avaliacao"]} {data["horario"]}'],
        ["Equipamento", data["equipamento_nome"] or "Não informado"],
        ["Modelo", data["equipamento_modelo"] or "Não informado"],
        ["Patrimônio/ID", data["equipamento_patrimonio"] or "Não informado"],
        ["Manguito", data["manguito"] or "Não informado"],
    ]
    t = Table(info, colWidths=[4*cm, 13*cm])
    t.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
    ]))
    story += [t, Spacer(1, 0.5*cm)]

    press = [
        ["Medida", "Direita (mmHg)", "Esquerda (mmHg)"],
        ["PAS braquial", data["braquial_direita"], data["braquial_esquerda"]],
        ["Artéria pediosa", data["pediosa_direita"], data["pediosa_esquerda"]],
        ["Artéria tibial posterior", data["tibial_posterior_direita"], data["tibial_posterior_esquerda"]],
    ]
    t2 = Table(press, colWidths=[8*cm, 4.5*cm, 4.5*cm])
    t2.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(1,1),(-1,-1),"CENTER"),
    ]))
    story += [
        Paragraph("Pressões registradas", styles["Heading2"]),
        t2, Spacer(1, 0.5*cm)
    ]

    result = [
        ["Membro", "ITB", "Classificação"],
        ["Direito", f'{data["itb_direito"]:.2f}', data["classificacao_direito"]],
        ["Esquerdo", f'{data["itb_esquerdo"]:.2f}', data["classificacao_esquerdo"]],
    ]
    t3 = Table(result, colWidths=[6*cm, 5*cm, 6*cm])
    t3.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(1,1),(-1,-1),"CENTER"),
    ]))
    story += [
        Paragraph("Resultado", styles["Heading2"]),
        t3, Spacer(1, 0.5*cm),
        Paragraph("Observações", styles["Heading2"]),
        Paragraph((data["observacoes"] or "Nenhuma observação registrada.").replace("\n","<br/>"), styles["Normal"]),
        Spacer(1, 0.5*cm),
        Paragraph(
            "Nota: ferramenta de apoio ao registro e cálculo. A interpretação deve considerar avaliação clínica, "
            "treinamento do profissional e protocolo institucional. Classificação apresentada conforme referência adotada no projeto.",
            styles["Italic"]
        )
    ]
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

st.title("ITB-Enf")
st.caption("Mensuração, cálculo, registro e relatório do Índice Tornozelo-Braquial")

st.info("Protótipo acadêmico. Não substitui avaliação clínica, treinamento profissional ou protocolo institucional.")

tab1, tab2 = st.tabs(["🫀 Nova avaliação", "📊 Banco de dados"])

with tab1:
    st.subheader("1. Identificação")
    codigo = st.text_input("Código do participante")
    avaliador = st.text_input("Avaliador")
    d = st.date_input("Data", datetime.now().date())
    h = st.time_input("Horário", datetime.now().time())

    st.subheader("2. Equipamento utilizado")
    equipamento_nome = st.text_input("Equipamento / fabricante")
    equipamento_modelo = st.text_input("Modelo")
    equipamento_patrimonio = st.text_input("Patrimônio / identificação do equipamento")
    manguito = st.text_input("Manguito utilizado (tamanho / identificação)")

    st.subheader("3. Pressões sistólicas (mmHg)")
    st.caption("Em telas pequenas, os campos aparecem em sequência para facilitar o preenchimento no celular.")

    braquial_direita = st.number_input("PAS braquial direita", 0, 300, 120, 1)
    braquial_esquerda = st.number_input("PAS braquial esquerda", 0, 300, 120, 1)
    pediosa_direita = st.number_input("PAS artéria pediosa direita", 0, 300, 100, 1)
    tibial_posterior_direita = st.number_input("PAS tibial posterior direita", 0, 300, 100, 1)
    pediosa_esquerda = st.number_input("PAS artéria pediosa esquerda", 0, 300, 100, 1)
    tibial_posterior_esquerda = st.number_input("PAS tibial posterior esquerda", 0, 300, 100, 1)

    braquial_max = max(braquial_direita, braquial_esquerda)
    ankle_right = max(pediosa_direita, tibial_posterior_direita)
    ankle_left = max(pediosa_esquerda, tibial_posterior_esquerda)

    if braquial_max > 0:
        itb_direito = ankle_right / braquial_max
        itb_esquerdo = ankle_left / braquial_max
        class_direito = classify(itb_direito)
        class_esquerdo = classify(itb_esquerdo)

        st.subheader("4. Resultado")
        st.metric("ITB direito", f"{itb_direito:.2f}", class_direito)
        st.metric("ITB esquerdo", f"{itb_esquerdo:.2f}", class_esquerdo)

        st.subheader("5. Observações")
        observacoes = st.text_area("Observações da avaliação")

        data = {
            "codigo": codigo, "avaliador": avaliador,
            "data_avaliacao": str(d), "horario": str(h),
            "equipamento_nome": equipamento_nome,
            "equipamento_modelo": equipamento_modelo,
            "equipamento_patrimonio": equipamento_patrimonio,
            "manguito": manguito,
            "braquial_direita": braquial_direita,
            "braquial_esquerda": braquial_esquerda,
            "pediosa_direita": pediosa_direita,
            "tibial_posterior_direita": tibial_posterior_direita,
            "pediosa_esquerda": pediosa_esquerda,
            "tibial_posterior_esquerda": tibial_posterior_esquerda,
            "itb_direito": itb_direito,
            "classificacao_direito": class_direito,
            "itb_esquerdo": itb_esquerdo,
            "classificacao_esquerdo": class_esquerdo,
            "observacoes": observacoes,
        }

        if st.button("💾 Salvar avaliação", type="primary", width="stretch"):
            save_record(data)
            st.success("Avaliação salva no banco de dados local.")

        if st.button("📄 Gerar relatório PDF", width="stretch"):
            pdf = pdf_report(data)
            st.download_button(
                "Baixar relatório PDF",
                pdf,
                file_name=f"ITB-Enf_{codigo or 'avaliacao'}_{d}.pdf",
                mime="application/pdf",
                width="stretch"
            )

with tab2:
    st.subheader("Banco de dados")
    df = get_data()
    if df.empty:
        st.info("Nenhuma avaliação salva ainda.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Exportar banco de dados CSV",
            csv,
            file_name="ITB-Enf_banco_de_dados.csv",
            mime="text/csv",
            width="stretch"
        )
        st.caption("O banco local utiliza SQLite. O CSV pode ser aberto no Excel e utilizado posteriormente para análise estatística.")

with st.expander("Classificação utilizada"):
    st.markdown("""
    | ITB | Classificação |
    |---|---|
    | ≤ 0,90 | Anormal |
    | 0,91–0,99 | Limítrofe |
    | 1,00–1,40 | Normal |
    | > 1,40 | Não compressível |
    """)
