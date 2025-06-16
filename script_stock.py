import requests
import streamlit as st
import os
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---------------- SEGURANÇA ---------------- #
try:
    with open("password.txt") as f:
        correct_password = f.read().strip()
    senha = st.text_input("🔐 Password de acesso", type="password")
    if senha != correct_password:
        st.warning("Acesso restrito.")
        st.stop()
except FileNotFoundError:
    st.error("Ficheiro 'password.txt' em falta.")
    st.stop()

# ---------------- CONFIGURAÇÕES ---------------- #
SHOP_URL = "https://bbgourmet-8638.myshopify.com"
ACCESS_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
LOCATION_ID = "71561281800"

if not ACCESS_TOKEN:
    st.error(
        "❌ Access Token não definido. Vai a Settings > Secrets e adiciona SHOPIFY_TOKEN."
    )
    st.stop()

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# Aliases e exclusões de coleções
alias_colecoes = {
    "para-picar": "Snacks",
    "sopas-diet": "Sopas Diet",
    "vegetarianos": "Pratos Vegetarianos"
}
colecoes_ocultas = ["descontinuado", "oculto"]

# ---------------- FUNÇÕES ---------------- #


@st.cache_data
def obter_colecoes():
    url = f"{SHOP_URL}/admin/api/2023-07/custom_collections.json?limit=250"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return []
    return r.json().get("custom_collections", [])


@st.cache_data
def obter_produtos_da_colecao(handle_colecao):
    colecoes = obter_colecoes()
    colecao_id = next(
        (c["id"] for c in colecoes if c["handle"] == handle_colecao), None)
    if not colecao_id:
        return []

    r = requests.get(
        f"{SHOP_URL}/admin/api/2023-07/collects.json?collection_id={colecao_id}&limit=250",
        headers=HEADERS)
    if r.status_code != 200:
        return []

    ids = [c["product_id"] for c in r.json().get("collects", [])]
    produtos = []
    for pid in ids:
        r = requests.get(f"{SHOP_URL}/admin/api/2023-07/products/{pid}.json",
                         headers=HEADERS)
        if r.status_code == 200:
            produtos.append(r.json().get("product"))
    return produtos


def obter_stock_batch(produtos):
    itens = []
    mapa = {}
    for p in produtos:
        for v in p["variants"]:
            iid = v["inventory_item_id"]
            itens.append(iid)
            mapa[str(iid)] = f"{p['title']} | {v['title']}"

    chunks = [itens[i:i + 50] for i in range(0, len(itens), 50)]
    dados = []
    for grupo in chunks:
        ids_txt = ",".join(str(x) for x in grupo)
        r = requests.get(
            f"{SHOP_URL}/admin/api/2023-07/inventory_levels.json?inventory_item_ids={ids_txt}&location_ids={LOCATION_ID}",
            headers=HEADERS)
        if r.status_code == 200:
            for x in r.json().get("inventory_levels", []):
                dados.append({
                    "Produto": mapa[str(x["inventory_item_id"])],
                    "Stock": x["available"],
                    "inventory_item_id": x["inventory_item_id"]
                })
    return pd.DataFrame(dados)


def atualizar_stock(iid, novo):
    r = requests.post(
        f"{SHOP_URL}/admin/api/2023-07/inventory_levels/set.json",
        headers=HEADERS,
        json={
            "location_id": LOCATION_ID,
            "inventory_item_id": iid,
            "available": int(novo)
        })
    return r.status_code == 200


# ---------------- UI ---------------- #

st.title("Dashboard de Stock - BBGourmet")

colecoes = obter_colecoes()
colecoes_filtradas = [
    c for c in colecoes if c["handle"] not in colecoes_ocultas
]
handle_opcoes = {
    alias_colecoes.get(c["handle"], c["title"]): c["handle"]
    for c in colecoes_filtradas
}

titulo_sel = st.selectbox("Seleciona uma coleção:", list(handle_opcoes.keys()))
handle = handle_opcoes[titulo_sel]

produtos = obter_produtos_da_colecao(handle)
df = obter_stock_batch(produtos)
df.sort_values("Stock", inplace=True)

# Divisão
df_vermelho = df[df["Stock"] == 0]
df_laranja = df[(df["Stock"] > 0) & (df["Stock"] <= 10)]
df_verde = df[df["Stock"] > 20]

st.subheader("🔴 Sem stock")
st.dataframe(df_vermelho, use_container_width=True)

with st.expander("🟠 Ver produtos com pouco stock"):
    st.dataframe(df_laranja, use_container_width=True)

with st.expander("🟢 Ver produtos com stock suficiente"):
    st.dataframe(df_verde, use_container_width=True)

st.markdown("### ✏️ Editar valores")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("Stock",
                    editable=True,
                    type=["numericColumn"],
                    cellStyle={
                        "styleConditions": [{
                            "condition": "params.value == 0",
                            "style": {
                                "backgroundColor": "#ff4d4d"
                            }
                        }, {
                            "condition": "params.value <= 10",
                            "style": {
                                "backgroundColor": "#ffa94d"
                            }
                        }, {
                            "condition": "params.value > 20",
                            "style": {
                                "backgroundColor": "#94d82d"
                            }
                        }]
                    })

grid = AgGrid(df,
              gridOptions=gb.build(),
              update_mode=GridUpdateMode.MODEL_CHANGED,
              editable=True,
              height=400,
              use_container_width=True,
              fit_columns_on_grid_load=True)

editado = grid["data"]
merged = df.merge(editado,
                  on="inventory_item_id",
                  suffixes=("_original", "_editado"))
alterados = merged[merged["Stock_original"] != merged["Stock_editado"]]

if not alterados.empty:
    for _, row in alterados.iterrows():
        novo = int(row["Stock_editado"])
        sucesso = atualizar_stock(row["inventory_item_id"], novo)
        if sucesso:
            st.success(
                f"{row['Produto_editado']} → atualizado para {novo} unidades")
        else:
            st.error(f"Erro ao atualizar {row['Produto_editado']}")
