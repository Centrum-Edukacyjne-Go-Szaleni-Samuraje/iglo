# Generated by Django 4.2.9 on 2025-01-18 12:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("league", "0033_alter_player_igor_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="upcoming_reminder_sent",
            field=models.DateTimeField(null=True),
        ),
    ]
