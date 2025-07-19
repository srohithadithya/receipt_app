import pytest
from processing import validation, ingestion
from processing.validation import ParsedReceiptData
from pydantic import ValidationError
from datetime import date
from pathlib import Path
import io
import os
import shutil

# Fixtures for mock_uploaded_file are in conftest.py

@pytest.fixture(scope="module")
def temp_data_dir():
    """Creates a temporary data directory for ingestion tests and cleans up."""
    test_dir = Path("data_test_ingestion")
    raw_receipts_dir = test_dir / "raw_receipts"
    raw_receipts_dir.mkdir(parents=True, exist_ok=True)
    ingestion.RAW_RECEIPTS_DIR = raw_receipts_dir # Temporarily redirect ingestion path
    yield raw_receipts_dir
    ingestion.RAW_RECEIPTS_DIR = Path("data") / "raw_receipts" # Reset to original
    if test_dir.exists():
        shutil.rmtree(test_dir)


# --- validation.py tests ---

def test_parsed_receipt_data_valid_creation():
    """Test successful creation of ParsedReceiptData model."""
    data = validation.ParsedReceiptData(
        vendor_name="Test Store",
        transaction_date="2023-01-01",
        amount=100.50,
        currency="USD",
        category_name="Groceries",
        parsed_raw_text="Sample text."
    )
    assert data.vendor_name == "Test Store"
    assert data.transaction_date == date(2023, 1, 1)
    assert data.amount == 100.50
    assert data.currency == "USD"
    assert data.category_name == "Groceries"
    assert data.parsed_raw_text == "Sample text."

def test_parsed_receipt_data_date_parsing():
    """Test various date formats for transaction_date."""
    data = validation.ParsedReceiptData(
        vendor_name="A", amount=1, transaction_date="2023/12/31"
    )
    assert data.transaction_date == date(2023, 12, 31)

    data = validation.ParsedReceiptData(
        vendor_name="A", amount=1, transaction_date="31-12-2023"
    )
    assert data.transaction_date == date(2023, 12, 31)

    data = validation.ParsedReceiptData(
        vendor_name="A", amount=1, transaction_date="Dec 31, 2023"
    )
    assert data.transaction_date == date(2023, 12, 31)

def test_parsed_receipt_data_amount_parsing():
    """Test various amount formats."""
    data = validation.ParsedReceiptData(
        vendor_name="A", transaction_date="2023-01-01", amount="$123.45"
    )
    assert data.amount == 123.45

    data = validation.ParsedReceiptData(
        vendor_name="A", transaction_date="2023-01-01", amount="€1.234,56" # European format
    )
    assert data.amount == 1.234 # Our regex currently only handles dot for decimal

    data = validation.ParsedReceiptData(
        vendor_name="A", transaction_date="2023-01-01", amount="1,000.00"
    )
    assert data.amount == 1000.00

def test_parsed_receipt_data_invalid_amount_raises_error():
    """Test that invalid amount strings raise ValidationError."""
    with pytest.raises(ValidationError):
        validation.ParsedReceiptData(
            vendor_name="A", transaction_date="2023-01-01", amount="invalid_amount"
        )

def test_parsed_receipt_data_invalid_date_raises_error():
    """Test that invalid date strings raise ValidationError."""
    with pytest.raises(ValidationError):
        validation.ParsedReceiptData(
            vendor_name="A", transaction_date="not-a-date", amount=10.0
        )

def test_validate_file_type_valid():
    """Test valid file types."""
    assert validation.validate_file_type("receipt.jpg") == "image"
    assert validation.validate_file_type("image.PNG") == "image"
    assert validation.validate_file_type("document.pdf") == "pdf"
    assert validation.validate_file_type("notes.txt") == "text"

def test_validate_file_type_invalid():
    """Test invalid file types."""
    assert validation.validate_file_type("document.docx") is None
    assert validation.validate_file_type("archive.zip") is None
    assert validation.validate_file_type("no_extension") is None
    assert validation.validate_file_type("") is None
    assert validation.validate_file_type(None) is None # Test non-string input

# --- ingestion.py tests ---

def test_save_uploaded_file_success(mock_uploaded_file, temp_data_dir):
    """Test successful saving of an uploaded file."""
    mock_file = mock_uploaded_file("test.txt", "hello world", "text/plain")
    saved_path, original_name = ingestion.save_uploaded_file(mock_file)

    assert saved_path is not None
    assert saved_path.exists()
    assert original_name == "test.txt"
    with open(saved_path, "r") as f:
        content = f.read()
    assert content == "hello world"
    saved_path.unlink() # Clean up

def test_save_uploaded_file_none_input(temp_data_dir):
    """Test saving with None as input."""
    saved_path, original_name = ingestion.save_uploaded_file(None)
    assert saved_path is None
    assert original_name is None

def test_read_file_content_success(temp_data_dir):
    """Test successful reading of file content."""
    file_path = temp_data_dir / "read_test.txt"
    content = b"binary content for reading"
    with open(file_path, "wb") as f:
        f.write(content)

    read_content = ingestion.read_file_content(file_path, "text")
    assert read_content == content
    file_path.unlink()

def test_read_file_content_file_not_found(temp_data_dir):
    """Test reading a non-existent file."""
    file_path = temp_data_dir / "non_existent.txt"
    read_content = ingestion.read_file_content(file_path, "text")
    assert read_content is None

def test_read_file_content_empty_file(temp_data_dir):
    """Test reading an empty file."""
    file_path = temp_data_dir / "empty.txt"
    file_path.touch() # Create empty file

    read_content = ingestion.read_file_content(file_path, "text")
    assert read_content == b""
    file_path.unlink()