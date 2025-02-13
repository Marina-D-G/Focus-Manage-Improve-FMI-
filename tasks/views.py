from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from notifications.signals import notify
from .models import TodoItem, TodoList
from .forms import TaskForm, TodoListForm, JoinListForm


def check_user(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        task_id = kwargs.get("task_id")
        task = get_object_or_404(TodoItem, id=task_id)
        if not task.todo_list.users.filter(id=request.user.id).exists():
            messages.error(request, "Нямате достъп до тази задача!")
            return redirect('tasks:tasks')
        return view_func(request, *args, **kwargs)
    return wrapped


@login_required
def tasks(request):
    sort_by = request.GET.get('sort_by')
    order = request.GET.get('order')
    list_id = request.GET.get('list')
    
    todo_lists = TodoList.objects.filter(users=request.user)
    tasks_qs = TodoItem.objects.filter(todo_list__in=todo_lists)

    current_list = None
    if list_id:
        current_list = get_object_or_404(TodoList, id=list_id, users=request.user)
        tasks_qs = tasks_qs.filter(todo_list_id=list_id)
        
    if sort_by == 'deadline':
        tasks_qs = tasks_qs.order_by('deadline' if order == 'asc' else '-deadline')
    elif sort_by == 'priority':
        tasks_qs = tasks_qs.order_by('priority' if order == 'low' else '-priority')
    
    tasks_list = list(tasks_qs)
    done_tasks = [t for t in tasks_list if t.phase == 'done']
    active_tasks = [t for t in tasks_list if t.phase != 'done']
    tasks_list = active_tasks + done_tasks

    context = {
        'tasks': tasks_list,
        'todo_lists': todo_lists,
        'current_list': current_list,
        'sort_by': sort_by,
        'order': order,
        'now': timezone.now(),
    }
    return render(request, 'tasks.html', context)


@login_required
def add_task(request, list_id):
    todo_list = get_object_or_404(TodoList, id=list_id, users=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.todo_list = todo_list
            task.save()
            same_day_tasks = TodoItem.objects.filter(
                todo_list=todo_list, 
                deadline__date=task.deadline.date()
            )
            if same_day_tasks.count() > 5:
                notify.send(
                    request.user,
                    recipient=todo_list.users.all(),
                    verb=f'Внимание! Имате повече от 5 задачи с краен срок {task.deadline.date()}! Помислете за почивка!'
                )
            return redirect('tasks:tasks')
    else:
        form = TaskForm()
    
    context = {
        'form': form,
        'todo_list': todo_list,
    }
    return render(request, 'add.html', context)


@login_required
def delete_list(request, list_id):
    todo_list = get_object_or_404(TodoList, id=list_id, users=request.user)
    if request.method == 'POST':
        todo_list.delete()
        messages.success(request, 'Списъкът беше успешно изтрит.')
    return redirect('tasks:tasks')


@login_required
def mark_done(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    task.phase = "done"
    task.save()
    return redirect(request.META.get('HTTP_REFERER', 'tasks:tasks'))


@login_required
@check_user
def edit_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("tasks:tasks")
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
    }
    return render(request, "edit.html", context)


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    if request.method == "POST":
        task.delete()
    return redirect("tasks:tasks")


@login_required
def add_list(request):
    if request.method == "POST":
        form = TodoListForm(request.POST)
        if form.is_valid():
            todo_list = form.save(commit=False)
            todo_list.save()
            todo_list.users.add(request.user)
            return redirect("tasks:tasks")
    else:
        form = TodoListForm()
   
    return render(request, "add_list.html", {"form": form})


@login_required
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