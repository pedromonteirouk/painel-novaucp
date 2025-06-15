import requests

SHOP_URL = "https://bbgourmet-8638.myshopify.com"
ACCESS_TOKEN = ""  # <-- substitui aqui

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}


# 1. Obter localização (location_id)
def obter_locations():
    url = f"{SHOP_URL}/admin/api/2023-07/locations.json"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        for loc in r.json().get("locations", []):
            print(f"📍 Location: {loc['name']} (ID: {loc['id']})")
    else:
        print("Erro a obter localizações:", r.text)


# 2. Obter coleções
def obter_colecoes():
    url = f"{SHOP_URL}/admin/api/2023-07/custom_collections.json?limit=250"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        print("🗂️ Coleções disponíveis:")
        for col in r.json().get("custom_collections", []):
            print(f"- {col['title']} → handle: {col['handle']}")
    else:
        print("Erro a obter coleções:", r.text)


if __name__ == "__main__":
    print("🔎 A verificar acesso ao Shopify...")
    obter_locations()
    print("\n------------------------------\n")
    obter_colecoes()
