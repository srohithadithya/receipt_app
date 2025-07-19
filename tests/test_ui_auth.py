import pytest
from unittest.mock import MagicMock, patch
from ui import auth_manager
from ui.pages.auth import login, signup
from database import crud
from utils import security
from utils.errors import AuthenticationError
from database.database import get_db # To be mocked

# Mock db_session from conftest.py implicitly patches get_db()


def test_auth_manager_initial_state(mock_streamlit):
    """Test the initial state of AuthManager."""
    am = auth_manager.AuthManager()
    assert not am.is_logged_in()
    assert am.get_current_username() is None
    assert am.get_current_user_id() is None

def test_auth_manager_login_success(mock_streamlit, db_session, test_user_data):
    """Test successful user login."""
    # Create a user in the test database
    hashed_password = security.hash_password(test_user_data["password"])
    mock_db_user = MagicMock(
        username=test_user_data["username"],
        password_hash=hashed_password,
        id=1
    )
    # Mock crud.get_user_by_username to return our mocked user
    with patch('database.crud.get_user_by_username', return_value=mock_db_user):
        am = auth_manager.AuthManager()
        result = am.login(test_user_data["username"], test_user_data["password"])

        assert result is True
        assert am.is_logged_in()
        assert am.get_current_username() == test_user_data["username"]
        assert am.get_current_user_id() == 1
        mock_streamlit.success.assert_called_once_with(f"Welcome, {test_user_data['username']}!")
        mock_streamlit.error.assert_not_called()

def test_auth_manager_login_fail_invalid_password(mock_streamlit, db_session, test_user_data):
    """Test failed login with invalid password."""
    hashed_password = security.hash_password(test_user_data["password"])
    mock_db_user = MagicMock(
        username=test_user_data["username"],
        password_hash=hashed_password,
        id=1
    )
    with patch('database.crud.get_user_by_username', return_value=mock_db_user):
        am = auth_manager.AuthManager()
        result = am.login(test_user_data["username"], "wrong_password")

        assert result is False
        assert not am.is_logged_in()
        mock_streamlit.error.assert_called_once_with("Invalid username or password.")
        mock_streamlit.success.assert_not_called()

def test_auth_manager_login_fail_user_not_found(mock_streamlit, db_session):
    """Test failed login when user is not found."""
    with patch('database.crud.get_user_by_username', return_value=None):
        am = auth_manager.AuthManager()
        result = am.login("nonexistent", "any_password")

        assert result is False
        assert not am.is_logged_in()
        mock_streamlit.error.assert_called_once_with("Invalid username or password.")
        mock_streamlit.success.assert_not_called()

def test_auth_manager_logout(mock_streamlit):
    """Test user logout functionality."""
    am = auth_manager.AuthManager()
    # Simulate a logged-in state
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.username = "logged_in_user"
    mock_streamlit.session_state.user_id = 1

    am.logout()

    assert not am.is_logged_in()
    assert am.get_current_username() is None
    assert am.get_current_user_id() is None
    mock_streamlit.info.assert_called_once_with("You have been logged out.")

def test_auth_manager_require_login_redirects_if_not_logged_in(mock_streamlit):
    """Test require_login stops execution if user is not logged in."""
    am = auth_manager.AuthManager() # Default not logged in
    am.require_login()
    mock_streamlit.warning.assert_called_once_with("Please log in to access this page.")
    mock_streamlit.stop.assert_called_once() # Should stop Streamlit execution

def test_auth_manager_require_login_allows_if_logged_in(mock_streamlit):
    """Test require_login does not stop if user is logged in."""
    am = auth_manager.AuthManager()
    mock_streamlit.session_state.logged_in = True
    am.require_login()
    mock_streamlit.warning.assert_not_called()
    mock_streamlit.stop.assert_not_called()


# --- ui.pages.auth.login tests ---

def test_show_login_page_successful_login(mock_streamlit, mocker, db_session):
    """Test login page logic on successful login."""
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True) # Simulate button click
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["testuser", "password"]) # Simulate inputs
    
    mock_auth_manager = auth_manager.AuthManager()
    mocker.patch.object(mock_auth_manager, 'login', return_value=True) # Mock AuthManager.login

    login.show_login_page(mock_auth_manager)

    mock_auth_manager.login.assert_called_once_with("testuser", "password")
    mock_streamlit.rerun.assert_called_once()

def test_show_login_page_failed_login(mock_streamlit, mocker, db_session):
    """Test login page logic on failed login."""
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True)
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["testuser", "wrong_password"])

    mock_auth_manager = auth_manager.AuthManager()
    mocker.patch.object(mock_auth_manager, 'login', return_value=False) # Mock AuthManager.login to fail

    login.show_login_page(mock_auth_manager)

    mock_auth_manager.login.assert_called_once_with("testuser", "wrong_password")
    mock_streamlit.rerun.assert_not_called() # No rerun on failed login (error message displayed)


# --- ui.pages.auth.signup tests ---

def test_show_signup_page_successful_signup(mock_streamlit, mocker, db_session):
    """Test signup page logic on successful signup."""
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True)
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["newuser", "test@example.com", "Password123!", "Password123!"])
    
    mocker.patch('database.crud.get_user_by_username', return_value=None) # User does not exist
    mocker.patch('database.crud.create_user', return_value=MagicMock(username="newuser")) # Simulate user creation
    mocker.patch('utils.security.validate_password_strength', return_value=True) # Password is strong

    signup.show_signup_page(MagicMock()) # AuthManager isn't directly used for login after signup here

    mock_streamlit.success.assert_called_once_with("Account created successfully for newuser! Please login.")
    mock_streamlit.error.assert_not_called()
    mock_streamlit.rerun.assert_not_called() # No rerun, user is informed to login

def test_show_signup_page_password_mismatch(mock_streamlit, mocker, db_session):
    """Test signup page logic when passwords do not match."""
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True)
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["newuser", "test@example.com", "Password123!", "Mismatch!"])

    signup.show_signup_page(MagicMock())

    mock_streamlit.error.assert_called_once_with("Passwords do not match.")
    mocker.patch('database.crud.create_user').assert_not_called()

def test_show_signup_page_username_exists(mock_streamlit, mocker, db_session):
    """Test signup page logic when username already exists."""
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True)
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["existinguser", "test@example.com", "Password123!", "Password123!"])
    
    mocker.patch('database.crud.get_user_by_username', return_value=MagicMock(username="existinguser")) # User exists
    mocker.patch('utils.security.validate_password_strength', return_value=True)

    signup.show_signup_page(MagicMock())

    mock_streamlit.error.assert_called_once_with("Username already exists. Please choose a different one.")
    mocker.patch('database.crud.create_user').assert_not_called()

def test_show_signup_page_weak_password(mock_streamlit, mocker, db_session):
    """Test signup page logic when password is weak."""
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True)
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["newuser", "test@example.com", "weak", "weak"])
    
    mocker.patch('database.crud.get_user_by_username', return_value=None)
    mocker.patch('utils.security.validate_password_strength', return_value=False) # Password is weak

    signup.show_signup_page(MagicMock())

    mock_streamlit.error.assert_called_once_with("Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.")
    mocker.patch('database.crud.create_user').assert_not_called()