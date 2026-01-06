from django.core.management.base import BaseCommand
import csv
from decimal import Decimal
from django.utils import timezone

from pharmacy.models import Medicine


class Command(BaseCommand):
    help = 'Calculate current inventory value (selling and cost) for items that are currently in stock'

    def add_arguments(self, parser):
        parser.add_argument('--out', dest='out', default=None, help='Optional output CSV path')
        parser.add_argument('--unit', dest='unit', choices=['box', 'strip', 'both'], default='both', help='Which unit to report: box, strip or both')

    def handle(self, *args, **options):
        out_path = options.get('out')
        unit = options.get('unit') or 'both'
        today = timezone.now().date()

        headers = []
        if unit in ('box', 'both'):
            headers += ['box_qty_available', 'box_price', 'box_purchase_price', 'total_selling_value_box', 'total_cost_value_box']
        if unit in ('strip', 'both'):
            headers += ['strip_qty_available', 'strip_price', 'strip_purchase_price', 'total_selling_value_strip', 'total_cost_value_strip']

        rows = []
        total_selling = Decimal('0')
        total_cost = Decimal('0')

        qs = Medicine.objects.filter(is_active=True).order_by('name')
        count_in_stock = 0
        for m in qs:
            try:
                box_qty = int(m.calculate_available_stock() or 0)
            except Exception:
                box_qty = int(m.stock or 0)

            # Compute strips not already counted as full boxes
            try:
                total_strips = int(m.strips_in_stock or 0)
            except Exception:
                total_strips = box_qty * (m.strips_per_box or 1) if box_qty else 0
            strips_per_box = m.strips_per_box or 1
            strip_qty = total_strips - (box_qty * strips_per_box)
            if strip_qty < 0:
                strip_qty = 0

            box_price = Decimal(m.price or 0)
            box_purchase = Decimal(m.purchase_price or 0)

            strips_per_box = m.strips_per_box or 1
            try:
                strip_price = Decimal(m.get_strip_price() or box_price)
            except Exception:
                strip_price = box_price
            strip_purchase = (box_purchase / Decimal(strips_per_box)) if strips_per_box else Decimal('0')

            total_selling_box = box_price * Decimal(box_qty)
            total_cost_box = box_purchase * Decimal(box_qty)

            total_selling_strip = strip_price * Decimal(strip_qty)
            total_cost_strip = strip_purchase * Decimal(strip_qty)

            if box_qty > 0 or strip_qty > 0:
                count_in_stock += 1
                row = [m.id, m.name]
                if unit in ('box', 'both'):
                    row += [box_qty, f"{box_price:.2f}", f"{box_purchase:.2f}", f"{total_selling_box:.2f}", f"{total_cost_box:.2f}"]
                if unit in ('strip', 'both'):
                    row += [strip_qty, f"{strip_price:.2f}", f"{strip_purchase:.2f}", f"{total_selling_strip:.2f}", f"{total_cost_strip:.2f}"]
                rows.append(row)

                # accumulate totals depending on unit selection
                if unit in ('box', 'both'):
                    total_selling += total_selling_box
                    total_cost += total_cost_box
                if unit in ('strip', 'both'):
                    total_selling += total_selling_strip
                    total_cost += total_cost_strip

        # print a concise report
        self.stdout.write(f"Products currently in stock: {count_in_stock}")
        self.stdout.write(f"Total potential selling value: {total_selling:.2f}")
        self.stdout.write(f"Total potential cost value:    {total_cost:.2f}")
        self.stdout.write(f"Potential gross margin (selling - cost): {(total_selling - total_cost):.2f}")

        if out_path:
            # build CSV header
            csv_headers = ['id', 'name'] + headers
            with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(csv_headers)
                writer.writerows(rows)
            self.stdout.write(self.style.SUCCESS(f'Wrote {len(rows)} rows to {out_path}'))
