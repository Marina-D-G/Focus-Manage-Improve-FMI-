# Generated by Django 5.1.4 on 2024-12-27 10:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_alter_todoitem_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todoitem',
            name='deadline',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2025, 1, 3, 12, 13, 33, 94750)),
        ),
    ]
