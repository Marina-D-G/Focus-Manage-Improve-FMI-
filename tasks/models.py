from django.db import models
from datetime import datetime, timedelta


class TodoItem(models.Model):
    title = models.CharField(max_length = 200)
    completed = models.BooleanField(default = False)
    deadline = models.DateTimeField(
        default= datetime.now() + timedelta(days=7),  
        blank=True
    )
    #priority

