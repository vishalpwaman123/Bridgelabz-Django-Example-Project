from django.conf.urls import url
from django.urls import path

from .views import Login, verify, refresh_jwt_token

urlpatterns = [
    path('login/', Login.as_view(), name='login'),
    path('login/verify/', verify, name='verification'),
    url(r'^api-token-refresh/', refresh_jwt_token,name="refreshtoken"),
]