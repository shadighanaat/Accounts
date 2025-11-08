from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from accounts.models import Marketer

class MarketerJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(self.get_header(request))
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        if validated_token.get("type") != "marketer":
            return None

        marketer_id = validated_token.get("marketer_id")
        try:
            marketer = Marketer.objects.get(id=marketer_id)
        except Marketer.DoesNotExist:
            raise AuthenticationFailed("کاربر بازاریاب پیدا نشد", code="user_not_found")

        return (marketer, validated_token) 
        