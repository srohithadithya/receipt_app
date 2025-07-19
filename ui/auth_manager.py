import streamlit as st
from database.crud import get_user_by_username
from database.database import get_db
from utils.security import verify_password

class AuthManager:
    def __init__(self):
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        if "username" not in st.session_state:
            st.session_state.username = None
        if "user_id" not in st.session_state:
            st.session_state.user_id = None

    def login(self, username, password):
        db_gen = get_db()
        db = next(db_gen) # Get the session
        user = get_user_by_username(db, username)
        db.close() # Close the session

        if user and verify_password(password, user.password_hash):
            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.user_id = user.id
            st.success(f"Welcome, {user.username}!")
            return True
        else:
            st.error("Invalid username or password.")
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            return False

    def logout(self):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.info("You have been logged out.")

    def is_logged_in(self):
        return st.session_state.logged_in

    def get_current_username(self):
        return st.session_state.username

    def get_current_user_id(self):
        return st.session_state.user_id

    def require_login(self):
        if not self.is_logged_in():
            st.warning("Please log in to access this page.")
            st.stop() # Stops execution of the rest of the page