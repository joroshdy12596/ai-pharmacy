from django.shortcuts import render
from django.db.models import Sum, F
from .models import SaleItem, Medicine

def most_sold_products(request):
    # Aggregate total sold for each medicine (by unit type)
    most_sold = (
        SaleItem.objects
        .values('medicine__name', 'unit_type')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:50]
    )
    # Prepare for template
    most_sold_products = [
        {
            'name': item['medicine__name'],
            'total_sold': item['total_sold'],
            'unit_type': item['unit_type'],
        }
        for item in most_sold
    ]
    return render(request, 'pharmacy/most_sold_products.html', {
        'most_sold_products': most_sold_products
    })
