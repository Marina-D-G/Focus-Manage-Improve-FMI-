from django.urls import path, include, reverse_lazy
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from . import views

app_name = "base"

urlpatterns = [
 path("", views.home, name="home"),
 path("signup/", views.sign_up, name="sign_up"),
 path("accounts/logout/", LogoutView.as_view(), name='logout'),
 path("accounts/", include("django.contrib.auth.urls")),
 path('profile/update/', views.update_profile, name='update_profile'),
 path('profile/<str:username>/', views.profile_view, name='profile'),
 path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='password_change.html',
        success_url=reverse_lazy('base:password_change_done'),
    ), name='password_change'),
 path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
]