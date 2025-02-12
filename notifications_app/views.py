from django.shortcuts import render, redirect
from .forms import ReminderForm
from notifications.models import Notification
from notifications.signals import notify

def latest_notifications(request):
    latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')[:20]
    return render(request, 'latest_notifications.html', {'latest_notifications': latest_notifications})

def add_reminder(request):
    if request.method == "POST":
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder_datetime = form.cleaned_data['reminder_datetime']
            message = form.cleaned_data['message']
            notify.send(
                request.user,
                recipient=request.user,
                verb=f"Напомняне за {reminder_datetime}",
                description=message,
            )
            return redirect('notifications_app:latest_notifications')
    else:
        form = ReminderForm()
    return render(request, 'add_reminder.html', {'form': form})