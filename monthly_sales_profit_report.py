import os
import django
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Elesraa.settings')
django.setup()

from pharmacy.models import Sale, SaleItem

grouped = defaultdict(lambda: {'sales': 0, 'total': Decimal('0.00'), 'profit': Decimal('0.00')})

sales = Sale.objects.filter(is_completed=True)
for sale in sales:
    month = sale.created_at.strftime('%Y-%m')
    grouped[month]['sales'] += 1
    grouped[month]['total'] += sale.total_amount
    # استخدم الخاصية profit من SaleItem
    profit = sum(item.profit for item in sale.items.all())
    grouped[month]['profit'] += profit

print('الشهر | عدد المبيعات | إجمالي المبيعات | صافي الربح')
for month in sorted(grouped.keys()):
    print(f"{month} | {grouped[month]['sales']} | {grouped[month]['total']:.2f} | {grouped[month]['profit']:.2f}")