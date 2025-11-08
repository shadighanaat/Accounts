from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

def generate_marketer_jwt_tokens(marketer, remember_me=False):
    lifetime = timedelta(days=30) if remember_me else timedelta(days=1)

    access = AccessToken()
    access.set_exp(from_time=timezone.now(), lifetime=lifetime)
    access["marketer_id"] = marketer.id
    access["phone_number"] = marketer.phone_number
    access["type"] = "marketer"

    refresh = RefreshToken()
    refresh.set_exp(from_time=timezone.now(), lifetime=timedelta(days=90))
    refresh["marketer_id"] = marketer.id
    refresh["type"] = "marketer"

    return str(refresh), str(access)
