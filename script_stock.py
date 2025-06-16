import requests
import streamlit as st
import os
import pandas as pd

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

# ---------------- FUNÇÕES ---------------- #


@st.cache_data
def obter_colecoes():
    url = f"{SHOP_URL}/admin/api/2023-07/custom_collections.json?limit=250"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        st.error("Erro ao obter coleções.")
        return []
    return r.json().get("custom_collections", [])


@st.cache_data
def obter_produtos_da_colecao(handle_colecao):
    colecoes = obter_colecoes()
    colecao_id = next(
        (c["id"] for c in colecoes if c["handle"] == handle_colecao), None)
    if not colecao_id:
        st.warning("Coleção não encontrada.")
        return []

    produtos_url = f"{SHOP_URL}/admin/api/2023-07/collects.json?collection_id={colecao_id}&limit=250"
    r = requests.get(produtos_url, headers=HEADERS)
    if r.status_code != 200:
        st.error("Erro a obter produtos da coleção.")
        return []

    product_ids = [c["product_id"] for c in r.json().get("collects", [])]

    produtos = []
    for pid in product_ids:
        produto_url = f"{SHOP_URL}/admin/api/2023-07/products/{pid}.json"
        r = requests.get(produto_url, headers=HEADERS)
        if r.status_code == 200:
            produtos.append(r.json().get("product"))
    return produtos


def obter_stock_por_produto(produto):
    resultado = []
    for variante in produto["variants"]:
        inventory_item_id = variante["inventory_item_id"]
        stock_url = f"{SHOP_URL}/admin/api/2023-07/inventory_levels.json?inventory_item_ids={inventory_item_id}&location_ids={LOCATION_ID}"
        r = requests.get(stock_url, headers=HEADERS)
        if r.status_code == 200:
            levels = r.json().get("inventory_levels", [])
            if levels:
                stock = levels[0]["available"]
                resultado.append({
                    "Produto": f"{produto['title']} | {variante['title']}",
                    "Stock": stock,
                    "inventory_item_id": inventory_item_id
                })
    return resultado


def atualizar_stock(inventory_item_id, novo_stock):
    payload = {
        "location_id": LOCATION_ID,
        "inventory_item_id": inventory_item_id,
        "available": int(novo_stock)
    }
    r = requests.post(
        f"{SHOP_URL}/admin/api/2023-07/inventory_levels/set.json",
        headers=HEADERS,
        json=payload)
    return r.status_code == 200


# ---------------- STREAMLIT UI ---------------- #

st.title("Dashboard de Stock - BBGourmet")

colecoes = obter_colecoes()
handle_opcoes = {c["title"]: c["handle"] for c in colecoes}
titulo_selecionado = st.selectbox("Seleciona uma coleção:",
                                  list(handle_opcoes.keys()))
handle_selecionado = handle_opcoes.get(titulo_selecionado)

if handle_selecionado:
    produtos = obter_produtos_da_colecao(handle_selecionado)
    resultado = []

    for produto in produtos:
        stock_info = obter_stock_por_produto(produto)
        resultado.extend(stock_info)

    df = pd.DataFrame(resultado)
    df.sort_values(by="Stock", inplace=True)
    df.reset_index(drop=True, inplace=True)

    st.subheader(f"📆 Produtos da coleção: {handle_selecionado}")

    def cor_linha(val):
        cor = "background-color: #ff4d4d" if val == 0 else \
              "background-color: #ffa94d" if val <= 10 else \
              "background-color: #94d82d" if val > 20 else ""
        return cor

    styled_df = df.style.applymap(cor_linha, subset=["Stock"])
    st.dataframe(styled_df, use_container_width=True)

    st.markdown("### ✏️ Atualizar stock")
    for i, row in df.iterrows():
        novo_valor = st.number_input(f"{row['Produto']}",
                                     value=int(row['Stock']),
                                     step=1,
                                     key=row["inventory_item_id"])
        if novo_valor != row['Stock']:
            sucesso = atualizar_stock(row['inventory_item_id'], novo_valor)
            if sucesso:
                st.success(
                    f"✅ {row['Produto']} atualizado para {novo_valor} unidades"
                )
            else:
                st.error("Erro ao atualizar o stock.")
