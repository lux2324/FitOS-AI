from django.db import models
from django.conf import settings
from plans.models import PlannedSession, PlannedExercise


class TrainingLog(models.Model):
    """One completed (or in-progress) workout session."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="training_logs")
    planned_session = models.ForeignKey(PlannedSession, on_delete=models.SET_NULL,
                                        null=True, related_name="logs")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_finished = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        name = self.planned_session.name if self.planned_session else "?"
        return f"{self.user} — {name} ({self.started_at:%Y-%m-%d})"

    @property
    def duration_seconds(self):
        if self.ended_at and self.started_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return None

    @property
    def total_volume_kg(self):
        total = 0
        for ex in self.logged_exercises.prefetch_related("sets").all():
            for s in ex.sets.filter(completed=True):
                if s.weight_kg and s.reps_done:
                    total += float(s.weight_kg) * s.reps_done
        return round(total, 1)


class LoggedExercise(models.Model):
    """One exercise within a TrainingLog."""
    training_log = models.ForeignKey(TrainingLog, on_delete=models.CASCADE,
                                     related_name="logged_exercises")
    planned_exercise = models.ForeignKey(PlannedExercise, on_delete=models.SET_NULL,
                                         null=True, related_name="logged_instances")
    order = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} (log #{self.training_log_id})"

    @property
    def is_done(self):
        target = self.planned_exercise.sets if self.planned_exercise else 3
        return self.sets.filter(completed=True).count() >= target


class LoggedSet(models.Model):
    """One set within a LoggedExercise."""
    logged_exercise = models.ForeignKey(LoggedExercise, on_delete=models.CASCADE,
                                        related_name="sets")
    set_number = models.PositiveSmallIntegerField()
    weight_kg = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    reps_done = models.PositiveSmallIntegerField(null=True, blank=True)
    rpe_done = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    completed = models.BooleanField(default=False)
    logged_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["set_number"]
        unique_together = [("logged_exercise", "set_number")]

    def __str__(self):
        return f"{self.logged_exercise.name} set {self.set_number}"
