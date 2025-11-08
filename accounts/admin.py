from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

@admin.register(models.CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    ordering = ('-date_joined',)
    search_fields = ('phone_number', 'username', 'email')
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password', 'username', 'email')}),
        ('دسترسی‌ها', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('date_joined',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'username', 'email',  'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

@admin.register(models.Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'province')
    list_filter = ('province',)
    search_fields = ('name',)


@admin.register(models.SellerType)
class SellerTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',)

@admin.register(models.IndustryCategory)
class IndustryCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',)

@admin.register(models.LegalSeller)
class SellerLegalAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'manager_full_name',
        'company_name', 
        'phone_number',
        'province', 
        'city',
        'is_verified',
        'accepted_terms', 
        'created_at', 
        'updated_at'
        )
    list_filter = ('company_name','accepted_terms', 'is_verified', 'created_at')
    search_fields = ('store_name', 'phone_number', 'user__user__phone_number')
    list_editable = ('is_verified',)
    readonly_fields = ('created_at', 'updated_at', 'national_card_uploaded_at', 'announcement_uploaded_at', 'business_license_uploaded_at')


@admin.register(models.RealSeller)
class SellerRealAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'province', 
        'city',
        'shop_name', 
        'phone_number',
        'is_verified', 
        'accepted_terms',
        'created_at', 
        'updated_at'
        )  
    list_filter = ('shop_name', 'accepted_terms', 'is_verified', 'created_at')
    search_fields = ('shop_name', 'phone_number', 'user__user__phone_number')
    list_editable = ('is_verified',)
    readonly_fields = ('created_at', 'updated_at', 'national_id_card_uploaded_at', 'business_license_uploaded_at')



@admin.register(models.Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'phone_number', 'accepted_terms']
    search_fields = ['full_name', 'phone_number', 'user__username', 'user__email']
    list_filter = ['accepted_terms']
    readonly_fields = ['user']

@admin.register(models.BuyerType)
class BuyerTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'title']
    search_fields = ['code', 'title']

@admin.register(models.BuyerCategory)
class BuyerCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(models.BusinessField)
class BusinessFieldAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(models.BuyerLegal)
class BuyerLegalAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'company_name', 'national_id', 'registration_number', 'ceo_full_name', 'is_verified']
    search_fields = ['company_name', 'national_id', 'registration_number', 'ceo_full_name', 'buyer__full_name']
    list_filter = ['is_verified', 'business_category']
    readonly_fields = [
        'national_card_uploaded_at',
        'announcement_uploaded_at',
        'business_license_uploaded_at',
    ]
    fieldsets = (
        (None, {
            'fields': ('buyer', 'company_name', 'national_id', 'registration_number', 'ceo_full_name', 'ceo_national_code', 'phone_number', 'phone_fixed', 'province', 'city', 'postal_code', 'office_address', 'is_verified', 'accepted_terms')
        }),
        ('اطلاعات بازاریاب', {
            'fields': ('marketer_code',),
            'classes': ('collapse',),
        }),
        ('کسب‌وکار', {
            'fields': ('buyer_types', 'business_category', 'business_fields', 'economic_number')
        }),
        ('بارگذاری مدارک', {
            'fields': ('ceo_national_card', 'national_card_uploaded_at', 'last_establishment_announcement', 'announcement_uploaded_at', 'activity_license', 'business_license_uploaded_at')
        }),
    )

@admin.register(models.BuyerReal)
class BuyerRealAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'full_name', 'store_name', 'national_code', 'birth_date', 'phone_number', 'is_verified']
    search_fields = ['full_name', 'store_name', 'national_code', 'buyer__full_name']
    list_filter = ['is_verified', 'business_category']
    readonly_fields = [
        'national_id_card_uploaded_at',
        'business_license_uploaded_at',
    ]
    fieldsets = (
        (None, {
            'fields': ('buyer', 'store_name', 'full_name', 'national_code', 'birth_date', 'phone_number', 'phone_fixed', 'province', 'city', 'postal_code', 'office_address', 'is_verified', 'accepted_terms')
        }),
        ('اطلاعات بازاریاب', {
            'fields': ('marketer_code',),
            'classes': ('collapse',),
        }),
        ('کسب‌وکار', {
            'fields': ('buyer_types', 'business_category', 'business_fields', 'economic_number')
        }),
        ('بارگذاری مدارک', {
            'fields': ('ceo_national_card', 'national_id_card_uploaded_at', 'activity_license', 'business_license_uploaded_at')
        }),
    )

@admin.register(models.Marketer)
class MarketerAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'phone_number',
        'national_code',
        'province',
        'city',
        'email',
        'is_verified',
        'is_active',
        'accepted_terms',
        'created_at',
        'updated_at'
    )
    list_filter = ('province', 'city', 'is_verified', 'is_active', 'accepted_terms', 'created_at')
    search_fields = ('full_name', 'phone_number', 'national_code', 'email')
    readonly_fields = ('created_at', 'updated_at', 'national_card_uploaded_at', 'cooperation_agreement_uploaded_at')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    filter_horizontal = ('groups', 'user_permissions',)
    fieldsets = (
        ('اطلاعات شخصی', {
            'fields': (
                'full_name',
                'phone_number',
                'email',
                'national_code',
                'province',
                'city',
                'is_active',
            )
        }),
        ('احراز هویت', {
            'fields': (
                'picture_national_card',
                'national_card_uploaded_at',
                'Marketing_cooperation_agreement',
                'cooperation_agreement_uploaded_at',
                'is_verified',
            )
        }),
        ('سایر', {
            'fields': (
                'accepted_terms',
                'created_at',
                'updated_at',
            )
        }),
    )
    def save_model(self, request, obj, form, change):
        if 'picture_national_card' in form.changed_data:
            obj.national_card_uploaded_at = timezone.now()
        if 'Marketing_cooperation_agreement' in form.changed_data:
            obj.cooperation_agreement_uploaded_at = timezone.now()
        super().save_model(request, obj, form, change)