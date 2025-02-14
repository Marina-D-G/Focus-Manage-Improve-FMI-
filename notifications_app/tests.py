from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from notifications.models import Notification


class NotificationViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ivanivanov', password='password123')
        self.client.login(username='ivanivanov', password='password123')

    def test_latest_notifications_view_with_notifications(self):
        """
        Тества, че изгледът за последните уведомления връща страницата с уведомления,
        съдържащa създадените уведомления.
        """
        # Създаваме две тестови уведомления
        now = timezone.now()
        Notification.objects.create(
            recipient=self.user,
            actor=self.user,
            verb="Тест уведомление 1",
            description="Описание 1",
            timestamp=now
        )
        Notification.objects.create(
            recipient=self.user,
            actor=self.user,
            verb="Тест уведомление 2",
            description="Описание 2",
            timestamp=now
        )

        url = reverse('notifications_app:latest_notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'latest_notifications.html')
        # Проверяваме, че съдържа текст от уведомленията
        self.assertContains(response, "Тест уведомление 1")
        self.assertContains(response, "Тест уведомление 2")

    def test_latest_notifications_view_requires_login(self):
        """
        Тества, че достъпът до изгледа за уведомления изисква логин.
        """
        self.client.logout()
        url = reverse('notifications_app:latest_notifications')
        response = self.client.get(url)
        # Обикновено ще има пренасочване към login страницата
        self.assertNotEqual(response.status_code, 200)
        self.assertIn('/login/', response.url)

    def test_add_reminder_get(self):
        """
        Тества GET заявка към изгледа за добавяне на напомняне.
        """
        url = reverse('notifications_app:add_reminder')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_reminder.html')
        # Проверяваме, че формата присъства в отговора
        self.assertContains(response, '<form')

    def test_add_reminder_post_valid(self):
        """
        Тества POST заявка към add_reminder с валидни данни.
        Очакваме да бъде създадено ново уведомление и пренасочване към последните уведомления.
        """
        # Подготвяме данните за формата
        future_datetime = timezone.now() + timezone.timedelta(days=1)
        message = "Това е напомнянето ми"
        data = {
            'reminder_datetime': future_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'message': message,
        }
        url = reverse('notifications_app:add_reminder')
        response = self.client.post(url, data)
        # Очакваме пренасочване към latest_notifications
        self.assertRedirects(response, reverse('notifications_app:latest_notifications'))
        # Проверяваме, че уведомление е създадено
        notification = Notification.objects.filter(
            recipient=self.user,
            verb__contains=future_datetime.strftime('%Y-%m-%d')
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.description, message)

    def test_add_reminder_post_invalid(self):
        """
        Тества POST заявка към add_reminder с невалидни данни.
        Очакваме да се върне същата страница с грешки във формата.
        """
        # Изпращаме POST заявка без задължителното поле reminder_datetime
        data = {
            'message': 'Липсва напомняне за дата/час'
        }
        url = reverse('notifications_app:add_reminder')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_reminder.html')
        # Проверяваме, че нито едно уведомление не е създадено
        notification_count = Notification.objects.filter(recipient=self.user).count()
        self.assertEqual(notification_count, 0)
