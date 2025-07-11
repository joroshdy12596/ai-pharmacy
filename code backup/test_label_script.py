# test_label_script.py
"""
Test script to generate a sample barcode label image for visual inspection.
This script does NOT require Django and can be run standalone.
"""
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import os
import sys
import subprocess

# Label settings
LABEL_WIDTH_MM = 40
LABEL_HEIGHT_MM = 25
DPI = 203
MM_TO_INCH = 25.4
WIDTH_PX = int(LABEL_WIDTH_MM / MM_TO_INCH * DPI)
HEIGHT_PX = int(LABEL_HEIGHT_MM / MM_TO_INCH * DPI)

# Sample data (replace as needed)
PHARMACY_NAME = "صيدلية الإسراء"
PRODUCT_NAME = "بانادول إكسترا"
PRICE = "15 ج.م"
BARCODE_VALUE = "6223003570187"

# Font settings (adjust path if needed)
FONT_PATHS = [
    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
    "C:\\Windows\\Fonts\\Tahoma.ttf",  # Windows alternative
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
]
FONT_SIZE = 22
font = None
for path in FONT_PATHS:
    try:
        font = ImageFont.truetype(path, FONT_SIZE)
        break
    except OSError:
        continue
if font is None:
    from PIL import ImageFont
    font = ImageFont.load_default()
    print("Warning: Could not load TTF font, using default font.")

# --- Arabic text shaping and bidi ---
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def shape_arabic(text):
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
except ImportError:
    print("Warning: arabic_reshaper and python-bidi are not installed. Arabic text may not render correctly.")
    def shape_arabic(text):
        return text

# Shape Arabic text
PHARMACY_NAME_SHAPED = shape_arabic(PHARMACY_NAME)
PRODUCT_NAME_SHAPED = shape_arabic(PRODUCT_NAME)

# Create blank label
image = Image.new("L", (WIDTH_PX, HEIGHT_PX), 255)
draw = ImageDraw.Draw(image)

# Helper to get text width and height
def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

# Draw pharmacy name (top, centered)
pharmacy_w, pharmacy_h = get_text_size(draw, PHARMACY_NAME_SHAPED, font)
draw.text(((WIDTH_PX - pharmacy_w) // 2, 5), PHARMACY_NAME_SHAPED, font=font, fill=0)

# Draw product name (centered)
product_w, product_h = get_text_size(draw, PRODUCT_NAME_SHAPED, font)
draw.text(((WIDTH_PX - product_w) // 2, 5 + pharmacy_h + 2), PRODUCT_NAME_SHAPED, font=font, fill=0)

# Draw price (move higher)
price_w, price_h = get_text_size(draw, PRICE, font)
# Move price up by 10 pixels from the bottom
price_y = HEIGHT_PX - price_h - 15
if price_y < 0:
    price_y = 0
# Draw price
draw.text(((WIDTH_PX - price_w) // 2, price_y), PRICE, font=font, fill=0)

# Generate barcode image (suppress text inside barcode)
code128 = barcode.get('code128', BARCODE_VALUE, writer=ImageWriter())
barcode_img_path = code128.save("test_barcode", options={"module_height": 8.0, "font_size": 10, "text_distance": 1, "quiet_zone": 1, "write_text": False})
# Make barcode a little smaller: width and height
barcode_width = WIDTH_PX - 30  # slightly smaller width
barcode_height = HEIGHT_PX - (5 + pharmacy_h + 2 + product_h + 5 + price_h + 15) - 10  # slightly less tall
if barcode_height < 20:
    barcode_height = 20  # minimum height
barcode_img = Image.open(barcode_img_path).convert("L").resize((barcode_width, barcode_height))

# Paste barcode (shift right by 20px)
barcode_y = 5 + pharmacy_h + 2 + product_h + 5
barcode_x = 36  # shift right by 20 pixels
image.paste(barcode_img, (barcode_x, barcode_y))

# Draw barcode number under the barcode
barcode_number_w, barcode_number_h = get_text_size(draw, BARCODE_VALUE, font)
barcode_number_x = (WIDTH_PX - barcode_number_w) // 2
barcode_number_y = barcode_y + barcode_height + 2  # 2px below barcode
if barcode_number_y + barcode_number_h < HEIGHT_PX:
    draw.text((barcode_number_x, barcode_number_y), BARCODE_VALUE, font=font, fill=0)

# Save final label image
output_path = "test_label_output.png"
image.save(output_path)
print(f"Label image saved to {output_path}")

# --- Windows direct printing helpers ---
def list_windows_printers():
    try:
        import win32print
        printers = win32print.EnumPrinters(2)
        print("Available printers:")
        for p in printers:
            print(f"- {p[2]}")
    except ImportError:
        print("pywin32 is not installed. Run: pip install pywin32")

def print_image_to_printer(image_path, printer_name=None):
    try:
        import win32print
        import win32ui
        from PIL import ImageWin
        # Open the image
        img = Image.open(image_path)
        hDC = win32ui.CreateDC()
        if printer_name is None:
            printer_name = win32print.GetDefaultPrinter()
        hDC.CreatePrinterDC(printer_name)
        printable_area = hDC.GetDeviceCaps(8), hDC.GetDeviceCaps(10)
        printer_size = hDC.GetDeviceCaps(110), hDC.GetDeviceCaps(111)
        hDC.StartDoc(image_path)
        hDC.StartPage()
        dib = ImageWin.Dib(img)
        # Center the image on the page
        x = int((printer_size[0] - img.size[0]) / 2)
        y = int((printer_size[1] - img.size[1]) / 2)
        dib.draw(hDC.GetHandleOutput(), (x, y, x + img.size[0], y + img.size[1]))
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        print(f"Image sent to printer: {printer_name}")
    except Exception as e:
        print(f"Error printing image: {e}")

# --- Uncomment to list printers ---
if sys.platform.startswith('win'):
    list_windows_printers()

# --- Uncomment and set your printer name to print directly ---
if sys.platform.startswith('win'):
    print_image_to_printer(output_path, printer_name="Xprinter XP-D365B")

# Clean up barcode image
ios_remove = getattr(os, "remove", None)
if callable(ios_remove):
    try:
        os.remove(barcode_img_path)
    except Exception:
        pass
