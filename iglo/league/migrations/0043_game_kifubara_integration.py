# Generated manually for Kifubara integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0042_game_assigned_teacher'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='kifubara_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='GameKifubaraUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sgf_hash', models.CharField(max_length=32, null=True)),
                ('status', models.CharField(choices=[('in_progress', 'in_progress'), ('done', 'done'), ('failed', 'failed')], max_length=16)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('error', models.TextField()),
                ('result', models.URLField(null=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kifubara_uploads', to='league.game')),
            ],
        ),
    ]
