import streamlit as st
from utils.auth import require_login

require_login()

st.title("📊 Painel de Produção")
st.write("""
Bem-vindo ao Painel de Produção Multipage!  
Usa o menu à esquerda para navegar:
- Dashboard → consulta geral do lote
- Registos → regista dados por dia
- Parâmetros → altera validades e configurações.
""")
