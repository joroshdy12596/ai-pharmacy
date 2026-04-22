from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Medicine, StockEntry

User = get_user_model()

class PosExpiryAlertTests(TestCase):
    def create_medicine(self, name, barcode='0000000000000'):
        return Medicine.objects.create(
            name=name,
            description='desc',
            price=10.0,
            purchase_price=5.0,
            stock=10,
            category='OTC',
            barcode_number=barcode
        )

    def test_alert_shown_to_staff_with_expiring_items(self):
        staff = User.objects.create_user('staff', 'staff@example.com', 'pass')
        staff.is_staff = True
        staff.save()
        self.client.force_login(staff)

        today = timezone.now().date()
        m1 = self.create_medicine('Med A', barcode='1111111111111')
        StockEntry.objects.create(medicine=m1, quantity=5, expiration_date=today + timedelta(days=10))
        m2 = self.create_medicine('Med B', barcode='2222222222222')
        StockEntry.objects.create(medicine=m2, quantity=2, expiration_date=today + timedelta(days=20))
        m3 = self.create_medicine('Med C', barcode='3333333333333')
        StockEntry.objects.create(medicine=m3, quantity=1, expiration_date=today + timedelta(days=30))
        m4 = self.create_medicine('Med D', barcode='4444444444444')
        StockEntry.objects.create(medicine=m4, quantity=3, expiration_date=today + timedelta(days=100))

        resp = self.client.get(reverse('pharmacy:pos'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('expiring_count', resp.context)
        self.assertTrue(resp.context['expiring_count'] >= 3)
        self.assertIn('expiring_items', resp.context)
        items = resp.context['expiring_items']
        self.assertEqual(len(items), 3)

        content = resp.content.decode()
        # Ensure top 3 medicine names are present in rendered HTML
        self.assertIn('Med A', content)
        self.assertIn('Med B', content)
        self.assertIn('Med C', content)

    def test_alert_not_shown_to_non_staff(self):
        user = User.objects.create_user('user', 'user@example.com', 'pass')
        self.client.force_login(user)
        today = timezone.now().date()
        m1 = self.create_medicine('Med Z', barcode='5555555555555')
        StockEntry.objects.create(medicine=m1, quantity=5, expiration_date=today + timedelta(days=10))

        resp = self.client.get(reverse('pharmacy:pos'))
        self.assertEqual(resp.status_code, 200)
        # Non-staff should not receive expiry context or see the alert
        self.assertFalse(resp.context.get('expiring_count'))
        self.assertNotIn('Med Z', resp.content.decode())

@override_settings(REPORTS_BASIC_AUTH_PASS='')
class ExpiryReportBucketTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # create with password and login via client.login to avoid host/auth subtlety
        self.staff = User.objects.create_user('staff2', 's2@example.com', 'pass')
        self.staff.is_staff = True
        self.staff.save()
        logged = self.client.login(username='staff2', password='pass')
        if not logged:
            # fallback to force_login
            self.client.force_login(self.staff)

    def test_61_90_bucket_contains_entries(self):
        today = timezone.now().date()
        m = Medicine.objects.create(
            name='Test 75d',
            description='d',
            price=5.0,
            purchase_price=2.0,
            stock=1,
            category='OTC',
            barcode_number='9999999999999'
        )
        StockEntry.objects.create(medicine=m, quantity=1, expiration_date=today + timedelta(days=75))
        resp = self.client.get(reverse('pharmacy:expiry_report'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('expiring_90', resp.context)
        self.assertEqual(resp.context['expiring_90'].count(), 1)
        self.assertIn('Test 75d', resp.content.decode())

    @override_settings(REPORTS_BASIC_AUTH_PASS='secret')
    def test_expiry_report_public_without_basic_auth(self):
        """Ensure the expiry report is accessible anonymously even when reports basic auth is set."""
        today = timezone.now().date()
        m = Medicine.objects.create(
            name='Public Test',
            description='d',
            price=3.0,
            purchase_price=1.0,
            stock=1,
            category='OTC',
            barcode_number='8888888888888'
        )
        StockEntry.objects.create(medicine=m, quantity=1, expiration_date=today + timedelta(days=10))
        # Use anonymous client
        client = self.client
        client.logout()
        resp = client.get(reverse('pharmacy:expiry_report'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Public Test', resp.content.decode())
