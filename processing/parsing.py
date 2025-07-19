import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

# Local imports
from processing.ingestion import read_file_content # To get raw bytes for OCR
from processing.ocr_utils import extract_text_from_image, detect_language
from processing.validation import ParsedReceiptData, validate_file_type
from utils.errors import ParsingError, FileProcessingError # Assuming these custom errors exist

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _extract_from_text(text: str, file_type: str = 'text') -> Dict[str, Any]:
    """
    Extracts structured data (vendor, date, amount, currency, category, billing period)
    from a block of text using rule-based (regex) parsing.

    :param text: The raw text content of the receipt/bill.
    :param file_type: The type of file (e.g., 'image', 'pdf', 'text'), used for context.
    :return: A dictionary of extracted fields.
    """
    extracted_data = {}
    lower_text = text.lower()

    # 1. Extract Amount and Currency
    # Prioritize patterns with currency symbols first, then floating point numbers
    # Regex for currency symbols ($€£₹) followed by numbers
    amount_regex_strong_currency = r"(?:total|amount|sum|grand total|bill|paid)\s*[:=]?\s*([$€£₹]\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)"
    amount_regex_iso_currency = r"((?:USD|EUR|GBP|INR|CAD|AUD)\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)"
    amount_regex_floating = r"(?<!\d)(?:total|amount|sum|grand total|bill|paid|due)\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)(?!\d)" # Captures the number only

    currency_map = {
        '$': 'USD', '€': 'EUR', '£': 'GBP', '₹': 'INR',
        'usd': 'USD', 'eur': 'EUR', 'gbp': 'GBP', 'inr': 'INR'
    }

    match_currency_symbol = re.search(amount_regex_strong_currency, lower_text, re.IGNORECASE)
    match_iso_currency = re.search(amount_regex_iso_currency, lower_text, re.IGNORECASE)

    amount = None
    currency = "USD" # Default currency

    if match_currency_symbol:
        value_str = match_currency_symbol.group(1).replace(',', '')
        symbol = value_str[0]
        if symbol in currency_map:
            currency = currency_map[symbol]
            amount = float(re.sub(r"[^0-9.]", "", value_str)) # Remove non-numeric except dot
        logger.debug(f"Amount (strong currency) found: {amount} {currency}")
    elif match_iso_currency:
        value_str = match_iso_currency.group(1).replace(',', '')
        iso_code = value_str[:3].upper()
        if iso_code in currency_map:
            currency = currency_map[iso_code]
            amount = float(re.sub(r"[^0-9.]", "", value_str))
        logger.debug(f"Amount (ISO currency) found: {amount} {currency}")
    else:
        # Fallback to general floating point number if no currency symbol found
        matches_floating = re.findall(amount_regex_floating, lower_text, re.IGNORECASE)
        if matches_floating:
            # Try to pick the last found number as it's often the total
            try:
                potential_amount = float(matches_floating[-1].replace(',', ''))
                # Basic sanity check for amount (e.g., usually not extremely small for totals)
                if potential_amount > 0.1:
                    amount = potential_amount
            except ValueError:
                pass
        logger.debug(f"Amount (floating point fallback) found: {amount}")

    if amount is not None:
        extracted_data['amount'] = amount
        extracted_data['currency'] = currency # Keep default if not detected

    # 2. Extract Date
    # Common date formats (YYYY-MM-DD, DD-MM-YYYY, YYYY/MM/DD, DD/MM/YYYY, Month DD, YYYY)
    date_patterns = [
        r'\d{4}[-/]\d{2}[-/]\d{2}',            # YYYY-MM-DD or YYYY/MM/DD
        r'\d{2}[-/]\d{2}[-/]\d{4}',            # DD-MM-YYYY or DD/MM-YYYY
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}[,\s]+\d{4}', # Mon DD, YYYY
        r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}' # DD Mon YYYY
    ]
    transaction_date = None
    for pattern in date_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            date_str = match.group(0).replace('.', '').replace(',', '')
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y', '%b %d %Y', '%B %d %Y', '%d %b %Y', '%d %B %Y'):
                try:
                    transaction_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            if transaction_date:
                break
    if transaction_date:
        extracted_data['transaction_date'] = transaction_date
        logger.debug(f"Transaction date found: {transaction_date}")

    # 3. Extract Vendor / Biller (Rule-based, can be expanded with known vendor lists)
    vendor_keywords = [
        r'invoice from\s*(.+)',
        r'bill from\s*(.+)',
        r'receipt from\s*(.+)',
        r'sold by\s*(.+)',
        r'purchased from\s*(.+)',
        r'billed by\s*(.+)',
        r'(?:vendor|biller|store):\s*(.+)',
        r'company:\s*(.+)'
    ]
    vendor_name = None
    for pattern in vendor_keywords:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            # Simple heuristic: take the first line after the keyword, up to a common separator
            potential_vendor = match.group(1).split('\n')[0].strip()
            # Clean up potential trailing info or common junk
            potential_vendor = re.split(r'[,;]\s*|phone|tel|email|website|www\.', potential_vendor, 1)[0].strip()
            if potential_vendor and len(potential_vendor) > 2 and len(potential_vendor) < 100: # Basic length check
                vendor_name = potential_vendor
                break
    
    # Fallback: Look for company names/common patterns at the beginning of the document
    if not vendor_name:
        # Simple heuristic: often the first few lines contain the vendor name
        first_lines = text.split('\n')[:5]
        for line in first_lines:
            line = line.strip()
            if len(line) > 5 and len(line) < 50 and not re.search(r'\d', line): # Likely a name, not date/amount
                # Avoid lines that look like addresses or dates if possible
                if not any(k in line.lower() for k in ['date', 'total', 'amount', 'street', 'road', 'avenue', 'p.o. box']):
                     vendor_name = line
                     break
    
    if vendor_name:
        extracted_data['vendor_name'] = vendor_name.title() # Capitalize words for consistency
        logger.debug(f"Vendor name found: {vendor_name}")

    # 4. Extract Category (Optional, based on keywords or known vendors)
    # This is a very basic example; a more robust system would use a lookup table for vendors
    # or more sophisticated NLP.
    category_map = {
        'grocer': 'Groceries', 'supermart': 'Groceries', 'hypermarket': 'Groceries',
        'electricity': 'Utilities', 'power bill': 'Utilities', 'light bill': 'Utilities',
        'internet': 'Utilities', 'telecom': 'Utilities', 'broadband': 'Utilities',
        'water bill': 'Utilities',
        'restaurant': 'Dining', 'cafe': 'Dining', 'food': 'Dining',
        'petrol': 'Transport', 'gas station': 'Transport', 'fuel': 'Transport',
        'pharmacy': 'Health', 'medicine': 'Health',
        'fashion': 'Shopping', 'clothing': 'Shopping',
        'online store': 'Shopping' # Generic
    }
    extracted_data['category_name'] = None
    for keyword, category in category_map.items():
        if keyword in lower_text or (vendor_name and keyword in vendor_name.lower()):
            extracted_data['category_name'] = category
            logger.debug(f"Category found: {category}")
            break

    # 5. Extract Billing Period (for bills)
    billing_period_regex = r"(?:billing|service)\s*period[:=]?\s*(\d{2}[-/]\d{2}[-/]\d{4}\s*to\s*\d{2}[-/]\d{2}[-/]\d{4})"
    match = re.search(billing_period_regex, lower_text, re.IGNORECASE)
    if match:
        period_str = match.group(1)
        dates = re.findall(r'\d{2}[-/]\d{2}[-/]\d{4}', period_str)
        if len(dates) == 2:
            try:
                start_date = datetime.strptime(dates[0], '%d-%m-%Y').date()
                end_date = datetime.strptime(dates[1], '%d-%m-%Y').date()
                extracted_data['billing_period_start'] = start_date
                extracted_data['billing_period_end'] = end_date
                logger.debug(f"Billing period found: {start_date} to {end_date}")
            except ValueError:
                pass

    return extracted_data

def parse_document(file_path: Path, original_filename: str) -> Optional[ParsedReceiptData]:
    """
    Main function to parse a document (image, PDF, or text) and extract structured data.
    Orchestrates ingestion, OCR (if needed), text extraction, rule-based parsing,
    and Pydantic validation.

    :param file_path: Path to the stored file.
    :param original_filename: The original filename for context.
    :return: A ParsedReceiptData Pydantic model instance if successful, else None.
    :raises FileProcessingError: If the file cannot be read or its type is unsupported.
    :raises ParsingError: If data extraction or validation fails.
    """
    file_type = validate_file_type(original_filename)
    if not file_type:
        raise FileProcessingError(f"Unsupported file type for {original_filename}")

    raw_content_bytes = read_file_content(file_path, file_type)
    if raw_content_bytes is None:
        raise FileProcessingError(f"Could not read content from {file_path}")

    extracted_text = None
    if file_type == 'text':
        try:
            extracted_text = raw_content_bytes.decode('utf-8')
            logger.info(f"Read text directly from {original_filename}.")
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode text file {original_filename}: {e}")
            raise FileProcessingError(f"Failed to decode text file: {e}")
    elif file_type in ['image', 'pdf']:
        # For PDF, first extract text directly if possible (PyPDF2), then fallback to OCR image layers
        if file_type == 'pdf':
            # This is a simple text extraction. More advanced PDF parsing might be needed.
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file_path)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() or ""
                if pdf_text.strip():
                    extracted_text = pdf_text
                    logger.info(f"Extracted text directly from PDF {original_filename}.")
                else:
                    logger.info(f"No text found directly in PDF {original_filename}, attempting OCR.")
            except Exception as e:
                logger.warning(f"Error extracting text directly from PDF {original_filename}: {e}. Falling back to OCR.")
        
        if not extracted_text or not extracted_text.strip(): # If PDF had no text, or it's an image
            try:
                # Basic language detection (from ocr_utils)
                detected_lang = detect_language(raw_content_bytes)
                ocr_lang = detected_lang if detected_lang else 'eng' # Default to English
                
                extracted_text = extract_text_from_image(raw_content_bytes, lang=ocr_lang)
                if not extracted_text:
                    raise ParsingError(f"OCR failed to extract text from {original_filename}.")
                logger.info(f"Extracted text from {original_filename} using OCR (lang={ocr_lang}).")
            except Exception as e:
                logger.error(f"OCR processing failed for {original_filename}: {e}")
                raise ParsingError(f"OCR processing failed: {e}")
    
    if not extracted_text or not extracted_text.strip():
        raise ParsingError(f"No meaningful text extracted from {original_filename}.")

    # Perform rule-based extraction
    extracted_fields = _extract_from_text(extracted_text, file_type)
    extracted_fields['parsed_raw_text'] = extracted_text # Store raw text in the final model

    # Validate with Pydantic model
    try:
        validated_data = ParsedReceiptData(**extracted_fields)
        logger.info(f"Successfully parsed and validated data for {original_filename}.")
        return validated_data
    except Exception as e:
        logger.error(f"Validation failed for {original_filename} with extracted fields: {extracted_fields}. Error: {e}")
        raise ParsingError(f"Data validation failed after extraction: {e}")

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    # Create dummy files for testing
    temp_dir = Path("data/temp_parsing_test")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Dummy Text File
    dummy_txt_content = """
    Invoice No: 12345
    Date: 2023-07-15
    Vendor: FreshMart Groceries
    Item: Apples 2kg @ 2.50 = 5.00
    Item: Milk 1 unit @ 3.00 = 3.00
    Total Amount: $8.00 USD
    Category: Food
    """
    dummy_txt_path = temp_dir / "invoice.txt"
    with open(dummy_txt_path, "w") as f:
        f.write(dummy_txt_content)

    # Dummy Image File (requires Pillow, OpenCV, Tesseract)
    # For a realistic test, replace with a scanned receipt image.
    dummy_img_path = temp_dir / "receipt_image.png"
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (500, 200), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            font_path = "arial.ttf" # Adjust path based on your OS
            fnt = ImageFont.truetype(font_path, 20)
        except IOError:
            fnt = ImageFont.load_default()
            logger.warning("Could not load Arial.ttf for demo, using default font.")

        d.text((50,50), "VENDOR: Electra Power Co.", fill=(0,0,0), font=fnt)
        d.text((50,80), "Date: 10/06/2023", fill=(0,0,0), font=fnt)
        d.text((50,110), "Amount Due: ₹ 750.25", fill=(0,0,0), font=fnt)
        d.text((50,140), "Billing Period: 01-05-2023 to 31-05-2023", fill=(0,0,0), font=fnt)
        img.save(dummy_img_path)
    except ImportError:
        print("Pillow, OpenCV, Tesseract-OCR required for image test. Skipping image generation.")
        dummy_img_path = None # Set to None if PIL not available

    # Test TXT file parsing
    print("\n--- Testing TXT File Parsing ---")
    try:
        parsed_data_txt = parse_document(dummy_txt_path, "invoice.txt")
        print(f"Parsed TXT Data: {parsed_data_txt.dict()}")
    except (FileProcessingError, ParsingError) as e:
        print(f"Error parsing TXT file: {e}")

    # Test Image file parsing (if image was created)
    if dummy_img_path and dummy_img_path.exists():
        print("\n--- Testing Image File Parsing ---")
        try:
            parsed_data_img = parse_document(dummy_img_path, "receipt_image.png")
            print(f"Parsed Image Data: {parsed_data_img.dict()}")
        except (FileProcessingError, ParsingError) as e:
            print(f"Error parsing Image file: {e}. Make sure Tesseract is installed and in PATH.")

    # Clean up dummy files
    if dummy_txt_path.exists():
        dummy_txt_path.unlink()
    if dummy_img_path and dummy_img_path.exists():
        dummy_img_path.unlink()
    if temp_dir.exists():
        temp_dir.rmdir()
    print("\nCleaned up test files and directories.")