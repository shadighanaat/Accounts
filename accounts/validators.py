from django.core.exceptions import ValidationError

def validate_iranian_phone(value):
    if not value.startswith('0') or len(value) != 11 or not value.isdigit():
        raise ValidationError('شماره موبایل باید 11 رقمی و با 0 شروع شود.')
