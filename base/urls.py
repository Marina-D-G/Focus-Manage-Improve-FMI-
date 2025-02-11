from django.urls import path, include
from django.contrib.auth.views import LogoutView
from . import views

app_name = "base"

urlpatterns = [
 path("", views.home, name="home"),
 path("signup/", views.sign_up, name="sign_up"),
 path("accounts/logout/", LogoutView.as_view(), name='logout'),
 path("accounts/", include("django.contrib.auth.urls")),
 path('profile/update/', views.update_profile, name='update_profile'),
 path('profile/<str:username>/', views.profile_view, name='profile'),
]