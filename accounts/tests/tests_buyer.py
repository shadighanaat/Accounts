from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.core.cache import cache
import uuid
import time

from accounts.models import CustomUser, Buyer
from accounts.throttles import OTPThrottle  # حتما این را ایمپورت کن

class BuyerRegisterOrLoginViewSetTest(APITestCase):

    def setUp(self):
        CustomUser.objects.all().delete()
        Buyer.objects.all().delete()
        cache.clear()

        self.phone_number = "09123456789"
        self.full_name = "Test Buyer"
        self.otp_token = str(uuid.uuid4())

        self.user = CustomUser.objects.create_user(phone_number=self.phone_number)
        cache.set(self.otp_token, self.user.id, timeout=300)
        cache.set(f"otp:{self.phone_number}", "123456", timeout=300)

    @patch('accounts.utils.OTPService.send')
    def test_register_new_user(self, mock_send_otp):
        mock_send_otp.return_value = None
        url = reverse('buyer-register')
        data = {
            "phone_number": "09123456790",
            "full_name": "New User",
            "remember_me": False
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertIn("کاربر جدید ساخته شد", response.data["detail"])
        self.assertTrue(CustomUser.objects.filter(phone_number="09123456790").exists())
        self.assertTrue(Buyer.objects.filter(user__phone_number="09123456790").exists())

    @patch('accounts.utils.OTPService.send')
    def test_register_existing_user(self, mock_send_otp):
        mock_send_otp.return_value = None
        url = reverse('buyer-register')
        data = {
            "phone_number": self.phone_number,
            "full_name": self.full_name
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("کاربر قبلا ثبت‌نام کرده است", response.data["detail"])

    @patch('accounts.utils.OTPService.send')
    def test_send_otp(self, mock_send_otp):
        mock_send_otp.return_value = None
        url = reverse('buyer-send-otp')
        data = {"phone_number": self.phone_number}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertIn("کد ورود به موبایل شما ارسال شد", response.data["detail"])
        
    @patch('accounts.utils.OTPService.is_otp_valid', return_value=True)
    def test_verify_otp_success(self, mock_is_otp_valid):
        cache.set(f"otp:{self.phone_number}", "123456", timeout=300)
        
        url = reverse('buyer-verify-otp')
        data = {
            "otp_token": self.otp_token,
            "otp_code": "123456"  # اصلاح شد: با مقدار cache هماهنگ شد
        }

        response = self.client.post(url, data)
        print("Response data:", response.data) 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "کد تایید با موفقیت انجام شد")

    def test_verify_otp_invalid_token(self):
        url = reverse('buyer-verify-otp')
        data = {
            "otp_token": "invalid-token",
            "otp_code": "123456"
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "توکن منقضی یا نامعتبر است")

    def test_verify_otp_wrong_code(self):
        url = reverse('buyer-verify-otp')
        data = {
            "otp_token": self.otp_token,
            "otp_code": "000000"
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "کد وارد شده اشتباه است")

    @patch('accounts.utils.OTPService.is_otp_valid', return_value=False)
    def test_verify_otp_failed_attempts_block(self, mock_otp_valid):
        url = reverse('buyer-verify-otp')

        for i in range(5):
            data = {
                "otp_token": self.otp_token,
                "otp_code": "wrongcode"
            }
            response = self.client.post(url, data)
            if i < 4:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("کد وارد شده اشتباه است", response.data["detail"])
            else:
                self.assertEqual(response.status_code, 429)
                self.assertIn("بیش از حد تلاش کردید", response.data["detail"])

        # تکرار بعد از بلاک شدن
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 429)
        self.assertIn("بیش از حد تلاش کردید", response.data["detail"])

    @patch('accounts.utils.OTPService.send')
    def test_send_otp_throttle(self, mock_send_otp):
        mock_send_otp.return_value = None
        url = reverse('buyer-send-otp')
        data = {"phone_number": self.phone_number}

        # استفاده دقیق از OTPThrottle برای گرفتن کلید صحیح
        throttle = OTPThrottle()
        fake_request = self.client.post(url, data)
        cache_key = throttle.get_cache_key(fake_request)
        cache.set(cache_key, {'blocked_until': time.time() + 60}, timeout=60)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 429)
        self.assertIn("تعداد درخواست‌های شما محدود شده است", response.data["detail"])
