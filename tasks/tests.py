from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from .models import TodoList, TodoItem


class TasksTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="ivanivanov", password="password123")
        self.client.login(username="ivanivanov", password="password123")

        self.todo_list = TodoList.objects.create(name="Списък")
        self.todo_list.users.add(self.user)

        self.task = TodoItem.objects.create(
            todo_list=self.todo_list,
            title="Задача",
            description="Описание",
            deadline=timezone.now() + timedelta(days=7),
            priority=2,
            phase="todo"
        )

    def test_tasks(self):
        url = reverse('tasks:tasks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)

        response = self.client.get(url, {'list': self.todo_list.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Списък")

    def test_add_task(self):
        url = reverse('tasks:add_task', kwargs={'list_id': self.todo_list.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        deadline = timezone.now() + timedelta(days=7)
        form_data = {
            'title': 'Нова задача',
            'description': 'Ново описание',
            'deadline': deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'priority': 2,
            'phase': 'todo'
        }
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TodoItem.objects.filter(title='Нова задача').exists())

    def test_add_task_notification(self):
        url = reverse('tasks:add_task', kwargs={'list_id': self.todo_list.id})
        deadline = timezone.now() + timedelta(days=7)
        for i in range(5):
            TodoItem.objects.create(
                todo_list=self.todo_list,
                title=f"Задача {i}",
                description=f"Описание {i}",
                deadline=deadline,
                priority=2,
                phase="todo"
            )
        form_data = {
            'title': 'Тестова задача',
            'description': 'Тест',
            'deadline': deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'priority': 2,
            'phase': 'todo'
        }

        with patch('tasks.views.notify.send') as mock_notify:
            response = self.client.post(url, data=form_data)
            self.assertEqual(response.status_code, 302)
            mock_notify.assert_called_once()

    def test_delete_list(self):
        url = reverse('tasks:delete_list', kwargs={'list_id': self.todo_list.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TodoList.objects.filter(id=self.todo_list.id).exists())

    def test_mark_done(self):
        url = reverse('tasks:mark_done', kwargs={'task_id': self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.phase, 'done')

    def test_edit_task(self):
        url = reverse('tasks:edit_task', kwargs={'task_id': self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        form_data = {
            'title': 'Редактирана задача',
            'description': self.task.description,
            'deadline': self.task.deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'priority': self.task.priority,
            'phase': self.task.phase
        }
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Редактирана задача')

    def test_delete_task(self):
        url = reverse('tasks:delete_task', kwargs={'task_id': self.task.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TodoItem.objects.filter(id=self.task.id).exists())

    def test_add_list(self):
        url = reverse('tasks:add_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data={'name': 'Нов списък'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TodoList.objects.filter(name='Нов списък').exists())

    def test_join_list(self):
        new_list = TodoList.objects.create(name="Списък")
        join_code = new_list.join_code
        url = reverse('tasks:join_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data={'join_code': join_code})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(new_list.users.filter(id=self.user.id).exists())
 
        response = self.client.post(url, data={'join_code': '000000'})
        self.assertEqual(response.status_code, 200)