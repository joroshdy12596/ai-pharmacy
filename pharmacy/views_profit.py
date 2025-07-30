from django.shortcuts import render
from .utils_profit import get_total_profit, get_total_revenue
from pharmacy.models import Sale, SaleItem
from django.utils.dateparse import parse_date

def profit_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sale_items = SaleItem.objects.select_related('medicine', 'sale')
    sales = Sale.objects.filter(is_completed=True)
    if start_date:
        sale_items = sale_items.filter(sale__created_at__date__gte=start_date)
        sales = sales.filter(created_at__date__gte=start_date)
    if end_date:
        sale_items = sale_items.filter(sale__created_at__date__lte=end_date)
        sales = sales.filter(created_at__date__lte=end_date)
    from django.db.models import Sum
    total_profit = sum(item.profit for item in sale_items)
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    return render(request, 'pharmacy/profit_report.html', {
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'start_date': start_date,
        'end_date': end_date,
    })
