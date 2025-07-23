import os
import pytesseract
import cv2
import google.generativeai as genai
import json
from dotenv import load_dotenv

# Path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load environment variables and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest")

def extract_text_from_image(image_path):
    """Preprocess image and extract text using Tesseract OCR."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image file.")

        # Preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # OCR Configuration
        config = r'--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:/- '
        text = pytesseract.image_to_string(gray, config=config)

        # Optional: Save preprocessed image for debugging
        debug_path = os.path.join(os.path.dirname(image_path), "debug_processed.png")
        cv2.imwrite(debug_path, gray)

        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def extract_marks_from_text(raw_text):
    """Use Gemini to extract student name and marks as JSON."""
    try:
        prompt = f"""
ANALYZE THE FOLLOWING OCR TEXT FROM AN ANSWER SHEET AND EXTRACT:

1. The student's name (e.g., "Name: Ravi Kumar", "Student: Priya Sharma", etc.)
2. Subject-mark pairs such as:
   - Math: 85
   - Science - 92%
   - English 78/100

👉 STRICTLY RETURN JSON like:
{{
  "student_name": "Ravi Kumar",
  "Math": 85,
  "Science": 92,
  "English": 78
}}

INPUT TEXT:
\"\"\" 
{raw_text} 
\"\"\"

❌ DO NOT RETURN ANY EXPLANATION — ONLY THE JSON ABOVE.
"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Extract pure JSON if markdown wrapped
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()

        return response_text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return '{"error": "Failed to extract marks or student name."}'
