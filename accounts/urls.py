from rest_framework.routers import DefaultRouter

# ویوهای احراز هویت
from .views.auth_views import AuthViewSet

# ویوهای فروشنده
from .views.seller_views import (
    AcceptTermsViewSet,
    LegalSellerViewSet,
    LegalBusinessInfoViewSet,
    ContactInfoLegalViewSet,
    LegalSellerOTPVerificationViewSet,
    RealSellerViewSet,
    RealPersonBusinessInfoViewSet,
    ContactInfoRealViewSet,
    RealSellerOTPVerificationViewSet,
)

# ویوهای خریدار
from .views.buyer_views import (
    BuyerRegisterOrLoginViewSet,
    BuyerAcceptTermsViewSet,
    BuyerLegalViewSet,
    BuyerLegalBusinessInfoViewSet,
    BuyerLegalContactInfoViewSet,
    BuyerLegalOTPVerificationViewSet,
    BuyerRealViewSet,
    BuyerRealBusinessInfoViewSet,
    BuyerRealContactInfoViewSet,
    BuyerRealOTPVerificationViewSet,
)

#ویوهای یازاریاب 
from .views.marketer_views import (
    MarketerAuthViewSet,
    MarketerAcceptTermsViewSet,
    MarketerSignupViewSet,
    MarketerOTPVerificationViewSet,
)

router = DefaultRouter()

# احراز هویت
router.register(r'auth', AuthViewSet, basename='auth')

#فروشنده - حقوقی و حقیقی
router.register(r'seller/accept-terms', AcceptTermsViewSet, basename='seller-accept-terms')
router.register(r'seller/legal', LegalSellerViewSet, basename='legal-seller')
router.register(r'seller/legal/business', LegalBusinessInfoViewSet, basename='business-legal-seller')
router.register(r'seller/legal/contact', ContactInfoLegalViewSet, basename='contact-legal-seller')
router.register(r'seller/legal/finallegalapproval', LegalSellerOTPVerificationViewSet, basename='finalapproval-legal-seller')

router.register(r'seller/real', RealSellerViewSet, basename='real-seller')
router.register(r'seller/real/business', RealPersonBusinessInfoViewSet, basename='business-real-seller')
router.register(r'seller/real/contact', ContactInfoRealViewSet, basename='contact-real-seller')
router.register(r'seller/real/finalrealapproval', RealSellerOTPVerificationViewSet, basename='finalapproval-real-seller')

#خریدار - حقوقی و حقیقی
router.register(r'buyer', BuyerRegisterOrLoginViewSet, basename='buyer')

router.register(r'buyer/accept-terms', BuyerAcceptTermsViewSet, basename="buyer-accept-terms")
router.register(r'buyer/legal', BuyerLegalViewSet, basename="legal-buyer")
router.register(r'buyer/legal/business', BuyerLegalBusinessInfoViewSet, basename="business-legal-buyer")
router.register(r'buyer/legal/contact', BuyerLegalContactInfoViewSet, basename='contact-legal-buyer')
router.register(r'buyer/legal/finallegalapproval', BuyerLegalOTPVerificationViewSet, basename='finalapproval-legal-buyer')

router.register(r'buyer/real', BuyerRealViewSet, basename='real-buyer')
router.register(r'buyer/real/business', BuyerRealBusinessInfoViewSet, basename='business-real-buyer')
router.register(r'buyer/real/contact', BuyerRealContactInfoViewSet, basename='contact-real-buyer')
router.register(r'buyer/real/finalrealapproval', BuyerRealOTPVerificationViewSet, basename='finalapproval-real-buyer')

#بازاریاب
router.register(r'marketer/auth', MarketerAuthViewSet, basename='marketer-auth')
router.register(r'marketer/accept-terms', MarketerAcceptTermsViewSet, basename='marketer-accept-terms')
router.register(r'marketer/signup', MarketerSignupViewSet, basename='marketer-signup')
router.register(r'marketer/finalrealapproval', MarketerOTPVerificationViewSet, basename='finalapproval-marketer')

urlpatterns = router.urls
