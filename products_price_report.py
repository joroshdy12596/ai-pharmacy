#!/usr/bin/env python
"""
تقرير شامل لأسعار الشراء والبيع لكل المنتجات
Comprehensive Report for Purchase and Selling Prices of All Products
"""

import os
import django
import csv
from datetime import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Elesraa.settings')
django.setup()

from pharmacy.models import Medicine

def print_formatted_table(headers, table_data):
    """Print a formatted ASCII table"""
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in table_data:
            max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width + 2)
    
    # Print header separator
    separator = "+" + "+".join(["-" * width for width in col_widths]) + "+"
    print(separator)
    
    # Print headers
    header_row = "|"
    for i, header in enumerate(headers):
        header_row += f" {header.center(col_widths[i] - 2)} |"
    print(header_row)
    print(separator)
    
    # Print data rows
    for row in table_data:
        data_row = "|"
        for i, cell in enumerate(row):
            data_row += f" {str(cell).center(col_widths[i] - 2)} |"
        print(data_row)
    
    # Print footer separator
    print(separator)

def generate_price_report():
    """Generate comprehensive price report for all medicines"""
    
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    
    if not medicines.exists():
        print("لا توجد منتجات متاحة / No products available")
        return
    
    # Data for table display
    table_data = []
    
    # Totals
    total_purchase_value = Decimal('0.00')
    total_selling_value = Decimal('0.00')
    total_profit = Decimal('0.00')
    
    for medicine in medicines:
        purchase_price = medicine.purchase_price or Decimal('0')
        selling_price = medicine.price or Decimal('0')
        stock = medicine.stock or 0
        
        purchase_value = purchase_price * stock
        selling_value = selling_price * stock
        profit = selling_value - purchase_value
        
        profit_margin = 0
        if purchase_price > 0:
            profit_margin = ((selling_price - purchase_price) / purchase_price) * 100
        
        total_purchase_value += purchase_value
        total_selling_value += selling_value
        total_profit += profit
        
        table_data.append([
            medicine.name[:25],  # Limit name length
            f"{purchase_price:.2f}",
            f"{selling_price:.2f}",
            stock,
            f"{purchase_value:.2f}",
            f"{selling_value:.2f}",
            f"{profit:.2f}",
            f"{profit_margin:.1f}%"
        ])
    
    # Print header
    print("\n" + "="*140)
    print("تقرير أسعار المنتجات الشامل - Comprehensive Products Price Report")
    print("="*140)
    print(f"تاريخ التقرير / Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Print table
    headers = [
        "المنتج / Product",
        "سعر الشراء / Purchase",
        "سعر البيع / Selling",
        "الكمية / Stock",
        "إجمالي الشراء",
        "إجمالي البيع",
        "الربح الإجمالي",
        "نسبة الربح %"
    ]
    
    print_formatted_table(headers, table_data)
    
    # Print totals
    print("\n" + "="*140)
    print("ملخص / Summary:")
    print("="*140)
    print(f"عدد المنتجات / Total Products: {medicines.count()}")
    print(f"إجمالي قيمة الشراء / Total Purchase Value: {total_purchase_value:.2f}")
    print(f"إجمالي قيمة البيع / Total Selling Value: {total_selling_value:.2f}")
    print(f"إجمالي الربح المحتمل / Total Potential Profit: {total_profit:.2f}")
    
    if total_purchase_value > 0:
        overall_margin = (total_profit / total_purchase_value) * 100
        print(f"نسبة الربح الإجمالية / Overall Profit Margin: {overall_margin:.1f}%")
    print("="*140 + "\n")
    
    # Generate CSV report
    generate_csv_report(medicines, total_purchase_value, total_selling_value, total_profit)

def generate_csv_report(medicines, total_purchase, total_selling, total_profit):
    """Generate CSV file with the report"""
    
    filename = f"products_price_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['تقرير أسعار المنتجات - Products Price Report'])
            writer.writerow([])
            writer.writerow([f'تاريخ التقرير - Report Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([])
            
            # Write column headers
            writer.writerow([
                'اسم المنتج',
                'Product Name',
                'سعر الشراء',
                'Purchase Price',
                'سعر البيع',
                'Selling Price',
                'الكمية',
                'Stock Qty',
                'إجمالي الشراء',
                'Total Purchase',
                'إجمالي البيع',
                'Total Selling',
                'الربح الإجمالي',
                'Total Profit',
                'نسبة الربح %',
                'Profit Margin %'
            ])
            
            # Write data rows
            for medicine in medicines:
                purchase_price = medicine.purchase_price or Decimal('0')
                selling_price = medicine.price or Decimal('0')
                stock = medicine.stock or 0
                
                purchase_value = purchase_price * stock
                selling_value = selling_price * stock
                profit = selling_value - purchase_value
                
                profit_margin = 0
                if purchase_price > 0:
                    profit_margin = ((selling_price - purchase_price) / purchase_price) * 100
                
                writer.writerow([
                    medicine.name,
                    medicine.name,
                    f"{purchase_price:.2f}",
                    f"{purchase_price:.2f}",
                    f"{selling_price:.2f}",
                    f"{selling_price:.2f}",
                    stock,
                    stock,
                    f"{purchase_value:.2f}",
                    f"{purchase_value:.2f}",
                    f"{selling_value:.2f}",
                    f"{selling_value:.2f}",
                    f"{profit:.2f}",
                    f"{profit:.2f}",
                    f"{profit_margin:.1f}",
                    f"{profit_margin:.1f}"
                ])
            
            # Write summary
            writer.writerow([])
            writer.writerow(['ملخص - Summary'])
            writer.writerow([f'إجمالي قيمة الشراء - Total Purchase Value', f"{total_purchase:.2f}"])
            writer.writerow([f'إجمالي قيمة البيع - Total Selling Value', f"{total_selling:.2f}"])
            writer.writerow([f'إجمالي الربح المحتمل - Total Potential Profit', f"{total_profit:.2f}"])
            
            if total_purchase > 0:
                overall_margin = (total_profit / total_purchase) * 100
                writer.writerow([f'نسبة الربح الإجمالية - Overall Profit Margin %', f"{overall_margin:.1f}"])
        
        print(f"✓ تم حفظ التقرير في / Report saved to: {filename}\n")
    except Exception as e:
        print(f"✗ خطأ في حفظ التقرير / Error saving report: {e}\n")

if __name__ == '__main__':
    generate_price_report()
