# Generated by Django 5.1.4 on 2024-12-26 15:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_todoitem_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todoitem',
            name='deadline',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2025, 1, 2, 17, 26, 37, 337759)),
        ),
    ]
