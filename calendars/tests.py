import calendar
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import Calendar, Event
from .views import (
    get_events,
    group_events_by_day,
    build_calendar_weeks,
    get_month_and_year,
    get_month_name,
)
from tasks.models import TodoItem

# Тестове за помощните функции
class CalendarUtilityFunctionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="utiltest", password="testpass")
        # За целите на тестовете задаваме dummy profile
        self.user.profile = SimpleNamespace(display_name="Util Test")
        self.calendar = Calendar.objects.create(name="Util Calendar", join_code="UTIL")
        self.calendar.users.add(self.user)
        self.event1 = Event.objects.create(
            name="Event 1",
            description="",
            date=date(2025, 2, 15),
            time=time(10, 0),
            owner=self.user,
            calendar=self.calendar
        )
        self.event2 = Event.objects.create(
            name="Event 2",
            description="",
            date=date(2025, 2, 15),
            time=time(12, 0),
            owner=self.user,
            calendar=self.calendar
        )

    def test_get_events_no_calendar_selected(self):
        # Когато не е избран конкретен календар, се връщат всички събития за даден месец, към които потребителя има достъп.
        events, selected_calendar, calendars = get_events(self.user, 2025, 2)
        self.assertIsNone(selected_calendar)
        qs_expected = Event.objects.filter(date__year=2025, date__month=2, calendar__users=self.user)
        self.assertQuerysetEqual(events.order_by("id"), qs_expected.order_by("id"), transform=lambda x: x)

    def test_group_events_by_day(self):
        events = [self.event1, self.event2]
        grouped = group_events_by_day(events)
        self.assertIn(15, grouped)
        self.assertEqual(len(grouped[15]), 2)

    def test_build_calendar_weeks(self):
        events_by_day = {15: [self.event1, self.event2]}
        today = date(2025, 2, 15)
        weeks = build_calendar_weeks(2025, 2, today, events_by_day)
        self.assertIsInstance(weeks, list)
        # Търсим деня 15 във всяка седмица и проверяваме, че събитията са правилно групирани и денят е маркиран като "днес"
        found = False
        for week in weeks:
            for day_info in week:
                if day_info['day'] == 15:
                    found = True
                    self.assertTrue(day_info['is_today'])
                    self.assertEqual(len(day_info['events']), 2)
        self.assertTrue(found)

    def test_get_month_and_year(self):
        prev_year, prev_month, next_year, next_month = get_month_and_year(2025, 1)
        self.assertEqual(prev_year, 2024)
        self.assertEqual(prev_month, 12)
        self.assertEqual(next_year, 2025)
        self.assertEqual(next_month, 2)

    def test_get_month_name(self):
        self.assertEqual(get_month_name(1), "Януари")
        self.assertEqual(get_month_name(12), "Декември")


# Тестове за изгледите
class CalendarViewsTests(TestCase):
    def setUp(self):
        # Създаваме тестов потребител и логваме го
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.profile = SimpleNamespace(display_name="Test User")
        self.client = Client()
        self.client.login(username="testuser", password="testpass")
        # Създаваме календар и добавяме потребителя към него
        self.calendar = Calendar.objects.create(name="Test Calendar", join_code="ABC123")
        self.calendar.users.add(self.user)
        # Създаваме втори календар за тестове с присъединяване
        self.other_calendar = Calendar.objects.create(name="Other Calendar", join_code="XYZ789")
        # Създаваме събитие в първия календар
        self.event = Event.objects.create(
            name="Test Event",
            description="Test Description",
            date=date.today(),
            time=time(12, 0),
            owner=self.user,
            calendar=self.calendar
        )
        # Създаваме елемент от задачите
        self.todo = TodoItem.objects.create(
            title="Test Todo",
            description="Test Todo Description",
            deadline=datetime.now() + timedelta(days=1)
        )

    def test_calendar_dashboard_view(self):
        url = reverse("calendars:calendar_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Проверяваме дали контекстът съдържа необходимите променливи
        self.assertIn("calendar_weeks", response.context)
        self.assertIn("calendars", response.context)

    def test_add_event_view_get(self):
        url = reverse("calendars:add_event", args=[self.calendar.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_event.html")

    def test_add_event_view_post(self):
        url = reverse("calendars:add_event", args=[self.calendar.id])
        event_data = {
            "name": "New Event",
            "description": "New Description",
            "date": date.today().strftime("%m-%Y-%d"),
            "time": "14:00",
        }
        response = self.client.post(url, data=event_data)
        # При успешна POST заявка се очаква пренасочване (HTTP 302)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(name="New Event").exists())

    def test_event_detail_view(self):
        url = reverse("calendars:event_detail", args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.name)

    def test_edit_event_view_get(self):
        url = reverse("calendars:edit_event", args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_event.html")

    def test_edit_event_view_post(self):
        url = reverse("calendars:edit_event", args=[self.event.id])
        updated_data = {
            "name": "Updated Event",
            "description": self.event.description,
            "date": self.event.date.strftime("%m-%Y-%d"),
            "time": self.event.time.strftime("%H:%M"),
        }
        response = self.client.post(url, data=updated_data)
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Updated Event")

    def test_delete_event_view(self):
        # Създаваме отделно събитие, което ще изтрием
        event_to_delete = Event.objects.create(
            name="Event to Delete",
            description="Delete me",
            date=date.today(),
            time=time(15, 0),
            owner=self.user,
            calendar=self.calendar
        )
        url = reverse("calendars:delete_event", args=[event_to_delete.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(id=event_to_delete.id).exists())

    def test_add_calendar_view_get(self):
        url = reverse("calendars:add_calendar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_calendar.html")

    def test_add_calendar_view_post(self):
        url = reverse("calendars:add_calendar")
        calendar_data = {"name": "New Calendar", "join_code": "NEWCODE"}
        response = self.client.post(url, data=calendar_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Calendar.objects.filter(name="New Calendar").exists())

    def test_join_calendar_view_get(self):
        url = reverse("calendars:join_calendar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "join_calendar.html")

    def test_join_calendar_view_post_valid(self):
        url = reverse("calendars:join_calendar")
        join_data = {"join_code": "XYZ789"}
        response = self.client.post(url, data=join_data)
        self.assertEqual(response.status_code, 302)
        # Проверяваме дали потребителят сега е член на втория календар
        self.assertIn(self.user, self.other_calendar.users.all())

    def test_join_calendar_view_post_invalid(self):
        url = reverse("calendars:join_calendar")
        join_data = {"join_code": "INVALID"}
        response = self.client.post(url, data=join_data)
        self.assertEqual(response.status_code, 302)
        # При невалиден код потребителят не трябва да бъде добавен към календар

    def test_remove_calendar_view(self):
        # Тъй като self.calendar има само един потребител, след POST заявката той трябва да бъде изтрит
        url = reverse("calendars:remove_calendar", args=[self.calendar.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Calendar.objects.filter(id=self.calendar.id).exists())

    def test_add_from_task_view_get(self):
        url = reverse("calendars:add_from_task", args=[self.todo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_from_task.html")

    def test_add_from_task_view_post_valid(self):
        # За да добавим задачата в календар, трябва потребителят да е член на календара.
        # Добавяме потребителя към other_calendar.
        self.other_calendar.users.add(self.user)
        url = reverse("calendars:add_from_task", args=[self.todo.id])
        post_data = {"join_code": self.other_calendar.join_code}
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        # Проверяваме дали е създадено събитие с името на задачата
        self.assertTrue(Event.objects.filter(name=self.todo.title).exists())

    def test_export_calendar_view(self):
        url = reverse("calendars:export_calendar", args=[self.calendar.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type"), "text/calendar; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", content)