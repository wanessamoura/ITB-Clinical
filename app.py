import io
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
import xlsxwriter
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

st.set_page_config(page_title="ITB Clinical", page_icon="🫀", layout="centered", initial_sidebar_state="collapsed")
DB = Path("itb_clinical.db")

FIELDS = [
("instituicao","TEXT"),("protocolo","TEXT"),("nome_sujeito","TEXT"),("avaliador","TEXT"),("data_avaliacao","TEXT"),("horario","TEXT"),
("sintoma_caminhar","TEXT"),("local_sintoma","TEXT"),("outro_local_sintoma","TEXT"),
("melhora_repouso","TEXT"),("tempo_melhora","REAL"),("dor_repouso","TEXT"),("lesoes","TEXT"),
("local_lesao","TEXT"),("achados_pele","TEXT"),("outro_achado_pele","TEXT"),
("femoral_d","TEXT"),("femoral_e","TEXT"),("popliteo_d","TEXT"),("popliteo_e","TEXT"),
("tibial_pulso_d","TEXT"),("tibial_pulso_e","TEXT"),("pedioso_pulso_d","TEXT"),("pedioso_pulso_e","TEXT"),
("braquial_direita","REAL"),("braquial_esquerda","REAL"),("pediosa_direita","REAL"),
("tibial_posterior_direita","REAL"),("pediosa_esquerda","REAL"),("tibial_posterior_esquerda","REAL"),
("itb_direito","REAL"),("classificacao_direito","TEXT"),("itb_esquerdo","REAL"),
("classificacao_esquerdo","TEXT"),("observacoes","TEXT")]

def init_db():
    con = sqlite3.connect(DB)
    cols = ", ".join(f"{n} {t}" for n, t in FIELDS)
    con.execute(f"CREATE TABLE IF NOT EXISTS avaliacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols})")

    # Migração simples: adiciona automaticamente novos campos quando uma versão
    # anterior do banco já existe na mesma pasta.
    existing = {row[1] for row in con.execute("PRAGMA table_info(avaliacoes)").fetchall()}
    for name, col_type in FIELDS:
        if name not in existing:
            con.execute(f"ALTER TABLE avaliacoes ADD COLUMN {name} {col_type}")

    con.commit()
    con.close()
init_db()

def classify(x):
    if x is None: return "Não calculável"
    if x <= .90: return "Anormal"
    if x <= .99: return "Limítrofe"
    if x <= 1.40: return "Normal"
    return "Não compressível"

def save_record(data):
    con=sqlite3.connect(DB); cols=list(data)
    con.execute(f"INSERT INTO avaliacoes ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", tuple(data[c] for c in cols))
    con.commit(); con.close()

def get_data():
    con=sqlite3.connect(DB); df=pd.read_sql_query("SELECT * FROM avaliacoes ORDER BY id DESC",con); con.close(); return df

def row_to_record(row):
    return {name: row[name] if name in row.index else None for name, _ in FIELDS}


EXPORT_COLUMNS = [
    "id",
    "instituicao", "protocolo", "nome_sujeito", "avaliador", "data_avaliacao", "horario",
    "sintoma_caminhar", "local_sintoma", "outro_local_sintoma",
    "melhora_repouso", "tempo_melhora", "dor_repouso", "lesoes", "local_lesao",
    "achados_pele", "outro_achado_pele",
    "femoral_d", "femoral_e", "popliteo_d", "popliteo_e",
    "tibial_pulso_d", "tibial_pulso_e", "pedioso_pulso_d", "pedioso_pulso_e",
    "braquial_direita", "braquial_esquerda",
    "pediosa_direita", "pediosa_esquerda",
    "tibial_posterior_direita", "tibial_posterior_esquerda",
    "itb_direito", "classificacao_direito", "itb_esquerdo", "classificacao_esquerdo",
    "observacoes",
]

EXPORT_LABELS = {
    "id": "ID",
    "instituicao": "Instituição / hospital",
    "protocolo": "Protocolo / estudo",
    "nome_sujeito": "Nome do sujeito",
    "avaliador": "Avaliador",
    "data_avaliacao": "Data da visita",
    "horario": "Horário",
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
    "observacoes": "Observações",
}

EXPORT_GROUPS = [
    ("Identificação", 0, 6),
    ("Sintomas e avaliação clínica", 7, 16),
    ("Pulsos periféricos", 17, 24),
    ("Pressões sistólicas", 25, 30),
    ("Resultado do ITB", 31, 34),
    ("Observações", 35, 35),
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
            "bold": True, "align": "center", "valign": "vcenter",
            "bg_color": "#17365D", "font_color": "#FFFFFF",
            "border": 1
        })
        fmt_header = workbook.add_format({
            "bold": True, "align": "center", "valign": "vcenter",
            "bg_color": "#D9EAF7", "font_color": "#17365D",
            "border": 1, "text_wrap": True
        })
        fmt_text = workbook.add_format({
            "valign": "top", "border": 1, "text_wrap": True
        })
        fmt_center = workbook.add_format({
            "align": "center", "valign": "vcenter", "border": 1
        })
        fmt_itb = workbook.add_format({
            "align": "center", "valign": "vcenter", "border": 1,
            "num_format": "0.00"
        })

        # Faixas de grupos
        for title, start_col, end_col in EXPORT_GROUPS:
            if start_col >= len(export_df.columns):
                continue
            end_col = min(end_col, len(export_df.columns) - 1)
            if start_col == end_col:
                worksheet.write(0, start_col, title, fmt_group)
            else:
                worksheet.merge_range(0, start_col, 0, end_col, title, fmt_group)

        # Cabeçalhos
        for col_idx, col_name in enumerate(export_df.columns):
            worksheet.write(2, col_idx, col_name, fmt_header)

        # Formatação geral
        worksheet.freeze_panes(3, 4)
        worksheet.autofilter(2, 0, 2 + len(export_df), len(export_df.columns) - 1)
        worksheet.set_row(0, 24)
        worksheet.set_row(1, 6)
        worksheet.set_row(2, 42)

        # Larguras por coluna, limitadas para manter legibilidade
        widths = {
            "ID": 8,
            "Instituição / hospital": 24,
            "Protocolo / estudo": 20,
            "Nome do sujeito": 24,
            "Avaliador": 22,
            "Data da visita": 13,
            "Horário": 11,
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
            "Observações": 36,
        }

        for i, col_name in enumerate(export_df.columns):
            worksheet.set_column(i, i, widths.get(col_name, 18), fmt_text)

        # Centralização de campos curtos
        center_names = {
            "ID", "Data da visita", "Horário", "Sintomas ao caminhar",
            "Melhora com repouso", "Dor em repouso",
            "Classificação — Direito", "Classificação — Esquerdo"
        }
        for i, col_name in enumerate(export_df.columns):
            if col_name in center_names:
                worksheet.set_column(i, i, widths.get(col_name, 18), fmt_center)
            if col_name in {"ITB — Direito", "ITB — Esquerdo"}:
                worksheet.set_column(i, i, widths.get(col_name, 13), fmt_itb)

        worksheet.hide_gridlines(2)

    output.seek(0)
    return output.getvalue()


def val(v): return "Não avaliado" if v is None else str(v)

def pressure(label,key):
    na=st.checkbox(f"Não avaliado — {label}",key=key+"_na")
    if na: return None
    return st.number_input(label,min_value=1,max_value=300,value=None,step=1,key=key,placeholder="Digite a PAS em mmHg")

def pulse(label,key):
    return st.selectbox(label,["Não avaliado","Normal","Reduzido","Ausente"],key=key)

def pdf_report(d):
    b=io.BytesIO(); doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=1.5*cm,leftMargin=1.5*cm,topMargin=1.5*cm,bottomMargin=1.5*cm)
    s=getSampleStyleSheet()
    story=[]
    logo_path = Path("itb_clinical_header.png")
    if logo_path.exists():
        img = Image(str(logo_path), width=17*cm, height=5.95*cm)
        story += [img, Spacer(1,.25*cm)]
    else:
        story += [Paragraph("ITB Clinical — Relatório",s["Title"]),
                  Paragraph("Triagem clínica considerando sintomas de claudicação e medida do Índice Tornozelo-Braquial (ITB)",s["Normal"]),
                  Spacer(1,.4*cm)]
    sections=[
      ("Identificação",[["Instituição / hospital",d["instituicao"] or "Não informado"],["Protocolo / estudo",d["protocolo"] or "Não informado"],["Nome do sujeito",d["nome_sujeito"] or "Não informado"],["Avaliador",d["avaliador"] or "Não informado"],["Data / horário",d["data_avaliacao"]+" "+d["horario"]]]),
      ("Avaliação de sintomas",[["Sintomas ao caminhar",d["sintoma_caminhar"]],["Local",d["local_sintoma"] or "Não informado"],["Melhora com repouso",d["melhora_repouso"]],["Tempo para melhora (min)",val(d["tempo_melhora"])],["Dor em repouso",d["dor_repouso"]],["Feridas/úlceras/gangrena/lesões",d["lesoes"]],["Local da lesão",d["local_lesao"] or "Não informado"],["Achados de pele",d["achados_pele"] or "Não informado"]]),
      ("Pulsos periféricos",[["Pulso","Direito","Esquerdo"],["Femoral",d["femoral_d"],d["femoral_e"]],["Poplíteo",d["popliteo_d"],d["popliteo_e"]],["Tibial posterior",d["tibial_pulso_d"],d["tibial_pulso_e"]],["Pedioso",d["pedioso_pulso_d"],d["pedioso_pulso_e"]]]),
      ("Pressões",[["Medida","Direita","Esquerda"],["PAS braquial",val(d["braquial_direita"]),val(d["braquial_esquerda"])],["Artéria pediosa",val(d["pediosa_direita"]),val(d["pediosa_esquerda"])],["Tibial posterior",val(d["tibial_posterior_direita"]),val(d["tibial_posterior_esquerda"])]]),
      ("Resultado",[["Membro","ITB","Classificação"],["Direito","Não calculável" if d["itb_direito"] is None else f'{d["itb_direito"]:.2f}',d["classificacao_direito"]],["Esquerdo","Não calculável" if d["itb_esquerdo"] is None else f'{d["itb_esquerdo"]:.2f}',d["classificacao_esquerdo"]]])]
    for title,rows in sections:
        story += [Paragraph(title,s["Heading2"])]
        t=Table(rows,colWidths=[7*cm]+([5*cm,5*cm] if len(rows[0])==3 else [10*cm]))
        t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story += [t,Spacer(1,.3*cm)]
    story += [
        Paragraph("Observações", s["Heading2"]),
        Paragraph((d["observacoes"] or "Nenhuma observação registrada.").replace("\n","<br/>"), s["Normal"]),
        Spacer(1, 0.5*cm),
        Paragraph("Referência para cálculo e interpretação do ITB", s["Heading2"]),
        Paragraph(
            "Cálculo e classificação do Índice Tornozelo-Braquial (ITB) realizados conforme os critérios da 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS Guideline for the Management of Lower Extremity Peripheral Artery Disease. Interpretação do ITB de repouso: ≤0,90 anormal; 0,91–0,99 limítrofe; 1,00–1,40 normal; >1,40 não compressível.",
            s["Normal"]
        ),
        Spacer(1, 1.2*cm),
        Paragraph("Assinatura do avaliador", s["Heading2"]),
        Spacer(1, 1.0*cm),
        Paragraph("_______________________________________________", s["Normal"]),
        Paragraph(d["avaliador"] or "Nome do avaliador", s["Normal"]),
        Spacer(1, 0.5*cm),
        Paragraph("Data: ____/____/________", s["Normal"]),
        Spacer(1, 0.6*cm),
        Paragraph(
            "Protótipo destinado ao uso exclusivo por equipe qualificada de pesquisa clínica, "
            "como ferramenta de apoio à triagem clínica e à mensuração do Índice Tornozelo-Braquial (ITB).",
            s["Italic"]
        )
    ]
    doc.build(story); b.seek(0); return b.getvalue()

st.image("itb_clinical_header.png", use_container_width=True)

tab1,tab2=st.tabs(["🫀 Nova avaliação","📊 Banco de dados"])

with tab1:
    st.subheader("1. Identificação")
    instituicao=st.text_input("Instituição / hospital", placeholder="Ex.: Hospital X")
    protocolo=st.text_input("Protocolo / estudo", placeholder="Ex.: ABC-123 ou nome do estudo")
    nome=st.text_input("Nome do sujeito"); avaliador=st.text_input("Avaliador")
    data=st.date_input("Data da visita",datetime.now().date()); hora=st.time_input("Horário",datetime.now().time())

    st.subheader("2. Avaliação de sintomas")
    sint=st.radio("O paciente apresenta dor, cansaço, peso, câimbra ou desconforto em membros inferiores ao caminhar?",["Não avaliado","Sim","Não"],horizontal=True)
    locais=st.multiselect("Local do sintoma",["Panturrilha","Coxa","Glúteo","Pé","Outro"])
    outro_local=st.text_input("Especifique outro local") if "Outro" in locais else ""
    melhora=st.radio("O sintoma melhora com repouso?",["Não avaliado","Sim","Não"],horizontal=True)
    tempo=st.number_input("Tempo para melhora (min)",min_value=0.0,value=None,step=.5) if melhora=="Sim" else None
    dor=st.radio("Há dor em repouso?",["Não avaliado","Sim","Não"],horizontal=True)
    lesao=st.radio("Há feridas, úlceras, gangrena ou lesões que não cicatrizam?",["Não avaliado","Sim","Não"],horizontal=True)
    local_lesao=st.text_input("Local da lesão") if lesao=="Sim" else ""
    ach=st.multiselect("Achados de pele",["Normal","Palidez","Cianose","Rubor dependente","Extremidade fria","Rarefação de pelos","Lesão/úlcera","Outro"])
    outro_ach=st.text_input("Especifique outro achado de pele") if "Outro" in ach else ""
    conflito="Normal" in ach and len(ach)>1
    if conflito: st.warning('“Normal” não pode ser selecionado junto com achados alterados.')

    st.subheader("3. Avaliação dos pulsos periféricos")
    fd=pulse("Femoral — Direito","fd"); fe=pulse("Femoral — Esquerdo","fe")
    pop_d=pulse("Poplíteo — Direito","pop_d"); pop_e=pulse("Poplíteo — Esquerdo","pop_e")
    td=pulse("Tibial posterior — Direito","td"); te=pulse("Tibial posterior — Esquerdo","te")
    ped=pulse("Pedioso — Direito","ped"); pee=pulse("Pedioso — Esquerdo","pee")

    st.subheader("4. Pressões sistólicas para cálculo do ITB (mmHg)")
    bd=pressure("PAS braquial direita","bd"); be=pressure("PAS braquial esquerda","be")
    pdd=pressure("PAS artéria pediosa direita","pdd"); tpd=pressure("PAS artéria tibial posterior direita","tpd")
    pde=pressure("PAS artéria pediosa esquerda","pde"); tpe=pressure("PAS artéria tibial posterior esquerda","tpe")
    br=[x for x in [bd,be] if x is not None]; rd=[x for x in [pdd,tpd] if x is not None]; le=[x for x in [pde,tpe] if x is not None]
    den=max(br) if br else None
    itbd=max(rd)/den if den and rd else None; itbe=max(le)/den if den and le else None
    cd=classify(itbd); ce=classify(itbe)

    st.subheader("5. Resultado")
    st.metric("ITB direito","Não calculável" if itbd is None else f"{itbd:.2f}",cd)
    st.metric("ITB esquerdo","Não calculável" if itbe is None else f"{itbe:.2f}",ce)
    st.subheader("6. Observações"); obs=st.text_area("Observações")

    rec={"instituicao":instituicao,"protocolo":protocolo,"nome_sujeito":nome,"avaliador":avaliador,"data_avaliacao":str(data),"horario":str(hora),"sintoma_caminhar":sint,"local_sintoma":", ".join(locais),"outro_local_sintoma":outro_local,"melhora_repouso":melhora,"tempo_melhora":tempo,"dor_repouso":dor,"lesoes":lesao,"local_lesao":local_lesao,"achados_pele":", ".join(ach),"outro_achado_pele":outro_ach,"femoral_d":fd,"femoral_e":fe,"popliteo_d":pop_d,"popliteo_e":pop_e,"tibial_pulso_d":td,"tibial_pulso_e":te,"pedioso_pulso_d":ped,"pedioso_pulso_e":pee,"braquial_direita":bd,"braquial_esquerda":be,"pediosa_direita":pdd,"tibial_posterior_direita":tpd,"pediosa_esquerda":pde,"tibial_posterior_esquerda":tpe,"itb_direito":itbd,"classificacao_direito":cd,"itb_esquerdo":itbe,"classificacao_esquerdo":ce,"observacoes":obs}
    if st.button("💾 Salvar avaliação",type="primary",width="stretch"):
        if conflito: st.error("Corrija os achados de pele antes de salvar.")
        else: save_record(rec); st.success("Avaliação salva.")
    if st.button("📄 Gerar relatório PDF",width="stretch"):
        if conflito: st.error("Corrija os achados de pele antes de gerar o relatório.")
        else:
            pdf=pdf_report(rec)
            st.download_button("Baixar relatório PDF",pdf,file_name=f"ITB_Clinical_{data}.pdf",mime="application/pdf",width="stretch")

with tab2:
    st.subheader("Área administrativa")
    st.caption("A visualização e a exportação do banco de dados são restritas ao administrador.")

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    try:
        admin_password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        admin_password = None

    # Para testes locais, permite criar uma senha temporária na própria sessão.
    # No Streamlit Cloud, a senha definitiva deve continuar em Settings > Secrets.
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
            key="senha_admin_temporaria"
        )
        confirmar_senha = st.text_input(
            "Confirmar senha temporária",
            type="password",
            key="confirmar_senha_admin_temporaria"
        )

        if st.button("Criar senha e entrar", type="primary", width="stretch"):
            if len(senha_nova) < 8:
                st.error("A senha deve ter pelo menos 8 caracteres.")
            elif senha_nova != confirmar_senha:
                st.error("As duas senhas não coincidem.")
            else:
                st.session_state["temporary_admin_password"] = senha_nova
                st.session_state.admin_authenticated = True
                st.rerun()

    elif not st.session_state.admin_authenticated:
        senha_digitada = st.text_input("Senha do administrador", type="password")
        if st.button("Entrar na área administrativa", type="primary", width="stretch"):
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
            st.dataframe(df_export, use_container_width=True, hide_index=True)

            csv = df_export.to_csv(index=False).encode("utf-8-sig")
            xlsx = excel_export(df)

            col_csv, col_xlsx = st.columns(2)
            with col_csv:
                st.download_button(
                    "📥 Exportar CSV organizado",
                    csv,
                    file_name="ITB_Clinical_banco_de_dados.csv",
                    mime="text/csv",
                    width="stretch"
                )
            with col_xlsx:
                st.download_button(
                    "📊 Exportar Excel organizado",
                    xlsx,
                    file_name="ITB_Clinical_banco_de_dados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )

            st.caption(
                "O CSV e o Excel usam cabeçalhos clínicos legíveis e uma ordem lógica: "
                "identificação, sintomas, pulsos, pressões, resultados e observações. "
                "A exportação continua restrita à área administrativa."
            )

            st.divider()
            st.subheader("🖨️ Segunda via do relatório PDF")
            st.caption(
                "Selecione uma avaliação já salva para gerar novamente o relatório em PDF."
            )

            opcoes = {}
            for _, row in df.iterrows():
                rotulo = (
                    f'ID {row["id"]} — '
                    f'{row.get("nome_sujeito", "Sem nome")} — '
                    f'{row.get("data_avaliacao", "")} — '
                    f'{row.get("protocolo", "") or "Sem protocolo"}'
                )
                opcoes[rotulo] = row

            selecionada = st.selectbox(
                "Avaliação salva",
                list(opcoes.keys()),
                key="segunda_via_select"
            )

            if selecionada:
                row = opcoes[selecionada]
                registro_pdf = row_to_record(row)
                pdf_segunda_via = pdf_report(registro_pdf)

                nome_seguro = str(row.get("nome_sujeito", "avaliacao"))
                nome_seguro = "".join(
                    c for c in nome_seguro if c.isalnum() or c in " _-"
                ).strip().replace(" ", "_")

                st.download_button(
                    "📄 Baixar segunda via em PDF",
                    pdf_segunda_via,
                    file_name=(
                        f'ITB_Clinical_segunda_via_'
                        f'{nome_seguro or "avaliacao"}_'
                        f'{row.get("data_avaliacao", "")}.pdf'
                    ),
                    mime="application/pdf",
                    width="stretch"
                )


st.info(
    """📚 **Referência para cálculo e interpretação do ITB:** Cálculo e classificação do Índice Tornozelo-Braquial (ITB) realizados conforme os critérios da 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS Guideline for the Management of Lower Extremity Peripheral Artery Disease. Interpretação do ITB de repouso: ≤0,90 anormal; 0,91–0,99 limítrofe; 1,00–1,40 normal; >1,40 não compressível."""
)

with st.expander("Classificação utilizada"):
    st.markdown("""| ITB | Classificação |
|---|---|
| ≤ 0,90 | Anormal |
| 0,91–0,99 | Limítrofe |
| 1,00–1,40 | Normal |
| > 1,40 | Não compressível |""")
