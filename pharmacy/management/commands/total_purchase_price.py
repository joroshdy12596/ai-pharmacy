from django.core.management.base import BaseCommand
from pharmacy.models import Medicine
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Show the total purchase (cost) price of all medicines in the pharmacy.'

    def handle(self, *args, **options):
        total = Medicine.objects.aggregate(total=Sum('purchase_price'))['total'] or 0
        self.stdout.write(self.style.SUCCESS(f'Total purchase price of all medicines: {total}'))
