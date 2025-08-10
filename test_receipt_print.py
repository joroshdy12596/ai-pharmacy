from PIL import Image, ImageDraw, ImageFont
import datetime

# --- Receipt settings ---
RECEIPT_WIDTH_MM = 80
RECEIPT_HEIGHT_MM = 200
DPI = 203
MM_TO_INCH = 25.4
WIDTH_PX = int(RECEIPT_WIDTH_MM / MM_TO_INCH * DPI)
HEIGHT_PX = int(RECEIPT_HEIGHT_MM / MM_TO_INCH * DPI)

# --- Data (replace with your test values) ---
PHARMACY_NAME = "صيدلية الإسراء"
SALE_ITEMS = [
    {"name": "اماريل ام اقراص", "quantity": 2, "unit_type": "STRIP", "price": 50, "total": 100},
    {"name": "باراسيتامول", "quantity": 1, "unit_type": "BOX", "price": 30, "total": 30},
]
TOTAL_AMOUNT = 130
SALE_DATE = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# --- Font ---
FONT_PATHS = [
    "C:\\Windows\\Fonts\\arial.ttf",
    "C:\\Windows\\Fonts\\Tahoma.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_SIZE = 22
font = None
for path in FONT_PATHS:
    try:
        font = ImageFont.truetype(path, FONT_SIZE)
        break
    except Exception:
        continue
if font is None:
    font = ImageFont.load_default()

# --- Create receipt image ---
image = Image.new("L", (WIDTH_PX, HEIGHT_PX), 255)
draw = ImageDraw.Draw(image)

y = 10
draw.text((WIDTH_PX // 2, y), PHARMACY_NAME, font=font, fill=0, anchor="ma")
y += FONT_SIZE + 10
draw.text((10, y), f"التاريخ: {SALE_DATE}", font=font, fill=0)
y += FONT_SIZE + 10

draw.text((10, y), "المنتج   الكمية   النوع   السعر   الإجمالي", font=font, fill=0)
y += FONT_SIZE + 5

for item in SALE_ITEMS:
    line = f"{item['name']}   {item['quantity']}   {item['unit_type']}   {item['price']}   {item['total']}"
    draw.text((10, y), line, font=font, fill=0)
    y += FONT_SIZE + 5

y += 10
draw.text((10, y), f"الإجمالي: {TOTAL_AMOUNT} م.ج", font=font, fill=0)

# Save image for debugging
image.save("debug_receipt.png")
print("Receipt image saved as debug_receipt.png")

# --- Print receipt image to default Windows printer ---
try:
    import win32print
    import win32ui
    from PIL import ImageWin
    
    # Path to the saved image
    image_path = "debug_receipt.png"
    img = Image.open(image_path)
    
    # Get default printer
    printer_name = win32print.GetDefaultPrinter()
    print(f"Sending receipt to printer: {printer_name}")
    
    # Create device context for printer
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    
    # Get printable area
    printer_size = hDC.GetDeviceCaps(110), hDC.GetDeviceCaps(111)
    
    # Start print job
    hDC.StartDoc("Receipt")
    hDC.StartPage()
    
    # Convert image for printing
    dib = ImageWin.Dib(img)
    x = int((printer_size[0] - img.size[0]) / 2)
    y = int((printer_size[1] - img.size[1]) / 2)
    dib.draw(hDC.GetHandleOutput(), (x, y, x + img.size[0], y + img.size[1]))
    
    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()
    print("Receipt sent to printer.")
except Exception as e:
    print(f"Error printing receipt: {e}")