# Runs every 5 minutes via Windows Task Scheduler. Nudges Telegram again
# for any guest prescription request still PENDING, with escalating urgency.

Set-Location "C:\Users\Mahmoud\ai-pharmacy"
docker exec ai-pharmacy-web-1 python manage.py remind_pending_prescriptions
