# Generated by Django 3.2.7 on 2021-11-10 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0007_alter_season_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='points_difference',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
        ),
    ]
