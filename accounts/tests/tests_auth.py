import time
from unittest.mock import patch
from rest_framework.test import APITestCase
from django.urls import reverse
from django.core.cache import cache
from django.test import override_settings
from accounts.models import CustomUser
import uuid


class AuthAPITestCase(APITestCase):

    def setUp(self):
        CustomUser.objects.all().delete()
        cache.clear()
        self.user = CustomUser.objects.create_user(
            phone_number="09123456789",
            username="shadi",
            password="testpass123"
        )
        self.otp_token = str(uuid.uuid4())
        cache.set(self.otp_token, self.user.id, timeout=300)
        cache.set(f"otp:{self.user.phone_number}", "123456", timeout=300)

    @patch('accounts.utils.send_sms')
    def test_send_otp(self, mock_send_sms):
        mock_send_sms.return_value = None
        url = reverse("auth-send-otp")
        data = {"phone_number": "09123456789"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("detail", response.data)

    @patch('accounts.utils.send_sms')
    def test_resend_otp(self, mock_send_sms):
        mock_send_sms.return_value = None
        url = reverse("auth-resend-otp")
        data = {"phone_number": "09123456789"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("detail", response.data)
    
    @patch('accounts.utils.OTPService.is_otp_valid', return_value=True)
    def test_verify_otp_success(self, mock_is_otp_valid): 
        url = reverse("auth-verify-otp")
        data = {
            "otp_token": self.otp_token,
            "otp_code": "123456",
            "remember_me": False
        }
        response = self.client.post(url, data)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)

    @override_settings(DEBUG=True)
    def test_verify_otp_invalid_token(self):
        url = reverse("auth-verify-otp")
        data = {
            "otp_token": "invalid-token",
            "otp_code": "123456"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_verify_otp_wrong_code(self):
        url = reverse("auth-verify-otp")
        data = {
            "otp_token": self.otp_token,
            "otp_code": "000000"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_login_with_password_success(self):
        self.user.set_password("Testpass123")
        self.user.save()
        url = reverse("auth-login-with-password")
        data = {
            "username": "shadi",
            "password": "Testpass123"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)

    def test_login_with_password_fail(self):
        url = reverse("auth-login-with-password")
        data = {
            "username": "shadi",
            "password": "wrongpass"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)

    def test_request_password_reset_success(self):
        CustomUser.objects.filter(phone_number='09123456790').delete()
        user = CustomUser.objects.create_user(email='test@example.com', phone_number='09123456790')
        url = reverse('auth-request-password-reset')
        response = self.client.post(url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('detail', response.data)

    def test_request_password_reset_invalid_email(self):
        url = reverse('auth-request-password-reset')
        response = self.client.post(url, {'email': 'nonexistent@example.com'})
        self.assertIn(response.status_code, [201, 400])

    @patch('accounts.utils.OTPService.is_otp_valid', return_value=True)
    def test_verify_otp_email_success(self, mock_otp_valid):
        CustomUser.objects.filter(phone_number='09123456791').delete()
        user = CustomUser.objects.create_user(email='test@example.com', phone_number='09123456791')
        otp_token = str(uuid.uuid4())
        cache.set(otp_token, user.id, timeout=300)

        url = reverse('auth-verify-otp-email')
        response = self.client.post(url, {
           'otp_token': otp_token,
            'otp_code': '123456'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('detail', response.data)

    @override_settings(DEBUG=True)
    def test_verify_otp_email_invalid_token(self):
        url = reverse('auth-verify-otp-email')
        response = self.client.post(url, {
            'otp_token': 'invalid-token',
            'otp_code': '123456'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_send_otp_throttle_blocked(self):
        CustomUser.objects.filter(phone_number='09123456792').delete()
        user = CustomUser.objects.create_user(phone_number='09123456792')
        url = reverse('auth-send-otp')
        cache_key = f"otp-throttle-{user.phone_number}"
        cache.set(cache_key, {'timestamps': [], 'failures': 0, 'blocked_until': time.time() + 60})

        response = self.client.post(url, {'phone_number': '09123456792'})
        self.assertEqual(response.status_code, 429)
