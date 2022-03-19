import os
import random

import jwt
import redis
# from django.conf import settings

from twilio.rest import Client
from myproject import settings

redis = redis.StrictRedis(host=settings.REDIS_HOST,
                          port=settings.REDIS_PORT, db=0)
account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_TOKEN')
client = Client(account_sid, auth_token)


def send_otp(mobile_num):
    otp = ""
    for i in range(6):
        otp += str(random.randint(0, 9))
    print(otp)
    redis.set(mobile_num, otp, 300)
    message = client.messages.create(
        body='Yor OTP for Login is ' + str(otp),
        from_=os.getenv('TWILIO_NUMBER'),
        to=mobile_num
    ) 


def create_access_token(uid, username, mobilenum):
    access_token = jwt.encode({'uid': uid, 'username': username, 'mobile_num': mobilenum,
                               'exp': timezone.now() + timedelta(seconds=settings.JWT_EXPIRATION_TIME), },
                              settings.SECRET_KEY,
                              algorithm='HS256')
    return access_token


def create_refresh_token(uid, username, mobilenum):
    refresh_token = jwt.encode({'uid': uid, 'username': username, 'mobile_num': mobilenum, 'token': 'refresh',
                                'exp': timezone.now() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_TIME),},
                               settings.SECRET_KEY, algorithm='HS256')
    return refresh_token
