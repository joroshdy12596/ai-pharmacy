from django.urls import path
from . import views
from pharmacy.views import ProfitAnalyticsView

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    # profit analytics page (uses the existing ProfitAnalyticsView from pharmacy)
    path('profit/', ProfitAnalyticsView.as_view(), name='profit'),
    # Inventory purchase cost standalone page
    path('inventory-cost/', views.inventory_cost, name='inventory_cost'),
    path('inventory-cost/export/', views.inventory_cost_export, name='inventory_cost_export'),
    path('inventory-summary/', views.inventory_summary, name='inventory_summary'),
]
