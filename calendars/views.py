import calendar
import datetime
from datetime import date
from icalendar import Calendar as ICalendar, Event as ICalEvent
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from notifications.signals import notify
from . import decorators
from .forms import EventForm, CalendarForm, JoinCalendarForm
from .models import Event, Calendar
from tasks.models import TodoItem


def get_events(user, year, month, selected_calendar_id=None):
    calendars = Calendar.objects.filter(users=user)
    if not calendars.exists():
        events = Event.objects.filter(date__year=year, date__month=month, owner=user)
        return events, None, calendars

    if not selected_calendar_id:
        events = Event.objects.filter(date__year=year, date__month=month, calendar__users=user)
        return events, None, calendars

    selected_calendar = calendars.filter(id=selected_calendar_id).first()
    events = Event.objects.filter(date__year=year, date__month=month, calendar=selected_calendar)
    return events, selected_calendar, calendars


def group_events_by_day(events):
    events_by_day = {}
    for event in events:
        day = event.date.day
        events_by_day.setdefault(day, []).append(event)
    return events_by_day


def build_calendar_weeks(year, month, today, events_by_day):
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    weeks = []

    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': None, 'events': [], 'is_today': False})
            else:
                week_data.append({
                    'day': day,
                    'events': events_by_day.get(day, []),
                    'is_today': (day == today.day and month == today.month and year == today.year)
                })
        weeks.append(week_data)
    return weeks


def get_month_and_year(year, month):
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    return prev_year, prev_month, next_year, next_month


def get_month_name(month):
    month_names = [
        "Януари", "Февруари", "Март", "Април", "Май", "Юни",
        "Юли", "Август", "Септември", "Октомври", "Ноември", "Декември"
    ]
    return month_names[month - 1]


def add_notifications(user, event, user_calendar):
    notify.send(
        user,
        recipient=user_calendar.users.all(),
        verb=f'{user.profile.display_name} добави "{event.name}" към календар {user_calendar.name}'
    )
    all_events = Event.objects.filter(calendar=user_calendar, date=event.date)
    if all_events.count() > 3:
        notify.send(
            user,
            recipient=user_calendar.users.all(),
            verb=(
                f'Внимание! На {event.date} имате повече от 3 събития в календар '
                f'{user_calendar.name}. Помислете за почивка!'
            )
        )


@login_required
@decorators.check_user
def calendar_dashboard(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    selected_calendar_id = request.GET.get('calendar_id')

    events, selected_calendar, calendars = get_events(request.user, year, month, selected_calendar_id)
    events_by_day = group_events_by_day(events)
    calendar_weeks = build_calendar_weeks(year, month, today, events_by_day)
    prev_year, prev_month, next_year, next_month = get_month_and_year(year, month)
    month_name = get_month_name(month)

    if not selected_calendar:
        upcoming_events = events.filter(date__gte=today).order_by('date')
    else:
        upcoming_events = events.filter(date__gte=today, calendar=selected_calendar).order_by('date')

    context = {
        'calendar_weeks': calendar_weeks,
        'year': year,
        'month': month,
        'month_name': month_name,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'upcoming_events': upcoming_events,
        'calendars': calendars,
        'selected_calendar': selected_calendar,
        'selected_calendar_id': selected_calendar_id,
    }
    return render(request, 'calendar_dashboard.html', context)


@login_required
@decorators.check_user
def add_event(request, selected_calendar_id):
    try:
        selected_calendar_id = int(selected_calendar_id)
    except ValueError:
        return redirect('calendars:calendar_dashboard')

    user_calendar = Calendar.objects.filter(id=selected_calendar_id, users=request.user).first()
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.owner = request.user
            event.calendar = user_calendar
            event.save()
            add_notifications(request.user, event, user_calendar)
            messages.success(request, "Събитието беше добавено успешно!")
            return redirect('calendars:calendar_dashboard')
    else:
        form = EventForm()

    context = {
        "form": form,
        "selected_calendar_id": selected_calendar_id,
        "user_calendar": user_calendar,
    }
    return render(request, "add_event.html", context)


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'event_detail.html', {'event': event, 'request_user': request.user})


@login_required
@decorators.check_owner
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Събитието беше редактирано успешно!")
            return redirect("calendars:calendar_dashboard")
    else:
        form = EventForm(instance=event)

    return render(request, "edit_event.html", {"form": form, "event": event})


@login_required
@decorators.check_owner
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Събитието беше изтрито успешно!")
        return redirect("calendars:calendar_dashboard")
    return redirect("calendars:calendar_dashboard")


@login_required
def add_calendar(request):
    if request.method == "POST":
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendar_new = form.save(commit=False)
            calendar_new.save()
            calendar_new.users.add(request.user)
            messages.success(request, "Календарът беше добавен успешно!")
            return redirect("calendars:calendar_dashboard")
    else:
        form = CalendarForm()

    return render(request, "add_calendar.html", {"form": form})


@login_required
def join_calendar(request):
    if request.method == "POST":
        form = JoinCalendarForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data["join_code"]
            try:
                calendar_to_join = Calendar.objects.get(join_code=join_code)
                calendar_to_join.users.add(request.user)
                notify.send(
                    request.user,
                    recipient=calendar_to_join.users.all(),
                    verb=(f'{request.user.profile.display_name} се присъедини към календар 'f'{calendar_to_join.name}')
                )
                messages.success(request, "Присъединихте се успешно към календара!")
                return redirect("calendars:calendar_dashboard")
            except Calendar.DoesNotExist:
                messages.warning(request, "Невалиден код!")
                return redirect("calendars:calendar_dashboard")
    else:
        form = JoinCalendarForm()

    return render(request, "join_calendar.html", {"form": form})


@login_required
@decorators.check_user
def remove_calendar(request, calendar_id):
    if request.method == "POST":
        calendar_obj = get_object_or_404(Calendar, id=calendar_id)
        if calendar_obj.users.count() <= 1:
            calendar_obj.delete()
        else:
            calendar_obj.users.remove(request.user)
        messages.success(request, "Календарът е изтрит успешно!")
        return redirect('calendars:calendar_dashboard')


@login_required
@decorators.check_user
def add_from_task(request, task_id):
    task = get_object_or_404(TodoItem, id=task_id)
    if request.method == "POST":
        form = JoinCalendarForm(request.POST)
        if form.is_valid():
            calendar_code = form.cleaned_data['join_code']
            try:
                calendar_obj = Calendar.objects.get(join_code=calendar_code, users=request.user)
            except Calendar.DoesNotExist:
                messages.warning(request, "Невалиден код!")
                return redirect("calendars:calendar_dashboard")

            event = Event.objects.create(
                name=task.title,
                description=f"Това е крайният срок за задача {task.title}. {task.description}",
                date=task.deadline.date(),
                time=task.deadline.time(),
                owner=request.user,
                calendar=calendar_obj
            )

            notify.send(
                request.user,
                recipient=calendar_obj.users.all(),
                verb=(f'{request.user.profile.display_name} добави задача {task.title} към календар 'f'{calendar_obj.name}'),
                description=f'Крайният срок на задачата е {event.date.strftime("%d.%m.%Y")}.'
            )
            messages.success(request, f"Задачата '{task.title}' беше добавена към календара!")
            return redirect("tasks:tasks")
    else:
        form = JoinCalendarForm()

    return render(request, "add_from_task.html", {"task": task, "form": form})


@login_required
@decorators.check_user
def export_calendar(request, calendar_id):
    calendar_obj = get_object_or_404(Calendar, id=calendar_id, users=request.user)
    events = Event.objects.filter(calendar=calendar_obj)

    cal = ICalendar()
    cal.add('prodid', '-//Моят календар //BG')
    cal.add('calscale', 'GREGORIAN')
    cal.add('version', '2.0')

    utc = datetime.timezone.utc

    for event in events:
        ical_event = ICalEvent()
        ical_event.add('uid', str(event.id))
        ical_event.add('summary', event.name)
        dtstart = datetime.datetime.combine(event.date, event.time).replace(tzinfo=utc)
        ical_event.add('dtstart', dtstart)
        dtend = dtstart + datetime.timedelta(hours=1)
        ical_event.add('dtend', dtend)
        ical_event.add('dtstamp', datetime.datetime.now(utc))
        cal.add_component(ical_event)

    ics_content = cal.to_ical()
    ics_str = ics_content.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    ics_str = ics_str.replace('\n', '\r\n')
    ics_content = ics_str.encode('utf-8')

    response = HttpResponse(ics_content, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="calendar_{calendar_obj.id}.ics"'
    return response