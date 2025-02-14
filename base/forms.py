from django import forms
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'profile_picture']
        labels = {
            'display_name': 'Име',
            'profile_picture': 'Профилна снимка',
        }
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Въведете вашето име'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

