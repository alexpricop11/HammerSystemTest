from django.urls import path

from user.views import SendVerificationCode, VerifyCode, UserProfileView, PhoneInvited

urlpatterns = [
    path('send-code', SendVerificationCode.as_view()),
    path('verify-code', VerifyCode.as_view()),
    path('profile', UserProfileView.as_view()),
    path('phone-invited', PhoneInvited.as_view())
]
