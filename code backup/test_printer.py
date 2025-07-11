import win32print
import tempfile
from PIL import Image, ImageDraw, ImageFont
import os

def create_arabic_text_bitmap(text, width, height, font_size=24):
    # Create a new image with white background
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    
    # Try to load Arial font which usually supports Arabic
    try:
        # For Windows
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            # Alternative font paths
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", font_size)
        except:
            # Fallback to default
            font = ImageFont.load_default()
    
    # Get text size
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate position to center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw the text
    draw.text((x, y), text, font=font, fill=0)
    
    return image

def test_label_print():
    printer_name = "Xprinter XP-D365B"
      # TSPL commands for the label
    # For 40mm width, center point is at 20mm
    # For text, we position it at 20mm - estimated half of text width
    # For barcode, we use a width of 30mm and start at (40mm-30mm)/2 = 5mm from the edge    # Create Arabic text bitmap
    arabic_text = "صيدلية الإسراء"
    text_width = 203  # ~25.4mm at 203 DPI
    text_height = 40  # ~5mm at 203 DPI
    arabic_image = create_arabic_text_bitmap(arabic_text, text_width, text_height)
    
    # Convert image to bitmap data
    bitmap_data = bytearray()
    pixels = arabic_image.load()
    for y in range(text_height):
        byte = 0
        count = 0
        for x in range(text_width):
            byte = (byte << 1) | (0 if pixels[x, y] == 0 else 1)
            count += 1
            if count == 8:
                bitmap_data.append(byte)
                byte = 0
                count = 0
        if count > 0:
            byte = byte << (8 - count)
            bitmap_data.append(byte)
    
    label_commands = f"""
SIZE 40 mm,25 mm
GAP 2 mm,0
DENSITY 8
DIRECTION 0
REFERENCE 0,0
CLS
BARCODE 5,10,"128",30,1,0,2,2,"123456789"
TEXT 20,14,"2",0,2,2,"123456789"
BITMAP 5,18,{(text_width + 7) // 8},{text_height},1
PRINT 1
""".encode('ascii')    try:
        # Open printer
        printer_handle = win32print.OpenPrinter(printer_name)
        try:
            # Create a temporary file
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='.prn')
            temp_path = temp.name
            
            # Write commands and bitmap data
            temp.write(label_commands.encode('ascii'))
            temp.write(bitmap_data)
            temp.write(b"\nPRINT 1\n")
            temp.close()

            # Start print job
            job = win32print.StartDocPrinter(printer_handle, 1, ("Test Label", temp_path, "RAW"))
            try:                win32print.StartPagePrinter(printer_handle)
                # Read and write the temporary file content
                with open(temp_path, 'rb') as f:
                    win32print.WritePrinter(printer_handle, f.read())
                win32print.EndPagePrinter(printer_handle)
                print("✅ Print job sent successfully")
            finally:
                win32print.EndDocPrinter(printer_handle)
        finally:
            win32print.ClosePrinter(printer_handle)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_label_print()
