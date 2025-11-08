import requests
from django.utils import timezone
from datetime import timedelta
from random import randint
from django.core.cache import cache

from django.core.mail import send_mail
from django.conf import settings

def send_sms(phone_number, message):
    """
    این تابع پیامک را به شماره موبایل مشخص شده ارسال می‌کند.
    برای ارسال پیامک از یک API سرویس پیامک استفاده می‌شود.
    """
    # URL و API_KEY باید با اطلاعات واقعی شما جایگزین شوند
    api_url = "https://api.sms-service.com/send"  # URL سرویس پیامک
    api_key = "your_api_key"  # کلید API شما

    data = {
        "to": phone_number,
        "message": message,
        "api_key": api_key
    }

    try:
        response = requests.post(api_url, data=data)
        if response.status_code == 200:
            print(f"پیامک به شماره {phone_number} ارسال شد.")
        else:
            print(f"ارسال پیامک به شماره {phone_number} با خطا مواجه شد: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارسال پیامک: {e}")


class OTPService:
    def __init__(self, user, purpose="login", via='sms'):
        """
        :param user: شیء کاربر
        :param purpose: منظور از OTP (مثلاً login یا register)
        :param via: روش ارسال ('sms' یا 'email')
        """
        self.user = user
        self.purpose = purpose
        self.via = via
        self.otp_timeout = getattr(settings, 'OTP_CODE_TIMEOUT', 120)

    def _otp_cache_key(self):
        return f"otp:{self.user.phone_number}:{self.purpose}"

    def _otp_token_cache_key(self, otp_token):
        return f"otp_token:{otp_token}:{self.purpose}"


    def send(self):
        otp_code = str(randint(10000, 99999))
        cache.set(self._otp_cache_key(), otp_code, timeout=self.otp_timeout)

        if self.purpose == "login":
            message = f"سیراف | کد ورود شما: {otp_code}"
        else:
            message = f"سیراف | کد ثبت‌نام شما: {otp_code}"

        if self.via == 'sms':
            self.send_sms(message)
        elif self.via == 'email':
            self.send_email(otp_code)

        if settings.DEBUG:
            print(f"کد برای {self.user.phone_number}: {otp_code}")

        return otp_code

    def send_sms(self, message):
        # اینجا تابع واقعی ارسال پیامک را صدا بزن
        send_sms(self.user.phone_number, message)

    def send_email(self, otp_code):
        subject = 'کد تأیید'
        message = f'کاربر گرامی، کد تأیید شما: {otp_code}\nاین کد تا {self.otp_timeout // 60} دقیقه معتبر است'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [self.user.email]
        send_mail(subject, message, from_email, recipient_list)

    def is_otp_valid(self, otp_code):
        cache_key = self._otp_cache_key()
        cached_otp = cache.get(cache_key)
        if cached_otp == otp_code:
            cache.delete(cache_key)
            return True
        return False

    def save_otp_token(self, otp_token):
        cache.set(self._otp_token_cache_key(otp_token), self.user.id, timeout=self.otp_timeout)

    def get_user_id_from_token(self, otp_token):
        return cache.get(self._otp_token_cache_key(otp_token))