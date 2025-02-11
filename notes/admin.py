from django.contrib import admin
from .models import Note, NoteImage


admin.site.register(Note)
admin.site.register(NoteImage)