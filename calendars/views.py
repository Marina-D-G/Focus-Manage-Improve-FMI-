import calendar
import datetime
from icalendar import Calendar as ICalendar, Event as ICalEvent
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from .models import Event, Calendar
from tasks.models import TodoItem
from .forms import EventForm, CalendarForm, JoinCalendarForm
from notifications.signals import notify


def calendar_dashboard(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    selected_calendar_id = request.GET.get('calendar_id', None)
    selected_calendar = None

    calendars = Calendar.objects.filter(users=request.user)
    
    if not calendars.exists():
        events_qs = Event.objects.filter(
            date__year=year,
            date__month=month,
            owner=request.user
        )
    elif not selected_calendar_id:
        events_qs = Event.objects.filter(
            date__year=year,
            date__month=month,
            calendar__users=request.user
        )   
    else:
        selected_calendar = calendars.filter(id=selected_calendar_id).first()
        events_qs = Event.objects.filter(
            date__year=year,
            date__month=month,
            calendar=selected_calendar
        )
    
    events_by_day = {}
    for event in events_qs:
        day = event.date.day
        events_by_day.setdefault(day, []).append(event)
    
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    calendar_weeks = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({
                    'day': None,
                    'events': [],
                    'is_today': False,
                })
            else:
                week_data.append({
                    'day': day,
                    'events': events_by_day.get(day, []),
                    'is_today': (day == today.day and month == today.month and year == today.year),
                })
        calendar_weeks.append(week_data)
    
    month_names = {
        1: "Януари", 2: "Февруари", 3: "Март", 4: "Април", 5: "Май", 6: "Юни",
        7: "Юли", 8: "Август", 9: "Септември", 10: "Октомври", 11: "Ноември", 12: "Декември"
    }
    month_name = month_names.get(month, "")
    
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
    
    if not selected_calendar:
        upcoming_events = events_qs.filter(
            date__gte=today,
        ).order_by('date')
    else:
        upcoming_events = events_qs.filter(
            date__gte=today,
            calendar=selected_calendar
        ).order_by('date')

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

def add_event(request, selected_calendar_id):
    selected_calendar_id = int(selected_calendar_id)
    user_calendar = Calendar.objects.filter(id=selected_calendar_id, users=request.user).first()
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.owner = request.user
            event.calendar = user_calendar
            event.save()
            notify.send(
                request.user,
                recipient=user_calendar.users.all(),
                verb=f'{request.user.profile.display_name} добави "{event.name}" към календар {user_calendar.name}'
            )
            return redirect('calendars:calendar_dashboard')
    else:
        form = EventForm()
    
    context = {
        "form": form,
        "selected_calendar_id": selected_calendar_id,
        "user_calendar": user_calendar
    }
    return render(request, "add_event.html", context)

def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    request_user = request.user
    return render(request, 'event_detail.html', {'event': event, 'request_user': request_user})

def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Събитието беше успешно редактирано!")
            return redirect("calendars:calendar_dashboard")
    else:
        form = EventForm(instance=event)
    
    return render(request, "edit_event.html", {"form": form, "event": event})

def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Събитието беше изтрито успешно!")
        return redirect("calendars:calendar_dashboard")

def add_calendar(request):
    if request.method == "POST":
        form = CalendarForm(request.POST)
        if form.is_valid():
            calendar_new = form.save(commit=False)
            calendar_new.save()
            calendar_new.users.add(request.user)
            return redirect("calendars:calendar_dashboard")
    else:
        form = CalendarForm()
   
    return render(request, "add_calendar.html", {"form": form})


def join_calendar(request):
    if request.method == "POST":
        form = JoinCalendarForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data["join_code"]
            try:
                calendar_to_join = Calendar.objects.get(join_code=join_code)
                calendar_to_join.users.add(request.user)
                messages.success(request, f"Успешно се присъединихте към '{calendar_to_join.name}'!")
                notify.send(
                    request.user,
                    recipient=calendar_to_join.users.all(),
                    verb=f'{request.user.profile.display_name} се присъедини към календар {calendar_to_join.name}'
                )
                return redirect("calendars:calendar_dashboard")
            except Calendar.DoesNotExist:
                messages.error(request, "Невалиден код!")
    else:
        form = JoinCalendarForm()

    return render(request, "join_calendar.html", {"form": form})

def remove_calendar(request, calendar_id):
    if request.method == "POST":
        calendar = get_object_or_404(Calendar, id=calendar_id)
        if calendar.users.count() <= 1:
            calendar.delete()
        else:
            calendar.users.remove(request.user)

        return redirect('calendars:calendar_dashboard')
    
def add_from_task(request, task_id):
    task = TodoItem.objects.get(id=task_id)
    
    if request.method == "POST":
        form = JoinCalendarForm(request.POST)
        if form.is_valid():
            calendar_code = form.cleaned_data['join_code']
            try:
                calendar = Calendar.objects.get(join_code=calendar_code, users=request.user)
            except Calendar.DoesNotExist:
                messages.error(request, "Невалиден код. Моля, опитайте отново.")
                return redirect("calendars:calendar_dashboard")
            
            event = Event.objects.create(
                name=task.title,
                description= f"Това е крайният срок за задача {task.title}. {task.description}",
                date=task.deadline.date(),
                time=task.deadline.time(),
                owner=request.user,
                calendar=calendar
            )

            notify.send(
                request.user,
                recipient=calendar.users.all(),
                verb=f'{request.user.profile.display_name} добави задача {task.title} към календар {calendar.name}',
                description=f'Крайният срок на задачата е {{ event.date|date:"d.m.Y" }}.'
            )

            messages.success(request, f"Задачата '{task.title}' беше добавена към календара!")
            return redirect("tasks:tasks")
    else:
        form = JoinCalendarForm()
    
    return render(request, "add_from_task.html", {"task": task, "form": form})

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
        ical_event.add('uid', f'{event.id}@example.com')
        ical_event.add('summary', event.name)
        dtstart = datetime.datetime.combine(event.date, event.time).replace(tzinfo=utc)
        ical_event.add('dtstart', dtstart)
        dtend = dtstart + datetime.timedelta(hours=1)
        ical_event.add('dtend', dtend)
        ical_event.add('dtstamp', datetime.datetime.now(utc))
        cal.add_component(ical_event)

    ics_content = cal.to_ical()

    ics_str = ics_content.decode('utf-8')
    ics_str = ics_str.replace('\r\n', '\n').replace('\r', '\n')
    ics_str = ics_str.replace('\n', '\r\n')
    ics_content = ics_str.encode('utf-8')

    response = HttpResponse(ics_content, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="calendar_{calendar_obj.id}.ics"'
    return response

