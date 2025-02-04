from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import TodoItem, TodoList

def home(request):
    return render(request, 'hello.html')

def tasks(request):
    todo_lists = TodoList.objects.filter(users=request.user) if request.user.is_authenticated else []
    
    list_id = request.GET.get('list')
    if list_id:
        current_list = get_object_or_404(TodoList, id=list_id, users=request.user)
        items = TodoItem.objects.filter(todo_list=current_list)
    else:
        current_list = None
        items = TodoItem.objects.filter(todo_list__users=request.user) if request.user.is_authenticated else []
    
    items = items.order_by('-priority', 'deadline')
    
    context = {
        "tasks": items,
        "todo_lists": todo_lists,
        "current_list": current_list,
        "now": timezone.now(),
    }
    
    return render(request, "tasks.html", context)

def add_task(request):
    # Тук ще добавите логиката за добавяне на нова задача
    return render(request, 'hello.html') #add_task.html