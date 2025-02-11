from django.shortcuts import render
from notifications.models import Notification


def latest_notifications(request):
    latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')[:20]
    return render(request, 'latest_notifications.html', {'latest_notifications': latest_notifications})