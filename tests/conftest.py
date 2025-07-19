import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import Base, get_db
from database import crud
from utils.security import hash_password
from datetime import date, datetime
import pandas as pd
from unittest.mock import MagicMock, patch
import io
import os

# --- Database Fixtures ---

@pytest.fixture(scope="session")
def engine():
    """Provides a SQLAlchemy engine connected to an in-memory SQLite database for the test session."""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="session")
def tables(engine):
    """Creates all tables in the in-memory database at the start of the session and drops them at the end."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine, tables):
    """
    Provides a database session for each test function.
    Each test gets a fresh session, and changes are rolled back afterwards.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Patch get_db to return our test session
    with patch('database.database.get_db', return_value=iter([session])):
        yield session

    session.close()
    transaction.rollback() # Rollback all changes
    connection.close()

# --- Mock Data Fixtures ---

@pytest.fixture
def test_user_data():
    """Provides data for a test user."""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "email": "test@example.com"
    }

@pytest.fixture
def create_test_user(db_session, test_user_data):
    """Creates and returns a test user in the database."""
    user = crud.create_user(db_session, **test_user_data)
    db_session.refresh(user)
    return user

@pytest.fixture
def create_sample_receipts(db_session, create_test_user):
    """Creates and returns sample receipts for the test user."""
    user = create_test_user
    receipts_data = [
        {
            "vendor_name": "Groceries Inc.",
            "transaction_date": date(2023, 1, 15),
            "amount": 100.50,
            "currency": "USD",
            "category_name": "Groceries",
            "original_filename": "receipt_grocery_1.jpg",
            "parsed_raw_text": "Vendor: Groceries Inc. Date: 2023-01-15 Total: $100.50"
        },
        {
            "vendor_name": "Utility Co.",
            "transaction_date": date(2023, 2, 1),
            "amount": 50.25,
            "currency": "EUR",
            "category_name": "Utilities",
            "original_filename": "bill_feb.pdf",
            "parsed_raw_text": "Utility Co. Bill Date: 2023-02-01 Amount: 50.25 EUR"
        },
        {
            "vendor_name": "Amazon Online",
            "transaction_date": date(2023, 2, 10),
            "amount": 75.00,
            "currency": "USD",
            "category_name": "Shopping",
            "original_filename": "amazon_order.txt",
            "parsed_raw_text": "Amazon.com Order Date: 02/10/2023 Total: $75.00"
        },
        {
            "vendor_name": "Groceries Inc.",
            "transaction_date": date(2023, 3, 5),
            "amount": 120.00,
            "currency": "USD",
            "category_name": "Groceries",
            "original_filename": "receipt_grocery_2.png",
            "parsed_raw_text": "Groceries Inc. Date: 03/05/2023 Total: $120.00"
        },
        {
            "vendor_name": "Local Cafe",
            "transaction_date": date(2023, 3, 10),
            "amount": 15.00,
            "currency": "USD",
            "category_name": "Dining",
            "original_filename": "cafe_bill.jpg",
            "parsed_raw_text": "Local Cafe Date: 03/10/2023 Total: $15.00"
        }
    ]
    created_receipts = []
    for data in receipts_data:
        receipt = crud.create_receipt(db_session, owner_id=user.id, **data)
        db_session.refresh(receipt)
        created_receipts.append(receipt)
    return created_receipts

# --- Mock Streamlit Fixture ---
@pytest.fixture
def mock_streamlit(mocker):
    """
    Mocks common Streamlit functions and session_state for testing UI logic.
    """
    mock_st = MagicMock()

    # Mock st.session_state
    mock_session_state = {}
    mock_st.session_state = mock_session_state

    # Common Streamlit functions
    mock_st.text_input = mocker.MagicMock(return_value="")
    mock_st.number_input = mocker.MagicMock(return_value=0.0)
    mock_st.date_input = mocker.MagicMock(return_value=date.today())
    mock_st.selectbox = mocker.MagicMock(side_effect=lambda label, options, **kwargs: options[0] if options else None)
    mock_st.radio = mocker.MagicMock(side_effect=lambda label, options, **kwargs: options[0] if options else None)
    mock_st.button = mocker.MagicMock(return_value=False)
    mock_st.form_submit_button = mocker.MagicMock(return_value=False)
    mock_st.file_uploader = mocker.MagicMock(return_value=None)
    mock_st.progress = mocker.MagicMock(return_value=MagicMock(empty=MagicMock())) # For progress bar
    mock_st.info = mocker.MagicMock()
    mock_st.warning = mocker.MagicMock()
    mock_st.error = mocker.MagicMock()
    mock_st.success = mocker.MagicMock()
    mock_st.write = mocker.MagicMock()
    mock_st.markdown = mocker.MagicMock()
    mock_st.header = mocker.MagicMock()
    mock_st.subheader = mocker.MagicMock()
    mock_st.image = mocker.MagicMock()
    mock_st.plotly_chart = mocker.MagicMock()
    mock_st.columns = mocker.MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
    mock_st.sidebar = MagicMock()
    mock_st.sidebar.title = mocker.MagicMock()
    mock_st.sidebar.radio = mocker.MagicMock(side_effect=lambda label, options, **kwargs: options[0] if options else None)
    mock_st.sidebar.text_input = mocker.MagicMock(return_value="")
    mock_st.sidebar.number_input = mocker.MagicMock(return_value=0.0)
    mock_st.sidebar.selectbox = mocker.MagicMock(side_effect=lambda label, options, **kwargs: options[0] if options else None)
    mock_st.sidebar.info = mocker.MagicMock()
    mock_st.sidebar.warning = mocker.MagicMock()
    mock_st.sidebar.image = mocker.MagicMock()
    mock_st.dataframe = mocker.MagicMock()
    mock_st.caption = mocker.MagicMock()
    mock_st.text_area = mocker.MagicMock(return_value="")
    mock_st.slider = mocker.MagicMock(return_value=1) # For dashboard slider
    mock_st.metric = mocker.MagicMock()
    mock_st.download_button = mocker.MagicMock()
    mock_st.stop = mocker.MagicMock() # To test st.stop() calls
    mock_st.rerun = mocker.MagicMock() # To test st.rerun() calls

    # Patch st.form to capture its body and ensure submit buttons work
    def mock_form(key, clear_on_submit=False):
        # This will return a context manager for `with st.form(...)`
        return MagicMock(__enter__=lambda self: self, __exit__=lambda self, exc_type, exc_val, exc_tb: None)

    mock_st.form = mocker.MagicMock(side_effect=mock_form)


    # Use patch.dict to mock sys.modules for 'streamlit'
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st

@pytest.fixture
def mock_uploaded_file(mocker):
    """
    Mocks a Streamlit uploaded file object with content.
    """
    def _mock_file(name: str, content: str | bytes, file_type: str):
        mock_file = mocker.MagicMock()
        mock_file.name = name
        mock_file.type = file_type
        if isinstance(content, str):
            mock_file.getbuffer.return_value = io.BytesIO(content.encode('utf-8'))
        else:
            mock_file.getbuffer.return_value = io.BytesIO(content)
        mock_file.getvalue.return_value = mock_file.getbuffer().getvalue() # For PyPDF2
        return mock_file
    return _mock_file