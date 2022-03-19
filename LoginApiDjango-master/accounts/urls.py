from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import verify_jwt_token
from .views import Registration, Logout, Login, dashboard_view, Home, activate, Forgotpassword

from . import views

urlpatterns = [
    path('api-token-verify/', verify_jwt_token),
    path('api/auth/', obtain_jwt_token), 
    path('home/', Home.as_view(), name='home'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    path('register/', Registration.as_view(), name='register_url'),
    path('activate/<url>/', activate, name="activate"),
    path('forgotpassword/', Forgotpassword.as_view(), name="forgotpassword"),
    path('reset_password/<surl>/', views.reset_password, name="reset_password"),
    path('resetpassword/<user_reset>/',
         views.ResetPassword.as_view(), name="resetpassword"),
    path('dashboard/', dashboard_view, name='dashboard'),
]
