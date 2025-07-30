from django.db.models import Sum
from pharmacy.models import Sale, SaleItem

def get_total_profit():
    # Sum all profits from all sale items (using Python, not ORM)
    total_profit = sum(item.profit for item in SaleItem.objects.select_related('medicine', 'sale').all())
    return total_profit

def get_total_revenue():
    # Sum all completed sales
    total_revenue = Sale.objects.filter(is_completed=True).aggregate(total=Sum('total_amount'))['total']
    return total_revenue

# Example usage:
# print("Total Revenue:", get_total_revenue())
# print("Net Profit (صافي الربح):", get_total_profit())
