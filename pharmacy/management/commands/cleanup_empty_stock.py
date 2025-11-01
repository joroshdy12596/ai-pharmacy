from django.core.management.base import BaseCommand
from pharmacy.models import StockEntry
from django.db.models import Q


class Command(BaseCommand):
    help = 'Delete StockEntry rows where no boxes and no strips are available'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show entries that would be deleted without deleting')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        # Start with candidates where boxes == 0 and strips_remaining is null or 0
        candidates = StockEntry.objects.filter(Q(quantity=0) & (Q(strips_remaining__isnull=True) | Q(strips_remaining=0)))

        to_delete = []
        for entry in candidates.select_related('medicine'):
            med = entry.medicine
            # Compute available strips: prefer strips_remaining if set, otherwise quantity * strips_per_box
            available_strips = entry.strips_remaining if entry.strips_remaining is not None else entry.quantity * (med.strips_per_box or 0)
            # If there are zero boxes and zero strips, mark for deletion
            if (entry.quantity or 0) == 0 and (available_strips or 0) == 0:
                to_delete.append(entry)

        count = len(to_delete)
        if count == 0:
            self.stdout.write('No empty stock entries found.')
            return

        self.stdout.write(f'Found {count} empty stock entries (after verifying strips availability).')
        if dry_run:
            for entry in to_delete:
                self.stdout.write(f"Would delete: id={entry.id} medicine={entry.medicine.name} exp={entry.expiration_date}")
            return

        deleted_info = []
        for entry in to_delete:
            deleted_info.append((entry.id, entry.medicine.name, str(entry.expiration_date)))
            entry.delete()

        self.stdout.write(self.style.SUCCESS(f'Deleted {len(deleted_info)} empty stock entries.'))
        for info in deleted_info:
            self.stdout.write(f"Deleted: id={info[0]} medicine={info[1]} exp={info[2]}")
