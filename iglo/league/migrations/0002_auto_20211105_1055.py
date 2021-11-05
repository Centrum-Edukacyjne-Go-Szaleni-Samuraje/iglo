# Generated by Django 3.2.7 on 2021-11-05 10:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='win_type',
            field=models.CharField(choices=[('points', 'Punkty'), ('resign', 'Rezygnacja'), ('time', 'Czas'), ('not_played', 'Nierozegrana')], max_length=16, null=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='winner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='won_games', to='league.member'),
        ),
    ]
