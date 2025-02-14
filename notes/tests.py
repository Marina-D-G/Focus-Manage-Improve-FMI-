from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Note, NoteImage
from base.models import Profile


class NoteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="ivanivanov", password="password123")
        Profile.objects.create(user=self.user, display_name="Иван Иванов")
        self.client.login(username="ivanivanov", password="password123")
        self.note = Note.objects.create(
            user=self.user,
            title="Бележка",
            content="Бележка",
            category="work"
        )

    def test_notes_dashboard(self):
        url = reverse("notes:notes_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.note.title)

        url_with_category = f"{url}?category=work"
        response = self.client.get(url_with_category)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.note.title)

    def test_add_note_get(self):
        url = reverse("notes:add_note")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_note.html")

    def test_add_note_post(self):
        url = reverse("notes:add_note")
        data = {
            "title": "Нова бележка",
            "content": "Бележка",
            "category": "work",
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse("notes:notes_dashboard"))
        self.assertTrue(Note.objects.filter(title="Нова бележка").exists())

    def test_delete_note(self):
        url = reverse("notes:delete_note", kwargs={"note_id": self.note.id})
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse("notes:notes_dashboard"))
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_edit_note_get(self):
        url = reverse("notes:edit_note", kwargs={"note_id": self.note.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_note.html")

    def test_edit_note_post(self):
        url = reverse("notes:edit_note", kwargs={"note_id": self.note.id})
        data = {
            "title": "Редактирана бележка",
            "content": "Редактирано",
            "category": "work",
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse("notes:notes_dashboard"))
        updated_note = Note.objects.get(id=self.note.id)
        self.assertEqual(updated_note.title, "Редактирана бележка")

    def test_note_detail(self):
        url = reverse("notes:note_detail", kwargs={"note_id": self.note.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.note.title)

    def test_view_note_post_valid(self):
        url = reverse("notes:view_note")
        data = {"join_code": self.note.join_code}
        response = self.client.post(url, data, follow=True)
        expected_url = reverse("notes:note_detail", kwargs={"note_id": self.note.id})
        self.assertRedirects(response, expected_url)

    def test_view_note_post_invalid(self):
        url = reverse("notes:view_note")
        data = {"join_code": "000000"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_delete_image(self):
        image_file = SimpleUploadedFile("delete.jpg", b"delete_content", content_type="image/jpeg")
        note_image = NoteImage.objects.create(note=self.note, image=image_file)
        url = reverse("notes:delete_image", kwargs={"image_id": note_image.id})
        response = self.client.post(url, HTTP_REFERER=reverse("notes:notes_dashboard"))
        self.assertRedirects(response, reverse("notes:notes_dashboard"))
        self.assertFalse(NoteImage.objects.filter(id=note_image.id).exists())

    def test_dashboard_requires_login(self):
        url = reverse("notes:notes_dashboard")
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f"/accounts/login/?next={url}")  