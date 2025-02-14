from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from notifications.models import Notification


class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ivanivanov', password='password123')
        self.client.login(username='ivanivanov', password='password123')

    def test_latest_notifications(self):
        now = timezone.now()
        Notification.objects.create(
            recipient=self.user,
            actor=self.user,
            verb="Тест 1",
            description="Описание 1",
            timestamp=now
        )
        Notification.objects.create(
            recipient=self.user,
            actor=self.user,
            verb="Тест 2",
            description="Описание 2",
            timestamp=now
        )

        url = reverse('notifications_app:latest_notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'latest_notifications.html')
        self.assertContains(response, "Тест 1")
        self.assertContains(response, "Тест 2")

    def test_add_reminder_get(self):
        url = reverse('notifications_app:add_reminder')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_reminder.html')
        self.assertContains(response, '<form')

    def test_add_reminder_post(self):
        future = timezone.now() + timezone.timedelta(days=1)
        message = "Това е напомнянето ми"
        data = {
            'reminder_datetime': future.strftime('%Y-%m-%d %H:%M:%S'),
            'message': message,
        }
        url = reverse('notifications_app:add_reminder')
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('notifications_app:latest_notifications'))

        notification = Notification.objects.filter(recipient=self.user, description=message).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.description, message)

        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 1)