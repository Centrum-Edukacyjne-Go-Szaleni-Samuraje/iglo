# Generated by Django 3.2.9 on 2022-01-20 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0001_initial'),
        ('league', '0018_alter_group_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='teacher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='groups', to='review.teacher'),
        ),
    ]
