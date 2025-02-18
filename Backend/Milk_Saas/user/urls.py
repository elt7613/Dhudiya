from django.urls import path
from .views import (
    UserRegistrationView, UserLoginView,
    ForgotPasswordView, ResetPasswordView,
    ApplyReferralCodeView, UserInfoView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('apply-referral/', ApplyReferralCodeView.as_view(), name='apply-referral'),
    path('info/', UserInfoView.as_view(), name='user-info'),
]