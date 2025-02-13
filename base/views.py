import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now
from .forms import ProfileUpdateForm
from .models import Profile
from tasks.models import TodoItem
from calendars.models import Event 
from translate import Translator

def get_info_homepage(request):
    notifications_list = list(request.user.notifications.unread())
    request.user.notifications.mark_all_as_read()
    quote, author = random_quotes()
    today = now().date()
    unfinished_tasks_count = TodoItem.objects.filter(deadline=today, todo_list__users=request.user).count()
    today_events_count = Event.objects.filter(date=today, calendar__users=request.user).count()
    context = {
        "notifications_list": notifications_list,
        "quote": quote,
        "author": author,
        "unfinished_tasks_count": unfinished_tasks_count,
        "today_events_count": today_events_count
    }
    return context


def home(request):
    if request.user.is_authenticated:
        context = get_info_homepage(request)
        return render(request, "home_logged_in.html", context)
    else:
        return render(request, "home_guest.html")


def sign_up(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            return redirect("base:login")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    is_owner = (request.user == user)
    context = {
        'profile': profile,
        'is_owner': is_owner,
    }
    return render(request, 'profile.html', context)


@login_required
def update_profile(request):
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect('base:profile', username=request.user.username)
    else:
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'update_profile.html', {'profile_form': profile_form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('change_password')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'change_password.html', {'form': form})


def translate_text(text):
    translator = Translator(to_lang="bg")
    translated_text = translator.translate(text)
    return translated_text


def random_quotes():
    quote_api_url = 'https://zenquotes.io/api/random'
    response = requests.get(quote_api_url)

    quote_text = "No quote available"
    author = "Unknown"

    if response.status_code == 200:
        quote_data = response.json()
        if isinstance(quote_data, list) and len(quote_data) > 0:
            quote_text = quote_data[0].get('q', "No quote available")
            author = quote_data[0].get('a', "Unknown")

    translated_quote = translate_text(quote_text)
    translated_author = translate_text(author)
    return translated_quote, translated_author