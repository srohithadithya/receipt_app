import streamlit as st
from database.crud import create_user, get_user_by_username
from database.database import get_db
from utils.security import validate_password_strength # Assuming this function exists

def show_signup_page(auth_manager):
    st.title("Sign Up")

    with st.form("signup_form"):
        username = st.text_input("Choose Username")
        email = st.text_input("Email (Optional)")
        password = st.text_input("Choose Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Sign Up")

        if submit_button:
            if not username or not password or not confirm_password:
                st.error("Username and Password are required.")
                return

            if password != confirm_password:
                st.error("Passwords do not match.")
                return

            # Basic password strength validation
            if not validate_password_strength(password):
                st.error("Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.")
                return

            db_gen = get_db()
            db = next(db_gen)
            if get_user_by_username(db, username):
                st.error("Username already exists. Please choose a different one.")
                db.close()
                return

            try:
                new_user = create_user(db, username, password, email)
                st.success(f"Account created successfully for {new_user.username}! Please login.")
                # Automatically log in the user after signup, or redirect to login page
                # auth_manager.login(username, password)
                # st.rerun()
            except Exception as e:
                st.error(f"An error occurred during signup: {e}")
            finally:
                db.close()