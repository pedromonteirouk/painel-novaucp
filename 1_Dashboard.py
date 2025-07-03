import streamlit as st
from utils.auth import require_login
from utils.sheets import get_worksheet

require_login()
st.title("Dashboard do Lote")

pagina = st.session_state.get("pagina", "NOVAUCP")
worksheet = get_worksheet(pagina)

valor_a1 = worksheet.acell("AG1").value or ""
st.text_input("Data / Semana", value=valor_a1, key="semana_input")
st.success(f"Mostrando dados para página: {pagina}")
