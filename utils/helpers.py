import pandas as pd
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_df_to_csv(df: pd.DataFrame) -> str:
    """
    Converts a pandas DataFrame to a CSV formatted string.

    :param df: The DataFrame to convert.
    :return: A string containing the CSV data, or an empty string on error.
    """
    if df.empty:
        logger.info("Attempted to convert empty DataFrame to CSV.")
        return ""
    try:
        csv_string = df.to_csv(index=False)
        logger.debug("DataFrame converted to CSV string successfully.")
        return csv_string
    except Exception as e:
        logger.error(f"Error converting DataFrame to CSV: {e}")
        return ""

def convert_df_to_json(df: pd.DataFrame) -> str:
    """
    Converts a pandas DataFrame to a JSON formatted string.
    Ensures date/datetime objects are serialized correctly to ISO format.

    :param df: The DataFrame to convert.
    :return: A string containing the JSON data, or an empty JSON object string on error.
    """
    if df.empty:
        logger.info("Attempted to convert empty DataFrame to JSON.")
        return "{}"
    try:
        # Create a copy to avoid modifying the original DataFrame
        df_json_friendly = df.copy()

        # Convert all date/datetime columns to ISO 8601 strings
        for col in df_json_friendly.columns:
            if pd.api.types.is_datetime64_any_dtype(df_json_friendly[col]):
                df_json_friendly[col] = df_json_friendly[col].dt.isoformat(timespec='seconds')
            # Handle date objects which might not be pd.Timestamp if loaded directly
            elif pd.api.types.is_object_dtype(df_json_friendly[col]) and not df_json_friendly[col].empty and isinstance(df_json_friendly[col].iloc[0], date):
                 df_json_friendly[col] = df_json_friendly[col].apply(lambda x: x.isoformat() if x else None)


        # Use orient="records" for a list of JSON objects (one per row)
        json_string = df_json_friendly.to_json(orient="records", indent=4, date_format="iso")
        logger.debug("DataFrame converted to JSON string successfully.")
        return json_string
    except Exception as e:
        logger.error(f"Error converting DataFrame to JSON: {e}")
        return "{}"

def parse_date_safely(date_str: str) -> Optional[date]:
    """
    Safely parses a date string into a datetime.date object.
    Supports a comprehensive list of common date formats.

    :param date_str: The string representation of a date.
    :return: A datetime.date object if parsing is successful, None otherwise.
    """
    if not isinstance(date_str, str) or not date_str.strip():
        return None

    # Define a list of common date formats to try
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", # YYYY-MM-DD, DD-MM-YYYY, MM-DD-YYYY
        "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", # YYYY/MM/DD, DD/MM/YYYY, MM/DD/YYYY
        "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y", # YYYY.MM.DD, DD.MM.YYYY, MM.DD.YYYY
        "%b %d, %Y", "%B %d, %Y",            # Jan 01, 2023 / January 01, 2023
        "%d %b %Y", "%d %B %Y",            # 01 Jan 2023 / 01 January 2023
        "%Y%m%d"                           # YYYYMMDD (e.g., 20230115)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue # Try next format
    logger.warning(f"Could not parse date string '{date_str}' with known formats.")
    return None

def detect_currency(text: str) -> str:
    """
    Detects currency based on common symbols and ISO codes found within a given text.
    Prioritizes explicit ISO codes if present.

    :param text: The text content (e.g., raw text from a receipt).
    :return: The detected currency code (e.g., 'USD', 'EUR'), defaults to 'USD'.
    """
    if not isinstance(text, str):
        logger.warning(f"Non-string input for currency detection: {type(text)}")
        return 'USD'

    text_lower = text.lower()

    # Define currency patterns with their corresponding codes and priorities
    # Prioritize ISO codes or explicit mentions over just symbols if possible
    currency_patterns = {
        'USD': [r'usd', r'\$', r'dollars', r'us dollar'],
        'EUR': [r'eur', r'€', r'euro'],
        'GBP': [r'gbp', r'£', r'pound'],
        'INR': [r'inr', r'₹', r'rupee'],
        'CAD': [r'cad', r'canadian dollar'],
        'AUD': [r'aud', r'australian dollar'],
        'JPY': [r'jpy', r'¥', r'yen'],
        # Add more currencies as needed
    }

    # Iterate through patterns to find the first match
    for code, patterns in currency_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                logger.debug(f"Detected currency: {code} from pattern '{pattern}'.")
                return code

    logger.info("No specific currency detected, defaulting to USD.")
    return 'USD'

def is_valid_email(email: str) -> bool:
    """
    Validates if a string is a well-formed email address using a simple regex.
    Note: This is a basic validation, not exhaustive.
    """
    if not isinstance(email, str):
        return False
    # Regex from StackOverflow - common basic email regex
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.search(regex, email, re.IGNORECASE):
        return True
    return False

# Example Usage (for testing/demonstration)
if __name__ == "__main__":
    import datetime

    print("\n--- DataFrame to CSV/JSON Conversion ---")
    data = {
        'id': [1, 2, 3],
        'vendor': ['Store A', 'Café B', 'Shop C'],
        'amount': [10.50, 5.75, 20.00],
        'date': [datetime.date(2023, 1, 1), datetime.date(2023, 1, 2), datetime.date(2023, 1, 3)],
        'timestamp': [datetime.datetime(2023, 1, 1, 10, 0, 0), datetime.datetime(2023, 1, 2, 11, 30, 0), datetime.datetime(2023, 1, 3, 12, 0, 0)]
    }
    sample_df = pd.DataFrame(data)
    print("Sample DataFrame:\n", sample_df)

    csv_output = convert_df_to_csv(sample_df)
    print("\nCSV Output:\n", csv_output)

    json_output = convert_df_to_json(sample_df)
    print("\nJSON Output:\n", json_output)

    print("\n--- Date Parsing Safely ---")
    print(f"Parsing '2023-01-15': {parse_date_safely('2023-01-15')}")
    print(f"Parsing '15/01/2023': {parse_date_safely('15/01/2023')}")
    print(f"Parsing 'Jan 15, 2023': {parse_date_safely('Jan 15, 2023')}")
    print(f"Parsing '15 Feb 2024': {parse_date_safely('15 Feb 2024')}")
    print(f"Parsing 'invalid-date': {parse_date_safely('invalid-date')}")
    print(f"Parsing '20230301': {parse_date_safely('20230301')}")


    print("\n--- Currency Detection ---")
    print(f"Text 'Total: $123.45': {detect_currency('Total: $123.45')}")
    print(f"Text 'Amount: 99.99 EUR': {detect_currency('Amount: 99.99 EUR')}")
    print(f"Text 'Price: £50': {detect_currency('Price: £50')}")
    print(f"Text 'Cost: ₹1500': {detect_currency('Cost: ₹1500')}")
    print(f"Text 'Bill is 75 USD': {detect_currency('Bill is 75 USD')}")
    print(f"Text 'Invoice for 200 Euro': {detect_currency('Invoice for 200 Euro')}")
    print(f"Text 'Price is 100': {detect_currency('Price is 100')}")

    print("\n--- Email Validation ---")
    print(f"'test@example.com' is valid: {is_valid_email('test@example.com')}")
    print(f"'invalid-email' is valid: {is_valid_email('invalid-email')}")
    print(f"'user@sub.domain.co' is valid: {is_valid_email('user@sub.domain.co')}")