import json
import logging

import jwt
from django.db import connection, DatabaseError, ProgrammingError, IntegrityError
from rest_framework.exceptions import APIException
import redis
from rest_framework.response import Response

from myproject import settings
from books.services import check_product

from .custom_exceptions import ProductExist, BookStoreError
from books.services import get_uid

logger = logging.getLogger('django')
redis = redis.StrictRedis(host=settings.REDIS_HOST,
                          port=settings.REDIS_PORT, db=0)
with open('books/mymessages.json', 'r') as myfile:
    data = myfile.read()
obj = json.loads(data)


def authenticate_user():
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            token = request.headers.get('X-Token')
            uid = redis.get(token)
            if uid is not None:
                uid = uid.decode('utf-8')
                decoded_token = jwt.decode(token, settings.SECRET_KEY)
                token_uid = decoded_token.get("uid")
                if uid == str(token_uid):
                    logger.info(str(obj['success_authentication']))
                    return view_func(request, *args, **kwargs)
            else:
                logger.warning(str(obj['token_notproper']))
                raise APIException(str(obj['token_notproper']))
        return wrap
    return decorator

def check_product_wishlist():
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            token = request.headers.get('X-Token')
            product_id = request.GET['product_id']
            uid = get_uid(token)
            if not check_product(product_id, uid):
                raise ProductExist
            else:
                return view_func(request, *args, **kwargs)
        return wrap
    return decorator

def check_sql_exceptions():
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            try:
                c = connection.cursor()
                return view_func(request, *args, **kwargs)
            except DatabaseError as e:
                raise BookStoreError('database_error')
            except ProgrammingError:
                raise BookStoreError('programming_error')
            except IntegrityError:
                raise BookStoreError('invalid_product_id')
            finally:
                c.close()
        return wrap
    return decorator
