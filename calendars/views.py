from django.shortcuts import render, redirect, get_object_or_404
from .models import Event, Calendar
from .forms import EventForm
from datetime import date
import calendar


def calendar_day(request):
    user = request.user 
    events = Event.objects.filter(users=user)
    return render(request, "calendar_day.html", {"events": events})

def calendar_week(request):
    user = request.user 
    events = Event.objects.filter(users=user)
    return render(request, "calendar_week.html", {"events": events})

def calendar_month(request):
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
    
    return render(request, 'calendar_month.html', context)

def add_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.owner = request.user
            event.save()
            return redirect('calendars:calendar_month')
    else:
        form = EventForm()
    
    return render(request, "add_event.html", {"form": form})

def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'event_detail.html', {'event': event})