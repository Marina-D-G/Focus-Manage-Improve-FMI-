from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

def get_default_calendar():
    try:
        return Calendar.objects.get(name="Default Calendar")
    except Calendar.DoesNotExist:
        return Calendar.objects.create(name="Default Calendar") 

class Calendar(models.Model):
    name = models.CharField(max_length=255)
    users = models.ManyToManyField(User, related_name="calendars")

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=datetime.date.today)
    time = models.TimeField(default=timezone.now)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name="events", null=True, blank=True, default=get_default_calendar)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="owned_events")

    def __str__(self):
        return self.name