from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from notifications.signals import notify
from .models import Note, NoteImage
from .forms import NoteForm, NoteImageForm, NoteEditForm, CodeForm


def create_note_image(note, image):
    if image:
        NoteImage.objects.create(note=note, image=image)


@login_required
def notes_dashboard(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    category = request.GET.get('category')
    if category:
        notes = notes.filter(category=category)
    return render(request, 'notes_dashboard.html', {'notes': notes})


@login_required
def add_note(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        image_form = NoteImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            image = image_form.cleaned_data.get('image')
            create_note_image(note, image)
            messages.success(request, "Бележката е добавена успешно!")
            return redirect('notes:notes_dashboard')
    else:
        form = NoteForm()
        image_form = NoteImageForm()

    context = {
        'form': form,
        'image_form': image_form,
    }
    return render(request, 'add_note.html', context)


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    return redirect('notes:notes_dashboard')


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    if request.method == 'POST':
        form = NoteEditForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            note = form.save()
            image = form.cleaned_data.get('image')
            create_note_image(note, image)
            return redirect('notes:notes_dashboard')
    else:
        form = NoteEditForm(instance=note)

    context = {
        'form': form,
        'note': note,
    }
    return render(request, 'edit_note.html', context)


@login_required
def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    return render(request, 'note_detail.html', {'note': note})


@login_required
def view_note(request):
    if request.method == "POST":
        form = CodeForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data["join_code"]
            try:
                note = Note.objects.get(join_code=join_code)
                notify.send(
                    request.user,
                    recipient=note.user,
                    verb=f'{request.user.profile.display_name} прегледа бележка "{note.title}"'
                )
                return redirect("notes:note_detail", note_id=note.id)
            except Note.DoesNotExist:
                messages.error(request, "Невалиден код!")
    else:
        form = CodeForm()

    return render(request, "view_note_through_code.html", {"form": form})


@login_required
def delete_image(request, image_id):
    if request.method == 'POST':
        image_obj = get_object_or_404(NoteImage, id=image_id)
        if image_obj.image:
            image_obj.image.delete()
        image_obj.delete()
        next_url = request.META.get('HTTP_REFERER', 'notes:notes_dashboard')
        return redirect(next_url)
    return redirect('notes:notes_dashboard')