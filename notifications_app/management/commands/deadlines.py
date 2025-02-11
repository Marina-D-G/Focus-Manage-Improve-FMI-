from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.signals import notify
from calendars.models import Event
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        upcoming_threshold = now + timedelta(hours=1)
        events = Event.objects.filter(deadline__gte=now, deadline__lte=upcoming_threshold, notification_sent=False)

        for event in events:
            recipients = event.calendar.users
            notify.send(
                event.owner,
                recipient=recipients,
                verb='Наближаващо събитие',
                description=f'"{event.title}" наближава! Планирано е за {event.deadline}. ',
                target=event,
            )
            event.notification_sent = True
            event.save()