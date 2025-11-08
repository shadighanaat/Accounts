import random
import time
import uuid
from datetime import timedelta

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

# DRF imports
from rest_framework import status, generics
from rest_framework.decorators import action
from rest_framework.exceptions import Throttled
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

# JWT
from rest_framework_simplejwt.tokens import RefreshToken

# DRF Spectacular
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiExample,
    extend_schema
)

# Local imports
from ..models import CustomUser, LegalSeller, RealSeller, SellerType, BuyerLegal
from ..serializers.auth_serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    LoginWithPasswordSerializer,
    VerifyOTPEmailSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer
)
from ..utils import OTPService
from ..throttles import OTPThrottle

def generate_jwt_tokens(user, remember_me=False):
    refresh = RefreshToken.for_user(user)
    if remember_me:
        refresh.set_exp(lifetime=timedelta(days=5))
        refresh.access_token.set_exp(lifetime=timedelta(days=5))
    else:
        refresh.set_exp(lifetime=timedelta(days=1))
        refresh.access_token.set_exp(lifetime=timedelta(minutes=15))
    return str(refresh), str(refresh.access_token)


class AuthViewSet(ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({
            "send_otp_login": reverse("auth-send-otp", request=request),
            "resend_otp": reverse("auth-resend-otp", request=request),
            "verify_otp": reverse("auth-verify-otp", request=request),
            "login_with_password": reverse("auth-login-with-password", request=request),
            "send_password_reset_otp": reverse("auth-request-password-reset", request=request),
            "resend_password_reset_otp": reverse("auth-resend-password-reset", request=request),
            "verify_otp_email": reverse("auth-verify-otp-email", request=request),
            "reset_password": reverse("auth-reset-password", request=request),
        })
    authentication_classes = []
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    @extend_schema(
    request=SendOTPSerializer,
    responses={
        201: OpenApiResponse(
            description="کدارسال شد و توکن بازگردانده شد",
            examples=[
                OpenApiExample(
                    "پاسخ موفق",
                    value={
                        "detail": "سیراف : کد ورود",
                        "otp_token": "uuid-توکن-مثال"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="خطا در ارسال داده‌ها",
            examples=[
                OpenApiExample(
                    "خطا در شماره موبایل",
                    value={"phone_number": ["فرمت شماره موبایل صحیح نیست"]}
                )
            ]
        )
    },
    description="ارسال کد ورود برای شماره موبایل"
    )
    def send_otp_login(self, request):
        throttle = self.throttle_classes[0]() 
        if not throttle.allow_request(request, self):
            cache_key = throttle.get_cache_key(request)
            data = cache.get(cache_key, {})
            blocked_until = data.get('blocked_until')
            if blocked_until:
                remaining = int(blocked_until - time.time())
                raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
            else:
                raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")
     
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            remember_me = serializer.validated_data.get('remember_me', False)

            user, created = CustomUser.objects.get_or_create(phone_number=phone_number ,
            defaults={
            "username": phone_number,
            "is_verified": False,
            })
            if created:
                user.is_verified = False
                user.save()

            otp_service = OTPService(user)
            otp_code = otp_service.send()

            otp_token = str(uuid.uuid4())
            timeout = 60 * 60 * 24 * 5 if remember_me else settings.OTP_CODE_TIMEOUT 
            cache.set(otp_token, user.id, timeout=timeout)

            response_data = {"detail": "کد ورود به موبایل شما ارسال شد"}

            if settings.DEBUG:
                response_data["otp_token"] = otp_token

            return Response(response_data, status=status.HTTP_201_CREATED) 

    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request):
        return self.send_otp_login(request)

    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request):
        return self.send_otp_login(request)       
   
    
    @extend_schema(
    request=VerifyOTPSerializer,
    responses={
        200: OpenApiResponse(
            description="کد تأیید و ورود با موفقیت انجام شد",
            examples=[
                OpenApiExample(
                    "تأیید و ورود موفق",
                    value={
                        "access_token": "<token>",
                        "refresh_token": "<token>",
                        "detail": "ورود با موفقیت انجام شد"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="خطا در تأیید کد",
            examples=[
                OpenApiExample(
                    "توکن منقضی شده",
                    value={"detail": "توکن منقضی یا نامعتبر است"}
                ),
                OpenApiExample(
                    "کد اشتباه",
                    value={"detail": "کد وارد شده اشتباه است"}
                )
            ]
        )
    },
    description="تأیید کد OTP و ورود همزمان"
    )

    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_token = serializer.validated_data['otp_token']
            otp_code = serializer.validated_data['otp_code']
            remember_me = serializer.validated_data.get('remember_me', False) 

            user_id = cache.get(otp_token)
            if not user_id:
                return Response({'detail': 'توکن منقضی یا نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(CustomUser, id=user_id)

            otp_service = OTPService(user)
            if not otp_service.is_otp_valid(otp_code):
                return Response({'detail': 'کد وارد شده اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

            cache.delete(f"otp:{user.phone_number}")
            cache.delete(otp_token)

            user.is_verified = True
            user.save()

            refresh_token, access_token = generate_jwt_tokens(user, remember_me)

            return Response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'detail': 'ورود با موفقیت انجام شد'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=LoginWithPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="ورود موفق با بازگردانی توکن‌ها",
                examples=[
                    OpenApiExample(
                        "ورود موفق",
                        value={
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "message": "!ورود با موفقیت انجام شد"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطا در فرآیند ورود",
                examples=[
                    OpenApiExample(
                        "نام کاربری یا رمز عبور اشتباه",
                        value={"non_field_errors": ["نام کاربری یا رمز عبور اشتباه است"]}
                    )
                ]
            )
        },
        description="ورود با نام کاربری و رمز عبور. در صورت موفقیت، توکن‌ها بازگردانده می‌شوند"
    )
    @action(detail=False, methods=['post'], url_path='login-with-password')
    def login_with_password(self, request):
        serializer = LoginWithPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            remember_me = serializer.validated_data.get('remember_me', False)

            refresh_token, access_token = generate_jwt_tokens(user, remember_me)   

            if RealSeller.objects.filter(user=user).exists():
                seller_type = 'real'
            elif LegalSeller.objects.filter(user=user).exists():
                seller_type = 'legal'
            else:
                seller_type = 'unknown'

            return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user.id,
            'username': user.username,
            'seller_type': seller_type,
            'message': '!ورود با موفقیت انجام شد'
             }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
    request=RequestPasswordResetSerializer,
    responses={
        201: OpenApiResponse(
            description="درخواست موفق برای بازیابی رمز عبور. کد تأیید ارسال شد",
            examples=[
                OpenApiExample(
                    "ارسال موفق ایمیل بازیابی",
                    value={
                        "detail": "کد به ایمیل شما ارسال شد",
                        "otp_token": "uuid-مثال",
                        "otp_code": "123456"
                    }
                )
            ]
        ),
        404: OpenApiResponse(
            description="کاربر با این ایمیل یافت نشد",
            examples=[
                OpenApiExample(
                    "ایمیل نامعتبر",
                    value={"detail": "کاربری با این ایمیل پیدا نشد"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="درخواست نامعتبر",
            examples=[
                OpenApiExample(
                    "فرم نامعتبر",
                    value={"detail": ["این فیلد الزامی است"]}
                )
            ]
        ),
    },
    description="درخواست بازیابی رمز عبور با ایمیل. اگر ایمیل معتبر باشد، کد تأیید به آن ارسال می‌شود"
    )
    def _send_password_reset_otp(self, request):
        self.check_throttles(request) 
        serializer = RequestPasswordResetSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email=email).first()
        if user:
            otp_service = OTPService(user)
            otp_code = otp_service.send()
            otp_token = str(uuid.uuid4())
            cache.set(otp_token, user.id, timeout=settings.OTP_CODE_TIMEOUT)

            response_data = {"detail": "کد بازیابی به ایمیل شما ارسال شد"}
            if settings.DEBUG:
                response_data["otp_token"] = otp_token
                response_data["otp_code"] = otp_code
        else:
            response_data = {"detail": "در صورت وجود حسابی با این ایمیل، کد بازیابی ارسال شد"}

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='request-password-reset')
    def request_password_reset(self, request):
        return self._send_password_reset_otp(request)

    @action(detail=False, methods=['post'], url_path='resend-password-reset')
    def resend_password_reset(self, request):
        return self._send_password_reset_otp(request)

    @extend_schema(
    request=VerifyOTPEmailSerializer,
    responses={
        200: OpenApiResponse(
            description="کد تأیید ایمیل با موفقیت تأیید شد",
            examples=[
                OpenApiExample(
                    "تأیید موفق",
                    value={"detail": "کد تأیید صحیح است"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="خطا در تأیید کد",
            examples=[
                OpenApiExample(
                    "کد نادرست یا منقضی شده",
                    value={"error": "کد وارد شده اشتباه است"}
                ),
                OpenApiExample(
                    "خطای توکن",
                    value={"error": "مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید"}
                ),
                OpenApiExample(
                    "خطای اعتبارسنجی",
                    value={
                        "otp_token": ["این فیلد الزامی است"],
                        "otp_code": ["این فیلد الزامی است"]
                    }
                ),
            ]
        )
    },
    description="تأیید آدرس ایمیل با کد ارسال‌شده به ایمیل کاربر. در صورت صحت کد، پاسخ موفق بازگردانده می‌شود"
    )
    @action(detail=False, methods=['post'], url_path='verify-otp-email')
    def verify_otp_email(self, request):
        throttle = self.throttle_classes[0]() 
        if not throttle.allow_request(request, self):
            cache_key = throttle.get_cache_key(request)
            data = cache.get(cache_key, {})
            blocked_until = data.get('blocked_until')
            if blocked_until:
                remaining = max(0, int(blocked_until - time.time()))
                raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
            else:
                raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")
        serializer = VerifyOTPEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        otp_token = serializer.validated_data['otp_token']
        otp_code = serializer.validated_data['otp_code']
        user_id = cache.get(otp_token)

        if not user_id:
            return Response({'error': 'مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, id=user_id)

        otp_service = OTPService(user)
        if not otp_service.is_otp_valid(otp_code):
            return Response({'error': 'کد وارد شده اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_verified = True
        user.save()
        # cache.delete(otp_token)

        return Response({'detail': 'کد تأیید صحیح است'}, 
        status=status.HTTP_200_OK)

    @extend_schema(
    request=ResetPasswordSerializer,
    responses={
        200: OpenApiResponse(
            description="بازنشانی موفق رمز عبور",
            examples=[
                OpenApiExample(
                    "بازنشانی موفق",
                    value={"message": "رمز عبور با موفقیت تغییر یافت"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="خطا در فرآیند بازنشانی رمز عبور",
            examples=[
                OpenApiExample(
                    "توکن نامعتبر یا منقضی شده",
                    value={"error": "مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید"}
                ),
                OpenApiExample(
                    "خطای اعتبارسنجی",
                    value={
                        "otp_token": ["این فیلد الزامی است"],
                        "new_password": ["این فیلد الزامی است"]
                    }
                )
            ]
        )
    },
    description="بازنشانی رمز عبور کاربر با استفاده از کد ارسال‌شده به ایمیل"
    )
    @action(detail=False, methods=["post"], url_path="reset-password")
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        otp_token = serializer.validated_data['otp_token']
        new_password = serializer.validated_data['new_password']
        remember_me = serializer.validated_data.get('remember_me', False)

        user_id = cache.get(otp_token)
        if not user_id:
            return Response({'error': 'مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, id=user_id)

        if not user.is_active:
            return Response({"error": "حساب کاربری غیرفعال است."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(otp_token)

        user.set_password(new_password)
        user.save()

        refresh_token, access_token = generate_jwt_tokens(user, remember_me)

        return Response({
            "message": "رمز عبور با موفقیت تغییر یافت.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, status=status.HTTP_200_OK)
