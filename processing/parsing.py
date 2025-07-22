import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import logging
import PyPDF2
import io # Import io for BytesIO

# Local imports
from processing.ingestion import read_file_content
from processing.ocr_utils import extract_text_from_image, detect_language
from processing.validation import ParsedReceiptData, validate_file_type
from utils.errors import ParsingError, FileProcessingError # Assuming these custom errors exist

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Re-define formats_to_try to be accessible in the module
formats_to_try = [
    "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", # YYYY-MM-DD, DD-MM-YYYY, MM-DD-YYYY
    "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", # YYYY/MM/DD, DD/MM/YYYY, MM/DD/YYYY
    "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y", # YYYY.MM.DD, DD.MM.YYYY, MM.DD.YYYY
    "%b %d, %Y", "%B %d, %Y",            # Jan 01, 2023 / January 01, 2023
    "%d %b %Y", "%d %B %Y",            # 01 Jan 2023 / 01 January 2023
    "%Y%m%d",                           # YYYYMMDD (e.g., 20230115)
    "%y-%m-%d", "%d-%m-%y", # For 2-digit years
    "%y/%m/%d", "%d/%m/%y"
]


def _extract_from_text(text: str, file_type: str = 'text') -> Dict[str, Any]:
    """
    Extracts structured data (vendor, date, amount, currency, category, billing period)
    from a block of text using rule-based (regex) parsing.
    Improved robustness for various receipt formats and OCR noise.

    :param text: The raw text content of the receipt/bill.
    :param file_type: The type of file (e.g., 'image', 'pdf', 'text'), used for context.
    :return: A dictionary of extracted fields.
    """
    extracted_data = {}
    lines = text.split('\n')
    lower_text = text.lower()

    amount_patterns = [
        # Strong indicators for total amounts, allowing for variations in spacing/symbols
        r"(?:total|amount due|grand total|net amount|balance due|total paid|total bill|due amount)\s*[:=]?\s*([$€£₹]\s*[\d,]+\.?\d{0,2})",
        r"([$€£₹]\s*[\d,]+\.?\d{0,2})\s*(?:total|amount|due|paid)", # Amount before keyword
        r"(?:total|amount|sum|grand total|bill|paid|due)\s*[:=]?\s*([\d,]+\.?\d{0,2})", # Generic numbers after keywords
        r"([\d,]+\.?\d{0,2})\s*(?:usd|eur|gbp|inr|cad|aud)", # Numbers before ISO currency
        r"(?:usd|eur|gbp|inr|cad|aud)\s*([\d,]+\.?\d{0,2})" # ISO currency before numbers
    ]

    amount = None
    currency = "INR" # Default currency

    for pattern in amount_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '').strip()
            # Attempt to extract currency symbol/code if present in the matched string
            detected_curr = re.search(r'([$€£₹]|usd|eur|gbp|inr|cad|aud)', value_str, re.IGNORECASE)
            if detected_curr:
                symbol_or_code = detected_curr.group(1).upper()
                if symbol_or_code == '$': currency = 'USD'
                elif symbol_or_code == '€': currency = 'EUR'
                elif symbol_or_code == '£': currency = 'GBP'
                elif symbol_or_code == '₹': currency = 'INR'
                else: currency = symbol_or_code # For ISO codes

            # Clean the number string
            clean_value_str = re.sub(r'[^\d.]', '', value_str) # Keep only digits and dot
            try:
                amount = float(clean_value_str)
                if amount > 0.01 and amount < 1_000_000:
                    break # Found a plausible amount, stop searching
                else:
                    amount = None # Discard implausible amount
            except ValueError:
                amount = None # Keep trying other patterns

    if amount is not None:
        extracted_data['amount'] = amount
        extracted_data['currency'] = currency
        logger.debug(f"Amount found: {amount} {currency}")
    else:
        logger.warning("Could not reliably extract amount.")

    date_patterns = [
        r'\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}',            # DD-MM-YY, DD/MM/YYYY etc.
        r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}',            # YYYY-MM-DD etc.
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}[,\s]+\d{4}', # Mon DD, YYYY
        r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}', # DD Month YYYY
        r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{2}', # DD Mon YY (e.g., 15 Jan 24)
        r'\d{1,2}[-/](?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-/]\d{2,4}', # DD-Mon-YYYY
    ]
    date_keywords = ['date', 'bill date', 'invoice date', 'transaction date', 'sale date', 'paid date', 'issue date']
    transaction_date = None

    for line in lines:
        lower_line = line.lower()
        for keyword in date_keywords:
            if keyword in lower_line:
                for pattern in date_patterns:
                    match = re.search(pattern, lower_line)
                    if match:
                        # Use the global formats_to_try for robust parsing
                        for fmt in formats_to_try:
                            try:
                                transaction_date = datetime.strptime(match.group(0).replace('.', '').replace(',', ''), fmt).date()
                                break
                            except ValueError:
                                continue
                        if transaction_date: break # Found date, break from keyword loop
                if transaction_date: break # Found date, break from line loop
        if transaction_date: break # Found date, break from line loop

    # Fallback: if not found near keyword, search widely
    if not transaction_date:
        for pattern in date_patterns:
            match = re.search(pattern, lower_text)
            if match:
                for fmt in formats_to_try:
                    try:
                        transaction_date = datetime.strptime(match.group(0).replace('.', '').replace(',', ''), fmt).date()
                        break
                    except ValueError:
                        continue
                if transaction_date: break
    
    if transaction_date:
        extracted_data['transaction_date'] = transaction_date
        logger.debug(f"Transaction date found: {transaction_date}")
    else:
        logger.warning("Could not reliably extract transaction date.")

    vendor_patterns = [
        r'invoice from[:\s]*(.+)',
        r'bill from[:\s]*(.+)',
        r'receipt from[:\s]*(.+)',
        r'sold by[:\s]*(.+)',
        r'purchased from[:\s]*(.+)',
        r'billed by[:\s]*(.+)',
        r'(?:vendor|biller|store|company)[:\s]*(.+)'
    ]
    vendor_name = None

    # First, look for strong indicators
    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            potential_vendor = match.group(1).split('\n')[0].strip()
            # Clean up: remove address lines, phone numbers, websites, tax IDs, common corporate suffixes etc.
            potential_vendor = re.split(r'[,;]\s*|phone|tel|email|website|www\.|gst|vat|abn|cin|ltd|inc|co\.|corporation|group|llc|pvt', potential_vendor, 1)[0].strip()
            if potential_vendor and len(potential_vendor) > 2 and len(potential_vendor) < 100:
                vendor_name = potential_vendor
                break
    
    if not vendor_name:
        # Consider the first 5-7 non-empty lines
        top_lines_to_scan = [line.strip() for line in lines if line.strip()][:7] 
        
        for i, line_content in enumerate(top_lines_to_scan):
            if not line_content: continue # Skip empty lines

            # Clean the line a bit
            cleaned_line = line_content.strip()

            # Criteria for a potential vendor name at the top:
            # 1. Not too long, not too short
            # 2. Contains at least one letter
            # 3. Does not look like an address (no common address keywords)
            # 4. Does not look like a date or total line
            # 5. Often starts with an uppercase letter, or is all caps
            # 6. Check for common company suffixes or keywords (e.g., Ltd, Inc, Co, Group, Services)
            # 7. Relax digit check slightly, but avoid lines that are mostly numbers (like phone numbers)
            
            is_address_like = re.search(r'street|road|avenue|po box|p\.o\.|city|state|zip|pin|building|floor|apt|suite|flat|unit', cleaned_line, re.IGNORECASE)
            is_number_heavy = bool(re.search(r'\d{3,}', cleaned_line)) and len(re.findall(r'\d', cleaned_line)) / len(cleaned_line) > 0.3 # More than 30% digits
            is_date_amount_keyword = re.search(r'date|total|amount|invoice|receipt|bill|gst|vat', cleaned_line, re.IGNORECASE)
            is_too_short_or_long = not (3 < len(cleaned_line) < 60) # Adjusted max length

            if (not is_address_like and
                not is_number_heavy and
                not is_date_amount_keyword and
                not is_too_short_or_long and
                (cleaned_line[0].isupper() or cleaned_line.isupper() or len(cleaned_line.split()) > 1)): # Starts with uppercase, or all caps, or multiple words
                
                vendor_name = cleaned_line
                # If we found a plausible candidate very early, prioritize it
                if i == 0 and not is_number_heavy: # Very first line is often the main name
                    break
                elif i < 3 and len(cleaned_line.split()) < 5: # Short, clean lines in the first few are strong candidates
                    break
                
    if vendor_name:
        # Final cleanup: remove extra spaces, then title-case.
        vendor_name = ' '.join(vendor_name.split()).title()
        extracted_data['vendor_name'] = vendor_name
        logger.debug(f"Vendor name found: {vendor_name}")
    else:
        logger.warning("Could not reliably extract vendor name.")
        
    category_map = {
        'grocer': 'Groceries', 'supermart': 'Groceries', 'hypermarket': 'Groceries', 'foodmart': 'Groceries', 'bakery': 'Groceries', 'market': 'Groceries',
        'electricity': 'Utilities', 'power bill': 'Utilities', 'light bill': 'Utilities',
        'internet': 'Utilities', 'telecom': 'Utilities', 'broadband': 'Utilities', 'water bill': 'Utilities', 'gas bill': 'Utilities',
        'restaurant': 'Dining', 'cafe': 'Dining', 'food': 'Dining', 'diner': 'Dining', 'eatery': 'Dining', 'pizzeria': 'Dining', 'kfc': 'Dining', 'mcdonalds': 'Dining',
        'petrol': 'Transport', 'gas station': 'Transport', 'fuel': 'Transport', 'auto': 'Transport', 'car wash': 'Transport',
        'pharmacy': 'Health', 'medicine': 'Health', 'clinic': 'Health', 'hospital': 'Health', 'doctor': 'Health',
        'fashion': 'Shopping', 'clothing': 'Shopping', 'boutique': 'Shopping', 'retail': 'Shopping', 'department store': 'Shopping', 'mall': 'Shopping',
        'electronics': 'Electronics', 'tech store': 'Electronics', 'computer': 'Electronics', 'mobile': 'Electronics',
        'bookstore': 'Books', 'library': 'Books',
        'travel': 'Travel', 'airline': 'Travel', 'hotel': 'Travel', 'vacation': 'Travel', 'resort': 'Travel',
        'subscription': 'Subscriptions', 'monthly fee': 'Subscriptions', 'membership': 'Subscriptions', 'streaming': 'Subscriptions'
    }
    extracted_data['category_name'] = None
    for keyword, category in category_map.items():
        if keyword in lower_text or (vendor_name and keyword in vendor_name.lower()):
            extracted_data['category_name'] = category
            logger.debug(f"Category found: {category}")
            break

    billing_period_patterns = [
        r"(?:billing|service|period)\s*[:=]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})",
        r"for the period\s*from\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\s*to\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"
    ]
    billing_period_start = None
    billing_period_end = None

    for pattern in billing_period_patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            date_str1 = match.group(1).replace('.', '')
            date_str2 = match.group(2).replace('.', '')
            
            parsed_start = None
            parsed_end = None
            for fmt in formats_to_try: # Use the same comprehensive formats as for transaction_date
                try:
                    parsed_start = datetime.strptime(date_str1, fmt).date()
                    break
                except ValueError:
                    pass
            for fmt in formats_to_try:
                try:
                    parsed_end = datetime.strptime(date_str2, fmt).date()
                    break
                except ValueError:
                    pass
            
            if parsed_start and parsed_end:
                billing_period_start = parsed_start
                billing_period_end = parsed_end
                break
    
    if billing_period_start and billing_period_end:
        extracted_data['billing_period_start'] = billing_period_start
        extracted_data['billing_period_end'] = billing_period_end
        logger.debug(f"Billing period found: {billing_period_start} to {billing_period_end}")
    else:
        logger.debug("Could not reliably extract billing period.")


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
            # Try common encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    extracted_text = raw_content_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if not extracted_text:
                raise UnicodeDecodeError("All common encodings failed.")
            logger.info(f"Read text directly from {original_filename}.")
        except Exception as e:
            logger.error(f"Failed to decode text file {original_filename}: {e}", exc_info=True)
            raise FileProcessingError(f"Failed to decode text file: {e}")
    elif file_type == 'pdf':
        try:
            # Attempt to extract text directly from PDF using PyPDF2
            pdf_file_obj = io.BytesIO(raw_content_bytes)
            reader = PyPDF2.PdfReader(pdf_file_obj)
            pdf_text = ""
            for page in reader.pages:
                pdf_text += page.extract_text() or "" # extract_text() can return None
            
            if pdf_text.strip():
                extracted_text = pdf_text
                logger.info(f"Extracted text directly from PDF {original_filename}.")
            else:
                logger.info(f"PDF {original_filename} contains no selectable text, or text extraction failed. Skipping OCR for PDF.")
            
        except Exception as e:
            logger.warning(f"Error extracting text directly from PDF {original_filename}: {e}. Treating as unreadable PDF for text extraction.", exc_info=True)
           
    elif file_type == 'image':
        try:
            detected_lang = detect_language(raw_content_bytes)
            ocr_lang = detected_lang if detected_lang else 'eng'
            
            extracted_text = extract_text_from_image(raw_content_bytes, lang=ocr_lang)
            if not extracted_text or not extracted_text.strip():
                raise ParsingError(f"OCR failed to extract text from {original_filename}.")
            logger.info(f"Extracted text from {original_filename} using OCR (lang={ocr_lang}).")
        except Exception as e:
            logger.error(f"OCR processing failed for {original_filename}: {e}", exc_info=True)
            raise ParsingError(f"OCR processing failed: {e}")


    if not extracted_text or not extracted_text.strip():
        logger.warning(f"Final extracted text from {original_filename} is empty or only whitespace.")
        if file_type == 'pdf':
            raise ParsingError(f"PDF {original_filename} has no selectable text. Please ensure it's a text-searchable PDF or convert it to an image (.png/.jpg) for OCR processing.")
        else:
            raise ParsingError(f"No meaningful text extracted from {original_filename}.")

    extracted_fields = _extract_from_text(extracted_text, file_type)
    extracted_fields['parsed_raw_text'] = extracted_text # Store raw text in the final model

    try:
        validated_data = ParsedReceiptData(**extracted_fields)
        logger.info(f"Successfully parsed and validated data for {original_filename}.")
        return validated_data
    except Exception as e:
        logger.error(f"Validation failed for {original_filename} with extracted fields: {extracted_fields}. Error: {e}", exc_info=True)
        raise ParsingError(f"Data validation failed after extraction: {e}")
