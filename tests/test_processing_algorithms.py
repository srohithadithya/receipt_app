import pytest
from processing.algorithms import search, sort
from datetime import date, datetime

# Sample data for algorithms testing
SAMPLE_RECORDS = [
    {"id": 1, "vendor": "Walmart", "amount": 100.50, "date": date(2023, 1, 15), "description": "Groceries at Walmart"},
    {"id": 2, "vendor": "Target", "amount": 50.25, "date": date(2023, 1, 20), "description": "Clothes from Target"},
    {"id": 3, "vendor": "WALMART Supercenter", "amount": 200.00, "date": date(2023, 2, 1), "description": "Electronics from Walmart"},
    {"id": 4, "vendor": "Local Cafe", "amount": 15.75, "date": date(2023, 2, 5), "description": "Coffee and snacks"},
    {"id": 5, "vendor": "Amazon", "amount": 75.00, "date": date(2023, 2, 10), "description": "Online shopping"},
    {"id": 6, "vendor": "Target", "amount": 30.00, "date": date(2023, 2, 12), "description": "Home goods"}
]

# --- search.py tests ---

def test_linear_search_records_keyword_found():
    """Test linear search with a keyword found (case-insensitive)."""
    results = search.linear_search_records(SAMPLE_RECORDS, "walmart", fields=["vendor"])
    assert len(results) == 2
    assert {r["id"] for r in results} == {1, 3}

def test_linear_search_records_keyword_not_found():
    """Test linear search with a keyword not found."""
    results = search.linear_search_records(SAMPLE_RECORDS, "Costco", fields=["vendor"])
    assert len(results) == 0

def test_linear_search_records_case_sensitive():
    """Test linear search with case-sensitive option."""
    results = search.linear_search_records(SAMPLE_RECORDS, "Walmart", fields=["vendor"], case_sensitive=True)
    assert len(results) == 1
    assert results[0]["id"] == 1

def test_linear_search_records_all_fields():
    """Test linear search across all string fields."""
    results = search.linear_search_records(SAMPLE_RECORDS, "snacks")
    assert len(results) == 1
    assert results[0]["id"] == 4

def test_linear_search_records_empty_input():
    """Test linear search with empty input list."""
    results = search.linear_search_records([], "query")
    assert len(results) == 0

def test_range_search_records_found():
    """Test range search with values found within range."""
    results = search.range_search_records(SAMPLE_RECORDS, "amount", min_value=50, max_value=100)
    assert len(results) == 2
    assert {r["id"] for r in results} == {2, 5}

def test_range_search_records_no_upper_bound():
    """Test range search with only a minimum value."""
    results = search.range_search_records(SAMPLE_RECORDS, "amount", min_value=150)
    assert len(results) == 1
    assert results[0]["id"] == 3

def test_range_search_records_no_lower_bound():
    """Test range search with only a maximum value."""
    results = search.range_search_records(SAMPLE_RECORDS, "amount", max_value=20)
    assert len(results) == 1
    assert results[0]["id"] == 4

def test_range_search_records_no_match():
    """Test range search with no values in range."""
    results = search.range_search_records(SAMPLE_RECORDS, "amount", min_value=300)
    assert len(results) == 0

def test_range_search_records_empty_input():
    """Test range search with empty input list."""
    results = search.range_search_records([], "amount", min_value=10)
    assert len(results) == 0

def test_pattern_search_records_found():
    """Test pattern search with a matching regex pattern."""
    results = search.pattern_search_records(SAMPLE_RECORDS, r"Targ.t", fields=["vendor"])
    assert len(results) == 2
    assert {r["id"] for r in results} == {2, 6}

def test_pattern_search_records_no_match():
    """Test pattern search with no matching regex pattern."""
    results = search.pattern_search_records(SAMPLE_RECORDS, r"XYZ", fields=["vendor"])
    assert len(results) == 0

def test_pattern_search_records_empty_input():
    """Test pattern search with empty input list."""
    results = search.pattern_search_records([], r"pattern")
    assert len(results) == 0

def test_pattern_search_records_invalid_regex():
    """Test pattern search with an invalid regex pattern."""
    results = search.pattern_search_records(SAMPLE_RECORDS, r"[abc", fields=["vendor"]) # Invalid regex
    assert len(results) == 0 # Should return empty list gracefully

def test_hashed_index_search_found():
    """Test HashedIndex search with a found key."""
    vendor_index = search.HashedIndex(SAMPLE_RECORDS, "vendor")
    results = vendor_index.search("walmart", records_list=SAMPLE_RECORDS)
    assert len(results) == 2
    assert {r["id"] for r in results} == {1, 3} # Case-insensitive by default for strings

def test_hashed_index_search_not_found():
    """Test HashedIndex search with a not found key."""
    vendor_index = search.HashedIndex(SAMPLE_RECORDS, "vendor")
    results = vendor_index.search("ZMart", records_list=SAMPLE_RECORDS)
    assert len(results) == 0

def test_hashed_index_search_case_sensitive():
    """Test HashedIndex search with case-sensitive option."""
    vendor_index = search.HashedIndex(SAMPLE_RECORDS, "vendor")
    results = vendor_index.search("Walmart", case_sensitive=True, records_list=SAMPLE_RECORDS)
    assert len(results) == 1
    assert results[0]["id"] == 1

def test_hashed_index_no_records_list():
    """Test HashedIndex search when records_list is not provided."""
    vendor_index = search.HashedIndex(SAMPLE_RECORDS, "vendor")
    results = vendor_index.search("Walmart")
    assert len(results) == 0 # Should return empty as it can't retrieve full records

# --- sort.py tests ---

def test_sort_records_timsort_amount_asc():
    """Test Timsort for numerical field (amount) ascending."""
    sorted_records = sort.sort_records(SAMPLE_RECORDS, "amount", reverse=False, algorithm="timsort")
    amounts = [r["amount"] for r in sorted_records]
    assert amounts == sorted(amounts) # Python's sorted uses Timsort

def test_sort_records_timsort_amount_desc():
    """Test Timsort for numerical field (amount) descending."""
    sorted_records = sort.sort_records(SAMPLE_RECORDS, "amount", reverse=True, algorithm="timsort")
    amounts = [r["amount"] for r in sorted_records]
    assert amounts == sorted(amounts, reverse=True)

def test_sort_records_timsort_vendor_asc():
    """Test Timsort for categorical field (vendor) ascending."""
    sorted_records = sort.sort_records(SAMPLE_RECORDS, "vendor", reverse=False, algorithm="timsort")
    vendors = [r["vendor"] for r in sorted_records]
    expected_order = [
        "Amazon", "Local Cafe", "Target", "Target", "Walmart", "WALMART Supercenter"
    ]
    assert [v.lower() for v in vendors] == [v.lower() for v in expected_order] # Compare lowercased

def test_sort_records_quicksort_amount_asc():
    """Test Quicksort for numerical field (amount) ascending."""
    sorted_records = sort.sort_records(SAMPLE_RECORDS, "amount", reverse=False, algorithm="quicksort")
    amounts = [r["amount"] for r in sorted_records]
    assert amounts == sorted(amounts)

def test_sort_records_mergesort_vendor_desc():
    """Test Mergesort for categorical field (vendor) descending."""
    sorted_records = sort.sort_records(SAMPLE_RECORDS, "vendor", reverse=True, algorithm="mergesort")
    vendors = [r["vendor"] for r in sorted_records]
    expected_order = [
        "WALMART Supercenter", "Walmart", "Target", "Target", "Local Cafe", "Amazon"
    ]
    assert [v.lower() for v in vendors] == [v.lower() for v in expected_order] # Compare lowercased

def test_sort_records_empty_list():
    """Test sorting an empty list."""
    results = sort.sort_records([], "amount")
    assert results == []

def test_sort_records_invalid_key():
    """Test sorting with an invalid key."""
    # This should gracefully fallback or attempt to sort by a string representation
    # Python's sorted() is robust; custom sorts might error
    sorted_records = sort.sort_records(SAMPLE_RECORDS, "non_existent_key", algorithm="timsort")
    assert len(sorted_records) == len(SAMPLE_RECORDS) # Should not error, just sort based on default value or type error
    # Assert specific behavior if you want to test how it handles missing keys
    # E.g., if it puts None/missing keys first or last.