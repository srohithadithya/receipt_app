import pytesseract
from PIL import Image
import cv2
import numpy as np
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set the path to the tesseract executable if it's not in your PATH
# For Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# For macOS/Linux, usually not needed if installed via package manager.
# Ensure Tesseract is installed on your system as a prerequisite.

def preprocess_image_for_ocr(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Preprocesses an image (bytes) for better OCR accuracy.
    Converts to grayscale, applies thresholding, and can include deskewing.

    :param image_bytes: Raw image content as bytes.
    :return: Processed image as an OpenCV numpy array, or None if processing fails.
    """
    try:
        # Convert bytes to numpy array (OpenCV format)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_np is None:
            logger.error("Failed to decode image from bytes.")
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding for better text separation
        # Using ADAPTIVE_THRESH_GAUSSIAN_C might give better results for varied lighting
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2) # Block size 11, C value 2

        # Optional: Deskewing (straighten slanted text)
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = img_np.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        logger.info("Image preprocessed (grayscale, thresholded, deskewed).")
        return deskewed

    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}")
        return None

def extract_text_from_image(image_bytes: bytes, lang: str = 'eng') -> Optional[str]:
    """
    Extracts text from an image using Tesseract OCR after preprocessing.

    :param image_bytes: Raw image content as bytes.
    :param lang: OCR language code (e.g., 'eng' for English, 'hin' for Hindi).
    :return: Extracted text as a string, or None if OCR fails.
    """
    processed_img_np = preprocess_image_for_ocr(image_bytes)
    if processed_img_np is None:
        return None

    try:
        # Convert the OpenCV image (NumPy array) to a PIL Image for Tesseract
        pil_img = Image.fromarray(processed_img_np)
        text = pytesseract.image_to_string(pil_img, lang=lang)
        logger.info(f"Text extracted using Tesseract (lang={lang}).")
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not found in PATH. Please install Tesseract OCR engine.")
        return None
    except Exception as e:
        logger.error(f"Error during OCR text extraction: {e}")
        return None

def detect_language(image_bytes: bytes) -> Optional[str]:
    """
    Attempts to detect the language of the text in an image using Tesseract's OSd.
    Note: Tesseract's OSd (Orientation and Script Detection) is not always accurate for language,
    but it can give hints. Requires `osd` data for Tesseract.

    :param image_bytes: Raw image content as bytes.
    :return: Detected language code (e.g., 'eng', 'hin') or None.
    """
    processed_img_np = preprocess_image_for_ocr(image_bytes)
    if processed_img_np is None:
        return None

    try:
        pil_img = Image.fromarray(processed_img_np)
        osd = pytesseract.image_to_osd(pil_img)
        # Parse the OSd output to find language. This is a simple regex.
        # A more robust parser might be needed for complex OSd outputs.
        match = re.search(r"Script: (\w+)\nLanguage: (\w+)", osd)
        if match:
            lang_code = match.group(2).lower()
            logger.info(f"Detected language: {lang_code}")
            return lang_code
        logger.info("Could not reliably detect language from OSD output.")
        return None
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not found in PATH for OSD. Please install Tesseract OCR engine with OSD data.")
        return None
    except Exception as e:
        logger.error(f"Error during language detection: {e}")
        return None

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    import re
    # Create a dummy image file for testing
    # Note: For real testing, use an actual receipt image.
    dummy_img_path = "temp_dummy_receipt_for_ocr.png"
    try:
        from PIL import ImageDraw, ImageFont
        img_test = Image.new('RGB', (400, 100), color = (255, 255, 255))
        d = ImageDraw.Draw(img_test)
        # Try to use a default font or one available on your system
        try:
            # Common font paths for different OS
            font_path = "arial.ttf" # Windows
            # font_path = "/Library/Fonts/Arial.ttf" # macOS
            # font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Linux
            fnt = ImageFont.truetype(font_path, 20)
        except IOError:
            fnt = ImageFont.load_default()
            logger.warning("Could not load Arial.ttf, using default PIL font. Text might look different.")

        d.text((10,10), "Total: $123.45", fill=(0,0,0), font=fnt)
        d.text((10,40), "Vendor: Acme Store", fill=(0,0,0), font=fnt)
        img_test.save(dummy_img_path)

        with open(dummy_img_path, 'rb') as f:
            dummy_image_bytes = f.read()

        print("\n--- Testing extract_text_from_image (English) ---")
        extracted_text_eng = extract_text_from_image(dummy_image_bytes, lang='eng')
        if extracted_text_eng:
            print(f"Extracted Text (ENG):\n{extracted_text_eng}")
        else:
            print("Failed to extract text (English). Check Tesseract installation and path.")

        # Example for another language (requires language data installed for Tesseract)
        # Assuming you have 'hin' (Hindi) language data installed
        # print("\n--- Testing extract_text_from_image (Hindi) ---")
        # extracted_text_hin = extract_text_from_image(dummy_image_bytes, lang='hin')
        # if extracted_text_hin:
        #     print(f"Extracted Text (HIN):\n{extracted_text_hin}")

        print("\n--- Testing language detection ---")
        detected_lang = detect_language(dummy_image_bytes)
        if detected_lang:
            print(f"Detected Language: {detected_lang}")
        else:
            print("Language detection failed or inconclusive.")

    except ImportError:
        print("Pillow and OpenCV-Python are required for OCR_Utils example. Please install them (`pip install Pillow opencv-python`).")
    except Exception as e:
        print(f"An error occurred during OCR_Utils example execution: {e}")
    finally:
        # Clean up dummy image file
        if Path(dummy_img_path).exists():
            Path(dummy_img_path).unlink()
            print(f"\nCleaned up {dummy_img_path}.")