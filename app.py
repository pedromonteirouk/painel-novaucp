import streamlit as st
import gspread
from datetime import datetime, date
from oauth2client.service_account import ServiceAccountCredentials
import os, json, base64

st.set_page_config(page_title="Painel Produção - Local Calc", layout="wide")

PIN_CORRETO = "9472"
if "acesso_autorizado" not in st.session_state:
    st.session_state.acesso_autorizado = False
if "tentou_entrar" not in st.session_state:
    st.session_state.tentou_entrar = False

if not st.session_state.acesso_autorizado:
    st.title("Acesso Restrito")
    pin = st.text_input("Introduz o código de acesso:", type="password")
    if st.button("Entrar"):
        st.session_state.tentou_entrar = True
        if pin == PIN_CORRETO:
            st.session_state.acesso_autorizado = True
            st.rerun()
    if st.session_state.tentou_entrar and not st.session_state.acesso_autorizado:
        st.error("Código incorreto. Tenta novamente.")
    st.stop()

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_json = base64.b64decode(os.environ["GOOGLE_CREDS_BASE64"]).decode()
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(creds_json), scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1-J2mqcgSaq3-2CFVwXHzOvUGvKdYr31v7UT8da3r_OU/edit"
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("NOVAUCP"):
        st.session_state.pagina = "NOVAUCP"
with col2:
    if st.button("CONGELADOS"):
        st.session_state.pagina = "CONGELADOS"
with col3:
    if st.button("MOLHOS"):
        st.session_state.pagina = "MOLHOS"
with col4:
    if st.button("PIC"):
        st.session_state.pagina = "PIC"

pagina_atual = st.session_state.get("pagina", "NOVAUCP")
worksheet = sheet.worksheet(pagina_atual)
rows = worksheet.get_all_values()
headers = rows[0]
data = [dict(zip(headers, row)) for row in rows[1:]]

st.title(f"Painel de Produção – {pagina_atual}")

produtos = sorted(
    set(
        str(item.get("Produto", "")).strip() for item in data
        if item.get("Produto", "").strip()))
produtos_opcoes = ["(Novo Produto)"] + produtos

col1, col2 = st.columns(2)
with col1:
    produto_escolhido = st.selectbox("Produto", produtos_opcoes)
    produto_novo = st.text_input(
        "Novo produto:", key="produto_input"
    ) if produto_escolhido == "(Novo Produto)" else produto_escolhido

ARMAZENS_FIXOS = ["UCP", "MAIORCA", "CLOUD"]
with col2:
    armazens = ARMAZENS_FIXOS if produto_escolhido == "(Novo Produto)" else sorted(
        set(item["ARMAZEM"] for item in data
            if item["Produto"] == produto_escolhido))
    armazem_escolhido = st.selectbox("Armazém", armazens)

registros_produto = [
    item for item in data if item.get("Produto", "").strip() == produto_novo
    and item.get("ARMAZEM", "").strip() == armazem_escolhido.strip()
]
lotes_existentes = list(
    set(item["LOTE"] for item in registros_produto if item.get("LOTE")))
lotes_opcoes = ["(Novo Lote)"] + sorted(lotes_existentes)
lote_escolhido = st.selectbox("Lote", lotes_opcoes)

registro = {}
if lote_escolhido != "(Novo Lote)":
    for item in reversed(data):
        if item.get("Produto") == produto_novo and item.get(
                "ARMAZEM") == armazem_escolhido and item.get(
                    "LOTE") == lote_escolhido:
            registro = item
            break

dias_semana = [
    "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"
]

st.subheader("Registos por Dia")
for dia in dias_semana:
    with st.expander(dia.capitalize()):
        col1, col2, col3 = st.columns(3)
        col1.text_input(f"{dia} - INÍCIO",
                        value=registro.get(f"{dia} - INÍCIO", ""),
                        key=f"{dia}_inicio")
        col2.text_input(f"{dia} - ENTRADA",
                        value=registro.get(f"{dia} - ENTRADA", ""),
                        key=f"{dia}_entrada")
        col3.text_input(f"{dia} - SAIDA",
                        value=registro.get(f"{dia} - FIM", ""),
                        key=f"{dia}_saida")

if st.button("Gravar alterações"):
    todas_colunas = worksheet.row_values(1)
    todas_linhas = worksheet.get_all_values()
    idx_lote = todas_colunas.index("LOTE")
    row_to_update = None
    for i, linha in enumerate(todas_linhas, start=2):
        if linha[idx_lote] == lote_escolhido:
            row_to_update = i
            break

    if row_to_update:
        saldo = None
        for idx, dia in enumerate(dias_semana):
            inicio = st.session_state.get(f"{dia}_inicio", "").strip()
            entrada = st.session_state.get(f"{dia}_entrada", "").strip()
            saida = st.session_state.get(f"{dia}_saida", "").strip()

            # Converte para inteiros ou 0 se vazio
            inicio = int(inicio) if inicio.isdigit() else 0 if inicio else (
                saldo if saldo is not None else 0)
            entrada = int(entrada) if entrada.isdigit() else 0
            saida = int(saida) if saida.isdigit() else 0

            saldo = inicio + entrada - saida

            # Grava valor calculado de Início no Sheets (sem fórmulas)
            col_inicio = ["H", "K", "N", "Q", "T", "W",
                          "Z"][idx]  # colunas SEG a DOM
            worksheet.update_acell(f"{col_inicio}{row_to_update}", saldo)

        # Atualiza STOCK como saldo final
        worksheet.update_acell(f"W{row_to_update}", saldo)
        st.success(
            f"Alterações gravadas e STOCK atualizado para {saldo} na linha {row_to_update}!"
        )
        st.rerun()
    else:
        st.error(f"Lote '{lote_escolhido}' não encontrado para atualização.")
