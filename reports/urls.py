from django.urls import path
from . import views
from pharmacy.views import ProfitAnalyticsView

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    # profit analytics page (uses the existing ProfitAnalyticsView from pharmacy)
    path('profit/', ProfitAnalyticsView.as_view(), name='profit'),
]
