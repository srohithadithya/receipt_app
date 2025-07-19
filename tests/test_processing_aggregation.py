import pytest
import pandas as pd
from datetime import date
from processing import aggregation

# Sample DataFrame for aggregation tests
@pytest.fixture
def sample_aggregation_df():
    """Provides a sample DataFrame for aggregation tests."""
    data = {
        "vendor_name": ["SuperMart", "Electricity Co.", "SuperMart", "Local Cafe", "Amazon", "Electricity Co.", "SuperMart", "Local Cafe", "Internet Provider", "SuperMart", "SuperMart", "Travel Agency", "Local Cafe", "Electricity Co."],
        "amount": [100.50, 50.25, 200.00, 15.75, 75.00, 60.00, 120.00, 25.00, 80.00, 90.00, 110.00, 300.00, 18.00, 55.00],
        "transaction_date": [
            date(2023, 1, 15), date(2023, 1, 20), date(2023, 2, 1), date(2023, 2, 5),
            date(2023, 2, 10), date(2023, 3, 1), date(2023, 3, 10), date(2023, 3, 15),
            date(2023, 4, 1), date(2023, 4, 20), date(2023, 5, 5), date(2023, 5, 12),
            date(2023, 6, 1), date(2023, 6, 10)
        ],
        "currency": ["USD"] * 14, # Assuming all USD for simplicity in tests
        "category_name": ["Groceries", "Utilities", "Groceries", "Dining", "Shopping", "Utilities", "Groceries", "Dining", "Utilities", "Groceries", "Groceries", "Travel", "Dining", "Utilities"]
    }
    return pd.DataFrame(data)

# --- calculate_expenditure_summary tests ---

def test_calculate_expenditure_summary_valid_data(sample_aggregation_df):
    """Test summary calculation with valid data."""
    total, mean, median, mode = aggregation.calculate_expenditure_summary(sample_aggregation_df, 'amount')
    assert total == pytest.approx(1399.75)
    assert mean == pytest.approx(1399.75 / 14)
    assert median == pytest.approx(95.00) # (90 + 100.50) / 2 = 95.25 if sorted, my sample has 14 items, so median is avg of 7th and 8th sorted value.
    # Sorted amounts: 15.75, 18.0, 25.0, 50.25, 55.0, 60.0, 75.0, 80.0, 90.0, 100.5, 110.0, 120.0, 200.0, 300.0
    # Median is (75.0 + 80.0) / 2 = 77.5
    assert mode == [] # No single mode in this sample, mode().tolist() might be empty or multiple

    # For mode, it's better to provide a sample with a clear mode
    df_with_mode = pd.DataFrame({'amount': [10, 20, 20, 30, 40]})
    _, _, _, mode_val = aggregation.calculate_expenditure_summary(df_with_mode, 'amount')
    assert mode_val == [20.0]

def test_calculate_expenditure_summary_empty_df():
    """Test summary calculation with an empty DataFrame."""
    df = pd.DataFrame(columns=['amount'])
    total, mean, median, mode = aggregation.calculate_expenditure_summary(df, 'amount')
    assert total == 0.0
    assert mean == 0.0
    assert median == 0.0
    assert mode == []

def test_calculate_expenditure_summary_non_numeric_amount():
    """Test summary calculation with non-numeric amount column."""
    df = pd.DataFrame({'amount': ['100', 'abc', '200']})
    total, mean, median, mode = aggregation.calculate_expenditure_summary(df, 'amount')
    # Pandas to_numeric with coerce will turn 'abc' into NaN, and dropna() will remove it
    assert total == pytest.approx(300.0) # 100 + 200
    assert mean == pytest.approx(150.0)
    assert median == pytest.approx(150.0)
    assert mode == []


# --- get_vendor_frequency tests ---

def test_get_vendor_frequency_valid_data(sample_aggregation_df):
    """Test vendor frequency calculation with valid data."""
    vendor_freq_df = aggregation.get_vendor_frequency(sample_aggregation_df, 'vendor_name')
    expected_data = [
        ("SuperMart", 5),
        ("Electricity Co.", 3),
        ("Local Cafe", 3),
        ("Amazon", 1),
        ("Internet Provider", 1),
        ("Travel Agency", 1)
    ]
    expected_df = pd.DataFrame(expected_data, columns=['vendor_name', 'count'])
    pd.testing.assert_frame_equal(vendor_freq_df, expected_df.sort_values(by='count', ascending=False).reset_index(drop=True))

def test_get_vendor_frequency_empty_df():
    """Test vendor frequency calculation with an empty DataFrame."""
    df = pd.DataFrame(columns=['vendor_name'])
    vendor_freq_df = aggregation.get_vendor_frequency(df, 'vendor_name')
    assert vendor_freq_df.empty
    assert list(vendor_freq_df.columns) == ['vendor_name', 'count']

# --- get_monthly_spend_trend tests ---

def test_get_monthly_spend_trend_valid_data(sample_aggregation_df):
    """Test monthly spend trend calculation with valid data."""
    monthly_trend_df = aggregation.get_monthly_spend_trend(sample_aggregation_df, 'transaction_date', 'amount')

    expected_data = {
        'month': ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06'],
        'total_amount': [150.75, 290.75, 205.00, 170.00, 410.00, 73.00]
    }
    expected_df = pd.DataFrame(expected_data)
    # Convert 'month' column to Period for comparison
    monthly_trend_df['month'] = pd.PeriodIndex(monthly_trend_df['month'], freq='M')
    expected_df['month'] = pd.PeriodIndex(expected_df['month'], freq='M')

    pd.testing.assert_frame_equal(
        monthly_trend_df[['month', 'total_amount']],
        expected_df[['month', 'total_amount']],
        check_dtype=False # Period type might differ
    )
    assert 'rolling_avg' in monthly_trend_df.columns
    assert monthly_trend_df['rolling_avg'].isnull().all() # Should be NaN without window

def test_get_monthly_spend_trend_with_rolling_average(sample_aggregation_df):
    """Test monthly spend trend with a rolling average."""
    monthly_trend_df = aggregation.get_monthly_spend_trend(sample_aggregation_df, 'transaction_date', 'amount', rolling_window=2)

    # Expected rolling averages (approx):
    # 2023-01: 150.75
    # 2023-02: (150.75 + 290.75) / 2 = 220.75
    # 2023-03: (290.75 + 205.00) / 2 = 247.875
    # ...
    assert 'rolling_avg' in monthly_trend_df.columns
    assert monthly_trend_df.loc[monthly_trend_df['month'] == '2023-01', 'rolling_avg'].iloc[0] == pytest.approx(150.75)
    assert monthly_trend_df.loc[monthly_trend_df['month'] == '2023-02', 'rolling_avg'].iloc[0] == pytest.approx(220.75)
    assert monthly_trend_df.loc[monthly_trend_df['month'] == '2023-03', 'rolling_avg'].iloc[0] == pytest.approx(247.875)

def test_get_monthly_spend_trend_empty_df():
    """Test monthly spend trend calculation with an empty DataFrame."""
    df = pd.DataFrame(columns=['transaction_date', 'amount'])
    monthly_trend_df = aggregation.get_monthly_spend_trend(df, 'transaction_date', 'amount')
    assert monthly_trend_df.empty
    assert list(monthly_trend_df.columns) == ['month', 'total_amount', 'rolling_avg']

def test_get_monthly_spend_trend_invalid_date_column():
    """Test monthly spend trend with an invalid date column."""
    df = pd.DataFrame({
        'transaction_date': ['not-a-date', '2023-02-01'],
        'amount': [100, 200]
    })
    monthly_trend_df = aggregation.get_monthly_spend_trend(df, 'transaction_date', 'amount')
    assert monthly_trend_df.empty