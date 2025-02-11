from django.shortcuts import render, redirect, get_object_or_404
from .models import Note, NoteImage
from .forms import NoteForm, NoteImageForm, NoteEditForm, CodeForm
from django.contrib import messages

def notes_dashboard(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notes_dashboard.html', {'notes': notes})

def add_note(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        image_form = NoteImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            image = image_form.cleaned_data.get('image')
            if image:
                NoteImage.objects.create(note=note, image=image)
            return redirect('notes:notes_dashboard')
    else:
        form = NoteForm()
        image_form = NoteImageForm()

    return render(request, 'add_note.html', {'form': form, 'image_form': image_form})

def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    return redirect('notes:notes_dashboard')

def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)

    if request.method == 'POST':
        form = NoteEditForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            note = form.save()
            image = form.cleaned_data.get('image')
            if image:
                NoteImage.objects.create(note=note, image=image)
            return redirect('notes:notes_dashboard')
    else:
        form = NoteEditForm(instance=note)
    return render(request, 'edit_note.html', {'form': form, 'note': note})

def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    return render(request, 'note_detail.html', {'note': note})

def view_note(request):
    if request.method == "POST":
        form = CodeForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data["join_code"]
            try:
                note = Note.objects.get(join_code=join_code)
                return redirect("notes:note_detail", note_id=note.id)
            except Note.DoesNotExist:
                messages.error(request, "Невалиден код!")
    else:
        form = CodeForm()

    return render(request, "view_note_through_code.html", {"form": form})

def delete_image(request, image_id):
    if request.method == 'POST':
        image_obj = get_object_or_404(NoteImage, id=image_id)
        if image_obj.image:
            image_obj.image.delete()
        image_obj.delete()
        next_url = request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
    return redirect('notes:notes_dashboard')