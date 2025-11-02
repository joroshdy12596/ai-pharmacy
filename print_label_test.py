from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import os
import math
import argparse

# This is a safe side script that creates an improved barcode label image
# and saves it locally for inspection. It will NOT send to the printer by default.

parser = argparse.ArgumentParser(description='Generate improved barcode label for testing')
parser.add_argument('--printer-path', default=None, help='If set, send TSPL to this device path (use with care)')
parser.add_argument('--out', default='improved_label.png', help='Output PNG filename')
parser.add_argument('--dpi', type=int, default=203, help='Target printer DPI (default 203)')
args = parser.parse_args()

# إعدادات الملصق (مم)
label_width_mm = 40
label_height_mm = 25
dpi = args.dpi

mm_to_inch = 25.4
width_px = int(label_width_mm / mm_to_inch * dpi)
height_px = int(label_height_mm / mm_to_inch * dpi)

# بيانات اختبارية - استبدل بقيمك عند التجربة
lines = [
    "صيدلية الإسراء",
    "بانادول إكسترا",
    "السعر: 15 جنيه"
]
barcode_value = "6223005678123"

# حاول تحميل خط شائع على النظام وإلا استخدم الخط الافتراضي
font_path_candidates = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
]
font = None
for p in font_path_candidates:
    if os.path.exists(p):
        try:
            font = ImageFont.truetype(p, 28)
            break
        except Exception:
            font = None
if font is None:
    font = ImageFont.load_default()

# Compatibility helper for measuring text size across Pillow versions
def measure_text(text, font, draw):
    try:
        # Older/newer Pillow may have draw.textsize
        return draw.textsize(text, font=font)
    except Exception:
        try:
            # Font object often has getsize
            return font.getsize(text)
        except Exception:
            # Fallback to textbbox which gives (x0,y0,x1,y1)
            bbox = draw.textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])

# إعداد صورة الملصق
image = Image.new("1", (width_px, height_px), 1)
draw = ImageDraw.Draw(image)

# احسب موضع النص (اترك مساحة للباركود في الأسفل)
line_spacing = 5
line_heights = [measure_text(line, font, draw)[1] for line in lines]
total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)

barcode_area_height = int(height_px * 0.40)  # اترك 40% من الارتفاع للباركود
current_y = (height_px - total_text_height - barcode_area_height) // 2

for line in lines:
    text_width, text_height = measure_text(line, font, draw)
    x = (width_px - text_width) // 2
    # Draw RTL text. Pillow can use libraqm for proper RTL shaping when available
    # If libraqm is not available, fall back to arabic_reshaper+python-bidi if installed,
    # otherwise draw the raw text (may not shape properly).
    try:
        draw.text((x, current_y), line, font=font, fill=0, direction="rtl")
    except Exception:
        try:
            # Try to reshape and bidi-reorder if libraries exist
            import arabic_reshaper
            from bidi.algorithm import get_display

            reshaped = arabic_reshaper.reshape(line)
            bidi_text = get_display(reshaped)
            draw.text((x, current_y), bidi_text, font=font, fill=0)
        except Exception:
            # Final fallback: draw the raw line
            draw.text((x, current_y), line, font=font, fill=0)
    current_y += text_height + line_spacing

# خيارات محسنة للباركود
# - quiet_zone أكبر
# - module_height أطول
# - حفظ بدقة DPI للطابعة
writer_opts = {
    'module_height': 18.0,  # يجعل البارات أطول
    'font_size': 10,
    'text_distance': 4,
    'quiet_zone': 6,
    'dpi': dpi
}

# أنشئ الباركود (image writer)
code128 = barcode.get('code128', barcode_value, writer=ImageWriter())
barcode_tmp = 'improved_barcode'
saved = code128.save(barcode_tmp, options=writer_opts)
# python-barcode عادة يحفظ كـ saved + .png
barcode_path = saved if saved.endswith('.png') else saved + '.png'

if not os.path.exists(barcode_path):
    raise FileNotFoundError(f"Barcode file not found: {barcode_path}")

# افتح الباركود، ضبّط الحدة، وحجمه دون تمويه
barcode_img = Image.open(barcode_path).convert('L')
# نريد أن يكون عرض الباركود أقل من عرض الملصق مع هامش
margin_px = max(6, int(dpi * 2 / 25.4))  # على الأقل 2mm هامش
target_barcode_width = width_px - margin_px * 2
# اضبط ارتفاع الباركود ليملأ مساحة الباركود المخصصة
target_barcode_height = int(barcode_area_height * 0.85)

# استعمل NEAREST للحفاظ على حواف حادة
barcode_resized = barcode_img.resize((target_barcode_width, target_barcode_height), resample=Image.NEAREST)
barcode_resized = barcode_resized.point(lambda x: 0 if x < 128 else 255, '1')

# الصق الباركود في أسفل الملصق
barcode_y = height_px - target_barcode_height - margin_px
barcode_x = (width_px - target_barcode_width) // 2
image.paste(barcode_resized, (barcode_x, barcode_y))

# حفظ الناتج بصيغة PNG و BMP للمعاينة
out_png = args.out
out_bmp = os.path.splitext(out_png)[0] + '.bmp'
# حفظ PNG بصيغة ثنائية 1-bit قد يخسر DPI metadata, لكن نحتفظ بالـ PNG للعرض
image.convert('L').save(out_png, dpi=(dpi, dpi))
image.save(out_bmp)

print(f"Saved improved label: {out_png} and {out_bmp}")

# أيضاً نحضّر محتوى BITMAP لملف TSPL لكن لا نرسله للطابعة إلا إذا طلبت ذلك
bytes_per_row = math.ceil(width_px / 8)
bitmap_data = bytearray()
pixels = image.load()
for y in range(height_px):
    byte = 0
    count = 0
    for x in range(width_px):
        byte = (byte << 1) | (0 if pixels[x, y] == 0 else 1)
        count += 1
        if count == 8:
            bitmap_data.append(byte)
            byte = 0
            count = 0
    if count > 0:
        byte = byte << (8 - count)
        bitmap_data.append(byte)

header = f"""SIZE {label_width_mm} mm,{label_height_mm} mm
GAP 2 mm,0
DENSITY 8
CLS
BITMAP 0,0,{bytes_per_row},{height_px},1,
"""

# احفظ ملف TSPL جاهز (لكن لا ترسله تلقائياً)
tspl_out = os.path.splitext(out_png)[0] + '.tspl'
with open(tspl_out, 'wb') as f:
    f.write(header.encode('ascii'))
    f.write(bitmap_data)
    f.write(b"\nPRINT 1\n")

print(f"Saved TSPL bitmap for inspection: {tspl_out}")

# إرسال للطابعة إن حدّدت --printer-path (استخدم بحذر)
if args.printer_path:
    try:
        with open(args.printer_path, 'wb') as printer:
            printer.write(header.encode('ascii'))
            printer.write(bitmap_data)
            printer.write(b"\nPRINT 1\n")
        print(f"Sent label to printer at: {args.printer_path}")
    except Exception as e:
        print(f"Failed to send to printer: {e}")

# نظف ملفات الباركود المؤقتة
try:
    if os.path.exists(barcode_path):
        os.remove(barcode_path)
except Exception:
    pass
