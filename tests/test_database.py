import pytest
from database import crud
from database.models import User, Receipt, Vendor, Category
from sqlalchemy.exc import IntegrityError
from datetime import date

# Fixtures for db_session and test_user_data are provided by conftest.py

def test_create_user(db_session, test_user_data):
    """Test creating a new user."""
    user = crud.create_user(db_session, **test_user_data)
    assert user.id is not None
    assert user.username == test_user_data["username"]
    assert crud.get_user_by_username(db_session, test_user_data["username"]) == user

def test_create_duplicate_user_raises_error(db_session, test_user_data):
    """Test that creating a user with a duplicate username raises an error."""
    crud.create_user(db_session, **test_user_data)
    with pytest.raises(ValueError, match="Username already exists"):
        crud.create_user(db_session, **test_user_data)

def test_get_user_by_username(db_session, create_test_user):
    """Test retrieving a user by username (case-insensitive)."""
    user = create_test_user
    retrieved_user_lower = crud.get_user_by_username(db_session, user.username.lower())
    assert retrieved_user_lower is not None
    assert retrieved_user_lower.username == user.username

    retrieved_user_upper = crud.get_user_by_username(db_session, user.username.upper())
    assert retrieved_user_upper is not None
    assert retrieved_user_upper.username == user.username

    assert crud.get_user_by_username(db_session, "nonexistent") is None

def test_get_user_by_id(db_session, create_test_user):
    """Test retrieving a user by ID."""
    user = create_test_user
    retrieved_user = crud.get_user_by_id(db_session, user.id)
    assert retrieved_user == user
    assert crud.get_user_by_id(db_session, 99999) is None

def test_create_vendor(db_session):
    """Test creating a vendor."""
    vendor = crud.create_vendor(db_session, name="New Vendor")
    assert vendor.id is not None
    assert vendor.name == "New Vendor"
    assert crud.get_vendor_by_name(db_session, "new vendor").name == "New Vendor" # Case-insensitive lookup

def test_create_category(db_session):
    """Test creating a category."""
    category = crud.create_category(db_session, name="New Category")
    assert category.id is not None
    assert category.name == "New Category"
    assert crud.get_category_by_name(db_session, "new category").name == "New Category" # Case-insensitive lookup

def test_create_receipt(db_session, create_test_user):
    """Test creating a receipt with new vendor/category."""
    user = create_test_user
    receipt = crud.create_receipt(
        db_session,
        owner_id=user.id,
        vendor_name="Test Shop",
        transaction_date=date(2023, 1, 1),
        amount=123.45,
        currency="USD",
        category_name="Electronics",
        original_filename="test.jpg"
    )
    assert receipt.id is not None
    assert receipt.owner_id == user.id
    assert receipt.vendor.name == "Test Shop"
    assert receipt.category.name == "Electronics"
    assert receipt.amount == 123.45
    assert receipt.transaction_date == date(2023, 1, 1)

    # Test creating another receipt using existing vendor/category
    receipt2 = crud.create_receipt(
        db_session,
        owner_id=user.id,
        vendor_name="Test Shop", # Existing
        transaction_date=date(2023, 1, 2),
        amount=10.00,
        category_name="Electronics", # Existing
        original_filename="test2.jpg"
    )
    assert receipt2.vendor.id == receipt.vendor.id
    assert receipt2.category.id == receipt.category.id

def test_get_receipts_by_user(db_session, create_sample_receipts):
    """Test retrieving receipts for a specific user."""
    user_id = create_sample_receipts[0].owner_id
    receipts = crud.get_receipts_by_user(db_session, user_id)
    assert len(receipts) == len(create_sample_receipts)
    assert all(r.owner_id == user_id for r in receipts)

    # Test sorting
    sorted_by_date_desc = crud.get_receipts_by_user(db_session, user_id, sort_by="transaction_date", sort_order="desc")
    assert sorted_by_date_desc[0].transaction_date == date(2023, 3, 10)
    assert sorted_by_date_desc[-1].transaction_date == date(2023, 1, 15)

    sorted_by_amount_asc = crud.get_receipts_by_user(db_session, user_id, sort_by="amount", sort_order="asc")
    assert sorted_by_amount_asc[0].amount == 15.00
    assert sorted_by_amount_asc[-1].amount == 120.00

    # Test vendor_name sort
    sorted_by_vendor_asc = crud.get_receipts_by_user(db_session, user_id, sort_by="vendor_name", sort_order="asc")
    assert sorted_by_vendor_asc[0].vendor.name == "Amazon Online"

def test_get_receipt_by_id(db_session, create_sample_receipts):
    """Test retrieving a single receipt by ID and owner."""
    receipt = create_sample_receipts[0]
    retrieved = crud.get_receipt_by_id(db_session, receipt.id, receipt.owner_id)
    assert retrieved == receipt
    assert crud.get_receipt_by_id(db_session, receipt.id, 9999) is None # Wrong owner
    assert crud.get_receipt_by_id(db_session, 9999, receipt.owner_id) is None # Non-existent ID

def test_update_receipt(db_session, create_sample_receipts):
    """Test updating a receipt."""
    receipt = create_sample_receipts[0]
    original_amount = receipt.amount
    original_vendor_name = receipt.vendor.name

    updated_data = {
        "amount": 150.75,
        "vendor_name": "Updated Vendor", # New vendor
        "category_name": "New Category For Update", # New category
        "currency": "CAD",
        "transaction_date": date(2023, 4, 1)
    }
    updated_receipt = crud.update_receipt(db_session, receipt.id, receipt.owner_id, updated_data)

    assert updated_receipt is not None
    assert updated_receipt.amount == 150.75
    assert updated_receipt.vendor.name == "Updated Vendor" # New vendor should be created
    assert updated_receipt.category.name == "New Category For Update" # New category should be created
    assert updated_receipt.currency == "CAD"
    assert updated_receipt.transaction_date == date(2023, 4, 1)

    # Test partial update
    updated_receipt2 = crud.update_receipt(db_session, receipt.id, receipt.owner_id, {"amount": 160.00})
    assert updated_receipt2.amount == 160.00
    assert updated_receipt2.vendor.name == "Updated Vendor" # Vendor should remain the same

    # Test updating category to None
    updated_receipt3 = crud.update_receipt(db_session, receipt.id, receipt.owner_id, {"category_name": None})
    assert updated_receipt3.category_id is None

def test_delete_receipt(db_session, create_sample_receipts):
    """Test deleting a receipt."""
    receipt_to_delete = create_sample_receipts[0]
    owner_id = receipt_to_delete.owner_id
    receipt_id = receipt_to_delete.id

    result = crud.delete_receipt(db_session, receipt_id, owner_id)
    assert result is True
    assert crud.get_receipt_by_id(db_session, receipt_id, owner_id) is None

    # Try deleting non-existent or unauthorized receipt
    assert crud.delete_receipt(db_session, receipt_id, owner_id) is False # Already deleted
    assert crud.delete_receipt(db_session, create_sample_receipts[1].id, 9999) is False # Wrong owner