from django.core.management.base import BaseCommand
from pharmacy.models import StockEntry
from django.db.models import Q

class Command(BaseCommand):
    help = 'Inspect a StockEntry by id and optionally delete if empty'

    def add_arguments(self, parser):
        parser.add_argument('entry_id', type=int, help='ID of the StockEntry to inspect')
        parser.add_argument('--delete', action='store_true', help='Delete the StockEntry if it has no boxes and no strips')

    def handle(self, *args, **options):
        entry_id = options['entry_id']
        delete = options['delete']
        try:
            entry = StockEntry.objects.select_related('medicine').get(id=entry_id)
        except StockEntry.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'StockEntry with id={entry_id} not found'))
            return

        med = entry.medicine
        strips_per_box = med.strips_per_box or 0
        available_strips = entry.strips_remaining if entry.strips_remaining is not None else entry.quantity * strips_per_box

        self.stdout.write(f"StockEntry id={entry.id}")
        self.stdout.write(f"  medicine: {med.name} (id={med.id})")
        self.stdout.write(f"  expiration_date: {entry.expiration_date}")
        self.stdout.write(f"  quantity (boxes): {entry.quantity}")
        self.stdout.write(f"  strips_remaining: {entry.strips_remaining}")
        self.stdout.write(f"  strips_per_box (medicine): {strips_per_box}")
        self.stdout.write(f"  computed available_strips: {available_strips}")

        if delete:
            if (entry.quantity or 0) == 0 and (available_strips or 0) == 0:
                entry.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted StockEntry id={entry_id}'))
            else:
                self.stdout.write(self.style.ERROR('Entry is not empty. Aborting delete.'))
        else:
            self.stdout.write('Dry run: no changes made. Use --delete to remove if safe.')
