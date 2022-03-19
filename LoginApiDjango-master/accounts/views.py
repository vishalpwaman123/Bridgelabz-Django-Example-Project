import datetime

import jwt
from django.contrib.sites import requests
from django.core.cache import cache
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework_jwt.settings import api_settings
from urllib3.util import url
from .models import Register
from .serializers import (
    RegistrationSerializers,
    LoginSerializers,
    EmailSerializers,
    ResetSerializers,
)
from django.shortcuts import render, redirect
# Create your views here.
from django.views.decorators import cache
from django.views.generic import TemplateView
from rest_framework import settings, permissions, request
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from login.settings import EMAIL_HOST
from login.settings import SECRET_KEY
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
AUTH_ENDPOINT = "/api/token"


class Home(TemplateView):
    template_name = 'registration/index.html'


class Registration(GenericAPIView):
    serializer_class = RegistrationSerializers

    # def get(self, request):
    #     return render(request, 'registration/register.html')

    def post(self, request):
        if request.user.is_authenticated:
            return Response("your are already registred,please do login")
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        print(username)
        if len(password) < 4 or len(confirm_password) < 4:
            return Response("length of the password must be greater than 4")
        elif password != confirm_password:
            return Response("passwords are not matching")
        qs_name = User.objects.filter(
            Q(username__iexact=username)
        )
        qs_email = User.objects.filter(
            Q(email__iexact=email)
        )
        if qs_name.exists():
            return Response("already user id present with this username ")
        elif qs_email.exists():
            return Response("already user id present with this  email")
        else:
            user = User.objects.create_user(username=username, email=email)
            user.set_password(password)
            user.is_active = False
            user.save()

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = jwt_response_payload_handler(token, user)
            url = str(token)
            surl = url
            z = surl.split("/")
            mail_subject = "Activate your account by clicking below link"
            mail_message = render_to_string('registration/email_validation.html', {
                'user': Register.username,
                'domain': get_current_site(request).domain,
                'surl': surl
            })
            recipient_email = user.email
            subject, from_email, to = 'Hello, Activate your account by clicking below link', EMAIL_HOST, recipient_email
            msg = EmailMultiAlternatives(subject, mail_message, from_email, [to])
            msg.attach_alternative(mail_message, "text/html")
            msg.send()
            return render(request, 'registration/login.html')


class Login(GenericAPIView):
    serializer_class = LoginSerializers

    def post(self, request):
        #  permission_classes = [permissions.AllowAny]
        if request.user.is_authenticated:
            return Response({'details': 'user is already authenticated'})
        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        user = authenticate(username=username, password=password)
        # print(username, password)

        qs = User.objects.filter(
            Q(username__iexact=username) or
            Q(email__iexact=email)
        ).distinct()
        if qs.count() == 1:
            user_obj = qs.first()
            if user_obj.check_password(password):
                user = user_obj
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                response = jwt_response_payload_handler(token, user)
                cache.__setattr__(username, token)
                user.is_active = True
                user.save()
                return render(request, 'registration/dashboard.html')
            return Response("check password again")

        return Response("multiple users are present with this username")


def activate(request, surl):
    try:
        tokenobject = url.objects.get(surl=surl)
        token = tokenobject.lurl
        decode = jwt.decode(token, settings.SECRET_KEY)
        username = decode['user_name']
        user = User.objects.get(username=username)
        # if user is not none then user account will be activated
        if user is not None:
            user.is_active = True
            user.save()
            return redirect('login')
        else:
            return HttpResponse('not valid user')
    except KeyError as e:
        return HttpResponse(e)
    except Exception as f:
        return HttpResponse(f)


class Logout(GenericAPIView):
    serializer_class = LoginSerializers

    def get(self, request):
        try:
            user = request.user
            logout(request)
            return render(request, 'registration/index.html')
        except Exception:
            return Response({'details': 'something went wrong while logout'})


class Forgotpassword(GenericAPIView):
    serializer_class = EmailSerializers

    def post(self, request):
        email = request.data['email']
        if email == "":
            return Response({'details': 'email should not be empty'})
        else:
                user = User.objects.filter(email=email)
                user_email = user.values()[0]['email']
                user_username = user.values()[0]['username']
                user_id = user.values()[0]['id']
                user_password = user.values()[0]['password']
                # print(user_email, user_id, user_username)
                # print(type(user_username))
                if user_email is not None:
                    token = token_activation(user_username, user_id)
                    url = str(token)
                    surl = url
                    z = surl.split('/')
                    mail_subject = "Change your account password by clicking below link"
                    mail_message = render_to_string('registration/email_changepassword.html', {
                        'user': user_username,
                        'domain': get_current_site(request).domain,
                        'surl': surl
                    })
                   # print(mail_message)
                    recipient_email = user_email
                    subject, from_email, to = 'Welcome, Change your account password by clicking below link', EMAIL_HOST, recipient_email
                    msg = EmailMultiAlternatives(subject, mail_message, from_email, [to])
                    msg.attach_alternative(mail_message, "text/html")
                    msg.send()
                    return Response({'details': 'please check your email,link has sent your email'})


def dashboard_view(request):
    return render(request, 'registration/dashboard.html')


def token_activation(username, password):
    data = {
        'username': username,
        'password': password,
        'exp': datetime.datetime.now() + datetime.timedelta(days=2)
    }
    token = jwt.encode(data, SECRET_KEY, algorithm="HS256").decode('utf-8')
    return token


def token_validation(username, password):
    data = {
        'username': username,
        'password': password
    }
    tokson = requests.post(AUTH_ENDPOINT, data=data)
    token = tokson.json()['access']
    return token


def reset_password(request, surl):
    try:
        tokenobject = ShortURL.objects.get(surl=surl)
        token = tokenobject.lurl
        decode = jwt.decode(token, settings.SECRET_KEY)
        username = decode['username']
        user = User.objects.get(username=username)
        if user is not None:
            context = {'userReset': username}
            print(context)
            return redirect('/resetpassword/' + str(user)+'/')
        else:
            messages.info(request, 'was not able to sent the email')
            return redirect('forgotpassword')
    except KeyError:
        messages.info(request, 'was not able to sent the email')
        return redirect('forgotpassword')
    except Exception as e:
        print(e)
        messages.info(request, 'activation link expired')
        return redirect('forgotpassword')


class ResetPassword(GenericAPIView):
    serializer_class = ResetSerializers

    def post(self, request, user_reset):
        password = request.data['password']

        if user_reset is None:
            return Response({'details': 'not a valid user'})
        elif (password or confirm_password) == "":
            return Response({'details': 'password should not be empty'})
        else:
            try:
                user = User.objects.get(username=user_reset)
                user.set_password(password)
                user.save()
                return Response({'details': 'your password has been Set'})
            except Exception:
                return Response({'details': 'not a valid user'})
