from typing import Optional, Any, Dict # Added Any here

class AppError(Exception):
    """Base exception for all custom application-specific errors."""
    def __init__(self, message: str = "An application error occurred.", details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
        # Log the error for debugging purposes
        import logging
        logger = logging.getLogger(__name__)
        # Ensure logger is initialized if this file is run directly for testing purposes
        if not logger.handlers:
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger.error(f"AppError: {message} | Details: {details}")

class FileProcessingError(AppError):
    """
    Raised when there's an issue reading, writing, saving, or handling a file.
    Examples: file not found, permission denied, unsupported format.
    """
    def __init__(self, message: str = "Error processing file.", filename: Optional[str] = None, original_error: Optional[Exception] = None):
        details = {"filename": filename, "original_error": str(original_error)} if filename or original_error else None
        super().__init__(message, details)
        self.filename = filename
        self.original_error = original_error

class ParsingError(AppError):
    """
    Raised when structured data extraction (e.g., from OCR text) or data validation fails.
    Examples: expected data not found, extracted data is malformed, Pydantic validation error.
    """
    def __init__(self, message: str = "Error parsing document data.", document_id: Optional[Any] = None, original_text: Optional[str] = None, original_error: Optional[Exception] = None):
        details = {"document_id": document_id, "original_text": original_text, "original_error": str(original_error)} if any([document_id, original_text, original_error]) else None
        super().__init__(message, details)
        self.document_id = document_id
        self.original_text = original_text
        self.original_error = original_error

class DatabaseError(AppError):
    """
    Raised when a database operation fails unexpectedly.
    Examples: connection issues, integrity errors, unexpected query results.
    """
    def __init__(self, message: str = "Database operation failed.", query_details: Optional[Dict] = None, original_error: Optional[Exception] = None):
        details = {"query_details": query_details, "original_error": str(original_error)} if query_details or original_error else None
        super().__init__(message, details)
        self.query_details = query_details
        self.original_error = original_error

class AuthenticationError(AppError):
    """
    Raised when user authentication or authorization fails.
    Examples: invalid credentials, unauthorized access.
    """
    def __init__(self, message: str = "Authentication failed.", username: Optional[str] = None, reason: Optional[str] = None):
        details = {"username": username, "reason": reason} if username or reason else None
        super().__init__(message, details)
        self.username = username
        self.reason = reason

# Example Usage (for testing/demonstration)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO) # Set logging level for demo

    print("\n--- Custom Error Handling Demo ---")

    try:
        raise FileProcessingError("Could not read image file.", filename="test.jpg", original_error=FileNotFoundError("No such file"))
    except FileProcessingError as e:
        print(f"Caught FileProcessingError: {e.message} | Filename: {e.filename} | Original Error: {e.original_error}")

    try:
        raise ParsingError("Amount could not be extracted.", document_id=123, original_text="Total: ABC", original_error=ValueError("Invalid float"))
    except ParsingError as e:
        print(f"Caught ParsingError: {e.message} | Doc ID: {e.document_id} | Original Text Snippet: {e.original_text} | Original Error: {e.original_error}")

    try:
        # Simulate a database error
        from sqlalchemy.exc import IntegrityError
        raise DatabaseError("Failed to insert user.", query_details={"user": "test_user"}, original_error=IntegrityError(None, None, None))
    except DatabaseError as e:
        print(f"Caught DatabaseError: {e.message} | Query: {e.query_details} | Original Error: {e.original_error}")

    try:
        raise AuthenticationError("Invalid username or password.", username="nonexistent_user", reason="credentials mismatch")
    except AuthenticationError as e:
        print(f"Caught AuthenticationError: {e.message} | User: {e.username} | Reason: {e.reason}")

    try:
        raise AppError("A generic application issue.")
    except AppError as e:
        print(f"Caught AppError: {e.message}")
