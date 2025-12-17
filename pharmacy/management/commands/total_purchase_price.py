from django.utils import timezone
from decimal import Decimal

from pharmacy.models import Medicine


class Command(BaseCommand):
    help = 'Calculate total inventory values: cost (purchase_price) and selling value (price). Considers non-expired stock entries and strips_remaining.'

    def handle(self, *args, **options):
        today = timezone.now().date()

        total_cost = Decimal('0')
        total_selling = Decimal('0')

        medicines = Medicine.objects.prefetch_related('stock_entries').all()
        for m in medicines:
            # Sum available boxes and strips from non-expired stock entries
            boxes = 0
            strips = 0
            for e in m.stock_entries.filter(expiration_date__gte=today):
                qty = e.quantity or 0
                boxes += qty
                if e.strips_remaining is None:
                    strips += qty * (m.strips_per_box or 0)
                else:
                    strips += e.strips_remaining or 0

            # Convert strips to fractional boxes
            spb = m.strips_per_box or 1
            boxes_equiv = Decimal(boxes) + (Decimal(str(strips)) / Decimal(spb))

            # Add to totals (use purchase_price for cost, price for selling value)
            purchase = m.purchase_price or 0
            sell = m.price or 0
            total_cost += boxes_equiv * Decimal(str(purchase))
            total_selling += boxes_equiv * Decimal(str(sell))

        self.stdout.write(self.style.SUCCESS(f'Total inventory cost (purchase_price): {total_cost:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Total inventory selling value (price): {total_selling:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Potential gross profit (selling - cost): {(total_selling - total_cost):.2f}'))
