from django.urls import path
from . import views

urlpatterns = [
    path("hello/", views.home),
    path("todos/", views.todos)
]