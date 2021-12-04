# Generated by Django 3.2.9 on 2021-11-24 19:15

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='roles',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('teacher', 'Nauczyciel'), ('referee', 'Sędzia')], max_length=32), default=list, size=None),
        ),
    ]
