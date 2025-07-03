import streamlit as st

PIN_CORRETO = "9472"

def require_login():
    if "acesso_autorizado" not in st.session_state:
        st.session_state.acesso_autorizado = False
    if "tentou_entrar" not in st.session_state:
        st.session_state.tentou_entrar = False

    if not st.session_state.acesso_autorizado:
        st.title("Acesso Restrito")
        pin = st.text_input("Introduz o código de acesso:", type="password")
        if st.button("Entrar"):
            st.session_state.tentou_entrar = True
            if pin == PIN_CORRETO:
                st.session_state.acesso_autorizado = True
                st.rerun()
        if st.session_state.tentou_entrar and not st.session_state.acesso_autorizado:
            st.error("Código incorreto. Tenta novamente.")
        st.stop()
