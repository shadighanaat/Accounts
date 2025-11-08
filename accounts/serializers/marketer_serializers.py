from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from ..validators import validate_iranian_phone
from ..models import Marketer

class SendOTPMarketerSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11,
        help_text="شماره موبایل معتبر (مثلاً 09123456789)",
        label="شماره موبایل",
        validators=[validate_iranian_phone]
        )
    remember_me = serializers.BooleanField(default=False)

class VerifyOTPMarketerSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    otp_code = serializers.CharField()


class LoginWithPasswordMarketerSerializer(serializers.Serializer):
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

    def validate_password(self, password):
       
        conditions = [
         (len(password) >= 7, 'پسورد باید حداقل 7 کاراکتر باشد'),
         (re.search(r'[A-Za-z]', password), 'پسورد باید حداقل شامل یک حرف باشد'),
         (re.search(r'[0-9]', password), 'پسورد باید حداقل شامل یک عدد باشد'),
         (len([char for char in password if char.isalnum()]) >= 7, 'پسورد باید حداقل شامل 7 کاراکتر از ترکیب حروف و اعداد باشد')
    ]

        for condition, message in conditions:
            if not condition:
                raise ValidationError(message)

class RequestPasswordResetMarketerSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("کاربری با این ایمیل یافت نشد")
        return value


class VerifyOTPEmailMarketerSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    otp_code = serializers.CharField()


class ResetPasswordMarketerSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    new_password = serializers.CharField(min_length=7)

    def validate_password(self, password):
       
        conditions = [
         (len(password) >= 7, 'پسورد باید حداقل 7 کاراکتر باشد'),
         (re.search(r'[A-Za-z]', password), 'پسورد باید حداقل شامل یک حرف باشد'),
         (re.search(r'[0-9]', password), 'پسورد باید حداقل شامل یک عدد باشد'),
         (len([char for char in password if char.isalnum()]) >= 7, 'پسورد باید حداقل شامل 7 کاراکتر از ترکیب حروف و اعداد باشد')
    ]

        for condition, message in conditions:
            if not condition:
                raise ValidationError(message)
                
        return value    

class AcceptTermsSerializer(serializers.Serializer):
    accepted_terms = serializers.BooleanField(write_only=True)

    def validate_accepted_terms(self, value):
        if not value:
            raise serializers.ValidationError("برای ادامه ثبت‌ نام باید شرایط همکاری را بپذیرید")
        return value        

class MarketerSignupSerializer(serializers.ModelSerializer):
    MAX_CEO_CARD_SIZE = 2 * 1024 * 1024 * 1024 
    MAX_OTHER_FILES_SIZE = 5 * 1024 * 1024      

    def validate_picture_national_card(self, value):
        if value.size > self.MAX_CEO_CARD_SIZE:
            raise serializers.ValidationError("حجم کارت ملی مدیرعامل نباید بیشتر از 2 گیگابایت باشد")
        return value

    def validate_Marketing_cooperation_agreement(self, value):
        if value.size > self.MAX_OTHER_FILES_SIZE:
            raise serializers.ValidationError("حجم مجوز فعالیت نباید بیشتر از 5 مگابایت باشد")
        return value

    class Meta:
        model = Marketer
        fields =[
            "full_name",
            "phone_number",
            "national_code",
            "province",
            "city",
            "email",
            "picture_national_card",
            "Marketing_cooperation_agreement",
        ]        


class FinalapprovalofMarketer(serializers.ModelSerializer): 
    class Meta:
        model = Marketer
        fields = [
           "full_name",
           "national_code",
           "phone_number",
           "province",
           "city",
           "email"
]                 