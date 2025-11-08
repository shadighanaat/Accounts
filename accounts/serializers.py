# import re

# from rest_framework import serializers
# from rest_framework_simplejwt.tokens import RefreshToken

# from .models import CustomUser, SellerType, LegalSeller, RealSeller, Buyer, BuyerLegal, BuyerType, BuyerReal
# from .validators import validate_iranian_phone
# from django.contrib.auth import authenticate
# from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError

# class SendOTPSerializer(serializers.Serializer):
#     phone_number = serializers.CharField(max_length=11,
#         help_text="شماره موبایل معتبر (مثلاً 09123456789)",
#         label="شماره موبایل",
#         validators=[validate_iranian_phone]
#         )
#     remember_me = serializers.BooleanField(default=False)

# class VerifyOTPSerializer(serializers.Serializer):
#     otp_token = serializers.CharField()
#     otp_code = serializers.CharField()



# class LoginSerializer(serializers.Serializer):
#     otp_token = serializers.CharField()
#     remember_me = serializers.BooleanField(default=False)


# class LoginWithPasswordSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField(write_only=True)
#     remember_me = serializers.BooleanField(required=False, default=False)

#     def validate(self, attrs):
#         username = attrs.get('username')
#         password = attrs.get('password')

#         User = get_user_model()

#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("نام کاربری یا رمز عبور نادرست است")

#         if not user.check_password(password):
#             raise serializers.ValidationError("نام کاربری یا رمز عبور نادرست است")

#         if not user.is_active:
#             raise serializers.ValidationError("حساب کاربری غیرفعال است")

#         attrs['user'] = user
#         return attrs

#     def validate_password(self, password):
       
#         conditions = [
#          (len(password) >= 7, 'پسورد باید حداقل 7 کاراکتر باشد'),
#          (re.search(r'[A-Za-z]', password), 'پسورد باید حداقل شامل یک حرف باشد'),
#          (re.search(r'[0-9]', password), 'پسورد باید حداقل شامل یک عدد باشد'),
#          (len([char for char in password if char.isalnum()]) >= 7, 'پسورد باید حداقل شامل 7 کاراکتر از ترکیب حروف و اعداد باشد')
#     ]

#         for condition, message in conditions:
#             if not condition:
#                 raise ValidationError(message)

# class RequestPasswordResetSerializer(serializers.Serializer):
#     email = serializers.EmailField()

#     def validate_email(self, value):
#         if not CustomUser.objects.filter(email__iexact=value).exists():
#             raise serializers.ValidationError("کاربری با این ایمیل یافت نشد")
#         return value


# class VerifyOTPEmailSerializer(serializers.Serializer):
#     otp_token = serializers.CharField()
#     otp_code = serializers.CharField()


# class ResetPasswordSerializer(serializers.Serializer):
#     otp_token = serializers.CharField()
#     new_password = serializers.CharField(min_length=7)

#     def validate_password(self, password):
       
#         conditions = [
#          (len(password) >= 7, 'پسورد باید حداقل 7 کاراکتر باشد'),
#          (re.search(r'[A-Za-z]', password), 'پسورد باید حداقل شامل یک حرف باشد'),
#          (re.search(r'[0-9]', password), 'پسورد باید حداقل شامل یک عدد باشد'),
#          (len([char for char in password if char.isalnum()]) >= 7, 'پسورد باید حداقل شامل 7 کاراکتر از ترکیب حروف و اعداد باشد')
#     ]

#         for condition, message in conditions:
#             if not condition:
#                 raise ValidationError(message)
                
#         return value


# class AcceptTermsSerializer(serializers.Serializer):
#     accepted_terms = serializers.BooleanField(write_only=True)

#     def validate_accepted_terms(self, value):
#         if not value:
#             raise serializers.ValidationError("برای ادامه ثبت‌ نام باید شرایط همکاری را بپذیرید")
#         return value

# class SellerTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SellerType
#         fields = ['code']

# class LegalSellerSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
#     supplier_types = serializers.SlugRelatedField(
#         many=True,
#         slug_field='code', 
#         queryset=SellerType.objects.all()
#     )

#     class Meta:
#         model = LegalSeller
#         fields = [
#             "id",
#             "company_name",
#             "national_id",
#             "company_registration_number",
#             "manager_full_name",
#             "manager_national_code",
#             "marketer_referral_code",
#             "supplier_types",
#         ]

# class BusinessAndLegalInformationSerializer(serializers.ModelSerializer):
#     manager_national_card = serializers.FileField(required=True)
#     announcement_of_the_latest_changes = serializers.FileField(required=True)

#     class Meta:
#         model = LegalSeller
#         fields = [
#             "economic_code",
#             "industryselection",
#             "manager_national_card",
#             "announcement_of_the_latest_changes",
#             "business_license",
#         ]

#     def validate_industryselection(self, value):
#         if len(value) > 4:
#             raise serializers.ValidationError("حداکثر ۴ صنف می‌توانید انتخاب کنید")
#         return value

    
#     def validate_file(self, value, allowed_extensions, max_file_size, field_name):
#         ext = value.name.split('.')[-1].lower()
#         if ext not in allowed_extensions:
#             raise serializers.ValidationError(
#                 f"تنها فایل‌های {', '.join([e.upper() for e in allowed_extensions])} مجاز هستند برای {field_name}"
#             )
#         if value.size > max_file_size:
#             raise serializers.ValidationError(
#                 f"حجم فایل {field_name} نباید بیشتر از {max_file_size // (1024 * 1024)} مگابایت باشد"
#             )
#         return value

#     def validate_manager_national_card(self, value):
#         return self.validate_file(value, ['jpeg', 'png', 'pdf'], 2 * 1024 * 1024, "کارت ملی مدیرعامل")

#     def validate_announcement_of_the_latest_changes(self, value):
#         return self.validate_file(value, ['jpeg', 'png', 'pdf'], 5 * 1024 * 1024, "آخرین آگهی تاسیسات")

#     def validate_business_license(self, value):
#         if not value:
#             return value
#         return self.validate_file(value, ['jpeg', 'png', 'pdf'], 5 * 1024 * 1024, "مجوز فعالیت")


# class ContactInfoLegalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LegalSeller
#         fields = [
#         "phone_number",
#         "phone_fixed",
#         "province",
#         "city",
#         "postal_code",
#         "office_address",
#         "has_warehouse",
#         "warehouse_address",
#     ]
        
#     def validate(self, data):
#         has_warehouse = data.get('has_warehouse')
#         warehouse_address = data.get('warehouse_address')
        
#         if has_warehouse and not warehouse_address:
#             raise serializers.ValidationError("اگر انبار دارید، آدرس انبار را باید وارد کنید")
#         if not has_warehouse:
#             data['warehouse_address'] = None 
        
#         return data

# class Finalapprovaloflegalseller(serializers.ModelSerializer):
#     class Meta:
#         model = LegalSeller
#         fields = [
#             "company_name",
#             "manager_full_name",
#             "manager_national_code",
#             "national_id",
#             "company_registration_number",
#             "economic_code",
#             "phone_number",
#             "phone_fixed",
#             "city",
#             "province",
#             "postal_code",
#             "office_address",
#             "warehouse_address",
# ]         
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         if not instance.warehouse_address:
#             data.pop("warehouse_address", None)
#         return data
   
# class RealSellerSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
#     supplier_types = serializers.SlugRelatedField(
#         many=True,
#         slug_field='code',
#         queryset=SellerType.objects.all()
#     )

#     class Meta:
#         model = RealSeller
#         fields = [
#             "id",
#             "full_name", 
#             "shop_name", 
#             "birth_date", 
#             "national_code",
#             "marketer_referral_code", 
#             "supplier_types",
#         ]

# class RealPersonBusinessInfoSerializer(serializers.ModelSerializer):
#     national_id_card = serializers.FileField(required=True)
#     business_license = serializers.FileField(required=True)
#     class Meta:
#         model = RealSeller
#         fields = [
#             'economic_code',
#             'industryselection',
#             'national_id_card',
#             'business_license',
#         ]

#     def validate_industryselection(self, value):
#         if len(value) > 4:
#             raise serializers.ValidationError("حداکثر ۴ صنف می‌توانید انتخاب کنید")
#         return value
            
#     def validate_file(self, value, max_size, allowed_extensions=['jpeg', 'png', 'pdf'], file_name='فایل'):
#         ext = value.name.split('.')[-1].lower()
#         if ext not in allowed_extensions:
#             raise serializers.ValidationError(f"تنها فایل‌های {', '.join(ext.upper() for ext in allowed_extensions)} مجاز هستند")
#         if value.size > max_size:
#             raise serializers.ValidationError(f"حجم {file_name} نباید بیشتر از {max_size // (1024*1024)} مگابایت باشد")
#         return value

#     def validate_national_id_card(self, value):
#         return self.validate_file(value, max_size=2*1024*1024, file_name='کارت ملی')

#     def validate_business_license(self, value):
#         return self.validate_file(value, max_size=5*1024*1024, file_name='مجوز فعالیت')

# class ContactInfoRealSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = RealSeller
#         fields = [
#             "phone_number",
#             "phone_fixed",
#             "province",
#             "city",
#             "postal_code",
#             "office_address",
#             "has_warehouse",
#             "warehouse_address",
#         ]   
        
#     def validate(self, data):
#         has_warehouse = data.get('has_warehouse')
#         warehouse_address = data.get('warehouse_address')
        
#         if has_warehouse and not warehouse_address:
#             raise serializers.ValidationError("اگر انبار دارید، آدرس انبار را باید وارد کنید")
#         if not has_warehouse:
#             data['warehouse_address'] = None
        
#         return data     


# class FinalapprovalofrealsellerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = RealSeller
#         fields = [
#             "shop_name",
#             "full_name",
#             "birth_date",
#             "national_code",
#             "supplier_types",
#             "phone_number",
#             "phone_fixed",
#             "city",
#             "province",
#             "postal_code",
#             "office_address",
#             "warehouse_address",
# ]         

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         if not instance.warehouse_address:
#             data.pop("warehouse_address", None)
#         return data

# class BuyerRegisterOrLoginSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Buyer
#         fields = [
#             "full_name",
#             "phone_number"
#         ]
        
# class BuyerLegalSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
#     class Meta:
#         model = BuyerLegal
#         fields = [
#             "id",
#             "company_name",
#             "national_id",
#             "registration_number",
#             "ceo_full_name",
#             "ceo_national_code",
#             "marketer_code",
#             "buyer_types"
#         ]

# class BuyerLegalBusinessInfoSerializer(serializers.ModelSerializer):
#     MAX_CEO_CARD_SIZE = 2 * 1024 * 1024 * 1024 
#     MAX_OTHER_FILES_SIZE = 5 * 1024 * 1024      

#     def validate_ceo_national_card(self, value):
#         if value.size > self.MAX_CEO_CARD_SIZE:
#             raise serializers.ValidationError("حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد")
#         return value

#     def validate_last_establishment_announcement(self, value):
#         if value.size > self.MAX_OTHER_FILES_SIZE:
#             raise serializers.ValidationError("حجم آگهی تاسیسات نباید بیشتر از 5 مگابایت باشد")
#         return value

#     def validate_activity_license(self, value):
#         if value.size > self.MAX_OTHER_FILES_SIZE:
#             raise serializers.ValidationError("حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد")
#         return value

#     def validate_industryselection(self, value):
#         if len(value) > 3:
#             raise serializers.ValidationError("حداکثر 3 صنف می‌توانید انتخاب کنید")
#         return value
        
#     class Meta:
#         model = BuyerLegal
#         fields = [
#             "economic_number",
#             "business_category",
#             "business_fields",
#             "ceo_national_card",
#             "last_establishment_announcement",
#             "activity_license",
#         ]

# class BuyerLegalContactInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BuyerLegal
#         fields = [
#             "phone_number", 
#             "phone_fixed", 
#             "province", 
#             "city",
#             "postal_code", 
#             "office_address",
#             "has_warehouse", 
#             "warehouse_address"
#         ]

#     def validate(self, data):
#         if data.get("has_warehouse") and not data.get("warehouse_address"):
#             raise serializers.ValidationError({"warehouse_address": "در صورت داشتن انبار، وارد کردن آدرس آن الزامی است"})
#         return data

# class FinalApprovalOfBuyerLegalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BuyerLegal
#         fields = [
#             "company_name",
#             "national_id",
#             "registration_number",
#             "ceo_full_name",
#             "ceo_national_code",
#             "marketer_code",
#             "buyer_types",
#             "phone_number", 
#             "phone_fixed", 
#             "province", 
#             "city",
#             "postal_code", 
#             "office_address",

#         ]

# class BuyerRealSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
#     buyer_types = serializers.SlugRelatedField(
#         many=True,
#         slug_field='code',
#         queryset=BuyerType.objects.all()
#     )
#     class Meta:
#         model = BuyerReal
#         fields = [
#             "id",
#             "store_name",
#             "full_name,"
#             "national_code",
#             "birth_date",
#             "marketer_code",
#             "buyer_types",
#         ]  

# class BuyerRealBusinessInfoSerializer(serializers.ModelSerializer):
#     MAX_CEO_CARD_SIZE = 2 * 1024 * 1024 * 1024 
#     MAX_OTHER_FILES_SIZE = 5 * 1024 * 1024      

#     def validate_ceo_national_card(self, value):
#         if value.size > self.MAX_CEO_CARD_SIZE:
#             raise serializers.ValidationError("حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد")
#         return value

#     def validate_activity_license(self, value):
#         if value.size > self.MAX_OTHER_FILES_SIZE:
#             raise serializers.ValidationError("حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد")
#         return value

#     def validate_industryselection(self, value):
#         if len(value) > 3:
#             raise serializers.ValidationError("حداکثر 3 صنف می‌توانید انتخاب کنید")
#         return value
        
#     class Meta:
#         model = BuyerReal
#         fields = [
#             "economic_number",
#             "business_category",
#             "business_fields",
#             "ceo_national_card",
#             "activity_license",
#         ]

# class BuyerRealContactInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BuyerLegal
#         fields = [
#             "phone_number", 
#             "phone_fixed", 
#             "province", 
#             "city",
#             "postal_code", 
#             "office_address",
#             "has_warehouse", 
#             "warehouse_address"
#         ]

#     def validate(self, data):
#         if data.get("has_warehouse") and not data.get("warehouse_address"):
#             raise serializers.ValidationError({"warehouse_address": "در صورت داشتن انبار، وارد کردن آدرس آن الزامی است"})
#         return data        

# class FinalApprovalOfBuyerRealSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BuyerLegal
#         fields = [
#             "company_name",
#             "national_id",
#             "registration_number",
#             "ceo_full_name",
#             "ceo_national_code",
#             "marketer_code",
#             "buyer_types",
#             "phone_number", 
#             "phone_fixed", 
#             "province", 
#             "city",
#             "postal_code", 
#             "office_address",

#         ]

