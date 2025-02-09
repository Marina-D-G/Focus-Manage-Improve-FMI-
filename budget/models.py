from django.db import models
from django.contrib.auth.models import User


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Приход'),
        ('expense', 'Разход'),
    ]

    CATEGORY_CHOICES = [
        ('food', 'Храна'),
        ('transport', 'Транспорт'),
        ('entertainment', 'Забавления'),
        ('bills', 'Сметки'),
        ('health', 'Здраве'),
        ('rent', 'Наем'),
        ('dept', 'Заем'),
        ('salary', 'Заплата'),
        ('other', 'Други'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.get_type_display()} - {self.amount} ({self.get_category_display()})"