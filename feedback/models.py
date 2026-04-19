from django.db import models
from django.conf import settings


class WeeklyFeedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weekly_feedbacks',
    )
    week_start = models.DateField(help_text='Ponedjeljak te tjedne')
    sleep_quality = models.IntegerField(
        help_text='1-5 (1=lose, 5=odlicno)',
        default=3,
    )
    stress_level = models.IntegerField(
        help_text='1-5 (1=nizak, 5=visok)',
        default=3,
    )
    doms_level = models.IntegerField(
        help_text='1-5 (1=nema, 5=jaka)',
        default=1,
    )
    training_notes = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = [('user', 'week_start')]

    def __str__(self):
        return f"Feedback -- {self.user} -- {self.week_start}"
