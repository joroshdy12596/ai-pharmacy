import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = 'https://api.telegram.org/bot{token}/sendMessage'


def send_telegram_message(text):
    """
    Sends a plain-text message to the configured Telegram chat. No-ops with
    a log warning if TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID aren't set, so the
    rest of the app keeps working even before Telegram is configured.
    Returns True on success, False otherwise (never raises).
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')

    if not token or not chat_id:
        logger.warning('Telegram not configured (missing bot token or chat id); skipping notification')
        return False

    try:
        resp = requests.post(
            TELEGRAM_API_URL.format(token=token),
            json={'chat_id': chat_id, 'text': text},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception('Failed to send Telegram notification')
        return False
