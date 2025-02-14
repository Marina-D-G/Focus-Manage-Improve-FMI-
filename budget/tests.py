import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import Transaction
from .views import CATEGORY_BUDGET_PERCENTAGES

class BudgetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='ivanivanov', password='password123')
        self.client.login(username='ivanivanov', password='password123')

    def test_dashboard_view(self):
        response = self.client.get(reverse('budget:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('transactions', response.context)
        self.assertIn('total_budget', response.context)
        self.assertIn('total_expenses', response.context)
        self.assertIn('budget_left', response.context)
        self.assertIn('months', response.context)
        self.assertIn('selected_month', response.context)
        self.assertIn('selected_month_label', response.context)

    def test_add_income_get(self):
        response = self.client.get(reverse('budget:add_income'))
        self.assertEqual(response.status_code, 200)

    def test_add_income_post(self):
        post_data = {
            'amount': '150.00',
            'date': datetime.date.today().strftime("%Y-%m-%d"),
            'category': 'other',
            'description': 'Приход'
        }
        response = self.client.post(reverse('budget:add_income'), data=post_data)
        self.assertEqual(response.status_code, 302)
        transaction = Transaction.objects.filter(user=self.user, type='income').first()
        self.assertIsNotNone(transaction)
        self.assertEqual(float(transaction.amount), 150.00)

    def test_add_expense_get(self):
        response = self.client.get(reverse('budget:add_expense'))
        self.assertEqual(response.status_code, 200)

    def test_add_expense_post(self):
        post_data = {
            'amount': '75.50',
            'date': datetime.date.today().strftime("%Y-%m-%d"),
            'category': 'food',
            'description': 'Разход'
        }
        response = self.client.post(reverse('budget:add_expense'), data=post_data)
        self.assertEqual(response.status_code, 302)
        transaction = Transaction.objects.filter(user=self.user, type='expense').first()
        self.assertIsNotNone(transaction)
        self.assertEqual(float(transaction.amount), 75.50)

    def test_remove_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=50,
            date=datetime.date.today(),
            category='other',
            type='expense',
            description='За изтриване'
        )
        response = self.client.get(reverse('budget:remove_transaction', args=[transaction.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())

    def test_expense_chart(self):
        Transaction.objects.create(
            user=self.user,
            amount=20,
            date=datetime.date.today(),
            category='food',
            type='expense',
            description='Разход за храна'
        )
        Transaction.objects.create(
            user=self.user,
            amount=30,
            date=datetime.date.today(),
            category='transport',
            type='expense',
            description='Разход за транспорт'
        )
        current_year = datetime.date.today().year
        current_month = datetime.date.today().month
        month_param = f"{current_year}-{current_month:02d}"
        response = self.client.get(reverse('budget:expense_chart') + f"?month={month_param}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_income_chart(self):
        Transaction.objects.create(
            user=self.user,
            amount=100,
            date=datetime.date.today(),
            category='other',
            type='income',
            description='Приход'
        )
        current_year = datetime.date.today().year
        current_month = datetime.date.today().month
        month_param = f"{current_year}-{current_month:02d}"
        response = self.client.get(reverse('budget:income_chart') + f"?month={month_param}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_set_category_limit_get(self):
        response = self.client.get(reverse('budget:set_category_limit'))
        self.assertEqual(response.status_code, 200)

    def test_set_category_limit_post(self):
        original = CATEGORY_BUDGET_PERCENTAGES.get('food', None)
        post_data = {
            'category': 'food',
            'percentage': 30,
        }
        response = self.client.post(reverse('budget:set_category_limit'), data=post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CATEGORY_BUDGET_PERCENTAGES.get('food'), 30)

    def test_views_require_login(self):
        self.client.logout()
        protected_urls = [
            reverse('budget:dashboard'),
            reverse('budget:add_income'),
            reverse('budget:add_expense'),
            reverse('budget:remove_transaction', args=[1]),
            reverse('budget:expense_chart'),
            reverse('budget:income_chart'),
            reverse('budget:set_category_limit'),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("login", response.url.lower())