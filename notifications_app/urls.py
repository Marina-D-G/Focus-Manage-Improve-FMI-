from django.urls import path
from . import views

app_name = 'notifications_app'

urlpatterns = [
    path('', views.latest_notifications, name='latest_notifications'),
    path('add_reminder/', views.add_reminder, name='add_reminder'),
]