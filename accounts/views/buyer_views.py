import random
import time
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, filters, generics
from rest_framework.decorators import action
from rest_framework.exceptions import Throttled
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)

from ..models import Buyer, BuyerLegal, BuyerReal, BuyerType, CustomUser
from ..serializers.buyer_serializers import (
    SendOTPBuyerSerializer,
    VerifyOTPBuyerSerializer,
    AcceptTermsSerializer,
    BuyerRegisterOrLoginSerializer,
    BuyerLegalSerializer,
    BuyerLegalBusinessInfoSerializer,
    BuyerLegalContactInfoSerializer,
    FinalApprovalOfBuyerLegalSerializer,
    BuyerRealSerializer,
    BuyerRealBusinessInfoSerializer,
    BuyerRealContactInfoSerializer,
    FinalApprovalOfBuyerRealSerializer,
)
from ..throttles import OTPThrottle
from ..utils import OTPService
from ..permissions import IsOwnerUser

class BuyerRegisterOrLoginViewSet(ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({
            "register": reverse("buyer-register", request=request),
            "send_otp_buyer": reverse("buyer-send-otp", request=request),
            "resend_otp": reverse("buyer-resend-otp", request=request),
            "verify_otp": reverse("buyer-verify-otp", request=request),
        })
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    @extend_schema(
        request=BuyerRegisterOrLoginSerializer,
        responses={
            201: OpenApiResponse(
                description="کاربر جدید ساخته شد و باید کد تایید دریافت شود",
                examples=[OpenApiExample(
                    "Created",
                    value={"detail": "کاربر جدید ساخته شد. لطفا کد تایید را دریافت کنید"}
                )]
            ),
            200: OpenApiResponse(
                description="کاربر قبلاً ثبت‌نام کرده است و باید کد تایید دریافت شود",
                examples=[OpenApiExample(
                    "Already Registered",
                    value={"detail": "کاربر قبلا ثبت‌نام کرده است. لطفا کد تایید را دریافت کنید"}
                )]
            ),
            400: OpenApiResponse(description="خطا در داده‌های ورودی")
        },
        description="ثبت‌نام یا ورود با شماره موبایل"
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = BuyerRegisterOrLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        full_name = serializer.validated_data['full_name']
        remember_me = serializer.validated_data.get('remember_me', False)

        user, created = CustomUser.objects.get_or_create(phone_number=phone_number)

        if created:
            user.full_name = full_name
            user.is_verified = False
            user.save()
            status_code = status.HTTP_201_CREATED
            response_detail = "کاربر جدید ساخته شد. لطفا کد تایید را دریافت کنید"
        else:
            status_code = status.HTTP_200_OK
            response_detail = "کاربر قبلا ثبت‌نام کرده است. لطفا کد تایید را دریافت کنید"

        buyer, buyer_created = Buyer.objects.get_or_create(
        user=user,
        defaults={
            'full_name': full_name,
            'phone_number': phone_number, 
        }
    )
        otp_service = OTPService(user, purpose="register")
        otp_service.send()

        otp_token = str(uuid.uuid4())
        timeout = 60 * 60 * 24 * 5 if remember_me else settings.OTP_CODE_TIMEOUT
        cache.set(otp_token, user.id, timeout=timeout)

        response_data = {"detail": response_detail}
        if settings.DEBUG:
            response_data["otp_token"] = otp_token

        return Response(response_data, status=status_code)

    def send_otp_buyer(self, request):
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

        serializer = SendOTPBuyerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        remember_me = serializer.validated_data.get('remember_me', False)

        user, created = CustomUser.objects.get_or_create(phone_number=phone_number)
        if created:
            user.is_verified = False
            user.save()

        otp_service = OTPService(user, purpose="register")
        otp_service.send()

        otp_token = str(uuid.uuid4())
        timeout = 60 * 60 * 24 * 5 if remember_me else settings.OTP_CODE_TIMEOUT
        cache.set(otp_token, user.id, timeout=timeout)

        response_data = {"detail": "کد ورود به موبایل شما ارسال شد"}

        if settings.DEBUG:
            response_data["otp_token"] = otp_token

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request):
        return self.send_otp_buyer(request)

    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request):
        return self.send_otp_buyer(request)

    @extend_schema(
        request=VerifyOTPBuyerSerializer,
        responses={
            200: OpenApiResponse(
                description="کد تایید با موفقیت انجام شد",
                examples=[
                    OpenApiExample(
                        "تایید موفق",
                        value={"detail": "کد تایید با موفقیت انجام شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطا در تایید کد",
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
            ),
            429: OpenApiResponse(
                description="بیش از حد تلاش شده است",
                examples=[
                    OpenApiExample(
                        "بلاک موقت",
                        value={"detail": "بیش از حد تلاش کردید. لطفاً ۵ دقیقه دیگر امتحان کنید."}
                    )
                ]
            ),
        },
        description="تأیید کد ورود ارسال‌شده برای شماره موبایل"
    )
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = VerifyOTPBuyerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_token = serializer.validated_data['otp_token']
        otp_code = serializer.validated_data['otp_code']
        user_id = cache.get(otp_token)

        if not user_id:
            return Response(
                {'detail': 'توکن منقضی یا نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(CustomUser, id=user_id)
        cache_key = f"otp-verify-attempts-{user.phone_number}"

        blocked_until = cache.get(f"{cache_key}-blocked")
        if blocked_until and time.time() < blocked_until:
            return Response(
                {'detail': 'بیش از حد تلاش کردید. لطفاً 60 دقیقه دیگر امتحان کنید'},
                status=429
            )

        otp_service = OTPService(user, purpose="register")
        if not otp_service.is_otp_valid(otp_code):
            failures = cache.get(cache_key, 0) + 1
            cache.set(cache_key, failures, timeout=60 * 10)

            if failures >= 5:
                cache.set(f"{cache_key}-blocked", time.time() + 60 * 5, timeout=60 * 5)
                return Response(
                    {'detail': 'بیش از حد تلاش کردید. لطفاً ۵ دقیقه دیگر امتحان کنید'},
                    status=429
                )

            return Response(
                {'detail': 'کد وارد شده اشتباه است'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache.delete(cache_key)
        cache.delete(f"{cache_key}-blocked")

        user.is_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': 'کد تایید با موفقیت انجام شد',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    description="پذیرش شرایط همکاری توسط کاربر"
)
class BuyerAcceptTermsViewSet(ViewSet):
    def create(self, request):
        serializer = AcceptTermsSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "شرایط همکاری پذیرفته شد"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BuyerLegalViewSet(ModelViewSet):
    serializer_class = BuyerLegalSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]
    
    def get_buyer(self):
        if not hasattr(self, '_buyer'):
            self._buyer = get_object_or_404(Buyer, user=self.request.user)
        return self._buyer

    def get_queryset(self):
        buyer = self.get_buyer()
        return (
            BuyerLegal.objects
            .filter(buyer=buyer)
            .select_related("buyer", "buyer__user")
            .prefetch_related("buyer_types")
        )
        
    def perform_update(self, serializer):
        serializer.save()

    @extend_schema(
        request=BuyerLegalSerializer,
        responses={
            201: OpenApiResponse(
                description="احراز هویت خریدار حقوقی با موفقیت انجام شد",
                examples=[
                    OpenApiExample(
                        "ثبت‌نام موفق",
                        value={"id": 1, "message": ".احراز هویت با موفقیت ثبت شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطا در پذیرش شرایط یا اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        "شرایط همکاری پذیرفته نشده",
                        value={"detail": ".برای ثبت‌ نام باید شرایط همکاری را بپذیرید"}
                    ),
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"field": ["این فیلد الزامی است"]}
                    )
                ]
            )
        },
        description="ثبت‌ نام خریدار حقوقی در صورت پذیرش شرایط همکاری"
    )
    def create(self, request, *args, **kwargs):
        accepted_terms = request.data.get("accepted_terms", False)
        if not accepted_terms:
            return Response(
                {"detail": ".برای ثبت‌ نام باید شرایط همکاری را بپذیرید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if BuyerLegal.objects.filter(buyer__user=request.user).exists():
            return Response(
                {"detail": "شما قبلاً ثبت‌نام کرده‌اید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        buyer = self.get_buyer()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        buyer_legal = serializer.save(buyer=buyer) 

        return Response(
            {"id": buyer_legal.id, "message": ".احراز هویت با موفقیت ثبت شد"},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=BuyerLegalSerializer,
        responses={
            200: OpenApiResponse(
                description="ویرایش اطلاعات خریدار حقوقی",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق",
                        value={"message": ".اطلاعات احراز هویت ویرایش شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"field": ["مقدار نامعتبر است"]}
                    )
                ]
            )
        },
        description="ویرایش اطلاعات احراز هویت خریدار حقوقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)


class BuyerLegalBusinessInfoViewSet(ModelViewSet):
    serializer_class = BuyerLegalBusinessInfoSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter]
    search_fields = ['business_fields__name']

    def get_queryset(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return (
            BuyerLegal
            .objects.filter(buyer=buyer)
            .select_related("buyer", "buyer__user", "business_category")
            .prefetch_related("business_fields")
        )
        
    @extend_schema(
        request=BuyerLegalBusinessInfoSerializer,
        responses={
            201: OpenApiResponse(
                description="اطلاعات کسب‌وکار با موفقیت ثبت شد",
                examples=[
                    OpenApiExample(
                        "ثبت موفق",
                        value={"id": 1, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی فایل‌ها یا داده‌ها",
                examples=[
                    OpenApiExample(
                        "حجم فایل زیاد است",
                        value={"ceo_national_card": ["حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد"]}
                    ),
                    OpenApiExample(
                        "فیلد الزامی",
                        value={"economic_number": ["این فیلد الزامی است"]}
                    )
                ]
            )
        },
        description="ثبت اطلاعات کسب‌وکار برای خریدار حقوقی"
    )
    def create(self, request, *args, **kwargs):
        buyer = get_object_or_404(Buyer, user=request.user)
        buyer_legal = get_object_or_404(BuyerLegal, buyer=buyer)

        if BuyerLegalBusinessInfo.objects.filter(buyer_legal=buyer_legal).exists():
            return Response(
                {"detail": "اطلاعات کسب‌وکار قبلاً ثبت شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business_fields = serializer.validated_data.pop("business_fields", [])

        instance = serializer.save(buyer_legal=buyer_legal)

        if business_fields:
            instance.business_fields.set(business_fields)

        return Response(
            {"id": serializer.instance.id, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=BuyerLegalBusinessInfoSerializer,
        responses={
            200: OpenApiResponse(
                description="ویرایش اطلاعات کسب‌وکار",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق",
                        value={"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        "فایل نامعتبر",
                        value={"activity_license": ["حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد"]}
                    )
                ]
            )
        },
        description="ویرایش اطلاعات کسب‌وکار خریدار حقوقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        business_fields = serializer.validated_data.pop("business_fields", None)
        instance = serializer.save()

        if business_fields is not None:
            current_ids = set(instance.business_fields.values_list("id", flat=True))
            new_ids = set([field.id for field in business_fields])
            if current_ids != new_ids:
                instance.business_fields.set(business_fields)
        return Response({"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}, status=status.HTTP_200_OK)


class BuyerLegalContactInfoViewSet(ModelViewSet):
    serializer_class = BuyerLegalContactInfoSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return BuyerLegal.objects.filter(buyer=buyer)

    @extend_schema(
        request=BuyerLegalContactInfoSerializer,
        responses={
            201: OpenApiResponse(
                description="اطلاعات تماس با موفقیت ثبت شد",
                examples=[OpenApiExample("ثبت موفق", value={"message": "اطلاعات تماس ثبت شد"})]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
                examples=[
                    OpenApiExample("آدرس انبار الزامی", value={"warehouse_address": ["در صورت داشتن انبار، وارد کردن آدرس آن الزامی است."]})
                ]
            )
        },
        description="ثبت اطلاعات تماس خریدار حقوقی"
    )
    def create(self, request, *args, **kwargs):
        buyer = get_object_or_404(Buyer, user=request.user)
        buyer_legal = get_object_or_404(BuyerLegal, buyer=buyer).select_related("user", "province", "city")

        if BuyerLegalContactInfo.objects.filter(buyer_legal=buyer_legal).exists():
            return Response(
                {"detail": "اطلاعات تماس قبلاً ثبت شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(buyer_legal=buyer_legal)

        return Response({"message": "اطلاعات تماس ثبت شد"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=BuyerLegalContactInfoSerializer,
        responses={
            200: OpenApiResponse(description="ویرایش اطلاعات تماس", examples=[OpenApiExample("ویرایش موفق", value={"message": "ویرایش انجام شد"})])
        },
        description="ویرایش اطلاعات تماس خریدار حقوقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": "ویرایش انجام شد"}, status=status.HTTP_200_OK)          


class BuyerLegalOTPVerificationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerUser]
    serializer_class = FinalApprovalOfBuyerLegalSerializer
    authentication_classes = [JWTAuthentication]
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    def get_queryset(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return BuyerLegal.objects.filter(buyer=buyer).select_related("buyer__user", "province", "city")

    def get_legal_buyer(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return get_object_or_404(
            BuyerLegal.objects.select_related("buyer__user", "province", "city"),
            buyer=buyer
    )

    @extend_schema(
        description="دریافت اطلاعات خریدار",
        responses={
            200: OpenApiResponse(
                description="اطلاعات خریدار با موفقیت دریافت شد",
                examples=[
                    OpenApiExample(
                        "دریافت موفق",
                        value={"id": 1, "name": "فروشگاه فلان", "is_verified": False}
                    )
                ],
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data, 
            "links": {
            "send_otp_signup": reverse("finalapproval-legal-buyer-send-otp", request=request),
            "resend_otp": reverse("finalapproval-legal-buyer-resend-otp", request=request),
            "verify_otp": reverse("finalapproval-legal-buyer-verify-otp", request=request),
        },
            "message": "اطلاعات با موفقیت دریافت شد"
        })

    @extend_schema(
    responses={
        201: OpenApiResponse(
            description="کد ثبت‌ نام ارسال شد",
            examples=[
                OpenApiExample(
                    "ارسال موفق کد",
                    value={
                        "detail": "کد ثبت‌ نام به موبایل شما ارسال شد.",
                        "otp_token": "550e8400-e29b-41d4-a716-446655440000"
                    }
                )
            ],
        ),
        403: OpenApiResponse(
            description="عدم دسترسی به خریدار",
            examples=[
                OpenApiExample(
                    "دسترسی غیرمجاز",
                    value={"detail": "دسترسی غیرمجاز"}
                )
            ],
        ),
        429: OpenApiResponse(
            description="محدودیت ارسال بیش از حد",
            examples=[
                OpenApiExample(
                    "محدودیت ارسال کد",
                    value={"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}
                )
            ],
        )
    },
    description="ارسال کد ثبت‌ نام (OTP) به شماره موبایل فروشنده حقوقی",
    operation_id="send_otp_for_legal_buyer"
    )
    def send_otp_signup(self, request):
        legal_buyer = self.get_legal_buyer()
        if not legal_buyer:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if not legal_buyer.is_complete():
            return Response({"detail": "اطلاعات فروشنده کامل نیست. لطفاً همه فیلدهای لازم را تکمیل کنید"},
                    status=status.HTTP_400_BAD_REQUEST)    

        self.check_throttles(request)
        otp_service = OTPService(request.user)
        otp_service.send()

        otp_token = str(uuid.uuid4())
        cache.set(f"otp_token:{otp_token}", request.user.id, timeout=300)
        otp_service.save_otp_token(otp_token)

        response_data = {"detail": "کد فعال‌سازی ارسال شد"}
        if settings.DEBUG:
            response_data["otp_token"] = otp_token
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request, pk=None):
        return self.send_otp_signup(request)

    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request, pk=None):
        return self.send_otp_signup(request) 
    
    @extend_schema(
    request=OpenApiExample(
        "درخواست تایید کد",
        value={
            "otp_code": "123456",
            "otp_token": "550e8400-e29b-41d4-a716-446655440000"
        },
        request_only=True,
    ),
    responses={
        200: OpenApiResponse(
            description="کد با موفقیت تایید شد",
            examples=[
                OpenApiExample(
                    "تایید موفق",
                    value={"message": "ثبت‌ نام شما با موفقیت تأیید شد"}
                )
            ],
        ),
        400: OpenApiResponse(
            description="خطا در ورودی",
            examples=[
                OpenApiExample("توکن ارسال نشده", value={"detail": "توکن ارسال نشده"}),
                OpenApiExample("توکن نامعتبر", value={"detail": "توکن نامعتبر است"}),
                OpenApiExample("کد اشتباه", value={"detail": "کد تأیید اشتباه است"}),
            ],
        ),
        403: OpenApiResponse(
            description="عدم دسترسی به فروشنده",
            examples=[
                OpenApiExample("دسترسی غیرمجاز", value={"detail": "دسترسی غیرمجاز"})
            ]
        )
    },
    description="تأیید کد ارسال شده برای فروشنده حقوقی با استفاده از توکن",
    operation_id="verify_otp_for_legal_buyer"
    )

    @action(detail=False, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request, pk=None):
        legal_buyer = self.get_legal_buyer()

        if not legal_buyer:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if legal_buyer.buyer.user != user:
            return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)

        otp_code = request.data.get("otp_code")
        otp_token = request.data.get("otp_token")

        if not otp_code:
            return Response({"detail": "کد تأیید ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_token:
            return Response({"detail": "توکن ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = cache.get(f"otp_token:{otp_token}")
        if user_id != user.id:
            return Response({"detail": "توکن نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

        otp_service = OTPService(user)
        if otp_service.is_otp_valid(otp_code):
            if not legal_buyer.is_complete():
                return Response({"detail": "اطلاعات فروشنده ناقص است. ثبت‌نام قابل تأیید نیست"},
                    status=status.HTTP_400_BAD_REQUEST)

            legal_buyer.is_verified = True
            legal_buyer.save()
            cache.delete(f"otp_token:{otp_token}")
            return Response({"message": "ثبت‌ نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)

        return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)   


class BuyerRealViewSet(ModelViewSet):
    serializer_class = BuyerRealSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]

    def get_buyer(self):
        if not hasattr(self, '_buyer'):
            self._buyer = get_object_or_404(Buyer, user=self.request.user)
        return self._buyer

    def get_queryset(self):
        buyer = self.get_buyer()
        return (
            BuyerReal.objects
            .filter(buyer=buyer)
            .select_related("buyer", "buyer__user")
            .prefetch_related("buyer_types")
        )

    def perform_update(self, serializer):
        serializer.save()

    @extend_schema(
        request=BuyerRealSerializer,
        responses={
            201: OpenApiResponse(
                description="اطلاعات خریدار حقیقی با موفقیت ثبت شد",
                examples=[
                    OpenApiExample(
                        "ثبت موفق",
                        value={"id": 1, "message": "اطلاعات با موفقیت ثبت شد."}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"national_code": ["این فیلد الزامی است."]}
                    )
                ],
            ),
        }
    )
    def create(self, request, *args, **kwargs):
        accepted_terms = request.data.get("accepted_terms", False)
        if not accepted_terms:
            return Response(
                {"detail": ".برای ثبت‌ نام باید شرایط همکاری را بپذیرید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if BuyerReal.objects.filter(buyer__user=request.user).exists():
            return Response(
                {"detail": "شما قبلاً ثبت‌نام کرده‌اید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        buyer = self.get_buyer()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        buyer_real = serializer.save(buyer=buyer) 

        return Response(
            {"id": buyer_real.id, "message": ".احراز هویت با موفقیت ثبت شد"},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=BuyerRealSerializer,
        responses={
            200: OpenApiResponse(
                description="ویرایش اطلاعات خریدار حقیقی",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق",
                        value={"message": "اطلاعات با موفقیت ویرایش شد."}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
            ),
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)

class BuyerRealBusinessInfoViewSet(ModelViewSet):
    serializer_class = BuyerRealBusinessInfoSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter]
    search_fields = ['business_fields__name']

    def get_queryset(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return (
            BuyerReal
            .objects.filter(buyer=buyer)
            .select_related("buyer", "buyer__user", "business_category")
            .prefetch_related("business_fields")
        )

    @extend_schema(
        request=BuyerRealBusinessInfoSerializer,
        responses={
            201: OpenApiResponse(
                description="اطلاعات کسب‌وکار با موفقیت ثبت شد",
                examples=[
                    OpenApiExample(
                        "ثبت موفق",
                        value={"id": 1, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی فایل‌ها یا داده‌ها",
                examples=[
                    OpenApiExample(
                        "حجم فایل زیاد است",
                        value={"ceo_national_card": ["حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد"]}
                    ),
                    OpenApiExample(
                        "فیلد الزامی",
                        value={"economic_number": ["این فیلد الزامی است"]}
                    )
                ]
            )
        },
        description="ثبت اطلاعات کسب‌وکار برای خریدار حقیقی"
    )
    def create(self, request, *args, **kwargs):
        buyer = get_object_or_404(Buyer, user=request.user)
        buyer_real = get_object_or_404(BuyerReal, buyer=buyer)

        if BuyerRealBusinessInfo.objects.filter(buyer_real=buyer_real).exists():
            return Response(
                {"detail": "اطلاعات کسب‌وکار قبلاً ثبت شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        business_fields = serializer.validated_data.pop("business_fields", [])

        instance = serializer.save(buyer_real=buyer_real)

        if business_fields:
            instance.business_fields.set(business_fields)

        return Response(
            {"id": serializer.instance.id, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=BuyerRealBusinessInfoSerializer,
        responses={
            200: OpenApiResponse(
                description="ویرایش اطلاعات کسب‌وکار",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق",
                        value={"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        "فایل نامعتبر",
                        value={"activity_license": ["حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد"]}
                    )
                ]
            )
        },
        description="ویرایش اطلاعات کسب‌وکار خریدار حقیقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        business_fields = serializer.validated_data.pop("business_fields", None)
        instance = serializer.save()

        if business_fields is not None:
            current_ids = set(instance.business_fields.values_list("id", flat=True))
            new_ids = set([field.id for field in business_fields])
            if current_ids != new_ids:
                instance.business_fields.set(business_fields)
        return Response({"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}, status=status.HTTP_200_OK)
     


class BuyerRealContactInfoViewSet(ModelViewSet):
    serializer_class = BuyerRealContactInfoSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return BuyerReal.objects.filter(buyer=buyer)

    @extend_schema(
        request=BuyerRealContactInfoSerializer,
        responses={
            201: OpenApiResponse(
                description="اطلاعات تماس با موفقیت ثبت شد",
                examples=[OpenApiExample("ثبت موفق", value={"message": "اطلاعات تماس ثبت شد"})]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
                examples=[
                    OpenApiExample("آدرس انبار الزامی", value={"warehouse_address": ["در صورت داشتن انبار، وارد کردن آدرس آن الزامی است"]})
                ]
            )
        },
        description="ثبت اطلاعات تماس خریدار حقیقی"
    )
    def create(self, request, *args, **kwargs):
        buyer = get_object_or_404(Buyer, user=request.user)
        buyer_real = get_object_or_404(BuyerReal, buyer=buyer).select_related("user", "province", "city")

        if BuyerReal.objects.filter(buyer_real=buyer_real).exists():
            return Response(
                {"detail": "اطلاعات تماس قبلاً ثبت شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(buyer_real=buyer_real)

        return Response({"message": "اطلاعات تماس ثبت شد"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=BuyerRealContactInfoSerializer,
        responses={
            200: OpenApiResponse(description="ویرایش اطلاعات تماس", examples=[OpenApiExample("ویرایش موفق", value={"message": "ویرایش انجام شد"})])
        },
        description="ویرایش اطلاعات تماس خریدار حقیقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": "ویرایش انجام شد"}, status=status.HTTP_200_OK)          


class BuyerRealOTPVerificationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerUser]
    serializer_class = FinalApprovalOfBuyerRealSerializer
    authentication_classes = [JWTAuthentication]
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    def get_queryset(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return BuyerReal.objects.filter(buyer=buyer).select_related("buyer__user", "province", "city")

    def get_real_buyer(self):
        buyer = get_object_or_404(Buyer, user=self.request.user)
        return get_object_or_404(
            BuyerReal.objects.select_related("buyer__user", "province", "city"),
            buyer=buyer
    )

    @extend_schema(
        description="دریافت اطلاعات خریدار",
        responses={
            200: OpenApiResponse(
                description="اطلاعات خریدار با موفقیت دریافت شد",
                examples=[
                    OpenApiExample(
                        "دریافت موفق",
                        value={"id": 1, "name": "فروشگاه فلان", "is_verified": False}
                    )
                ],
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data, 
            "links": {
            "send_otp_signup": reverse("finalapproval-real-buyer-send-otp", request=request),
            "resend_otp": reverse("finalapproval-real-buyer-resend-otp", request=request),
            "verify_otp": reverse("finalapproval-real-buyer-verify-otp", request=request),
        },
            "message": "اطلاعات با موفقیت دریافت شد"
        })

    @extend_schema(
    responses={
        201: OpenApiResponse(
            description="کد ثبت‌ نام ارسال شد",
            examples=[
                OpenApiExample(
                    "ارسال موفق کد",
                    value={
                        "detail": "کد ثبت‌ نام به موبایل شما ارسال شد.",
                        "otp_token": "550e8400-e29b-41d4-a716-446655440000"
                    }
                )
            ],
        ),
        403: OpenApiResponse(
            description="عدم دسترسی به خریدار",
            examples=[
                OpenApiExample(
                    "دسترسی غیرمجاز",
                    value={"detail": "دسترسی غیرمجاز"}
                )
            ],
        ),
        429: OpenApiResponse(
            description="محدودیت ارسال بیش از حد",
            examples=[
                OpenApiExample(
                    "محدودیت ارسال کد",
                    value={"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}
                )
            ],
        )
    },
    description="ارسال کد ثبت‌ نام (OTP) به شماره موبایل فروشنده حقوقی",
    operation_id="send_otp_for_legal_buyer"
    )
    def send_otp_signup(self, request):
        real_buyer = self.get_real_buyer()

        if not real_buyer.is_complete():
            return Response({"detail": "اطلاعات فروشنده کامل نیست. لطفاً همه فیلدهای لازم را تکمیل کنید"},
                    status=status.HTTP_400_BAD_REQUEST)    

        self.check_throttles(request)
        otp_service = OTPService(request.user)
        otp_service.send()

        otp_token = str(uuid.uuid4())
        cache.set(f"otp_token:{otp_token}", request.user.id, timeout=300)
        otp_service.save_otp_token(otp_token)

        response_data = {"detail": "کد فعال‌سازی ارسال شد"}
        if settings.DEBUG:
            response_data["otp_token"] = otp_token
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request, pk=None):
        return self.send_otp_signup(request)

    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request, pk=None):
        return self.send_otp_signup(request) 
    
    @extend_schema(
    request=OpenApiExample(
        "درخواست تایید کد",
        value={
            "otp_code": "123456",
            "otp_token": "550e8400-e29b-41d4-a716-446655440000"
        },
        request_only=True,
    ),
    responses={
        200: OpenApiResponse(
            description="کد با موفقیت تایید شد",
            examples=[
                OpenApiExample(
                    "تایید موفق",
                    value={"message": "ثبت‌ نام شما با موفقیت تأیید شد"}
                )
            ],
        ),
        400: OpenApiResponse(
            description="خطا در ورودی",
            examples=[
                OpenApiExample("توکن ارسال نشده", value={"detail": "توکن ارسال نشده"}),
                OpenApiExample("توکن نامعتبر", value={"detail": "توکن نامعتبر است"}),
                OpenApiExample("کد اشتباه", value={"detail": "کد تأیید اشتباه است"}),
            ],
        ),
        403: OpenApiResponse(
            description="عدم دسترسی به فروشنده",
            examples=[
                OpenApiExample("دسترسی غیرمجاز", value={"detail": "دسترسی غیرمجاز"})
            ]
        )
    },
    description="تأیید کد ارسال شده برای فروشنده حقوقی با استفاده از توکن",
    operation_id="verify_otp_for_real_buyer"
    )

    @action(detail=False, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request, pk=None):
        real_buyer = self.get_real_buyer()

        if not real_buyer:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if real_buyer.buyer.user != user:
            return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)

        otp_code = request.data.get("otp_code")
        otp_token = request.data.get("otp_token")

        if not otp_code:
            return Response({"detail": "کد تأیید ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_token:
            return Response({"detail": "توکن ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = cache.get(f"otp_token:{otp_token}")
        if user_id != user.id:
            return Response({"detail": "توکن نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

        otp_service = OTPService(user)
        if otp_service.is_otp_valid(otp_code):
            if not real_buyer.is_complete():
                return Response({"detail": "اطلاعات فروشنده ناقص است. ثبت‌نام قابل تأیید نیست"},
                    status=status.HTTP_400_BAD_REQUEST)

            real_buyer.is_verified = True
            real_buyer.save()
            cache.delete(f"otp_token:{otp_token}")
            return Response({"message": "ثبت‌ نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)

        return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)   

