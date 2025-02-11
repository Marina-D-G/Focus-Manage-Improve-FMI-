from django.urls import path
from . import views

app_name = 'notifications_app'

urlpatterns = [
    path('', views.latest_notifications, name='latest_notifications'),
]