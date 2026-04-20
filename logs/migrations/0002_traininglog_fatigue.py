from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='traininglog',
            name='fatigue',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
