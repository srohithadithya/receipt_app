from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import User, Receipt, Vendor, Category
from utils.security import hash_password # Assuming utils.security has hash_password function
from datetime import date, datetime
import logging

# Configure logging for CRUD operations
logging.basicConfig(level=logging.INFO)

# --- User CRUD Operations ---

def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Retrieves a user by their username.
    :param db: SQLAlchemy database session.
    :param username: The username to search for.
    :return: User object if found, else None.
    """
    return db.query(User).filter(func.lower(User.username) == func.lower(username)).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    Retrieves a user by their ID.
    :param db: SQLAlchemy database session.
    :param user_id: The ID of the user to search for.
    :return: User object if found, else None.
    """
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, username: str, password: str, email: str = None) -> User:
    """
    Creates a new user in the database.
    Hashes the password before storing.
    :param db: SQLAlchemy database session.
    :param username: Username for the new user.
    :param password: Plaintext password for the new user.
    :param email: Optional email for the new user.
    :return: The newly created User object.
    :raises ValueError: If username already exists.
    """
    if get_user_by_username(db, username):
        raise ValueError("Username already exists.")

    hashed_password = hash_password(password) # Hash the password
    db_user = User(username=username, password_hash=hashed_password, email=email)
    db.add(db_user)
    db.commit() # Commit the transaction
    db.refresh(db_user) # Refresh the instance to get its ID and other default values
    logging.info(f"User '{username}' created successfully.")
    return db_user

# --- Receipt CRUD Operations ---

def create_receipt(
    db: Session,
    owner_id: int,
    vendor_name: str,
    transaction_date: date,
    amount: float,
    currency: str = "USD",
    category_name: str = None,
    original_filename: str = "",
    parsed_raw_text: str = None,
    billing_period_start: date = None,
    billing_period_end: date = None
) -> Receipt:
    """
    Creates a new receipt record in the database.
    Automatically creates vendor and category if they don't exist.
    :param db: SQLAlchemy database session.
    :param owner_id: ID of the user who owns this receipt.
    :param vendor_name: Name of the vendor.
    :param transaction_date: Date of the transaction.
    :param amount: Amount of the transaction.
    :param currency: Currency of the transaction (default "USD").
    :param category_name: Optional category name for the receipt.
    :param original_filename: Original filename of the uploaded receipt.
    :param parsed_raw_text: Raw text extracted from the receipt.
    :param billing_period_start: Optional start date of billing period.
    :param billing_period_end: Optional end date of billing period.
    :return: The newly created Receipt object.
    """
    # Get or create Vendor
    vendor = db.query(Vendor).filter(func.lower(Vendor.name) == func.lower(vendor_name)).first()
    if not vendor:
        vendor = Vendor(name=vendor_name)
        db.add(vendor)
        db.flush() # Flush to assign an ID to the new vendor before committing the receipt
        logging.info(f"New vendor '{vendor_name}' created.")

    # Get or create Category (if provided)
    category = None
    if category_name:
        category = db.query(Category).filter(func.lower(Category.name) == func.lower(category_name)).first()
        if not category:
            category = Category(name=category_name)
            db.add(category)
            db.flush() # Flush to assign an ID to the new category
            logging.info(f"New category '{category_name}' created.")

    db_receipt = Receipt(
        owner_id=owner_id,
        vendor_id=vendor.id,
        transaction_date=transaction_date,
        amount=amount,
        currency=currency,
        category_id=category.id if category else None,
        original_filename=original_filename,
        parsed_raw_text=parsed_raw_text,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        upload_date=datetime.now() # Ensure upload_date is set explicitly
    )
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)
    logging.info(f"Receipt for '{vendor_name}' (Amount: {amount}) created for user {owner_id}.")
    return db_receipt

def get_receipts_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "transaction_date",
    sort_order: str = "desc"
) -> list[Receipt]:
    """
    Retrieves a list of receipts for a specific user, with pagination and sorting.
    :param db: SQLAlchemy database session.
    :param user_id: The ID of the user whose receipts to retrieve.
    :param skip: Number of records to skip (for pagination).
    :param limit: Maximum number of records to return (for pagination).
    :param sort_by: Field to sort by (e.g., "transaction_date", "amount", "vendor_name").
    :param sort_order: "asc" for ascending, "desc" for descending.
    :return: A list of Receipt objects.
    """
    query = db.query(Receipt).filter(Receipt.owner_id == user_id)

    # Apply joins for sorting by related table names
    if sort_by == "vendor_name":
        query = query.join(Vendor).order_by(Vendor.name.asc() if sort_order == "asc" else Vendor.name.desc())
    elif sort_by == "category_name":
        query = query.join(Category).order_by(Category.name.asc() if sort_order == "asc" else Category.name.desc())
    elif hasattr(Receipt, sort_by): # Check if the Receipt model has the attribute
        sort_column = getattr(Receipt, sort_by)
        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())
    else:
        # Default sort if invalid sort_by is provided
        query = query.order_by(Receipt.transaction_date.desc())


    return query.offset(skip).limit(limit).all()

def get_receipt_by_id(db: Session, receipt_id: int, owner_id: int) -> Receipt | None:
    """
    Retrieves a single receipt by its ID, ensuring it belongs to the specified owner.
    :param db: SQLAlchemy database session.
    :param receipt_id: The ID of the receipt to retrieve.
    :param owner_id: The ID of the owner for security.
    :return: Receipt object if found and belongs to owner, else None.
    """
    return db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.owner_id == owner_id).first()

def update_receipt(db: Session, receipt_id: int, owner_id: int, data: dict) -> Receipt | None:
    """
    Updates an existing receipt record.
    Allows partial updates by providing a dictionary of fields to update.
    Handles updating vendor and category by name if provided in data.
    :param db: SQLAlchemy database session.
    :param receipt_id: ID of the receipt to update.
    :param owner_id: ID of the owner (for authorization).
    :param data: Dictionary of fields and new values to update.
    :return: The updated Receipt object or None if not found/authorized.
    """
    db_receipt = get_receipt_by_id(db, receipt_id, owner_id)
    if not db_receipt:
        return None

    # Handle special cases for vendor and category names
    if 'vendor_name' in data:
        vendor_name = data.pop('vendor_name')
        vendor = db.query(Vendor).filter(func.lower(Vendor.name) == func.lower(vendor_name)).first()
        if not vendor:
            vendor = Vendor(name=vendor_name)
            db.add(vendor)
            db.flush()
            logging.info(f"New vendor '{vendor_name}' created during receipt update.")
        db_receipt.vendor_id = vendor.id

    if 'category_name' in data:
        category_name = data.pop('category_name')
        category = db.query(Category).filter(func.lower(Category.name) == func.lower(category_name)).first()
        if not category:
            category = Category(name=category_name)
            db.add(category)
            db.flush()
            logging.info(f"New category '{category_name}' created during receipt update.")
        db_receipt.category_id = category.id
    else: # If category_name is explicitly set to None (e.g., to uncategorize)
        if 'category_id' in data and data['category_id'] is None:
            db_receipt.category_id = None


    for key, value in data.items():
        if hasattr(db_receipt, key):
            setattr(db_receipt, key, value)
    
    db.commit()
    db.refresh(db_receipt)
    logging.info(f"Receipt ID {receipt_id} updated for user {owner_id}.")
    return db_receipt

def delete_receipt(db: Session, receipt_id: int, owner_id: int) -> bool:
    """
    Deletes a receipt record from the database.
    :param db: SQLAlchemy database session.
    :param receipt_id: ID of the receipt to delete.
    :param owner_id: ID of the owner (for authorization).
    :return: True if deleted successfully, False otherwise.
    """
    db_receipt = get_receipt_by_id(db, receipt_id, owner_id)
    if db_receipt:
        db.delete(db_receipt)
        db.commit()
        logging.info(f"Receipt ID {receipt_id} deleted for user {owner_id}.")
        return True
    logging.warning(f"Attempted to delete Receipt ID {receipt_id} for user {owner_id} but not found/authorized.")
    return False

# --- Vendor CRUD Operations ---

def get_vendor_by_name(db: Session, name: str) -> Vendor | None:
    """
    Retrieves a vendor by name.
    """
    return db.query(Vendor).filter(func.lower(Vendor.name) == func.lower(name)).first()

def get_all_vendors(db: Session) -> list[Vendor]:
    """
    Retrieves all vendors.
    """
    return db.query(Vendor).all()

def create_vendor(db: Session, name: str) -> Vendor:
    """
    Creates a new vendor.
    """
    db_vendor = Vendor(name=name)
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

# --- Category CRUD Operations ---

def get_category_by_name(db: Session, name: str) -> Category | None:
    """
    Retrieves a category by name.
    """
    return db.query(Category).filter(func.lower(Category.name) == func.lower(name)).first()

def get_all_categories(db: Session) -> list[Category]:
    """
    Retrieves all categories.
    """
    return db.query(Category).all()

def create_category(db: Session, name: str) -> Category:
    """
    Creates a new category.
    """
    db_category = Category(name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category