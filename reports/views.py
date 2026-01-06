from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import csv
from pharmacy.models import SaleItem, PurchaseItem, Medicine


def reports_dashboard(request):
	"""
	Dashboard under /reports/ showing:
	- Total sold amount and profit (using historical purchase prices)
	- Current inventory selling value and cost (potential profit)

	Accepts optional GET params: from (YYYY-MM-DD) and to (YYYY-MM-DD)
	"""
	from_date = request.GET.get('from')
	to_date = request.GET.get('to')

	items_qs = SaleItem.objects.select_related('sale', 'medicine').filter(sale__is_completed=True)
	# apply date filters if provided
	if from_date:
		try:
			fd = timezone.datetime.strptime(from_date, '%Y-%m-%d')
			items_qs = items_qs.filter(sale__created_at__date__gte=fd.date())
		except Exception:
			from_date = None
	if to_date:
		try:
			td = timezone.datetime.strptime(to_date, '%Y-%m-%d')
			items_qs = items_qs.filter(sale__created_at__date__lte=td.date())
		except Exception:
			to_date = None

	total_sold = Decimal('0')
	total_profit = Decimal('0')

	purchase_cache = {}
	for it in items_qs.iterator():
		sale_date = it.sale.created_at
		total_sold += Decimal(str(it.subtotal))

		key = (it.medicine_id, sale_date.date())
		hist_price = None
		if key in purchase_cache:
			hist_price = purchase_cache[key]
		else:
			pi = PurchaseItem.objects.filter(medicine=it.medicine, purchase__date__date__lte=sale_date.date()).order_by('-purchase__date').first()
			if pi:
				hist_price = Decimal(str(pi.price))
			else:
				hist_price = Decimal(str(it.medicine.purchase_price or 0))
			purchase_cache[key] = hist_price

		if it.unit_type == 'STRIP':
			spb = it.medicine.strips_per_box or 1
			unit_cost_hist = (hist_price / Decimal(spb))
		else:
			unit_cost_hist = hist_price

		unit_price = Decimal(str(it.price))
		unit_profit_hist = unit_price - unit_cost_hist
		profit_hist = unit_profit_hist * Decimal(it.quantity)
		total_profit += profit_hist

	# Current inventory calculations
	total_inv_selling = Decimal('0')
	total_inv_cost = Decimal('0')
	inv_rows = []
	meds = Medicine.objects.filter(is_active=True).order_by('name')
	for m in meds:
		try:
			box_qty = int(m.calculate_available_stock() or 0)
		except Exception:
			box_qty = int(m.stock or 0)
		# Compute extra strips beyond full boxes to avoid double-counting
		try:
			total_strips = int(m.strips_in_stock or 0)
		except Exception:
			total_strips = box_qty * (m.strips_per_box or 1) if box_qty else 0
		strips_per_box = m.strips_per_box or 1
		strip_qty = total_strips - (box_qty * strips_per_box)
		if strip_qty < 0:
			strip_qty = 0

		box_price = Decimal(m.price or 0)
		box_purchase = Decimal(m.purchase_price or 0)
		strips_per_box = m.strips_per_box or 1
		try:
			strip_price = Decimal(m.get_strip_price() or box_price)
		except Exception:
			strip_price = box_price
		strip_purchase = (box_purchase / Decimal(strips_per_box)) if strips_per_box else Decimal('0')

		total_selling_box = box_price * Decimal(box_qty)
		total_cost_box = box_purchase * Decimal(box_qty)
		total_selling_strip = strip_price * Decimal(strip_qty)
		total_cost_strip = strip_purchase * Decimal(strip_qty)

		if box_qty > 0 or strip_qty > 0:
			total_inv_selling += total_selling_box + total_selling_strip
			total_inv_cost += total_cost_box + total_cost_strip
			inv_rows.append({
				'id': m.id,
				'name': m.name,
				'box_qty': box_qty,
				'strip_qty': strip_qty,
				'box_price': f"{box_price:.2f}",
				'box_purchase': f"{box_purchase:.2f}",
				'total_selling_box': f"{total_selling_box:.2f}",
				'total_cost_box': f"{total_cost_box:.2f}",
			})

	context = {
		'total_sold': f"{total_sold:.2f}",
		'total_profit_sold': f"{total_profit:.2f}",
		'total_inv_selling': f"{total_inv_selling:.2f}",
		'total_inv_cost': f"{total_inv_cost:.2f}",
		'total_inv_profit': f"{(total_inv_selling - total_inv_cost):.2f}",
		'inv_rows': inv_rows[:200],  # avoid huge pages; show top 200
		'from_date': from_date,
		'to_date': to_date,
	}

	return render(request, 'reports/dashboard.html', context)

@login_required
def inventory_cost(request):
    """Standalone page: Total purchase cost of current products"""
    meds = Medicine.objects.filter(is_active=True).order_by('name')
    total_purchase_cost = Decimal('0')
    rows = []

    for m in meds:
        try:
            box_qty = int(m.calculate_available_stock() or 0)
        except Exception:
            box_qty = int(m.stock or 0)
        # Compute strips not already counted as full boxes
        try:
            total_strips = int(m.strips_in_stock or 0)
        except Exception:
            total_strips = box_qty * (m.strips_per_box or 1) if box_qty else 0
        strips_per_box = m.strips_per_box or 1
        strip_qty = total_strips - (box_qty * strips_per_box)
        if strip_qty < 0:
            strip_qty = 0

        unit_purchase = Decimal(str(m.purchase_price or 0))
        strips_per_box = m.strips_per_box or 1
        strip_purchase = (unit_purchase / Decimal(strips_per_box)) if strips_per_box else Decimal('0')

        total_purchase = (unit_purchase * Decimal(box_qty)) + (strip_purchase * Decimal(strip_qty))
        total_purchase_cost += total_purchase

        rows.append({
            'id': m.id,
            'name': m.name,
            'box_qty': box_qty,
            'strip_qty': strip_qty,
            'unit_purchase': f"{unit_purchase:.2f}",
            'total_purchase': f"{total_purchase:.2f}",
        })

    context = {
        'rows': rows,
        'total_purchase_cost': f"{total_purchase_cost:.2f}",
    }
    return render(request, 'reports/inventory_cost.html', context)


@login_required
def inventory_cost_export(request):
    """CSV export for inventory purchase costs"""
    medicines = Medicine.objects.filter(is_active=True).order_by('name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="inventory_purchase_cost_{timezone.now().date().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Medicine', 'Box Qty', 'Strip Qty', 'Unit Purchase', 'Total Purchase'])

    for m in medicines:
        try:
            box_qty = int(m.calculate_available_stock() or 0)
        except Exception:
            box_qty = int(m.stock or 0)
        # Compute strips not already counted as full boxes
        try:
            total_strips = int(m.strips_in_stock or 0)
        except Exception:
            total_strips = box_qty * (m.strips_per_box or 1) if box_qty else 0
        strips_per_box = m.strips_per_box or 1
        strip_qty = total_strips - (box_qty * strips_per_box)
        if strip_qty < 0:
            strip_qty = 0

        unit_purchase = Decimal(str(m.purchase_price or 0))
        strips_per_box = m.strips_per_box or 1
        strip_purchase = (unit_purchase / Decimal(strips_per_box)) if strips_per_box else Decimal('0')

        total_purchase = (unit_purchase * Decimal(box_qty)) + (strip_purchase * Decimal(strip_qty))
        writer.writerow([m.name, box_qty, strip_qty, f"{unit_purchase:.2f}", f"{total_purchase:.2f}"])

    return response


@login_required
def inventory_summary(request):
    """Compact overview showing total selling value, total purchase cost, and expected profit."""
    meds = Medicine.objects.filter(is_active=True).order_by('name')
    total_selling = Decimal('0')
    total_purchase = Decimal('0')

    for m in meds:
        try:
            box_qty = int(m.calculate_available_stock() or 0)
        except Exception:
            box_qty = int(m.stock or 0)
        # Compute strips not already counted as full boxes
        try:
            total_strips = int(m.strips_in_stock or 0)
        except Exception:
            total_strips = box_qty * (m.strips_per_box or 1) if box_qty else 0
        strips_per_box = m.strips_per_box or 1
        strip_qty = total_strips - (box_qty * strips_per_box)
        if strip_qty < 0:
            strip_qty = 0

        unit_price = Decimal(str(m.price or 0))
        unit_purchase = Decimal(str(m.purchase_price or 0))
        strips_per_box = m.strips_per_box or 1

        try:
            strip_price = Decimal(m.get_strip_price() or unit_price)
        except Exception:
            strip_price = unit_price
        strip_purchase = (unit_purchase / Decimal(strips_per_box)) if strips_per_box else Decimal('0')

        total_selling += (unit_price * Decimal(box_qty)) + (strip_price * Decimal(strip_qty))
        total_purchase += (unit_purchase * Decimal(box_qty)) + (strip_purchase * Decimal(strip_qty))

    total_profit = total_selling - total_purchase

    context = {
        'total_selling': f"{total_selling:.2f}",
        'total_purchase': f"{total_purchase:.2f}",
        'total_profit': f"{total_profit:.2f}",
    }
    return render(request, 'reports/inventory_summary.html', context)