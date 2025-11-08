import re
from datetime import timedelta

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone

# DRF imports
from rest_framework.exceptions import ValidationError

# Local imports
from .validators import validate_iranian_phone


class CustomUserManager(BaseUserManager):
    def validate_password(self, password):
        conditions = [
            (len(password) >= 7, 'رمز عبور باید حداقل ۷ کاراکتر باشد'),
            (re.search(r'[A-Za-z]', password), 'رمز عبور باید حداقل یک حرف داشته باشد'),
            (re.search(r'[0-9]', password), 'رمز عبور باید حداقل یک عدد داشته باشد'),
        ]

        for condition, message in conditions:
            if not condition:
                raise ValidationError(message)
                
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('وارد کردن شماره موبایل الزامی است')
        
        if password:
            self.validate_password(password)

        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
    max_length=15,
    unique=True,
    validators=[validate_iranian_phone],
    verbose_name="شماره موبایل تایید شده"
    )
    username = models.CharField(
    max_length=150,
    blank=True, null=True,
    unique=True,
    verbose_name='نام کاربری'
    )
    email = models.EmailField(
        blank=True, null=True,
        unique=True,
        verbose_name="ایمیل"
    )
    is_active = models.BooleanField(
        default=True, verbose_name="فعال"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تأیید شده'
    ) 
    is_staff = models.BooleanField(
        default=False, verbose_name="کارمند ادمین؟"
    )
    date_joined = models.DateTimeField(
        default=timezone.now, verbose_name="تاریخ عضویت"
    )
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        permissions = [
        ("view_user", "Can view user"),
        ("change_user", "Can change user"),
        ("delete_user", "Can delete user"),
        ("verify_user", "Can verify user"),
    ]
    default_permissions = ()

    def __str__(self):
        return f"{self.username} ({self.phone_number})"
    

class Province(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name = "استان"
    )
    class Meta:
        verbose_name = "استان محل فعالیت"
        verbose_name_plural = "استان‌های محل فعالیت"

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name = "شهر"
    )
    province = models.ForeignKey(
        Province, 
        related_name="cities", 
        on_delete=models.CASCADE,
        verbose_name = "استان"
    )
    class Meta:
        verbose_name = "شهر محل فعالیت"
        verbose_name_plural = "شهرهای محل فعالیت"

    def __str__(self):
        return f"{self.name} - {self.province.name}"    


class SellerType(models.Model):
    code = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="کد"
    )
    name = models.CharField(
        max_length=100, 
        verbose_name="نام"
    )

    class Meta:
        verbose_name = "نوع کسب و کار فروشنده"
        verbose_name_plural = "انواع کسب و کار فروشندگان"

    def __str__(self):
        return self.name

class IndustryCategory(models.Model):
    name = models.CharField(max_length=255, 
    unique=True, 
    verbose_name="دسته بندی صنف"
    )

    class Meta:
        verbose_name = "دسته بندی صنف فروشنده"
        verbose_name_plural = "دسته بندی صنف فروشندگان"

    def __str__(self):
        return self.name

class LegalSeller(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        null=True, blank=True,
        verbose_name="فروشنده حقوقی"
    )
    manager_full_name = models.CharField(
        max_length=255,
        verbose_name="نام و نام خانوادگی مدیر عامل"
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name="نام شرکت"
    )
    manager_national_code = models.CharField(
        max_length=20,
        verbose_name="کد ملی مدیر عامل"
    )
    national_id = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شناسه ی ملی شرکت"   
    )
    company_registration_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name = "شماره ثبت شرکت"
    )  
    supplier_types = models.ManyToManyField(
        SellerType,
        verbose_name="نوع کسب و کار"
    )
    marketer_referral_code = models.CharField(
        max_length=50, 
        null=True, blank=True,
        verbose_name="کد معرف بازاریاب"
    )
    economic_code = models.CharField(
        max_length=20,
        null=True, blank=True,
        verbose_name="شماره اقتصادی"
    )
    manager_national_card = models.FileField(
        upload_to="national_cards/",
        null=True, blank=True,
        verbose_name="کارت ملی مدیرعامل"
    )
    national_card_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود کارت ملی"
    )
    announcement_of_the_latest_changes = models.FileField(
        upload_to='establishment_docs/',
        null=True, blank=True,
        verbose_name="آخرین آگهی تغییرات یا تاسیس"
    )
    announcement_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود آگهی تغییرات"
    )
    business_license = models.FileField(
        upload_to='licenses/',
        blank=True,
        null=True,
        verbose_name="مجوز فعالیت / پروانه بهره‌برداری / کارت بازرگانی"
    )
    business_license_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود مجوز فعالیت"
    )
    industryselection = models.ManyToManyField(
        IndustryCategory, 
        blank=True,
        verbose_name="انتخاب صنف"
    )
    phone_number = models.CharField(
        max_length=15,
        null=True, blank=True,
        validators=[validate_iranian_phone],
        verbose_name="تلفن همراه"
    )
    phone_fixed = models.CharField(
        max_length=15, 
        null=True, blank=True,
        verbose_name="تلفن ثابت"
    )
    province = models.ForeignKey(
        Province, 
        null=True, blank=True,
        on_delete=models.CASCADE, 
        verbose_name="استان"
    )
    city = models.ForeignKey(
        City, 
        null=True, blank=True,
        on_delete=models.CASCADE, 
        verbose_name="شهر"
    )
    postal_code = models.CharField(
        max_length=20, 
        null=True, blank=True,
        verbose_name="کدپستی"
    )
    office_address = models.TextField(
        null=True, blank=True,
        verbose_name="آدرس دفتر کار یا محل فعالیت"
    )
    has_warehouse = models.BooleanField(
        null=True, blank=True,
        default=False, 
        verbose_name="آیا انبار دارید؟"
    )
    warehouse_address = models.TextField(
        verbose_name="آدرس انبار",
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name="تایید شده توسط ادمین"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ آخرین تغییر"
    )
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name="شرایط پذیرفته شده"
    )

    def is_complete(self):
        required_fields = [
            self.company_name,
            self.national_id,
            self.company_registration_number,
            self.manager_full_name,
            self.manager_national_code,
            self.supplier_types.exists(),
            self.economic_code,
            self.industryselection.exists(),
            self.manager_national_card,
            self.announcement_of_the_latest_changes,
            self.phone_number,
            self.phone_fixed,
            self.city,
            self.province,
            self.postal_code,
            self.office_address,
            self.has_warehouse is not None,
            self.warehouse_addressif if self.has_warehouse else True

        ]
        return all(required_fields)    
    
    def __str__(self):
        return f"{self.company_name} ({self.user})" if self.user else self.company_name

    class Meta:
        verbose_name = "فروشنده حقوقی"
        verbose_name_plural = "فروشندگان حقوقی"
        permissions = [
            ("view_legalseller", "Can view legal seller"),
            ("change_legalseller", "Can change legal seller"),
            ("delete_legalseller", "Can delete legal seller"),
            ("verify_legalseller", "Can verify legal seller"),
        ]
        default_permissions = ()

class RealSeller(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="فروشنده حقیقی"
    )
    full_name = models.CharField(
        max_length=100,
        verbose_name="نام و نام خانوادگی"
    )
    shop_name = models.CharField(
        max_length=100, 
        verbose_name="نام فروشگاه / کسب‌وکار"
    )
    birth_date = models.DateField(
        verbose_name="سال تولد"
    )
    national_code = models.CharField(
        max_length=10, 
        verbose_name="کد ملی"
    )
    marketer_referral_code = models.CharField(
        max_length=20, 
        blank=True, null=True, 
        verbose_name="کد معرف بازاریاب"
    )
    supplier_types = models.ManyToManyField(
        SellerType, 
        verbose_name="نوع کسب‌وکار"
    )
    economic_code = models.CharField(
        max_length=20, 
        blank=True,
        null=True,
        verbose_name="شماره اقتصادی"
    )
    national_id_card = models.FileField(
        upload_to='national_id_cards/',
        null=True, blank=True,
        verbose_name="کارت ملی مدیرعامل"
    )
    national_id_card_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود کارت ملی"
    )
    business_license = models.FileField(
        upload_to='business_licenses/',
        null=True, blank=True,
        verbose_name="مجوز فعالیت/پروانه بهره برداری/کارت بازرگانی"
    )
    business_license_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود مجوز فعالیت"
    )
    industryselection = models.ManyToManyField(
        IndustryCategory, 
        blank=True,
        verbose_name="انتخاب صنف"
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True, blank=True,
        validators=[validate_iranian_phone],
        verbose_name="تلفن همراه"
    )
    phone_fixed = models.CharField(
        max_length=15, 
        null=True, blank=True,
        verbose_name="تلفن ثابت"
    )
    province = models.ForeignKey(
        Province, 
        null=True, blank=True,
        on_delete=models.CASCADE, 
        verbose_name="استان"
    )
    city = models.ForeignKey(
        City, 
        null=True, blank=True,
        on_delete=models.CASCADE, 
        verbose_name="شهر"
    )
    postal_code = models.CharField(
        max_length=20, 
        null=True, blank=True,
        verbose_name="کدپستی"
    )
    office_address = models.TextField(
        null=True, blank=True,
        verbose_name="آدرس دفتر کار یا محل فعالیت"
    )
    has_warehouse = models.BooleanField(
        default=False,
        null=True, blank=True, 
        verbose_name="آیا انبار دارید؟"
    )
    warehouse_address = models.TextField(
        verbose_name="آدرس انبار",
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name="تایید شده توسط ادمین"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ آخرین تغییر"
    )
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name="شرایط پذیرفته شده"
    )
    
    def is_complete(self):
        required_fields = [
            self.shop_name,
            self.national_code,
            self.birth_date,
            self.full_name,
            self.supplier_types,
            self.industryselection,
            self.national_id_card,
            self.business_license,
            self.phone_number,
            self.phone_fixed,
            self.city,
            self.province,
            self.postal_code,
            self.office_address,
            self.has_warehouse,
            self.warehouse_address

        ]
        return all(required_fields)   

    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "فروشنده حقیقی"
        verbose_name_plural = "فروشندگان حقیقی"
        permissions = [
            ("view_realseller", "Can view real seller"),
            ("change_realseller", "Can change real seller"),
            ("delete_realseller", "Can delete real seller"),
            ("verify_realseller", "Can verify real seller"),
        ]
        default_permissions = ()

class Buyer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="خریدار", 
        related_name='buyer_profile'
    )
    full_name = models.CharField(
        max_length=50
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[validate_iranian_phone],
        verbose_name="تلفن همراه"
    )
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name="شرایط همکاری"
    )
    class Meta:
        verbose_name = "خریدار"
        verbose_name_plural = "خریداران"


    def __str__(self):
        return f'{self.full_name}'


class BuyerType(models.Model):
    code = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="کد"
    )
    title = models.CharField(
        max_length=100,
        verbose_name = "نام"
    )

    class Meta:
        verbose_name = "انواع کسب و کار خریدار"
        verbose_name_plural = "انواع کسب و کار خریداران"

    def __str__(self):
        return self.title

class BuyerCategory(models.Model):
    name = models.CharField(
    max_length=100, 
    verbose_name="دسته‌بندی صنف"
    )
    class Meta:
        verbose_name ="دسته بندی صنف خریدار"
        verbose_name_plural = "دسته بندی صنف خریداران"


    def __str__(self):
        return self.name


class BusinessField(models.Model):
    name = models.CharField(
    max_length=100,
    verbose_name="زمینه فعالیت"
    )

    class Meta:
        verbose_name = "زمینه فعالیت خریدار"
        verbose_name_plural = "زمینه فعالیت خریداران"
    def __str__(self):
        return self.name


class BuyerLegal(models.Model):
    buyer = models.OneToOneField(
        "Buyer", 
        on_delete=models.CASCADE, 
        verbose_name="پروفایل خریدار"
    )
    company_name = models.CharField(
        max_length=255, 
        verbose_name="نام شرکت"
    )
    national_id = models.CharField(
        max_length=11, 
        unique=True,
        verbose_name="شناسه ملی شرکت"
    )
    registration_number = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="شماره ثبت شرکت"
    )
    ceo_full_name = models.CharField(
        max_length=255, 
        verbose_name="نام و نام خانوادگی مدیرعامل"
    )
    ceo_national_code = models.CharField(
        max_length=10, 
        verbose_name="کد ملی مدیرعامل"
    )
    marketer_code = models.CharField(
        max_length=50, 
        blank=True, null=True, 
        verbose_name="کد معرف بازاریاب"
    )
    buyer_types = models.ManyToManyField(
        BuyerType, 
        blank=True, 
        verbose_name="نوع کسب‌وکار"
    )
    economic_number = models.CharField(
        max_length=20,
        blank=True, null=True,
        unique=True,
        verbose_name="شماره اقتصادی"
    )
    business_category = models.ForeignKey(
        BuyerCategory,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name="صنف"
    )
    business_fields = models.ManyToManyField(
        BusinessField,
        blank=True,
        verbose_name="زمینه فعالیت"
    )
    ceo_national_card = models.FileField(
        upload_to='ceo_national_cards/',
        verbose_name="کارت ملی مدیرعامل",
        blank=True, null=True,
        max_length=255
    )
    national_card_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود کارت ملی"
    )
    last_establishment_announcement = models.FileField(
        upload_to='establishment_announcements/',
        blank=True, null=True,
        verbose_name="آخرین آگهی تغییرات یا تاسیس",
        max_length=255
    )
    announcement_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود آگهی تغییرات"
    )
    activity_license = models.FileField(
        upload_to='activity_licenses/',
        max_length=255,
        blank=True, null=True,
        verbose_name="مجوز فعالیت",
    )
    business_license_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود مجوز فعالیت"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True, null=True,
        validators=[validate_iranian_phone],
        verbose_name="تلفن همراه"
    )
    phone_fixed = models.CharField(
        max_length=15, 
        blank=True, null=True,
        verbose_name="تلفن ثابت"
    )
    province = models.ForeignKey(
        Province, 
        blank=True, null=True,
        on_delete=models.CASCADE,  
        verbose_name="استان"
    )
    city = models.ForeignKey(
        City, 
        blank=True, null=True,
        on_delete=models.CASCADE, 
        verbose_name="شهر"
    )
    postal_code = models.CharField(
        max_length=20, 
        blank=True, null=True,
        verbose_name="کدپستی"
    )
    office_address = models.TextField(
        blank=True, null=True,
        verbose_name="آدرس دفتر کار یا محل فعالیت"
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name="تأیید شده توسط ادمین"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ آخرین تغییر"
    )
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name="شرایط پذیرفته شده"
    )
    
    def is_complete(self):
        required_fields = [
            self.company_name,
            self.national_id,
            self.registration_number,
            self.ceo_full_name,
            self.ceo_national_code,
            self.buyer_types.exists(),
            self.economic_number,
            self.business_category,
            self.business_fields.exists(),
            self.ceo_national_card,
            self.last_establishment_announcement,
            self.phone_number,
            self.phone_fixed,
            self.city,
            self.province,
            self.postal_code,
            self.office_address,
        ]

        return all(required_fields)    

    def __str__(self):
        return self.company_name
    
    class Meta:
        verbose_name = "خریدار حقوقی"
        verbose_name_plural = "خریداران حقوقی"
        permissions = [
            ("view_buyerlegal", "Can view legal buyer"),
            ("change_buyerlegal", "Can change legal buyer"),
            ("delete_buyerlegal", "Can delete legal buyer"),
            ("verify_buyerlegal", "Can verify legal buyer"),
        ]
        default_permissions = ()

class BuyerReal(models.Model):
    buyer = models.OneToOneField(
        "Buyer", 
        on_delete=models.CASCADE, 
        verbose_name="پروفایل خریدار"
    )
    store_name = models.CharField(
        max_length=255, 
        verbose_name="نام فروشگاه"
    )
    full_name = models.CharField(
        max_length=255, 
        verbose_name="نام و نام خانوادگی"
    )
    national_code = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="کد ملی"
    )
    birth_date = models.DateField(
        verbose_name="سال تولد"
    )
    marketer_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="کد معرف بازاریاب"
    )
    buyer_types = models.ManyToManyField(
        BuyerType, 
        verbose_name="نوع کسب‌وکار"
    )
    economic_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True, 
        null=True,
        verbose_name="شماره اقتصادی"
    )
    business_category = models.ForeignKey(
        BuyerCategory,
        on_delete=models.SET_NULL,
        blank=True, 
        null=True,
        verbose_name="صنف"
    )
    business_fields = models.ManyToManyField(
        BusinessField,
        blank=True, 
        verbose_name="زمینه فعالیت"
    )
    ceo_national_card = models.FileField(
        upload_to='ceo_national_cards/',
        blank=True, 
        null=True,
        verbose_name="کارت ملی",
        max_length=255
    )
    national_id_card_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود کارت ملی"
    )
    activity_license = models.FileField(
        upload_to='activity_licenses/',
        max_length=255,
        blank=True, null=True,
        verbose_name="مجوز فعالیت",
    )
    business_license_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود مجوز فعالیت"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True, 
        null=True,
        validators=[validate_iranian_phone],
        verbose_name="تلفن همراه"
    )
    phone_fixed = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name="تلفن ثابت"
    )
    province = models.ForeignKey(
        Province, 
        blank=True, 
        null=True,
        on_delete=models.CASCADE,  
        verbose_name="استان"
    )
    city = models.ForeignKey(
        City, 
        blank=True, 
        null=True,
        on_delete=models.CASCADE, 
        verbose_name="شهر"
    )
    postal_code = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="کدپستی"
    )
    office_address = models.TextField(
        blank=True, 
        null=True,
        verbose_name="آدرس دفتر کار یا محل فعالیت"
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name="تأیید شده توسط ادمین"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ آخرین تغییر"
    )
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name="شرایط پذیرفته شده"
    )
   
    def is_complete(self):
        required_fields = [
            self.store_name,
            self.national_code,
            self.full_name,
            self.birth_date,
            self.buyer_types.exists(),
            self.economic_number,
            self.business_category,
            self.business_fields.exists(),
            self.ceo_national_card,
            self.phone_number,
            self.phone_fixed,
            self.city,
            self.province,
            self.postal_code,
            self.office_address,
        ]

        return all(required_fields)       
    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "خریدار حقیقی"
        verbose_name_plural = "خریداران حقیقی"
        permissions = [
            ("view_buyerreal", "Can view real buyer"),
            ("change_buyerreal", "Can change real buyer"),
            ("delete_buyerreal", "Can delete real buyer"),
            ("verify_buyerreal", "Can verify real buyer"),
        ]
        default_permissions = ()


class MarketerManager(BaseUserManager):
    def validate_password(self, password):
        conditions = [
            (len(password) >= 7, 'رمز عبور باید حداقل ۷ کاراکتر باشد'),
            (re.search(r'[A-Za-z]', password), 'رمز عبور باید حداقل یک حرف داشته باشد'),
            (re.search(r'[0-9]', password), 'رمز عبور باید حداقل یک عدد داشته باشد'),
        ]

        for condition, message in conditions:
            if not condition:
                raise ValidationError(message)
                
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('وارد کردن شماره موبایل الزامی است')
        
        if password:
            self.validate_password(password)

        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class Marketer(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(
        max_length=255,
        verbose_name = "نام و نام خانوادگی"
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[validate_iranian_phone],
        verbose_name="تلفن همراه"
    )
    national_code = models.CharField(
        max_length=11,
        verbose_name="کد ملی"
    )
    province = models.ForeignKey(
        Province,
        null=True,
        blank=True, 
        on_delete=models.CASCADE, 
        verbose_name="استان"
    )
    city = models.ForeignKey(
        City,
        null=True,
        blank=True, 
        on_delete=models.CASCADE,  
        verbose_name="شهر"
    )
    email = models.EmailField(
        blank=True, null=True,
        unique=True,
        verbose_name="ایمیل"
    )
    picture_national_card = models.FileField(
        upload_to="national_cards/",
        verbose_name="بارگذاری تصویر کارت ملی"
    )
    national_card_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="زمان ایجاد آپلود کارت ملی"
    )
    Marketing_cooperation_agreement = models.FileField(
        upload_to='establishment_docs/',
        verbose_name="بارگذاری قرارداد همکاری بازاریابی"
    )
    cooperation_agreement_uploaded_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name= "زمان ایجاد آپلود قرارداد همکاری"
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name="تأیید شده توسط ادمین"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ آخرین تغییر"
    )
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name="شرایط پذیرفته شده"
    )
    is_active = models.BooleanField(
        default=True, verbose_name="فعال"
    )
    is_staff = models.BooleanField(
        default=False, verbose_name="کارمند ادمین؟"
    )
    date_joined = models.DateTimeField(
        default=timezone.now, verbose_name="تاریخ عضویت"
    )
    groups = models.ManyToManyField(
        Group,
        related_name='marketer_set',
        blank=True,
        help_text='گروه‌هایی که این بازاریاب عضو آن‌هاست',
        verbose_name='groups',
        related_query_name='marketer'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='marketer_set',
        blank=True,
        help_text='دسترسی‌های خاص برای این بازاریاب',
        verbose_name='user permissions',
        related_query_name='marketer'
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = MarketerManager()

    def __str__(self):
        return self.full_name

    def is_complete(self):
        required_fields = [
            self.full_name, 
            self.phone_number, 
            self.national_code, 
            self.province, 
            self.city, 
            self.email, 
            self.picture_national_card, 
            self.Marketing_cooperation_agreement
            ]
        
        return all(required_fields)

    class Meta:
        verbose_name = "بازاریاب"
        verbose_name_plural = "بازاریاب ها"
        