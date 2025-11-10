# ماژول Accounts

این مخزن نسخه‌ی ارائه‌ای از ماژول **Accounts** هست که برای نمونه‌کار آماده کردم. این بخش فقط مربوط به سیستم اکانت‌هاست و به‌صورت مستقل گذاشته شده تا روند احراز هویت و ثبت‌نام در پروژه را به شکل واضح و قابل ارائه نشان دهد.

---

## توضیح کوتاه

این ماژول با **Django REST Framework** پیاده‌سازی شده و سعی کردم ساختار کد تمیز، قابل فهم و استاندارد باشد. هدف اصلی این بخش، مدیریت ثبت‌نام چندمرحله‌ای و ورود کاربران با OTP است.

### قابلیت‌ها

* ورود کاربر با **OTP** (ارسال و تأیید کد)
* ثبت‌نام **خریدار (Buyer)** و **فروشنده (Seller)** به‌صورت مرحله‌ای
* امکان ثبت‌نام و ورود **بازاریاب (Marketer)**
* تست‌ها برای مدل‌ها، سریالایزرها و ویوها نوشته شده
* امکان اجرا با **Docker** به‌صورت مستقل

---

## تکنولوژی‌ها

* Python
* Django
* Django REST Framework (DRF)
* PostgreSQL (قابل پیکربندی)
* Docker & Docker Compose

---

## راه‌اندازی سریع

### با Docker Compose

```bash
git clone <repo-link>
cd Accounts
cp .env.example .env
# مقادیر داخل .env را تنظیم کنید
docker-compose up --build
```

### بدون Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## اجرای تست‌ها

تمام تست‌ها در پوشهٔ `tests/` قرار دارند. برای اجرا:

```bash
python manage.py test
# یا در صورت نصب pytest
pytest
```

---

## نمونه Endpoints



POST /api/accounts/otp/send/     >>>    ارسال کد OTP برای ورود        
POST /api/accounts/otp/verify/     >>>    تأیید کد و ورود               
POST /api/accounts/register/buyer/  >>>  ثبت‌نام خریدار (چندمرحله‌ای)  
POST /api/accounts/register/seller/ >>>  ثبت‌نام فروشنده (چندمرحله‌ای) 
POST /api/accounts/register/marketer/  >>> ثبت‌نام بازاریاب              
GET /api/accounts/profile/    >>>    مشاهده/ویرایش پروفایل         

---

## وضعیت پروژه

* کد آماده‌ی استفاده یا ادغام در پروژه‌های دیگر است
* تست‌ها و Docker کانفیگ شده‌اند
* تنها کافیست اطلاعات محیطی و سرویس پیامک تنظیم شود

--

