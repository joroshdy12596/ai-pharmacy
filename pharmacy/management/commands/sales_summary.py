from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import csv

from pharmacy.models import SaleItem, Sale


class Command(BaseCommand):
    help = 'Show total sold amount and total profit for completed sales (exclude current stock). Optional --from YYYY-MM-DD --to YYYY-MM-DD and --csv output file.'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_date', help='Start date (inclusive) YYYY-MM-DD')
        parser.add_argument('--to', dest='to_date', help='End date (inclusive) YYYY-MM-DD')
        parser.add_argument('--include-uncompleted', action='store_true', help='Include sales that are not marked completed')
        parser.add_argument('--csv', dest='csvfile', help='Write detailed per-item rows to CSV file')

    def handle(self, *args, **options):
        from_date = options.get('from_date')
        to_date = options.get('to_date')
        include_uncompleted = options.get('include_uncompleted')
        csvfile = options.get('csvfile')

        items_qs = SaleItem.objects.select_related('sale', 'medicine')

        # Filter by sale completion unless asked otherwise
        if not include_uncompleted:
            items_qs = items_qs.filter(sale__is_completed=True)

        # Filter by sale date if provided
        if from_date:
            try:
                fd = timezone.datetime.strptime(from_date, '%Y-%m-%d')
                items_qs = items_qs.filter(sale__created_at__date__gte=fd.date())
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Invalid --from date: {e}'))
                return
        if to_date:
            try:
                td = timezone.datetime.strptime(to_date, '%Y-%m-%d')
                items_qs = items_qs.filter(sale__created_at__date__lte=td.date())
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Invalid --to date: {e}'))
                return

        total_sold = Decimal('0')
        total_profit = Decimal('0')
        count = 0

        # Optionally write details to CSV
        csv_handle = None
        csv_writer = None
        if csvfile:
            csv_handle = open(csvfile, 'w', newline='', encoding='utf-8')
            csv_writer = csv.writer(csv_handle)
            csv_writer.writerow([
                'sale_id', 'sale_date', 'medicine', 'unit_type', 'quantity', 'unit_price',
                'subtotal', 'profit', 'purchase_price', 'unit_cost', 'unit_profit'
            ])

        for it in items_qs.iterator():
            # subtotal property may be Decimal or float; ensure Decimal
            try:
                subtotal = Decimal(str(it.subtotal))
            except Exception:
                subtotal = Decimal('0')
            try:
                profit = Decimal(str(it.profit))
            except Exception:
                profit = Decimal('0')

            total_sold += subtotal
            total_profit += profit
            count += 1

            # compute purchase price and unit cost
            try:
                purchase_price = Decimal(str(it.medicine.purchase_price or 0))
            except Exception:
                purchase_price = Decimal('0')

            if it.unit_type == 'STRIP':
                spb = it.medicine.strips_per_box or 1
                unit_cost = (purchase_price / Decimal(spb))
            else:
                unit_cost = purchase_price

            try:
                unit_price = Decimal(str(it.price))
            except Exception:
                unit_price = Decimal('0')

            unit_profit = (unit_price - unit_cost)
            total_profit_calc = unit_profit * Decimal(it.quantity)

            if csv_writer:
                csv_writer.writerow([
                    it.sale.id,
                    it.sale.created_at.strftime('%Y-%m-%d %H:%M'),
                    it.medicine.name,
                    it.unit_type,
                    it.quantity,
                    f'{unit_price:.2f}',
                    f'{subtotal:.2f}',
                    f'{profit:.2f}',
                    f'{purchase_price:.2f}',
                    f'{unit_cost:.2f}',
                    f'{unit_profit:.2f}'
                ])

        if csv_handle:
            csv_handle.close()

        self.stdout.write(self.style.SUCCESS(f'Total sold amount (sum of subtotals): {total_sold:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Total profit (sum of item profits): {total_profit:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Total items counted: {count}'))

        if csvfile:
            self.stdout.write(self.style.SUCCESS(f'Details written to CSV: {csvfile}'))
