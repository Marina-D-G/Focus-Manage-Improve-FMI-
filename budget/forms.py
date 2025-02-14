from django import forms
from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'date', 'description']
        labels = {
            'category': 'Категория',
            'amount': 'Сума',
            'date': 'Дата',
            'description': 'Описание'
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class CategoryLimitForm(forms.Form):
    CATEGORY_CHOICES = [
        ('food', 'Храна'),
        ('transport', 'Транспорт'),
        ('entertainment', 'Забавления'),
        ('bills', 'Сметки'),
        ('health', 'Здраве'),
        ('rent', 'Наем'),
        ('dept', 'Заем'),
        ('other', 'Други'),
    ]
    labels = {
            'category': 'Категория',
            'percentage': 'Процент(%)',
    }
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    percentage = forms.IntegerField(
        min_value=0, 
        max_value=100, 
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )