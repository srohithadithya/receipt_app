from pydantic import BaseModel, Field, ValidationError, validator
from datetime import date
from typing import Optional, Literal, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParsedReceiptData(BaseModel):
    """
    Pydantic model for validating and structuring extracted receipt data.
    """
    vendor_name: str = Field(..., min_length=1, description="Name of the vendor or biller.")
    transaction_date: date = Field(..., description="Date of the transaction.")
    amount: float = Field(..., gt=0, description="Total amount of the transaction.")
    currency: str = Field("USD", min_length=1, max_length=5, description="Currency of the transaction (e.g., USD, EUR, INR).")
    category_name: Optional[str] = Field(None, description="Categorization of the expense (e.g., Groceries, Utilities).")
    billing_period_start: Optional[date] = Field(None, description="Start date of the billing period for bills.")
    billing_period_end: Optional[date] = Field(None, description="End date of the billing period for bills.")
    parsed_raw_text: Optional[str] = Field(None, description="Raw text extracted from the document.")

    @validator('transaction_date', 'billing_period_start', 'billing_period_end', pre=True)
    def parse_date_strings(cls, v):
        if isinstance(v, str):
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y', '%b %d, %Y', '%B %d, %Y'):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Could not parse date: {v}. Expected formats like YYYY-MM-DD or DD-MM-YYYY.")
        elif isinstance(v, date):
            return v
        elif v is None:
            return None
        raise TypeError("Date must be a string or date object.")

    @validator('amount', pre=True)
    def parse_amount(cls, v):
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Remove currency symbols, commas, and trim whitespace
            clean_v = v.replace('$', '').replace('€', '').replace('£', '').replace('₹', '').replace(',', '').strip()
            try:
                return float(clean_v)
            except ValueError:
                raise ValueError(f"Could not parse amount: {v}. Expected a valid number format.")
        raise TypeError("Amount must be a number or string.")

    @validator('currency', pre=True)
    def validate_currency(cls, v):
        if isinstance(v, str):
            upper_v = v.upper().strip()
            # Basic validation for common currencies. Could be expanded with a lookup table.
            if len(upper_v) <= 5 and upper_v.isalpha():
                return upper_v
        return "USD" # Default to USD if invalid or cannot determine

def validate_file_type(file_name: str) -> Optional[str]:
    """
    Validates the file extension against allowed types.
    :param file_name: The name of the file.
    :return: The detected file type (e.g., 'image', 'pdf', 'text') or None if invalid.
    """
    if not isinstance(file_name, str):
        logger.warning(f"Invalid file_name type: {type(file_name)}")
        return None

    file_extension = file_name.split('.')[-1].lower()
    if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return 'image'
    elif file_extension == 'pdf':
        return 'pdf'
    elif file_extension == 'txt':
        return 'text'
    else:
        logger.warning(f"Unsupported file type: {file_extension} for file {file_name}")
        return None

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    from datetime import date

    # Test valid data
    try:
        data = ParsedReceiptData(
            vendor_name="SuperMart",
            transaction_date="2023-01-15",
            amount="45.75",
            currency="USD",
            category_name="Groceries"
        )
        logger.info(f"Valid Data 1: {data.dict()}")
    except ValidationError as e:
        logger.error(f"Validation Error 1: {e.json()}")

    try:
        data = ParsedReceiptData(
            vendor_name="Internet Provider",
            transaction_date=date(2023, 2, 1),
            amount=59.99,
            billing_period_start="2023/01/01",
            billing_period_end="2023/01/31"
        )
        logger.info(f"Valid Data 2: {data.dict()}")
    except ValidationError as e:
        logger.error(f"Validation Error 2: {e.json()}")

    # Test invalid data
    try:
        data = ParsedReceiptData(
            vendor_name="", # Empty vendor name
            transaction_date="not-a-date",
            amount="abc", # Invalid amount
            currency="$$"
        )
        logger.info(f"Invalid Data Attempt: {data.dict()}")
    except ValidationError as e:
        logger.error(f"Validation Error with invalid data: {e.json()}")

    # Test file type validation
    logger.info(f"File Type Validation 'receipt.jpg': {validate_file_type('receipt.jpg')}")
    logger.info(f"File Type Validation 'bill.pdf': {validate_file_type('bill.pdf')}")
    logger.info(f"File Type Validation 'notes.txt': {validate_file_type('notes.txt')}")
    logger.info(f"File Type Validation 'document.docx': {validate_file_type('document.docx')}")