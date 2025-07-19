import pytest
from utils import security
from utils.errors import AuthenticationError # Assuming this custom error is defined

# Fixture for password hashing is implicitly used by utils.security

def test_hash_password_returns_string():
    """Test that hash_password returns a string."""
    password = "testpassword"
    hashed_pw = security.hash_password(password)
    assert isinstance(hashed_pw, str)
    assert hashed_pw != password # Hashed password should not be plaintext

def test_hash_password_for_same_input_is_different():
    """Test that hashing the same password twice produces different hashes due to salting."""
    password = "another_password"
    hashed_pw1 = security.hash_password(password)
    hashed_pw2 = security.hash_password(password)
    assert hashed_pw1 != hashed_pw2

def test_verify_password_correctly():
    """Test that verify_password correctly validates a correct password."""
    password = "CorrectHorseBatteryStaple"
    hashed_pw = security.hash_password(password)
    assert security.verify_password(password, hashed_pw) is True

def test_verify_password_incorrectly():
    """Test that verify_password correctly identifies an incorrect password."""
    password = "CorrectHorseBatteryStaple"
    hashed_pw = security.hash_password(password)
    assert security.verify_password("WrongPassword", hashed_pw) is False

def test_verify_password_invalid_hash():
    """Test that verify_password handles invalid hash formats gracefully."""
    password = "testpassword"
    invalid_hash = "thisisnotavalidhashformat"
    assert security.verify_password(password, invalid_hash) is False

def test_validate_password_strength_valid():
    """Test a password that meets all strength criteria."""
    valid_password = "MyStrongP@ssw0rd1"
    assert security.validate_password_strength(valid_password) is True

def test_validate_password_strength_too_short():
    """Test password strength: too short."""
    assert security.validate_password_strength("short") is False

def test_validate_password_strength_no_uppercase():
    """Test password strength: no uppercase."""
    assert security.validate_password_strength("mystrongp@ssw0rd1") is False

def test_validate_password_strength_no_lowercase():
    """Test password strength: no lowercase."""
    assert security.validate_password_strength("MYSTRONGP@SSW0RD1") is False

def test_validate_password_strength_no_digit():
    """Test password strength: no digit."""
    assert security.validate_password_strength("MyStrongP@ssword!") is False

def test_validate_password_strength_no_special_char():
    """Test password strength: no special character."""
    assert security.validate_password_strength("MyStrongPassword123") is False

def test_validate_password_strength_empty_string():
    """Test password strength: empty string."""
    assert security.validate_password_strength("") is False

def test_validate_password_strength_none_input():
    """Test password strength: None input."""
    assert security.validate_password_strength(None) is False