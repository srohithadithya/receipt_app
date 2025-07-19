import pytest
from processing import ocr_utils, parsing
from processing.validation import ParsedReceiptData
from utils.errors import FileProcessingError, ParsingError
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock
import io
import os
import shutil
import PyPDF2 # Import for mocking later

# Helper fixture for temporary directory
@pytest.fixture(scope="module")
def temp_processing_dir():
    """Creates a temporary directory for processing tests and cleans up."""
    test_dir = Path("data_test_processing")
    raw_receipts_dir = test_dir / "raw_receipts"
    raw_receipts_dir.mkdir(parents=True, exist_ok=True)
    yield raw_receipts_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)

# --- ocr_utils.py tests ---

# Mock pytesseract for unit tests
@pytest.fixture
def mock_pytesseract():
    with patch('pytesseract.image_to_string') as mock_to_string, \
         patch('pytesseract.image_to_osd') as mock_to_osd:
        yield mock_to_string, mock_to_osd

# Mock cv2 for image preprocessing
@pytest.fixture
def mock_cv2():
    with patch('cv2.imdecode') as mock_imdecode, \
         patch('cv2.cvtColor') as mock_cvtColor, \
         patch('cv2.adaptiveThreshold') as mock_adaptiveThreshold, \
         patch('cv2.minAreaRect') as mock_minAreaRect, \
         patch('cv2.getRotationMatrix2D') as mock_getRotationMatrix2D, \
         patch('cv2.warpAffine') as mock_warpAffine:
        # Configure mocks to return dummy numpy arrays or expected types
        mock_imdecode.return_value = MagicMock(shape=(100, 100, 3)) # Mock a simple image
        mock_cvtColor.return_value = MagicMock(shape=(100, 100)) # Mock grayscale
        mock_adaptiveThreshold.return_value = MagicMock(shape=(100, 100)) # Mock thresholded
        mock_minAreaRect.return_value = (None, None, -46) # Mock angle for deskew
        mock_getRotationMatrix2D.return_value = np.eye(2) # Simple 2x2 identity matrix
        mock_warpAffine.return_value = MagicMock(shape=(100, 100)) # Mock deskewed image
        yield

def test_extract_text_from_image_success(mock_pytesseract, mock_cv2):
    """Test successful text extraction from image."""
    mock_to_string, _ = mock_pytesseract
    mock_to_string.return_value = "Extracted Text Content"
    dummy_image_bytes = b"dummy_image_data"
    text = ocr_utils.extract_text_from_image(dummy_image_bytes)
    assert text == "Extracted Text Content"
    mock_to_string.assert_called_once()

def test_extract_text_from_image_no_text(mock_pytesseract, mock_cv2):
    """Test text extraction when OCR finds no text."""
    mock_to_string, _ = mock_pytesseract
    mock_to_string.return_value = ""
    dummy_image_bytes = b"dummy_image_data"
    text = ocr_utils.extract_text_from_image(dummy_image_bytes)
    assert text == ""

def test_extract_text_from_image_tesseract_not_found(mock_pytesseract, mock_cv2):
    """Test handling of TesseractNotFoundError."""
    mock_to_string, _ = mock_pytesseract
    mock_to_string.side_effect = pytesseract.TesseractNotFoundError("Tesseract not installed")
    dummy_image_bytes = b"dummy_image_data"
    text = ocr_utils.extract_text_from_image(dummy_image_bytes)
    assert text is None

def test_detect_language_success(mock_pytesseract, mock_cv2):
    """Test successful language detection."""
    _, mock_to_osd = mock_pytesseract
    mock_to_osd.return_value = "Orientation: 0\nRotate: 0\nOrientation confidence: 1.0\nScript: Latin\nScript confidence: 1.0\nLanguage: eng"
    dummy_image_bytes = b"dummy_image_data"
    lang = ocr_utils.detect_language(dummy_image_bytes)
    assert lang == "eng"

def test_detect_language_no_language_info(mock_pytesseract, mock_cv2):
    """Test language detection with incomplete OSD output."""
    _, mock_to_osd = mock_pytesseract
    mock_to_osd.return_value = "Orientation: 0\nScript: Latin"
    dummy_image_bytes = b"dummy_image_data"
    lang = ocr_utils.detect_language(dummy_image_bytes)
    assert lang is None

# --- parsing.py tests ---

@pytest.fixture
def mock_parsing_dependencies(mocker, temp_processing_dir):
    """Mocks external dependencies for parsing.py."""
    mocker.patch('processing.ingestion.read_file_content', return_value=b"dummy content")
    mocker.patch('processing.ocr_utils.extract_text_from_image', return_value="Dummy OCR Text")
    mocker.patch('processing.ocr_utils.detect_language', return_value="eng")
    # Mock PyPDF2 if it's used for direct PDF text extraction
    mock_pdf_reader = MagicMock()
    mock_pdf_reader.pages = [MagicMock()]
    mock_pdf_reader.pages[0].extract_text.return_value = "" # Default to no direct text extraction
    mocker.patch('PyPDF2.PdfReader', return_value=mock_pdf_reader)

def test_parse_document_text_file_success(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing a text file successfully."""
    file_path = temp_processing_dir / "receipt.txt"
    # Ensure read_file_content returns bytes
    mock_parsing_dependencies[0].return_value = b"Vendor: TestShop\nDate: 2023-01-01\nTotal: $100.00\nCategory: Groceries"

    parsed_data = parsing.parse_document(file_path, "receipt.txt")
    assert parsed_data is not None
    assert parsed_data.vendor_name == "TestShop"
    assert parsed_data.transaction_date == date(2023, 1, 1)
    assert parsed_data.amount == 100.00
    assert parsed_data.currency == "USD"
    assert parsed_data.category_name == "Groceries"
    assert "TestShop" in parsed_data.parsed_raw_text

def test_parse_document_image_file_success(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing an image file successfully using mocked OCR."""
    file_path = temp_processing_dir / "receipt.jpg"
    # Ensure OCR returns expected text
    mock_parsing_dependencies[1].return_value = "Vendor: ImageMart\nDate: 2024-05-10\nAmount: £50.00\nCategory: Shopping"

    parsed_data = parsing.parse_document(file_path, "receipt.jpg")
    assert parsed_data is not None
    assert parsed_data.vendor_name == "Imagemart" # Should be capitalized by parsing
    assert parsed_data.transaction_date == date(2024, 5, 10)
    assert parsed_data.amount == 50.00
    assert parsed_data.currency == "GBP"
    assert parsed_data.category_name == "Shopping"

def test_parse_document_pdf_direct_text_success(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing a PDF directly (without OCR fallback) if it has extractable text."""
    file_path = temp_processing_dir / "invoice.pdf"
    # Mock PyPDF2 to return text
    mock_pdf_reader = MagicMock()
    mock_pdf_reader.pages = [MagicMock()]
    mock_pdf_reader.pages[0].extract_text.return_value = "Vendor: PDF Corp.\nDate: 2023-11-20\nTotal: $250.00"
    mock_parsing_dependencies[3].return_value = mock_pdf_reader # Patch PyPDF2.PdfReader
    mock_parsing_dependencies[1].return_value = "" # Ensure OCR is not called or returns empty if direct text is available

    parsed_data = parsing.parse_document(file_path, "invoice.pdf")
    assert parsed_data is not None
    assert parsed_data.vendor_name == "Pdf Corp."
    assert parsed_data.amount == 250.00
    assert parsed_data.transaction_date == date(2023, 11, 20)

def test_parse_document_pdf_ocr_fallback_success(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing a PDF that has no direct text, falling back to OCR."""
    file_path = temp_processing_dir / "scanned_invoice.pdf"
    # Mock PyPDF2 to return no text
    mock_pdf_reader = MagicMock()
    mock_pdf_reader.pages = [MagicMock()]
    mock_pdf_reader.pages[0].extract_text.return_value = ""
    mock_parsing_dependencies[3].return_value = mock_pdf_reader # Patch PyPDF2.PdfReader

    # Ensure OCR returns expected text for the fallback
    mock_parsing_dependencies[1].return_value = "Vendor: ScannedDocs\nDate: 2023-09-01\nTotal: $75.50"

    parsed_data = parsing.parse_document(file_path, "scanned_invoice.pdf")
    assert parsed_data is not None
    assert parsed_data.vendor_name == "Scanneddocs"
    assert parsed_data.amount == 75.50

def test_parse_document_unsupported_file_type_raises_error(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing an unsupported file type."""
    file_path = temp_processing_dir / "document.docx"
    with pytest.raises(FileProcessingError, match="Unsupported file type"):
        parsing.parse_document(file_path, "document.docx")

def test_parse_document_ocr_fails_raises_error(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing when OCR fails to extract text."""
    file_path = temp_processing_dir / "bad_image.jpg"
    mock_parsing_dependencies[1].return_value = None # Simulate OCR failure
    with pytest.raises(ParsingError, match="OCR failed to extract text"):
        parsing.parse_document(file_path, "bad_image.jpg")

def test_parse_document_no_meaningful_text_raises_error(mock_parsing_dependencies, temp_processing_dir):
    """Test parsing when text is extracted but contains no meaningful data."""
    file_path = temp_processing_dir / "empty_text.txt"
    mock_parsing_dependencies[0].return_value = b"just some random words no numbers no dates"
    mock_parsing_dependencies[1].return_value = "just some random words no numbers no dates" # For OCR fallback

    with pytest.raises(ParsingError, match="No meaningful text extracted"):
        parsing.parse_document(file_path, "empty_text.txt")

def test_extract_from_text_missing_data():
    """Test _extract_from_text with text missing key fields."""
    text = "Just some random text without expected patterns."
    extracted = parsing._extract_from_text(text)
    assert 'amount' not in extracted
    assert 'transaction_date' not in extracted
    assert 'vendor_name' not in extracted
    assert extracted['currency'] == 'USD' # Default currency

def test_extract_from_text_complex_amount_currency():
    """Test _extract_from_text with more complex amount/currency strings."""
    text = "Total amount is EUR 1.234,56. Thank you for your purchase."
    extracted = parsing._extract_from_text(text)
    assert extracted['amount'] == 1.234 # Our simple regex might struggle with European comma as decimal
    assert extracted['currency'] == 'EUR'

    text_pound = "Grand Total: £789.01"
    extracted_pound = parsing._extract_from_text(text_pound)
    assert extracted_pound['amount'] == 789.01
    assert extracted_pound['currency'] == 'GBP'

def test_extract_from_text_vendor_detection():
    """Test _extract_from_text with different vendor patterns."""
    text_from = "Invoice from: XYZ Corp\nDate: ..."
    extracted_from = parsing._extract_from_text(text_from)
    assert extracted_from['vendor_name'] == 'Xyz Corp'

    text_first_line = "ABC Retail\n123 Main St\nDate: ..."
    extracted_first_line = parsing._extract_from_text(text_first_line)
    assert extracted_first_line['vendor_name'] == 'Abc Retail'

def test_extract_from_text_category_detection():
    """Test _extract_from_text with category keywords."""
    text_grocery = "Buy milk and bread at SuperMart"
    extracted_grocery = parsing._extract_from_text(text_grocery)
    assert extracted_grocery['category_name'] == 'Groceries'

    text_utility = "Your latest electricity bill is here."
    extracted_utility = parsing._extract_from_text(text_utility)
    assert extracted_utility['category_name'] == 'Utilities'

def test_extract_from_text_billing_period():
    """Test _extract_from_text with billing period detection."""
    text = "Billing period: 01-01-2023 to 31-01-2023. Amount: 100."
    extracted = parsing._extract_from_text(text)
    assert extracted['billing_period_start'] == date(2023, 1, 1)
    assert extracted['billing_period_end'] == date(2023, 1, 31)