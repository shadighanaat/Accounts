# from django.db import models
# from django.contrib.auth.models import User
# from django.conf import settings
# from django.utils import timezone
# from datetime import timedelta
# from django.contrib.auth import get_user_model

# User = get_user_model()

# def validate_supplier_code(value):
#     if value == "S120":
#         raise ValidationError("کد فروشنده نباید با کد سایت یکسان باشد.")


# def validate_national_id_card(value):
#     file_extension = value.name.split('.')[-1].lower()
#     if file_extension not in ['jpg', 'jpeg', 'png', 'pdf']:
#         raise ValidationError("فقط فایل‌های jpg، jpeg، png و pdf مجاز هستند.")

# class Category(models.Model):
#     name = models.CharField(
#         max_length=100, 
#         unique=True, 
#         verbose_name= "نام دسته‌بندی"
#         )  
#     description = models.TextField(
#         blank=True, null=True, 
#         verbose_name= "توضیحات"
#         )  
#     processing_fee_percentage = models.DecimalField(
#         max_digits=5, decimal_places=2, 
#         verbose_name="درصد کارمزد فروشنده"
#     )
#     minimum_processing_fee = models.DecimalField(
#         max_digits=10, decimal_places=2, 
#         verbose_name="حداقل کارمزد ثابت"
#     )
#     commission_percentage = models.DecimalField(
#         max_digits=5, decimal_places=2, 
#         verbose_name="درصد پورسانت"
#     )

#     def __str__(self):
#         return self.name


# class Supplier(models.Model):
#     user = models.OneToOneField(
#         User, on_delete=models.CASCADE,
#         verbose_name= "فروشنده"
#         )
#     email = models.EmailField(
#         unique=True, verbose_name = "ایمیل"
#         )
#     economic_code = models.CharField(
#         max_length=20, verbose_name = "شماره اقتصادي"
#         )
#     referrer_code = models.CharField(
#         max_length=20, 
#         blank=True, null=True, 
#         verbose_name = "کد ارجاع دهنده"
#         )
#     supplier_code = models.CharField(
#         max_length=10,
#         unique=True,
#         blank=True,
#         validators=[validate_supplier_code], 
#         verbose_name = "کد فروشنده"
#         )
#     product_category = models.ManyToManyField(
#         Category, 
#         blank=True, 
#         verbose_name = "دسته بندی محصول"
#         )
#     website_url = models.URLField(
#         blank=True, null=True, 
#         verbose_name = "آدرس وب سایت"
#         )
#     company_registration_number = models.CharField(
#         max_length=50, blank=True, null=True, verbose_name = "شماره ثبت شرکت"
#         )  
#     contract_number = models.CharField(
#         max_length=50, verbose_name = "شماره قرارداد حق العملكاري"
#         ) 
#     bank_account_number = models.CharField(
#         max_length=20, verbose_name = "شماره شبا جهت تسويه حساب"
#         ) 
    
#     business_card_upload = models.FileField(
#         upload_to='supplier_business_cards/', 
#         validators=[validate_national_id_card],
#         verbose_name = "آپلود كارت ملي مدير مسئول"  
#     )
#     is_info_verified = models.BooleanField(
#         default=False, 
#         verbose_name = "تاييد قرارداد ﻫمكاري"
#         )  
#     registration_date_created = models.DateTimeField(
#         auto_now_add=True, 
#         verbose_name = "تاریخ ثبت نام"
#         )
#     registration_date_modified = models.DateTimeField(
#         auto_now=True, 
#         verbose_name = "تاریخ آخرین تغییر ثبت نام"
#         )
#     is_active = models.BooleanField(
#         default=True, 
#         verbose_name="فروش فعال / غیر فعال"
#         )
#     is_active_changed_at = models.DateTimeField(
#         null=True, blank=True, 
#         verbose_name = "تاریخ تغییر فعال"
#         )
#     total_balance = models.DecimalField(
#         max_digits=12, 
#         decimal_places=2, default=0,
#         verbose_name="موجودی کل"
#         )
#     withdrawable_balance = models.DecimalField(
#         max_digits=12, 
#         decimal_places=2, default=0,
#         verbose_name="موجودی قابل برداشت"
#         )
#     withdrawal_delay_days = models.PositiveIntegerField(
#         default=7,  # مثلاً ۷ روز تا تبدیل به موجودی قابل برداشت
#         verbose_name="مدت انتظار برای برداشت (روز)"
#         )
#     def save(self, *args, **kwargs):
#         if not self.supplier_code:
#             latest_supplier = (
#                 Supplier.objects
#                 .exclude(supplier_code__in=settings.SITE_SUPPLIER_CODE)
#                 .order_by('-id')
#                 .first()
#             )
#             next_code = int(latest_supplier.supplier_code[1:]) if latest_supplier else settings.SUPPLIER_CODE_START - 1
#             self.supplier_code = f"S{next_code + 1}"

#         if not self.website_url:
#             self.website_url = f"https://ciraf.com/shop/{self.supplier_code}"

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.user} ({self.supplier_code})"


# class SalesEmployee(models.Model):
#     supplier = models.ForeignKey(
#         Supplier, on_delete=models.CASCADE, 
#         related_name="employees", 
#         verbose_name= "فروشنده"
#         )
#     user = models.OneToOneField(
#         User, on_delete=models.CASCADE, 
#         verbose_name="حساب کاربری کارمند فروش"
#         )
#     can_view_orders = models.BooleanField(
#         default=False, 
#         verbose_name="دسترسی به سفارشات"
#         )
#     can_manage_products = models.BooleanField(
#         default=False, 
#         verbose_name="مدیریت محصولات"
#         )
#     can_view_finances = models.BooleanField(
#         default=False, 
#         verbose_name="دسترسی به مالیات‌ها"
#         )
#     can_edit_profile = models.BooleanField(
#         default=False, 
#         verbose_name="ویرایش پروفایل"
#         )
#     created_at = models.DateTimeField(
#         auto_now_add=True, 
#         verbose_name="زمان ساخت"
#         )

#     def __str__(self):
#         return f"{self.user.get_full_name()} - {self.supplier.name}"

#     class Meta:
#         verbose_name = "کارمند فروش"
#         verbose_name_plural = "کارمندان فروش"


# class SalesEmployeePhone(models.Model):
#     supplier = models.ForeignKey(
#         Supplier, on_delete=models.CASCADE, 
#         related_name="employee_phones", 
#         verbose_name="فروشنده")
#     phone_number = models.CharField(
#         max_length=15, 
#         verbose_name="شماره تلفن"
#         )
#     employee = models.ForeignKey(
#         SalesEmployee, 
#         on_delete=models.CASCADE, 
#         related_name="phones", 
#         verbose_name="کارمند فروش"
#         )
#     is_primary = models.BooleanField(
#         default=True, 
#         verbose_name="شماره اصلی"
#         )

#     def __str__(self):
#         return self.phone_number

#     class Meta:
#         verbose_name = "شماره تلفن کارمند"
#         verbose_name_plural = "شماره‌های تلفن کارمندان"
# class Product(models.Model):
#     name = models.CharField(
#         max_length=255,
#         verbose_name = "نام محصول"
#         ) 
#     description = models.TextField(
#         blank=True, null=True, 
#         verbose_name = "توضیحات محصول"
#         ) 
#     supplier = models.ForeignKey(
#         'Supplier', 
#         on_delete=models.CASCADE, 
#         verbose_name = "فروشنده محصول"
#         ) 
#     category = models.ForeignKey(
#         Category, on_delete=models.CASCADE, 
#         verbose_name="دسته‌بندی"
#         )    
#     warranty = models.CharField(
#         max_length=255,
#         blank=True, null=True, 
#         verbose_name="گارانتی"
#         )  
#     delivery_time_days = models.PositiveIntegerField(
#         blank=True, null=True, 
#         verbose_name="زمان تحویل توسط فروشنده (روز)"
#         )
#     additional_notes = models.TextField(
#         blank=True, null=True, 
#         verbose_name="سایر نکات فروشنده"
#         )   
#     created_at = models.DateTimeField(
#         auto_now_add=True, 
#         verbose_name = "تاریخ ایجاد محصول"
#         ) 
#     updated_at = models.DateTimeField(
#         auto_now=True, 
#         verbose_name="تاریخ ایجادآخرین محصول"
#         )

#     def __str__(self):
#         return self.name

#     def get_price_for_quantity(self, quantity):
#         return self.prices.filter(
#             min_quantity__lte=quantity,
#             max_quantity__gte=quantity
#         ).order_by('min_quantity').first()

#     def get_discounted_price_for_quantity(self, quantity):
#         tier = self.get_price_for_quantity(quantity)
#         if not tier:
#             return None
#         now = timezone.now()
#         discount = self.discounts.filter(
#             valid_from__lte=now, valid_until__gte=now
#         ).first()
#         if discount:
#             return tier.price * (1 - discount.discount_percentage / 100)
#         return tier.price  

#     def get_total_delivery_time(self):
#         ciraf_processing_time = 2  #day
#         if self.delivery_time_days:
#             return ciraf_processing_time + self.delivery_time_days
#         return ciraf_processing_time   

#     def get_estimated_delivery_date(self):
#         total_days = self.get_total_delivery_time()
#         return timezone.now().date() + timedelta(days=total_days)


# class ProductPrice(models.Model):
#     product = models.ForeignKey(
#         Product, related_name='prices', 
#         on_delete=models.CASCADE,
#         verbose_name = "محصول"
#         )
#     min_quantity = models.PositiveIntegerField(
#         verbose_name = "حداقل تعداد فروش"
#         ) 
#     max_quantity = models.PositiveIntegerField(
#         verbose_name = "حداکثر تعداد فروش"
#         )  
#     price = models.DecimalField(
#     max_digits=10, decimal_places=2, 
#     verbose_name = "قیمت فروش"
#        )  

#     def __str__(self):
#         return f"Price for {self.product.name} from {self.min_quantity} to {self.max_quantity}"

#     def get_discounted_price(self):
#         now = timezone.now()
#         active_discount = self.product.discounts.filter(
#             valid_from__lte=now, valid_until__gte=now
#         ).first()
#         if active_discount:
#             return self.price * (1 - active_discount.discount_percentage / 100)
#         return self.price

# class Discount(models.Model):
#     product = models.ForeignKey(
#         Product, related_name='discounts', 
#         on_delete=models.CASCADE, 
#         verbose_name = "محصول"
#         )
#     discount_percentage = models.DecimalField(
#         max_digits=5, decimal_places=2, 
#         verbose_name = "درصد تخفیف"
#         ) 
#     valid_from = models.DateTimeField(
#         verbose_name = "تاریخ شروع تخفیف"
#         )  
#     valid_until = models.DateTimeField(
#         verbose_name = "تاریخ پایان تخفیف"
#         )  

#     def __str__(self):
#         return f"{self.discount_percentage}% discount for {self.product.name}"

# class ProductOffering(models.Model):
#     product = models.ForeignKey(
#         Product, on_delete=models.CASCADE, 
#         related_name='offerings', 
#         verbose_name="محصول"
#         )
#     supplier = models.ForeignKey(
#         'Supplier', on_delete=models.CASCADE, 
#         verbose_name="فروشنده"
#         )
#     price = models.DecimalField(
#         max_digits=10, decimal_places=2, 
#         verbose_name="قیمت"
#         )
#     warranty = models.CharField(
#         max_length=255, 
#         blank=True, null=True, 
#         verbose_name="گارانتی"
#         )
#     delivery_time = models.PositiveIntegerField(
#         verbose_name="زمان تحویل (روز)"
#         )
#     product_code = models.CharField(
#         max_length=100, 
#         blank=True, null=True,
#         verbose_name="شناسه کالا"
#         )
#     additional_notes = models.TextField(
#         blank=True, null=True, 
#         verbose_name="نکات اضافی"
#         )
#     is_ready_for_delivery = models.BooleanField(
#         default=False, 
#         verbose_name="محصول آماده تحویل است"
#         )
#     serial_number = models.CharField(
#         max_length=255, 
#         blank=True, null=True, 
#         verbose_name="سریال محصول"
#         ) 

#     def __str__(self):
#         return f"{self.product.name} - {self.supplier.name}"

#     def send_notification_to_admin(self):
#         # اینجا می‌توانید کدی برای ارسال نوتیفیکیشن به مدیر سایت بنویسید.
#         # مثلا از سیستم پیام‌رسانی یا نوتیفیکیشن‌های داخلی استفاده کنید.
#         pass

#     def mark_as_ready_for_delivery(self):
#         self.is_ready_for_delivery = True
#         self.save()
#         self.send_notification_to_admin()  

#     def calculate_seller_fee(self):
#         category = self.product.category
#         fee_percentage = category.processing_fee_percentage
#         minimum_fee = category.minimum_processing_fee
#         fee = (self.price * fee_percentage / 100)
#         return max(fee, minimum_fee)  

#     def calculate_commission(self):
#         category = self.product.category
#         commission_percentage = category.commission_percentage
#         return self.price * commission_percentage / 100

#     def calculate_final_price_for_customer(self):
#         seller_fee = self.calculate_seller_fee()
#         commission = self.calculate_commission()
#         return self.price + commission + seller_fee  

#     def total_delivery_time(self):
#         ciraf_processing_time = 3
#         return self.delivery_time + ciraf_processing_time


# class Shipment(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'در انتظار آماده‌سازی'),
#         ('ready', 'آماده ارسال'),
#         ('shipped', 'ارسال شده'),
#         ('delivered', 'تحویل داده شده'),
#         ('returned', 'مرجوع شده'),
#     ]

#     order = models.ForeignKey(
#         'Order', on_delete=models.CASCADE, 
#         verbose_name="سفارش"
#         )
#     offering = models.ForeignKey(
#         'ProductOffering', 
#         on_delete=models.CASCADE, 
#         verbose_name="پیشنهاد فروشنده"
#         )
#     quantity = models.PositiveIntegerField(
#         verbose_name="تعداد"
#         )
#     serial_number = models.CharField(
#         max_length=255, 
#         blank=True, null=True, 
#         verbose_name="سریال کالا"
#         )
#     tracking_code = models.CharField(
#         max_length=100, 
#         blank=True, null=True, 
#         verbose_name="کد رهگیری"
#         )
#     status = models.CharField(
#         max_length=20, 
#         choices=STATUS_CHOICES, 
#         default='pending', 
#         verbose_name="وضعیت ارسال"
#         )
#     shipped_at = models.DateTimeField(
#         blank=True, null=True, 
#         verbose_name="تاریخ ارسال"
#         )
#     delivered_at = models.DateTimeField(
#         blank=True, null=True, 
#         verbose_name="تاریخ تحویل"
#         )

#     delivery_confirmed_by_admin = models.BooleanField(
#         default=False, 
#         verbose_name="تأییدیه تحویل توسط نماینده"
#         )

#     def mark_as_ready(self):
#         self.status = 'ready'
#         self.save()

#     def mark_as_shipped(self):
#         self.status = 'shipped'
#         self.shipped_at = timezone.now()
#         self.save()

#     def mark_as_delivered(self):
#         self.status = 'delivered'
#         self.delivered_at = timezone.now()
#         self.delivery_confirmed_by_admin = True
#         self.save()

#     def mark_as_returned(self):
#         self.status = 'returned'
#         self.save()

#     def __str__(self):
#         return f"{self.offering.product.name} - {self.order.id}"

#     @staticmethod
#     def count_pending_shipments_for_supplier(supplier):
#         return Shipment.objects.filter(
#             offering__supplier=supplier,
#             status='pending'
#         ).count()
