import streamlit as st
import gspread
from datetime import datetime, date
from oauth2client.service_account import ServiceAccountCredentials

# Configuração da página
st.set_page_config(page_title="Painel de Produção - NOVAUCP", layout="wide")

# Estilo embutido
st.markdown("""
    <style>
        .titulo {
            font-size:32px;
            font-weight:700;
            color:#2c3e50;
            margin-bottom:20px;
        }
        .bloco {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .cabecalho {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .campo {
            background-color: #f0f4f8;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
    </style>
""",
            unsafe_allow_html=True)

# Autenticação com Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credenciais.json", scope)
client = gspread.authorize(creds)

# Acesso ao sheet
sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1-J2mqcgSaq3-2CFVwXHzOvUGvKdYr31v7UT8da3r_OU/edit"
)
worksheet = sheet.worksheet("NOVAUCP")
data = worksheet.get_all_records()

# Produto e armazém
produtos = list(set(item["Produto"] for item in data))
produto_escolhido = st.selectbox("🧊 Escolha um produto:", produtos)
armazens = list(
    set(item["ARMAZEM"] for item in data
        if item["Produto"] == produto_escolhido))
armazem_escolhido = st.selectbox("🏢 Escolha um armazém:", armazens)

# Filtrar registros
registros_produto = [
    item for item in data if item["Produto"] == produto_escolhido
    and item["ARMAZEM"] == armazem_escolhido
]
lotes = list(set(item["LOTE"] for item in registros_produto))
lote_escolhido = st.selectbox("📦 Escolha um lote:", lotes)

registro = next(
    (item for item in registros_produto if item["LOTE"] == lote_escolhido), {})

# Botão novo lote
if st.button("➕ Novo Lote"):
    nova_linha = {"Produto": produto_escolhido, "ARMAZEM": armazem_escolhido}
    worksheet.append_row(
        [nova_linha.get(col, "") for col in worksheet.row_values(1)])
    st.rerun()

st.markdown('<div class="titulo">📋 Painel de Produção - NOVAUCP</div>',
            unsafe_allow_html=True)

# Bloco de dados do lote
st.markdown('<div class="bloco">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

stock = col1.text_input("Stock",
                        value=str(registro.get("STOCK", "")),
                        key="stock_input")
lote = col2.text_input("Lote",
                       value=str(registro.get("LOTE", "")),
                       key="lote_input")

# Data de Produção
dt_prod_raw = registro.get("DT PRODUÇÃO", "")
try:
    dt_prod = datetime.strptime(dt_prod_raw.strip(),
                                "%d-%m-%y") if dt_prod_raw else date.today()
except ValueError:
    dt_prod = date.today()
dt_prod = col3.date_input("Data de Produção",
                          value=dt_prod,
                          key="dt_prod_input")

# Data de Validade
dt_val_raw = registro.get("DT VALIDADE", "")
try:
    dt_val = datetime.strptime(dt_val_raw.strip(),
                               "%d-%m-%y") if dt_val_raw else date.today()
except ValueError:
    dt_val = date.today()
dt_val = col4.date_input("Data de Validade", value=dt_val, key="dt_val_input")

st.markdown('</div>', unsafe_allow_html=True)

# Bloco dos dias da semana
dias_semana = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA"]
for dia in dias_semana:
    st.markdown(f'<div class="bloco"><div class="cabecalho">{dia}</div>',
                unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.text_input(f"{dia} - INÍCIO",
                    value=str(registro.get(f"{dia} - INICIO", "")),
                    key=f"{dia}_inicio")
    col2.text_input(f"{dia} - ENTRADA",
                    value=str(registro.get(f"{dia} - ENTRADA", "")),
                    key=f"{dia}_entrada")
    col3.text_input(f"{dia} - FIM",
                    value=str(registro.get(f"{dia} - FIM", "")),
                    key=f"{dia}_fim")
    st.markdown('</div>', unsafe_allow_html=True)

# Botão Gravar (futuramente para update)
st.button("💾 Gravar alterações")
