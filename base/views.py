from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProfileUpdateForm
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from .models import Profile
from notifications.signals import notify
from notifications.models import Notification

def home(request):
    if request.user.is_authenticated:
        notifications_list = list(request.user.notifications.unread())
        request.user.notifications.mark_all_as_read()
        return render(request, "home_logged_in.html", {"notifications_list": notifications_list})
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

def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile = user_obj.profile
    is_owner = (request.user == user_obj)
    context = {
        'profile': profile,
        'is_owner': is_owner,
    }
    return render(request, 'profile.html', context)

def update_profile(request):
    profile = request.user.profile
    username = request.user.username
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        password_form = PasswordChangeForm(user=request.user, data=request.POST)
        
        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            user = password_form.save()
            update_session_auth_hash(request, user)
            return redirect('base:profile', username)
    else:
        profile_form = ProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(user=request.user)
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'update_profile.html', context)

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
