from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.notes_dashboard, name='notes_dashboard'),
    path('add/', views.add_note, name='add_note'),
    path('delete/<int:note_id>/', views.delete_note, name='delete_note'),
    path('edit/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('note_detail/<int:note_id>/', views.note_detail, name='note_detail'),
    path('view/', views.view_note, name='view_note'), #through code
]
