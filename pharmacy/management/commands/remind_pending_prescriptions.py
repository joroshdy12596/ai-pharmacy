from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from pharmacy.models import GuestPrescriptionRequest
from pharmacy.telegram_utils import send_telegram_message

REMINDER_INTERVAL_MINUTES = 5
MAX_REMINDERS = 6  # stops nagging after 6 * 5min = 30 minutes of silence


class Command(BaseCommand):
    help = (
        'Resends a Telegram reminder for any GuestPrescriptionRequest still '
        'PENDING after REMINDER_INTERVAL_MINUTES, escalating urgency, up to '
        'MAX_REMINDERS times. Intended to run every 5 minutes via a '
        'scheduled task.'
    )

    def handle(self, *args, **options):
        now = timezone.now()
        pending = GuestPrescriptionRequest.objects.filter(
            status='PENDING',
            reminder_count__lt=MAX_REMINDERS,
        )

        sent = 0
        for req in pending:
            reference_time = req.last_reminded_at or req.created_at
            minutes_since = (now - reference_time).total_seconds() / 60
            if minutes_since < REMINDER_INTERVAL_MINUTES:
                continue

            total_wait_minutes = int((now - req.created_at).total_seconds() / 60)
            urgency = '🚨' * min(req.reminder_count + 1, 3)
            reply_path = reverse('pharmacy:staff_prescription_reply', args=[req.id])
            reply_url = f'{settings.PUBLIC_SITE_URL}{reply_path}' if settings.PUBLIC_SITE_URL else reply_path

            send_telegram_message(
                f'{urgency} تذكير: روشتة #{req.id} لسه مستنية رد من {total_wait_minutes} دقيقة!\n'
                f'الاسم: {req.guest_name}, الموبايل: {req.guest_phone}\n'
                f'رابط المراجعة: {reply_url}'
            )

            req.reminder_count += 1
            req.last_reminded_at = now
            req.save(update_fields=['reminder_count', 'last_reminded_at'])
            sent += 1

        self.stdout.write(self.style.SUCCESS(f'Sent {sent} reminder(s)'))
