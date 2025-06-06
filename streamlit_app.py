import streamlit as st
from st_snowauth import snowauth_session

# Mostra contenuti visibili prima dell'autenticazione
st.markdown("## Benvenuto nella nostra applicazione")

# Avvia la sessione di autenticazione
session = snowauth_session()

# Mostra contenuti visibili solo dopo l'autenticazione
st.markdown("## Contenuti protetti")
st.write("Benvenuto, sei autenticato come:", session.user)
