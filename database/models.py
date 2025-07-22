from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from database.database import Base

class User(Base):
    """
    SQLAlchemy model for storing user information.
    """
    __tablename__ = "users" # Table name in the database

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # Stores the hashed password
    email = Column(String, unique=True, index=True, nullable=True) # Optional email
    created_at = Column(DateTime, default=datetime.now) # Timestamp for creation

    # Define a one-to-many relationship with Receipt.
    # 'back_populates' links this relationship back to the 'owner' attribute in the Receipt model.
    receipts = relationship("Receipt", back_populates="owner")

class Vendor(Base):
    """
    SQLAlchemy model for storing vendor information.
    """
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # Unique vendor name

    # One-to-many relationship with Receipt.
    receipts = relationship("Receipt", back_populates="vendor")

class Category(Base):
    """
    SQLAlchemy model for storing spending categories.
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # Unique category name

    # One-to-many relationship with Receipt.
    receipts = relationship("Receipt", back_populates="category")

class Receipt(Base):
    """
    SQLAlchemy model for storing parsed receipt and bill data.
    """
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Foreign key linking to User
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True) # Foreign key linking to Vendor
    transaction_date = Column(Date, nullable=False) # Date of the transaction
    billing_period_start = Column(Date, nullable=True) # Optional start of billing period
    billing_period_end = Column(Date, nullable=True) # Optional end of billing period
    amount = Column(Float, nullable=False) # Transaction amount
    currency = Column(String, default="USD") # Bonus: Currency detection, default USD
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True) # Foreign key linking to Category
    original_filename = Column(String, nullable=False) # Name of the original uploaded file
    parsed_raw_text = Column(Text, nullable=True) # Stores the raw text extracted from OCR/parsing
    upload_date = Column(DateTime, default=datetime.now) # Timestamp for upload

    # Define relationships with other models.
    owner = relationship("User", back_populates="receipts")
    vendor = relationship("Vendor", back_populates="receipts")
    category = relationship("Category", back_populates="receipts")
