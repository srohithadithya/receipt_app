import pytesseract
from PIL import Image
import cv2
import numpy as np
import logging
import re # Added for detect_language
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# For Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# For macOS/Linux, usually not needed if installed via package manager.
# Ensure Tesseract is installed on your system as a prerequisite.

def preprocess_image_for_ocr(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Preprocesses an image (bytes) for better OCR accuracy.
    Converts to grayscale, applies thresholding, and can include deskewing and noise reduction.

    :param image_bytes: Raw image content as bytes.
    :return: Processed image as an OpenCV numpy array, or None if processing fails.
    """
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_np is None:
            logger.error("Failed to decode image from bytes in preprocess_image_for_ocr.")
            return None

        # --- Basic Preprocessing ---
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2) # Block size 11, C value 2

        # Only attempt if the image is large enough
        if thresh.shape[0] > 10 and thresh.shape[1] > 10:
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) > 0: # Ensure there are white pixels to find contours
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                (h, w) = img_np.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                thresh = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                logger.debug(f"Image deskewed by {angle:.2f} degrees.")
            else:
                logger.debug("No contours found for deskewing.")
        else:
            logger.debug("Image too small for deskewing attempt.")


        # --- Ensure image is 300 DPI for Tesseract (if original resolution is too low) 
        logger.info("Image preprocessed (grayscale, adaptive thresholded, deskewed attempted).")
        return thresh # Return the processed NumPy array

    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}", exc_info=True)
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
        logger.error("Preprocessing failed, cannot perform OCR.")
        return None

    try:
        # Convert the OpenCV image (NumPy array) to a PIL Image for Tesseract
        pil_img = Image.fromarray(processed_img_np)
        text = pytesseract.image_to_string(pil_img, lang=lang, config='--psm 6') # --psm 6 is often good for a single uniform block of text (like a receipt)
        logger.info(f"Text extracted using Tesseract (lang={lang}, PSM 6).")
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not found in PATH. Please install Tesseract OCR engine.", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error during OCR text extraction: {e}", exc_info=True)
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
        osd_output = pytesseract.image_to_osd(pil_img)
        
        # Regex to capture the language code
        match = re.search(r"Language:\s*(\w+)", osd_output, re.IGNORECASE)
        if match:
            lang_code = match.group(1).lower()
            logger.info(f"Detected language: {lang_code} from OSD output.")
            return lang_code
        logger.info("Could not reliably detect language from OSD output or OSD data missing.")
        return None
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or missing OSD data. Cannot perform language detection.", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error during language detection: {e}", exc_info=True)
        return None
