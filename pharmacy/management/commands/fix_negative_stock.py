from django.core.management.base import BaseCommand
from django.db.models import Q
from pharmacy.models import StockEntry

class Command(BaseCommand):
    help = 'Clamp negative quantity/strips_remaining to zero for StockEntry rows'

    def handle(self, *args, **options):
        qs = StockEntry.objects.filter(Q(quantity__lt=0) | Q(strips_remaining__lt=0))
        total = qs.count()
        if total == 0:
            self.stdout.write('No negative stock entries found.')
            return
        self.stdout.write(f'Found {total} entries with negative values; fixing...')
        fixed = []
        for e in qs.select_related('medicine'):
            old_q = e.quantity
            old_s = e.strips_remaining
            changed = False
            if e.quantity is None:
                e.quantity = 0
                changed = True
            if e.quantity < 0:
                e.quantity = 0
                changed = True
            if e.strips_remaining is None:
                # leave None
                pass
            else:
                if e.strips_remaining < 0:
                    e.strips_remaining = 0
                    changed = True
            if changed:
                e.save()
                fixed.append((e.id, e.medicine.name, old_q, old_s, e.quantity, e.strips_remaining))
                self.stdout.write(f'Fixed id={e.id} med={e.medicine.name} from q={old_q},s={old_s} to q={e.quantity},s={e.strips_remaining}')
        self.stdout.write(self.style.SUCCESS(f'Done. Fixed {len(fixed)} entries.'))
