#!/usr/bin/env python3
"""Compute total purchase cost of current inventory (boxes + strips).

Usage (PowerShell):
    .\\venv\\Scripts\\python.exe scripts\\compute_current_purchase_cost.py [--csv out.csv]

This script sets up Django environment and prints the total cost, and
optionally writes a per-product CSV with cost breakdown.
"""
import os
import sys
import argparse
from decimal import Decimal
import pathlib

# Ensure project root is on sys.path so `Elesraa` package can be imported
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Elesraa.settings')
import django
django.setup()

from pharmacy.models import Medicine
from django.utils import timezone
import csv


def compute(write_csv_path=None):
    total_cost = Decimal('0')
    rows = []
    now = timezone.now()

    for m in Medicine.objects.filter(is_active=True).order_by('name'):
        try:
            box_qty = int(m.calculate_available_stock() or 0)
        except Exception:
            box_qty = int(m.stock or 0)

        # Compute strips not already counted as full boxes
        try:
            total_strips = int(m.strips_in_stock or 0)
        except Exception:
            strips_per_box = m.strips_per_box or 1
            total_strips = box_qty * strips_per_box if box_qty else 0
        strips_per_box = m.strips_per_box or 1
        strip_qty = total_strips - (box_qty * strips_per_box)
        if strip_qty < 0:
            strip_qty = 0

        box_purchase = Decimal(m.purchase_price or 0)
        strips_per_box = m.strips_per_box or 1
        strip_purchase = (box_purchase / Decimal(strips_per_box)) if strips_per_box else Decimal('0')

        cost_box = box_purchase * Decimal(box_qty)
        cost_strip = strip_purchase * Decimal(strip_qty)
        cost_total = cost_box + cost_strip

        total_cost += cost_total

        rows.append({
            'id': m.id,
            'name': m.name,
            'box_qty': box_qty,
            'strip_qty': strip_qty,
            'box_purchase': f"{box_purchase:.2f}",
            'strip_purchase': f"{strip_purchase:.2f}",
            'cost_box': f"{cost_box:.2f}",
            'cost_strip': f"{cost_strip:.2f}",
            'cost_total': f"{cost_total:.2f}",
        })

    if write_csv_path:
        headers = ['id','name','box_qty','strip_qty','box_purchase','strip_purchase','cost_box','cost_strip','cost_total']
        with open(write_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in rows:
                writer.writerow([r[h] for h in headers])

    return total_cost, rows


def main():
    p = argparse.ArgumentParser(description='Compute total purchase cost of current inventory')
    p.add_argument('--csv', dest='csv', help='Optional output CSV path')
    args = p.parse_args()

    total_cost, rows = compute(write_csv_path=args.csv)
    print(f'Total purchase cost of current inventory: {total_cost:.2f}')
    if args.csv:
        print(f'Wrote per-product breakdown to {args.csv}')


if __name__ == '__main__':
    main()
