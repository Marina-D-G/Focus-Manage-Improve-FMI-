import matplotlib.pyplot as plt
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from .models import Transaction
from .forms import TransactionForm


def add_transaction(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('budget:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'add_transaction.html', {'form': form})

def add_income(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = 'income'
            transaction.save()
            return redirect('budget:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'add_transaction.html', {'form': form})

def add_expense(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = 'expense'
            transaction.save()
            return redirect('budget:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'add_transaction.html', {'form': form})

def remove_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    return redirect("budget:dashboard")

def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    
    total_budget = transactions.filter(type="income").aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type="expense").aggregate(Sum('amount'))['amount__sum'] or 0
    budget_left = total_budget - total_expenses

    context = {
        'total_budget': total_budget,
        'total_expenses': total_expenses,
        'budget_left': budget_left,
        'transactions': transactions,
    }
    
    return render(request, "dashboard.html", context)

def generate_pie_chart(labels, values, title):
    fig, ax = plt.subplots()
    
    if sum(values) == 0:
        ax.text(0.5, 0.5, "No Data", fontsize=15, ha='center')
        ax.axis('off')
    else:
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title(title)
        ax.axis('equal')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    return buffer

def expense_chart(request):
    transactions = Transaction.objects.filter(user=request.user, type="expense")
    
    categories = list(transactions.values_list('category', flat=True).distinct())
    amounts = [transactions.filter(category=cat).aggregate(Sum('amount'))['amount__sum'] or 0 for cat in categories]

    buffer = generate_pie_chart(categories, amounts, "Expense Breakdown")
    return HttpResponse(buffer.getvalue(), content_type="image/png")

def income_chart(request):
    transactions = Transaction.objects.filter(user=request.user, type="income")

    categories = list(transactions.values_list('category', flat=True).distinct())
    amounts = [transactions.filter(category=cat).aggregate(Sum('amount'))['amount__sum'] or 0 for cat in categories]

    buffer = generate_pie_chart(categories, amounts, "Income Breakdown")
    return HttpResponse(buffer.getvalue(), content_type="image/png")