import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from calendars.models import Calendar, Event
from base.models import Profile

class CalendarsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="ivanivanov", password="password123")
        Profile.objects.create(user=self.user, display_name="Иван Иванов")
        self.client.login(username="ivanivanov", password="password123")
        
        self.calendar = Calendar.objects.create(name="Календар", join_code="123456")
        self.calendar.users.add(self.user)
        
        self.event = Event.objects.create(
            name="Събитие",
            description="Описание",
            date=datetime.date.today(),
            time=(datetime.datetime.now() + datetime.timedelta(hours=1)).time(),
            calendar=self.calendar,
            owner=self.user
        )

    def test_calendar_dashboard(self):
        url = reverse("calendars:calendar_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "calendar_dashboard.html")
        self.assertIn("calendar_weeks", response.context)
        self.assertIn("calendars", response.context)

    def test_add_event_get(self):
        url = reverse("calendars:add_event", args=[self.calendar.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_event.html")

    def test_event_detail(self):
        url = reverse("calendars:event_detail", args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get("event").name, self.event.name)

    def test_edit_event_get(self):
        url = reverse("calendars:edit_event", args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_event.html")

    def test_delete_event(self):
        url = reverse("calendars:delete_event", args=[self.event.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("calendars:calendar_dashboard"))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_add_calendar(self):
        url = reverse("calendars:add_calendar")
        data = {"name": "Нов календар"}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("calendars:calendar_dashboard"))
        self.assertTrue(Calendar.objects.filter(name="Нов календар").exists())

    def test_join_calendar(self):
        join_calendar = Calendar.objects.create(name="Календар", join_code="654321")
        url = reverse("calendars:join_calendar")
        data = {"join_code": "654321"}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("calendars:calendar_dashboard"))
        join_calendar.refresh_from_db()
        self.assertIn(self.user, join_calendar.users.all())

    def test_remove_calendar(self):
        url = reverse("calendars:remove_calendar", args=[self.calendar.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("calendars:calendar_dashboard"))
        self.assertFalse(Calendar.objects.filter(id=self.calendar.id).exists())

    def test_export_calendar(self):
        url = reverse("calendars:export_calendar", args=[self.calendar.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type"), "text/calendar; charset=utf-8")
        content_disp = response.get("Content-Disposition", "")
        self.assertIn(f'attachment; filename="calendar_{self.calendar.id}.ics"', content_disp)