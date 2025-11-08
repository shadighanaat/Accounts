import re

# Django imports
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

# DRF imports
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from ..models import CustomUser
from ..validators import validate_iranian_phone

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11,
        help_text="شماره موبایل معتبر (مثلاً 09123456789)",
        label="شماره موبایل",
        validators=[validate_iranian_phone]
        )
    remember_me = serializers.BooleanField(required=False, default=False)


class VerifyOTPSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    otp_code = serializers.CharField()
    remember_me = serializers.BooleanField(required=False, default=False)


class LoginWithPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        User = get_user_model()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("نام کاربری یا رمز عبور نادرست است")

        if not user.check_password(password):
            raise serializers.ValidationError("نام کاربری یا رمز عبور نادرست است")

        if not user.is_active:
            raise serializers.ValidationError("حساب کاربری غیرفعال است")

        attrs['user'] = user
        return attrs

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("کاربری با این ایمیل یافت نشد")
        return value


class VerifyOTPEmailSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    otp_code = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    new_password = serializers.CharField(min_length=7)

    def validate_new_password(self, password):
       
        conditions = [
         (len(password) >= 7, 'پسورد باید حداقل 7 کاراکتر باشد'),
         (re.search(r'[A-Za-z]', password), 'پسورد باید حداقل شامل یک حرف باشد'),
         (re.search(r'[0-9]', password), 'پسورد باید حداقل شامل یک عدد باشد'),
         (len([char for char in password if char.isalnum()]) >= 7, 'پسورد باید حداقل شامل 7 کاراکتر از ترکیب حروف و اعداد باشد')
        ]

        for condition, message in conditions:
            if not condition:
                raise ValidationError(message)
                
        return password
