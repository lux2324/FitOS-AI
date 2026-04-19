from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WeeklyFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_start', models.DateField(help_text='Ponedjeljak te tjedne')),
                ('sleep_quality', models.IntegerField(default=3, help_text='1-5 (1=lose, 5=odlicno)')),
                ('stress_level', models.IntegerField(default=3, help_text='1-5 (1=nizak, 5=visok)')),
                ('doms_level', models.IntegerField(default=1, help_text='1-5 (1=nema, 5=jaka)')),
                ('training_notes', models.TextField(blank=True)),
                ('ai_summary', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='weekly_feedbacks',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-week_start'],
                'unique_together': {('user', 'week_start')},
            },
        ),
    ]
