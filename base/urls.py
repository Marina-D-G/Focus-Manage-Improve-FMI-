from django.urls import path, include
from django.contrib.auth.views import LogoutView
from .views import sign_up, home

app_name = "base"

urlpatterns = [
 path("", home, name="home"),
 path("signup/", sign_up, name="sign_up"),
 path("accounts/logout/", LogoutView.as_view(), name='logout'),
 path("accounts/", include("django.contrib.auth.urls")),
]