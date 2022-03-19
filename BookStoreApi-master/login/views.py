import json
import logging
from datetime import timedelta
import jwt
import redis
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .serializers import UserSerializer
from .services import send_otp, create_access_token, create_refresh_token
from myproject import settings

redis = redis.StrictRedis(host=settings.REDIS_HOST,
                          port=settings.REDIS_PORT, db=0)
logger = logging.getLogger('django')
with open('login/mymessages.json', 'r') as myfile:
    data = myfile.read()
obj = json.loads(data)


class Login(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')
        with connection.cursor() as cursor:
            qs = cursor.execute("SELECT mobilenum FROM user WHERE username=%s AND password=SHA1(%s)", [
                                username, password])
            if qs != 0:
                mobilenum = cursor.fetchall()
                mobilenum = mobilenum[0][0]
                send_otp(mobilenum)
                logger.info(str(obj['login_success']))
                return Response(str(obj['login_success']), status=200)
        logger.info(str(obj['not_found']))
        return Response(str(obj['not_found']), status=400)


@api_view(('POST',))
def verify(request):
    otp = request.POST['otp']
    mobilenum = request.POST['mobile_num']
    dbotp = redis.get(mobilenum)
    if dbotp is not None:
        dbotp = dbotp.decode('utf-8')
    if str(dbotp) == otp:
        c = connection.cursor()
        c.execute(
            "SELECT id,username FROM user WHERE mobilenum=%s", [mobilenum])
        user = c.fetchall()
        uid = user[0][0]
        username = user[0][1]
        access_token = create_access_token(uid, username, mobilenum)
        redis.set(access_token, uid, ex=timedelta(
            seconds=settings.JWT_EXPIRATION_TIME))
        refresh_token = create_refresh_token(uid, username, mobilenum)
        redis.set(refresh_token, uid, ex=timedelta(
            days=settings.JWT_REFRESH_EXPIRATION_TIME))
        response = {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        logger.info(response)
        return Response(response, status=200)
    logger.info(str(obj['not_correct']))
    return Response(str(obj['not_correct']), status=400)


@api_view(("POST",))
def refresh_jwt_token(request):
    refresh_token = request.POST['token']
    decoded_token = jwt.decode(refresh_token, settings.SECRET_KEY)
    uid = decoded_token.get("uid")
    username = decoded_token.get("username")
    mobile_num = decoded_token.get("mobile_num")
    access_token = create_access_token(uid, username, mobile_num)
    redis.set(access_token, uid, ex=300)
    return Response({"access_token": access_token})
