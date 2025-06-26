import streamlit as st
import gspread
from datetime import datetime, date
from oauth2client.service_account import ServiceAccountCredentials
import os, json, base64

# --- CONFIGURACAO INICIAL ---
st.set_page_config(page_title="Painel de Produção - UCP", layout="wide")

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

# --- CREDENCIAIS GOOGLE SHEETS ---
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
worksheet = sheet.worksheet("NOVAUCP")
rows = worksheet.get_all_values()
headers = rows[0]
data = [dict(zip(headers, row)) for row in rows[1:]]

# --- PRODUTOS E ARMAZEM ---
produtos = sorted(
    set(
        str(item.get("Produto", "")).strip() for item in data
        if item.get("Produto", "").strip()))
produtos_opcoes = ["(Novo Produto)"] + produtos
col1, col2 = st.columns(2)
with col1:
    produto_escolhido = st.selectbox("🧊 Produto", produtos_opcoes)
    if produto_escolhido == "(Novo Produto)":
        produto_novo = st.text_input("✏️ Novo produto:", key="produto_input")
    else:
        produto_novo = produto_escolhido

ARMAZENS_FIXOS = ["UCP", "MAIORCA", "CLOUD"]
with col2:
    if produto_escolhido == "(Novo Produto)":
        armazens = ARMAZENS_FIXOS
    else:
        armazens = sorted(
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

# --- DADOS DO LOTE ---
st.subheader("📋 Dados do Lote")
col1, col2, col3, col4 = st.columns(4)
stock = col1.text_input("Stock",
                        value=str(registro.get("STOCK", "")),
                        key="stock_input")
lote = col2.text_input("Lote",
                       value=str(registro.get("LOTE", "")),
                       key="lote_input")

# Datas
dt_prod_raw = registro.get("DT PROD", "")
dt_val_raw = registro.get("DT VAL", "")
dt_cong_raw = registro.get("DT CONG", "")
dias_val_raw = registro.get("Dias Val", "")

try:
    dt_prod = datetime.strptime(dt_prod_raw.strip(),
                                "%d-%m-%y") if dt_prod_raw else date.today()
except ValueError:
    dt_prod = date.today()
try:
    dt_val = datetime.strptime(dt_val_raw.strip(),
                               "%d-%m-%y") if dt_val_raw else date.today()
except ValueError:
    dt_val = date.today()
try:
    dt_cong = datetime.strptime(dt_cong_raw.strip(),
                                "%d-%m-%y") if dt_cong_raw else date.today()
except ValueError:
    dt_cong = date.today()

col5, col6 = st.columns(2)
dt_prod = col3.date_input("Data de Produção",
                          value=dt_prod,
                          key="dt_prod_input")
dt_val = col4.date_input("Data de Validade", value=dt_val, key="dt_val_input")
dt_cong = col5.date_input("Data de Cong.", value=dt_cong, key="dt_cong_input")
dias_val = col6.text_input("Dias Val",
                           value=dias_val_raw,
                           key="dias_val_input")


# --- FUNCAO BLOCOS DIARIOS ---
def bloco_dia(dia, registro):
    with st.expander(f"{dia.capitalize()}" if dia != "DOMINGO" else "Domingo"):
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


# --- DIAS DA SEMANA ---
st.markdown("---")
st.subheader("📆 Registos por Dia")
dias_semana = [
    "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"
]
for dia in dias_semana:
    bloco_dia(dia, registro)

# --- GRAVAR ALTERACOES ---
if st.button("📂 Gravar alterações"):
    lote_digitado = st.session_state.get("lote_input", "")
    stock_digitado = st.session_state.get("stock_input", "")
    dt_prod_digitado = st.session_state.get("dt_prod_input", date.today())
    dt_val_digitado = st.session_state.get("dt_val_input", date.today())
    dt_cong_digitado = st.session_state.get("dt_cong_input", date.today())
    dias_val_digitado = st.session_state.get("dias_val_input", "")

    dt_prod_str = dt_prod_digitado.strftime("%d-%m-%y")
    dt_val_str = dt_val_digitado.strftime("%d-%m-%y")
    dt_cong_str = dt_cong_digitado.strftime("%d-%m-%y")

    campos_dias = {}
    for dia in dias_semana:
        campos_dias[f"{dia} - INÍCIO"] = st.session_state.get(
            f"{dia}_inicio", "")
        campos_dias[f"{dia} - ENTRADA"] = st.session_state.get(
            f"{dia}_entrada", "")
        campos_dias[f"{dia} - FIM"] = st.session_state.get(f"{dia}_fim", "")

    nova_linha = {
        "Produto": produto_novo,
        "ARMAZEM": armazem_escolhido,
        "STOCK": stock_digitado,
        "LOTE": lote_digitado,
        "DT PROD": dt_prod_str,
        "DT VAL": dt_val_str,
        "DT CONG": dt_cong_str,
        "Dias Val": dias_val_digitado,
        "Data / Semana": data_semana
    }
    nova_linha.update(campos_dias)

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
