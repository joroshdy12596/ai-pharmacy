from django.core.management.base import BaseCommand
from django.db import transaction
from pharmacy.models import StockEntry
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Merge duplicate StockEntry rows with same medicine and expiration_date'

    def handle(self, *args, **options):
        # Find duplicates grouped by medicine+expiration_date
        duplicates = (StockEntry.objects.values('medicine', 'expiration_date')
                      .annotate(count=Sum('quantity'))
                      .order_by())

        # We'll iterate unique pairs where more than one row exists
        merged_count = 0
        for pair in duplicates:
            meds = pair['medicine']
            exp = pair['expiration_date']
            rows = StockEntry.objects.filter(medicine_id=meds, expiration_date=exp).order_by('created_at')
            if rows.count() > 1:
                # Keep the earliest row, merge others into it
                keeper = rows.first()
                others = rows.exclude(id=keeper.id)
                total_qty = sum((r.quantity or 0) for r in rows)
                total_strips = sum((r.strips_remaining or (r.quantity or 0) * (keeper.medicine.strips_per_box or 0)) for r in rows)
                with transaction.atomic():
                    keeper.quantity = total_qty
                    keeper.strips_remaining = total_strips
                    keeper.save()
                    deleted = others.count()
                    others.delete()
                    merged_count += deleted
                    self.stdout.write(f'Merged {deleted} rows into StockEntry id={keeper.id} (med={keeper.medicine_id}, exp={exp})')

        self.stdout.write(self.style.SUCCESS(f'Finished dedupe. Merged {merged_count} rows.'))
