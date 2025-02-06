from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TodoItem, TodoList
from .forms import TaskForm, TodoListForm

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

def add_task(request, list_id):
    todo_list = get_object_or_404(TodoList, id=list_id, users=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.todo_list = todo_list
            task.user = request.user
            task.save()
            
            return redirect('tasks:tasks')
    else:
        form = TaskForm()
    
    context = {
        'form': form,
        'todo_list': todo_list
    }
    return render(request, 'add.html', context)

def delete_list(request, list_id):
    todo_list = get_object_or_404(TodoList, id=list_id, users=request.user)
    
    if request.method == 'POST':
        todo_list.delete()
        messages.success(request, 'Списъкът беше успешно изтрит.')
        return redirect('tasks:tasks')
    
    return redirect('tasks:tasks')

def mark_done(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    task.status = True
    task.save()
    return redirect(request.META.get('HTTP_REFERER', 'tasks:tasks'))

def edit_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("tasks:tasks")  # Пренасочва обратно към списъка със задачи
    else:
        form = TaskForm(instance=task)

    return render(request, "edit.html", {"form": form, "task": task})

def delete_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    
    if request.method == "POST":
        task.delete()
        return redirect("tasks:tasks")  # Пренасочване обратно към списъка със задачи

    return redirect("tasks:tasks")  # Ако някой се опита да достъпи URL-а с GET

def add_list(request):
    if request.method == "POST":
        form = TodoListForm(request.POST)
        if form.is_valid():
            task_list = form.save(commit=False)
            task_list.save()
            task_list.users.add(request.user)  # Добавя текущия потребител автоматично
            return redirect("tasks:tasks")
    else:
        form = TodoListForm()
   
    return render(request, "add_list.html", {"form": form})