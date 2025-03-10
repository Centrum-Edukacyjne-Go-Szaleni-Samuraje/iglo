# Generated by Django 4.2.18 on 2025-03-06 08:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("league", "0037_group_point_difference_alter_member_initial_score"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="is_egd",
            field=models.BooleanField(
                default=False,
                help_text="Deprecated. Games are now eligible for EGD export based on individual player approvals.",
            ),
        ),
    ]
