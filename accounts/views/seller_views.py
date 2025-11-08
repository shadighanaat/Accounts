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

from ..models import CustomUser, LegalSeller, RealSeller, SellerType
from ..serializers.seller_serializers import (
    SendOTPSellerSerializer,
    VerifyOTPSellerSerializer,
    AcceptTermsSerializer,
    LegalSellerSerializer,
    BusinessAndLegalInformationSerializer,
    ContactInfoLegalSerializer,
    Finalapprovaloflegalseller,
    RealSellerSerializer,
    RealPersonBusinessInfoSerializer,
    ContactInfoRealSerializer,
    FinalapprovalofrealsellerSerializer,
)
from ..utils import OTPService
from ..throttles import OTPThrottle
from ..permissions import IsOwnerUser


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
class AcceptTermsViewSet(ViewSet):
    def create(self, request):
        serializer = AcceptTermsSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "شرایط همکاری پذیرفته شد"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LegalSellerViewSet(ModelViewSet):
    serializer_class = LegalSellerSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication] 

    def get_queryset(self):
        return LegalSeller.objects.filter(user=self.request.user).select_related("user").prefetch_related('supplier_types')

    def perform_update(self, serializer):
        serializer.save()    

    @extend_schema(
        request=LegalSellerSerializer,
        responses={
            201: OpenApiResponse(
                description="مرحله احرازهویت با موفقیت ذخیره شد",
                examples=[
                    OpenApiExample(
                        "ثبت‌نام موفق",
                        value={"id": 1, "message": "مرحله احرازهویت با موفقیت ذخیره شد"}
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
        description="ثبت‌نام فروشنده حقوقی در صورت پذیرش شرایط همکاری"
    )
    def create(self, request, *args, **kwargs):
        accepted_terms = request.data.get("accepted_terms", False)
        if not accepted_terms:
            return Response(
                {"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supplier_types_data = serializer.validated_data.pop("supplier_types", [])

        if LegalSeller.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "شما قبلا ثبت‌نام کرده‌اید"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        legal_seller = LegalSeller.objects.create(
            **serializer.validated_data,
            user=request.user
        )

        legal_seller.supplier_types.set(supplier_types_data)

        return Response(
            {"id": legal_seller.id, "message": ".مرحله احرازهویت با موفقیت ذخیره شد"},
            status=status.HTTP_201_CREATED
        )
        
    @extend_schema(
        request=LegalSellerSerializer,
        responses={
            200: OpenApiResponse(
                description="اطلاعات احراز هویت با موفقیت ویرایش شد",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق",
                        value={"message": ".اطلاعات احراز هویت ویرایش شد"}
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
        description="ویرایش اطلاعات احراز هویت فروشنده حقوقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)


class LegalBusinessInfoViewSet(ModelViewSet):
    serializer_class = BusinessAndLegalInformationSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter]
    search_fields = ['industryselection__name'] 

    def get_queryset(self):
        return LegalSeller.objects.filter(user=self.request.user).select_related("user").prefetch_related("industryselection")

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = (
            LegalSeller.objects
            .select_related("user") 
            .prefetch_related("industryselection")  
            .filter(user=self.request.user)
            .first()
        )
        return self._object
    

    @extend_schema(
        request=BusinessAndLegalInformationSerializer,
        responses={
            201: OpenApiResponse(
                description="اطلاعات کسب و کار با موفقیت ثبت شد",
                examples=[OpenApiExample("ثبت موفق", value={"detail": "اطلاعات کسب و کار ثبت شد"})]
            ),
            400: OpenApiResponse(
                description="خطا در ثبت اطلاعات",
                examples=[OpenApiExample("خطا", value={"detail": "اطلاعات ارسال شده معتبر نیست"})]
            )
        },
        description="ثبت یا بروزرسانی اطلاعات کسب و کار حقوقی کاربر"
    )
    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"detail": "اطلاعات کسب و کار ثبت شد"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=BusinessAndLegalInformationSerializer,
        responses={
            200: OpenApiResponse(
                description="اطلاعات کسب و کار با موفقیت ویرایش شد",
                examples=[OpenApiExample("ویرایش موفق", value={"detail": "اطلاعات کسب و کار ویرایش شد"})]
            ),
            400: OpenApiResponse(
                description="خطا در ویرایش اطلاعات",
                examples=[OpenApiExample("خطا", value={"detail": "اطلاعات ارسال شده معتبر نیست"})]
            ),
            404: OpenApiResponse(
                description="رکورد یافت نشد",
                examples=[OpenApiExample("یافت نشد", value={"detail": "اطلاعات کسب و کار یافت نشد"})]
            )
        },
        description="ویرایش اطلاعات کسب و کار حقوقی کاربر"
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({"detail": "اطلاعات کسب و کار یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer( instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"detail": "اطلاعات کسب و کار ویرایش شد"}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({"detail": "اطلاعاتی ثبت نشده"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContactInfoLegalViewSet(ModelViewSet):
    serializer_class = ContactInfoLegalSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return LegalSeller.objects.filter(user=self.request.user).select_related("user", "province", "city")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save() 

    @extend_schema(
        request=ContactInfoLegalSerializer,
        responses={
            201: OpenApiResponse(
                description="مرحله اطلاعات تماس با موفقیت ذخیره شد",
                examples=[
                    OpenApiExample(
                        "ثبت اطلاعات تماس موفق",
                        value={"id": 1, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"phone": ["این فیلد الزامی است"]}
                    ),
                ],
            ),
        },
        description="ثبت اطلاعات تماس فروشنده حقوقی"
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"id": serializer.instance.id, "message": "مرحله اطلاعات تماس با موفقیت ذخیره شد"},
            status=status.HTTP_201_CREATED
            )
            
    @extend_schema(
        request=ContactInfoLegalSerializer,
        responses={
            200: OpenApiResponse(
                description="مرحله اطلاعات تماس با موفقیت ویرایش شد",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق اطلاعات تماس",
                        value={"message": ".مرحله اطلاعات تماس ویرایش شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"phone": ["شماره تلفن نامعتبر است"]}
                    ),
                ],
            ),
        },
        description="ویرایش اطلاعات تماس فروشنده حقوقی"
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".مرحله اطلاعات تماس ویرایش شد"}, status=status.HTTP_200_OK)


class LegalSellerOTPVerificationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerUser]
    serializer_class = Finalapprovaloflegalseller 
    authentication_classes = [JWTAuthentication]
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    def get_queryset(self):
        return LegalSeller.objects.filter(user=self.request.user).select_related("user", "province", "city")

    def get_legal_seller(self):
        try:
            return LegalSeller.objects.select_related("user", "province", "city").get(user=self.request.user)
        except LegalSeller.DoesNotExist:
            return None     

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="اطلاعات فروشنده حقوقی با موفقیت دریافت شد",
                examples=[
                    OpenApiExample(
                        "دریافت موفق",
                        value={"id": 1, "name": "نام فروشنده", "is_verified": False}
                    )
                ],
            )
        },
        description="دریافت اطلاعات فروشنده حقوقی"
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "links": {
            "send_otp_signup": reverse("finalapproval-legal-seller-send-otp", request=request),
            "resend_otp": reverse("finalapproval-legal-seller-resend-otp", request=request),
            "verify_otp": reverse("finalapproval-legal-seller-verify-otp", request=request),
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
            description="عدم دسترسی به فروشنده",
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
    operation_id="send_otp_for_legal_seller"
    )
    def send_otp_signup(self, request):
        legal_seller = self.get_legal_seller()
        if not legal_seller:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if not legal_seller.is_complete():
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
    operation_id="verify_otp_for_legal_seller"
    )

    @action(detail=False, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request, pk=None):
        user = request.user
        legal_seller = self.get_legal_seller()

        if not legal_seller:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if legal_seller.user != user:
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
            if not legal_seller.is_complete():
                return Response({"detail": "اطلاعات فروشنده ناقص است. ثبت‌نام قابل تأیید نیست"},
                    status=status.HTTP_400_BAD_REQUEST)

            legal_seller.is_verified = True
            legal_seller.save()
            cache.delete(f"otp_token:{otp_token}")
            return Response({"message": "ثبت‌ نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)

        return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)    


class RealSellerViewSet(ModelViewSet):
    serializer_class = RealSellerSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return RealSeller.objects.filter(user=self.request.user).select_related("user").prefetch_related('supplier_types')

    def perform_update(self, serializer):
        serializer.save()
    
    @extend_schema(
        request=RealSellerSerializer,
        responses={
            201: OpenApiResponse(
                description="مرحله اطلاعات احراز هویت حقیقی با موفقیت ذخیره شد",
                examples=[
                    OpenApiExample(
                        "ثبت موفق اطلاعات هویتی",
                        value={"id": 1, "message": ".مرحله اطلاعات احراز هویت حقیقی با موفقیت ذخیره شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"national_id": ["این فیلد الزامی است"]}
                    ),
                ],
            ),
        },
        description="ثبت اطلاعات هویتی فروشنده حقیقی"
    )
    def create(self, request, *args, **kwargs):
        accepted_terms = request.data.get("accepted_terms", False)
        if not accepted_terms:
            return Response(
            {"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"},
            status=status.HTTP_400_BAD_REQUEST
        )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supplier_types_data = serializer.validated_data.pop("supplier_types", [])

        if RealSeller.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "شما قبلا ثبت‌نام کرده‌اید"},
                status=status.HTTP_400_BAD_REQUEST
            )

        real_seller = RealSeller.objects.create(
            **serializer.validated_data,
            user=request.user
        )

        real_seller.supplier_types.set(supplier_types_instances)

        return Response(
        {"id": real_seller.id, "message": ".مرحله احرازهویت با موفقیت ذخیره شد"},
        status=status.HTTP_201_CREATED
        )

    
    @extend_schema(
        request=RealSellerSerializer,
        responses={
            200: OpenApiResponse(
                description="مرحله اطلاعات احراز هویت حقیقی ویرایش شد",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق اطلاعات هویتی",
                        value={"message": ".مرحله اطلاعات احراز هویت حقیقی ویرایش شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"national_id": ["شناسه ملی نامعتبر است"]}
                    ),
                ],
            ),
        },
        description="ویرایش اطلاعات هویتی فروشنده حقیقی"
    )    

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)


class RealPersonBusinessInfoViewSet(ModelViewSet):
    serializer_class = RealPersonBusinessInfoSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter]
    search_fields = ['industryselection__name']

    def get_queryset(self):
        return RealSeller.objects.filter(user=self.request.user).select_related("user").prefetch_related("industryselection")

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = (
            RealSeller.objects
            .select_related("user") 
            .prefetch_related("industryselection")  
            .filter(user=self.request.user)
            .first()
        )
        return self._object     

    @extend_schema(
        request=RealPersonBusinessInfoSerializer,
        responses={
            201: OpenApiResponse(
                description="مرحله اطلاعات کسب و کار با موفقیت ذخیره شد",
                examples=[
                    OpenApiExample(
                        "ثبت موفق اطلاعات کسب و کار",
                        value={"id": 1, "message": ".مرحله اطلاعات کسب و کار با موفقیت ذخیره شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"field1": ["این فیلد الزامی است"]}
                    )
                ],
            ),
        },
        description="ثبت اطلاعات کسب و کار شخص حقیقی"
    )    
    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"detail": "اطلاعات کسب و کار ثبت شد"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=RealPersonBusinessInfoSerializer,
        responses={
            200: OpenApiResponse(
                description="مرحله اطلاعات کسب و کار با موفقیت ویرایش شد",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق اطلاعات کسب و کار",
                        value={"message": ".اطلاعات اطلاعات کسب و کار ویرایش شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"field1": ["مقدار نامعتبر است"]}
                    )
                ],
            ),
        },
        description="ویرایش اطلاعات کسب و کار شخص حقیقی"
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({"detail": "اطلاعات کسب و کار یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer( instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"detail": "اطلاعات کسب و کار ویرایش شد"}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({"detail": "اطلاعاتی ثبت نشده"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContactInfoRealViewSet(ModelViewSet):
    serializer_class = ContactInfoRealSerializer
    permission_classes = [IsAuthenticated, IsOwnerUser]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return RealSeller.objects.filter(user=self.request.user).select_related("user", "province", "city")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @extend_schema(
        request=ContactInfoRealSerializer,
        responses={
            201: OpenApiResponse(
                description="مرحله اطلاعات تماس با موفقیت ذخیره شد",
                examples=[
                    OpenApiExample(
                        "ثبت موفق اطلاعات تماس",
                        value={"id": 1, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"phone": ["این فیلد الزامی است"], "email": ["ایمیل نامعتبر است"]}
                    )
                ],
            ),
        },
        description="ثبت اطلاعات تماس شخص حقیقی"
    )    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"id": serializer.instance.id, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=ContactInfoRealSerializer,
        responses={
            200: OpenApiResponse(
                description="مرحله اطلاعات تماس با موفقیت ویرایش شد",
                examples=[
                    OpenApiExample(
                        "ویرایش موفق اطلاعات تماس",
                        value={"message": ".اطلاعات تماس ویرایش شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی ورودی",
                examples=[
                    OpenApiExample(
                        "خطای اعتبارسنجی",
                        value={"phone": ["شماره تلفن نامعتبر است"]}
                    )
                ],
            ),
        },
        description="ویرایش اطلاعات تماس شخص حقیقی"
    )    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": ".اطلاعات تماس ویرایش شد"}, status=status.HTTP_200_OK)
    

class RealSellerOTPVerificationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FinalapprovalofrealsellerSerializer
    authentication_classes = [JWTAuthentication]
    throttle_classes = [OTPThrottle]
    throttle_scope = 'send_otp'

    def get_queryset(self):
        return RealSeller.objects.filter(user=self.request.user).select_related("user", "province", "city")
    
    def get_real_seller(self):
        return get_object_or_404(
        RealSeller.objects.select_related("province", "city"),
        user=self.request.user
    )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="اطلاعات فروشنده حقیقی با موفقیت دریافت شد",
                examples=[
                    OpenApiExample(
                        "دریافت موفق",
                        value={"id": 1, "name": "نام فروشنده", "is_verified": False}
                    )
                ],
            )
        },
        description="دریافت اطلاعات فروشنده حقیقی"
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "links": {
            "send_otp_signup": reverse("finalapproval-real-seller-send-otp", request=request),
            "resend_otp": reverse("finalapproval-real-seller-resend-otp", request=request),
            "verify_otp": reverse("finalapproval-real-seller-verify-otp", request=request),
        },
            "message": "اطلاعات با موفقیت دریافت شد"
        })

    @extend_schema(
        request=None,
        responses={
            201: OpenApiResponse(
                description="کد ثبت‌ نام ارسال شد",
                examples=[
                    OpenApiExample(
                        "ارسال موفق",
                        value={
                            "detail": "سیراف: کد ثبت‌ نام ارسال شد.",
                            "otp_token": "550e8400-e29b-41d4-a716-446655440000"
                        }
                    )
                ],
            ),
            200: OpenApiResponse(
                description="ثبت‌ نام با موفقیت تایید شد",
                examples=[
                    OpenApiExample(
                        "تایید موفق",
                        value={"message": "ثبت‌ نام شما با موفقیت تأیید شد"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="خطا در ارسال یا تایید",
                examples=[
                    OpenApiExample(
                        "توکن ارسال نشده",
                        value={"detail": "توکن ارسال نشده"}
                    ),
                    OpenApiExample(
                        "توکن نامعتبر",
                        value={"detail": "توکن نامعتبر است"}
                    ),
                    OpenApiExample(
                        "کد تایید اشتباه",
                        value={"detail": "کد تأیید اشتباه است"}
                    )
                ],
            ),
            429: OpenApiResponse(
                description="محدودیت ارسال بیش از حد کد فعال است",
                examples=[
                    OpenApiExample(
                        "محدودیت ارسال کد",
                        value={"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}
                    )
                ],
            ),
        },
        description="ارسال و تایید کد برای ثبت‌ نام فروشنده حقیقی"
    )
    def send_otp_signup(self, request):
        real_seller = self.get_real_seller()
        if not real_seller:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if not real_seller.is_complete():
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
    operation_id="verify_otp_for_legal_seller"
    )

    @action(detail=False, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request, pk=None):
        user = request.user
        real_seller = self.get_real_seller()

        if not real_seller:
            return Response({"detail": "فروشنده یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if real_seller.user != user:
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
            if not real_seller.is_complete():
                return Response({"detail": "اطلاعات فروشنده ناقص است. ثبت‌نام قابل تأیید نیست"},
                    status=status.HTTP_400_BAD_REQUEST)

            real_seller.is_verified = True
            real_seller.save()
            cache.delete(f"otp_token:{otp_token}")
            return Response({"message": "ثبت‌ نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)

        return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)    
