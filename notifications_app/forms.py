from django import forms

class ReminderForm(forms.Form):
    reminder_datetime = forms.DateTimeField(
        label="Дата и час на напомнянето",
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }
        )
    )
    message = forms.CharField(
        label="Съобщение",
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Въведете съобщението за напомнянето'
            }
        )
    )
