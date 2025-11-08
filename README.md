ماژول Accounts

این مخزن نسخه‌ی ارائه‌ای از ماژول Accounts هست که برای نمونه‌کار آماده کردم. این بخش فقط مربوط به سیستم اکانت‌هاست و به‌صورت مستقل گذاشته شده تا روند احراز هویت و ثبت‌نام در پروژه رو به شکل واضح و قابل‌ارائه نشان بده.

توضیح کوتاه

این ماژول با Django REST Framework پیاده‌سازی شده و سعی کردم ساختار کد تمیز، قابل فهم و استاندارد باشه.
هدف اصلی این بخش، مدیریت ثبت‌نام چندمرحله‌ای و ورود کاربران با OTP هست.

قابلیت‌ها

ورود کاربر با OTP (ارسال و تأیید کد)

ثبت‌نام خریدار (Buyer) و فروشنده (Seller) به‌صورت مرحله‌ای

امکان ثبت‌نام و ورود بازاریاب (Marketer)

تست‌ها برای مدل‌ها، سریالایزرها و ویوها نوشته شده

امکان اجرا با Docker به‌صورت مستقل
---

## تکنولوژی‌ها

* Python 
* Django
* Django REST Framework (DRF)
* PostgreSQL (قابل پیکربندی)
* Docker & Docker Compose

---

## راه‌اندازی سریع (Local / Docker)

با Docker Compose توصیه می‌کنم:
cd Accounts
cp .env.example .env
# تنظیم مقادیر داخل .env
docker-compose up --build

```

اگر Docker ندارید:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## اجرای تست‌ها

تمام تست‌ها در پوشهٔ `tests/` قرار گرفته‌اند. با یکی از این دستورات تست‌ها را اجرا کنید:

```bash
python manage.py test
# یا
pytest
```

---
نمونه Endpoints
مسیر	توضیح
POST /api/accounts/otp/send/	ارسال کد برای ورود
POST /api/accounts/otp/verify/	تأیید کد و ورود
POST /api/accounts/register/buyer/	ثبت‌نام خریدار (چندمرحله‌ای)
POST /api/accounts/register/seller/	ثبت‌نام فروشنده (چندمرحله‌ای)
POST /api/accounts/register/marketer مشاهده/ویرایش پروفایل

---
##وضعیت پروژه

کد آماده‌ی استفاده یا ادغام در پروژه‌های دیگر است

تست‌ها و Docker کانفیگ شده‌اند

فقط کافی‌ست اطلاعات محیطی و سرویس پیامک تنظیم شود

---

اگر می‌خواهید این README به انگلیسی هم داشته باشید یا می‌خواهید من نسخه‌ای که دقیقاً شبیهِ نوشتهٔ شما باشد بازنویسی کنم، بگو تا انجام دهم.
