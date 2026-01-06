from django.core.management.base import BaseCommand
import csv
from decimal import Decimal
from django.utils import timezone

from pharmacy.models import Medicine


class Command(BaseCommand):
    help = 'Export currently-available inventory (non-expired) to CSV'

    def add_arguments(self, parser):
        parser.add_argument('--out', dest='out', default='current_inventory.csv', help='Output CSV path')

    def handle(self, *args, **options):
        out_path = options.get('out') or 'current_inventory.csv'
        today = timezone.now().date()

        headers = [
            'id', 'name',
            'box_qty_available', 'box_price', 'box_purchase_price', 'total_selling_value_box', 'total_cost_value_box',
            'strip_qty_available', 'strip_price', 'strip_purchase_price', 'total_selling_value_strip', 'total_cost_value_strip',
        ]

        rows = []
        for m in Medicine.objects.filter(is_active=True).order_by('name'):
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

            total_selling_value_box = box_price * Decimal(box_qty)
            total_cost_value_box = box_purchase * Decimal(box_qty)

            total_selling_value_strip = strip_price * Decimal(strip_qty)
            total_cost_value_strip = strip_purchase * Decimal(strip_qty)

            if box_qty > 0 or strip_qty > 0:
                rows.append([
                    m.id, m.name,
                    box_qty, f"{box_price:.2f}", f"{box_purchase:.2f}", f"{total_selling_value_box:.2f}", f"{total_cost_value_box:.2f}",
                    strip_qty, f"{strip_price:.2f}", f"{strip_purchase:.2f}", f"{total_selling_value_strip:.2f}", f"{total_cost_value_strip:.2f}",
                ])

        with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(f'Wrote {len(rows)} rows to {out_path}'))
