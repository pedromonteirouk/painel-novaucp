import streamlit as st
import gspread
from datetime import datetime, date
from oauth2client.service_account import ServiceAccountCredentials
import os, json, base64

# ===== CONFIGURACAO INICIAL =====
st.set_page_config(page_title="Painel Multi-Páginas", layout="wide")
PIN_CORRETO = "9472"

if "acesso_autorizado" not in st.session_state:
    st.session_state.acesso_autorizado = False
if "tentou_entrar" not in st.session_state:
    st.session_state.tentou_entrar = False

if not st.session_state.acesso_autorizado:
    st.title("🔐 Acesso Restrito")
    pin = st.text_input("Introduz o código de acesso:", type="password")
    if st.button("Entrar"):
        st.session_state.tentou_entrar = True
        if pin == PIN_CORRETO:
            st.session_state.acesso_autorizado = True
            st.rerun()
    if st.session_state.tentou_entrar and not st.session_state.acesso_autorizado:
        st.error("❌ Código incorreto. Tenta novamente.")
    st.stop()

# ===== SELECAO DE PAGINA =====
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
st.title(f"📊 Painel de Produção – {pagina_atual}")

# ===== CREDENCIAIS GOOGLE SHEETS =====
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
worksheet = sheet.worksheet(pagina_atual)
rows = worksheet.get_all_values()
headers = rows[0]
data = [dict(zip(headers, row)) for row in rows[1:]]

# ===== PRODUTOS E ARMAZEM =====
produtos = sorted(
    set(
        str(item.get("Produto", "")).strip() for item in data
        if item.get("Produto", "").strip()))
produtos_opcoes = ["(Novo Produto)"] + produtos

col1, col2 = st.columns(2)
with col1:
    produto_escolhido = st.selectbox("🫒 Produto", produtos_opcoes)
    produto_novo = st.text_input(
        "✏️ Novo produto:", key="produto_input"
    ) if produto_escolhido == "(Novo Produto)" else produto_escolhido

ARMAZENS_FIXOS = ["UCP", "MAIORCA", "CLOUD"]
with col2:
    armazens = ARMAZENS_FIXOS if produto_escolhido == "(Novo Produto)" else sorted(
        set(item["ARMAZEM"] for item in data
            if item["Produto"] == produto_escolhido))
    armazem_escolhido = st.selectbox("🏢 Armazém", armazens)

registros_produto = [
    item for item in data if item.get("Produto", "").strip() == produto_novo
    and item.get("ARMAZEM", "").strip() == armazem_escolhido.strip()
]
lotes_existentes = list(
    set(item["LOTE"] for item in registros_produto if item.get("LOTE")))
lotes_opcoes = ["(Novo Lote)"] + sorted(lotes_existentes)
lote_escolhido = st.selectbox("📦 Lote", lotes_opcoes)

registro = {}
if lote_escolhido != "(Novo Lote)":
    for item in reversed(data):
        if item.get("Produto") == produto_novo and item.get(
                "ARMAZEM") == armazem_escolhido and item.get(
                    "LOTE") == lote_escolhido:
            registro = item
            break

valor_a1 = worksheet.acell("AG1").value or ""
data_semana = st.text_input("🗓️ Data / Semana",
                            value=valor_a1,
                            key="semana_input")
if st.button("📂 Atualizar Data / Semana"):
    worksheet.update_acell("AG1", data_semana)
    st.success("✔️ Data / Semana atualizada!")
    st.rerun()

st.markdown("---")

# ===== DADOS DO LOTE =====
st.subheader("📋 Dados do Lote")
col1, col2, col3, col4 = st.columns(4)

stock_calculado = registro.get("STOCK", "0")
col1.info(f"📦 Stock calculado: **{stock_calculado}**")

lote = col2.text_input("Lote",
                       value=registro.get("LOTE", ""),
                       key="lote_input")


def obter_data(data_str):
    for fmt in ["%d-%m-%y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(data_str.strip(), fmt)
        except:
            continue
    return None


def parse_data_para_input(valor):
    if valor:
        dt = obter_data(valor)
        if dt:
            return dt.date()
    return date(2000, 1, 1)


dt_prod = col3.date_input("Data de Produção",
                          value=parse_data_para_input(
                              registro.get("DT PROD", "")),
                          key="dt_prod_input")
dt_val = col4.date_input("Data de Validade",
                         value=parse_data_para_input(registro.get(
                             "DT VAL", "")),
                         key="dt_val_input")
col5, col6 = st.columns(2)
dt_cong = col5.date_input("Data de Cong.",
                          value=parse_data_para_input(
                              registro.get("DT CONG", "")),
                          key="dt_cong_input")
dias_val = col6.text_input("Dias Val",
                           value=registro.get("Dias Val", ""),
                           key="dias_val_input")

st.markdown("---")
st.subheader("📆 Registos por Dia")
dias_semana = [
    "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"
]
for dia in dias_semana:
    with st.expander(dia.capitalize()):
        col1, col2, col3 = st.columns(3)
        col1.text_input(f"{dia} - INÍCIO",
                        value=registro.get(f"{dia} - INÍCIO", ""),
                        key=f"{dia}_inicio")
        col2.text_input(f"{dia} - ENTRADA",
                        value=registro.get(f"{dia} - ENTRADA", ""),
                        key=f"{dia}_entrada")
        col3.text_input(f"{dia} - FIM",
                        value=registro.get(f"{dia} - FIM", ""),
                        key=f"{dia}_fim")

if st.button("📂 Gravar alterações"):
    nova_linha = {
        "Produto":
        produto_novo,
        "ARMAZEM":
        armazem_escolhido,
        "LOTE":
        st.session_state.get("lote_input", ""),
        "DT PROD":
        st.session_state.get("dt_prod_input",
                             date.today()).strftime("%d-%m-%y"),
        "DT VAL":
        st.session_state.get("dt_val_input",
                             date.today()).strftime("%d-%m-%y"),
        "DT CONG":
        st.session_state.get("dt_cong_input",
                             date.today()).strftime("%d-%m-%y"),
        "Dias Val":
        st.session_state.get("dias_val_input", ""),
        "Data / Semana":
        data_semana
    }
    for dia in dias_semana:
        nova_linha[f"{dia} - INÍCIO"] = st.session_state.get(
            f"{dia}_inicio", "")
        nova_linha[f"{dia} - ENTRADA"] = st.session_state.get(
            f"{dia}_entrada", "")
        nova_linha[f"{dia} - FIM"] = st.session_state.get(f"{dia}_fim", "")

    todas_colunas = worksheet.row_values(1)
    valores_para_inserir = [nova_linha.get(col, "") for col in todas_colunas]

    if lote_escolhido == "(Novo Lote)":
        worksheet.append_row(valores_para_inserir)
        st.success("✔️ Novo lote adicionado com sucesso!")
        st.rerun()
    else:
        todas_linhas = worksheet.get_all_values()
        idx_lote = todas_colunas.index("LOTE")
        row_to_update = None
        for i, linha in enumerate(todas_linhas, start=2):
            if linha[idx_lote] == lote_escolhido:
                row_to_update = i
                break
        if row_to_update:
            worksheet.update(f"A{row_to_update}", [valores_para_inserir])
            st.success("✔️ Lote atualizado com sucesso!")
            st.rerun()
        else:
            st.error("❌ Lote não encontrado para atualização.")
