import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# For Streamlit, st.file_uploader provides BytesIO object, not a direct file path.
BASE_DATA_DIR = Path("data")
RAW_RECEIPTS_DIR = BASE_DATA_DIR / "raw_receipts"

# Ensure the directories exist
RAW_RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file_buffer) -> Tuple[Optional[Path], Optional[str]]:
    """
    Saves an uploaded Streamlit file buffer to the raw_receipts directory.
    This function should be called with the object returned by st.file_uploader.

    :param uploaded_file_buffer: The file-like object (BytesIO) received from Streamlit's file_uploader.
    :return: A tuple containing the Path to the saved file and its original filename,
             or (None, None) if saving fails.
    """
    if uploaded_file_buffer is None:
        logger.warning("No file buffer provided to save_uploaded_file.")
        return None, None

    original_filename = uploaded_file_buffer.name
    file_path = RAW_RECEIPTS_DIR / original_filename

    try:
        # Write the file content to the specified path
        with open(file_path, "wb") as f:
            f.write(uploaded_file_buffer.getbuffer())
        logger.info(f"File saved successfully: {file_path}")
        return file_path, original_filename
    except Exception as e:
        logger.error(f"Failed to save file {original_filename}: {e}")
        return None, None

def read_file_content(file_path: Path, file_type: str) -> Optional[bytes]:
    """
    Reads the raw byte content of a file based on its type.
    This is less about parsing structured data and more about getting the raw bytes
    for OCR or text processing.

    :param file_path: Path to the file.
    :param file_type: The validated type of the file ('image', 'pdf', 'text').
    :return: The raw content of the file as bytes, or None if reading fails.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        logger.info(f"Read {file_type} file content from {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading {file_type} file {file_path}: {e}")
        return None

# Example usage (for testing/demonstration, requires a dummy file)
if __name__ == "__main__":
    # Create dummy files for testing
    test_dir = Path("data/test_ingestion")
    test_dir.mkdir(parents=True, exist_ok=True)

    dummy_txt_path = test_dir / "dummy_receipt.txt"
    with open(dummy_txt_path, "w") as f:
        f.write("Vendor: Test Mart\nDate: 2023-01-01\nAmount: 123.45")

    dummy_img_path = test_dir / "dummy_receipt.png"
    # Create a dummy image file (e.g., using Pillow)
    from PIL import Image
    img = Image.new('RGB', (60, 30), color = (73, 109, 137))
    img.save(dummy_img_path)

    # Simulate Streamlit uploaded file object
    class MockUploadedFile:
        def __init__(self, path: Path):
            self.name = path.name
            with open(path, 'rb') as f:
                self._content = f.read()

        def getbuffer(self):
            # Simulate BytesIO getbuffer()
            import io
            return io.BytesIO(self._content).getbuffer()

    print("\n--- Testing save_uploaded_file ---")
    mock_txt_file = MockUploadedFile(dummy_txt_path)
    saved_path_txt, saved_name_txt = save_uploaded_file(mock_txt_file)
    if saved_path_txt:
        print(f"Saved TXT file: {saved_path_txt}")
        # Clean up the saved file for testing
        if saved_path_txt.exists():
            saved_path_txt.unlink()

    mock_img_file = MockUploadedFile(dummy_img_path)
    saved_path_img, saved_name_img = save_uploaded_file(mock_img_file)
    if saved_path_img:
        print(f"Saved IMG file: {saved_path_img}")
        # Clean up the saved file for testing
        if saved_path_img.exists():
            saved_path_img.unlink()

    print("\n--- Testing read_file_content ---")
    # To test read_file_content, we'll read the original dummy files
    content_txt = read_file_content(dummy_txt_path, 'text')
    if content_txt:
        print(f"Content of TXT file (first 50 chars): {content_txt.decode('utf-8')[:50]}...")

    content_img = read_file_content(dummy_img_path, 'image')
    if content_img:
        print(f"Content of IMG file (first 50 bytes): {content_img[:50]}...")

    # Clean up dummy test files and directory
    dummy_txt_path.unlink()
    dummy_img_path.unlink()
    test_dir.rmdir()
    print("\nCleaned up test files.")
