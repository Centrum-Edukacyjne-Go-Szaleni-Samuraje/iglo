# Generated by Django 4.2.18 on 2025-05-05 03:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0002_auto_20220123_1539'),
        ('league', '0041_member_ogs_deviation_member_ogs_id_member_ogs_rating_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='assigned_teacher',
            field=models.ForeignKey(blank=True, help_text='Teacher assigned specifically to this game', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_games', to='review.teacher'),
        ),
    ]
