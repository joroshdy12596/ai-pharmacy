import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Elesraa.settings')
django.setup()

from pharmacy.models import Medicine

medicines = Medicine.objects.all()
total_value = sum(Decimal(str(m.stock)) * m.price for m in medicines)

print(f"إجمالي قيمة البضاعة الحالية في المخزن: {total_value:.2f} ج.م")
