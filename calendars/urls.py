from django.urls import path
from . import views


app_name = 'calendars'

urlpatterns = [
    path('', views.calendar_month, name='calendar_month'),
    path('day/', views.calendar_day, name='calendar_day'),
    path('week/', views.calendar_week, name='calendar_week'),
    path('add/', views.add_event, name='add_event'),
    path('event/<int:id>/', views.event_detail, name='event_detail')
]