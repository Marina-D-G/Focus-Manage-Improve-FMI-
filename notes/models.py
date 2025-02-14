from django.db import models
from django.contrib.auth.models import User
import random

class Note(models.Model):
    CATEGORY_CHOICES = (
        ('work', 'Работа'),
        ('education', 'Образование'),
        ('ideas', 'Идеи'),
        ('travel', 'Пътуване'),
        ('health', 'Здраве'),
        ('hobbies', 'Хобита'),
        ('recipes', 'Рецепти'),
        ('personal', 'Лични бележки'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    join_code = models.CharField(max_length=6, unique=True, blank=True, null=True)

    def generate_code(self):
        while True:
            code = str(random.randint(100000, 999999))
            if not Note.objects.filter(join_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = self.generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class NoteImage(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='note_images/')

    def __str__(self):
        return f"{self.note.title}"