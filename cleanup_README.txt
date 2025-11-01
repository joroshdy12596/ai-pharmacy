Cleanup empty StockEntry rows

Command:

    python manage.py cleanup_empty_stock [--dry-run]

- Use --dry-run to list rows that would be deleted without removing them.
- Schedule this command to run periodically (e.g., daily or hourly) using Task Scheduler on Windows or cron on Linux.

Example Task Scheduler action:
- Program/script: C:\Python39\python.exe
- Add arguments: C:\Users\Dr.ESRAA\Desktop\ai-pharmacy\manage.py cleanup_empty_stock
- Start in: C:\Users\Dr.ESRAA\Desktop\ai-pharmacy

Or run via a batch file:

backup_and_cleanup.bat:

@echo off
cd /d C:\Users\Dr.ESRAA\Desktop\ai-pharmacy
python manage.py cleanup_empty_stock

Schedule that batch file every 2 hours if desired.
