from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TodoItem, TodoList
from .forms import TaskForm, TodoListForm, JoinListForm

def home(request):
    return render(request, 'hello.html')

def tasks(request):
    sort_by = request.GET.get('sort_by')
    order = request.GET.get('order')
    list_id = request.GET.get('list')
    
    todo_lists = TodoList.objects.filter(users=request.user)
    tasks = TodoItem.objects.filter(todo_list__in=todo_lists)

    if list_id:
        current_list = TodoList.objects.get(id=list_id)
        tasks = tasks.filter(todo_list_id=list_id)
    else:
        current_list = None
        
    if sort_by == 'deadline':
        tasks = tasks.order_by('deadline' if order == 'asc' else '-deadline')
    elif sort_by == 'priority':
        tasks = tasks.order_by('priority' if order == 'low' else '-priority')
    
    tasks = list(tasks)
    done_tasks = [t for t in tasks if t.phase == 'done']
    active_tasks = [t for t in tasks if t.phase != 'done']
    tasks = active_tasks + done_tasks

    context = {
        'tasks': tasks,
        'todo_lists': todo_lists,
        'current_list': current_list,
        'sort_by': sort_by,
        'order': order,
        'now': timezone.now(),
    }
    
    return render(request, 'tasks.html', context)

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
    task.phase = "done"
    task.save()
    return redirect(request.META.get('HTTP_REFERER', 'tasks:tasks'))

def edit_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("tasks:tasks")
    else:
        form = TaskForm(instance=task)

    return render(request, "edit.html", {"form": form, "task": task})

def delete_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    
    if request.method == "POST":
        task.delete()
        return redirect("tasks:tasks")

    return redirect("tasks:tasks") #with get

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


def join_list(request):
    if request.method == "POST":
        form = JoinListForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data["join_code"]
            try:
                todo_list = TodoList.objects.get(join_code=join_code)
                todo_list.users.add(request.user)
                messages.success(request, f"Успешно се присъединихте към '{todo_list.name}'!")
                return redirect("tasks:tasks")
            except TodoList.DoesNotExist:
                messages.error(request, "Невалиден код!")
    else:
        form = JoinListForm()

    return render(request, "join_list.html", {"form": form})