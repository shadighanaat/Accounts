# import random
# import uuid

# from django.core.cache import cache
# from django.contrib.auth.models import User
# from django.contrib.auth import get_user_model ,login
# from rest_framework.viewsets import ModelViewSet, ViewSet
# from django.shortcuts import render, get_object_or_404
# from django.core.mail import send_mail
# from django.utils import timezone

# from drf_spectacular.utils import OpenApiResponse, OpenApiExample
# from rest_framework.exceptions import Throttled

# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.response import Response
# from rest_framework import status, generics
# from rest_framework.views import APIView
# from rest_framework.throttling import ScopedRateThrottle
# from .serializers import (LoginWithPasswordSerializer, 
#                           SendOTPSerializer, 
#                           VerifyOTPSerializer, 
#                           LoginSerializer,
#                           ResetPasswordSerializer,
#                           VerifyOTPEmailSerializer,
#                           RequestPasswordResetSerializer,
#                           AcceptTermsSerializer,
#                           LegalSellerSerializer,
#                           BusinessAndLegalInformationSerializer,
#                           ContactInfoLegalSerializer,
#                           Finalapprovaloflegalseller,
#                           RealSellerSerializer,
#                           RealPersonBusinessInfoSerializer,
#                           ContactInfoRealSerializer,
#                           FinalapprovalofrealsellerSerializer,
#                           BuyerRegisterOrLoginSerializer,
#                           BuyerLegalSerializer,
#                           BuyerLegalBusinessInfoSerializer,
#                           BuyerLegalContactInfoSerializer,
#                           FinalApprovalOfBuyerSerializer,
#                           BuyerRealSerializer,
#                           BuyerRealBusinessInfoSerializer,
# )

# from .models import CustomUser, LegalSeller, RealSeller, SellerType, BuyerLegal
# from .utils import OTPService
# from datetime import timedelta
# from drf_spectacular.utils import extend_schema
# from rest_framework.decorators import action
# from django.conf import settings
# from .throttles import OTPThrottle
# import time

# User = get_user_model()
# def generate_jwt_tokens(user, remember_me=False):
#     refresh = RefreshToken.for_user(user)
#     if remember_me:
#         refresh.set_exp(lifetime=timedelta(days=5))
#         refresh.access_token.set_exp(lifetime=timedelta(days=5))
#     else:
#         refresh.set_exp(lifetime=timedelta(days=1))
#         refresh.access_token.set_exp(lifetime=timedelta(minutes=15))
#     return str(refresh), str(refresh.access_token)


# class AuthViewSet(ViewSet):
#     throttle_classes = [OTPThrottle]
#     throttle_scope = 'send_otp'

#     @extend_schema(
#     request=SendOTPSerializer,
#     responses={
#         201: OpenApiResponse(
#             description="کدارسال شد و توکن بازگردانده شد",
#             examples=[
#                 OpenApiExample(
#                     "پاسخ موفق",
#                     value={
#                         "detail": "سیراف : کد ورود",
#                         "otp_token": "uuid-توکن-مثال"
#                     }
#                 )
#             ]
#         ),
#         400: OpenApiResponse(
#             description="خطا در ارسال داده‌ها",
#             examples=[
#                 OpenApiExample(
#                     "خطا در شماره موبایل",
#                     value={"phone_number": ["فرمت شماره موبایل صحیح نیست"]}
#                 )
#             ]
#         )
#     },
#     description="ارسال کد ورود برای شماره موبایل"
#     )
#     def send_otp_login(self, request):
#         throttle = self.throttle_classes[0]() 
#         if not throttle.allow_request(request, self):
#             cache_key = throttle.get_cache_key(request)
#             data = cache.get(cache_key, {})
#             blocked_until = data.get('blocked_until')
#             if blocked_until:
#                 remaining = int(blocked_until - time.time())
#                 raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
#             else:
#                 raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")
     
#         serializer = SendOTPSerializer(data=request.data)
#         if serializer.is_valid():
#             phone_number = serializer.validated_data['phone_number']
#             remember_me = serializer.validated_data.get('remember_me', False)

#             user, created = CustomUser.objects.get_or_create(phone_number=phone_number)
#             if created:
#                 user.is_verified = False
#                 user.save()

#             otp_service = OTPService(user)
#             otp_code = otp_service.send()

#             otp_token = str(uuid.uuid4())
#             timeout = 60 * 60 * 24 * 5 if remember_me else settings.OTP_RESET_TIMEOUT
#             cache.set(otp_token, user.id, timeout=timeout)

#             response_data = {"detail": "کد ورود به موبایل شما ارسال شد"}

#             if settings.DEBUG==True:
#                 response_data["otp_token"] = otp_token

#                 return Response(response_data, status=status.HTTP_201_CREATED)
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

#         @action(detail=False, methods=['post'], url_path='send-otp')
#         def send_otp(self, request):
#             return self._send_otp_to_user(request)

#         @action(detail=False, methods=['post'], url_path='resend-otp')
#         def resend_otp(self, request):
#             return self._send_otp_to_user(request)       
   
#     @extend_schema(
#     request=VerifyOTPSerializer,
#     responses={
#         200: OpenApiResponse(
#             description="کد تایید با موفقیت انجام شد",
#             examples=[
#                 OpenApiExample(
#                     "تایید موفق",
#                     value={"detail": ".کد تایید با موفقیت انجام شد"}
#                 )
#             ]
#         ),
#         400: OpenApiResponse(
#             description="خطا در تایید کد",
#             examples=[
#                 OpenApiExample(
#                     "توکن منقضی شده",
#                     value={"detail": "توکن منقضی یا نامعتبر است"}
#                 ),
#                 OpenApiExample(
#                     "کد اشتباه",
#                     value={"detail": "کد وارد شده اشتباه است"}
#                 )
#             ]
#         )
#     },
#     description="تأیید کد ورود ارسال‌شده برای شماره موبایل"
#     )
#     @action(detail=False, methods=['post'], url_path='verify-otp')
#     def verify_otp_login(self, request):
#         serializer = VerifyOTPSerializer(data=request.data)
#         if serializer.is_valid():
#             otp_token = serializer.validated_data['otp_token']
#             otp_code = serializer.validated_data['otp_code']
#             user_id = cache.get(otp_token)

#             if not user_id:
#                 return Response({'detail': 'توکن منقضی یا نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)

#             user = get_object_or_404(CustomUser, id=user_id)

#             otp_service = OTPService(user)
#             if not otp_service.is_otp_valid(otp_code):
#                 return Response({'detail': 'کد وارد شده اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)
     
#             user.is_verified = True
#             user.save()

#             return Response({'detail': '.کد تایید با موفقیت انجام شد'}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=400)
        
#     @extend_schema(
#     request=LoginSerializer,
#     responses={
#         200: OpenApiResponse(
#             description="ورود موفق با بازگردانی توکن‌های JWT",
#             examples=[
#                 OpenApiExample(
#                     "ورود موفق",
#                     value={
#                         "refresh": "token-refresh-مثال",
#                         "access": "token-access-مثال",
#                         "detail": "ورود با موفقیت انجام شد"
#                     }
#                 )
#             ]
#         ),
#         400: OpenApiResponse(
#             description="خطا در فرآیند ورود",
#             examples=[
#                 OpenApiExample(
#                     "توکن نامعتبر",
#                     value={"detail": "مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید"}
#                 )
#             ]
#         )
#     },
#     description="ورود با کد پس از تأیید موفق"
#     )
#     @action(detail=False, methods=['post'], url_path='login')
#     def login(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             otp_token = serializer.validated_data['otp_token'] 
#             remember_me = serializer.validated_data.get('remember_me', False)

#             user_id = cache.get(otp_token)
#             if not user_id:
#                return Response({'detail': 'مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید'},
#                status=status.HTTP_400_BAD_REQUEST)

#             user = get_object_or_404(CustomUser, id=user_id)
#             refresh_token, access_token = generate_jwt_tokens(user, remember_me)
#             cache.delete(otp_token) 

#             return Response({
#                 'access_token': access_token,
#                 'refresh_token': refresh_token,
#                 'detail': '!ورود با موفقیت انجام شد'
#             })
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     @extend_schema(
#         request=LoginWithPasswordSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="ورود موفق با بازگردانی توکن‌ها",
#                 examples=[
#                     OpenApiExample(
#                         "ورود موفق",
#                         value={
#                             "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#                             "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#                             "message": "!ورود با موفقیت انجام شد"
#                         }
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطا در فرآیند ورود",
#                 examples=[
#                     OpenApiExample(
#                         "نام کاربری یا رمز عبور اشتباه",
#                         value={"non_field_errors": ["نام کاربری یا رمز عبور اشتباه است"]}
#                     )
#                 ]
#             )
#         },
#         description="ورود با نام کاربری و رمز عبور. در صورت موفقیت، توکن‌ها بازگردانده می‌شوند"
#     )
#     @action(detail=False, methods=['post'], url_path='login-with-password')
#     def login_with_password(self, request):
#         serializer = LoginWithPasswordSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             remember_me = serializer.validated_data.get('remember_me', False)

#             refresh_token, access_token = generate_jwt_tokens(user, remember_me)   

#             if RealSeller.objects.filter(user=user).exists():
#                 seller_type = 'real'
#             elif LegalSeller.objects.filter(user=user).exists():
#                 seller_type = 'legal'
#             else:
#                 seller_type = 'unknown'

#             return Response({
#             'access_token': access_token,
#             'refresh_token': refresh_token,
#             'user_id': user.id,
#             'username': user.username,
#             'seller_type': seller_type,
#             'message': '!ورود با موفقیت انجام شد'
#              }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @extend_schema(
#     request=RequestPasswordResetSerializer,
#     responses={
#         201: OpenApiResponse(
#             description="درخواست موفق برای بازیابی رمز عبور. کد تأیید ارسال شد",
#             examples=[
#                 OpenApiExample(
#                     "ارسال موفق ایمیل بازیابی",
#                     value={
#                         "detail": "کد به ایمیل شما ارسال شد",
#                         "otp_token": "uuid-مثال",
#                         "otp_code": "123456"
#                     }
#                 )
#             ]
#         ),
#         404: OpenApiResponse(
#             description="کاربر با این ایمیل یافت نشد",
#             examples=[
#                 OpenApiExample(
#                     "ایمیل نامعتبر",
#                     value={"detail": "کاربری با این ایمیل پیدا نشد"}
#                 )
#             ]
#         ),
#         400: OpenApiResponse(
#             description="درخواست نامعتبر",
#             examples=[
#                 OpenApiExample(
#                     "فرم نامعتبر",
#                     value={"detail": ["این فیلد الزامی است"]}
#                 )
#             ]
#         ),
#     },
#     description="درخواست بازیابی رمز عبور با ایمیل. اگر ایمیل معتبر باشد، کد تأیید به آن ارسال می‌شود"
#     )
#     def _send_password_reset_otp(self, request):
#         self.check_throttles(request) 
#         serializer = RequestPasswordResetSerializer(data=request.data)
        
#         serializer.is_valid(raise_exception=True)

#         email = serializer.validated_data['email']
#         user = CustomUser.objects.filter(email=email).first()
#         if user:
#             otp_service = OTPService(user)
#             otp_code = otp_service.send()
#             otp_token = str(uuid.uuid4())
#             cache.set(otp_token, user.id, timeout=settings.OTP_RESET_TIMEOUT)

#             response_data = {"detail": "کد بازیابی به ایمیل شما ارسال شد"}
#             if settings.DEBUG:
#                 response_data["otp_token"] = otp_token
#                 response_data["otp_code"] = otp_code
#         else:
#             response_data = {"detail": "در صورت وجود حسابی با این ایمیل، کد بازیابی ارسال شد"}

#         return Response(response_data, status=status.HTTP_201_CREATED)

#     @action(detail=False, methods=['post'], url_path='request-password-reset')
#     def request_password_reset(self, request):
#         return self._send_password_reset_otp(request)

#     @action(detail=False, methods=['post'], url_path='resend-password-reset')
#     def resend_password_reset(self, request):
#         return self._send_password_reset_otp(request)

#     @extend_schema(
#     request=VerifyOTPEmailSerializer,
#     responses={
#         200: OpenApiResponse(
#             description="کد تأیید ایمیل با موفقیت تأیید شد",
#             examples=[
#                 OpenApiExample(
#                     "تأیید موفق",
#                     value={"detail": "کد تأیید صحیح است"}
#                 )
#             ]
#         ),
#         400: OpenApiResponse(
#             description="خطا در تأیید کد",
#             examples=[
#                 OpenApiExample(
#                     "کد نادرست یا منقضی شده",
#                     value={"error": "کد وارد شده اشتباه است"}
#                 ),
#                 OpenApiExample(
#                     "خطای توکن",
#                     value={"error": "مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید"}
#                 ),
#                 OpenApiExample(
#                     "خطای اعتبارسنجی",
#                     value={
#                         "otp_token": ["این فیلد الزامی است"],
#                         "otp_code": ["این فیلد الزامی است"]
#                     }
#                 ),
#             ]
#         )
#     },
#     description="تأیید آدرس ایمیل با کد ارسال‌شده به ایمیل کاربر. در صورت صحت کد، پاسخ موفق بازگردانده می‌شود"
#     )
#     @action(detail=False, methods=['post'], url_path='verify-otp-email')
#     def verify_otp_email(self, request):
#         throttle = self.throttle_classes[0]() 
#         if not throttle.allow_request(request, self):
#             cache_key = throttle.get_cache_key(request)
#             data = cache.get(cache_key, {})
#             blocked_until = data.get('blocked_until')
#             if blocked_until:
#                 remaining = int(blocked_until - time.time())
#                 raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
#             else:
#                 raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")
#         serializer = VerifyOTPEmailSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         otp_token = serializer.validated_data['otp_token']
#         otp_code = serializer.validated_data['otp_code']
#         user_id = cache.get(otp_token)

#         if not user_id:
#             return Response({'error': 'مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید'},
#                             status=status.HTTP_400_BAD_REQUEST)

#         user = get_object_or_404(User, id=user_id)

#         otp_service = OTPService(user)
#         if not otp_service.is_otp_valid(otp_code):
#             return Response({'error': 'کد وارد شده اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)
        
#         user.is_verified = True
#         user.save()
#         cache.delete(otp_token)

#         return Response({'detail': 'کد تأیید صحیح است'}, 
#         status=status.HTTP_200_OK)

#     @extend_schema(
#     request=ResetPasswordSerializer,
#     responses={
#         200: OpenApiResponse(
#             description="بازنشانی موفق رمز عبور",
#             examples=[
#                 OpenApiExample(
#                     "بازنشانی موفق",
#                     value={"message": "رمز عبور با موفقیت تغییر یافت"}
#                 )
#             ]
#         ),
#         400: OpenApiResponse(
#             description="خطا در فرآیند بازنشانی رمز عبور",
#             examples=[
#                 OpenApiExample(
#                     "توکن نامعتبر یا منقضی شده",
#                     value={"error": "مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید"}
#                 ),
#                 OpenApiExample(
#                     "خطای اعتبارسنجی",
#                     value={
#                         "otp_token": ["این فیلد الزامی است"],
#                         "new_password": ["این فیلد الزامی است"]
#                     }
#                 )
#             ]
#         )
#     },
#     description="بازنشانی رمز عبور کاربر با استفاده از کد ارسال‌شده به ایمیل"
#     )
#     @action(detail=False, methods=["post"], url_path="reset-password")
#     def reset_password(self, request):
#         serializer = ResetPasswordSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         otp_token = serializer.validated_data['otp_token']
#         new_password = serializer.validated_data['new_password']
#         remember_me = serializer.validated_data.get('remember_me', False)

#         user_id = cache.get(otp_token)
#         if not user_id:
#             return Response({'error': 'مشکلی در فرآیند ورود رخ داده است. لطفاً مجدداً تلاش کنید'}, status=status.HTTP_400_BAD_REQUEST)

#         user = get_object_or_404(CustomUser, id=user_id)

#         if not user.is_active:
#             return Response({"error": "حساب کاربری غیرفعال است."}, status=status.HTTP_400_BAD_REQUEST)

#         cache.delete(otp_token)

#         user.set_password(new_password)
#         user.save()

#         refresh_token, access_token = generate_jwt_tokens(user, remember_me)

#         return Response({
#             "message": "رمز عبور با موفقیت تغییر یافت.",
#             "access_token": access_token,
#             "refresh_token": refresh_token
#         }, status=status.HTTP_200_OK)


# @extend_schema(
#     request=AcceptTermsSerializer,
#     responses={
#         200: OpenApiResponse(
#             description="شرایط همکاری پذیرفته شد",
#             examples=[
#                 OpenApiExample(
#                     "موفقیت در پذیرش شرایط",
#                     value={"message": "شرایط همکاری پذیرفته شد"}
#                 )
#             ],
#         ),
#         400: OpenApiResponse(
#             description="خطا در اعتبارسنجی ورودی",
#             examples=[
#                 OpenApiExample(
#                     "خطای اعتبارسنجی",
#                     value={"accepted": ["این فیلد الزامی است"]}
#                 )
#             ],
#         ),
#     },
#     description="پذیرش شرایط همکاری توسط کاربر"
# )

# class AcceptTermsViewSet(ViewSet):
#     def create(self, request):
#         serializer = AcceptTermsSerializer(data=request.data)
#         if serializer.is_valid():
#             return Response({"message": "شرایط همکاری پذیرفته شد"}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LegalSellerViewSet(ModelViewSet):
#     serializer_class = LegalSellerSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             return LegalSeller.objects.filter(user=self.request.user)
#         return LegalSeller.objects.none()

#     def perform_update(self, serializer):
#         serializer.save()    

#     @extend_schema(
#         request=LegalSellerSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="مرحله احرازهویت با موفقیت ذخیره شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت‌نام موفق",
#                         value={"id": 1, "message": "مرحله احرازهویت با موفقیت ذخیره شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در پذیرش شرایط همکاری یا اعتبارسنجی",
#                 examples=[
#                     OpenApiExample(
#                         "عدم پذیرش شرایط همکاری",
#                         value={"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"}
#                     ),
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"field_name": ["این فیلد الزامی است"]}
#                     ),
#                 ],
#             ),
#         },
#         description="ثبت‌نام فروشنده حقوقی در صورت پذیرش شرایط همکاری"
#     )
#     def create(self, request, *args, **kwargs):
#         accepted_terms = request.data.get("accepted_terms", False)
#         if not accepted_terms:
#             return Response(
#             {"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         supplier_types_data = serializer.validated_data.pop("supplier_types", [])

#         if request.user.is_authenticated and LegalSeller.objects.filter(user=request.user).exists():
#             return Response(
#             {"detail": "شما قبلا ثبت‌نام کرده‌اید"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#         legal_seller = LegalSeller.objects.create(
#         **serializer.validated_data,
#         user=request.user
#         )

#         supplier_type_instances = []
#         for item in supplier_types_data:
#             supplier_types_data = get_object_or_404(SellerType, code=item["code"])
#             supplier_type_instances.append(supplier_types_data)

#         legal_seller.supplier_types.set(supplier_type_instances)

#         return Response(
#         {"id": legal_seller.id, "message": ".مرحله احرازهویت با موفقیت ذخیره شد"},
#         status=status.HTTP_201_CREATED
#         )
        
#     @extend_schema(
#         request=LegalSellerSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="اطلاعات احراز هویت با موفقیت ویرایش شد",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق",
#                         value={"message": ".اطلاعات احراز هویت ویرایش شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"field_name": ["مقدار نامعتبر است"]}
#                     ),
#                 ],
#             ),
#         },
#         description="ویرایش اطلاعات احراز هویت فروشنده حقوقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)


# class LegalBusinessInfoViewSet(ModelViewSet):
#     serializer_class = BusinessAndLegalInformationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return LegalSeller.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.us)    

#     @extend_schema(
#         request=BusinessAndLegalInformationSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="اطلاعات کسب و کار با موفقیت ثبت شد",
#                 examples=[OpenApiExample("ثبت موفق", value={"detail": "اطلاعات کسب و کار ثبت شد"})]
#             ),
#             400: OpenApiResponse(
#                 description="خطا در ثبت اطلاعات",
#                 examples=[OpenApiExample("خطا", value={"detail": "اطلاعات ارسال شده معتبر نیست"})]
#             )
#         },
#         description="ثبت یا بروزرسانی اطلاعات کسب و کار حقوقی کاربر"
#     )
#     def create(self, request, *args, **kwargs):
#         user = request.user
#         instance = LegalSeller.objects.filter(user=user).first()
#         if instance:
#             serializer = self.get_serializer(instance, data=request.data, partial=True)
#         else:
#             serializer = self.get_serializer(data=request.data)

#         serializer.is_valid(raise_exception=True)
#         serializer.save(user=user)
#         return Response({"detail": "اطلاعات کسب و کار ثبت شد"}, status=status.HTTP_201_CREATED)

#     @extend_schema(
#         request=BusinessAndLegalInformationSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="اطلاعات کسب و کار با موفقیت ویرایش شد",
#                 examples=[OpenApiExample("ویرایش موفق", value={"detail": "اطلاعات کسب و کار ویرایش شد"})]
#             ),
#             400: OpenApiResponse(
#                 description="خطا در ویرایش اطلاعات",
#                 examples=[OpenApiExample("خطا", value={"detail": "اطلاعات ارسال شده معتبر نیست"})]
#             ),
#             404: OpenApiResponse(
#                 description="رکورد یافت نشد",
#                 examples=[OpenApiExample("یافت نشد", value={"detail": "اطلاعات کسب و کار یافت نشد"})]
#             )
#         },
#         description="ویرایش اطلاعات کسب و کار حقوقی کاربر"
#     )
#     def update(self, request, *args, **kwargs):
#         user = request.user
#         instance = LegalSeller.objects.filter(user=user).first()
#         if not instance:
#             return Response({"detail": "اطلاعات کسب و کار یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = self.get_serializer( instance, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(user=user)
#         return Response({"detail": "اطلاعات کسب و کار ویرایش شد"}, status=status.HTTP_200_OK)

#     def list(self, request, *args, **kwargs):
#         instance = LegalSeller.objects.filter(user=request.user).first()
#         if not instance:
#             return Response({"detail": "اطلاعاتی ثبت نشده"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = self.get_serializer(instance)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# class ContactInfoLegalViewSet(ModelViewSet):
#     serializer_class = ContactInfoLegalSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return LegalSeller.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def perform_update(self, serializer):
#         serializer.save() 

#     @extend_schema(
#         request=ContactInfoLegalSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="مرحله اطلاعات تماس با موفقیت ذخیره شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت اطلاعات تماس موفق",
#                         value={"id": 1, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"phone": ["این فیلد الزامی است"]}
#                     ),
#                 ],
#             ),
#         },
#         description="ثبت اطلاعات تماس فروشنده حقوقی"
#     )
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return Response(
#             {"id": serializer.instance.id, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"},
#             status=status.HTTP_201_CREATED
#             )
            
#     @extend_schema(
#         request=ContactInfoLegalSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="مرحله اطلاعات تماس با موفقیت ویرایش شد",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق اطلاعات تماس",
#                         value={"message": ".مرحله اطلاعات تماس ویرایش شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"phone": ["شماره تلفن نامعتبر است"]}
#                     ),
#                 ],
#             ),
#         },
#         description="ویرایش اطلاعات تماس فروشنده حقوقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".مرحله اطلاعات تماس ویرایش شد"}, status=status.HTTP_200_OK)


# class LegalSellerOTPVerificationViewSet(ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = Finalapprovaloflegalseller 
#     throttle_classes = [OTPThrottle]
#     throttle_scope = 'send_otp'

#     def get_queryset(self):
#         return LegalSeller.objects.filter(user=self.request.user)

#     @extend_schema(
#         responses={
#             200: OpenApiResponse(
#                 description="اطلاعات فروشنده حقوقی با موفقیت دریافت شد",
#                 examples=[
#                     OpenApiExample(
#                         "دریافت موفق",
#                         value={"id": 1, "name": "نام فروشنده", "is_verified": False}
#                     )
#                 ],
#             )
#         },
#         description="دریافت اطلاعات فروشنده حقوقی"
#     )
#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.user != request.user:
#             return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)
#         serializer = self.get_serializer(instance)
#         return Response({
#             "data": serializer.data,
#             "message": "اطلاعات با موفقیت دریافت شد"
#         })

#     @extend_schema(
#         request=None,
#         responses={
#             201: OpenApiResponse(
#                 description="کد ثبت‌ نام ارسال شد",
#                 examples=[
#                     OpenApiExample(
#                         "ارسال موفق",
#                         value={
#                             "detail": "سیراف: کد ثبت‌ نام ارسال شد.",
#                             "otp_token": "550e8400-e29b-41d4-a716-446655440000"
#                         }
#                     )
#                 ],
#             ),
#             200: OpenApiResponse(
#                 description="ثبت‌ نام با موفقیت تایید شد",
#                 examples=[
#                     OpenApiExample(
#                         "تایید موفق",
#                         value={"message": "ثبت‌ نام شما با موفقیت تأیید شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در ارسال یا تایید",
#                 examples=[
#                     OpenApiExample(
#                         "توکن ارسال نشده",
#                         value={"detail": "توکن ارسال نشده"}
#                     ),
#                     OpenApiExample(
#                         "توکن نامعتبر",
#                         value={"detail": "توکن نامعتبر است"}
#                     ),
#                     OpenApiExample(
#                         "کد تایید اشتباه",
#                         value={"detail": "کد تأیید اشتباه است"}
#                     )
#                 ],
#             ),
#             429: OpenApiResponse(
#                 description="محدودیت ارسال بیش از حد کد فعال است",
#                 examples=[
#                     OpenApiExample(
#                         "محدودیت ارسال کد",
#                         value={"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}
#                     )
#                 ],
#             ),
#         },
#         description="ارسال و تایید کد برای ثبت‌ نام فروشنده حقوقی"
#     )
#     @action(detail=True, methods=['post'], url_path='verify-otp_signup_seller', permission_classes=[])
#     def verify_otp_signup(self, request, pk=None):
#         throttle = self.throttle_classes[0]() 
#         if not throttle.allow_request(request, self):
#             cache_key = throttle.get_cache_key(request)
#             data = cache.get(cache_key, {})
#             blocked_until = data.get('blocked_until')
#         if blocked_until:
#             remaining = int(blocked_until - time.time())
#             raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
#         else:
#             raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")

#         user = request.user
#         legal_seller = self.get_object()

#         if legal_seller.user != user:
#             return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)

#         otp_code = request.data.get("otp_code")
#         otp_token = request.data.get("otp_token")

#         if not otp_code:
#             try:
#                 self.check_throttles(request)
#             except Exception:
#                 return Response({"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

#         otp_service = OTPService(user)
#         otp_service.send()

#         otp_token = str(uuid.uuid4())
#         cache.set(f"otp_token:{otp_token}", user.id, timeout=300)
#         otp_service.save_otp_token(otp_token)

#         response_data = {"detail": "کد ثبت نام به موبایل شما ارسال شد"}

#         if settings.DEBUG:
#             response_data["otp_token"] = otp_token

#         return Response(response_data, status=status.HTTP_201_CREATED)

#         if not otp_token:
#             return Response({"detail": "توکن ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

#         user_id = cache.get(f"otp_token:{otp_token}")
#         if user_id != user.id:
#             return Response({"detail": "توکن نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

#         otp_service = OTPService(user)
#         if otp_service.is_otp_valid(otp_code):
#             legal_seller.is_verified = True
#             legal_seller.save()
#             return Response({"message": "ثبت‌ نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)

#         return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)

        
# class RealSellerViewSet(ModelViewSet):
#     serializer_class = RealSellerSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             return RealSeller.objects.filter(user=self.request.user)
#         return RealSeller.objects.none()

#     def perform_update(self, serializer):
#         serializer.save()
    
#     @extend_schema(
#         request=RealSellerSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="مرحله اطلاعات احراز هویت حقیقی با موفقیت ذخیره شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت موفق اطلاعات هویتی",
#                         value={"id": 1, "message": ".مرحله اطلاعات احراز هویت حقیقی با موفقیت ذخیره شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"national_id": ["این فیلد الزامی است"]}
#                     ),
#                 ],
#             ),
#         },
#         description="ثبت اطلاعات هویتی فروشنده حقیقی"
#     )
#     def create(self, request, *args, **kwargs):
#         accepted_terms = request.data.get("accepted_terms", False)
#         if not accepted_terms:
#             return Response(
#             {"detail": ".برای شروع ثبت‌ نام باید ابتدا شرایط همکاری را بپذیرید"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         supplier_types_data = serializer.validated_data.pop("supplier_types", [])

#         real_seller = RealSeller.objects.create(
#             user=request.user if request.user.is_authenticated else None,
#             **serializer.validated_data
#         )

#         supplier_types_instances = []
#         for item in supplier_types_data:
#             supplier_types_data = get_object_or_404(SellerType, code=item["code"])
#             supplier_types_instances.append(supplier_types_data)

#         real_seller.supplier_types.set(supplier_types_instances)

#         return Response(
#         {"id": real_seller.id, "message": ".مرحله احرازهویت با موفقیت ذخیره شد"},
#         status=status.HTTP_201_CREATED
#         )

    
#     @extend_schema(
#         request=RealSellerSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="مرحله اطلاعات احراز هویت حقیقی ویرایش شد",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق اطلاعات هویتی",
#                         value={"message": ".مرحله اطلاعات احراز هویت حقیقی ویرایش شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"national_id": ["شناسه ملی نامعتبر است"]}
#                     ),
#                 ],
#             ),
#         },
#         description="ویرایش اطلاعات هویتی فروشنده حقیقی"
#     )    

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)


# class RealPersonBusinessInfoViewSet(ModelViewSet):
#     queryset = RealSeller.objects.all()
#     serializer_class = RealPersonBusinessInfoSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return RealSeller.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def perform_update(self, serializer):
#         serializer.save()

#     @extend_schema(
#         request=RealPersonBusinessInfoSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="مرحله اطلاعات کسب و کار با موفقیت ذخیره شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت موفق اطلاعات کسب و کار",
#                         value={"id": 1, "message": ".مرحله اطلاعات کسب و کار با موفقیت ذخیره شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"field1": ["این فیلد الزامی است"]}
#                     )
#                 ],
#             ),
#         },
#         description="ثبت اطلاعات کسب و کار شخص حقیقی"
#     )    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(
#             {"id": serializer.instance.id, "message": ".مرحله اطلاعات کسب و کار با موفقیت ذخیره شد"},
#             status=status.HTTP_201_CREATED,
#             headers=headers
#         )

#     @extend_schema(
#         request=RealPersonBusinessInfoSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="مرحله اطلاعات کسب و کار با موفقیت ویرایش شد",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق اطلاعات کسب و کار",
#                         value={"message": ".اطلاعات اطلاعات کسب و کار ویرایش شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"field1": ["مقدار نامعتبر است"]}
#                     )
#                 ],
#             ),
#         },
#         description="ویرایش اطلاعات کسب و کار شخص حقیقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات اطلاعات کسب و کار ویرایش شد"}, status=status.HTTP_200_OK)


# class ContactInfoRealViewSet(ModelViewSet):
#     queryset = RealSeller.objects.all()
#     serializer_class = ContactInfoRealSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return RealSeller.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def perform_update(self, serializer):
#         serializer.save()

#     @extend_schema(
#         request=ContactInfoRealSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="مرحله اطلاعات تماس با موفقیت ذخیره شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت موفق اطلاعات تماس",
#                         value={"id": 1, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"phone": ["این فیلد الزامی است"], "email": ["ایمیل نامعتبر است"]}
#                     )
#                 ],
#             ),
#         },
#         description="ثبت اطلاعات تماس شخص حقیقی"
#     )    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(
#             {"id": serializer.instance.id, "message": ".مرحله اطلاعات تماس با موفقیت ذخیره شد"},
#             status=status.HTTP_201_CREATED,
#             headers=headers
#         )

#     @extend_schema(
#         request=ContactInfoRealSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="مرحله اطلاعات تماس با موفقیت ویرایش شد",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق اطلاعات تماس",
#                         value={"message": ".اطلاعات تماس ویرایش شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی ورودی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"phone": ["شماره تلفن نامعتبر است"]}
#                     )
#                 ],
#             ),
#         },
#         description="ویرایش اطلاعات تماس شخص حقیقی"
#     )    
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات تماس ویرایش شد"}, status=status.HTTP_200_OK)
    

# class RealSellerOTPVerificationViewSet(ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = FinalapprovalofrealsellerSerializer
#     throttle_classes = [OTPThrottle]
#     throttle_scope = 'send_otp'

#     def get_queryset(self):
#         return RealSeller.objects.filter(user__user=self.request.user)

#     @extend_schema(
#         responses={
#             200: OpenApiResponse(
#                 description="اطلاعات فروشنده حقیقی با موفقیت دریافت شد",
#                 examples=[
#                     OpenApiExample(
#                         "دریافت موفق",
#                         value={"id": 1, "name": "نام فروشنده", "is_verified": False}
#                     )
#                 ],
#             )
#         },
#         description="دریافت اطلاعات فروشنده حقیقی"
#     )
#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.user.user != request.user:
#             return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)
#         serializer = self.get_serializer(instance)
#         return Response({"data": serializer.data})

#     @extend_schema(
#         request=None,
#         responses={
#             201: OpenApiResponse(
#                 description="کد ثبت‌ نام ارسال شد",
#                 examples=[
#                     OpenApiExample(
#                         "ارسال موفق",
#                         value={
#                             "detail": "سیراف: کد ثبت‌ نام ارسال شد.",
#                             "otp_token": "550e8400-e29b-41d4-a716-446655440000"
#                         }
#                     )
#                 ],
#             ),
#             200: OpenApiResponse(
#                 description="ثبت‌ نام با موفقیت تایید شد",
#                 examples=[
#                     OpenApiExample(
#                         "تایید موفق",
#                         value={"message": "ثبت‌ نام شما با موفقیت تأیید شد"}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در ارسال یا تایید",
#                 examples=[
#                     OpenApiExample(
#                         "توکن ارسال نشده",
#                         value={"detail": "توکن ارسال نشده"}
#                     ),
#                     OpenApiExample(
#                         "توکن نامعتبر",
#                         value={"detail": "توکن نامعتبر است"}
#                     ),
#                     OpenApiExample(
#                         "کد تایید اشتباه",
#                         value={"detail": "کد تأیید اشتباه است"}
#                     )
#                 ],
#             ),
#             429: OpenApiResponse(
#                 description="محدودیت ارسال بیش از حد کد فعال است",
#                 examples=[
#                     OpenApiExample(
#                         "محدودیت ارسال کد",
#                         value={"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}
#                     )
#                 ],
#             ),
#         },
#         description="ارسال و تایید کد برای ثبت‌ نام فروشنده حقیقی"
#     )
#     @action(detail=True, methods=['post'], url_path='verify-otp_signup_seller', permission_classes=[])
#     def verify_otp_signup(self, request, pk=None):
#         throttle = self.throttle_classes[0]() 
#         if not throttle.allow_request(request, self):
#             cache_key = throttle.get_cache_key(request)
#             data = cache.get(cache_key, {})
#             blocked_until = data.get('blocked_until')
#             if blocked_until:
#                 remaining = int(blocked_until - time.time())
#                 raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
#             else:
#                 raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")

#         user = request.user
#         real_seller = self.get_object()

#         if real_seller.user != user:
#             return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)

#         otp_code = request.data.get("otp_code")
#         otp_token = request.data.get("otp_token")

#         if not otp_code:
#             self.throttle_scope = 'send_otp'
#             try:
#                 self.check_throttles(request)
#             except Exception as e:
#                 return Response({"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

#             otp_service = OTPService(user)
#             otp_service.send()

#             otp_token = str(uuid.uuid4())
#             cache.set(f"otp_token:{otp_token}", user.id, timeout=300)
#             otp_service.save_otp_token(otp_token)

#             response_data = {"detail": "کد ثبت نام به موبایل شما ارسال شد"}
    
#             if settings.DEBUG:
#                 response_data["otp_token"] = otp_token

#             return Response(response_data, status=status.HTTP_201_CREATED)
            
#         if not otp_token:
#             return Response({"detail": "توکن ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

#         user_id = cache.get(f"otp_token:{otp_token}")
#         if user_id != user.id:
#             return Response({"detail": "توکن نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

#         otp_service = OTPService(user)
#         if otp_service.is_otp_valid(otp_code):
#             real_seller.is_verified = True
#             real_seller.save()
#             return Response({"message": "ثبت‌ نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)
 
#         return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)


# class BuyerRegisterOrLoginViewSet(ModelViewSet):
#     throttle_classes = [OTPThrottle]
#     throttle_scope = 'send_otp'

#     @extend_schema(
#         request=BuyerRegisterOrLoginSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="کاربر جدید ساخته شد و باید کد تایید دریافت شود",
#                 examples=[OpenApiExample(
#                     "Created",
#                     value={"detail": "کاربر جدید ساخته شد. لطفا کد تایید را دریافت کنید"}
#                 )]
#             ),
#             200: OpenApiResponse(
#                 description="کاربر قبلاً ثبت‌نام کرده است و باید کد تایید دریافت شود",
#                 examples=[OpenApiExample(
#                     "Already Registered",
#                     value={"detail": "کاربر قبلا ثبت‌نام کرده است. لطفا کد تایید را دریافت کنید"}
#                 )]
#             ),
#             400: OpenApiResponse(description="خطا در داده‌های ورودی")
#         },
#         description="ثبت‌نام یا ورود با شماره موبایل"
#     )
#     @action(detail=False, methods=['post'], url_path='register')
#     def register(self, request):
#         serializer = BuyerRegisterOrLoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         phone_number = serializer.validated_data['phone_number']
#         full_name = serializer.validated_data['full_name']

#         user, created = CustomUser.objects.get_or_create(phone_number=phone_number)

#         if created:
#             user.full_name = full_name
#             user.is_verified = False
#             user.save()
#             status_code = status.HTTP_201_CREATED
#             response_detail = "کاربر جدید ساخته شد. لطفا کد تایید را دریافت کنید"
#         else:
#             status_code = status.HTTP_200_OK
#             response_detail = "کاربر قبلا ثبت‌نام کرده است. لطفا کد تایید را دریافت کنید"

#         otp_service = OTPService(user)
#         otp_service.send()

#         otp_token = str(uuid.uuid4())
#         timeout = settings.OTP_RESET_TIMEOUT
#         cache.set(otp_token, user.id, timeout=timeout)

#         response_data = {"detail": response_detail}
#         if settings.DEBUG:
#             response_data["otp_token"] = otp_token

#         return Response(response_data, status=status_code)

#     def send_otp_to_user(self, request):
#         throttle = self.throttle_classes[0]()
#         if not throttle.allow_request(request, self):
#             cache_key = throttle.get_cache_key(request)
#             data = cache.get(cache_key, {})
#             blocked_until = data.get('blocked_until')
#             if blocked_until:
#                 remaining = int(blocked_until - time.time())
#                 raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
#             else:
#                 raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")

#         serializer = SendOTPSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         phone_number = serializer.validated_data['phone_number']
#         remember_me = serializer.validated_data.get('remember_me', False)

#         user, created = CustomUser.objects.get_or_create(phone_number=phone_number)
#         if created:
#             user.is_verified = False
#             user.save()

#         otp_service = OTPService(user)
#         otp_service.send()

#         otp_token = str(uuid.uuid4())
#         timeout = 60 * 60 * 24 * 5 if remember_me else settings.OTP_RESET_TIMEOUT
#         cache.set(otp_token, user.id, timeout=timeout)

#         response_data = {"detail": "کد ورود به موبایل شما ارسال شد"}

#         if settings.DEBUG:
#             response_data["otp_token"] = otp_token

#         return Response(response_data, status=status.HTTP_201_CREATED)

#     @action(detail=False, methods=['post'], url_path='send-otp')
#     def send_otp(self, request):
#         return self._send_otp_to_user(request)

#     @action(detail=False, methods=['post'], url_path='resend-otp')
#     def resend_otp(self, request):
#         return self._send_otp_to_user(request)

#     @extend_schema(
#         request=VerifyOTPSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="کد تایید با موفقیت انجام شد",
#                 examples=[
#                     OpenApiExample(
#                         "تایید موفق",
#                         value={"detail": "کد تایید با موفقیت انجام شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطا در تایید کد",
#                 examples=[
#                     OpenApiExample(
#                         "توکن منقضی شده",
#                         value={"detail": "توکن منقضی یا نامعتبر است"}
#                     ),
#                     OpenApiExample(
#                         "کد اشتباه",
#                         value={"detail": "کد وارد شده اشتباه است"}
#                     )
#                 ]
#             ),
#             429: OpenApiResponse(
#                 description="بیش از حد تلاش شده است",
#                 examples=[
#                     OpenApiExample(
#                         "بلاک موقت",
#                         value={"detail": "بیش از حد تلاش کردید. لطفاً ۵ دقیقه دیگر امتحان کنید."}
#                     )
#                 ]
#             ),
#         },
#         description="تأیید کد ورود ارسال‌شده برای شماره موبایل"
#     )
#     @action(detail=False, methods=['post'], url_path='verify-otp_signup_buyer')
#     def verify_otp(self, request):
#         serializer = VerifyOTPSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         otp_token = serializer.validated_data['otp_token']
#         otp_code = serializer.validated_data['otp_code']
#         user_id = cache.get(otp_token)

#         if not user_id:
#             return Response(
#                 {'detail': 'توکن منقضی یا نامعتبر است'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         user = get_object_or_404(CustomUser, id=user_id)
#         cache_key = f"otp-verify-attempts-{user.phone_number}"

#         blocked_until = cache.get(f"{cache_key}-blocked")
#         if blocked_until and time.time() < blocked_until:
#             return Response(
#                 {'detail': 'بیش از حد تلاش کردید. لطفاً 60 دقیقه دیگر امتحان کنید'},
#                 status=429
#             )

#         otp_service = OTPService(user)
#         if not otp_service.is_otp_valid(otp_code):
#             failures = cache.get(cache_key, 0) + 1
#             cache.set(cache_key, failures, timeout=60 * 10)

#             if failures >= 5:
#                 cache.set(f"{cache_key}-blocked", time.time() + 60 * 5, timeout=60 * 5)
#                 return Response(
#                     {'detail': 'بیش از حد تلاش کردید. لطفاً ۵ دقیقه دیگر امتحان کنید'},
#                     status=429
#                 )

#             return Response(
#                 {'detail': 'کد وارد شده اشتباه است'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         cache.delete(cache_key)
#         cache.delete(f"{cache_key}-blocked")

#         user.is_verified = True
#         user.save()

#         refresh = RefreshToken.for_user(user)
#         return Response({
#             'detail': 'کد تایید با موفقیت انجام شد',
#             'access': str(refresh.access_token),
#             'refresh': str(refresh),
#         }, status=status.HTTP_200_OK)


# class BuyerAcceptTermsViewSet(ViewSet):
#     permission_classes = [IsAuthenticated]
    
#     @extend_schema(
#         request=AcceptTermsSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="شرایط استفاده با موفقیت پذیرفته شد",
#                 examples=[
#                     OpenApiExample(
#                         "پذیرش موفق",
#                         value={"detail": "شرایط استفاده با موفقیت پذیرفته شد."}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در داده‌های ارسالی",
#                 examples=[
#                     OpenApiExample(
#                         "عدم پذیرش شرایط",
#                         value={
#                             "accepted_terms": [
#                                 "برای ادامه ثبت‌ نام باید شرایط همکاری را بپذیرید"
#                             ]
#                         }
#                     )
#                 ],
#             ),
#             404: OpenApiResponse(
#                 description="خریدار یافت نشد",
#                 examples=[
#                     OpenApiExample(
#                         "پروفایل خریدار موجود نیست",
#                         value={"detail": "خریدار مرتبط یافت نشد."}
#                     )
#                 ],
#             ),
#             401: OpenApiResponse(
#                 description="توکن ارسال نشده یا نامعتبر",
#                 examples=[
#                     OpenApiExample(
#                         "توکن ارسال نشده یا نامعتبر",
#                         value={"detail": "برای دسترسی به این بخش باید وارد حساب خود شوید."}
#              )
#                 ],
#             ),
#         }
#     )
#     def post(self, request):
#         serializer = AcceptTermsSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         buyer = Buyer.objects.get(user=request.user)
#         buyer.accepted_terms = True
#         buyer.save()

#         return Response({"detail": "شرایط استفاده با موفقیت پذیرفته شد"}, status=status.HTTP_200_OK)     



# class BuyerLegalViewSet(ModelViewSet):
#     serializer_class = BuyerLegalSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             buyer = get_object_or_404(Buyer, user=self.request.user)
#             return BuyerLegal.objects.filter(buyer=buyer)
#         return BuyerLegal.objects.none()

#     def perform_update(self, serializer):
#         serializer.save()

#     @extend_schema(
#         request=BuyerLegalSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="احراز هویت خریدار حقوقی با موفقیت انجام شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت‌نام موفق",
#                         value={"id": 1, "message": ".احراز هویت با موفقیت ثبت شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطا در پذیرش شرایط یا اعتبارسنجی",
#                 examples=[
#                     OpenApiExample(
#                         "شرایط همکاری پذیرفته نشده",
#                         value={"detail": ".برای ثبت‌ نام باید شرایط همکاری را بپذیرید"}
#                     ),
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"field": ["این فیلد الزامی است"]}
#                     )
#                 ]
#             )
#         },
#         description="ثبت‌ نام خریدار حقوقی در صورت پذیرش شرایط همکاری"
#     )
#     def create(self, request, *args, **kwargs):
#         accepted_terms = request.data.get("accepted_terms", False)
#         if not accepted_terms:
#             return Response(
#                 {"detail": ".برای ثبت‌ نام باید شرایط همکاری را بپذیرید"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         if BuyerLegal.objects.filter(buyer__user=request.user).exists():
#             return Response(
#                 {"detail": "شما قبلاً ثبت‌نام کرده‌اید"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         buyer = get_object_or_404(Buyer, user=request.user)

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         buyer_types_data = serializer.validated_data.pop("buyer_types", [])

#         buyer_legal = BuyerLegal.objects.create(
#             buyer=buyer,
#             **serializer.validated_data
#         )

#         buyer_type_instances = []
#         for item in buyer_types_data:
#             buyer_type = get_object_or_404(BuyerType, code=item["code"])
#             buyer_type_instances.append(buyer_type)

#         buyer_legal.buyer_types.set(buyer_type_instances)

#         return Response(
#             {"id": buyer_legal.id, "message": ".احراز هویت با موفقیت ثبت شد"},
#             status=status.HTTP_201_CREATED
#         )

#     @extend_schema(
#         request=BuyerLegalSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="ویرایش اطلاعات خریدار حقوقی",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق",
#                         value={"message": ".اطلاعات احراز هویت ویرایش شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"field": ["مقدار نامعتبر است"]}
#                     )
#                 ]
#             )
#         },
#         description="ویرایش اطلاعات احراز هویت خریدار حقوقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات احراز هویت ویرایش شد"}, status=status.HTTP_200_OK)


# class BuyerLegalBusinessInfoViewSet(ModelViewSet):
#     serializer_class = BuyerLegalBusinessInfoSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             buyer = get_object_or_404(Buyer, user=self.request.user)
#             return BuyerLegal.objects.filter(buyer=buyer)
#         return BuyerLegal.objects.none()

#     @extend_schema(
#         request=BuyerLegalBusinessInfoSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="اطلاعات کسب‌وکار با موفقیت ثبت شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت موفق",
#                         value={"id": 1, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی فایل‌ها یا داده‌ها",
#                 examples=[
#                     OpenApiExample(
#                         "حجم فایل زیاد است",
#                         value={"ceo_national_card": ["حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد"]}
#                     ),
#                     OpenApiExample(
#                         "فیلد الزامی",
#                         value={"economic_number": ["این فیلد الزامی است"]}
#                     )
#                 ]
#             )
#         },
#         description="ثبت اطلاعات کسب‌وکار برای خریدار حقوقی"
#     )
#     def create(self, request, *args, **kwargs):
#         buyer = get_object_or_404(Buyer, user=request.user)
#         buyer_legal = get_object_or_404(BuyerLegal, buyer=buyer)

#         if BuyerLegalBusinessInfo.objects.filter(buyer_legal=buyer_legal).exists():
#             return Response(
#                 {"detail": "اطلاعات کسب‌وکار قبلاً ثبت شده است"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(buyer_legal=buyer_legal)

#         return Response(
#             {"id": serializer.instance.id, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"},
#             status=status.HTTP_201_CREATED
#         )

#     @extend_schema(
#         request=BuyerLegalBusinessInfoSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="ویرایش اطلاعات کسب‌وکار",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق",
#                         value={"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی",
#                 examples=[
#                     OpenApiExample(
#                         "فایل نامعتبر",
#                         value={"activity_license": ["حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد"]}
#                     )
#                 ]
#             )
#         },
#         description="ویرایش اطلاعات کسب‌وکار خریدار حقوقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}, status=status.HTTP_200_OK)


# class BuyerLegalContactInfoViewSet(ModelViewSet):
#     serializer_class = BuyerLegalContactInfoSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             buyer = get_object_or_404(Buyer, user=self.request.user)
#             return BuyerLegal.objects.filter(buyer=buyer)
#         return BuyerLegal.objects.none()

#     def get_queryset(self):
#         buyer = get_object_or_404(Buyer, user=self.request.user)
#         buyer_legal = get_object_or_404(BuyerLegal, buyer=buyer)
#         return BuyerLegalContactInfo.objects.filter(buyer_legal=buyer_legal)

#     @extend_schema(
#         request=BuyerLegalContactInfoSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="اطلاعات تماس با موفقیت ثبت شد",
#                 examples=[OpenApiExample("ثبت موفق", value={"message": "اطلاعات تماس ثبت شد"})]
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی",
#                 examples=[
#                     OpenApiExample("آدرس انبار الزامی", value={"warehouse_address": ["در صورت داشتن انبار، وارد کردن آدرس آن الزامی است."]})
#                 ]
#             )
#         },
#         description="ثبت اطلاعات تماس خریدار حقوقی"
#     )
#     def create(self, request, *args, **kwargs):
#         buyer = get_object_or_404(Buyer, user=request.user)
#         buyer_legal = get_object_or_404(BuyerLegal, buyer=buyer)

#         if BuyerLegalContactInfo.objects.filter(buyer_legal=buyer_legal).exists():
#             return Response(
#                 {"detail": "اطلاعات تماس قبلاً ثبت شده است."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(buyer_legal=buyer_legal)

#         return Response({"message": "اطلاعات تماس ثبت شد"}, status=status.HTTP_201_CREATED)

#     @extend_schema(
#         request=BuyerLegalContactInfoSerializer,
#         responses={
#             200: OpenApiResponse(description="ویرایش اطلاعات تماس", examples=[OpenApiExample("ویرایش موفق", value={"message": "ویرایش انجام شد"})])
#         },
#         description="ویرایش اطلاعات تماس خریدار حقوقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop("partial", False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": "ویرایش انجام شد"}, status=status.HTTP_200_OK)          


# class BuyerOTPVerificationViewSet(ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = FinalApprovalOfBuyerSerializer
#     throttle_classes = [OTPThrottle]
#     throttle_scope = 'send_otp'

#     def get_queryset(self):
#         user = self.request.user
#         return BuyerLegal.objects.filter(user=user)

#     @extend_schema(
#         description="دریافت اطلاعات خریدار",
#         responses={
#             200: OpenApiResponse(
#                 description="اطلاعات خریدار با موفقیت دریافت شد",
#                 examples=[
#                     OpenApiExample(
#                         "دریافت موفق",
#                         value={"id": 1, "name": "فروشگاه فلان", "is_verified": False}
#                     )
#                 ],
#             )
#         }
#     )
#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.user != request.user:
#             return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)
#         serializer = self.get_serializer(instance)
#         return Response({"data": serializer.data})

#     @extend_schema(
#         request=None,
#         description="ارسال و تایید کد برای ثبت‌ نام خریدار",
#         responses={
#             201: OpenApiResponse(description="کد ثبت‌ نام ارسال شد"),
#             200: OpenApiResponse(description="ثبت‌ نام با موفقیت تایید شد"),
#             400: OpenApiResponse(description="خطا در ارسال یا تایید"),
#             429: OpenApiResponse(description="محدودیت ارسال بیش از حد کد فعال است"),
#         },
#     )
#     @action(detail=True, methods=['post'], url_path='verify-otp_signup_buyer', permission_classes=[])
#     def verify_otp_signup(self, request, pk=None):
#         throttle = self.throttle_classes[0]()
#         if not throttle.allow_request(request, self):
#             cache_key = throttle.get_cache_key(request)
#             data = cache.get(cache_key, {})
#             blocked_until = data.get('blocked_until')
#             if blocked_until:
#                 remaining = int(blocked_until - time.time())
#                 raise Throttled(detail=f"ارسال بیش از حد مجاز. لطفاً {remaining // 60} دقیقه دیگر امتحان کنید")
#             else:
#                 raise Throttled(detail="ارسال بیش از حد مجاز. لطفاً کمی صبر کنید")

#         user = request.user
#         buyer = self.get_object()

#         if buyer.user != user:
#             return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)

#         otp_code = request.data.get("otp_code")
#         otp_token = request.data.get("otp_token")

#         if not otp_code:
#             self.throttle_scope = 'send_otp'
#             try:
#                 self.check_throttles(request)
#             except Exception:
#                 return Response({"detail": "درخواست‌های ارسال کد بیش از حد مجاز است"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

#             otp_service = OTPService(user)
#             otp_service.send()

#             otp_token = str(uuid.uuid4())
#             cache.set(f"otp_token:{otp_token}", user.id, timeout=300)
#             otp_service.save_otp_token(otp_token)

#             response_data = {"detail": "کد ثبت‌نام به موبایل شما ارسال شد"}
#             if settings.DEBUG:
#                 response_data["otp_token"] = otp_token

#             return Response(response_data, status=status.HTTP_201_CREATED)

#         if not otp_token:
#             return Response({"detail": "توکن ارسال نشده"}, status=status.HTTP_400_BAD_REQUEST)

#         user_id = cache.get(f"otp_token:{otp_token}")
#         if user_id != user.id:
#             return Response({"detail": "توکن نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

#         otp_service = OTPService(user)
#         if otp_service.is_otp_valid(otp_code):
#             buyer.is_verified = True
#             buyer.save()
#             return Response({"message": "ثبت‌نام شما با موفقیت تأیید شد"}, status=status.HTTP_200_OK)

#         return Response({"detail": "کد تأیید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)


# class BuyerRealViewSet(ModelViewSet):
#     serializer_class = BuyerRealSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return BuyerReal.objects.filter(buyer__user=self.request.user)

#     def perform_update(self, serializer):
#         serializer.save()

#     @extend_schema(
#         request=BuyerRealSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="اطلاعات خریدار حقیقی با موفقیت ثبت شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت موفق",
#                         value={"id": 1, "message": "اطلاعات با موفقیت ثبت شد."}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطا در اعتبارسنجی",
#                 examples=[
#                     OpenApiExample(
#                         "خطای اعتبارسنجی",
#                         value={"national_code": ["این فیلد الزامی است."]}
#                     )
#                 ],
#             ),
#         }
#     )
#     def create(self, request, *args, **kwargs):
#         try:
#             buyer = request.user.buyer_profile
#         except Buyer.DoesNotExist:
#             return Response(
#                 {"detail": "ابتدا باید حساب خریدار ایجاد شود."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         buyer_types_data = serializer.validated_data.pop('buyer_types', [])

#         buyer_real = BuyerReal.objects.create(
#             buyer=buyer,
#             **serializer.validated_data
#         )

#         buyer_real.buyer_types.set(buyer_types_data)

#         return Response(
#             {"id": buyer_real.id, "message": "اطلاعات با موفقیت ثبت شد."},
#             status=status.HTTP_201_CREATED
#         )

#     @extend_schema(
#         request=BuyerRealSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="ویرایش اطلاعات خریدار حقیقی",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق",
#                         value={"message": "اطلاعات با موفقیت ویرایش شد."}
#                     )
#                 ],
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی",
#             ),
#         }
#     )
#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         partial = kwargs.pop("partial", False)
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)

#         buyer_types_data = serializer.validated_data.pop('buyer_types', [])
#         self.perform_update(serializer)
#         instance.buyer_types.set(buyer_types_data)

#         return Response({"message": "اطلاعات با موفقیت ویرایش شد."}, status=status.HTTP_200_OK)

# class BuyerRealBusinessInfoViewSet(ModelViewSet):
#     serializer_class = BuyerRealBusinessInfoSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             buyer = get_object_or_404(Buyer, user=self.request.user)
#             return BuyerReal.objects.filter(buyer=buyer)
#         return BuyerReal.objects.none()

#     @extend_schema(
#         request=BuyerRealBusinessInfoSerializer,
#         responses={
#             201: OpenApiResponse(
#                 description="اطلاعات کسب‌وکار با موفقیت ثبت شد",
#                 examples=[
#                     OpenApiExample(
#                         "ثبت موفق",
#                         value={"id": 1, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی فایل‌ها یا داده‌ها",
#                 examples=[
#                     OpenApiExample(
#                         "حجم فایل زیاد است",
#                         value={"ceo_national_card": ["حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد"]}
#                     ),
#                     OpenApiExample(
#                         "فیلد الزامی",
#                         value={"economic_number": ["این فیلد الزامی است"]}
#                     )
#                 ]
#             )
#         },
#         description="ثبت اطلاعات کسب‌وکار برای خریدار حقیقی"
#     )
#     def create(self, request, *args, **kwargs):
#         buyer = get_object_or_404(Buyer, user=request.user)
#         buyer_real = get_object_or_404(BuyerReal, buyer=buyer)

#         if BuyerLegalBusinessInfo.objects.filter(buyer_real=buyer_real).exists():
#             return Response(
#                 {"detail": "اطلاعات کسب‌وکار قبلاً ثبت شده است"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(buyer_real=buyer_real)

#         return Response(
#             {"id": serializer.instance.id, "message": ".اطلاعات کسب‌وکار با موفقیت ثبت شد"},
#             status=status.HTTP_201_CREATED
#         )

#     @extend_schema(
#         request=BuyerRealBusinessInfoSerializer,
#         responses={
#             200: OpenApiResponse(
#                 description="ویرایش اطلاعات کسب‌وکار",
#                 examples=[
#                     OpenApiExample(
#                         "ویرایش موفق",
#                         value={"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}
#                     )
#                 ]
#             ),
#             400: OpenApiResponse(
#                 description="خطای اعتبارسنجی",
#                 examples=[
#                     OpenApiExample(
#                         "فایل نامعتبر",
#                         value={"activity_license": ["حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد"]}
#                     )
#                 ]
#             )
#         },
#         description="ویرایش اطلاعات کسب‌وکار خریدار حقیقی"
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({"message": ".اطلاعات کسب‌وکار با موفقیت ویرایش شد"}, status=status.HTTP_200_OK)
     