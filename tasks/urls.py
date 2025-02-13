from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.tasks, name='tasks'),
    path('add_task/<int:list_id>/', views.add_task, name='add_task'),
    path('delete_list/<int:list_id>/', views.delete_list, name='delete_list'),
    path('<int:task_id>/done/', views.mark_done, name='mark_done'),
    path('<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('lists/add/', views.add_list, name='add_list'),
    path('lists/join/', views.join_list, name="join_list"),
]