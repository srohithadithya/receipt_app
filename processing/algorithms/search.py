from typing import List, Dict, Any, Optional
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def linear_search_records(
    records: List[Dict[str, Any]],
    query: str,
    fields: Optional[List[str]] = None,
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """
    Performs a linear search on a list of dictionaries (records).
    It checks if the query string is present in the specified fields or all fields if none are specified.

    :param records: A list of dictionaries, where each dictionary is a record.
    :param query: The string to search for.
    :param fields: Optional list of keys (strings) to search within. If None, all string values are searched.
    :param case_sensitive: Boolean, if True, the search is case-sensitive. Default is False.
    :return: A list of records that match the query.
    """
    if not records or not query:
        return []

    results = []
    normalized_query = query if case_sensitive else query.lower()

    for record in records:
        match_found = False
        keys_to_search = fields if fields is not None else record.keys()

        for key in keys_to_search:
            value = record.get(key)
            if isinstance(value, str):
                normalized_value = value if case_sensitive else value.lower()
                if normalized_query in normalized_value:
                    match_found = True
                    break
            elif value is not None and not fields: # If no specific fields, check non-string values too (converted to string)
                str_value = str(value)
                normalized_str_value = str_value if case_sensitive else str_value.lower()
                if normalized_query in normalized_str_value:
                    match_found = True
                    break
        if match_found:
            results.append(record)
    logger.info(f"Linear search completed for query '{query}', found {len(results)} results.")
    return results

def range_search_records(
    records: List[Dict[str, Any]],
    field: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Performs a range search on a numerical field in a list of dictionaries (records).

    :param records: A list of dictionaries, where each dictionary is a record.
    :param field: The key (string) of the numerical field to search within.
    :param min_value: The minimum value (inclusive) for the range. If None, no lower bound.
    :param max_value: The maximum value (inclusive) for the range. If None, no upper bound.
    :return: A list of records where the specified field's value falls within the given range.
    """
    if not records or not field:
        return []

    results = []
    for record in records:
        value = record.get(field)
        if isinstance(value, (int, float)):
            if (min_value is None or value >= min_value) and \
               (max_value is None or value <= max_value):
                results.append(record)
    logger.info(f"Range search completed for field '{field}' within [{min_value}, {max_value}], found {len(results)} results.")
    return results

def pattern_search_records(
    records: List[Dict[str, Any]],
    pattern: str,
    fields: Optional[List[str]] = None,
    flags: int = re.IGNORECASE
) -> List[Dict[str, Any]]:
    """
    Performs a regex pattern search on a list of dictionaries (records).

    :param records: A list of dictionaries, where each dictionary is a record.
    :param pattern: The regex pattern string to search for.
    :param fields: Optional list of keys (strings) to search within. If None, all string values are searched.
    :param flags: Regex flags, e.g., re.IGNORECASE. Default is re.IGNORECASE.
    :return: A list of records that match the pattern.
    """
    if not records or not pattern:
        return []

    results = []
    try:
        compiled_pattern = re.compile(pattern, flags)
    except re.error as e:
        logger.error(f"Invalid regex pattern '{pattern}': {e}")
        return []

    for record in records:
        match_found = False
        keys_to_search = fields if fields is not None else record.keys()

        for key in keys_to_search:
            value = record.get(key)
            if isinstance(value, str):
                if compiled_pattern.search(value):
                    match_found = True
                    break
            elif value is not None and not fields: # If no specific fields, convert non-strings to string for search
                if compiled_pattern.search(str(value)):
                    match_found = True
                    break
        if match_found:
            results.append(record)
    logger.info(f"Pattern search completed for pattern '{pattern}', found {len(results)} results.")
    return results

class HashedIndex:
    """
    A simple hashed index for speeding up exact keyword lookups on a specific field.
    Note: This is a basic in-memory hash map; it doesn't handle range or pattern searches directly.
    """
    def __init__(self, records: List[Dict[str, Any]], field: str):
        self.index = {}
        self.field = field
        self._build_index(records)
        logger.info(f"Hashed index built for field '{field}' with {len(self.index)} unique entries.")

    def _build_index(self, records: List[Dict[str, Any]]):
        for i, record in enumerate(records):
            value = record.get(self.field)
            if value is not None:
                # Store normalized value (e.g., lowercase for case-insensitive search)
                key = str(value).lower() if isinstance(value, str) else value
                if key not in self.index:
                    self.index[key] = []
                self.index[key].append(i) # Store index of record

    def search(self, query: Any, case_sensitive: bool = False, records_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Searches the index for an exact match.
        :param query: The exact value to search for.
        :param case_sensitive: If True, the search is case-sensitive for strings.
        :param records_list: The original list of records. Required to retrieve full records.
        :return: A list of matching records.
        """
        if records_list is None:
            logger.error("records_list must be provided to retrieve full records from HashedIndex.")
            return []

        normalized_query = query
        if isinstance(query, str) and not case_sensitive:
            normalized_query = query.lower()

        indices = self.index.get(normalized_query, [])
        results = [records_list[i] for i in indices]
        logger.info(f"Hashed index search for '{query}' on field '{self.field}', found {len(results)} results.")
        return results

# Example Usage
if __name__ == "__main__":
    sample_records = [
        {"id": 1, "vendor": "Walmart", "amount": 100.50, "date": "2023-01-15", "description": "Groceries at Walmart"},
        {"id": 2, "vendor": "Target", "amount": 50.25, "date": "2023-01-20", "description": "Clothes from Target"},
        {"id": 3, "vendor": "WALMART Supercenter", "amount": 200.00, "date": "2023-02-01", "description": "Electronics from Walmart"},
        {"id": 4, "vendor": "Local Cafe", "amount": 15.75, "date": "2023-02-05", "description": "Coffee and snacks"},
        {"id": 5, "vendor": "Amazon", "amount": 75.00, "date": "2023-02-10", "description": "Online shopping"},
        {"id": 6, "vendor": "Target", "amount": 30.00, "date": "2023-02-12", "description": "Home goods"}
    ]

    print("\n--- Linear Search ---")
    results = linear_search_records(sample_records, "walmart", fields=["vendor"], case_sensitive=False)
    print(f"Search 'walmart' in 'vendor' (case-insensitive): {len(results)} results")
    for r in results: print(r)

    results = linear_search_records(sample_records, "Target", fields=["vendor"], case_sensitive=True)
    print(f"Search 'Target' in 'vendor' (case-sensitive): {len(results)} results")
    for r in results: print(r)

    results = linear_search_records(sample_records, "snacks", fields=["description"])
    print(f"Search 'snacks' in 'description': {len(results)} results")
    for r in results: print(r)

    print("\n--- Range Search ---")
    results = range_search_records(sample_records, "amount", min_value=50, max_value=150)
    print(f"Search amount between 50 and 150: {len(results)} results")
    for r in results: print(r)

    results = range_search_records(sample_records, "amount", min_value=100)
    print(f"Search amount >= 100: {len(results)} results")
    for r in results: print(r)

    print("\n--- Pattern Search ---")
    results = pattern_search_records(sample_records, r"^Walm", fields=["vendor"])
    print(f"Pattern '^Walm' in 'vendor': {len(results)} results")
    for r in results: print(r)

    results = pattern_search_records(sample_records, r"online|electronics", fields=["description"])
    print(f"Pattern 'online|electronics' in 'description': {len(results)} results")
    for r in results: print(r)

    print("\n--- Hashed Index Search ---")
    vendor_index = HashedIndex(sample_records, "vendor")

    results = vendor_index.search("walmart", records_list=sample_records)
    print(f"Hashed search for 'walmart': {len(results)} results")
    for r in results: print(r)

    results = vendor_index.search("Target", case_sensitive=False, records_list=sample_records)
    print(f"Hashed search for 'Target' (case-insensitive): {len(results)} results")
    for r in results: print(r)

    results = vendor_index.search("Target", case_sensitive=True, records_list=sample_records)
    print(f"Hashed search for 'Target' (case-sensitive): {len(results)} results")
    for r in results: print(r)