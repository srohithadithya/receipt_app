from typing import List, Dict, Any, Callable
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sort_records(
    records: List[Dict[str, Any]],
    sort_key: str,
    reverse: bool = False,
    algorithm: str = "timsort"
) -> List[Dict[str, Any]]:
    """
    Sorts a list of dictionaries (records) based on a specified key.

    :param records: A list of dictionaries, where each dictionary is a record.
    :param sort_key: The key (string) in the dictionaries to sort by.
    :param reverse: If True, sort in descending order. Default is False (ascending).
    :param algorithm: The sorting algorithm to use. 'timsort' uses Python's built-in sorted().
                      'quicksort' and 'mergesort' are custom implementations.
    :return: A new list of sorted records.
    :raises ValueError: If an unsupported algorithm is specified or sort_key is invalid.
    """
    if not records:
        return []

    def get_sort_value(item):
        value = item.get(sort_key)
        if isinstance(value, str):
            return value.lower()
        return value

    try:
        if algorithm == "timsort":
            sorted_records = sorted(records, key=get_sort_value, reverse=reverse)
            logger.info(f"Records sorted using Timsort by '{sort_key}' ({'desc' if reverse else 'asc'}).")
            return sorted_records
        elif algorithm == "quicksort":
            sorted_records = _quicksort(list(records), sort_key, reverse)
            logger.info(f"Records sorted using Custom Quicksort by '{sort_key}' ({'desc' if reverse else 'asc'}).")
            return sorted_records
        elif algorithm == "mergesort":
            sorted_records = _mergesort(list(records), sort_key, reverse)
            logger.info(f"Records sorted using Custom Mergesort by '{sort_key}' ({'desc' if reverse else 'asc'}).")
            return sorted_records
        else:
            raise ValueError(f"Unsupported sorting algorithm: {algorithm}")
    except TypeError as e:
        logger.error(f"Error sorting records by key '{sort_key}': Incomparable types or key missing. Error: {e}")
        return sorted(records, key=lambda x: str(x.get(sort_key, '')), reverse=reverse) # Attempt string conversion for problematic types
    except Exception as e:
        logger.error(f"An unexpected error occurred during sorting: {e}")
        return list(records)

def _quicksort(data: List[Dict[str, Any]], sort_key: str, reverse: bool) -> List[Dict[str, Any]]:
    """
    Private helper function implementing Quicksort.
    Time Complexity: Average O(N log N), Worst O(N^2)
    Space Complexity: O(log N) (for recursion stack)
    """
    if len(data) <= 1:
        return data

    pivot = data[len(data) // 2]
    pivot_value = pivot.get(sort_key)
    if isinstance(pivot_value, str): pivot_value = pivot_value.lower()

    left = [item for item in data if (item.get(sort_key).lower() if isinstance(item.get(sort_key), str) else item.get(sort_key)) < pivot_value]
    middle = [item for item in data if (item.get(sort_key).lower() if isinstance(item.get(sort_key), str) else item.get(sort_key)) == pivot_value]
    right = [item for item in data if (item.get(sort_key).lower() if isinstance(item.get(sort_key), str) else item.get(sort_key)) > pivot_value]

    if reverse:
        return _quicksort(right, sort_key, reverse) + middle + _quicksort(left, sort_key, reverse)
    else:
        return _quicksort(left, sort_key, reverse) + middle + _quicksort(right, sort_key, reverse)


def _mergesort(data: List[Dict[str, Any]], sort_key: str, reverse: bool) -> List[Dict[str, Any]]:
    """
    Private helper function implementing Mergesort.
    Time Complexity: O(N log N) (Worst, Average, Best)
    Space Complexity: O(N) (for temporary arrays)
    """
    if len(data) <= 1:
        return data

    mid = len(data) // 2
    left_half = data[:mid]
    right_half = data[mid:]

    left_half = _mergesort(left_half, sort_key, reverse)
    right_half = _mergesort(right_half, sort_key, reverse)

    return _merge(left_half, right_half, sort_key, reverse)

def _merge(left: List[Dict[str, Any]], right: List[Dict[str, Any]], sort_key: str, reverse: bool) -> List[Dict[str, Any]]:
    """
    Private helper for Mergesort, merges two sorted lists.
    """
    result = []
    left_idx, right_idx = 0, 0

    while left_idx < len(left) and right_idx < len(right):
        left_val = left[left_idx].get(sort_key)
        right_val = right[right_idx].get(sort_key)

        # Normalize string values for comparison
        if isinstance(left_val, str): left_val = left_val.lower()
        if isinstance(right_val, str): right_val = right_val.lower()

        should_append_left = False
        if reverse:
            should_append_left = (left_val >= right_val) # For descending
        else:
            should_append_left = (left_val <= right_val) # For ascending

        if should_append_left:
            result.append(left[left_idx])
            left_idx += 1
        else:
            result.append(right[right_idx])
            right_idx += 1

    result.extend(left[left_idx:])
    result.extend(right[right_idx:])
    return result

# Example Usage
if __name__ == "__main__":
    sample_records = [
        {"id": 1, "vendor": "Walmart", "amount": 100.50, "date": "2023-01-15"},
        {"id": 2, "vendor": "Target", "amount": 50.25, "date": "2023-01-20"},
        {"id": 3, "vendor": "WALMART Supercenter", "amount": 200.00, "date": "2023-02-01"},
        {"id": 4, "vendor": "Local Cafe", "amount": 15.75, "date": "2023-02-05"},
        {"id": 5, "vendor": "Amazon", "amount": 75.00, "date": "2023-02-10"},
        {"id": 6, "vendor": "Target", "amount": 30.00, "date": "2023-02-12"}
    ]

    print("\n--- Sorting by Amount (Ascending, Timsort) ---")
    sorted_amount_asc = sort_records(sample_records, "amount", reverse=False, algorithm="timsort")
    for r in sorted_amount_asc: print(r)

    print("\n--- Sorting by Amount (Descending, Timsort) ---")
    sorted_amount_desc = sort_records(sample_records, "amount", reverse=True, algorithm="timsort")
    for r in sorted_amount_desc: print(r)

    print("\n--- Sorting by Vendor (Ascending, Quicksort) ---")
    sorted_vendor_asc_qs = sort_records(sample_records, "vendor", reverse=False, algorithm="quicksort")
    for r in sorted_vendor_asc_qs: print(r)

    print("\n--- Sorting by Vendor (Descending, Mergesort) ---")
    sorted_vendor_desc_ms = sort_records(sample_records, "vendor", reverse=True, algorithm="mergesort")
    for r in sorted_vendor_desc_ms: print(r)

    print("\n--- Sorting by Date (Descending, Timsort) ---")
    # Convert date strings to actual date objects for proper sorting
    from datetime import date
    sample_records_with_dates = [
        {"id": 1, "vendor": "Walmart", "amount": 100.50, "date": date(2023, 1, 15)},
        {"id": 2, "vendor": "Target", "amount": 50.25, "date": date(2023, 1, 20)},
        {"id": 3, "vendor": "WALMART Supercenter", "amount": 200.00, "date": date(2023, 2, 1)},
        {"id": 4, "vendor": "Local Cafe", "amount": 15.75, "date": date(2023, 2, 5)},
        {"id": 5, "vendor": "Amazon", "amount": 75.00, "date": date(2023, 2, 10)},
        {"id": 6, "vendor": "Target", "amount": 30.00, "date": date(2023, 2, 12)}
    ]
    sorted_date_desc = sort_records(sample_records_with_dates, "date", reverse=True, algorithm="timsort")
    for r in sorted_date_desc: print(r)
