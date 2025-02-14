from django import forms
from .models import Event, Calendar


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date', 'time', 'description']
        labels = {
            'name': 'Име',
            'date': 'Дата',
            'time': 'Час',
            'description': 'Описание'
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['name']
        labels = {'name': 'Име'}
    

class JoinCalendarForm(forms.Form):
    join_code = forms.CharField(label="Код за присъединяване", max_length=6)