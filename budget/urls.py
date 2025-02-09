from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add_income/', views.add_income, name='add_income'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('remove_transaction/<int:transaction_id>/', views.remove_transaction, name='remove_transaction'),
    path('expense_chart/', views.expense_chart, name='expense_chart'),
    path('income_chart/', views.income_chart, name='income_chart'),
]
