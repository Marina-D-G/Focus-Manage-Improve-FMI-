import matplotlib.pyplot as plt
import io
import calendar
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from .models import Transaction
from .forms import TransactionForm
from notifications.signals import notify


BULGARIAN_MONTHS = {
    "January": "Януари", "February": "Февруари", "March": "Март", "April": "Април",
    "May": "Май", "June": "Юни", "July": "Юли", "August": "Август",
    "September": "Септември", "October": "Октомври", "November": "Ноември", "December": "Декември"
}

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

from django.shortcuts import render, redirect
from django.db.models import Sum
from notifications.signals import notify
from .forms import TransactionForm
from .models import Transaction

def add_expense(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = 'expense'
            transaction.save()

            today = datetime.date.today()
            transactions = Transaction.objects.filter(user=request.user, date=today)
            total_budget = transactions.filter(type="income").aggregate(Sum('amount'))['amount__sum'] or 0
            total_expenses = transactions.filter(type="expense").aggregate(Sum('amount'))['amount__sum'] or 0
            budget_left = total_budget - total_expenses

            if budget_left > 0 and total_budget > 0 and (budget_left / total_budget) < 0.15:
                notify.send(
                    request.user,
                    recipient=request.user,
                    verb='Внимание! Оставеният ви бюджет е под 15% от целият бюджет за месеца.',
                    description=f'Оставащият бюджет е {budget_left:.2f}лв. от {total_budget:.2f}лв..'
                )

            if budget_left < 0:
                notify.send(
                    request.user,
                    recipient=request.user,
                    verb='Внимание! Вие сте изхарчили целият бюджет за месеца.',
                    description=f'Надхвърлили сте бюджета си с {-budget_left:.2f}лв..'
                )

            return redirect('budget:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'add_transaction.html', {'form': form})


def remove_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    return redirect("budget:dashboard")

def dashboard(request):
    today = datetime.date.today()
    months = []

    for i in range(12):
        month_date = today - datetime.timedelta(days=i * 30)
        month_value = month_date.strftime("%Y-%m")
        month_name_en = month_date.strftime("%B")
        month_name_bg = BULGARIAN_MONTHS[month_name_en]

        income = Transaction.objects.filter(user=request.user, date__year=month_date.year, date__month=month_date.month, type="income").aggregate(Sum("amount"))["amount__sum"] or 0
        expenses = Transaction.objects.filter(user=request.user, date__year=month_date.year, date__month=month_date.month, type="expense").aggregate(Sum("amount"))["amount__sum"] or 0

        months.append({
            "value": month_value,
            "label": f"{month_name_bg} {month_date.year} (+{income} лв., -{expenses} лв.)",
            "income": income,
            "expenses": expenses
        })

    selected_month = request.GET.get("month", today.strftime("%Y-%m"))
    selected_year, selected_month_num = map(int, selected_month.split("-"))
    selected_month_label = f"{BULGARIAN_MONTHS[datetime.date(selected_year, selected_month_num, 1).strftime('%B')]} {selected_year}"

    transactions = Transaction.objects.filter(user=request.user, date__year=selected_year, date__month=selected_month_num)

    total_budget = transactions.filter(type="income").aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type="expense").aggregate(Sum('amount'))['amount__sum'] or 0
    budget_left = total_budget - total_expenses

    context = {
        "transactions": transactions,
        "total_budget": total_budget,
        "total_expenses": total_expenses,
        "budget_left": budget_left,
        "months": months,
        "selected_month": selected_month,
        "selected_month_label": selected_month_label
    }

    return render(request, "dashboard.html", context)


def generate_pie_chart(labels, values, title):
    fig, ax = plt.subplots()
    
    if sum(values) == 0:
        ax.text(0.5, 0.5, "Няма данни", fontsize=15, ha='center')
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
    selected_month = request.GET.get("month", datetime.date.today().strftime("%Y-%m"))
    selected_year, selected_month_num = map(int, selected_month.split("-"))

    transactions = Transaction.objects.filter(user=request.user, type="expense", date__year=selected_year, date__month=selected_month_num)

    CATEGORY_DICT = dict(Transaction.CATEGORY_CHOICES)

    categories = [CATEGORY_DICT[cat] for cat in transactions.values_list('category', flat=True).distinct()]
    amounts = [transactions.filter(category=cat).aggregate(Sum('amount'))['amount__sum'] or 0 for cat in transactions.values_list('category', flat=True).distinct()]

    buffer = generate_pie_chart(categories, amounts, f"Разходи за {selected_month}")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def income_chart(request):
    selected_month = request.GET.get("month", datetime.date.today().strftime("%Y-%m"))
    selected_year, selected_month_num = map(int, selected_month.split("-"))

    transactions = Transaction.objects.filter(user=request.user, type="income", date__year=selected_year, date__month=selected_month_num)

    CATEGORY_DICT = dict(Transaction.CATEGORY_CHOICES)

    categories = [CATEGORY_DICT[cat] for cat in transactions.values_list('category', flat=True).distinct()]
    amounts = [transactions.filter(category=cat).aggregate(Sum('amount'))['amount__sum'] or 0 for cat in transactions.values_list('category', flat=True).distinct()]

    buffer = generate_pie_chart(categories, amounts, f"Приходи за {selected_month}")
    return HttpResponse(buffer.getvalue(), content_type="image/png")
