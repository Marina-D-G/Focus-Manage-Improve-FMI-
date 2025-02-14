from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from .models import Profile
from base.views import random_quotes, translate_text

class BaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="ivanivanov", password="password123")
        self.profile = Profile.objects.create(user=self.user, display_name="Иван Иванов")

    def test_home_guest(self):
        response = self.client.get(reverse("base:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home_guest.html")

    @patch('base.views.random_quotes', return_value=("Преведен цитат", "Автор"))
    def test_home_logged_in(self, _):
        self.client.login(username="ivanivanov", password="password123")
        response = self.client.get(reverse("base:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home_logged_in.html")
        self.assertEqual(response.context.get("quote"), "Преведен цитат")
        self.assertEqual(response.context.get("author"), "Автор")

    def test_sign_up(self):
        user_count = User.objects.count()
        data = {
            "username": "PetarPetrov",
            "password1": "Password123!",
            "password2": "Password123!"
        }
        response = self.client.post(reverse("base:sign_up"), data)
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertRedirects(response, reverse("base:login"))

    def test_profile_view(self):
        self.client.login(username="ivanivanov", password="password123")
        response = self.client.get(reverse("base:profile", kwargs={"username": "ivanivanov"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")
        self.assertEqual(response.context.get("profile").user.username, "ivanivanov")

    def test_update_profile(self):
        self.client.login(username="ivanivanov", password="password123")
        response = self.client.get(reverse("base:update_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "update_profile.html")

    def test_change_password_get(self):
        self.client.login(username="ivanivanov", password="password123")
        response = self.client.get(reverse("base:password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "password_change.html")

    def test_change_password_post(self):
        self.client.login(username="ivanivanov", password="password123")
        response = self.client.post(reverse("base:password_change"), {
            "old_password": "password123",
            "new_password1": "Newpassword123",
            "new_password2": "Newpassword123",
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Newpassword123"))

    @patch("base.views.requests.get")
    @patch("base.views.translate_text", lambda x: x)
    def test_random_quotes_api(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"q": "Test Quote", "a": "Test Author"}]
        quote, author = random_quotes()
        self.assertEqual(quote, "Test Quote")
        self.assertEqual(author, "Test Author")

    @patch("base.views.Translator.translate", return_value="Тест")
    def test_translate_text(self, _):
        self.assertEqual(translate_text("Test"), "Тест")