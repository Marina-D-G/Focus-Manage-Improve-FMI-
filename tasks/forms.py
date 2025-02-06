from django import forms
from .models import TodoItem, TodoList

class TaskForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ["title", "description", "priority", "phase", "deadline"]

class TodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ["name"]
        labels = {"name": "Име на списъка"}
