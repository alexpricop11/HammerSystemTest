from django.contrib.auth import login
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserProfile
from .serializers import VerifyCodeSerializer, SendCodeSerializer, UserProfileSerializer
import random
import string
import time


class SendVerificationCode(APIView):
    """
        Отправляет код верификации на указанный номер телефона и сохраняет его в базу данных.
        Параметры запроса:
        - phone_number: номер телефона пользователя
        Ответ:
        - verification_code: сгенерированный код
        """
    serializer_class = SendCodeSerializer
    template_name = 'send_code.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            user_profile, created = UserProfile.objects.get_or_create(phone_number=phone_number)
            time.sleep(random.uniform(1, 2))
            verification_code = ''.join(random.choices(string.digits, k=4))
            user_profile.code_auth = verification_code
            user_profile.save()
            return render(request, 'code.html', {'verification_code': verification_code})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCode(APIView):
    """
        Проверяет введенный код верификации.
        Параметры запроса:
        - phone_number: номер телефона пользователя
        - code: введенный пользователем код
        Ответ:
        генерируется инвайт-код
        - message: сообщение о результате проверки
        """
    serializer_class = VerifyCodeSerializer
    template_name = 'verify_code.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            code_auth = serializer.validated_data.get('code_auth')
            user_profile = UserProfile.objects.filter(phone_number=phone_number, code_auth=code_auth)
            if user_profile.exists():
                user_profile = user_profile.first()
                login(request, user_profile)
                user_profile.invite_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                user_profile.save()
                response_data = {"message": "Пользователь успешно аутентифицирован и вошел в систему.",
                                 "result_type": "success"}
                return render(request, 'result_verify.html', response_data)
            else:
                response_data = {"message": "Ошибка аутентификации. Неверный код верификации или номер телефона.",
                                 "result_type": "danger"}
                return render(request, 'result_verify.html', response_data)
        else:
            return render(request, 'result_verify.html',
                          {"message": "Неверные данные в запросе.", "result_type": "danger"})


class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer
    template_name = 'invite_code.html'
    """
    Представление для управления профилем пользователя.
    возвращает активированный код приглашения пользователя, если таковой существует. В противном случае возвращает 
    сообщение о том, что пользователь еще не активировал ни один код приглашения.
    позволяет пользователю активировать код приглашения, который он вводит. Если код приглашения существует
    в базе данных, то он становится активным для данного пользователя. 
    Если пользователь уже активировал другой код приглашения ранее, то будет возвращено сообщение об ошибке. 
    Если введенный код приглашения не существует в базе данных, возвращается сообщение о невалидности кода приглашения.
    """

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        invite_code = request.data.get('invite_code')
        try:
            inviter_profile = UserProfile.objects.get(invite_code=invite_code)
        except UserProfile.DoesNotExist:
            response_data = {"message": "Введённый код приглашения недействителен."}
            return render(request, 'result_invite.html', response_data)
        user_profile = UserProfile.objects.get(phone_number=request.user.phone_number)
        if user_profile.invite_by:
            response_data = {"message": "Вы уже активировали код приглашения."}
            return render(request, 'result_invite.html', response_data)
        else:
            user_profile.invite_by = inviter_profile
            user_profile.save()
            response_data = {"message": "Текущий пользователь ассоциирован с пользователем, введшим код приглашения."}
            return render(request, 'result_invite.html', response_data)


class PhoneInvited(APIView):
    permission_classes = (IsAuthenticated,)
    template_name = 'phone_invated.html'

    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(phone_number=request.user.phone_number)
        except UserProfile.DoesNotExist:
            response_data = {"message": "Профиль пользователя не найден."}
            return render(request, self.template_name, response_data)

        except UserProfile.MultipleObjectsReturned:
            response_data = {"message": "Произошла ошибка. Свяжитесь с администратором."}
            return render(request, self.template_name, response_data)
        if user_profile.invite_by:
            inviter_id = user_profile.invite_by_id
            try:
                inviter_profile = UserProfile.objects.get(id=inviter_id)
            except UserProfile.DoesNotExist:
                response_data = {"message": "Профиль пригласившего пользователя не найден."}
                return render(request, self.template_name, response_data)
            response_data = {"invited_number": inviter_profile.phone_number}
            return render(request, self.template_name, response_data)
        else:
            response_data = {"message": "Вы не были приглашены никем."}
            return render(request, self.template_name, response_data)
