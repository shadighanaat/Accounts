from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
import time

class OTPThrottle(BaseThrottle):
    rate_limit = 2
    cooldown_period = 60 * 2
    block_after_retries = 3 
    block_period = 60 * 60  

    def get_cache_key(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return None
        return f"otp-throttle-{phone_number}"

    def allow_request(self, request, view):
        cache_key = self.get_cache_key(request)
        if not cache_key:
            return True

        data = cache.get(cache_key, {
            'timestamps': [],
            'failures': 0,
            'blocked_until': None,
        })

        now = time.time()

        if data['blocked_until'] and now < data['blocked_until']:
            return False

        data['timestamps'] = [ts for ts in data['timestamps'] if now - ts < 60]

        if len(data['timestamps']) >= self.rate_limit:
            data['failures'] += 1

            if data['failures'] >= self.block_after_retries:
                data['blocked_until'] = now + self.block_period
            else:
                data['blocked_until'] = now + self.cooldown_period

            cache.set(cache_key, data, timeout=self.block_period)
            return False

        data['timestamps'].append(now)
        cache.set(cache_key, data, timeout=self.block_period)
        return True

    def wait(self):
        return None
        