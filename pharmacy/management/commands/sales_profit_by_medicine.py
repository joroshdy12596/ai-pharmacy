from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from collections import defaultdict

from pharmacy.models import SaleItem, PurchaseItem


class Command(BaseCommand):
    help = 'Aggregate sold amount and historical profit by medicine (top positives and negatives).'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_date', help='Start date YYYY-MM-DD')
        parser.add_argument('--to', dest='to_date', help='End date YYYY-MM-DD')
        parser.add_argument('--top', type=int, default=20, help='How many top items to show')

    def handle(self, *args, **options):
        from_date = options.get('from_date')
        to_date = options.get('to_date')
        top = options.get('top') or 20

        items_qs = SaleItem.objects.select_related('sale', 'medicine').filter(sale__is_completed=True)
        if from_date:
            fd = timezone.datetime.strptime(from_date, '%Y-%m-%d')
            items_qs = items_qs.filter(sale__created_at__date__gte=fd.date())
        if to_date:
            td = timezone.datetime.strptime(to_date, '%Y-%m-%d')
            items_qs = items_qs.filter(sale__created_at__date__lte=td.date())

        # We'll compute historical purchase price like the historical summary
        purchase_cache = {}
        agg = defaultdict(lambda: {'sold': Decimal('0'), 'profit': Decimal('0'), 'count': 0})

        for it in items_qs.iterator():
            sale_date = it.sale.created_at
            agg[it.medicine.name]['sold'] += Decimal(str(it.subtotal))
            agg[it.medicine.name]['count'] += 1

            key = (it.medicine_id, sale_date.date())
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
                unit_cost_hist = (hist_price / Decimal(spb))
            else:
                unit_cost_hist = hist_price

            unit_price = Decimal(str(it.price))
            profit_hist = (unit_price - unit_cost_hist) * Decimal(it.quantity)
            agg[it.medicine.name]['profit'] += profit_hist

        # Prepare lists
        entries = [(name, data['sold'], data['profit'], data['count']) for name, data in agg.items()]
        top_pos = sorted(entries, key=lambda e: e[2], reverse=True)[:top]
        top_neg = sorted(entries, key=lambda e: e[2])[:top]

        self.stdout.write('Top positive profit medicines:')
        for name, sold, profit, count in top_pos:
            self.stdout.write(f'{name:40.40} sold={sold:.2f} profit={profit:.2f} items={count}')

        self.stdout.write('\nTop negative profit medicines:')
        for name, sold, profit, count in top_neg:
            self.stdout.write(f'{name:40.40} sold={sold:.2f} profit={profit:.2f} items={count}')
