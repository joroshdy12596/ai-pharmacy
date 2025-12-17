from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import csv
from collections import defaultdict

from pharmacy.models import Medicine, SaleItem, PurchaseItem


class Command(BaseCommand):
    help = 'Detect medicines with suspicious selling prices. Flags zero price, price < purchase_price, very low margin, very high price, or negative avg historical profit.'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_date', help='Start date YYYY-MM-DD')
        parser.add_argument('--to', dest='to_date', help='End date YYYY-MM-DD')
        parser.add_argument('--min-margin', type=float, default=0.05, help='Minimum acceptable profit margin (fraction of purchase price). Default 0.05 (5%)')
        parser.add_argument('--max-mult', type=float, default=10.0, help='Maximum multiplier of price/purchase_price considered plausible. Default 10x')
        parser.add_argument('--csv', dest='csvfile', help='Write anomalies to CSV')

    def handle(self, *args, **options):
        from_date = options.get('from_date')
        to_date = options.get('to_date')
        min_margin = Decimal(str(options.get('min_margin') or 0.05))
        max_mult = Decimal(str(options.get('max_mult') or 10.0))
        csvfile = options.get('csvfile')

        # Prepare sales filter
        items_qs = SaleItem.objects.select_related('sale', 'medicine').filter(sale__is_completed=True)
        if from_date:
            fd = timezone.datetime.strptime(from_date, '%Y-%m-%d')
            items_qs = items_qs.filter(sale__created_at__date__gte=fd.date())
        if to_date:
            td = timezone.datetime.strptime(to_date, '%Y-%m-%d')
            items_qs = items_qs.filter(sale__created_at__date__lte=td.date())

        # Aggregate per medicine
        agg_qty = defaultdict(int)
        agg_revenue = defaultdict(Decimal)
        agg_profit_hist = defaultdict(Decimal)
        agg_unit_price_sum = defaultdict(Decimal)
        agg_unit_price_count = defaultdict(int)

        purchase_cache = {}

        for it in items_qs.iterator():
            mid = it.medicine_id
            qty = it.quantity or 0
            unit_price = Decimal(str(it.price or 0))
            agg_qty[mid] += qty
            agg_revenue[mid] += unit_price * Decimal(qty)
            agg_unit_price_sum[mid] += unit_price
            agg_unit_price_count[mid] += 1

            # historical purchase price lookup
            sale_date = it.sale.created_at
            key = (mid, sale_date.date())
            if key in purchase_cache:
                hist_price = purchase_cache[key]
            else:
                pi = PurchaseItem.objects.filter(medicine=it.medicine, purchase__date__date__lte=sale_date.date()).order_by('-purchase__date').first()
                if pi:
                    hist_price = Decimal(str(pi.price))
                else:
                    hist_price = Decimal(str(it.medicine.purchase_price or 0))
                purchase_cache[key] = hist_price

            if it.unit_type == 'STRIP':
                spb = it.medicine.strips_per_box or 1
                unit_cost = (hist_price / Decimal(spb))
            else:
                unit_cost = hist_price

            agg_profit_hist[mid] += (unit_price - unit_cost) * Decimal(qty)

        # Prepare output
        anomalies = []
        for m in Medicine.objects.all():
            mid = m.id
            current_price = Decimal(str(m.price or 0))
            purchase_price = Decimal(str(m.purchase_price or 0))
            qty_sold = agg_qty.get(mid, 0)
            revenue = agg_revenue.get(mid, Decimal('0'))
            avg_sold_price = (agg_unit_price_sum.get(mid, Decimal('0')) / Decimal(agg_unit_price_count[mid])) if agg_unit_price_count.get(mid) else None
            hist_profit = agg_profit_hist.get(mid, Decimal('0'))

            reasons = []
            if current_price <= 0:
                reasons.append('price_zero')
            if purchase_price > 0 and current_price < purchase_price:
                reasons.append('price_below_purchase')
            if purchase_price > 0 and current_price < (purchase_price * (Decimal('1.0') + min_margin)):
                reasons.append('low_margin')
            if purchase_price > 0 and current_price > (purchase_price * max_mult):
                reasons.append('price_too_high')
            if qty_sold > 0:
                # avg historical profit per unit
                avg_hist_profit_per_unit = (hist_profit / Decimal(qty_sold))
                if avg_hist_profit_per_unit < 0:
                    reasons.append('negative_avg_hist_profit')

            if reasons:
                anomalies.append({
                    'id': mid,
                    'name': m.name,
                    'current_price': f'{current_price:.2f}',
                    'purchase_price': f'{purchase_price:.2f}',
                    'qty_sold': qty_sold,
                    'revenue': f'{revenue:.2f}',
                    'avg_sold_price': f'{avg_sold_price:.2f}' if avg_sold_price is not None else '',
                    'avg_hist_profit_per_unit': f'{(hist_profit / Decimal(qty_sold)):.2f}' if qty_sold else '',
                    'reasons': ';'.join(reasons)
                })

        # sort anomalies by magnitude of negative avg_hist_profit_per_unit or by reasons
        anomalies_sorted = sorted(anomalies, key=lambda a: Decimal(a['avg_hist_profit_per_unit'] or '0'))

        # Output
        if csvfile:
            with open(csvfile, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id','name','current_price','purchase_price','qty_sold','revenue','avg_sold_price','avg_hist_profit_per_unit','reasons'])
                writer.writeheader()
                for a in anomalies_sorted:
                    writer.writerow(a)
            self.stdout.write(self.style.SUCCESS(f'Wrote anomalies to {csvfile}'))

        # print quick summary
        self.stdout.write('Anomalies detected:')
        for a in anomalies_sorted[:200]:
            self.stdout.write(f"{a['id']:5} {a['name'][:40]:40} price={a['current_price']:>8} purchase={a['purchase_price']:>8} sold={a['qty_sold']:5} avg_profit_unit={a['avg_hist_profit_per_unit']:>8} reasons={a['reasons']}")
