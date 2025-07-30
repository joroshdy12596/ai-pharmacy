from django.core.management.base import BaseCommand
from pharmacy.models import Medicine
import csv

class Command(BaseCommand):
    help = 'Export all medicines with their purchase (cost) prices to a CSV file.'

    def handle(self, *args, **options):
        filename = 'medicine_purchase_prices.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Name', 'Barcode', 'Purchase Price'])
            for med in Medicine.objects.all():
                writer.writerow([
                    med.id,
                    med.name,
                    med.barcode_number,
                    float(med.purchase_price)
                ])
        self.stdout.write(self.style.SUCCESS(f'Exported purchase prices to {filename}'))
