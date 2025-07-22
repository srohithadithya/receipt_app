import pytesseract
from PIL import Image
import cv2
import numpy as np
import logging
import re # Added for detect_language
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

        # Apply adaptive thresholding (good for varying lighting)
        # Using ADAPTIVE_THRESH_GAUSSIAN_C can be more robust than MEAN_C
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2) # Block size 11, C value 2

        # --- Optional: Noise Reduction (Median Blur) ---
        # Useful if image has salt-and-pepper noise
        # thresh = cv2.medianBlur(thresh, 3) # Apply a median blur with a 3x3 kernel

        # --- Optional: Deskewing (straighten slanted text) ---
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


        # --- Ensure image is 300 DPI for Tesseract (if original resolution is too low) ---
        # This is more conceptual for CV2 processing; actual DPI depends on initial image source
        # For actual DPI control, you might need to resize the image explicitly.
        # Example: if you know you want 300 DPI and current is 72, scale factor = 300/72
        # scaled_thresh = cv2.resize(thresh, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        # For this standard setup, we rely on the internal scaling of tesseract, or good input.

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
    # For language detection, sometimes raw image works better or a different preprocessing
    # For now, reuse the same preprocessing
    processed_img_np = preprocess_image_for_ocr(image_bytes)
    if processed_img_np is None:
        return None

    try:
        pil_img = Image.fromarray(processed_img_np)
        osd_output = pytesseract.image_to_osd(pil_img)
        # Parse the OSd output to find language. This is a simple regex.
        # Example OSD output:
        # Page number: 0
        # Orientation in degrees: 0
        # Rotate: 0
        # Orientation confidence: 26.21
        # Script: Latin
        # Script confidence: 4.67
        # Language: eng
        
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
