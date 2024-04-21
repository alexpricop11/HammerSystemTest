from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers

from user.models import UserProfile


class SendCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class VerifyCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code_auth = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['invite_code']


