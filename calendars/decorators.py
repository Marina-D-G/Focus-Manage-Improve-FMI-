from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from .models import Event, Calendar


def check_owner(func):
    @wraps(func)
    def wrapper(request, event_id):
        event = get_object_or_404(Event, id=event_id)
        if event.owner != request.user:
            return redirect("calendars:calendar_dashboard")
        return func(request, event_id)
    return wrapper


def check_user(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        calendar_id = request.GET.get('calendar_id')
        if calendar_id:
            try:
                calendar_id = int(calendar_id)
            except ValueError:
                return redirect('calendars:calendar_dashboard')
            if not Calendar.objects.filter(id=calendar_id, users=request.user).exists():
                return redirect('calendars:calendar_dashboard')
        return func(request, *args, **kwargs)
    return wrapper