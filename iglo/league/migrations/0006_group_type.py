# Generated by Django 3.2.7 on 2021-11-07 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0005_auto_20211106_0747'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='type',
            field=models.CharField(choices=[('round_robin', 'Każdy z każdym'), ('mcmahon', 'McMahon')], default='round_robin', max_length=16),
            preserve_default=False,
        ),
    ]
