import re

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import CustomUser, SellerType, LegalSeller, RealSeller
from ..validators import validate_iranian_phone


class SendOTPSellerSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11,
        help_text="شماره موبایل معتبر (مثلاً 09123456789)",
        label="شماره موبایل",
        validators=[validate_iranian_phone]
        )
    remember_me = serializers.BooleanField(default=False)

class VerifyOTPSellerSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    otp_code = serializers.CharField()


class AcceptTermsSerializer(serializers.Serializer):
    accepted_terms = serializers.BooleanField(write_only=True)

    def validate_accepted_terms(self, value):
        if not value:
            raise serializers.ValidationError("برای ادامه ثبت‌ نام باید شرایط همکاری را بپذیرید")
        return value

class SellerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerType
        fields = ['code']

class LegalSellerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    supplier_types = serializers.SlugRelatedField(
        many=True,
        slug_field='code', 
        queryset=SellerType.objects.all()
    )

    class Meta:
        model = LegalSeller
        fields = [
            "id",
            "company_name",
            "national_id",
            "company_registration_number",
            "manager_full_name",
            "manager_national_code",
            "marketer_referral_code",
            "supplier_types",
        ]

class BusinessAndLegalInformationSerializer(serializers.ModelSerializer):
    manager_national_card = serializers.FileField(required=True)
    announcement_of_the_latest_changes = serializers.FileField(required=True)

    class Meta:
        model = LegalSeller
        fields = [
            "economic_code",
            "industryselection",
            "manager_national_card",
            "announcement_of_the_latest_changes",
            "business_license",
        ]

    def validate_industryselection(self, value):
        if len(value) > 4:
            raise serializers.ValidationError("حداکثر ۴ صنف می‌توانید انتخاب کنید")
        return value

    
    def validate_file(self, value, allowed_extensions, max_file_size, field_name):
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"تنها فایل‌های {', '.join([e.upper() for e in allowed_extensions])} مجاز هستند برای {field_name}"
            )
        if value.size > max_file_size:
            raise serializers.ValidationError(
                f"حجم فایل {field_name} نباید بیشتر از {max_file_size // (1024 * 1024)} مگابایت باشد"
            )
        return value

    def validate_manager_national_card(self, value):
        return self.validate_file(value, ['jpeg', 'png', 'pdf'], 2 * 1024 * 1024, "کارت ملی مدیرعامل")

    def validate_announcement_of_the_latest_changes(self, value):
        return self.validate_file(value, ['jpeg', 'png', 'pdf'], 5 * 1024 * 1024, "آخرین آگهی تاسیسات")

    def validate_business_license(self, value):
        if not value:
            return value
        return self.validate_file(value, ['jpeg', 'png', 'pdf'], 5 * 1024 * 1024, "مجوز فعالیت")


class ContactInfoLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalSeller
        fields = [
        "phone_number",
        "phone_fixed",
        "province",
        "city",
        "postal_code",
        "office_address",
        "has_warehouse",
        "warehouse_address",
    ]
        
    def validate(self, data):
        has_warehouse = data.get('has_warehouse')
        warehouse_address = data.get('warehouse_address')
        
        if has_warehouse and not warehouse_address:
            raise serializers.ValidationError("اگر انبار دارید، آدرس انبار را باید وارد کنید")
        if not has_warehouse:
            data['warehouse_address'] = None 
        
        return data

class Finalapprovaloflegalseller(serializers.ModelSerializer):
    class Meta:
        model = LegalSeller
        fields = [
            "company_name",
            "manager_full_name",
            "manager_national_code",
            "national_id",
            "company_registration_number",
            "economic_code",
            "phone_number",
            "phone_fixed",
            "city",
            "province",
            "postal_code",
            "office_address",
            "warehouse_address",
]         
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.warehouse_address:
            data.pop("warehouse_address", None)
        return data
   
class RealSellerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    supplier_types = serializers.SlugRelatedField(
        many=True,
        slug_field='code',
        queryset=SellerType.objects.all()
    )

    class Meta:
        model = RealSeller
        fields = [
            "id",
            "full_name", 
            "shop_name", 
            "birth_date", 
            "national_code",
            "marketer_referral_code", 
            "supplier_types",
        ]

class RealPersonBusinessInfoSerializer(serializers.ModelSerializer):
    national_id_card = serializers.FileField(required=True)
    business_license = serializers.FileField(required=True)
    class Meta:
        model = RealSeller
        fields = [
            'economic_code',
            'industryselection',
            'national_id_card',
            'business_license',
        ]

    def validate_industryselection(self, value):
        if len(value) > 4:
            raise serializers.ValidationError("حداکثر ۴ صنف می‌توانید انتخاب کنید")
        return value
            
    def validate_file(self, value, max_size, allowed_extensions=['jpeg', 'png', 'pdf'], file_name='فایل'):
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"تنها فایل‌های {', '.join(ext.upper() for ext in allowed_extensions)} مجاز هستند")
        if value.size > max_size:
            raise serializers.ValidationError(f"حجم {file_name} نباید بیشتر از {max_size // (1024*1024)} مگابایت باشد")
        return value

    def validate_national_id_card(self, value):
        return self.validate_file(value, max_size=2*1024*1024, file_name='کارت ملی')

    def validate_business_license(self, value):
        return self.validate_file(value, max_size=5*1024*1024, file_name='مجوز فعالیت')

class ContactInfoRealSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealSeller
        fields = [
            "phone_number",
            "phone_fixed",
            "province",
            "city",
            "postal_code",
            "office_address",
            "has_warehouse",
            "warehouse_address",
        ]   
        
    def validate(self, data):
        has_warehouse = data.get('has_warehouse')
        warehouse_address = data.get('warehouse_address')
        
        if has_warehouse and not warehouse_address:
            raise serializers.ValidationError("اگر انبار دارید، آدرس انبار را باید وارد کنید")
        if not has_warehouse:
            data['warehouse_address'] = None
        
        return data     


class FinalapprovalofrealsellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealSeller
        fields = [
            "shop_name",
            "full_name",
            "birth_date",
            "national_code",
            "supplier_types",
            "phone_number",
            "phone_fixed",
            "city",
            "province",
            "postal_code",
            "office_address",
            "warehouse_address",
]         

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.warehouse_address:
            data.pop("warehouse_address", None)
        return data
