from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import random


class Calendar(models.Model):
    name = models.CharField(max_length=255)
    users = models.ManyToManyField(User, related_name="calendars")
    join_code = models.CharField(max_length=6, unique=True, blank=True, null=True)

    def generate_code(self):
        while True:
            code = str(random.randint(100000, 999999)) 
            if not Calendar.objects.filter(join_code=code).exists():
                self.join_code = code
                self.save()
                break

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=datetime.date.today)
    time = models.TimeField(default=timezone.now)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="owned_events")
    
    
    def __str__(self):
        return self.name