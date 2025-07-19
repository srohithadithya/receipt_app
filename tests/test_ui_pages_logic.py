import pytest
import pandas as pd
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from ui.auth_manager import AuthManager
from ui.pages import dashboard, upload, records
from database import crud
from processing import ingestion, parsing, aggregation
from processing.validation import ParsedReceiptData
from utils import helpers
from utils.errors import FileProcessingError, ParsingError


# Fixtures for mock_streamlit, db_session, create_test_user, create_sample_receipts are in conftest.py

# --- Dashboard Page Logic Tests ---

def test_dashboard_page_no_receipts(mock_streamlit, db_session, create_test_user):
    """Test dashboard display when user has no receipts."""
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = create_test_user.id
    mock_streamlit.session_state.username = create_test_user.username

    # Ensure no receipts are returned
    mocker = MagicMock()
    mocker.patch('database.crud.get_receipts_by_user', return_value=[])
    mocker.patch('database.crud.get_all_vendors', return_value=[])
    mocker.patch('database.crud.get_all_categories', return_value=[])

    with patch.multiple(crud,
                        get_receipts_by_user=mocker.get_receipts_by_user,
                        get_all_vendors=mocker.get_all_vendors,
                        get_all_categories=mocker.get_all_categories):
        dashboard.show_dashboard_page()

    mock_streamlit.title.assert_called_once()
    mock_streamlit.info.assert_called_once_with("No receipts uploaded yet. Please upload some to see insights!")
    mock_streamlit.plotly_chart.assert_not_called() # No charts should be displayed

def test_dashboard_page_with_receipts(mock_streamlit, db_session, create_sample_receipts, mocker):
    """Test dashboard display when user has receipts."""
    user = create_sample_receipts[0].owner
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id
    mock_streamlit.session_state.username = user.username

    # Mock DB calls
    mocker.patch('database.crud.get_receipts_by_user', return_value=create_sample_receipts)
    mocker.patch('database.crud.get_all_vendors', return_value=[create_sample_receipts[0].vendor])
    mocker.patch('database.crud.get_all_categories', return_value=[create_sample_receipts[0].category])

    # Mock aggregation and plotting functions to ensure they are called
    mocker.patch('processing.aggregation.calculate_expenditure_summary', return_value=(1000.0, 100.0, 90.0, [80.0]))
    mocker.patch('processing.aggregation.get_vendor_frequency', return_value=pd.DataFrame({'vendor_name': ['A'], 'count': [1]}))
    mocker.patch('processing.aggregation.get_monthly_spend_trend', return_value=pd.DataFrame({'month': ['2023-01'], 'total_amount': [100.0]}))
    mocker.patch('ui.plots.plot_bar_chart', return_value=MagicMock())
    mocker.patch('ui.plots.plot_pie_chart', return_value=MagicMock())
    mocker.patch('ui.plots.plot_line_chart', return_value=MagicMock())
    mocker.patch('ui.components.display_info_card')


    dashboard.show_dashboard_page()

    mock_streamlit.title.assert_called_once()
    mock_streamlit.plotly_chart.call_count == 3 # Should call for bar, pie, line charts
    aggregation.calculate_expenditure_summary.assert_called_once()
    aggregation.get_vendor_frequency.assert_called_once()
    aggregation.get_monthly_spend_trend.assert_called_once()
    mock_streamlit.info.assert_not_called() # Should not show 'no receipts' message


# --- Upload Page Logic Tests ---

def test_upload_page_successful_single_file_processing(mock_streamlit, mocker, db_session, create_test_user, mock_uploaded_file, tmp_path):
    """Test successful processing of a single uploaded file."""
    user = create_test_user
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id

    mock_file = mock_uploaded_file("receipt.txt", "Vendor: Test\nDate: 2023-01-01\nAmount: $100.00", "text/plain")
    mocker.patch.object(mock_streamlit, 'file_uploader', return_value=[mock_file])

    # Mock file system interaction and parsing
    mocker.patch('processing.ingestion.save_uploaded_file', return_value=(tmp_path / "receipt.txt", "receipt.txt"))
    mocker.patch('processing.parsing.parse_document', return_value=ParsedReceiptData(
        vendor_name="ParsedVendor", transaction_date="2023-01-01", amount=100.0, currency="USD"
    ))
    mocker.patch('database.crud.create_receipt', return_value=MagicMock(id=1, vendor_name="ParsedVendor", amount=100.0))

    upload.show_upload_page()

    ingestion.save_uploaded_file.assert_called_once_with(mock_file)
    parsing.parse_document.assert_called_once_with(tmp_path / "receipt.txt", "receipt.txt")
    crud.create_receipt.assert_called_once()
    mock_streamlit.success.assert_called_once()
    mock_streamlit.rerun.assert_not_called() # Rerun only if button clicked

def test_upload_page_file_processing_failure(mock_streamlit, mocker, db_session, create_test_user, mock_uploaded_file, tmp_path):
    """Test handling of file processing errors during upload."""
    user = create_test_user
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id

    mock_file = mock_uploaded_file("bad_receipt.jpg", b"invalid_image_data", "image/jpeg")
    mocker.patch.object(mock_streamlit, 'file_uploader', return_value=[mock_file])

    mocker.patch('processing.ingestion.save_uploaded_file', return_value=(tmp_path / "bad_receipt.jpg", "bad_receipt.jpg"))
    # Simulate a parsing error
    mocker.patch('processing.parsing.parse_document', side_effect=ParsingError("OCR failed"))

    upload.show_upload_page()

    parsing.parse_document.assert_called_once()
    crud.create_receipt.assert_not_called() # Should not call if parsing fails
    mock_streamlit.error.assert_called_once()
    assert "OCR failed" in mock_streamlit.error.call_args[0][0]


# --- Records Page Logic Tests ---

def test_records_page_no_receipts(mock_streamlit, db_session, create_test_user):
    """Test records page display when user has no receipts."""
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = create_test_user.id

    mocker = MagicMock()
    mocker.patch('database.crud.get_receipts_by_user', return_value=[])
    mocker.patch('database.crud.get_all_vendors', return_value=[])
    mocker.patch('database.crud.get_all_categories', return_value=[])

    with patch.multiple(crud,
                        get_receipts_by_user=mocker.get_receipts_by_user,
                        get_all_vendors=mocker.get_all_vendors,
                        get_all_categories=mocker.get_all_categories):
        records.show_records_page()

    mock_streamlit.title.assert_called_once()
    mock_streamlit.info.assert_called_once_with("No records found for your account. Start by uploading receipts!")
    mock_streamlit.dataframe.assert_not_called()

def test_records_page_with_receipts_and_sorting(mock_streamlit, mocker, db_session, create_sample_receipts):
    """Test records page display with data and sorting functionality."""
    user = create_sample_receipts[0].owner
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id

    # Mock DB calls
    mocker.patch('database.crud.get_receipts_by_user', return_value=create_sample_receipts)
    mocker.patch('database.crud.get_all_vendors', return_value=[r.vendor for r in create_sample_receipts if r.vendor])
    mocker.patch('database.crud.get_all_categories', return_value=[r.category for r in create_sample_receipts if r.category])

    # Mock Streamlit UI interactions for sorting
    mocker.patch.object(mock_streamlit.sidebar, 'selectbox', return_value="Amount")
    mocker.patch.object(mock_streamlit.sidebar, 'radio', return_value="Ascending")

    records.show_records_page()

    mock_streamlit.dataframe.assert_called_once()
    displayed_df = mock_streamlit.dataframe.call_args[0][0]
    # Check if sorting was applied (e.g., by amount ascending)
    assert displayed_df['amount'].is_monotonic_increasing

def test_records_page_update_record(mock_streamlit, mocker, db_session, create_sample_receipts):
    """Test updating a record via the records page form."""
    user = create_sample_receipts[0].owner
    first_receipt = create_sample_receipts[0]
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id

    # Mock DB and other dependencies
    mocker.patch('database.crud.get_receipts_by_user', return_value=create_sample_receipts)
    mocker.patch('database.crud.get_all_vendors', return_value=[mocker.MagicMock(id=first_receipt.vendor_id, name=first_receipt.vendor.name)])
    mocker.patch('database.crud.get_all_categories', return_value=[mocker.MagicMock(id=first_receipt.category_id, name=first_receipt.category.name)])
    mocker.patch('database.crud.update_receipt', return_value=MagicMock(id=first_receipt.id, amount=200.00))

    # Mock Streamlit UI interactions
    mocker.patch.object(mock_streamlit, 'selectbox', side_effect=[first_receipt.id]) # Select record ID
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', True) # Click update button
    mocker.patch.object(mock_streamlit, 'text_input', side_effect=["NewVendor", "USD", first_receipt.original_filename])
    mocker.patch.object(mock_streamlit, 'number_input', return_value=200.00)
    mocker.patch.object(mock_streamlit, 'date_input', side_effect=[date(2023,1,1), None, None])
    mocker.patch.object(mock_streamlit, 'radio', return_value="Descending") # For sort order

    records.show_records_page()

    crud.update_receipt.assert_called_once()
    call_args = crud.update_receipt.call_args[1]
    assert call_args['receipt_id'] == first_receipt.id
    assert call_args['owner_id'] == user.id
    assert call_args['data']['amount'] == 200.00
    mock_streamlit.success.assert_called_once_with(f"Record ID {first_receipt.id} updated successfully!")
    mock_streamlit.rerun.assert_called_once() # Should rerun after update

def test_records_page_delete_record(mock_streamlit, mocker, db_session, create_sample_receipts):
    """Test deleting a record via the records page form."""
    user = create_sample_receipts[0].owner
    receipt_to_delete = create_sample_receipts[0]
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id

    mocker.patch('database.crud.get_receipts_by_user', return_value=create_sample_receipts)
    mocker.patch('database.crud.get_all_vendors', return_value=[])
    mocker.patch('database.crud.get_all_categories', return_value=[])
    mocker.patch('database.crud.delete_receipt', return_value=True) # Mock successful delete

    mocker.patch.object(mock_streamlit, 'selectbox', side_effect=[receipt_to_delete.id]) # Select record ID
    mocker.patch.object(mock_streamlit.form_submit_button, 'return_value', False) # Don't click update
    mocker.patch.object(mock_streamlit.form_submit_button, 'side_effect', [False, True]) # Mock Update, then Delete
    # Mock the "Confirm Deletion" button after the warning
    mocker.patch.object(mock_streamlit, 'button', return_value=True) # Mock Confirm Deletion button

    records.show_records_page()

    crud.delete_receipt.assert_called_once_with(db_session, receipt_to_delete.id, user.id)
    mock_streamlit.success.assert_called_once_with(f"Record ID {receipt_to_delete.id} deleted successfully.")
    mock_streamlit.rerun.assert_called_once() # Should rerun after delete

def test_records_page_export_csv_json(mock_streamlit, mocker, db_session, create_sample_receipts):
    """Test CSV and JSON export functionality."""
    user = create_sample_receipts[0].owner
    mock_streamlit.session_state.logged_in = True
    mock_streamlit.session_state.user_id = user.id

    mocker.patch('database.crud.get_receipts_by_user', return_value=create_sample_receipts)
    mocker.patch('database.crud.get_all_vendors', return_value=[])
    mocker.patch('database.crud.get_all_categories', return_value=[])
    
    # Mock conversion functions
    mocker.patch('utils.helpers.convert_df_to_csv', return_value="header\n1,2,3")
    mocker.patch('utils.helpers.convert_df_to_json', return_value='[{"data": 1}]')

    records.show_records_page()

    helpers.convert_df_to_csv.assert_called_once()
    helpers.convert_df_to_json.assert_called_once()
    mock_streamlit.download_button.call_count == 2 # Should call download button for CSV and JSON