import streamlit as st
from utils.auth import require_login

require_login()
st.title("Gestão de Parâmetros")

st.selectbox("Produto para editar", ["Produto 1", "Produto 2"])
st.number_input("Nova validade (dias)", min_value=0, max_value=365, step=1)
if st.button("Atualizar validade"):
    st.success("Validade atualizada (exemplo)!")
