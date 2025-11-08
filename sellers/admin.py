# from django.contrib import admin
# from .models import Category, SalesEmployee, SalesEmployeePhone

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'processing_fee_percentage', 'minimum_processing_fee', 'commission_percentage']

# @admin.register(SalesEmployee)
# class SalesEmployeeAdmin(admin.ModelAdmin):
#     list_display = ('user', 'supplier', 'can_view_orders', 'can_manage_products', 'can_view_finances', 'can_edit_profile')
#     search_fields = ('user__username', 'user__email')

# @admin.register(SalesEmployeePhone)
# class SalesEmployeePhoneAdmin(admin.ModelAdmin):
#     list_display = ('supplier', 'employee', 'phone_number', 'is_primary')
#     search_fields = ('phone_number',)