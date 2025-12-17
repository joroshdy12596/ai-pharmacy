from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import csv

from pharmacy.models import SaleItem, PurchaseItem


class Command(BaseCommand):
    help = 'Compute sales totals and profit using historical purchase prices (closest purchase before sale date). Use --from/--to and --csv.'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_date', help='Start date (inclusive) YYYY-MM-DD')
        parser.add_argument('--to', dest='to_date', help='End date (inclusive) YYYY-MM-DD')
        parser.add_argument('--csv', dest='csvfile', help='Write detailed per-item rows to CSV file')

    def handle(self, *args, **options):
        from_date = options.get('from_date')
        to_date = options.get('to_date')
        csvfile = options.get('csvfile')

        items_qs = SaleItem.objects.select_related('sale', 'medicine').filter(sale__is_completed=True)

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

        csv_handle = None
        csv_writer = None
        if csvfile:
            csv_handle = open(csvfile, 'w', newline='', encoding='utf-8')
            csv_writer = csv.writer(csv_handle)
            csv_writer.writerow([
                'sale_id', 'sale_date', 'medicine', 'unit_type', 'quantity', 'unit_price',
                'subtotal', 'profit_old', 'hist_purchase_price', 'unit_cost_hist', 'unit_profit_hist', 'profit_hist'
            ])

        # simple cache for latest purchase price per medicine before a date to reduce DB hits
        purchase_cache = {}

        for it in items_qs.iterator():
            sale_date = it.sale.created_at
            total_sold += Decimal(str(it.subtotal))

            # find historical purchase price: latest PurchaseItem.price where purchase.date <= sale_date
            key = (it.medicine_id, sale_date.date())
            hist_price = None
            if key in purchase_cache:
                hist_price = purchase_cache[key]
            else:
                pi = PurchaseItem.objects.filter(medicine=it.medicine, purchase__date__date__lte=sale_date.date()).order_by('-purchase__date').first()
                if pi:
                    hist_price = Decimal(str(pi.price))
                else:
                    # fallback to medicine current purchase_price
                    hist_price = Decimal(str(it.medicine.purchase_price or 0))
                purchase_cache[key] = hist_price

            # compute unit cost based on unit_type
            if it.unit_type == 'STRIP':
                spb = it.medicine.strips_per_box or 1
                unit_cost_hist = (hist_price / Decimal(spb))
            else:
                unit_cost_hist = hist_price

            unit_price = Decimal(str(it.price))
            unit_profit_hist = unit_price - unit_cost_hist
            profit_hist = unit_profit_hist * Decimal(it.quantity)

            total_profit += profit_hist
            count += 1

            if csv_writer:
                csv_writer.writerow([
                    it.sale.id,
                    it.sale.created_at.strftime('%Y-%m-%d %H:%M'),
                    it.medicine.name,
                    it.unit_type,
                    it.quantity,
                    f'{unit_price:.2f}',
                    f'{Decimal(str(it.subtotal)):.2f}',
                    f'{Decimal(str(it.profit)):.2f}',
                    f'{hist_price:.2f}',
                    f'{unit_cost_hist:.2f}',
                    f'{unit_profit_hist:.2f}',
                    f'{profit_hist:.2f}'
                ])

        if csv_handle:
            csv_handle.close()

        self.stdout.write(self.style.SUCCESS(f'Total sold amount (sum of subtotals): {total_sold:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Total profit using historical purchase prices: {total_profit:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Total items counted: {count}'))
