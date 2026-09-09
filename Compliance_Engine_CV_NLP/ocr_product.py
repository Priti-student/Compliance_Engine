from PIL import Image
import pytesseract

# Path to your product image
image_path = "package_003.jpg"

# Load image
image = Image.open(image_path)

# Extract text using OCR
text = pytesseract.image_to_string(image)

# Display extracted text
print("\n========== EXTRACTED PRODUCT TEXT ==========\n")
print(text)
print("============================================")