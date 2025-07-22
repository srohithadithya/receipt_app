import streamlit as st
import logging

# Local imports from your project structure
from ui.auth_manager import AuthManager
from ui.pages.auth import login, signup
from ui.pages import dashboard, upload, records, home # Import the new home page
from database.database import create_db_tables, get_db # Import for initial table creation and session
from database.crud import get_receipts_by_user # For checking user records efficiently

# Configure basic logging for the application's entry point
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Application Initialization ---

# Initialize AuthManager instance
auth_manager = AuthManager()

try:
    create_db_tables()
    logger.info("Database tables initialized successfully or already exist.")
except Exception as e:
    logger.critical(f"Failed to initialize database tables: {e}")
    st.error("Application startup failed: Could not connect to or initialize the database. Please check logs.")
    st.stop() # Halt the Streamlit app if DB fails to initialize

# --- Main Streamlit Application Logic ---

def main():
    """
    Main function to run the Streamlit application.
    Handles page configuration, authentication flow, and content routing.
    """
    st.set_page_config(
        page_title="Receipt & Bill Tracker",
        page_icon="💸",
        layout="wide",
        initial_sidebar_state="expanded" # Keep sidebar open by default
    )

    # Custom CSS for better aesthetics and interactive effects
    st.markdown("""
        <style>
        /* General button styling */
        .stButton>button {
            border-radius: 5px;
            border: 1px solid #4CAF50; /* Primary color border */
            color: white;
            background-color: #4CAF50; /* Primary color background */
            padding: 10px 24px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.2s ease-in-out; /* Smooth transition for hover effects */
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); /* Subtle shadow */
        }
        /* Button hover effect */
        .stButton>button:hover {
            background-color: #45a049; /* Slightly darker green */
            border-color: #45a049;
            box-shadow: 0 4px 10px rgba(0,0,0,0.25); /* Enhanced shadow */
            transform: translateY(-2px); /* Slight lift effect */
        }

        /* Sidebar navigation links */
        .css-1d391kg a { /* Targets <a> tags within the sidebar nav list */
            color: #303030; /* Dark text color for links */
            font-size: 1.1em;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 5px;
            transition: all 0.2s ease-in-out;
        }
        .css-1d391kg a:hover {
            background-color: #e0f2f1; /* Light teal hover background */
            color: #00796b; /* Darker teal text on hover */
            transform: translateX(5px); /* Slide effect on hover */
        }
        .css-1d391kg a[aria-selected="true"] { /* Active selected link */
            background-color: #4CAF50; /* Primary color for active link */
            color: white;
            font-weight: bold;
        }
        .css-1d391kg a[aria-selected="true"]:hover { /* Active selected link hover */
            background-color: #4CAF50; /* Keep same color */
            transform: none; /* No slide effect */
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #303030; /* Dark gray for all headers */
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }

        /* Markdown text */
        .stMarkdown {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #555; /* Slightly lighter gray for body text */
        }

        /* Streamlit info, warning, error messages */
        .stAlert {
            border-radius: 8px;
        }
        .stAlert.info { border-left: 5px solid #2196F3; } /* Blue */
        .stAlert.warning { border-left: 5px solid #FFC107; } /* Amber */
        .stAlert.error { border-left: 5px solid #F44336; } /* Red */
        .stAlert.success { border-left: 5px solid #4CAF50; } /* Green */

        /* General container styling */
        .stApp {
            background-color: #f8f9fa; /* Very light gray overall background */
        }

        /* Card-like styling for sections (e.g., info cards in dashboard) */
        div[data-testid="stVerticalBlock"] > div > div {
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            padding: 20px;
            background-color: white;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)


    # Authentication Check and Navigation Routing
    if not auth_manager.is_logged_in():
        # Display authentication pages (Home, Login, Signup)
        st.sidebar.title("Welcome!")
        page = st.sidebar.radio("Go to", ["Home", "Login", "Signup"], key="auth_nav_radio")

        if page == "Home":
            home.show_home_page()
        elif page == "Login":
            login.show_login_page(auth_manager)
        elif page == "Signup":
            signup.show_signup_page(auth_manager)
    else:
        # User is logged in, display main application pages
        st.sidebar.title(f"Welcome, {auth_manager.get_current_username()}! 👋")

        # Check if the user has any existing records to optimize initial navigation
        has_records = False
        db_gen = get_db() # Get a database session
        db = next(db_gen) # Retrieve the session object
        try:
            user_id = auth_manager.get_current_user_id()
            # Efficiently check for existing records (limit=1 is key here)
            first_record = get_receipts_by_user(db, user_id, limit=1)
            has_records = bool(first_record)
        except Exception as e:
            logger.error(f"Error checking for user records in app.py: {e}")
            st.error("Failed to check for your past records. Please try again.")
        finally:
            db.close() # Always close the database session

        # Determine navigation options based on whether user has records
        if not has_records:
            st.sidebar.info("It looks like you don't have any records yet. Let's get started!")
            page_options = ["Upload Receipt", "Logout"]
            default_page = "Upload Receipt"
        else:
            page_options = ["Dashboard", "Upload Receipt", "View Records", "Logout"]
            default_page = "Dashboard" # Default to dashboard if records exist

        # Use st.session_state to persist selected page across reruns
        if "current_main_page" not in st.session_state:
            st.session_state["current_main_page"] = default_page

        page = st.sidebar.radio(
            "Navigation",
            page_options,
            key="main_nav_radio",
            index=page_options.index(st.session_state["current_main_page"]) if st.session_state["current_main_page"] in page_options else 0
        )
        st.session_state["current_main_page"] = page # Update session state on selection

        # Route to the selected page function
        if page == "Dashboard":
            dashboard.show_dashboard_page()
        elif page == "Upload Receipt":
            upload.show_upload_page()
        elif page == "View Records":
            records.show_records_page()
        elif page == "Logout":
            auth_manager.logout()
            st.session_state.clear() # Clear all session state on logout
            st.rerun() # Force a rerun to return to the unauthenticated state

# --- Entry Point ---
if __name__ == "__main__":
    import database.database # Ensures database.py is loaded and tables potentially created
    import database.crud    # Ensures CRUD functions are available
    import utils.security
    import utils.errors
    import utils.helpers

    main()
