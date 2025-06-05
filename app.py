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
import os, json, base64

creds_json = base64.b64decode(os.environ["GOOGLE_CREDS_BASE64"]).decode()
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(creds_json), scope)
client = gspread.authorize(creds)

# Acesso ao sheet
sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1-J2mqcgSaq3-2CFVwXHzOvUGvKdYr31v7UT8da3r_OU/edit"
)
worksheet = sheet.worksheet("NOVAUCP")
rows = worksheet.get_all_values()
headers = rows[0]
data = [dict(zip(headers, row)) for row in rows[1:]]

st.write(data_raw)

# Produto e armazém
produtos = sorted(
    set(str(item["Produto"]).strip() for item in data if item.get("Produto")))
produto_escolhido = st.selectbox("🧊 Escolha um produto:", produtos)

armazens = list(
    set(item["ARMAZEM"] for item in data
        if item["Produto"] == produto_escolhido))
armazem_escolhido = st.selectbox("🏢 Escolha um armazém:", armazens)

# Registros filtrados
registros_produto = [
    item for item in data if item["Produto"] == produto_escolhido
    and item["ARMAZEM"] == armazem_escolhido
]

lotes_existentes = list(
    set(str(item["LOTE"]) for item in registros_produto if item.get("LOTE")))
lotes_opcoes = ["(Novo Lote)"] + sorted(lotes_existentes)
lote_escolhido = st.selectbox("📦 Escolha um lote:", lotes_opcoes)

# Determina o registro atual

registro = {}
if lote_escolhido != "(Novo Lote)":
    for item in data:
        if (str(item.get("Produto")) == produto_escolhido
                and str(item.get("ARMAZEM")) == armazem_escolhido
                and str(item.get("LOTE")) == lote_escolhido):
            registro = item
            break

data_semana = st.text_input("🗓️ Data / Semana",
                            value=registro.get("Data / Semana", ""),
                            key="semana_input")

# Título e botão gravar
st.markdown('<div class="titulo">📋 Painel de Produção - NOVAUCP</div>',
            unsafe_allow_html=True)

if st.button("💾 Gravar alterações"):
    # Recolhe valores preenchidos
    lote_digitado = st.session_state.get("lote_input", "")
    stock_digitado = st.session_state.get("stock_input", "")
    dt_prod_digitado = st.session_state.get("dt_prod_input", date.today())
    dt_val_digitado = st.session_state.get("dt_val_input", date.today())

    # Formatar datas
    dt_prod_str = dt_prod_digitado.strftime("%d-%m-%y")
    dt_val_str = dt_val_digitado.strftime("%d-%m-%y")

    # Recolher horários por dia
    dias_semana = [
        "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"
    ]
    campos_dias = {}
    for dia in dias_semana:
        campos_dias[f"{dia} - INÍCIO"] = st.session_state.get(
            f"{dia}_inicio", "")
        campos_dias[f"{dia} - ENTRADA"] = st.session_state.get(
            f"{dia}_entrada", "")
        campos_dias[f"{dia} - FIM"] = st.session_state.get(f"{dia}_fim", "")

    # Preparar nova linha
    nova_linha = {
        "Produto": produto_escolhido,
        "ARMAZEM": armazem_escolhido,
        "STOCK": stock_digitado,
        "LOTE": lote_digitado,
        "DT PRODUÇÃO": dt_prod_str,
        "DT VALIDADE": dt_val_str,
        "Data / Semana": data_semana
    }
    nova_linha.update(campos_dias)

    # Obter todas as colunas na ordem correta
    todas_colunas = worksheet.row_values(1)
    valores_para_inserir = [nova_linha.get(col, "") for col in todas_colunas]

    # Se for novo lote, adicionar
    if lote_escolhido == "(Novo Lote)":
        worksheet.append_row(valores_para_inserir)
        st.success("✔️ Novo lote adicionado com sucesso!")
        worksheet = sheet.worksheet("NOVAUCP")
        data = worksheet.get_all_records()
        st.rerun()
    else:
        # Atualizar lote existente
        todas_linhas = worksheet.get_all_values()
        idx_lote = todas_colunas.index("LOTE")
        row_to_update = None
        for i, linha in enumerate(todas_linhas, start=2):  # pular cabeçalho
            if linha[idx_lote] == lote_escolhido:
                row_to_update = i
                break
        if row_to_update:
            worksheet.update(f"A{row_to_update}", [valores_para_inserir])
            st.success("✔️ Lote atualizado com sucesso!")
            st.rerun()

        else:
            st.error("❌ Lote não encontrado para atualização.")

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
dias_semana = [
    "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"
]
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
