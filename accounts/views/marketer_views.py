import time
import uuid
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from rest_framework import status, generics
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)

from accounts.authentication import MarketerJWTAuthentication
from accounts.tokens import generate_marketer_jwt_tokens
from ..models import Marketer
from ..permissions import IsOwnerMarketer
from ..serializers.marketer_serializers import (
    AcceptTermsSerializer,
    FinalapprovalofMarketer,
    LoginWithPasswordMarketerSerializer,
    MarketerSignupSerializer,
    RequestPasswordResetMarketerSerializer,
    ResetPasswordMarketerSerializer,
    SendOTPMarketerSerializer,
    VerifyOTPEmailMarketerSerializer,
    VerifyOTPMarketerSerializer,
)
from ..throttles import OTPThrottle
from ..utils import OTPService


class MarketerAuthViewSet(ViewSet):
    def get_authenticators(self):
        action = getattr(self, 'action', None)
        unauthenticated_actions = [
            'send_otp', 'resend_otp', 'verify_otp',
            'request_password_reset_otp', 'resend_password_reset_otp', "login_with_password",
            'verify_otp_email', 'reset_password'
        ]
        if action in unauthenticated_actions:
            return []
        return [MarketerJWTAuthentication()]
        
    def list(self, request, *args, **kwargs):
        return Response({
            "send_otp": reverse("marketer-auth-send-otp", request=request),
            "resend_otp": reverse("marketer-auth-resend-otp", request=request),
            "verify-otp": reverse("marketer-auth-verify-otp", request=request),
            "login_with_password": reverse("marketer-auth-login-with-password", request=request),
            "request_password_reset_otp": reverse("marketer-auth-request-password-reset", request=request),
            "resend_password_reset_otp": reverse("marketer-auth-resend-password-reset", request=request),
            "verify_otp_email": reverse("marketer-auth-verify-otp-email", request=request),
            "reset_password": reverse("marketer-auth-reset-password", request=request),
        })
    authentication_classes = []
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    @extend_schema(
        request=SendOTPMarketerSerializer,
        responses={
            201: OpenApiResponse(
                description="کد ارسال شد. در حالت DEBUG مقدار `otp_token` نیز بازگردانده می‌شود",
                examples=[
                    OpenApiExample(
                        "پاسخ موفق در حالت DEBUG",
                        value={
                            "detail": "کد ورود ارسال شد",
                            "otp_token": "7f7b3f49-f3fa-4d13-9e2a-452c4d3c5fcf"
                        }
                    ),
                    OpenApiExample(
                        "پاسخ موفق در حالت توسعه",
                        value={
                            "detail": "کد ورود ارسال شد"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطا در داده‌ها",
                examples=[
                    OpenApiExample(
                        "شماره موبایل نامعتبر",
                        value={"phone_number": ["شماره موبایل معتبر نیست"]}
                    )
                ]
            )
        },
        description="ارسال کد ورود یک‌بارمصرف (OTP) برای بازاریاب. در حالت DEBUG مقدار `otp_token` نیز بازگردانده می‌شود"
    )
    def send_otp_login(self, request):
        throttle = self.throttle_classes[0]()
        if not throttle.allow_request(request, self):
            cache_key = throttle.get_cache_key(request)
            data = cache.get(cache_key, {})
            blocked_until = data.get('blocked_until')
            if blocked_until:
                remaining = int(blocked_until - time.time())
                raise Throttled(detail=f"ارسال بیش از حد مجاز {remaining // 60} دقیقه دیگر امتحان کنید")
            raise Throttled(detail="ارسال بیش از حد مجاز")

        serializer = SendOTPMarketerSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone_number']
            remember_me = serializer.validated_data.get('remember_me', False)

            marketer, created = Marketer.objects.get_or_create(phone_number=phone)
            if created:
                marketer.is_verified = False
                marketer.save()

            otp_service = OTPService(marketer, purpose="login")
            otp_service.send()

            otp_token = str(uuid4())
            timeout = 60 * 60 * 24 * 5 if remember_me else settings.OTP_CODE_TIMEOUT
            cache.set(otp_token, marketer.id, timeout=timeout)

            response_data = {"detail": "کد ورود به موبایل شما ارسال شد"}

            if settings.DEBUG:
                response_data["otp_token"] = otp_token

            return Response(response_data, status=status.HTTP_201_CREATED) 

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'], url_path='send-otp')
    @permission_classes([AllowAny])
    def send_otp(self, request):
        return self.send_otp_login(request)

    @action(detail=False, methods=['post'], url_path='resend-otp')
    @permission_classes([AllowAny])
    def resend_otp(self, request):
        return self.send_otp_login(request)       
   
    @extend_schema(
        request=VerifyOTPMarketerSerializer,
        responses={
            200: OpenApiResponse(
                description="کد تأیید شد",
                examples=[
                    OpenApiExample("تأیید موفق", value={"detail": "کد تأیید شد"})
                ]
            ),
            400: OpenApiResponse(
                description="کد اشتباه یا منقضی",
                examples=[
                    OpenApiExample("کد اشتباه", value={"detail": "کد وارد شده اشتباه است"}),
                    OpenApiExample("توکن منقضی", value={"detail": "توکن نامعتبر است"})
                ]
            )
        },
        description="تأیید کد ورود بازاریاب"
    )
    @action(detail=False, methods=['post'], url_path='verify-otp')
    @permission_classes([AllowAny])
    def verify_otp(self, request):
        serializer = VerifyOTPMarketerSerializer(data=request.data)
        if serializer.is_valid():
            otp_token = serializer.validated_data['otp_token']
            otp_code = serializer.validated_data['otp_code']
            remember_me = serializer.validated_data.get('remember_me', False) 

            marketer_id = cache.get(otp_token)
            if not marketer_id:
                return Response({'detail': 'توکن منقضی یا نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)

            marketer = get_object_or_404(Marketer, id=marketer_id)

            otp_service = OTPService(marketer, purpose="login")
            if not otp_service.is_otp_valid(otp_code):
                return Response({'detail': 'کد وارد شده اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

            cache.delete(f"otp:{marketer.phone_number}")
            cache.delete(otp_token)

            marketer.is_verified = True
            marketer.save()

            refresh_token, access_token = generate_marketer_jwt_tokens(marketer, remember_me)

            return Response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'detail': 'ورود با موفقیت انجام شد'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login-with-password')
    def login_with_password(self, request):
        serializer = LoginWithPasswordMarketerSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            remember_me = serializer.validated_data.get('remember_me', False)

            refresh_token, access_token = generate_marketer_jwt_tokens(user, remember_me)   

            marketer_type = 'marketer' if Marketer.objects.filter(user=user).exists() else 'unknown'

            return Response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_id': user.id,
                'username': user.username,
                'marketer_type': marketer_type,
                'message': '!ورود با موفقیت انجام شد'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_password_reset_otp(self, request):
        self.check_throttles(request)
        serializer = RequestPasswordResetMarketerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email=email).first()
        if user:
            otp_service = OTPService(user)
            otp_code = otp_service.send()
            otp_token = str(uuid.uuid4())
            cache.set(f"otp_token_marketer:{otp_token}", user.id, timeout=settings.OTP_RESET_TIMEOUT)

            response_data = {"detail": "کد بازیابی به ایمیل شما ارسال شد"}
            if settings.DEBUG:
                response_data["otp_token"] = otp_token
                response_data["otp_code"] = otp_code
        else:
            response_data = {"detail": "در صورت وجود حسابی با این ایمیل، کد بازیابی ارسال شد"}

        return Response(response_data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=RequestPasswordResetMarketerSerializer,
        responses={
            201: OpenApiResponse(description="درخواست موفق برای بازیابی رمز عبور. کد تأیید ارسال شد"),
            404: OpenApiResponse(description="کاربر با این ایمیل یافت نشد"),
            400: OpenApiResponse(description="درخواست نامعتبر")
        },
        description="درخواست بازیابی رمز عبور بازاریاب با ایمیل. اگر ایمیل معتبر باشد، کد تأیید ارسال می‌شود"
    )
    @action(detail=False, methods=['post'], url_path='request-password-reset')
    def request_password_reset(self, request):
        return self._send_password_reset_otp(request)

    @action(detail=False, methods=['post'], url_path='resend-password-reset')
    def resend_password_reset(self, request):
        return self._send_password_reset_otp(request)

    @extend_schema(
        request=VerifyOTPEmailMarketerSerializer,
        responses={
            200: OpenApiResponse(description="کد تأیید ایمیل با موفقیت تأیید شد"),
            400: OpenApiResponse(description="خطا در تأیید کد")
        },
        description="تأیید ایمیل بازاریاب با کد ارسال‌شده. در صورت صحت کد، تأیید انجام می‌شود"
    )
    @action(detail=False, methods=['post'], url_path='verify-otp-email-marketer')
    def verify_otp_email(self, request):
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

        serializer = VerifyOTPEmailMarketerSerializer(data=request.data)
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
        cache.delete(otp_token)

        return Response({'detail': 'کد تأیید صحیح است'}, status=status.HTTP_200_OK)

    @extend_schema(
        request=ResetPasswordMarketerSerializer,
        responses={
            200: OpenApiResponse(description="بازنشانی موفق رمز عبور"),
            400: OpenApiResponse(description="خطا در فرآیند بازنشانی رمز عبور")
        },
        description="بازنشانی رمز عبور بازاریاب با استفاده از کد ارسال‌شده به ایمیل"
    )
    @action(detail=False, methods=["post"], url_path="reset-password")
    def reset_password(self, request):
        serializer = ResetPasswordMarketerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        otp_token = serializer.validated_data['otp_token']
        new_password = serializer.validated_data['new_password']
        remember_me = serializer.validated_data.get('remember_me', False)

        user_id = cache.get(otp_token)
        if not user_id:
            return Response({'error': 'مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, id=user_id)

        if not user.is_active:
            return Response({"error": "حساب کاربری غیرفعال است."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(otp_token)

        user.set_password(new_password)
        user.save()

        refresh_token, access_token = generate_jwt_tokens(user, remember_me)

        return Response({
            "message": "رمز عبور با موفقیت تغییر یافت",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, status=status.HTTP_200_OK)

@extend_schema(
    request=AcceptTermsSerializer,
    responses={
        200: OpenApiResponse(
            description="شرایط همکاری پذیرفته شد",
            examples=[
                OpenApiExample(
                    "موفقیت در پذیرش شرایط",
                    value={"message": "شرایط همکاری پذیرفته شد"}
                )
            ],
        ),
        400: OpenApiResponse(
            description="خطا در اعتبارسنجی ورودی",
            examples=[
                OpenApiExample(
                    "خطای اعتبارسنجی",
                    value={"accepted": ["این فیلد الزامی است"]}
                )
            ],
        ),
    },
    description= "پذیرش شرایط همکاری توسط بازاریاب"
)
class MarketerAcceptTermsViewSet(ViewSet):
    def create(self, request):
        serializer = AcceptTermsSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "شرایط همکاری پذیرفته شد"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   

class MarketerSignupViewSet(ModelViewSet):
    serializer_class = MarketerSignupSerializer
    permission_classes = [IsAuthenticated, IsOwnerMarketer]
    authentication_classes = [MarketerJWTAuthentication]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Marketer.objects.filter(pk=self.request.user.pk).select_related("province", "city")
        return Marketer.objects.none()

    def perform_update(self, serializer):
        serializer.save()    

    @extend_schema(
        request=MarketerSignupSerializer,
        responses={
            201: OpenApiResponse(
                description="با موفقیت ذخیره شد",
                examples=[
                    OpenApiExample(
                        "ثبت‌نام موفق",
                        value={"id": 1, "message": "با موفقیت ذخیره شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در پذیرش شرایط همکاری یا اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        "عدم پذیرش شرایط همکاری",
                        value={"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"}
                    ),
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"field_name": ["این فیلد الزامی است"]}
                    ),
                ],
            ),
        },
        description=" در صورت پذیرش شرایط همکاری"
    )
    def create(self, request, *args, **kwargs):
        accepted_terms = request.data.get("accepted_terms", False)
        if not accepted_terms:
            return Response(
                {"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        existing_marketer = Marketer.objects.filter(id=user.id).first()

        if existing_marketer and existing_marketer.accepted_terms:
            return Response(
                {"detail": "شما قبلاً ثبت‌نام کرده‌اید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if existing_marketer:
       
            for field, value in serializer.validated_data.items():
                setattr(existing_marketer, field, value)
            existing_marketer.accepted_terms = True
            existing_marketer.save()
            return Response(
                {"id": existing_marketer.id, "message": "با موفقیت ثبت‌نام شدید"},
                status=status.HTTP_201_CREATED
            )

        new_marketer = Marketer.objects.create_user(phone_number=user.phone_number, **serializer.validated_data)
        new_marketer.accepted_terms = True
        new_marketer.save()

        return Response(
            {"id": new_marketer.id, "message": "با موفقیت ثبت‌نام شدید"},
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        request=MarketerSignupSerializer,
        responses={
            200: OpenApiResponse(
                description="با موفقیت ویرایش شد",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق",
                        value={"message": ".اطلاعات ویرایش شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"field_name": ["مقدار نامعتبر است"]}
                    ),
                ],
            ),
        },
        description="ویرایش اطلاعات بازاریاب"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".اطلاعات بازاریاب ویرایش شد"}, status=status.HTTP_200_OK)


class MarketerOTPVerificationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerMarketer]
    serializer_class = FinalapprovalofMarketer
    authentication_classes = [MarketerJWTAuthentication]
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'
    
    def get_queryset(self):
        return Marketer.objects.filter(pk=self.request.user.pk)

    def get_marketer(self):
        return get_object_or_404(Marketer, pk=self.request.user.pk)

    @extend_schema(
        description="دریافت اطلاعات بازاریاب",
        responses={
            200: OpenApiResponse(
                response=FinalapprovalofMarketer,
                description="اطلاعات بازاریاب با موفقیت دریافت شد",
                examples=[
                    OpenApiExample(
                        "مثال موفق",
                        value={
                            "full_name": "سیراف سیویل",
                            "national_code": "1234567890",
                            "phone_number": "09121234567",
                            "province": "تهران",
                            "city": "تهران",
                            "email": "shadi@example.com"
                        }
                    )
                ]
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        marketer = self.get_marketer()
        serializer = self.get_serializer(marketer)
        return Response({
            "data": serializer.data,
            "links": {
                "send_otp": reverse("finalapproval-marketer-send-otp", request=request),
                "resend_otp": reverse("finalapproval-marketer-resend-otp", request=request),
                "verify_otp": reverse("finalapproval-marketer-verify-otp", request=request),
            },
            "message": "اطلاعات با موفقیت دریافت شد"
        })

    @extend_schema(
        description="ارسال کد تایید ثبت‌نام برای بازاریاب",
        responses={
            201: OpenApiResponse(
                description="کد تایید ارسال شد",
                examples=[
                    OpenApiExample(
                        "ارسال موفق کد",
                        value={
                            "detail": "کد تایید ارسال شد",
                            "otp_token": "550e8400-e29b-41d4-a716-446655440000"
                            if settings.DEBUG else None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="اطلاعات ناقص یا خطا",
                examples=[
                    OpenApiExample(
                        "اطلاعات ناقص",
                        value={"detail": "اطلاعات بازاریاب کامل نیست"}
                    )
                ]
            ),
            429: OpenApiResponse(
                description="محدودیت ارسال بیش از حد",
                examples=[
                    OpenApiExample(
                        "محدودیت ارسال کد",
                        value={"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}
                    )
                ]
            )
        }
    )
    def send_otp_marketer(self, request):
        marketer = self.get_marketer()

        if not marketer.is_complete():
            return Response(
                {"detail": "اطلاعات بازاریاب کامل نیست"},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.check_throttles(request)

        otp_service = OTPService(request.user)
        otp_service.send()

        otp_token = str(uuid.uuid4())
        cache.set(f"otp_token:{otp_token}", request.user.id, timeout=300)
        otp_service.save_otp_token(otp_token)

        response_data = {"detail": "کد تایید ارسال شد"}
        if settings.DEBUG:
            response_data["otp_token"] = otp_token
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="send-otp")
    def send_otp(self, request):
        return self.send_otp_marketer(request)
            
    @action(detail=False, methods=["post"], url_path="resend-otp")
    def resend_otp(self, request):
        return self.send_otp_marketer(request)

    @extend_schema(
        description="تایید کد ارسال شده و نهایی‌سازی ثبت‌نام بازاریاب",
        responses={
            200: OpenApiResponse(
                description="ثبت‌نام بازاریاب تایید شد",
                examples=[
                    OpenApiExample(
                        "تایید موفق",
                        value={"message": "ثبت‌نام شما با موفقیت تایید شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطا در کد یا توکن",
                examples=[
                    OpenApiExample(
                        "کد یا توکن ارسال نشده",
                        value={"detail": "کد یا توکن ارسال نشده"}
                    ),
                    OpenApiExample(
                        "توکن نامعتبر",
                        value={"detail": "توکن نامعتبر است"}
                    ),
                    OpenApiExample(
                        "کد اشتباه",
                        value={"detail": "کد تأیید اشتباه است"}
                    )
                ]
            )
        }
    )
    @action(detail=False, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request):
        marketer = self.get_marketer()
        otp_code = request.data.get("otp_code")
        otp_token = request.data.get("otp_token")

        if not otp_code or not otp_token:
            return Response(
                {"detail": "کد یا توکن ارسال نشده"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_id = cache.get(f"otp_token:{otp_token}")
        if user_id != request.user.id:
            return Response(
                {"detail": "توکن نامعتبر است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_service = OTPService(request.user)
        if not otp_service.is_otp_valid(otp_code):
            return Response(
                {"detail": "کد تأیید اشتباه است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        marketer.is_verified = True
        marketer.save()
        cache.delete(f"otp_token:{otp_token}")

        return Response(
            {"message": "ثبت‌نام شما با موفقیت تایید شد"},
            status=status.HTTP_200_OK
        )