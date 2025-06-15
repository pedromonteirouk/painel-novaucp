import requests
import streamlit as st
import os

# ---------------- CONFIGURAÇÕES ---------------- #
SHOP_URL = "https://bbgourmet-8638.myshopify.com"
ACCESS_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")

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
def obter_produtos_da_colecao(handle_colecao):
    """Obter produtos de uma coleção específica (por handle)."""
    colecao_url = f"{SHOP_URL}/admin/api/2023-07/custom_collections.json"
    r = requests.get(colecao_url, headers=HEADERS)
    if r.status_code != 200:
        st.error("Erro a obter coleções.")
        return []

    colecoes = r.json().get("custom_collections", [])
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


@st.cache_data
def obter_stock_por_produto(produto, location_id):
    resultado = []
    for variante in produto["variants"]:
        inventory_item_id = variante["inventory_item_id"]
        stock_url = f"{SHOP_URL}/admin/api/2023-07/inventory_levels.json?inventory_item_ids={inventory_item_id}&location_ids={location_id}"
        r = requests.get(stock_url, headers=HEADERS)
        if r.status_code == 200:
            levels = r.json().get("inventory_levels", [])
            if levels:
                stock = levels[0]["available"]
                resultado.append({"title": produto["title"], "stock": stock})
    return resultado


# ---------------- STREAMLIT UI ---------------- #

st.title("Dashboard de Stock - BBGourmet")
location_id = st.text_input("ID do local de stock (location_id da loja):")

if location_id:
    produtos = obter_produtos_da_colecao("refrigeradoscongelados")
    resultado = []

    for produto in produtos:
        stock_info = obter_stock_por_produto(produto, location_id)
        resultado.extend(stock_info)

    produtos_ordenados = sorted(
        resultado,
        key=lambda x: (x['stock'] == 0, x['stock'] <= 10, -x['stock']))

    st.subheader("📦 Produtos da coleção 'Refrigerados & Congelados'")
    for p in produtos_ordenados:
        cor = "🔴" if p['stock'] == 0 else "🟠" if p['stock'] <= 10 else "🟢"
        st.write(f"{cor} **{p['title']}** — {p['stock']} unidades")
