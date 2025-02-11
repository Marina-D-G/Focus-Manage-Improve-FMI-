from django.urls import path
from . import views


app_name = 'calendars'

urlpatterns = [
    path('', views.calendar_dashboard, name='calendar_dashboard'),
    path('add_event/<int:selected_calendar_id>/', views.add_event, name='add_event'),
    path('add_from_task/<int:task_id>/', views.add_from_task, name="add_from_task"),
    path('<int:event_id>/edit/', views.edit_event, name="edit_event"),
    path('<int:event_id>/delete/', views.delete_event, name="delete_event"),
    path('event/<int:id>/', views.event_detail, name='event_detail'),
    path('cal/add', views.add_calendar, name='add_calendar'),
    path('cal/join', views.join_calendar, name='join_calendar'),
    path('remove_calendar/<int:calendar_id>/', views.remove_calendar, name='remove_calendar'),
    path('export_calendar/<int:calendar_id>/', views.export_calendar, name='export_calendar'),
]