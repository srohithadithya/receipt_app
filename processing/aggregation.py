import pandas as pd
import numpy as np
from datetime import date, datetime
from typing import List, Dict, Any, Tuple, Optional # Added Optional here
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_expenditure_summary(df: pd.DataFrame, amount_col: str = 'amount') -> Tuple[float, float, float, List[float]]:
    """
    Calculates summary statistics (sum, mean, median, mode) for expenditure.

    :param df: Pandas DataFrame containing receipt data.
    :param amount_col: Name of the column containing expenditure amounts (default 'amount').
    :return: A tuple containing (total_spend, mean_spend, median_spend, mode_spend).
             Returns (0.0, 0.0, 0.0, []) if the DataFrame is empty or amount column is missing/invalid.
    """
    if df.empty or amount_col not in df.columns or not pd.api.types.is_numeric_dtype(df[amount_col]):
        logger.warning("DataFrame is empty, missing amount column, or amount column is not numeric. Returning default summary.")
        return 0.0, 0.0, 0.0, []

    # Drop any non-numeric or NaN values from the amount column for calculations
    amounts = df[amount_col].dropna().astype(float)

    if amounts.empty:
        return 0.0, 0.0, 0.0, []

    total_spend = amounts.sum()
    mean_spend = amounts.mean()
    median_spend = amounts.median()
    # Mode can return multiple values, so return as a list
    mode_spend = amounts.mode().tolist()

    logger.info(f"Calculated expenditure summary: Total={total_spend:.2f}, Mean={mean_spend:.2f}, Median={median_spend:.2f}, Mode={mode_spend}")
    return total_spend, mean_spend, median_spend, mode_spend

def get_vendor_frequency(df: pd.DataFrame, vendor_col: str = 'vendor_name') -> pd.DataFrame:
    """
    Calculates the frequency distribution of vendors.

    :param df: Pandas DataFrame containing receipt data.
    :param vendor_col: Name of the column containing vendor names (default 'vendor_name').
    :return: A DataFrame with 'vendor_name' and 'count' columns, sorted by count descending.
             Returns an empty DataFrame if input is invalid.
    """
    if df.empty or vendor_col not in df.columns:
        logger.warning("DataFrame is empty or missing vendor column. Returning empty vendor frequency DataFrame.")
        return pd.DataFrame(columns=[vendor_col, 'count'])

    # Ensure vendor_col is treated as string and handle NaNs
    vendor_counts = df[vendor_col].astype(str).value_counts().reset_index()
    vendor_counts.columns = [vendor_col, 'count']
    vendor_counts = vendor_counts.sort_values(by='count', ascending=False)
    logger.info(f"Generated vendor frequency for {len(vendor_counts)} unique vendors.")
    return vendor_counts

def get_monthly_spend_trend(df: pd.DataFrame, date_col: str = 'transaction_date', amount_col: str = 'amount',
                            rolling_window: Optional[int] = None) -> pd.DataFrame:
    """
    Calculates the monthly spending trend and optionally a rolling average.

    :param df: Pandas DataFrame containing receipt data.
    :param date_col: Name of the column containing transaction dates (default 'transaction_date').
    :param amount_col: Name of the column containing expenditure amounts (default 'amount').
    :param rolling_window: Optional; if provided, calculates a rolling mean over this many months.
    :return: A DataFrame with 'month' (period), 'total_amount', and optionally 'rolling_avg' columns.
             Returns an empty DataFrame if input is invalid.
    """
    if df.empty or date_col not in df.columns or amount_col not in df.columns:
        logger.warning("DataFrame is empty or missing date/amount columns. Returning empty monthly trend DataFrame.")
        return pd.DataFrame(columns=['month', 'total_amount', 'rolling_avg'])

    df_copy = df.copy() # Work on a copy to avoid SettingWithCopyWarning

    # Ensure date_col is datetime objects
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
    df_copy = df_copy.dropna(subset=[date_col]) # Drop rows where date conversion failed

    if df_copy.empty:
        logger.warning("No valid dates found after conversion for monthly trend. Returning empty DataFrame.")
        return pd.DataFrame(columns=['month', 'total_amount', 'rolling_avg'])

    # Ensure amount_col is numeric
    df_copy[amount_col] = pd.to_numeric(df_copy[amount_col], errors='coerce')
    df_copy = df_copy.dropna(subset=[amount_col]) # Drop rows where amount is not numeric

    if df_copy.empty:
        logger.warning("No valid amounts found after conversion for monthly trend. Returning empty DataFrame.")
        return pd.DataFrame(columns=['month', 'total_amount', 'rolling_avg'])

    # Set date_col as index for resampling
    df_copy = df_copy.set_index(date_col)

    # Resample by month and sum amounts
    monthly_spend = df_copy[amount_col].resample('MS').sum().reset_index()
    monthly_spend.columns = ['month', 'total_amount']

    # Convert 'month' to a string format for better display in charts (e.g., 'YYYY-MM')
    monthly_spend['month'] = monthly_spend['month'].dt.to_period('M').astype(str)

    # Calculate rolling average if requested
    if rolling_window and rolling_window > 0:
        # Need to re-index by datetime for rolling window calculation
        temp_df_for_rolling = monthly_spend.set_index(pd.to_datetime(monthly_spend['month']))
        monthly_spend['rolling_avg'] = temp_df_for_rolling['total_amount'].rolling(window=rolling_window, min_periods=1).mean().values
        logger.info(f"Generated monthly spend trend with {rolling_window}-month rolling average.")
    else:
        monthly_spend['rolling_avg'] = np.nan # No rolling avg column

    monthly_spend = monthly_spend.sort_values(by='month')
    logger.info(f"Generated monthly spend trend for {len(monthly_spend)} months.")
    return monthly_spend

# Example Usage (for testing/demonstration)
if __name__ == "__main__":
    # Create dummy data resembling parsed receipts (as a list of dicts)
    # In a real scenario, this would come from database/crud.py's get_receipts_by_user
    sample_receipt_data = [
        {"id": 1, "vendor_name": "SuperMart", "amount": 100.50, "transaction_date": date(2023, 1, 15), "category_name": "Groceries"},
        {"id": 2, "vendor_name": "Electricity Co.", "amount": 50.25, "transaction_date": date(2023, 1, 20), "category_name": "Utilities"},
        {"id": 3, "vendor_name": "SuperMart", "amount": 200.00, "transaction_date": date(2023, 2, 1), "category_name": "Groceries"},
        {"id": 4, "vendor_name": "Local Cafe", "amount": 15.75, "transaction_date": date(2023, 2, 5), "category_name": "Dining"},
        {"id": 5, "vendor_name": "Amazon", "amount": 75.00, "transaction_date": date(2023, 2, 10), "category_name": "Shopping"},
        {"id": 6, "vendor_name": "Electricity Co.", "amount": 60.00, "transaction_date": date(2023, 3, 1), "category_name": "Utilities"},
        {"id": 7, "vendor_name": "SuperMart", "amount": 120.00, "transaction_date": date(2023, 3, 10), "category_name": "Groceries"},
        {"id": 8, "vendor_name": "Local Cafe", "amount": 25.00, "transaction_date": date(2023, 3, 15), "category_name": "Dining"},
        {"id": 9, "vendor_name": "Internet Provider", "amount": 80.00, "transaction_date": date(2023, 4, 1), "category_name": "Utilities"},
        {"id": 10, "vendor_name": "SuperMart", "amount": 90.00, "transaction_date": date(2023, 4, 20), "category_name": "Groceries"},
        {"id": 11, "vendor_name": "SuperMart", "amount": 110.00, "transaction_date": date(2023, 5, 5), "category_name": "Groceries"},
        {"id": 12, "vendor_name": "Travel Agency", "amount": 300.00, "transaction_date": date(2023, 5, 12), "category_name": "Travel"},
        {"id": 13, "vendor_name": "Local Cafe", "amount": 18.00, "transaction_date": date(2023, 6, 1), "category_name": "Dining"},
        {"id": 14, "vendor_name": "Electricity Co.", "amount": 55.00, "transaction_date": date(2023, 6, 10), "category_name": "Utilities"},
    ]

    # Convert list of dicts to DataFrame
    df_receipts = pd.DataFrame(sample_receipt_data)

    print("--- Original DataFrame ---")
    print(df_receipts)

    # Test Expenditure Summary
    print("\n--- Expenditure Summary ---")
    total, mean, median, mode = calculate_expenditure_summary(df_receipts)
    print(f"Total Spend: {total:.2f}")
    print(f"Mean Spend: {mean:.2f}")
    print(f"Median Spend: {median:.2f}")
    print(f"Mode Spend: {mode}")

    # Test Vendor Frequency
    print("\n--- Vendor Frequency ---")
    vendor_freq_df = get_vendor_frequency(df_receipts)
    print(vendor_freq_df)

    # Test Monthly Spend Trend
    print("\n--- Monthly Spend Trend (without rolling average) ---")
    monthly_trend_df = get_monthly_spend_trend(df_receipts)
    print(monthly_trend_df)

    print("\n--- Monthly Spend Trend (with 3-month rolling average) ---")
    monthly_trend_rolling_df = get_monthly_spend_trend(df_receipts, rolling_window=3)
    print(monthly_trend_rolling_df)

    # Test with empty DataFrame
    print("\n--- Testing with Empty DataFrame ---")
    empty_df = pd.DataFrame(columns=['vendor_name', 'amount', 'transaction_date'])
    total_e, mean_e, median_e, mode_e = calculate_expenditure_summary(empty_df)
    print(f"Empty DF Summary: Total={total_e}, Mean={mean_e}, Median={median_e}, Mode={mode_e}")
    vendor_freq_e = get_vendor_frequency(empty_df)
    print(f"Empty DF Vendor Freq:\n{vendor_freq_e}")
    monthly_trend_e = get_monthly_spend_trend(empty_df)
    print(f"Empty DF Monthly Trend:\n{monthly_trend_e}")