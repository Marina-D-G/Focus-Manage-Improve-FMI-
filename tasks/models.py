import random
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta


def default_deadline():
    return datetime.now() + timedelta(days=7)

class TodoList(models.Model):
    users = models.ManyToManyField(User, related_name="todo_lists")
    name = models.CharField(max_length=200)
    join_code = models.CharField(max_length=6, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

    def generate_code(self):
        while True:
            code = str(random.randint(100000, 999999))
            if not TodoList.objects.filter(join_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = self.generate_code()
        super().save(*args, **kwargs)


class TodoItem(models.Model):
    PRIORITY_CHOICES = [
        (1, "Нисък"),
        (2, "Среден"),
        (3, "Висок"),
    ]

    PHASE_CHOICES = [
        ("todo", "Планирано"),
        ("in_progress", "В процес"),
        ("done", "Завършено"),
    ]

    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True, default=1)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(default=default_deadline, blank=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default="todo")

    @classmethod
    def filter_by_priority(cls, priority):
        return cls.objects.filter(priority=priority)

    @classmethod
    def filter_by_phase(cls, phase):
        return cls.objects.filter(phase=phase)

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"