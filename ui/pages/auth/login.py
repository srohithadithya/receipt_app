import streamlit as st
from ui.auth_manager import AuthManager

def show_login_page(auth_manager: AuthManager):
    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if auth_manager.login(username, password):
                st.rerun() # Rerun to change UI based on login status