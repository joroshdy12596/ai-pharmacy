import base64
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse
from django.core import signing
from django.utils import timezone

logger = logging.getLogger(__name__)

class ReportsBasicAuthMiddleware:
    """
    Simple HTTP Basic Auth middleware that protects any path starting with
    /reports/ when REPORTS_BASIC_AUTH_USER and REPORTS_BASIC_AUTH_PASS are set
    in Django settings (or via environment variables).

    Behavior:
    - If credentials are not configured, middleware does nothing (no auth enforced).
    - If configured, requests to paths under /reports/ must supply HTTP Basic Auth
      matching the configured username/password, otherwise a 401 with
      WWW-Authenticate header is returned.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # user optional: if not provided, any username is accepted as long as password matches
        self.user = getattr(settings, 'REPORTS_BASIC_AUTH_USER', '')
        self.password = getattr(settings, 'REPORTS_BASIC_AUTH_PASS', '')
        self.realm = getattr(settings, 'REPORTS_BASIC_AUTH_REALM', 'Reports')
        # TTL (seconds) for how long an authenticated session lasts before forcing re-prompt
        self.ttl = int(getattr(settings, 'REPORTS_BASIC_AUTH_TTL', 300))
        if not self.password:
            logger.info('ReportsBasicAuthMiddleware disabled: REPORTS_BASIC_AUTH_PASS not set')

        # cookie names
        self.ts_cookie = getattr(settings, 'REPORTS_BASIC_AUTH_TS_COOKIE', 'reports_auth_ts')
        self.ever_cookie = getattr(settings, 'REPORTS_BASIC_AUTH_EVER_COOKIE', 'reports_auth_ever')
        self.challenged_cookie = getattr(settings, 'REPORTS_BASIC_AUTH_CHALLENGED_COOKIE', 'reports_auth_challenged')

    def __call__(self, request):
        # Only protect URLs starting with /reports/
        path = request.path or ''
        # protect /reports/ only when a password is configured
        if path.startswith('/reports/') and self.password:
            # 1) If we have a signed timestamp cookie and it's not expired -> allow
            ts_val = request.COOKIES.get(self.ts_cookie)
            if ts_val:
                try:
                    ts = signing.loads(ts_val)
                    # ts is ISO format string
                    ts_dt = datetime.fromisoformat(ts)
                    if timezone.is_aware(ts_dt):
                        # convert to naive for comparison
                        ts_dt = ts_dt.replace(tzinfo=None)
                    age = (datetime.utcnow() - ts_dt).total_seconds()
                    if age <= self.ttl:
                        return self.get_response(request)
                except Exception:
                    logger.debug('Invalid or tampered ts cookie', exc_info=True)

            # 2) If no valid ts cookie, check if this request is a follow-up after a previous 401 challenge
            challenged = request.COOKIES.get(self.challenged_cookie)
            auth = request.META.get('HTTP_AUTHORIZATION')

            # helper to validate Authorization header
            def auth_valid(auth_header):
                if not auth_header or not auth_header.startswith('Basic '):
                    return False, None
                try:
                    encoded = auth_header.split(' ', 1)[1].strip()
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    username, sep, passwd = decoded.partition(':')
                    if sep and passwd == self.password and (not self.user or username == self.user):
                        return True, username
                except Exception:
                    logger.debug('Failed to decode Basic auth header for reports', exc_info=True)
                return False, None

            valid, username = auth_valid(auth)

            # if this request is a follow-up (challenged cookie present) and Authorization is valid -> accept and set ts cookie
            if challenged and valid:
                resp = self.get_response(request)
                # set signed timestamp cookie for ttl seconds
                now_iso = datetime.utcnow().isoformat()
                signed = signing.dumps(now_iso)
                resp.set_cookie(self.ts_cookie, signed, max_age=self.ttl, httponly=True)
                # set 'ever' marker long lived
                resp.set_cookie(self.ever_cookie, '1', max_age=60 * 60 * 24 * 30, httponly=True)
                # clear challenged cookie
                resp.set_cookie(self.challenged_cookie, '', max_age=0)
                return resp

            # Otherwise, issue a challenge (set a short 'challenged' cookie so the browser's follow-up can be accepted)
            # Only set challenged cookie when we either have an Authorization header (so browser will prompt) or not.
            res = HttpResponse('Authentication required', status=401)
            res['WWW-Authenticate'] = f'Basic realm="{self.realm}"'
            # short-lived marker allowing the browser's follow-up to be accepted
            res.set_cookie(self.challenged_cookie, '1', max_age=60, httponly=True)
            return res

        return self.get_response(request)
