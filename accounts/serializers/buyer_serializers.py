import re

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import (
    CustomUser,
    Buyer,
    BuyerLegal,
    BuyerReal,
    BuyerType,
    BusinessField,
)
from ..validators import validate_iranian_phone


class SendOTPBuyerSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11,
        help_text="شماره موبایل معتبر (مثلاً 09123456789)",
        label="شماره موبایل",
        validators=[validate_iranian_phone]
        )
    remember_me = serializers.BooleanField(default=False)

class VerifyOTPBuyerSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    otp_code = serializers.CharField()

class AcceptTermsSerializer(serializers.Serializer):
    accepted_terms = serializers.BooleanField(write_only=True)

    def validate_accepted_terms(self, value):
        if not value:
            raise serializers.ValidationError("برای ادامه ثبت‌ نام باید شرایط همکاری را بپذیرید")
        return value

class BuyerRegisterOrLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = [
            "full_name",
            "phone_number"
        ]
        
class BuyerLegalSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    buyer_types = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=BuyerType.objects.all()
    )
    
    class Meta:
        model = BuyerLegal
        fields = [
            "id",
            "company_name",
            "national_id",
            "registration_number",
            "ceo_full_name",
            "ceo_national_code",
            "marketer_code",
            "buyer_types"
        ]

class BuyerLegalBusinessInfoSerializer(serializers.ModelSerializer):
    ceo_national_card = serializers.FileField(required=False, allow_null=True)
    last_establishment_announcement = serializers.FileField(required=False, allow_null=True)
    activity_license = serializers.FileField(required=False, allow_null=True)
    business_fields = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=BusinessField.objects.all(),
        required=False
    )
    MAX_CEO_CARD_SIZE = 2 * 1024 * 1024 * 1024 
    MAX_OTHER_FILES_SIZE = 5 * 1024 * 1024      

    def validate_ceo_national_card(self, value):
        if value is None:
            return value
        if value.size > self.MAX_CEO_CARD_SIZE:
            raise serializers.ValidationError("حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد")
        return value

    def validate_last_establishment_announcement(self, value):
        if value is None:
            return value
        if value.size > self.MAX_OTHER_FILES_SIZE:
            raise serializers.ValidationError("حجم آگهی تاسیسات نباید بیشتر از 5 مگابایت باشد")
        return value

    def validate_activity_license(self, value):
        if value is None:
            return value
        if value.size > self.MAX_OTHER_FILES_SIZE:
            raise serializers.ValidationError("حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد")
        return value

    def validate_business_fields(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("حداکثر 3 صنف می‌توانید انتخاب کنید")
        return value
        
    class Meta:
        model = BuyerLegal
        fields = [
            "economic_number",
            "business_category",
            "business_fields",
            "ceo_national_card",
            "last_establishment_announcement",
            "activity_license",
        ]

class BuyerLegalContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerLegal
        fields = [
            "phone_number", 
            "phone_fixed", 
            "province", 
            "city",
            "postal_code", 
            "office_address",
        ]

class FinalApprovalOfBuyerLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerLegal
        fields = [
            "company_name",
            "national_id",
            "registration_number",
            "ceo_full_name",
            "ceo_national_code",
            "marketer_code",
            "phone_number", 
            "phone_fixed", 
            "province", 
            "city",
            "postal_code", 
            "office_address",
        ]

class BuyerRealSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    buyer_types = serializers.SlugRelatedField(
        many=True,
        slug_field='code',
        queryset=BuyerType.objects.all()
    )
    class Meta:
        model = BuyerReal
        fields = [
            "id",
            "store_name",
            "full_name",
            "national_code",
            "birth_date",
            "marketer_code",
            "buyer_types",
        ]  

class BuyerRealBusinessInfoSerializer(serializers.ModelSerializer):
    ceo_national_card = serializers.FileField(required=False, allow_null=True)
    activity_license = serializers.FileField(required=False, allow_null=True)
    business_fields = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=BusinessField.objects.all(),
        required=False
    )

    MAX_CEO_CARD_SIZE = 2 * 1024 * 1024 * 1024 
    MAX_OTHER_FILES_SIZE = 5 * 1024 * 1024      

    def validate_ceo_national_card(self, value):
        if value.size > self.MAX_CEO_CARD_SIZE:
            raise serializers.ValidationError("حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد")
        return value

    def validate_activity_license(self, value):
        if value.size > self.MAX_OTHER_FILES_SIZE:
            raise serializers.ValidationError("حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد")
        return value

    def validate_business_fields(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("حداکثر 3 صنف می‌توانید انتخاب کنید")
        return value
        
    class Meta:
        model = BuyerReal
        fields = [
            "economic_number",
            "business_category",
            "business_fields",
            "ceo_national_card",
            "activity_license",
        ]

class BuyerRealContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerReal
        fields = [
            "phone_number", 
            "phone_fixed", 
            "province", 
            "city",
            "postal_code", 
            "office_address",
        ]      

class FinalApprovalOfBuyerRealSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerReal
        fields = [
            "store_name",
            "full_name",
            "national_code",
            "birth_date",
            "marketer_code",
            "phone_number", 
            "phone_fixed", 
            "province", 
            "city",
            "postal_code", 
            "office_address",

        ]

