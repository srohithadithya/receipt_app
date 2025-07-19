from passlib.hash import bcrypt
import re
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt.

    Bcrypt is a robust, adaptive, and widely-recommended password hashing function.
    It automatically handles salt generation, making each hash unique for the same password.

    :param password: The plaintext password string.
    :return: The bcrypt hashed password string.
    :raises TypeError: If the input password is not a string.
    """
    if not isinstance(password, str):
        logger.error(f"Attempted to hash a non-string password: {type(password)}")
        raise TypeError("Password must be a string.")
    try:
        hashed = bcrypt.hash(password)
        logger.debug("Password hashed successfully.")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise # Re-raise the exception after logging

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hashed password.

    :param password: The plaintext password string to verify.
    :param hashed_password: The bcrypt hashed password string stored in the database.
    :return: True if the password matches the hash, False otherwise.
    :raises TypeError: If inputs are not strings.
    """
    if not isinstance(password, str) or not isinstance(hashed_password, str):
        logger.error("Attempted to verify non-string password or hash.")
        raise TypeError("Both password and hashed_password must be strings.")
    try:
        is_valid = bcrypt.verify(password, hashed_password)
        if not is_valid:
            logger.warning("Password verification failed for a user (invalid credentials).")
        else:
            logger.debug("Password verification successful.")
        return is_valid
    except ValueError:
        # This typically happens if the hashed_password format is invalid/corrupted
        logger.error("Invalid hashed password format encountered during verification.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        raise # Re-raise the exception after logging

def validate_password_strength(password: str) -> bool:
    """
    Validates the strength of a password based on common criteria.

    Criteria:
    - Minimum length: 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (non-alphanumeric)

    :param password: The plaintext password string to validate.
    :return: True if the password meets all strength criteria, False otherwise.
    """
    if not isinstance(password, str):
        logger.warning(f"Attempted to validate password strength for non-string type: {type(password)}")
        return False

    if len(password) < 8:
        logger.debug("Password fails strength: too short.")
        return False
    if not re.search(r"[A-Z]", password):
        logger.debug("Password fails strength: no uppercase.")
        return False
    if not re.search(r"[a-z]", password):
        logger.debug("Password fails strength: no lowercase.")
        return False
    if not re.search(r"\d", password):
        logger.debug("Password fails strength: no digit.")
        return False
    # Use a regex that matches any character that is not a letter, number, or underscore
    if not re.search(r"[^a-zA-Z0-9\s]", password): # Allows spaces, if spaces are allowed in pw
        logger.debug("Password fails strength: no special character.")
        return False

    logger.debug("Password meets strength requirements.")
    return True

# Example Usage (for testing/demonstration)
if __name__ == "__main__":
    test_password = "MyStrongPassword123!"
    weak_password = "password"
    no_special_char = "MyStrongPassword123"
    no_digit = "MyStrongPassword!"

    print("\n--- Password Hashing and Verification ---")
    hashed_pw = hash_password(test_password)
    print(f"Original Password: {test_password}")
    print(f"Hashed Password: {hashed_pw}")

    print(f"Verification (Correct Password): {verify_password(test_password, hashed_pw)}")
    print(f"Verification (Incorrect Password): {verify_password('wrong_password', hashed_pw)}")
    print(f"Verification (Invalid Hash Format): {verify_password(test_password, 'invalid_hash')}")

    print("\n--- Password Strength Validation ---")
    print(f"'{test_password}' is strong: {validate_password_strength(test_password)}")
    print(f"'{weak_password}' is strong: {validate_password_strength(weak_password)}")
    print(f"'{no_special_char}' is strong: {validate_password_strength(no_special_char)}")
    print(f"'{no_digit}' is strong: {validate_password_strength(no_digit)}")
    print(f"'' (empty) is strong: {validate_password_strength('')}")