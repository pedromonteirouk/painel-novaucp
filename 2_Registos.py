import streamlit as st
from utils.auth import require_login

require_login()
st.title("Registos por Dia")

dias = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
for dia in dias:
    with st.expander(dia.capitalize()):
        st.text_input(f"{dia} - INÍCIO", key=f"{dia}_inicio")
        st.text_input(f"{dia} - ENTRADA", key=f"{dia}_entrada")
        st.text_input(f"{dia} - SAIDA", key=f"{dia}_saida")
