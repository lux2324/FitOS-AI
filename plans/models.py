from django.db import models
from django.conf import settings


class WeeklyPlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weekly_plans",
    )
    week_number = models.PositiveIntegerField(default=1)
    split_type = models.CharField(max_length=40)  # e.g. "push_pull_legs_upper"
    days_per_week = models.PositiveIntegerField()
    max_session_minutes = models.PositiveIntegerField()

    # Parameters used for this generation (may differ from intake if overridden)
    generation_params = models.JSONField(null=True, blank=True)

    # Snapshots so we can audit how this plan was built
    volume_targets = models.JSONField(null=True, blank=True)
    volume_actual = models.JSONField(null=True, blank=True)
    validation_report = models.JSONField(null=True, blank=True)

    # Raw outputs from each AI step (for debugging variance)
    ai_draft = models.JSONField(null=True, blank=True)
    ai_refined = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Plan #{self.pk} — {self.user.email} — {self.split_type}"


class PlannedSession(models.Model):
    plan = models.ForeignKey(
        WeeklyPlan, on_delete=models.CASCADE, related_name="sessions"
    )
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=40)            # "Push", "Upper 1"...
    template_key = models.CharField(max_length=40)    # "push", "upper_1"...

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.plan_id}/{self.order} {self.name}"


class PlannedExercise(models.Model):
    session = models.ForeignKey(
        PlannedSession, on_delete=models.CASCADE, related_name="exercises"
    )
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=80)
    role = models.CharField(max_length=20)
    movement_category = models.CharField(max_length=40)
    sets = models.PositiveIntegerField()
    reps_min = models.PositiveIntegerField()
    reps_max = models.PositiveIntegerField()
    target_rpe = models.DecimalField(max_digits=3, decimal_places=1)
    rest = models.CharField(max_length=20)
    weight_kg = models.FloatField(null=True, blank=True)  # null = establish_needed

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} {self.sets}x{self.reps_min}-{self.reps_max}"
