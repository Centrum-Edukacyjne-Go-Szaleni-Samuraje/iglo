# Generated by Django 4.2.18 on 2025-03-11 21:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("league", "0039_add_egd_approval_to_member"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="ogs_deviation",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="player",
            name="ogs_rating",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
