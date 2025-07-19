from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging for SQLAlchemy
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO) # Or INFO for less verbose

# SQLite database URL. The database file will be created in the project root.
DATABASE_URL = "sqlite:///./receipt_app.db"

# Create a SQLAlchemy engine.
# connect_args={"check_same_thread": False} is required for SQLite with FastAPI/Streamlit
# because SQLite doesn't allow multiple threads to access the same connection by default.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session local class.
# This instance of SessionLocal will be the actual database session.
# autocommit=False means transactions are not committed automatically.
# autoflush=False means objects are not flushed to the database until commit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models.
# All SQLAlchemy models will inherit from this Base.
Base = declarative_base()

def get_db():
    """
    Dependency function to get a database session.
    This is designed to be used with `with` statements or `yield` in frameworks.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback() # Rollback in case of an error
        logging.error(f"Database error occurred: {e}")
        raise # Re-raise the exception after rollback
    finally:
        db.close()

def create_db_tables():
    """
    Creates all database tables defined by SQLAlchemy models inheriting from Base.
    This function should be called once at application startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully or already exist.")
    except SQLAlchemyError as e:
        logging.error(f"Error creating database tables: {e}")
        raise # Re-raise the exception if table creation fails

# It's good practice to call create_db_tables at the application's entry point (e.g., app.py)
# rather than directly here to ensure the engine is fully set up and avoid circular imports.
# However, for a complete standalone file, uncommenting this will create tables upon import.
# create_db_tables()