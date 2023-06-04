import cv2
import pytesseract
import re


def preprocess_image(image_path, denoising_h=10, denoising_template_window=7, denoising_search_window=21):
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    # Apply image preprocessing techniques
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply denoising
    denoised = cv2.fastNlMeansDenoising(
        gray, h=denoising_h, templateWindowSize=denoising_template_window, searchWindowSize=denoising_search_window)

    # Apply additional preprocessing steps as needed
    # ...

    return denoised


def extract_id(image_path):
    # Preprocess the image
    preprocessed_image = preprocess_image(image_path)

    # Extract text using Tesseract OCR
    extracted_text = pytesseract.image_to_string(preprocessed_image)

    # Extract the unique ID from the extracted text
    unique_id = None

    # Update the regular expression pattern to match the desired ID pattern
    pattern = r'[A-Z]{6}\d{8}[A-Z]\d{3}'

    # Search for the pattern within the extracted text
    match = re.search(pattern, extracted_text)
    if match:
        unique_id = match.group(0)
        print(unique_id)

    return unique_id
