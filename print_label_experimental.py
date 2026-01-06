r"""
Experimental barcode label generator for testing printer readability.
Outputs: PNG (anti-aliased off via nearest scaling), BMP, and a TSPL .prn file that follows the same BITMAP + raw bytes pattern used in `test_printer.py`.

Usage examples (PowerShell):
    python .\print_label_experimental.py --barcode 6223005678123 --product "باركود تجريبي" --price "12.50" --prefix mylabel

Options:
    --width-mm, --height-mm: label physical size in mm (default 40x25)
    --dpi: printer DPI (default 203)
    --margin-mm: left/right margin in mm
    --quiet-zone-mm: extra quiet zone around barcode in mm
    --module-height-mm: barcode module height override (visual only)
    --send: optional flag to send the generated .prn file directly to a Windows printer (raw)
    --printer: printer name to send to when using --send (required with --send)

The script tries to use arabic_reshaper + python-bidi for nicer Arabic rendering if installed.
"""

import argparse
import os
import tempfile
import sys
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter

# Optional Windows raw printing support
try:
    import win32print
    _HAS_WIN32 = True
except Exception:
    _HAS_WIN32 = False
try:
    import win32ui
    from PIL import ImageWin
    _HAS_WIN32UI = True
except Exception:
    _HAS_WIN32UI = False

# Optional Arabic shaping
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _HAS_ARABIC = True
except Exception:
    _HAS_ARABIC = False


def mm_to_px(mm, dpi):
    return int(round(mm / 25.4 * dpi))


def choose_barcode_type(value):
    # Prefer EAN13 for 12/13 digit numeric codes, else Code128
    if value.isdigit() and len(value) in (12, 13):
        return 'ean13'
    return 'code128'


def pack_image_to_tspl_bytes(im):
    """Pack a monochrome PIL image (mode '1' or 'L') into raw bytes matching test_printer packing.
    Returns a bytes object of width_bytes * height length.
    The packing follows the pattern used in test_printer.py: for each row, left-to-right, accumulate bits and append bytes.
    """
    if im.mode != '1':
        mono = im.convert('1')
    else:
        mono = im
    pixels = mono.load()
    w, h = mono.size
    out = bytearray()
    for y in range(h):
        byte = 0
        count = 0
        for x in range(w):
            # In '1' mode, pixel is 0 or 255 (0 black). Mirror test_printer logic: append 0 for black, 1 for white.
            val = 0 if pixels[x, y] == 0 else 1
            byte = (byte << 1) | (0 if val == 0 else 1)
            count += 1
            if count == 8:
                out.append(byte)
                byte = 0
                count = 0
        if count > 0:
            byte = byte << (8 - count)
            out.append(byte)
    return bytes(out)


def shape_arabic(text):
    if _HAS_ARABIC:
        try:
            reshaped = arabic_reshaper.reshape(text)
            bidi = get_display(reshaped)
            return bidi
        except Exception:
            return text
    return text


def create_label(barcode_value, product_text, price_text, prefix, width_mm=40, height_mm=25, dpi=203, margin_mm=2, quiet_zone_mm=2, module_height_mm=8.0):
    width_px = mm_to_px(width_mm, dpi)
    height_px = mm_to_px(height_mm, dpi)
    margin_px = mm_to_px(margin_mm, dpi)
    quiet_px = mm_to_px(quiet_zone_mm, dpi)

    # Create barcode image via python-barcode into a temp file
    bc_type = choose_barcode_type(barcode_value)
    writer_opts = {
        'module_height': module_height_mm,  # best-effort: this is for the writer library
        'quiet_zone': 1,
        'write_text': False,
    }
    try:
        code = barcode.get(bc_type, barcode_value, writer=ImageWriter())
    except Exception as e:
        print(f"Error creating barcode object: {e}")
        return

    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmpf.close()
    try:
        saved = code.save(tmpf.name.replace('.png', ''), options=writer_opts)
        barcode_path = saved if saved.endswith('.png') else saved + '.png'
        if not os.path.exists(barcode_path):
            raise FileNotFoundError(barcode_path)
    except Exception as e:
        print(f"Failed to render barcode image: {e}")
        try:
            os.unlink(tmpf.name)
        except Exception:
            pass
        return

    # Load barcode and convert to grayscale
    barcode_img = Image.open(barcode_path).convert('L')

    # Target barcode area: give barcode about 40% of height by default
    barcode_area_height = int(height_px * 0.40)
    target_barcode_width = width_px - margin_px * 2
    target_barcode_height = max(20, int(barcode_area_height * 0.85))

    # Resize barcode using NEAREST to keep bars sharp
    barcode_resized = barcode_img.resize((target_barcode_width, target_barcode_height), resample=Image.NEAREST)

    # Create final canvas (white background)
    canvas = Image.new('L', (width_px, height_px), 255)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    try:
        font_main = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        try:
            font_main = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 18)
        except Exception:
            font_main = ImageFont.load_default()

    # Prepare product and price text (try Arabic shaping)
    product_draw_text = shape_arabic(product_text)
    price_draw_text = price_text

    # Measure text heights
    p_bbox = draw.textbbox((0, 0), product_draw_text, font=font_main)
    p_h = p_bbox[3] - p_bbox[1]
    price_bbox = draw.textbbox((0, 0), price_draw_text, font=font_main)
    price_h = price_bbox[3] - price_bbox[1]

    # Layout: top product, middle barcode, bottom price
    # Compute Y positions
    y_top = margin_px
    y_barcode = (height_px - target_barcode_height) // 2
    y_bottom = height_px - margin_px - price_h

    # Draw product text centered
    p_w = p_bbox[2] - p_bbox[0]
    draw.text(((width_px - p_w) // 2, y_top), product_draw_text, font=font_main, fill=0)

    # Paste barcode centered horizontally at y_barcode
    canvas.paste(barcode_resized, ((width_px - target_barcode_width) // 2, y_barcode))

    # Draw price text
    price_w = price_bbox[2] - price_bbox[0]
    draw.text(((width_px - price_w) // 2, y_bottom), price_draw_text, font=font_main, fill=0)

    # Save PNG and BMP
    png_path = f"{prefix}.png"
    bmp_path = f"{prefix}.bmp"
    canvas.save(png_path)
    # Save BMP in 1-bit or RGB? Use BMP mode '1' to produce monochrome BMP
    canvas.convert('1').save(bmp_path)

    print(f"Saved: {png_path}, {bmp_path}")

    # Create TSPL .prn file
    prn_path = f"{prefix}.prn"
    # Pack the whole canvas to TSPL bytes
    mono = canvas.convert('1')
    width_bytes = (mono.width + 7) // 8
    tspl_bitmap = pack_image_to_tspl_bytes(mono)

    # Use similar header as test_printer.py
    header = []
    header.append(f"SIZE {int(width_mm)} mm,{int(height_mm)} mm")
    header.append("GAP 2 mm,0")
    header.append("DENSITY 8")
    header.append("DIRECTION 0")
    header.append("REFERENCE 0,0")
    header.append("CLS")
    # Place barcode as BITMAP at small offset (0,0)
    header.append(f"BITMAP 0,0,{width_bytes},{mono.height},1")

    try:
        with open(prn_path, 'wb') as f:
            f.write('\n'.join(header).encode('ascii'))
            f.write(b"\n")
            f.write(tspl_bitmap)
            f.write(b"\nPRINT 1\n")
        print(f"Saved TSPL: {prn_path}")
    except Exception as e:
        print(f"Failed to write PRN file: {e}")

    # Cleanup temporary barcode file
    try:
        os.unlink(barcode_path)
    except Exception:
        pass

    return png_path, bmp_path, prn_path


def send_to_printer(printer_name, filepath):
    """Send a binary file to the named Windows printer using raw mode.
    Returns True on success, False otherwise.
    """
    if not _HAS_WIN32:
        print("win32print module not available: cannot send to printer on Windows from this script.")
        return False
    # Prefer GDI drawing path if available (matches working view code). Otherwise fallback to RAW write.
    if _HAS_WIN32UI:
        try:
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            printer_size = hDC.GetDeviceCaps(110), hDC.GetDeviceCaps(111)
            # Open image (use BMP/PNG from filepath if possible)
            try:
                im = Image.open(filepath)
            except Exception:
                # If raw prn was passed, try replacing extension with .bmp
                alt = os.path.splitext(filepath)[0] + '.bmp'
                im = Image.open(alt)
            dib = ImageWin.Dib(im)
            hDC.StartDoc(os.path.basename(filepath))
            hDC.StartPage()
            x = int((printer_size[0] - im.size[0]) / 2)
            y = int((printer_size[1] - im.size[1]) / 2)
            dib.draw(hDC.GetHandleOutput(), (x, y, x + im.size[0], y + im.size[1]))
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            return True
        except Exception as e:
            print(f"GDI print path failed: {e}")
            # Fall back to raw path below

    # Fallback: raw write to printer (may work for some printers that accept TSPL raw)
    try:
        ph = win32print.OpenPrinter(printer_name)
    except Exception as e:
        print(f"Failed to open printer '{printer_name}': {e}")
        return False
    try:
        # Read file bytes and send as RAW
        with open(filepath, 'rb') as f:
            data = f.read()
        hJob = win32print.StartDocPrinter(ph, 1, (os.path.basename(filepath), None, "RAW"))
        try:
            win32print.StartPagePrinter(ph)
            win32print.WritePrinter(ph, data)
            win32print.EndPagePrinter(ph)
        finally:
            win32print.EndDocPrinter(ph)
    except Exception as e:
        print(f"Error sending file to printer: {e}")
        try:
            win32print.ClosePrinter(ph)
        except Exception:
            pass
        return False
    try:
        win32print.ClosePrinter(ph)
    except Exception:
        pass
    return True


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Generate improved barcode label (PNG/BMP/TSPL)')
    p.add_argument('--barcode', required=True, help='Barcode value')
    p.add_argument('--product', default='Product', help='Product name to print')
    p.add_argument('--price', default='', help='Price text to print')
    p.add_argument('--prefix', default='improved_label', help='Output file prefix')
    p.add_argument('--width-mm', type=float, default=40.0)
    p.add_argument('--height-mm', type=float, default=25.0)
    p.add_argument('--dpi', type=int, default=203)
    p.add_argument('--margin-mm', type=float, default=2.0)
    p.add_argument('--quiet-zone-mm', type=float, default=2.0)
    p.add_argument('--module-height-mm', type=float, default=8.0)
    p.add_argument('--send', action='store_true', help='Send generated .prn to a Windows printer')
    p.add_argument('--printer', type=str, default=None, help='Printer name to use with --send')
    p.add_argument('--ab', action='store_true', help='Create two variants (A/B) with different barcode settings for comparison')
    args = p.parse_args()

    if args.ab:
        # Variant A: larger module height and quiet zone (more aggressive)
        prefix_a = f"{args.prefix}_A"
        print(f"Generating A variant -> {prefix_a}")
        png_a, bmp_a, prn_a = create_label(
            args.barcode,
            args.product,
            args.price,
            prefix_a,
            width_mm=args.width_mm,
            height_mm=args.height_mm,
            dpi=args.dpi,
            margin_mm=args.margin_mm,
            quiet_zone_mm=max(args.quiet_zone_mm, 6.0),
            module_height_mm=max(args.module_height_mm, 24.0),
        )

        # Variant B: moderate settings (closer to existing web settings)
        prefix_b = f"{args.prefix}_B"
        print(f"Generating B variant -> {prefix_b}")
        png_b, bmp_b, prn_b = create_label(
            args.barcode,
            args.product,
            args.price,
            prefix_b,
            width_mm=args.width_mm,
            height_mm=args.height_mm,
            dpi=args.dpi,
            margin_mm=args.margin_mm,
            quiet_zone_mm=max(args.quiet_zone_mm, 3.0),
            module_height_mm=max(args.module_height_mm, 14.0),
        )

        # Optionally send both
        if args.send:
            if not args.printer:
                print("--send requires --printer PRINTER_NAME. Use --help for details.")
            else:
                for pth in (prn_a, prn_b):
                    print(f"Sending {pth} to printer '{args.printer}'...")
                    ok = send_to_printer(args.printer, pth)
                    print("✅ Sent" if ok else "❌ Failed to send")

    print("A/B generation complete. Files:")
    print(png_a, bmp_a, prn_a)
    print(png_b, bmp_b, prn_b)
    sys.exit(0)

    png_path, bmp_path, prn_path = create_label(
        args.barcode,
        args.product,
        args.price,
        args.prefix,
        width_mm=args.width_mm,
        height_mm=args.height_mm,
        dpi=args.dpi,
        margin_mm=args.margin_mm,
        quiet_zone_mm=args.quiet_zone_mm,
        module_height_mm=args.module_height_mm,
    )

    if args.send:
        if not args.printer:
            print("--send requires --printer PRINTER_NAME. Use --help for details.")
        else:
            print(f"Sending {prn_path} to printer '{args.printer}'...")
            ok = send_to_printer(args.printer, prn_path)
            if ok:
                print("✅ Sent to printer successfully")
            else:
                print("❌ Failed to send to printer")
