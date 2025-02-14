from django import forms
from .models import TodoItem, TodoList

class TaskForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ["title", "description", "priority", "phase", "deadline"]
        labels = {
            'title': 'Заглавие',
            'description': 'Описание',
            'priority': 'Приоритет',
            'phase': 'Етап',
            'deadline': 'Краен срок',
        }

class TodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ["name"]
        labels = {"name": "Име на списъка"}

class JoinListForm(forms.Form):
    join_code = forms.CharField(label="Код за присъединяване", max_length=6)
