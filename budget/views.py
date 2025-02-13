import matplotlib.pyplot as plt
import io
import calendar
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from .models import Transaction
from .forms import TransactionForm, CategoryLimitForm
from notifications.signals import notify


BULGARIAN_MONTHS = {
    "January": "Януари", "February": "Февруари", "March": "Март", "April": "Април",
    "May": "Май", "June": "Юни", "July": "Юли", "August": "Август",
    "September": "Септември", "October": "Октомври", "November": "Ноември", "December": "Декември"
}

CATEGORY_BUDGET_PERCENTAGES = {
    'food': 25,
    'transport': 5,
    'entertainment': 10,
    'bills': 20,
    'health': 10,
    'rent': 20,
    'dept': 5,
    'other': 5,
}


def get_current_month_transactions(user):
    today = datetime.date.today()
    start_of_month = datetime.date(today.year, today.month, 1)
    end_of_month = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    return Transaction.objects.filter(user=user, date__range=(start_of_month, end_of_month))


def calculate_budget(transactions):
    total_income = transactions.filter(type="income").aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type="expense").aggregate(Sum('amount'))['amount__sum'] or 0
    return total_income, total_expenses, total_income - total_expenses


def send_notifications(user, transaction, transactions, total_budget, budget_left):
    if total_budget > 0:
        if budget_left > 0 and (budget_left / total_budget) < 0.15:
            notify.send(
                user,
                recipient=user,
                verb='Внимание! Оставеният ви бюджет е под 15% от целият бюджет за месеца.',
                description=f'Оставащият бюджет е {budget_left:.2f}лв. от {total_budget:.2f}лв.'
            )
        if budget_left < 0:
            notify.send(
                user,
                recipient=user,
                verb='Внимание! Вие сте изхарчили целият бюджет за месеца.',
                description=f'Надхвърлили сте бюджета си с {-budget_left:.2f}лв.'
            )

    allowed_category_budget = total_budget * CATEGORY_BUDGET_PERCENTAGES.get(transaction.category, 0) / 100
    category_expenses = transactions.filter(category=transaction.category).aggregate(total=Sum('amount'))['total'] or 0
    if total_budget > 0 and category_expenses > allowed_category_budget:
        notify.send(
            user,
            recipient=user,
            verb=f'Внимание! Разходите ви за категорията "{transaction.get_category_display()}" надвишиха лимита в бюджета.',
            description=(
                f'Разходите в тази категория са {category_expenses:.2f}лв., '
                f'допустимата сума е {allowed_category_budget:.2f}лв. '
                f'(т.е. {CATEGORY_BUDGET_PERCENTAGES.get(transaction.category, 0)}% от общия бюджет).'
            )
        )


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


def get_chart_data(transactions):
    CATEGORY_DICT = dict(Transaction.CATEGORY_CHOICES)
    category_ids = transactions.values_list('category', flat=True).distinct()
    labels = [CATEGORY_DICT.get(cat, cat) for cat in category_ids]
    amounts = [
        transactions.filter(category=cat).aggregate(total=Sum('amount'))['total'] or 0
        for cat in category_ids
    ]
    return labels, amounts


@login_required
def add_income(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = 'income'
            transaction.save()
            messages.success(request, "Приходът е добавен към бюджета!")
            return redirect('budget:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'add_transaction.html', {'form': form})


@login_required
def add_expense(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = 'expense'
            transaction.save()

            transactions = get_current_month_transactions(request.user)
            total_budget, total_expenses, budget_left = calculate_budget(transactions)
            send_notifications(request.user, transaction, transactions, total_budget, budget_left)

            messages.success(request, "Разходът е добавен успешно!")
            return redirect('budget:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'add_transaction.html', {'form': form})


@login_required
def remove_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    messages.success(request, "Премахнато е движение в бюджета!")
    return redirect("budget:dashboard")


@login_required
def dashboard(request):
    today = datetime.date.today()
    months = []

    for i in range(12):
        month_date = today - datetime.timedelta(days=i * 30)
        month_value = month_date.strftime("%m-%Y")
        month_name_en = month_date.strftime("%B")
        month_name_bg = BULGARIAN_MONTHS.get(month_name_en, month_name_en)

        income = Transaction.objects.filter(
            user=request.user,
            date__year=month_date.year,
            date__month=month_date.month,
            type="income"
        ).aggregate(Sum("amount"))["amount__sum"] or 0

        expenses = Transaction.objects.filter(
            user=request.user,
            date__year=month_date.year,
            date__month=month_date.month,
            type="expense"
        ).aggregate(Sum("amount"))["amount__sum"] or 0

        months.append({
            "value": month_value,
            "label": f"{month_name_bg} {month_date.year} (+{income} лв., -{expenses} лв.)",
            "income": income,
            "expenses": expenses
        })

    selected_month = request.GET.get("month", today.strftime("%m-%Y"))
    selected_month_num, selected_year = map(int, selected_month.split("-"))
    selected_month_label = f"{BULGARIAN_MONTHS[datetime.date(selected_year, selected_month_num, 1).strftime('%B')]} {selected_year}"

    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=selected_year,
        date__month=selected_month_num
    )
    total_budget, total_expenses, budget_left = calculate_budget(transactions)

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


@login_required
def set_category_limit(request):
    if request.method == 'POST':
        form = CategoryLimitForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            percentage = form.cleaned_data['percentage']
            CATEGORY_BUDGET_PERCENTAGES[category] = percentage
            messages.success(request, "Лимитът е зададен успешно!")
            return redirect('budget:dashboard')
    else:
        form = CategoryLimitForm()
    return render(request, 'set_category_limit.html', {'form': form})


@login_required
def expense_chart(request):
    selected_month = request.GET.get("month", datetime.date.today().strftime("%m-%Y"))
    selected_year, selected_month_num = map(int, selected_month.split("-"))
    transactions = Transaction.objects.filter(
        user=request.user,
        type="expense",
        date__year=selected_year,
        date__month=selected_month_num
    )
    labels, amounts = get_chart_data(transactions)
    buffer = generate_pie_chart(labels, amounts, f"Разходи за {selected_month}")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def income_chart(request):
    selected_month = request.GET.get("month", datetime.date.today().strftime("%m-%Y"))
    selected_year, selected_month_num = map(int, selected_month.split("-"))
    transactions = Transaction.objects.filter(
        user=request.user,
        type="income",
        date__year=selected_year,
        date__month=selected_month_num
    )
    labels, amounts = get_chart_data(transactions)
    buffer = generate_pie_chart(labels, amounts, f"Приходи за {selected_month}")
    return HttpResponse(buffer.getvalue(), content_type="image/png")