import streamlit as st
import requests
import os

# --- CONFIGURAÇÕES ---
SHOP_URL = "https://bbgourmet-8638.myshopify.com"
ACCESS_TOKEN = os.environ.get("", "")

if not ACCESS_TOKEN:
    st.error(
        "❌ Access Token não definido. Vai a Settings > Secrets e adiciona SHOPIFY_TOKEN."
    )
    st.stop()

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# --- COLEÇÕES BBGOURMET ---
COLECOES = {
    "Sopas": "sopas",
    "Sopas Diet": "sopas-diet",
    "Carnes": "carnes",
    "Peixes": "peixes",
    "Vegetarianos": "vegetarianos",
    "Familiares": "familiares",
    "Guarnições": "guarnicoes"
}


# --- FUNÇÕES ---
def obter_produtos_ativos_por_colecao(handle_colecao):
    url = f"{SHOP_URL}/admin/api/2023-07/collections/{handle_colecao}/products.json?status=active&limit=250"
    resposta = requests.get(url, headers=HEADERS)
    if resposta.status_code != 200:
        st.error(
            f"Erro ao buscar produtos da coleção '{handle_colecao}': {resposta.text}"
        )
        return []
    return resposta.json().get("products", [])


def obter_stock_por_inventory_item(inventory_item_id, location_id):
    url = f"{SHOP_URL}/admin/api/2023-07/inventory_levels.json?inventory_item_ids={inventory_item_id}&location_ids={location_id}"
    resposta = requests.get(url, headers=HEADERS)
    if resposta.status_code != 200:
        return None
    dados = resposta.json().get("inventory_levels", [])
    if dados:
        return dados[0].get("available")
    return None


def cor_stock(qtd):
    if qtd <= 0:
        return "#ff4d4d"  # vermelho
    elif qtd <= 10:
        return "#ffa94d"  # laranja
    elif qtd >= 20:
        return "#94d82d"  # verde
    else:
        return "#d3d3d3"  # cinza


# --- INTERFACE ---
st.set_page_config("Dashboard de Stock - BBGourmet", layout="wide")
st.title("Dashboard de Stock - BBGourmet")

location_id = st.text_input("ID do local de stock (location_id da loja):")

if location_id:
    for nome_colecao, handle in COLECOES.items():
        st.subheader(f"🌟 {nome_colecao}")
        produtos = obter_produtos_ativos_por_colecao(handle)

        lista_produtos = []
        for produto in produtos:
            for variante in produto.get("variants", []):
                inventory_item_id = variante.get("inventory_item_id")
                titulo = f"{produto['title']} ({variante['title']})"
                stock = obter_stock_por_inventory_item(inventory_item_id,
                                                       location_id)
                if stock is not None:
                    lista_produtos.append({
                        "titulo":
                        titulo,
                        "stock":
                        stock,
                        "inventory_item_id":
                        inventory_item_id
                    })

        lista_produtos.sort(key=lambda x: x["stock"])

        for item in lista_produtos:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(item["titulo"])
            with col2:
                cor = cor_stock(item["stock"])
                novo_stock = st.number_input(
                    "",
                    value=item["stock"],
                    step=1,
                    key=f"{item['inventory_item_id']}")
                st.markdown(
                    f"<div style='background-color:{cor};padding:5px;border-radius:5px;text-align:center;'>{novo_stock}</div>",
                    unsafe_allow_html=True)

                # Atualizar stock se alterado
                if novo_stock != item["stock"]:
                    url_update = f"{SHOP_URL}/admin/api/2023-07/inventory_levels/set.json"
                    payload = {
                        "location_id": location_id,
                        "inventory_item_id": item["inventory_item_id"],
                        "available": int(novo_stock)
                    }
                    r = requests.post(url_update,
                                      headers=HEADERS,
                                      json=payload)
                    if r.status_code == 200:
                        st.success(f"Stock atualizado para {novo_stock}!")
                    else:
                        st.error(f"Erro ao atualizar stock: {r.text}")
