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
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session local class.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models.
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
